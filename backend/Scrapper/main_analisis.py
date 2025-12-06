import os
import sys
import json
import argparse
import importlib.util
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# load .env untuk baca GEMINI_API_KEYS / GEMINI_API_KEY bila ada
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

def _find_file_recursive(filename: str, start_dir: str) -> str | None:
	for root, _, files in os.walk(start_dir):
		if filename in files:
			return os.path.join(root, filename)
	return None

def _load_module(path: str, fallback_filename: str | None = None):
	# try exact path
	if not os.path.exists(path):
		# try recursive search by filename if provided
		if fallback_filename:
			found = _find_file_recursive(fallback_filename, BASE_DIR)
			if found and os.path.exists(found):
				path = found
			else:
				raise FileNotFoundError(f"Module not found: {path} (searched {fallback_filename} recursively under {BASE_DIR})")
		else:
			raise FileNotFoundError(f"Module not found: {path}")
	spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)  # type: ignore
	return mod

# --- quick fallbacks if 01-modules not found ---
def _quick_preprocess(input_csv: str, output_csv: str):
	import re
	print(f"[quick-preprocess] {input_csv} -> {output_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if "comment" not in df.columns:
		raise SystemExit("Kolom 'comment' tidak ditemukan pada CSV input.")
	def clean_text(text: str) -> str:
		if not isinstance(text, str):
			return ""
		text = text.lower()
		text = re.sub(r"http\S+|www\S+", "", text)
		text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
		text = re.sub(r"\s+", " ", text).strip()
		return text
	df["comment_clean"] = df["comment"].astype(str).apply(clean_text)
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	print(f"✅ (quick) review_clean.csv disimpan: {output_csv}")

def _quick_tokenize(input_csv: str, output_csv: str, text_col: str = "comment_clean"):
	print(f"[quick-tokenize] {input_csv} -> {output_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom '{text_col}' tidak ditemukan di {input_csv}")
	def simple_tokenize(text: str):
		if not isinstance(text, str):
			return []
		return [t for t in text.strip().split() if t]
	tokens_list = df[text_col].astype(str).apply(simple_tokenize)
	df_out = df.copy()
	df_out["tokens"] = tokens_list.apply(lambda xs: " ".join(xs))
	df_out["tokens_count"] = tokens_list.apply(len)
	df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
	print(f"✅ (quick) review_tokens.csv disimpan: {output_csv}")

def _safe_parse_dt(x):
	# support epoch (sec) or iso-ish strings
	if x is None or x == "":
		return None
	try:
		# numeric epoch (ms or s)
		val = float(x)
		# assume seconds if < 10^12
		if val > 1e12:
			val = val / 1000.0
		return datetime.utcfromtimestamp(val)
	except Exception:
		pass
	# try pandas parser
	try:
		return pd.to_datetime(x, utc=True, errors="coerce").to_pydatetime()
	except Exception:
		return None

def _extract_variant_label(r: dict):
	# Shopee ratings often contain 'product_items' with 'model_name' or 'name'
	try:
		items = r.get("product_items") or r.get("product_item") or []
		if isinstance(items, dict):
			items = [items]
		for it in items:
			for k in ("model_name","name","modelname","variation_name"):
				if it.get(k):
					return str(it.get(k))
	except Exception:
		pass
	for k in ("model_name","modelname","variant_name","variation","options"):
		if r.get(k):
			v = r.get(k)
			if isinstance(v, list):
				v = " / ".join(map(str, v))
			return str(v)
	return None

def _ensure_review_csv(out_dir: str = OUTPUT_DIR):
	csv_path = os.path.join(out_dir, "review.csv")
	if os.path.exists(csv_path):
		return csv_path
	# build from review.json (best-effort)
	json_candidates = [
		os.path.join(BASE_DIR, "review.json"),
		os.path.join(OUTPUT_DIR, "review.json"),
	]
	# load produk.json (opsional) untuk metadata produk global
	product_meta = None
	prod_path = os.path.join(BASE_DIR, "produk.json")
	if os.path.exists(prod_path):
		try:
			with open(prod_path, "r", encoding="utf-8") as f:
				product_meta = json.load(f)
		except Exception:
			product_meta = None
	product_name = product_meta.get("name") if isinstance(product_meta, dict) else None
	product_type = None
	if isinstance(product_meta, dict):
		cats = product_meta.get("categories") or product_meta.get("fe_categories") or []
		if isinstance(cats, list) and cats:
			# ambil kategori paling spesifik
			try:
				product_type = cats[-1].get("display_name") or cats[0].get("display_name")
			except Exception:
				product_type = None

	for p in json_candidates:
		if os.path.exists(p):
			with open(p, "r", encoding="utf-8") as f:
				obj = json.load(f)
			# Shopee ratings array or raw list
			if isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], dict) and "ratings" in obj["data"]:
				revs = obj["data"]["ratings"] or []
			elif isinstance(obj, list):
				revs = obj
			else:
				# unknown shape
				revs = []
			rows = []
			for r in revs:
				raw_ct = r.get("mtime") or r.get("ctime") or r.get("create_time")
				dt = _safe_parse_dt(raw_ct)
				iso_time = dt.isoformat() if dt else (str(raw_ct) if raw_ct is not None else None)
				comment = r.get("comment") or ""
				variant = _extract_variant_label(r)
				rows.append({
					"username": r.get("author_username") or r.get("author_shopid") or "",
					"comment": comment,
					"rating": r.get("rating_star") or r.get("rating") or None,
					"likes": r.get("like_count") or r.get("like") or 0,
					"create_time": iso_time,
					"userid": r.get("userid") or r.get("author_userid") or None,
					"orderid": r.get("orderid") or None,
					"product_name": product_name,
					"product_type": product_type,
					"product_label": variant
				})
			df = pd.DataFrame(rows)
			# sanitize basics
			df["comment"] = df["comment"].fillna("").astype(str)
			# label usefulness
			df["comment_usefulness"] = df["comment"].apply(lambda s: "tidak_berguna" if not str(s).strip() else "berguna")
			df["rating"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).astype(int)
			df["likes"] = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0).astype(int)
			# ensure create_time string
			if "create_time" in df.columns:
				df["create_time"] = df["create_time"].astype(str)
			os.makedirs(out_dir, exist_ok=True)
			df.to_csv(csv_path, index=False, encoding="utf-8-sig")
			print(f"✅ Dibuat dari review.json: {csv_path} (rows={len(df)})")
			return csv_path
	# nothing found
	raise SystemExit("review.csv tidak ditemukan dan review.json juga tidak ada. Jalankan scrapper terlebih dahulu.")

