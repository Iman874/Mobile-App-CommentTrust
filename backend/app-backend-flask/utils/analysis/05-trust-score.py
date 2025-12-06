"""05 - Trust Score Calculation

Menghitung trust_score per komentar + ringkasan produk minimal.
Fungsi publik:
	compute(input_csv: str, out_csv: str, product_json: str | None = None, product_out: str | None = None) -> str
"""

from __future__ import annotations
import os
import json
import pandas as pd
import numpy as np

def _sentiment_val(s: str) -> float:
	s = (s or "").lower()
	if s == "positive": return 1.0
	if s == "negative": return 0.0
	return 0.5

def compute(input_csv: str, out_csv: str, product_json: str | None = None, product_out: str | None = None) -> str:
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	df["likes"] = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0).astype(int)
	df["rating"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).astype(float)
	if "sentiment_confidence" in df.columns:
		df["sentiment_confidence"] = pd.to_numeric(df["sentiment_confidence"], errors="coerce").fillna(0.5).clip(0,1)
	else:
		df["sentiment_confidence"] = 0.5
	df["fake_score"] = pd.to_numeric(df.get("fake_score", df.get("suspicion_score", 0)), errors="coerce").fillna(0.0)
	df["fake_pred"] = pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0).astype(int)
	df["sentiment"] = df.get("sentiment", "neutral").fillna("neutral").astype(str)
	sent_val = df["sentiment"].apply(_sentiment_val)
	likes_term = 0.2*(1 - np.exp(-df["likes"]/10.0))
	rating_term = 0.2*(df["rating"]/5.0)
	penalty = 0.6*df["fake_pred"] + 0.3*df["fake_score"]
	raw = 0.6*sent_val + likes_term + rating_term
	trust = (raw*(1 - penalty)).clip(0,1)
	df["trust_score"] = (trust*100).round(2)
	df.to_csv(out_csv, index=False, encoding="utf-8-sig")

	# ringkasan produk minimal
	n = len(df)
	fake_rate = float((df["fake_pred"]>0).mean()) if n else 0.0
	avg_trust = float(df["trust_score"].mean()) if n else 0.0
	avg_rating = float(df["rating"].mean()) if n else 0.0
	product_obj = None
	if product_json and os.path.exists(product_json):
		try:
			product_obj = json.load(open(product_json, "r", encoding="utf-8"))
		except Exception:
			product_obj = None
	summary = {
		"product": product_obj.get("name") if isinstance(product_obj, dict) else None,
		"metrics": {
			"count_reviews": n,
			"fake_rate": round(fake_rate,4),
			"avg_trust_score": round(avg_trust,2),
			"avg_rating": round(avg_rating,2)
		}
	}
	if product_out:
		with open(product_out, "w", encoding="utf-8") as f:
			json.dump(summary, f, ensure_ascii=False, indent=2)
	return out_csv

