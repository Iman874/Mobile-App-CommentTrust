"""01 - Text Extraction

Tujuan: Mengubah sumber `review.json` menjadi `review-<product_id>.csv` berisi kolom dasar.
Digunakan di API pipeline sebelum preprocessing.

Fungsi publik:
	extract_review_json(json_path: str, out_csv: str) -> str
"""

from __future__ import annotations
import os
import json
import pandas as pd

def extract_review_json(json_path: str, out_csv: str) -> str:
	if not os.path.exists(json_path):
		# buat csv kosong agar tahap berikut tetap jalan
		df_empty = pd.DataFrame(columns=["username","comment","rating","likes","create_time"])
		df_empty.to_csv(out_csv, index=False, encoding="utf-8-sig")
		return out_csv
	with open(json_path, "r", encoding="utf-8") as f:
		obj = json.load(f)
	if isinstance(obj, dict) and "data" in obj and isinstance(obj["data"], dict) and "ratings" in obj["data"]:
		revs = obj["data"]["ratings"] or []
	elif isinstance(obj, list):
		revs = obj
	else:
		revs = []
	rows = []
	for r in revs:
		rows.append({
			"username": r.get("author_username") or r.get("author_shopid") or "",
			"comment": r.get("comment") or "",
			"rating": r.get("rating_star") or r.get("rating") or None,
			"likes": r.get("like_count") or r.get("like") or 0,
			"create_time": r.get("mtime") or r.get("ctime") or r.get("create_time")
		})
	df = pd.DataFrame(rows)
	df["comment"] = df["comment"].fillna("").astype(str)
	df["rating"] = pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).astype(int)
	df["likes"] = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0).astype(int)
	df.to_csv(out_csv, index=False, encoding="utf-8-sig")
	return out_csv