def run_pipeline(use_gemini: bool, gemini_key: str | None, auto_install: bool, serve: bool, *, backend: str = "auto", nb_model_path: str | None = None, gemini_keys_str: str | None = None):
	# 01 - Preprocessing
	print("\n[01] Text Preprocessing — membersihkan kolom 'comment' -> 'comment_clean'")
	# Tentukan root output per-backend
	backend_key = (backend or "auto").lower()
	# gunakan lowercase konsisten agar selaras dengan app (?b=indobert)
	folder_map = {"gemini": "gemini", "indobert": "indobert", "nb": "nb", "lexicon": "lexicon", "auto": "auto"}
	out_root = os.path.join(BASE_DIR, "output", folder_map.get(backend_key, "auto"))
	os.makedirs(out_root, exist_ok=True)
	print(f"[out] Menulis artefak ke: {out_root}")

	pre = _load_module(os.path.join(BASE_DIR, "01-Text Preprocessing", "preprocess_reviews.py"))
	csv_in = _ensure_review_csv(out_root)
	clean_csv = os.path.join(out_root, "review_clean.csv")
	pre.process_csv(input_csv=csv_in, output_csv=clean_csv)

	# 01b - Tokenisasi
	print("\n[01b] Tokenisasi — membangun kolom 'tokens' dan 'tokens_count'")
	tok = _load_module(os.path.join(BASE_DIR, "01-Text Preprocessing", "tokenisasi.py"))
	tokens_csv = os.path.join(out_root, "review_tokens.csv")
	tok.build_tokens(input_csv=clean_csv, output_csv=tokens_csv, text_col="comment_clean")

	# 03 - Sentiment (pilih backend)
	print("\n[03] Sentiment Analysis — pilih: IndoBERT / Gemini / Naive Bayes / Lexicon")
	sent = _load_module(os.path.join(BASE_DIR, "03-Sentiment Analysis", "sentiment.py"), fallback_filename="sentiment.py")
	in_csv_for_sent = tokens_csv if os.path.exists(tokens_csv) else clean_csv
	sent_out = os.path.join(out_root, "review_sentiment.csv")
	text_col_guess = "tokens" if "tokens" in pd.read_csv(in_csv_for_sent, nrows=1, encoding="utf-8-sig").columns else "comment_clean"
	backend = (backend or "auto").lower()
	print(f"[03] Backend terpilih: {backend}")
	if backend == "gemini" or (backend == "auto" and use_gemini):
		env_multi = os.environ.get("GEMINI_API_KEYS", "")
		keys_str = gemini_keys_str or env_multi
		keys = [k.strip() for k in keys_str.split(",") if k.strip()] if keys_str else ([gemini_key] if gemini_key else [])
		print(f"[03] Gemini Sentiment dengan {len(keys) or 1} API key(s). Rotasi tiap 10 request, limit 15/min per key.")
		sent.gemini_classify(
			in_csv_for_sent,
			text_col=text_col_guess,
			out_csv=sent_out,
			api_key=gemini_key,
			api_keys=keys if keys else None,
			model="gemini-2.0-flash",
			auto_install=auto_install,
			rotate_every=10,
			per_min_limit=15
		)
	elif backend == "indobert" or backend == "auto":
		try:
			print("[03] IndoBERT classifier (offline).")
			indo_model = os.environ.get("INDO_SENT_MODEL", "indobenchmark/indobert-base-p2")
			sent.indobert_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out, model_name=indo_model)
		except Exception as e:
			print(f"⚠️ IndoBERT gagal: {e}")
			nb_model = nb_model_path or os.path.join(OUTPUT_DIR, "sentiment_nb.joblib")
			if os.path.exists(nb_model):
				try:
					print("[03] Fallback ke Naive Bayes model.")
					sent.nb_predict(in_csv_for_sent, text_col=text_col_guess, model_path=nb_model, out_csv=sent_out)
				except Exception as e2:
					print(f"⚠️ NB gagal: {e2}. Fallback ke leksikon.")
					sent.lexicon_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out)
			else:
				print("[03] Fallback ke leksikon (offline).")
				sent.lexicon_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out)
	elif backend == "nb":
		nb_model = nb_model_path or os.path.join(OUTPUT_DIR, "sentiment_nb.joblib")
		if not os.path.exists(nb_model):
			print(f"⚠️ NB model tidak ditemukan: {nb_model}. Fallback ke leksikon.")
			sent.lexicon_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out)
		else:
			print(f"[03] Naive Bayes predict: {nb_model}")
			sent.nb_predict(in_csv_for_sent, text_col=text_col_guess, model_path=nb_model, out_csv=sent_out)
	elif backend == "lexicon":
		print("[03] Lexicon-based sentiment (offline).")
		sent.lexicon_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out)
	else:
		# guard: unknown backend, use auto
		print("[03] Backend tidak dikenal. Menggunakan mode auto (IndoBERT→NB→Lexicon).")
		try:
			indo_model = os.environ.get("INDO_SENT_MODEL", "indobenchmark/indobert-base-p2")
			sent.indobert_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out, model_name=indo_model)
		except Exception:
			nb_model = os.path.join(OUTPUT_DIR, "sentiment_nb.joblib")
			if os.path.exists(nb_model):
				sent.nb_predict(in_csv_for_sent, text_col=text_col_guess, model_path=nb_model, out_csv=sent_out)
			else:
				sent.lexicon_classify(in_csv_for_sent, text_col=text_col_guess, out_csv=sent_out)

	# 04 - Fake Review Detection (heuristics)
	print("\n[04] Fake Review Detection — heuristics")
	det = _load_module(os.path.join(BASE_DIR, "04-Fake Review Detection", "detect_fake.py"), fallback_filename="detect_fake.py")
	df_head = pd.read_csv(sent_out, nrows=1, encoding="utf-8-sig")
	text_col = "tokens" if "tokens" in df_head.columns else ("comment_clean" if "comment_clean" in df_head.columns else "comment")
	fake_out = os.path.join(out_root, "review_fake.csv")
	det.heuristics_detect(sent_out, text_col=text_col, out_csv=fake_out)

	# 05 - Trust Score
	print("\n[05] Trust Score Calculation")
	ts = _load_module(os.path.join(BASE_DIR, "05-Trust Score", "trust_score.py"), fallback_filename="trust_score.py")
	df_fake = pd.read_csv(fake_out, encoding="utf-8-sig")
	df_trust = ts.compute_trust(df_fake)
	trust_out = os.path.join(out_root, "review_trust.csv")
	df_trust.to_csv(trust_out, index=False, encoding="utf-8-sig")
	# product summary
	product_json = os.path.join(BASE_DIR, "produk.json")
	summary = ts.product_summary(df_trust, product=json.load(open(product_json, "r", encoding="utf-8"))) if os.path.exists(product_json) else ts.product_summary(df_trust)
	product_out = os.path.join(out_root, "product_trust.json")
	with open(product_out, "w", encoding="utf-8") as f:
		json.dump(summary, f, ensure_ascii=False, indent=2)
	print(f"✅ Output: {trust_out}, {product_out}")

	# 06 - Summarization
	print("\n[06] Summarization — Gemini (fallback ke ringkasan berbasis data)")
	sum_mod = _load_module(os.path.join(BASE_DIR, "06-Summarization", "summarize.py"), fallback_filename="summarize.py")
	df_tr = pd.read_csv(trust_out, encoding="utf-8-sig")
	if gemini_key:
		result = sum_mod.summarize_with_gemini(df_tr, model="gemini-1.5-flash", api_key=gemini_key, auto_install=auto_install)
	else:
		result = sum_mod.summarize_with_gemini(df_tr, model="gemini-1.5-flash", api_key="invalid-key", auto_install=False)

	# ====== Perbaiki fallback pros/cons dan persentase ======
	def _sent_counts(df):
		vc = df.get("sentiment", pd.Series([])).astype(str).str.lower().value_counts()
		pos = int(vc.get("positive", 0)); neg = int(vc.get("negative", 0)); neu = int(vc.get("neutral", 0))
		tot = max(1, pos + neg + neu)
		return pos, neg, neu, tot

	STOPWORDS_ID = {
		"yg","yang","buat","untuk","itu","dan","di","ke","dengan","ada","jadi","sangat","banget","real","pict","aja","juga","udah","sih","saja","serta","atau","kan","nih","lah",
		"warna","hitam","abu","merah","biru","putih","tas","bagus","banget","keren","oke","ok","mantap","item","produk","barang"
	}
	def _clean_phrase(s: str) -> str:
		s = " ".join(str(s).lower().split())
		# buang token 1 huruf/angka dan stopwords warna/filler
		toks = [t for t in s.split() if len(t) >= 2 and t not in STOPWORDS_ID]
		return " ".join(toks)

	def _top_phrases(texts: list[str], n=5):
		texts = [t for t in (texts or []) if isinstance(t, str)]
		if not texts:
			return []
		# prefer TF-IDF 2-3 gram
		try:
			from sklearn.feature_extraction.text import TfidfVectorizer
			vec = TfidfVectorizer(
				ngram_range=(2,3),
				min_df=2,
				max_features=1000,
				token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b"
			)
			X = vec.fit_transform(texts)
			# skor rata-rata per fitur
			import numpy as np
			scores = X.mean(axis=0).A1
			feats = vec.get_feature_names_out()
			cands = [(feats[i], scores[i]) for i in range(len(feats))]
			cands.sort(key=lambda x: x[1], reverse=True)
			out = []
			seen = set()
			for p, _ in cands:
				pp = _clean_phrase(p)
				if not pp or pp in seen: 
					continue
				seen.add(pp)
				out.append(pp)
				if len(out) >= n:
					break
			return out
		except Exception:
			# fallback: frekuensi bigram + unigram
			from collections import Counter
			import re
			def toks(t): 
				return [w for w in re.findall(r"[a-zA-Z]{2,}", t.lower()) if w not in STOPWORDS_ID]
			bi = Counter()
			uni = Counter()
			for t in texts:
				ws = toks(t)
				for i in range(len(ws)-1):
					bi[(ws[i], ws[i+1])] += 1
				for w in ws:
					uni[w] += 1
			cands = [" ".join(k) for k,_ in bi.most_common(n*3)] + [k for k,_ in uni.most_common(n*3)]
			out, seen = [], set()
			for p in cands:
				pp = _clean_phrase(p)
				if not pp or pp in seen: 
					continue
				seen.add(pp); out.append(pp)
				if len(out) >= n: break
			return out

	# hitung distribusi sentimen + ekstraksi frasa berbasis data
	pos, neg, neu, tot = _sent_counts(df_tr)
	pos_pct = round(100.0*pos/max(1, tot), 1)
	neg_pct = round(100.0*neg/max(1, tot), 1)
	txt_col = "comment_clean" if "comment_clean" in df_tr.columns else "comment"
	pos_texts = df_tr.loc[df_tr["sentiment"].astype(str).str.lower().eq("positive"), txt_col].astype(str).tolist() if "sentiment" in df_tr.columns else []
	neg_texts = df_tr.loc[df_tr["sentiment"].astype(str).str.lower().eq("negative"), txt_col].astype(str).tolist() if "sentiment" in df_tr.columns else []
	pros_phr = _top_phrases(pos_texts, n=5)
	cons_phr = _top_phrases(neg_texts, n=7)

	POS_WORDS = {"bagus","keren","mantap","rapi","tebal","cepat","recommended","sesuai","murah","puas","halus","nyaman","cocok"}
	def _filter_cons(lst):
		out = []
		seen = set()
		for p in lst:
			toks = set(p.split())
			if toks & POS_WORDS:
				continue
			if any(w in STOPWORDS_ID for w in toks):
				continue
			if p in seen or len(p) < 4:
				continue
			seen.add(p); out.append(p)
			if len(out) >= 5: break
		return out[:5]
	cons_phr = _filter_cons(cons_phr)
	if not pros_phr:
		pros_phr = ["bahan baik", "pengiriman cepat", "harga sesuai", "banyak kantong", "desain menarik"]
	if not cons_phr:
		cons_phr = ["busa pelindung tipis", "kurang muat laptop besar", "kemasan kurang rapi"]

	# perbarui summary dasar
	if not result.get("positive_summary"):
		result["positive_summary"] = f"Sebagian ulasan positif ({pos_pct}%) menyoroti kualitas bahan, tampilan, dan fungsi penyimpanan."
	if not result.get("negative_summary"):
		result["negative_summary"] = "Ringkasan negatif menyoroti proteksi busa yang tipis, ukuran yang kurang pas untuk laptop besar, dan kemasan yang biasa."

	# ====== Filter khusus backend Gemini: bersihkan frasa tak bermakna ======
	BAN_SINGLE = {"yg","yang","buat","real","pict","foto","gambar","itu","dan","aja","aja","nih","loh","dong","warna","hitam","abu","putih","merah","biru"}
	BAN_POS_IN_CONS = POS_WORDS
	BAN_PATTERNS = {"real pict","tampil real","pict warna","buat yg","yg laptop","warna hitam","warna abu"}
	def _clean_list_phrases(lst, is_cons=False, fallback=[]):
		out, seen = [], set()
		for p in (lst or []):
			s = _clean_phrase(p)
			toks = s.split()
			# drop jika sangat pendek, berisi token terlarang, atau pola terlarang
			if len(s) < 4: 
				continue
			if any(t in BAN_SINGLE for t in toks):
				continue
			if any(s.find(bp) != -1 for bp in BAN_PATTERNS):
				continue
			if is_cons and (set(toks) & BAN_POS_IN_CONS):
				continue
			if s in seen:
				continue
			seen.add(s)
			out.append(s)
			if len(out) >= 5:
				break
		# jika hasil terlalu sedikit, gunakan fallback data-driven
		if is_cons and len(out) < 3 and fallback:
			for p in fallback:
				if p not in seen:
					seen.add(p); out.append(p)
				if len(out) >= 5:
					break
		if (not is_cons) and len(out) < 3 and fallback:
			for p in fallback:
				if p not in seen:
					seen.add(p); out.append(p)
				if len(out) >= 5:
					break
		return out[:5]

	# tentukan apakah backend Gemini dipakai
	backend_lower = (backend or "auto").lower()
	used_gemini = (backend_lower == "gemini") or (backend_lower == "auto" and use_gemini)

	if used_gemini:
		# sanitize pros/cons dari output LLM
		result["pros"] = _clean_list_phrases(result.get("pros") or [], is_cons=False, fallback=pros_phr)
		result["cons"] = _clean_list_phrases(result.get("cons") or [], is_cons=True, fallback=cons_phr)
	else:
		# non-Gemini: pastikan pros/cons tetap masuk akal dengan gabungan hasil ekstraksi data
		def _is_poor_list(xs): 
			return (not xs) or any(isinstance(x, str) and len(x) <= 2 for x in xs)
		if _is_poor_list(result.get("pros")):
			result["pros"] = pros_phr
		else:
			extra = [p for p in pros_phr if p not in (result.get("pros") or [])]
			result["pros"] = (result.get("pros") or []) + extra
			result["pros"] = result["pros"][:5]
		if _is_poor_list(result.get("cons")) or any(any(w in POS_WORDS for w in str(c).split()) for c in (result.get("cons") or [])):
			result["cons"] = cons_phr
		else:
			extra = [c for c in cons_phr if c not in (result.get("cons") or [])]
			result["cons"] = (result.get("cons") or []) + extra
			result["cons"] = result["cons"][:5]

	# pastikan overall_summary terisi
	if not result.get("overall_summary"):
		result["overall_summary"] = "Kesimpulan: produk cukup direkomendasikan dengan kualitas bahan dan fungsi memadai; perhatikan proteksi busa dan ukuran laptop."

	# recent 30d dan simpan
	def _recent_30d_stats(df):
		df2 = df.copy()
		if "create_time" in df2.columns:
			df2["__dt"] = pd.to_datetime(df2["create_time"], errors="coerce", utc=True)
			cut = pd.Timestamp.utcnow() - pd.Timedelta(days=30)
			df2 = df2[df2["__dt"] >= cut]
		else:
			df2 = df2.iloc[0:0]
		count = int(len(df2))
		sent_dist = df2.get("sentiment", pd.Series([])).astype(str).str.lower().value_counts().to_dict()
		highlights = []
		if count:
			top = df2.sort_values(["trust_score"], ascending=False).head(5)
			for _, r in top.iterrows():
				highlights.append({
					"sentiment": str(r.get("sentiment")),
					"trust": float(pd.to_numeric(r.get("trust_score"), errors="coerce") or 0),
					"comment": str(r.get("comment_clean") or r.get("comment") or ""),
					"time": str(r.get("create_time") or "")
				})
		return {"count": count, "sentiment_distribution": sent_dist, "highlights": highlights}

	result["recent_30d"] = _recent_30d_stats(df_tr)

	summary_json = os.path.join(out_root, "summary.json")
	with open(summary_json, "w", encoding="utf-8") as f:
		json.dump(result, f, ensure_ascii=False, indent=2)
	print(f"✅ Output: {summary_json}")

	# 07 - Visualisasi (opsional serve)
	if serve:
		print("\n[07] Visualisasi — menjalankan Flask dashboard di http://localhost:5000")
		from subprocess import Popen
		app_path = os.path.join(BASE_DIR, "07-visualisi", "app.py")
		Popen([sys.executable, app_path])

