import os
import argparse
import pandas as pd
from dotenv import load_dotenv
import json

# Lokasi folder output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
# load .env if present
load_dotenv(os.path.join(SCRAPPER_DIR, ".env"))

def simple_tokenize(text: str):
	# input sudah dibersihkan di review_clean.csv
	if not isinstance(text, str):
		return []
	# split by whitespace cukup, karena sudah clean-lowercase-stem
	return [t for t in text.strip().split() if t]

def build_tokens(input_csv: str, output_csv: str, text_col: str = "comment_clean"):
	print(f"Membaca: {input_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom '{text_col}' tidak ditemukan di {input_csv}")

	# Tokenisasi
	tokens_list = df[text_col].astype(str).apply(simple_tokenize)
	df_out = df.copy()
	df_out["tokens"] = tokens_list.apply(lambda xs: " ".join(xs))
	df_out["tokens_count"] = tokens_list.apply(len)

	# Simpan
	df_out.to_csv(output_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Tokens disimpan: {output_csv}")
	print(df_out[[text_col, "tokens", "tokens_count"]].head(5))

def _save_vectors_parquet_or_csv(df: pd.DataFrame, out_parquet: str):
	"""
	Try saving to Parquet (prefer pyarrow with explicit schema for list<float>).
	Fallback to CSV if engines are unavailable or fail.
	"""
	# 1) Try pyarrow with explicit list<float32> type for embeddings
	try:
		import pyarrow as pa
		import pyarrow.parquet as pq

		# prepare columns
		texts = df["text"].astype(str).tolist() if "text" in df.columns else []
		embs_col = None
		if "embedding" in df.columns:
			raw_embs = df["embedding"].tolist()
			# ensure list of python floats
			embs = []
			for row in raw_embs:
				if hasattr(row, "tolist"):
					row = row.tolist()
				elif isinstance(row, (tuple, list)):
					row = list(row)
				else:
					# last resort try to load from json string
					try:
						row = json.loads(row)
					except Exception:
						row = []
				embs.append([float(x) for x in row])
			embs_col = pa.array(embs, type=pa.list_(pa.float32()))

		columns = {}
		if texts:
			columns["text"] = pa.array(texts, type=pa.string())
		if embs_col is not None:
			columns["embedding"] = embs_col

		# include any other scalar columns (optional)
		for col in df.columns:
			if col in ("text", "embedding"):
				continue
			series = df[col]
			# only take simple dtypes
			if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_string_dtype(series) or pd.api.types.is_bool_dtype(series):
				columns[col] = pa.array(series.tolist())

		table = pa.table(columns)
		pq.write_table(table, out_parquet)
		print(f"✅ Embeddings disimpan (Parquet): {out_parquet} (rows={len(df)})")
		return
	except Exception as e:
		# Continue to next attempt
		print(f"ℹ️ pyarrow write_table gagal atau tidak tersedia: {e}")

	# 2) Try pandas.to_parquet (engine auto) — may work if pyarrow installed
	try:
		df.to_parquet(out_parquet, index=False)
		print(f"✅ Embeddings disimpan (Parquet via pandas): {out_parquet} (rows={len(df)})")
		return
	except Exception as e:
		print(f"ℹ️ pandas.to_parquet gagal: {e}")

	# 3) Fallback CSV (serialize embedding as JSON)
	csv_path = os.path.splitext(out_parquet)[0] + ".csv"
	df_csv = df.copy()
	if "embedding" in df_csv.columns:
		df_csv["embedding"] = df_csv["embedding"].apply(
			lambda v: json.dumps(v.tolist() if hasattr(v, "tolist") else (list(v) if isinstance(v, (list, tuple)) else json.loads(v) if isinstance(v, str) else []))
		)
	df_csv.to_csv(csv_path, index=False, encoding="utf-8-sig")
	print("⚠️ Semua metode Parquet gagal. Menyimpan fallback CSV.")
	print(f"✅ Embeddings disimpan (CSV): {csv_path} (rows={len(df)})")
	print("ℹ️ Instal pyarrow untuk dukungan Parquet yang andal: pip install pyarrow")

def embed_bert(input_csv: str, out_parquet: str, text_col: str = "comment_clean", model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", batch_size: int = 64):
	from sentence_transformers import SentenceTransformer
	import numpy as np

	print(f"Embedding BERT: {input_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom '{text_col}' tidak ditemukan di {input_csv}")

	model = SentenceTransformer(model_name)
	emb = model.encode(df[text_col].astype(str).tolist(), batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

	df_emb = pd.DataFrame({
		"text": df[text_col].astype(str).tolist(),
		"embedding": list(emb.astype(float))  # list of arrays
	})
	# Simpan dengan fallback ke CSV bila engine parquet tidak tersedia/bermasalah
	_save_vectors_parquet_or_csv(df_emb, out_parquet)

def embed_gemini(input_csv: str, out_parquet: str, text_col: str = "comment_clean", api_key: str = None, batch_size: int = 64, model_name: str = "models/text-embedding-004"):
	import os
	import pandas as pd
	import google.generativeai as genai

	# Cari kunci di argumen, lalu .env/ENV: GEMINI_API_KEY atau GOOGLE_API_KEY
	key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
	if not key:
		raise SystemExit("GEMINI_API_KEY / GOOGLE_API_KEY tidak ditemukan. Set di .env atau gunakan --gemini-api-key.")
	genai.configure(api_key=key)

	print(f"Embedding Gemini: {input_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")
	if text_col not in df.columns:
		raise SystemExit(f"Kolom '{text_col}' tidak ditemukan di {input_csv}")

	texts = df[text_col].astype(str).tolist()
	embeddings = []

	# batching
	for i in range(0, len(texts), batch_size):
		batch = texts[i:i+batch_size]
		resp = genai.embed_content(model=model_name, content=batch)
		vecs = resp["embedding"] if "embedding" in resp else resp["embeddings"]
		# adapt when API returns list of dicts
		if isinstance(vecs, list) and isinstance(vecs[0], dict) and "values" in vecs[0]:
			vecs = [v["values"] for v in vecs]
		embeddings.extend(vecs)

	df_emb = pd.DataFrame({
		"text": texts,
		"embedding": embeddings
	})
	# Simpan dengan fallback ke CSV bila engine parquet tidak tersedia/bermasalah
	_save_vectors_parquet_or_csv(df_emb, out_parquet)

def main():
	ap = argparse.ArgumentParser(description="Tokenisasi review_clean.csv dan opsional pembuatan embeddings.")
	ap.add_argument("--in", dest="infile", default=os.path.join(OUTPUT_DIR, "review_clean.csv"), help="Path input CSV (default: output/review_clean.csv)")
	ap.add_argument("--out", dest="outfile", default=os.path.join(OUTPUT_DIR, "review_tokens.csv"), help="Path output tokens CSV (default: output/review_tokens.csv)")
	ap.add_argument("--text-col", dest="text_col", default="comment_clean", help="Nama kolom teks (default: comment_clean)")

	ap.add_argument("--bert", action="store_true", help="Jalankan embedding BERT")
	ap.add_argument("--bert-out", dest="bert_out", default=os.path.join(OUTPUT_DIR, "review_bert.parquet"), help="Output Parquet BERT (default: output/review_bert.parquet)")
	ap.add_argument("--bert-model", dest="bert_model", default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", help="Nama model BERT (default multilingual MiniLM)")

	ap.add_argument("--gemini", action="store_true", help="Jalankan embedding Gemini")
	ap.add_argument("--gemini-out", dest="gemini_out", default=os.path.join(OUTPUT_DIR, "review_gemini.parquet"), help="Output Parquet Gemini (default: output/review_gemini.parquet)")
	ap.add_argument("--gemini-api-key", dest="gem_api_key", default=None, help="API key Gemini (opsional, atau set GOOGLE_API_KEY)")
	ap.add_argument("--batch-size", dest="batch_size", type=int, default=64, help="Batch size untuk embedding (default: 64)")

	args = ap.parse_args()

	# 1) Tokenisasi
	build_tokens(args.infile, args.outfile, text_col=args.text_col)

	# 2) Embeddings (opsional)
	if args.bert:
		embed_bert(args.infile, args.bert_out, text_col=args.text_col, model_name=args.bert_model, batch_size=args.batch_size)
	if args.gemini:
		embed_gemini(args.infile, args.gemini_out, text_col=args.text_col, api_key=args.gem_api_key, batch_size=args.batch_size)

if __name__ == "__main__":
	main()
