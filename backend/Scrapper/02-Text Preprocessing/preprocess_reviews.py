import os
import re
import pandas as pd

# NLTK + Sastrawi
try:
	from nltk.tokenize import word_tokenize
	import nltk  # untuk fallback unduh punkt
	_HAS_NLTK = True
except Exception:
	_HAS_NLTK = False

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Folder output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 1. Fungsi pembersihan teks ===
def clean_text(text: str) -> str:
	if not isinstance(text, str):
		return ""
	text = text.lower()
	text = re.sub(r"http\S+|www\S+", "", text)
	text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text

# === 2. Tokenisasi dan Stopword Removal ===
stop_factory = StopWordRemoverFactory()
stopwords = set(stop_factory.get_stop_words())

def _safe_tokenize(text: str):
	if _HAS_NLTK:
		try:
			return word_tokenize(text)
		except LookupError:
			try:
				import nltk
				nltk.download("punkt", quiet=True)
				return word_tokenize(text)
			except Exception:
				pass
	# fallback sangat sederhana bila NLTK tidak tersedia
	return text.split()

def tokenize_and_filter(text: str):
	tokens = _safe_tokenize(text)
	return [t for t in tokens if t not in stopwords]

# === 3. Stemming Bahasa Indonesia ===
stem_factory = StemmerFactory()
stemmer = stem_factory.create_stemmer()

def stem_tokens(tokens):
	return [stemmer.stem(t) for t in tokens]

# === 4. Gabung ke pipeline utama ===
def preprocess_text(text):
	cleaned = clean_text(text)
	tokens = tokenize_and_filter(cleaned)
	stemmed = stem_tokens(tokens)
	return " ".join(stemmed)

# === 5. Proses CSV hasil scraping ===
def process_csv(input_csv=os.path.join(OUTPUT_DIR, "review.csv"),
               output_csv=os.path.join(OUTPUT_DIR, "review_clean.csv")):
	print(f"Membaca file: {input_csv}")
	df = pd.read_csv(input_csv, encoding="utf-8-sig")

	# Tambahkan kolom hasil preprocessing
	if "comment" not in df.columns:
		raise SystemExit("Kolom 'comment' tidak ditemukan pada CSV.")
	df["comment_clean"] = df["comment"].astype(str).apply(preprocess_text)

	# Simpan hasil
	df.to_csv(output_csv, index=False, encoding="utf-8-sig")
	print(f"✅ Berhasil disimpan: {output_csv}")
	print(df[["comment", "comment_clean"]].head(5))

# === 6. Eksekusi langsung ===
if __name__ == "__main__":
	process_csv()