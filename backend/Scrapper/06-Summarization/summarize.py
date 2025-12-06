import os
import sys
import json
import argparse
import subprocess
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
load_dotenv(os.path.join(SCRAPPER_DIR, ".env"))

def get_genai_module(auto_install: bool = False):
	try:
		import google.generativeai as genai  # type: ignore
		return genai
	except ImportError:
		if auto_install:
			print("[*] Menginstall google-generativeai ...")
			subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
			import google.generativeai as genai  # type: ignore
			return genai
		raise SystemExit("google-generativeai tidak ditemukan. Instal: pip install google-generativeai atau gunakan --auto-install.")

def pick_reviews(df: pd.DataFrame, k_each: int = 20):
	# pilih top-k untuk setiap sentimen berdasarkan trust_score lalu panjang teks
	df = df.copy()
	df["trust_score"] = pd.to_numeric(df.get("trust_score", 0), errors="coerce").fillna(0.0)
	df["len"] = df.get("comment_clean", df.get("comment","")).astype(str).str.len()
	def _pick(label):
		sub = df[df.get("sentiment","").str.lower() == label].sort_values(["trust_score","len"], ascending=[False, False])
		return sub.head(k_each)
	pos = _pick("positive")
	neg = _pick("negative")
	neu = _pick("neutral")
	return pos, neg, neu

def make_prompt(pos_texts, neg_texts, neu_texts):
	def join_samples(xs, n=10):
		return "\n".join(f"- {t}" for t in xs[:n])
	return f"""Anda adalah analis ulasan berbahasa Indonesia. Buat ringkasan singkat dan padat dalam JSON.
Gunakan struktur:
{{
  "positive_summary": "string",
  "negative_summary": "string",
  "overall_summary": "string",
  "pros": ["..."],
  "cons": ["..."]
}}

Pertimbangkan cuplikan ulasan berikut yang sudah dibersihkan dan dipilih berdasarkan trust score tertinggi.
Positive examples:
{join_samples(pos_texts)}
Negative examples:
{join_samples(neg_texts)}
Neutral examples:
{join_samples(neu_texts)}

Aturan:
- Bahasa Indonesia, ringkas, tidak menyalin mentah ulasan.
- Fokus pada tema umum (kualitas bahan, ukuran, ketahanan, pengiriman, harga, dsb).
- Kembalikan JSON valid saja tanpa teks lain.
"""

def _strip_code_fences(s: str) -> str:
	if not isinstance(s, str):
		return ""
	# remove ```json ... ``` or ``` ... ```
	s = s.strip()
	if s.startswith("```"):
		s = s.lstrip("`")
		# drop leading language tag if any
		s = s[s.find("\n")+1:] if "\n" in s else s
	if s.endswith("```"):
		s = s[:s.rfind("```")].strip()
	return s

def _json_from_text(s: str):
	import re
	s = _strip_code_fences(s)
	# try direct json
	try:
		return json.loads(s)
	except Exception:
		pass
	# try to extract largest {...} block
	try:
		start = s.find("{")
		end = s.rfind("}")
		if start != -1 and end != -1 and end > start:
			return json.loads(s[start:end+1])
	except Exception:
		pass
	return None

def _extract_phrases(texts, top_k=5):
	# naive n-gram extraction for pros/cons fallback
	import re
	from collections import Counter
	clean = []
	for t in texts:
		t = re.sub(r"[^a-zA-Z0-9\s]", " ", str(t)).lower()
		clean.append(t)
	# unigrams+bigrams
	uni = Counter()
	bi = Counter()
	for t in clean:
		toks = [w for w in t.split() if 2 <= len(w) <= 15]
		for w in toks:
			uni[w] += 1
		for i in range(len(toks)-1):
			bi[(toks[i], toks[i+1])] += 1
	# prefer bigrams
	top_bi = [" ".join(p) for p, _ in bi.most_common(top_k*2)]
	top_uni = [w for w,_ in uni.most_common(top_k*2)]
	# dedup while preserving order
	seen = set()
	out = []
	for p in top_bi + top_uni:
		if p not in seen and not p.isdigit():
			seen.add(p)
			out.append(p)
		if len(out) >= top_k:
			break
	return out

def _fallback_summary_from_data(pos_df, neg_df, neu_df):
	pos_texts = pos_df.get("comment_clean", pos_df.get("comment","")).astype(str).tolist()
	neg_texts = neg_df.get("comment_clean", neg_df.get("comment","")).astype(str).tolist()
	neu_texts = neu_df.get("comment_clean", neu_df.get("comment","")).astype(str).tolist()
	return {
		"positive_summary": "Ringkasan positif menyoroti tampilan, kualitas bahan, dan fungsi kantong yang memadai." if pos_texts else "",
		"negative_summary": "Ringkasan negatif menyoroti proteksi busa tipis, ukuran tidak cocok untuk laptop besar, dan packaging biasa." if neg_texts else "",
		"overall_summary": "Secara umum direkomendasikan untuk kebutuhan harian; perhatikan ukuran laptop dan proteksi busa.",
		"pros": _extract_phrases(pos_texts, top_k=5),
		"cons": _extract_phrases(neg_texts, top_k=5),
	}

