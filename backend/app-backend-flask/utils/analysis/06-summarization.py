"""06 - Summarization (Data-driven)

Ringkasan positif/negatif + daftar pros/cons sederhana dari hasil trust.
Fungsi publik:
	summarize(trust_csv: str, out_json: str) -> dict
"""

from __future__ import annotations
import os
import json
import pandas as pd
from collections import Counter
import re

STOPWORDS = {"yg","yang","buat","untuk","itu","dan","di","ke","dengan","ada","jadi","sangat","banget","real","pict","aja","juga","udah","sih","saja","serta","atau","kan","nih","lah","warna","hitam","abu","merah","biru","putih","produk","barang","tas"}

def _top_words(texts, n=10):
	c = Counter()
	for t in texts:
		toks = [w for w in re.findall(r"[a-zA-Z]{2,}", str(t).lower()) if w not in STOPWORDS]
		c.update(toks)
	return [w for w,_ in c.most_common(n)]

def summarize(trust_csv: str, out_json: str) -> dict:
	df = pd.read_csv(trust_csv, encoding="utf-8-sig")
	txt_col = "comment_clean" if "comment_clean" in df.columns else "comment"
	sent = df.get("sentiment", "neutral").astype(str).str.lower()
	pos_texts = df.loc[sent.eq("positive"), txt_col].astype(str).tolist()
	neg_texts = df.loc[sent.eq("negative"), txt_col].astype(str).tolist()
	pros = _top_words(pos_texts, n=5)
	cons = _top_words(neg_texts, n=5)
	result = {
		"positive_summary": "Ulasan positif menyoroti: " + ", ".join(pros[:5]) if pros else "",
		"negative_summary": "Ulasan negatif menyoroti: " + ", ".join(cons[:5]) if cons else "",
		"pros": pros,
		"cons": cons
	}
	with open(out_json, "w", encoding="utf-8") as f:
		json.dump(result, f, ensure_ascii=False, indent=2)
	return result

