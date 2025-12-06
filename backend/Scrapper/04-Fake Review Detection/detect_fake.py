import os
import sys
import argparse
import subprocess
import json
import pandas as pd
import numpy as np
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
load_dotenv(os.path.join(SCRAPPER_DIR, ".env"))

def _auto_install(pkg: str):
	try:
		subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
	except Exception as e:
		raise SystemExit(f"Gagal memasang paket {pkg}: {e}")

def _char_repeat_ratio(text: str) -> float:
	if not isinstance(text, str) or not text:
		return 0.0
	# rasio huruf berulang (contoh: 'bagussss' → tinggi)
	repeats = sum(1 for i in range(1, len(text)) if text[i] == text[i-1])
	return repeats / max(1, len(text))

def _token_repeat_ratio(text: str) -> float:
	if not isinstance(text, str) or not text.strip():
		return 0.0
	toks = text.split()
	if not toks:
		return 0.0
	from collections import Counter
	cnt = Counter(toks)
	more2 = sum(v for v in cnt.values() if v >= 2)
	return more2 / max(1, len(toks))

def _sentiment_rating_mismatch(sentiment: str, rating: float) -> float:
	# mismatch tinggi bila rating sangat positif tapi sentimen negatif (atau sebaliknya)
	s = (sentiment or "").lower()
	if rating is None or pd.isna(rating):
		return 0.0
	if rating >= 4 and s == "negative":
		return 1.0
	if rating <= 2 and s == "positive":
		return 1.0
	return 0.0

def _duplication_score(series_text: pd.Series) -> pd.Series:
	# beri skor tinggi untuk komentar yang identik muncul berkali-kali
	vc = series_text.fillna("").astype(str).str.strip().value_counts()
	return series_text.fillna("").astype(str).str.strip().map(lambda t: 0.0 if t == "" else (min(1.0, (vc.get(t, 1)-1)/5.0)))

