"""03 - Sentiment Analysis (Light)

Versi ringan: lexicon rule-based. Dapat diperluas (IndoBERT, Gemini) nanti.
Fungsi publik:
	classify(input_csv: str, output_csv: str, text_col: str | None = None) -> str
"""

from __future__ import annotations
import pandas as pd

POS = {"bagus","keren","mantap","cepat","recommended","puas","cocok","tebal","rapi","sesuai"}
NEG = {"jelek","lama","buruk","tipis","rusak","mengecewakan","tidak","kurang"}

def _lexicon_label(text: str):
	toks = set((text or "").lower().split())
	sp = len(toks & POS); sn = len(toks & NEG)
	if sp > sn and sp > 0: return "positive", 0.75
	if sn > sp and sn > 0: return "negative", 0.75
	return "neutral", 0.55

def classify(input_csv: str, output_csv: str, text_col: str | None = None) -> str:
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if not text_col:
		text_col = "tokens" if "tokens" in df.columns else ("comment_clean" if "comment_clean" in df.columns else "comment")
	labels, confs = [], []
	for s in df[text_col].astype(str).tolist():
		lab, c = _lexicon_label(s)
		labels.append(lab); confs.append(c)
	df["sentiment"] = labels
	df["sentiment_confidence"] = confs
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	return output_csv