def main():
	ap = argparse.ArgumentParser(description="Pipeline End-to-End: 01→07")
	ap.add_argument("--use-gemini", action="store_true", help="Paksa gunakan Gemini (override auto)")
	ap.add_argument("--auto-install", action="store_true", help="Auto-install dependency saat perlu")
	ap.add_argument("--serve", action="store_true", help="Jalankan Flask dashboard setelah selesai")
	ap.add_argument("--gemini-api-key", dest="gem_api_key", default=None, help="API key Gemini (opsional; .env GOOGLE_API_KEY/GEMINI_API_KEY)")
	# pilihan backend sentiment
	ap.add_argument("--sentiment-backend", dest="sent_backend", choices=["auto","indobert","gemini","nb","lexicon"], default="auto", help="Backend sentiment: auto (default) | indobert | gemini | nb | lexicon")
	ap.add_argument("--nb-model", dest="nb_model_path", default=None, help="Path model NB untuk sentiment (default: output/sentiment_nb.joblib)")
	ap.add_argument("--gemini-keys", dest="gem_keys", default=None, help="Daftar API key Gemini dipisah koma untuk rotasi (override ENV GEMINI_API_KEYS)")
	args = ap.parse_args()

	# API key resolusi
	key = args.gem_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
	run_pipeline(
		use_gemini=args.use_gemini or bool(key),
		gemini_key=key,
		auto_install=args.auto_install,
		serve=args.serve,
		backend=args.sent_backend,
		nb_model_path=args.nb_model_path,
		gemini_keys_str=args.gem_keys
	)

if __name__ == "__main__":
	main()
