import os
import argparse
import json
import time
import pandas as pd
from dotenv import load_dotenv
import sys
import subprocess
from collections import defaultdict

# struktur folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
# load .env di root Scrapper
load_dotenv(os.path.join(SCRAPPER_DIR, ".env"))

# ===== helper: safe import google-generativeai =====
def get_genai_module(auto_install: bool = False):
	try:
		import google.generativeai as genai  # type: ignore
		return genai
	except ImportError:
		if auto_install:
			print("[*] google-generativeai belum terpasang. Menginstall otomatis...")
			try:
				subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai"])
				import google.generativeai as genai  # type: ignore
				return genai
			except Exception as e:
				raise SystemExit(f"Gagal memasang google-generativeai: {e}\nCoba manual: pip install google-generativeai")
		raise SystemExit(
			"Module 'google-generativeai' tidak ditemukan.\n"
			"Instal terlebih dahulu: pip install google-generativeai\n"
			"Atau jalankan dengan --auto-install untuk memasang otomatis."
		)

# ===== util umum =====
def _pick_input_csv(pref_tokens=True):
	in_tokens = os.path.join(OUTPUT_DIR, "review_tokens.csv")
	in_clean = os.path.join(OUTPUT_DIR, "review_clean.csv")
	if pref_tokens and os.path.exists(in_tokens):
		return in_tokens
	if os.path.exists(in_clean):
		return in_clean
	raise SystemExit("Input tidak ditemukan. Pastikan file output/review_tokens.csv atau output/review_clean.csv tersedia.")

def _ensure_text_col(df: pd.DataFrame, text_col: str):
	if text_col not in df.columns:
		raise SystemExit(f"Kolom teks '{text_col}' tidak ditemukan di input CSV. Kolom tersedia: {list(df.columns)}")

def _save_result(df_out: pd.DataFrame, out_csv: str):
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Sentiment disimpan: {out_csv} (rows={len(df_out)})")
	print(df_out[[c for c in df_out.columns if c in ('comment', 'comment_clean')]+['sentiment']].head(5))

# ===== normalization helpers & lexicon fallback (kept) =====
_VALID_LABELS = {"positive", "neutral", "negative"}
def _normalize_label(s: str) -> str:
	s = (s or "").strip().lower()
	if s in _VALID_LABELS:
		return s
	# simple id synonyms
	if s in ("positif", "pos", "bagus", "baik"):
		return "positive"
	if s in ("negatif", "neg", "buruk", "jelek"):
		return "negative"
	return "neutral"

def _safe_conf(v, default=0.5):
	try:
		x = float(v)
		if not (x == x):  # NaN check
			return default
		return max(0.0, min(1.0, x))
	except Exception:
		return default

POS_LEX = {
	"bagus","baik","mantap","keren","recommended","worth","cepat","halus","puas",
	"best","good","nice","great","perfect","love","suka","realpict","rapi","aman"
}
NEG_LEX = {
	"jelek","buruk","tipis","kecil","pecah","rusak","mengecewakan","lambat","kecewa",
	"tidak","kurang","nggak","ga","parah","patah","sobek","bocor","tipiss","kekecilan"
}
def _lexicon_score(text: str):
	t = (text or "").lower()
	if not t.strip():
		return 0.0
	toks = t.split()
	if not toks:
		return 0.0
	pos = sum(1 for w in toks if w in POS_LEX)
	neg = sum(1 for w in toks if w in NEG_LEX)
	# emoji/lightweight cues
	if "👍" in t or "🥰" in t or "🔥" in t: pos += 1
	if "😔" in t or "😠" in t or "👎" in t: neg += 1
	score = (pos - neg) / max(1.0, (pos + neg))
	# clamp -1..1
	return max(-1.0, min(1.0, score))

def _lexicon_label_conf(text: str):
	s = _lexicon_score(text)
	if s > 0.05:
		return "positive", min(1.0, 0.6 + 0.4*abs(s))
	if s < -0.05:
		return "negative", min(1.0, 0.6 + 0.4*abs(s))
	return "neutral", max(0.3, 0.6 - 0.4*abs(s))

