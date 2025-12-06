"""04 - Fake Review Detection (Heuristics)

Menciptakan kolom fake_score (0..1) + fake_pred (>= threshold).
Fungsi publik:
	detect(input_csv: str, output_csv: str, text_col: str | None = None, threshold: float = 0.6) -> str
"""

from __future__ import annotations
import pandas as pd
from collections import Counter

def _char_repeat_ratio(text: str) -> float:
	if not isinstance(text, str) or not text:
		return 0.0
	repeats = sum(1 for i in range(1, len(text)) if text[i] == text[i-1])
	return repeats / max(1, len(text))

def _token_repeat_ratio(text: str) -> float:
	if not isinstance(text, str) or not text.strip():
		return 0.0
	toks = text.split()
	cnt = Counter(toks)
	more2 = sum(v for v in cnt.values() if v >= 2)
	return more2 / max(1, len(toks))

def _sentiment_rating_mismatch(sentiment: str, rating) -> float:
	s = (sentiment or "").lower()
	try:
		r = float(rating)
	except Exception:
		r = None
	if r is None:
		return 0.0
	if r >= 4 and s == "negative": return 1.0
	if r <= 2 and s == "positive": return 1.0
	return 0.0

def detect(input_csv: str, output_csv: str, text_col: str | None = None, threshold: float = 0.6) -> str:
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if not text_col:
		text_col = "tokens" if "tokens" in df.columns else ("comment_clean" if "comment_clean" in df.columns else "comment")
	df["text_len"] = df[text_col].fillna("").astype(str).str.len()
	df["tokens_count"] = df.get("tokens_count", df[text_col].fillna("").astype(str).apply(lambda s: len(s.split())))
	df["char_repeat_ratio"] = df[text_col].astype(str).apply(_char_repeat_ratio)
	df["token_repeat_ratio"] = df[text_col].astype(str).apply(_token_repeat_ratio)
	vc = df[text_col].fillna("").astype(str).str.strip().value_counts()
	df["dup_score"] = df[text_col].fillna("").astype(str).str.strip().map(lambda t: 0.0 if t == "" else (min(1.0, (vc.get(t,1)-1)/5.0)))
	mismatch_series = df.apply(lambda r: _sentiment_rating_mismatch(r.get("sentiment",""), r.get("rating", None)), axis=1)
	if hasattr(mismatch_series, "ndim") and getattr(mismatch_series, "ndim", 1) > 1:
		try:
			mismatch_series = mismatch_series.iloc[:,0]
		except Exception:
			mismatch_series = pd.Series([0.0]*len(df))
	df["mismatch"] = pd.to_numeric(mismatch_series, errors="coerce").fillna(0.0)
	short_penalty = (df["text_len"] < 8).astype(float)*0.6 + (df["text_len"].between(8,15)).astype(float)*0.2
	score = (0.25*df["char_repeat_ratio"].clip(0,1) + 0.25*df["token_repeat_ratio"].clip(0,1) + 0.30*df["dup_score"].clip(0,1) + 0.20*df["mismatch"].clip(0,1) + short_penalty.clip(0,1))
	df["fake_score"] = score.clip(0,1)
	df["fake_pred"] = (df["fake_score"] >= float(threshold)).astype(int)
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	return output_csv