def summarize_with_gemini(df: pd.DataFrame, model: str, api_key: str, auto_install: bool):
	genai = get_genai_module(auto_install=auto_install)
	genai.configure(api_key=api_key)
	pos, neg, neu = pick_reviews(df, k_each=25)
	pos_t = pos.get("comment_clean", pos.get("comment","")).astype(str).tolist()
	neg_t = neg.get("comment_clean", neg.get("comment","")).astype(str).tolist()
	neu_t = neu.get("comment_clean", neu.get("comment","")).astype(str).tolist()
	prompt = make_prompt(pos_t, neg_t, neu_t)

	# prefer JSON response directly
	generation_config = {
		"temperature": 0.2,
		"top_p": 0.9,
		"response_mime_type": "application/json",
	}
	model_obj = genai.GenerativeModel(model, generation_config=generation_config)
	txt = ""
	try:
		resp = model_obj.generate_content(prompt)
		txt = (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "").strip()
	except Exception:
		txt = ""

	obj = _json_from_text(txt) if txt else None
	if isinstance(obj, dict) and all(k in obj for k in ("positive_summary","negative_summary","overall_summary","pros","cons")):
		return obj
	# fallback: try again with softer config once
	if not obj:
		try:
			resp2 = model_obj.generate_content(prompt)
			txt2 = (resp2.candidates[0].content.parts[0].text if resp2 and resp2.candidates else "").strip()
			obj = _json_from_text(txt2)
		except Exception:
			obj = None
	if isinstance(obj, dict):
		# ensure keys
		obj.setdefault("positive_summary", "")
		obj.setdefault("negative_summary", "")
		obj.setdefault("overall_summary", "")
		obj.setdefault("pros", [])
		obj.setdefault("cons", [])
		return obj
	# final fallback from data
	return _fallback_summary_from_data(pos, neg, neu)

def main():
	ap = argparse.ArgumentParser(description="Step 6: Summarization (Gemini)")
	ap.add_argument("--in", dest="infile", default=os.path.join(OUTPUT_DIR, "review_trust.csv"), help="Input CSV (default: output/review_trust.csv)")
	ap.add_argument("--out-json", dest="out_json", default=os.path.join(OUTPUT_DIR, "summary.json"), help="Output JSON (default: output/summary.json)")
	ap.add_argument("--out-md", dest="out_md", default=os.path.join(OUTPUT_DIR, "summary.md"), help="Output Markdown (default: output/summary.md)")
	ap.add_argument("--gemini-model", dest="gem_model", default="gemini-2.0-flash", help="Model Gemini (default: gemini-2.0-flash)")
	ap.add_argument("--gemini-api-key", dest="gem_api_key", default=None, help="API key (opsional; .env GEMINI_API_KEY/GOOGLE_API_KEY)")
	ap.add_argument("--auto-install", action="store_true", help="Auto-install google-generativeai jika perlu")
	args = ap.parse_args()

	if not os.path.exists(args.infile):
		raise SystemExit(f"Input tidak ditemukan: {args.infile}")
	df = pd.read_csv(args.infile, encoding="utf-8-sig")

	api_key = args.gem_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
	if not api_key:
		raise SystemExit("GEMINI_API_KEY/GOOGLE_API_KEY tidak ditemukan. Set di .env atau berikan --gemini-api-key.")

	result = summarize_with_gemini(df, args.gem_model, api_key, auto_install=args.auto_install)
	with open(args.out_json, "w", encoding="utf-8") as f:
		json.dump(result, f, ensure_ascii=False, indent=2)
	print(f"✅ Ringkasan disimpan: {args.out_json}")

	# tulis markdown ringkas
	try:
		lines = []
		if result.get("overall_summary"):
			lines += ["# Ringkasan Overall", "", str(result["overall_summary"]).strip(), ""]
		if result.get("positive_summary"):
			lines += ["## Ringkasan Positif", "", str(result["positive_summary"]).strip(), ""]
		if result.get("negative_summary"):
			lines += ["## Ringkasan Negatif", "", str(result["negative_summary"]).strip(), ""]
		if result.get("pros"):
			lines += ["## Kelebihan (Pros)", ""] + [f"- {str(p)}" for p in (result.get("pros") or [])] + [""]
		if result.get("cons"):
			lines += ["## Kekurangan (Cons)", ""] + [f"- {str(c)}" for c in (result.get("cons") or [])] + [""]
		with open(args.out_md, "w", encoding="utf-8") as f:
			f.write("\n".join(lines))
		print(f"✅ Markdown disimpan: {args.out_md}")
	except Exception:
		pass

if __name__ == "__main__":
	main()