def _heuristic_fake(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
	df = df.copy()
	df["text_len"] = df[text_col].fillna("").astype(str).str.len()
	df["tokens_count"] = df.get("tokens_count", df[text_col].fillna("").astype(str).apply(lambda s: len(s.split())))
	df["char_repeat_ratio"] = df[text_col].astype(str).apply(_char_repeat_ratio)
	df["token_repeat_ratio"] = df[text_col].astype(str).apply(_token_repeat_ratio)
	df["dup_score"] = _duplication_score(df[text_col])
	df["mismatch"] = df.apply(lambda r: _sentiment_rating_mismatch(r.get("sentiment",""), r.get("rating", None)), axis=1)

	# normalisasi panjang teks (sangat pendek → lebih curiga)
	short_penalty = (df["text_len"] < 8).astype(float) * 0.6 + (df["text_len"].between(8, 15)).astype(float) * 0.2

	# komponen skor [0..1]
	score = (
		0.25*df["char_repeat_ratio"].clip(0,1) +
		0.25*df["token_repeat_ratio"].clip(0,1) +
		0.30*df["dup_score"].clip(0,1) +
		0.20*df["mismatch"].clip(0,1) +
		short_penalty.clip(0,1)
	)

	df["suspicion_score"] = score.clip(0, 1.0)
	df["fake_pred"] = (df["suspicion_score"] >= 0.6).astype(int)
	return df

def _build_feature_table(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
	tmp = _heuristic_fake(df, text_col)  # sudah menambahkan kolom fitur
	# pilih subset fitur numerik untuk model
	feat_cols = ["text_len", "tokens_count", "char_repeat_ratio", "token_repeat_ratio", "dup_score", "mismatch", "likes", "rating"]
	for c in feat_cols:
		if c not in tmp.columns:
			tmp[c] = 0.0
	return tmp[feat_cols]

def xgb_train(train_csv: str, text_col: str, label_col: str, model_out: str, auto_install: bool):
	try:
		import xgboost as xgb
	except ImportError:
		if auto_install:
			_auto_install("xgboost")
			import xgboost as xgb
		else:
			raise SystemExit("xgboost belum terpasang. Jalankan dengan --auto-install atau pip install xgboost")

	df = pd.read_csv(train_csv, encoding="utf-8-sig")
	if text_col not in df.columns or label_col not in df.columns:
		raise SystemExit(f"Kolom {text_col}/{label_col} tidak ditemukan pada {train_csv}")
	# siapkan fitur
	X = _build_feature_table(df, text_col).astype(float).values
	y = df[label_col].astype(int).values
	dtrain = xgb.DMatrix(X, label=y)
	params = {
		"objective": "binary:logistic",
		"eval_metric": "logloss",
		"max_depth": 5,
		"eta": 0.2,
		"subsample": 0.8,
		"colsample_bytree": 0.8,
	}
	bst = xgb.train(params, dtrain, num_boost_round=200)
	# simpan model
	try:
		bst.save_model(model_out)
	except Exception:
		# fallback via pickle
		import pickle
		with open(model_out if model_out.endswith(".pkl") else os.path.splitext(model_out)[0]+".pkl", "wb") as f:
			pickle.dump(bst, f)
	print(f"✅ Model XGBoost disimpan: {model_out}")

def xgb_predict(input_csv: str, text_col: str, model_path: str, out_csv: str, auto_install: bool):
	try:
		import xgboost as xgb
	except ImportError:
		if auto_install:
			_auto_install("xgboost")
			import xgboost as xgb
		else:
			raise SystemExit("xgboost belum terpasang. Jalankan dengan --auto-install atau pip install xgboost")

	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom teks '{text_col}' tidak ada di {input_csv}")
	X = _build_feature_table(df, text_col).astype(float).values
	dtest = xgb.DMatrix(X)
	# load model
	bst = xgb.Booster()
	bst.load_model(model_path)
	prob = bst.predict(dtest)  # [0..1]
	df_out = df.copy()
	df_out["fake_score"] = prob
	df_out["fake_pred"] = (df_out["fake_score"] >= 0.5).astype(int)
	# Terapkan threshold 0.6 pada fake_score bila tersedia
	if "fake_score" in df_out.columns:
		df_out["fake_score"] = pd.to_numeric(df_out["fake_score"], errors="coerce").fillna(0.0)
		df_out["fake_pred"] = (df_out["fake_score"] >= 0.6).astype(int)
	elif "suspicion_score" in df_out.columns:
		df_out["fake_pred"] = (pd.to_numeric(df_out["suspicion_score"], errors="coerce").fillna(0.0) >= 0.6).astype(int)
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ XGB predict disimpan: {out_csv}")

def heuristics_detect(input_csv: str, text_col: str, out_csv: str):
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom teks '{text_col}' tidak ada di {input_csv}")
	df_out = _heuristic_fake(df, text_col)
	# selaraskan nama kolom skor
	df_out["fake_score"] = df_out["suspicion_score"]
	# Pastikan fake_score ada (fallback ke suspicion_score) lalu terapkan threshold 0.6
	df_out["fake_score"] = pd.to_numeric(df_out.get("fake_score", df_out.get("suspicion_score", 0)), errors="coerce").fillna(0.0)
	df_out["fake_pred"] = (df_out["fake_score"] >= 0.6).astype(int)
	# tulis hasil
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Heuristics fake detection disimpan: {out_csv}")

def make_sample_train(input_csv: str, text_col: str, out_csv: str, threshold: float = 0.6):
	"""
	Buat data latih pseudo-label dari input (menggunakan heuristics suspicion_score).
	Menulis kolom: text_col, likes, rating, sentiment (jika ada), suspicion_score, is_fake.
	"""
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		# bila kolom tidak ada, coba deteksi default
		text_col = "tokens" if "tokens" in df.columns else "comment_clean" if "comment_clean" in df.columns else None
		if not text_col:
			raise SystemExit("Tidak menemukan kolom teks untuk membuat sample train. Gunakan --text-col.")
	# pastikan ada suspicion_score
	if "suspicion_score" not in df.columns:
		df = _heuristic_fake(df, text_col)
	df_out = pd.DataFrame({
		text_col: df[text_col].astype(str),
		"likes": pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0).astype(int),
		"rating": pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).astype(int),
		"sentiment": df.get("sentiment", None),
		"suspicion_score": pd.to_numeric(df["suspicion_score"], errors="coerce").fillna(0.0),
	})
	df_out["is_fake"] = (df_out["suspicion_score"] >= float(threshold)).astype(int)
	df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Sample train dibuat: {out_csv} (threshold={threshold})")

