"""02 - Text Preprocessing

Membersihkan kolom comment menjadi comment_clean.
Fungsi publik:
	preprocess(input_csv: str, output_csv: str) -> str
"""

from __future__ import annotations
import re
import pandas as pd

def _clean_text(text: str) -> str:
	if not isinstance(text, str):
		return ""
	text = text.lower()
	text = re.sub(r"http\S+|www\S+", "", text)
	text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text

def preprocess(input_csv: str, output_csv: str) -> str:
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if "comment" not in df.columns:
		df["comment"] = ""
	df["comment_clean"] = df["comment"].astype(str).apply(_clean_text)
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	return output_csv

