import os
import json
import argparse
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _sentiment_val(s: str) -> float:
	s = (s or "").lower()
	if s == "positive": return 1.0
	if s == "negative": return 0.0
	return 0.5

def _sanitize_inputs(df: pd.DataFrame) -> pd.DataFrame:
	df = df.copy()
	# numeric defaults
	df["likes"] = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0).astype(int)
	df["rating"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).astype(float)
	# sentiment_confidence in [0,1], default 0.5
	if "sentiment_confidence" in df.columns:
		df["sentiment_confidence"] = pd.to_numeric(df["sentiment_confidence"], errors="coerce").fillna(0.5).clip(0,1)
	else:
		df["sentiment_confidence"] = 0.5
	# fake_score fallback dari suspicion_score bila ada
	if "fake_score" not in df.columns and "suspicion_score" in df.columns:
		df["fake_score"] = pd.to_numeric(df["suspicion_score"], errors="coerce").fillna(0.0)
	else:
		df["fake_score"] = pd.to_numeric(df.get("fake_score", 0), errors="coerce").fillna(0.0)
	# fake_pred biner
	df["fake_pred"] = pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0).astype(int)
	# sentiment label default neutral
	if "sentiment" in df.columns:
		df["sentiment"] = df["sentiment"].fillna("neutral").astype(str)
	else:
		df["sentiment"] = "neutral"
	return df

def compute_trust(df: pd.DataFrame) -> pd.DataFrame:
	df = _sanitize_inputs(df)
	# nilai dasar dari sentiment
	df["sentiment_val"] = df.get("sentiment", "").apply(_sentiment_val)
	# faktor likes (0..0.2)
	likes = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0)
	df["likes_term"] = 0.2*(1 - np.exp(-likes/10.0))
	# faktor rating (0..0.2)
	rating = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0)
	df["rating_term"] = 0.2*(rating/5.0)
	# penalti fake
	fake_pred = pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0)
	fake_score = pd.to_numeric(df.get("fake_score", df.get("suspicion_score", 0)), errors="coerce").fillna(0)
	penalty = 0.6*fake_pred + 0.3*fake_score  # 0..0.9
	# skor total
	raw = (0.6*df["sentiment_val"] + df["likes_term"] + df["rating_term"])
	trust = raw*(1 - penalty).clip(0, 1)
	df["trust_score"] = (trust*100).round(2)
	return df

def product_summary(df: pd.DataFrame, product: dict | None = None) -> dict:
	n = len(df)
	fake_rate = float((pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0) > 0).mean()) if n else 0.0
	avg_trust = float(pd.to_numeric(df.get("trust_score", 0), errors="coerce").fillna(0).mean()) if n else 0.0
	avg_rating = float(pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).mean()) if n else 0.0
	# sentiment distribution
	sent_series = df.get("sentiment", pd.Series(["neutral"] * n)).astype(str).str.lower()
	sent_dist = sent_series.value_counts(normalize=True).to_dict() if n else {}
	sent_val = sent_series.apply(_sentiment_val) if n else pd.Series([])
	avg_sentiment = float(sent_val.mean()) if n else 0.0
	metrics = {
		"count_reviews": n,
		"fake_rate": round(fake_rate, 4),
		"avg_trust_score": round(avg_trust, 2),
		"avg_rating": round(avg_rating, 2),
		"avg_sentiment": round(avg_sentiment, 3),
		"sentiment_distribution": {k: round(float(v), 4) for k, v in sent_dist.items()},
		"fake_count": int((pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0) > 0).sum()),
	}
	product_info = None
	if isinstance(product, dict):
		ir = product.get("item_rating") or {}
		product_info = {
			"name": product.get("name"),
			"itemid": product.get("itemid"),
			"shopid": product.get("shopid"),
			"rating_star": ir.get("rating_star"),
			"rating_count": ir.get("rating_count"),
			"cmt_count": product.get("cmt_count"),
			"historical_sold": product.get("historical_sold"),
			"price_min": product.get("price_min"),
			"price_max": product.get("price_max"),
			"shop_location": product.get("shop_location"),
			"is_preferred_plus_seller": product.get("is_preferred_plus_seller"),
			"images_count": len(product.get("images", []) or []),
			"models_count": len(product.get("models", []) or []),
		}
	return {"product": product_info, "metrics": metrics}

def main():
	ap = argparse.ArgumentParser(description="Step 5: Trust Score Calculation")
	# input/output
	ap.add_argument("--in", dest="infile", default=None, help="Input CSV (default: output/review_fake.csv lalu fallback ke review_sentiment.csv)")
	ap.add_argument("--out", dest="outfile", default=os.path.join(OUTPUT_DIR, "review_trust.csv"), help="Output per-review (default: output/review_trust.csv)")
	ap.add_argument("--product-out", dest="product_out", default=os.path.join(OUTPUT_DIR, "product_trust.json"), help="Output ringkasan produk (JSON)")
	ap.add_argument("--product-json", dest="product_json", default=os.path.join(SCRAPPER_DIR, "produk.json"), help="Path produk.json untuk metadata produk (opsional)")
	args = ap.parse_args()

	infile = args.infile or (os.path.join(OUTPUT_DIR, "review_fake.csv") if os.path.exists(os.path.join(OUTPUT_DIR, "review_fake.csv")) else os.path.join(OUTPUT_DIR, "review_sentiment.csv"))
	if not os.path.exists(infile):
		raise SystemExit(f"Input tidak ditemukan: {infile}")

	df = pd.read_csv(infile, encoding="utf-8-sig")
	df_out = compute_trust(df)
	df_out.to_csv(args.outfile, index=False, encoding="utf-8-sig")
	print(f"✅ Trust per-review disimpan: {args.outfile}")

	# load produk.json (opsional) untuk memperkaya ringkasan produk
	product = None
	if args.product_json and os.path.exists(args.product_json):
		try:
			with open(args.product_json, "r", encoding="utf-8") as f:
				product = json.load(f)
		except Exception:
			product = None
	summary = product_summary(df_out, product=product)
	with open(args.product_out, "w", encoding="utf-8") as f:
		json.dump(summary, f, ensure_ascii=False, indent=2)
	print(f"✅ Ringkasan produk disimpan: {args.product_out}\n{summary}")

if __name__ == "__main__":
	main()