# --- Fallback offline: lexicon-based sentiment (ID/EN) ---
def lexicon_classify(input_csv: str, text_col: str, out_csv: str):
	"""
	Klasifikasi sentimen offline berbasis leksikon (tanpa API).
	- Menghasilkan label: positive/neutral/negative dan confidence 0..1.
	- Komentar kosong/placeholder ('comment_tidak_berguna') diberi neutral, confidence rendah (0.2).
	"""
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		# fallback ke kolom umum
		if "tokens" in df.columns:
			text_col = "tokens"
		elif "comment_clean" in df.columns:
			text_col = "comment_clean"
		elif "comment" in df.columns:
			text_col = "comment"
		else:
			raise SystemExit(f"Tidak menemukan kolom teks untuk lexicon_classify. Dapatkan salah satu dari: tokens/comment_clean/comment.")

	POS_LEX = {
		"bagus","baik","mantap","keren","recommended","worth","cepat","halus","puas",
		"best","good","nice","great","perfect","love","suka","rapi","aman"
	}
	NEG_LEX = {
		"jelek","buruk","tipis","kecil","pecah","rusak","mengecewakan","lambat","kecewa",
		"tidak","kurang","parah","patah","sobek","bocor","kekecewa","cacat"
	}

	def score_text(t: str):
		# change handling for empty comment to NEGATIVE (was neutral)
		if not isinstance(t, str) or not t.strip() or t.strip() == "comment_tidak_berguna":
			return "negative", 0.6
		low = t.lower()
		toks = [w for w in low.split() if w]
		pos = sum(1 for w in toks if w in POS_LEX) + (1 if any(ch in low for ch in ["👍","🥰","🔥"]) else 0)
		neg = sum(1 for w in toks if w in NEG_LEX) + (1 if any(ch in low for ch in ["😔","😠","👎"]) else 0)
		if pos == 0 and neg == 0:
			return "neutral", 0.5
		raw = (pos - neg) / max(1.0, (pos + neg))  # -1..1
		if raw > 0.05:
			lbl = "positive"
		elif raw < -0.05:
			lbl = "negative"
		else:
			lbl = "neutral"
		conf = min(0.95, 0.6 + 0.4*abs(raw))
		return lbl, float(conf)

	lbls = []
	confs = []
	for t in df[text_col].astype(str).tolist():
		l, c = score_text(t)
		lbls.append(l)
		confs.append(c)

	df_out = df.copy()
	df_out["sentiment"] = lbls
	df_out["sentiment_confidence"] = pd.to_numeric(confs, errors="coerce").fillna(0.6).clip(0,1)
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Sentiment (offline leksikon) disimpan: {out_csv}")

# ===== Naive Bayes path =====
def _detect_label_text_cols(df: pd.DataFrame):
	# deteksi kolom label umum
	label_col = None
	for c in ("label", "sentiment", "y", "target"):
		if c in df.columns:
			label_col = c
			break
	if not label_col:
		raise SystemExit("Data latih tidak memiliki kolom label. Harap sediakan kolom 'label' atau 'sentiment'.")
	# deteksi kolom teks umum
	text_col = None
	for c in ("comment_clean", "tokens", "comment", "text"):
		if c in df.columns:
			text_col = c
			break
	if not text_col:
		raise SystemExit("Data latih tidak memiliki kolom teks. Harap sediakan 'comment_clean' / 'tokens' / 'comment' / 'text'.")
	return text_col, label_col