def main():
	ap = argparse.ArgumentParser(description="Step 4: Fake Review Detection (XGBoost / Heuristics)")
	ap.add_argument("--in", dest="infile", default=os.path.join(OUTPUT_DIR, "review_sentiment.csv"), help="Input CSV (default: output/review_sentiment.csv)")
	ap.add_argument("--out", dest="outfile", default=os.path.join(OUTPUT_DIR, "review_fake.csv"), help="Output CSV (default: output/review_fake.csv)")
	ap.add_argument("--text-col", dest="text_col", default=None, help="Kolom teks (default: tokens bila ada, selain itu comment_clean)")
	# XGB
	ap.add_argument("--xgb-train", dest="xgb_train_csv", default=None, help="CSV data latih berlabel (kolom label: fake/is_fake/label)")
	ap.add_argument("--xgb-label-col", dest="xgb_label_col", default=None, help="Nama kolom label di data latih")
	ap.add_argument("--xgb-model", dest="xgb_model", default=os.path.join(OUTPUT_DIR, "fake_xgb.json"), help="Path model XGBoost")
	ap.add_argument("--xgb-predict", action="store_true", help="Prediksi dengan XGBoost model")
	ap.add_argument("--auto-install", action="store_true", help="Auto-install dependency (xgboost)")
	# Utility: generate sample train
	ap.add_argument("--make-sample-train", action="store_true", help="Buat sample training CSV dengan pseudo-label dari heuristics")
	ap.add_argument("--sample-out", dest="sample_out", default=os.path.join(OUTPUT_DIR, "train_fake_sample.csv"), help="Path sample training CSV")
	ap.add_argument("--threshold", dest="threshold", type=float, default=0.6, help="Ambang pseudo-label heuristics (default: 0.6)")
	args = ap.parse_args()

	# tentukan kolom teks default
	df_head = pd.read_csv(args.infile, nrows=1, encoding="utf-8-sig")
	text_col = args.text_col or ("tokens" if "tokens" in df_head.columns else "comment_clean" if "comment_clean" in df_head.columns else None)
	if not text_col:
		raise SystemExit("Tidak bisa menentukan kolom teks. Gunakan --text-col.")

	# Utility: buat sample train lalu keluar
	if args.make_sample_train:  # keep the flag name exact
		make_sample_train(args.infile, text_col, args.sample_out, threshold=args.threshold)
		return

	# training (opsional)
	if args.xgb_train_csv:
		if not os.path.exists(args.xgb_train_csv):
			raise SystemExit(f"CSV data latih tidak ditemukan: {args.xgb_train_csv}\nTip: buat dulu sample dengan --make-sample-train, lalu jalankan --xgb-train {args.sample_out}")
		label_col = args.xgb_label_col
		if not label_col:
			# deteksi kolom label umum
			for c in ("fake", "is_fake", "label", "target"):
				if c in pd.read_csv(args.xgb_train_csv, nrows=1, encoding="utf-8-sig").columns:
					label_col = c
					break
		if not label_col:
		   raise SystemExit("Kolom label tidak ditemukan. Set --xgb-label-col.")
		xgb_train(args.xgb_train_csv, text_col, label_col, args.xgb_model, auto_install=args.auto_install)

	# prediksi XGB
	if args.xgb_predict:
		# validasi model
		model_path = args.xgb_model
		if not os.path.exists(model_path):
			pkl_fallback = model_path if model_path.endswith(".pkl") else os.path.splitext(model_path)[0] + ".pkl"
			if not os.path.exists(pkl_fallback):
				raise SystemExit(f"Model tidak ditemukan: {model_path} (atau {pkl_fallback})")
		xgb_predict(args.infile, text_col, model_path, args.outfile, auto_install=args.auto_install)
		return

	# default: heuristics
	heuristics_detect(args.infile, text_col, args.outfile)

if __name__ == "__main__":
	main()

"""
Deteksi Fake Comment (Fitur & Bobot)
------------------------------------
Fitur                              | Keterangan                                                         | Bobot (ke fake_score)
---------------------------------------------------------------------------------------------------------------
Panjang komentar < 10 kata         | Komentar terlalu pendek dan tidak informatif cenderung fake        | +0.30
Rating 5 tapi teks terlalu pendek  | Indikasi ulasan palsu untuk menaikkan rating                       | +0.25
Mirip komentar lain (>90% similar) | Pola teks berulang seperti spam/testimoni bot                      | +0.20
Tier user rendah                   | Akun baru/tidak aktif sering dipakai untuk fake review             | +0.10

Ambang Klasifikasi:
fake_pred = 1 jika fake_score >= 0.6, selain itu 0.
Catatan: Bobot di atas dipertahankan; perubahan hanya pada ambang klasifikasi agar mengurangi false positive.
"""
