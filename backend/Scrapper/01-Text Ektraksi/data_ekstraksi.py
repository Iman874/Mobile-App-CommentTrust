import os
import json
import argparse
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def _ts_to_iso(ts):
	try:
		if ts is None:
			return ""
		ts = float(ts)
		if ts > 1e12:
			ts /= 1000.0
		return datetime.fromtimestamp(ts).isoformat(sep=" ", timespec="seconds")
	except Exception:
		return ""

def _first(lst, key):
	try:
		return (lst or [{}])[0].get(key, "")
	except Exception:
		return ""

def normalize_review(r: dict) -> dict:
	return {
		"username": r.get("author_username", ""),
		"comment": r.get("comment", ""),
		"rating": r.get("rating_star", 0),
		"likes": r.get("like_count", 0),
		"member_tier": (r.get("loyalty_info") or {}).get("tier_text", ""),
		"product_name": (r.get("original_item_info") or {}).get("name", "") or _first(r.get("product_items") or [], "name") or _first(r.get("product_items") or [], "model_name"),
		"model_name": _first(r.get("product_items") or [], "model_name"),
		"variant_name": _first(r.get("product_items") or [], "name"),
		"images_count": len(r.get("images") or []),
		"videos_count": len(r.get("videos") or []),
		"shop_reply": r.get("shop_reply", ""),
		"create_time": _ts_to_iso(r.get("ctime")),
		"orderid": r.get("orderid", ""),
		"userid": r.get("userid", ""),
	}

def load_reviews(path: str):
	with open(path, "r", encoding="utf-8") as f:
		data = json.load(f)
	if isinstance(data, list):
		return data
	if isinstance(data, dict) and isinstance(data.get("data"), list):
		return data["data"]
	raise ValueError("Unsupported JSON format: expected list of ratings or {'data': [...]}")

def to_dataframe(reviews_json: list) -> pd.DataFrame:
	rows = [normalize_review(r or {}) for r in reviews_json]
	return pd.DataFrame(rows)

def main():
	ap = argparse.ArgumentParser(description="Ekstraksi review.json → CSV/XLSX")
	ap.add_argument("--in", dest="infile", default=os.path.join(SCRAPPER_DIR, "review.json"), help="Path input JSON (default: review.json di folder Scrapper)")
	ap.add_argument("--out-csv", dest="out_csv", default=os.path.join(OUTPUT_DIR, "review.csv"), help="Path output CSV (default: output/review.csv)")
	ap.add_argument("--out-xlsx", dest="out_xlsx", default=None, help="Path output XLSX (opsional)")
	args = ap.parse_args()

	revs = load_reviews(args.infile)
	df = to_dataframe(revs)

	df.to_csv(args.out_csv, index=False, encoding="utf-8-sig")
	print(f"✅ CSV disimpan: {args.out_csv}")
	if args.out_xlsx:
		df.to_excel(args.out_xlsx, index=False)
		print(f"✅ XLSX disimpan: {args.out_xlsx}")
	print(df.head(5))

if __name__ == "__main__":
	main()