def nb_train(train_csv: str, model_out: str):
	from sklearn.feature_extraction.text import TfidfVectorizer
	from sklearn.naive_bayes import MultinomialNB
	from sklearn.pipeline import Pipeline
	from sklearn.preprocessing import FunctionTransformer
	import joblib

	print(f"[NB] Training dari: {train_csv}")
	df = pd.read_csv(train_csv, encoding="utf-8-sig")
	text_col, label_col = _detect_label_text_cols(df)
	X = df[text_col].astype(str).tolist()
	y = df[label_col].astype(str).tolist()

	# pipeline tfidf + NB; pakai unigram+bigram
	pipe = Pipeline([
		("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, max_features=100000)),
		("clf", MultinomialNB())
	])
	pipe.fit(X, y)
	joblib.dump({"pipe": pipe, "text_col": text_col}, model_out)
	print(f"✅ Model NB disimpan: {model_out}")

def nb_predict(input_csv: str, text_col: str, model_path: str, out_csv: str):
	import joblib
	import numpy as np

	print(f"[NB] Predict: {input_csv} dengan model: {model_path}")
	obj = joblib.load(model_path)
	pipe = obj["pipe"]
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	_ensure_text_col(df, text_col)

	X = df[text_col].astype(str).tolist()
	preds = pipe.predict(X)
	# prob max sebagai confidence (jika tersedia)
	if hasattr(pipe, "predict_proba"):
		proba = pipe.predict_proba(X)
		conf = proba.max(axis=1)
	else:
		conf = np.ones(len(preds), dtype=float)

	df_out = df.copy()
	df_out["sentiment"] = preds
	df_out["sentiment_confidence"] = conf
	_save_result(df_out, out_csv)

# ===== API key rotation + rate limit =====
class KeyRotator:
	def __init__(self, keys: list[str], per_min_limit: int = 15, rotate_every: int = 10):
		self.keys = [k.strip() for k in keys if k and k.strip()]
		if not self.keys:
			raise ValueError("Tidak ada API key Gemini yang valid.")
		self.per_min_limit = max(1, per_min_limit)
		self.rotate_every = max(1, rotate_every)
		self.idx = 0
		self.used_with_current = 0
		self.counter = defaultdict(int)      # count in current window per key
		self.window_start = defaultdict(float)  # epoch start per key

	def _mask(self, k: str) -> str:
		if not k:
			return ""
		head = k[:4]
		tail = k[-4:] if len(k) > 8 else "****"
		return f"{head}…{tail}"

	def _ensure_window(self, key: str):
		now = time.time()
		ws = self.window_start.get(key, None)
		if ws is None or (now - ws) >= 60.0:
			self.window_start[key] = now
			self.counter[key] = 0

	def acquire(self) -> tuple[str, str]:
		"""
		Return (key, masked) yang siap dipakai, sleep bila perlu agar <= per_min_limit/menit.
		Rotate key setiap rotate_every request.
		"""
		key = self.keys[self.idx]
		self._ensure_window(key)
		# rate-limit per key
		now = time.time()
		elapsed = now - self.window_start[key]
		if self.counter[key] >= self.per_min_limit:
			sleep_for = max(0.0, 60.0 - elapsed) + 0.05
			print(f"[Gemini] Rate limit tercapai untuk key {self._mask(key)} — tidur {sleep_for:.1f}s")
			time.sleep(sleep_for)
			self._ensure_window(key)
		# gunakan key ini
		self.counter[key] += 1
		self.used_with_current += 1
		# rotasi setiap N request
		if self.used_with_current >= self.rotate_every:
			self.idx = (self.idx + 1) % len(self.keys)
			self.used_with_current = 0
		return key, self._mask(key)

# ===== Gemini path =====
def gemini_classify(
	input_csv: str,
	text_col: str,
	out_csv: str,
	api_key: str | None = None,
	*,                 # force keyword-only below
	api_keys: list[str] | None = None,
	model: str = "gemini-2.0-flash",
	batch_size: int = 20,
	sleep_s: float = 0.3,
	limit: int = None,
	auto_install: bool = False,
	rotate_every: int = 10,
	per_min_limit: int = 15
):
	genai = get_genai_module(auto_install=auto_install)

	# Kumpulkan keys: prioritas arg api_keys > env GEMINI_API_KEYS > api_key > env GEMINI_API_KEY/GOOGLE_API_KEY
	keys: list[str] = []
	if api_keys and isinstance(api_keys, (list, tuple)):
		keys = list(api_keys)
	else:
		env_multi = os.environ.get("GEMINI_API_KEYS", "")
		if env_multi:
			keys = [k.strip() for k in env_multi.split(",") if k.strip()]
	if not keys:
		single = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
		if single:
			keys = [single]
	if not keys:
		raise SystemExit("Tidak ada API key. Isi --gemini-keys, atau set GEMINI_API_KEYS/GEMINI_API_KEY/GOOGLE_API_KEY.")

	rotator = KeyRotator(keys, per_min_limit=per_min_limit, rotate_every=rotate_every)

	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	_ensure_text_col(df, text_col)
	texts = df[text_col].astype(str).tolist()
	if limit:
		texts = texts[:limit]
		df = df.iloc[:limit].copy()

	system_prompt = (
		"Klasifikasikan sentimen ulasan Bahasa Indonesia menjadi salah satu label: positive, neutral, negative. "
		"Kembalikan JSON valid saja dengan format: {\"sentiment\":\"positive|neutral|negative\",\"confidence\":0..1}. "
		"Confidence mencerminkan keyakinan model (0..1). Jangan sertakan teks lain."
	)
	generation_config = {
		"temperature": 0.2,
		"top_p": 0.9,
		"response_mime_type": "application/json",
	}

	# indices that have content
	N = len(texts)
	results = [{"sentiment": "negative", "confidence": 0.6} for _ in range(N)]
	idxs = [i for i, t in enumerate(texts) if t.strip() and t.strip() != "comment_tidak_berguna"]
	cls_texts = [texts[i] for i in idxs]
	print(f"[Gemini] total={N}, to_classify={len(cls_texts)}, skipped_empty={N - len(cls_texts)}")

	def classify_one(t: str):
		key, masked = rotator.acquire()
		genai.configure(api_key=key)
		model_obj = genai.GenerativeModel(model, generation_config=generation_config)
		print(f"[Gemini] classifying with key={masked}")
		txt = ""
		try:
			resp = model_obj.generate_content(f"{system_prompt}\nTeks:\n{t}")
			txt = (resp.candidates[0].content.parts[0].text if resp and resp.candidates else "").strip()
		except Exception:
			txt = ""
		obj = None
		if txt:
			try:
				obj = json.loads(txt)
			except Exception:
				obj = None
		if isinstance(obj, dict):
			lbl_norm = _normalize_label(obj.get("sentiment", "neutral"))
			conf_val = _safe_conf(obj.get("confidence"), default=0.6)
			return {"sentiment": lbl_norm, "confidence": conf_val}
		# fallback lexicon for non-empty texts
		lbl, conf = _lexicon_label_conf(t)
		return {"sentiment": lbl, "confidence": _safe_conf(conf, default=0.6)}

	# classify only non-empty texts
	if cls_texts:
		batched = 0
		for i in range(0, len(cls_texts), batch_size):
			batch = cls_texts[i:i+batch_size]
			for j, t in enumerate(batch):
				res = classify_one(t)
				results[idxs[i + j]] = res
				time.sleep(sleep_s)
			batched += len(batch)
			print(f"[Gemini] progress: {min(batched, len(cls_texts))}/{len(cls_texts)}")

	df_out = df.copy()
	df_out["sentiment"] = [r["sentiment"] for r in results]
	conf_series = pd.Series([r.get("confidence", 0.6) for r in results], dtype="float64")
	df_out["sentiment_confidence"] = pd.to_numeric(conf_series, errors="coerce").fillna(0.6).clip(0, 1)
	_save_result(df_out, out_csv)
 
# ===== IndoBERT sentiment (Transformers) =====
def indobert_classify(input_csv: str, text_col: str, out_csv: str, model_name: str = "indobenchmark/indobert-base-p2", batch_size: int = 32):
	"""
	Klasifikasi sentimen offline berbasis IndoBERT (Transformers).
	- Default mencoba 'indobenchmark/indobert-base-p2'.
	- Jika checkpoint default tidak punya classification head, fallback ke model-model ID sentiment umum (otomatis).
	- Output: sentiment (positive/neutral/negative) + confidence (0..1).
	"""
	try:
		from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
		import torch
	except Exception as e:
		raise SystemExit("Transformers belum terpasang. Install dulu: pip install transformers torch --upgrade") from e

	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		if "tokens" in df.columns:
			text_col = "tokens"
		elif "comment_clean" in df.columns:
			text_col = "comment_clean"
		elif "comment" in df.columns:
			text_col = "comment"
		else:
			raise SystemExit(f"Tidak menemukan kolom teks (tokens/comment_clean/comment) di {input_csv}")
	texts = df[text_col].astype(str).tolist()

	device = 0 if torch.cuda.is_available() else -1

	# urutan fallback model (akan dipakai jika model_name gagal atau tanpa head)
	candidates = [model_name]
	# fallback populer (beberapa bukan IndoBERT murni, tapi bekerja untuk ID sentiment)
	candidates += [
		"ayameRushia/indobert-base-p1-sentiment",
		"cahya/bert-base-indonesian-1.5G-sentiment",
		"w11wo/indonesian-roberta-base-sentiment-classification"
	]

	pipeline = None
	last_err = None
	for ckpt in candidates:
		try:
			tokenizer = AutoTokenizer.from_pretrained(ckpt)
			model = AutoModelForSequenceClassification.from_pretrained(ckpt)
			pipeline = TextClassificationPipeline(model=model, tokenizer=tokenizer, device=device, return_all_scores=False)
			print(f"[IndoBERT] loaded checkpoint: {ckpt}")
			break
		except Exception as e:
			last_err = e
			continue
	if pipeline is None:
		# fallback ke leksikon bila semua gagal
		print(f"⚠️ Gagal memuat IndoBERT classifier: {last_err}. Fallback ke leksikon.")
		return lexicon_classify(input_csv, text_col, out_csv)

	def map_label(lbl_raw: str) -> str:
		s = (lbl_raw or "").strip().lower()
		# langsung cocok jika sudah standard
		if s in ("positive", "pos", "label_2"):
			return "positive"
		if s in ("negative", "neg", "label_0"):
			return "negative"
		if s in ("neutral", "neu", "label_1"):
			return "neutral"
		# coba baca dari id2label
		try:
			id2label = {int(k): v for k, v in pipeline.model.config.id2label.items()}
			lbls = [v.lower() for v in id2label.values()]
			if "neutral" in lbls:
				# mendekati standard tiga kelas
				if s in lbls:
					return s if s in ("positive","neutral","negative") else "neutral"
				# default
				return "neutral"
			# dua kelas: pilih pos/neg
			return "positive" if "pos" in s or "positive" in s else ("negative" if "neg" in s or "negative" in s else "neutral")
		except Exception:
			return "neutral"

	def infer_batch(batch_texts):
		outs = []
		# gunakan chunking manual
		for i in range(0, len(batch_texts), batch_size):
			b = batch_texts[i:i+batch_size]
			try:
				res = pipeline(b)
			except Exception:
				# bila error pada sebagian, proses satu per satu
				res = []
				for t in b:
					try:
						res.append(pipeline(t))
					except Exception:
						res.append({"label": "neutral", "score": 0.5})
			# normalisasi bentuk output: pipeline bisa return dict atau list[dict]
			for r in res:
				if isinstance(r, list) and r and isinstance(r[0], dict) and "label" in r[0]:
					r0 = max(r, key=lambda x: x.get("score", 0))
					outs.append({"label": r0["label"], "score": float(r.get("score", 0.6))})
				elif isinstance(r, dict) and "label" in r:
					outs.append({"label": r["label"], "score": float(r.get("score", 0.6))})
				else:
					outs.append({"label": "neutral", "score": 0.5})
		return outs

	raw_outputs = infer_batch(texts)
	lbls = [map_label(o.get("label")) for o in raw_outputs]
	confs = [float(o.get("score", 0.6)) for o in raw_outputs]

	df_out = df.copy()
	df_out["sentiment"] = lbls
	# bungkus dalam Series agar fillna/clip tersedia
	conf_series = pd.Series(confs, dtype="float64")
	df_out["sentiment_confidence"] = pd.to_numeric(conf_series, errors="coerce").fillna(0.6).clip(0, 1)
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Sentiment (IndoBERT) disimpan: {out_csv}")

def main():
	# pastikan seluruh blok main memakai TAB untuk konsistensi dengan file ini
	ap = argparse.ArgumentParser(description="Step 3: Sentiment Analysis (Naive Bayes / Gemini / IndoBERT)")
	# input/output
	ap.add_argument("--in", dest="infile", default=None, help="Path input CSV. Default: output/review_tokens.csv atau review_clean.csv")
	ap.add_argument("--out", dest="outfile", default=os.path.join(OUTPUT_DIR, "review_sentiment.csv"), help="Path output CSV (default: output/review_sentiment.csv)")
	ap.add_argument("--text-col", dest="text_col", default=None, help="Kolom teks (default: tokens jika ada, selain itu comment_clean)")

	# NB options
	ap.add_argument("--nb-train", dest="nb_train_csv", default=None, help="CSV data latih (wajib ada kolom label/sentiment). Menyimpan model NB.")
	ap.add_argument("--nb-model", dest="nb_model_path", default=os.path.join(OUTPUT_DIR, "sentiment_nb.joblib"), help="Path model NB (default: output/sentiment_nb.joblib)")
	ap.add_argument("--nb-predict", action="store_true", help="Jalankan prediksi NB pada --in menggunakan --nb-model")

	# Gemini options
	ap.add_argument("--gemini", action="store_true", help="Gunakan Gemini Text Classification")
	ap.add_argument("--gemini-api-key", dest="gem_api_key", default=None, help="API key (opsional, atau gunakan .env)")
	ap.add_argument("--gemini-model", dest="gem_model", default="gemini-1.5-flash", help="Nama model Gemini (default: gemini-1.5-flash)")
	ap.add_argument("--batch-size", dest="batch_size", type=int, default=20, help="Batch size Gemini (default: 20)")
	ap.add_argument("--limit", dest="limit", type=int, default=None, help="Batasi jumlah baris untuk uji coba (opsional)")
	ap.add_argument("--auto-install", action="store_true", help="Auto-install google-generativeai jika belum ada")
	ap.add_argument("--gemini-keys", dest="gem_keys", default=None, help="Daftar API key dipisah koma untuk rotasi, atau set ENV GEMINI_API_KEYS")
	ap.add_argument("--per-min-limit", dest="per_min_limit", type=int, default=15, help="Batas request/menit per key (default 15)")
	ap.add_argument("--rotate-every", dest="rotate_every", type=int, default=10, help="Ganti key setiap N request (default 10)")

	# Tambahkan opsi IndoBERT (gunakan indentasi TAB)
	ap.add_argument("--indobert", action="store_true", help="Gunakan IndoBERT sentiment model (offline)")
	ap.add_argument("--indobert-model", dest="indo_model", default="indobenchmark/indobert-base-p2", help="Nama checkpoint Transformers untuk IndoBERT sentiment")

	args = ap.parse_args()

	# Tentukan input
	infile = args.infile or _pick_input_csv(pref_tokens=True)
	df_head = pd.read_csv(infile, nrows=1, encoding="utf-8-sig")
	default_text_col = "tokens" if "tokens" in df_head.columns else ("comment_clean" if "comment_clean" in df_head.columns else None)
	text_col = args.text_col or default_text_col
	if not text_col:
		raise SystemExit("Tidak dapat menentukan kolom teks. Sertakan --text-col.")

	# Urutan prioritas sesuai flag CLI
	if getattr(args, "indobert", False):
		indobert_classify(infile, text_col, args.outfile, model_name=args.indo_model)
		return

	if getattr(args, "gemini", False):
		keys = None
		if args.gem_keys:
			keys = [k.strip() for k in args.gem_keys.split(",") if k.strip()]
		gemini_classify(
			infile,
			text_col,
			args.outfile,
			api_key=args.gem_api_key,
			api_keys=keys,
 			model=args.gem_model or "gemini-2.0-flash",
 			batch_size=args.batch_size,
 			limit=args.limit,
 			auto_install=args.auto_install,
 			rotate_every=args.rotate_every,
 			per_min_limit=args.per_min_limit,
 		)
		return

	# NAIVE BAYES path jika flag NB digunakan, atau default fallback
	if args.nb_train_csv:
		nb_train(args.nb_train_csv, args.nb_model_path)
		# otomatis prediksi setelah train bila diminta atau jika --gemini tidak dipilih
		if args.nb_predict or (not args.gemini):
			nb_predict(infile, text_col, args.nb_model_path, args.outfile)
			return

	if args.nb_predict:
		nb_predict(infile, text_col, args.nb_model_path, args.outfile)
		return

	# Jika tidak ada yang dipilih, pakai IndoBERT sebagai default (fallback terakhir ke leksikon)
	try:
		indobert_classify(infile, text_col, args.outfile, model_name=getattr(args, "indo_model", "indobenchmark/indobert-base-p2"))
		return
	except Exception:
		lexicon_classify(infile, text_col, args.outfile)

if __name__ == "__main__":
	main()
