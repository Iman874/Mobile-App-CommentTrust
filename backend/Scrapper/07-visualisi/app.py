import os
import json
import math
from flask import Flask, jsonify, request, send_file, Response
import pandas as pd

# @context: CommentTrust AI project
# @goal: Convert avg_trust value into normalized 0–100% percentage for dashboard
# @priority: Display readable trust indicator with color level (Low/Medium/High)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPPER_DIR = os.path.dirname(BASE_DIR)
OUTPUT_DIR = os.path.join(SCRAPPER_DIR, "output")

app = Flask(__name__)

def _read_csv_safe(path):
	if not os.path.exists(path):
		return None
	try:
		return pd.read_csv(path, encoding="utf-8-sig")
	except Exception:
		try:
			return pd.read_csv(path)
		except Exception:
			return None

# --- normalize avg_trust (0..100) to 0..100% via sigmoid ---
def normalize_trust(avg_trust):
	try:
	  v = float(avg_trust)
	  if not (v == v):  # NaN
		  return 0.0
	except Exception:
	  return 0.0
	return round(100.0 / (1.0 + math.exp(-v / 10.0)), 2)

def trust_level(val_percent: float):
	if val_percent >= 71.0:
		return "🟢 High Trust", "trust-high"
	if val_percent >= 41.0:
		return "🟡 Medium Trust", "trust-med"
	return "🔴 Low Trust", "trust-low"

# Threshold fake detection yang dikonfigurasi (selaras dengan detector): 0.6
FAKE_THRESHOLD = 0.6

# --- backend output resolver ---
_BACKENDS = ("gemini", "indobert", "nb")
def _backend_name(raw: str | None) -> str | None:
	if not raw:
		return None
	raw = raw.strip().lower()
	return raw if raw in _BACKENDS else None

def _out_dir_for_backend(b: str | None) -> str:
	"""
	Kembalikan output dir untuk backend tertentu:
	- output/<backend>/ jika ada
	- fallback: output/ (root)
	"""
	base = OUTPUT_DIR
	if b:
		p = os.path.join(OUTPUT_DIR, b)
		if os.path.isdir(p):
			return p
		# robust: historical naming "indoBert" → fallback bila "indobert" tidak ada
		if b == "indobert":
			p_alt = os.path.join(OUTPUT_DIR, "indoBert")
			if os.path.isdir(p_alt):
				return p_alt
		return base
	return base

def _paths(b: str | None):
	outdir = _out_dir_for_backend(b)
	return {
		"outdir": outdir,
		"reviews": os.path.join(outdir, "review_trust.csv"),
		"summary": os.path.join(outdir, "summary.json"),
		"product": os.path.join(outdir, "product_trust.json"),
	}

@app.get("/")
def index():
	# pilih backend via ?b=gemini|indobert|nb|lexicon
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)

	# load product + summary (best-effort)
	product = {}
	summary = {}
	try:
		if os.path.exists(paths["product"]):
			with open(paths["product"], "r", encoding="utf-8") as f:
				product = json.load(f)
	except Exception:
		product = {}
	try:
		if os.path.exists(paths["summary"]):
			with open(paths["summary"], "r", encoding="utf-8") as f:
				summary = json.load(f)
	except Exception:
		summary = {}

	pr = product.get("product") or {}
	mt = product.get("metrics") or {}
	last30 = summary.get("recent_30d") or {}
	name = pr.get("name") or "Produk"
	count_reviews = mt.get("count_reviews", 0)
	avg_rating = mt.get("avg_rating", 0)
	avg_trust = mt.get("avg_trust_score", 0)
	avg_trust_pct = normalize_trust(avg_trust)
	trust_badge_text, trust_badge_class = trust_level(avg_trust_pct)

	# Override fake_rate dari CSV dengan threshold 0.6 agar konsisten
	fake_rate = mt.get("fake_rate", 0)
	try:
		df_rt = _read_csv_safe(paths["reviews"])
		if df_rt is not None and len(df_rt) > 0:
			fs = pd.to_numeric(df_rt.get("fake_score", df_rt.get("suspicion_score", 0)), errors="coerce").fillna(0).clip(0, 1)
			fake_rate = float((fs >= FAKE_THRESHOLD).mean())
	except Exception:
		pass

	pos_sum = summary.get("positive_summary", "")
	neg_sum = summary.get("negative_summary", "")
	pros = summary.get("pros", []) or []
	cons = summary.get("cons", []) or []
	last_cnt = (last30 or {}).get("count", 0)

	# UI
	backend_label = b or "default"
	# link helper keep backend
	def _l(path):
		return f"{path}?b={backend_label}" if b else path

	return Response(f"""
		<html>
		<head>
			<title>CommentTrust Dashboard ({backend_label})</title>
			<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
			<meta charset="utf-8"/>
			<style>
				.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 12px; }}
				.card {{ padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }}
				.badge {{ display:inline-block; padding:4px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; }}
				.trust-high {{ background:#e8f5e9; color:#1b5e20; }}
				.trust-med  {{ background:#fff8e1; color:#f57f17; }}
				.trust-low  {{ background:#ffebee; color:#b71c1c; }}
				.kv span {{ display:block; font-size:12px; color:#666; }}
				.kv strong {{ font-size:20px; }}
				.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
				ul.compact li {{ margin: 4px 0; }}
				/* Pros/Cons iconized lists */
				ul.pros, ul.cons {{ list-style: none; padding-left: 0; margin-left: 0; }}
				ul.pros li::before {{ content: "✔ "; color:#1b5e20; font-weight:600; margin-right:6px; }}
				ul.cons li::before {{ content: "✖ "; color:#b71c1c; font-weight:600; margin-right:6px; }}
				.header {{ display:flex; justify-content:space-between; align-items:center; }}
				.pills a {{ margin-right:6px; text-decoration:none; }}
			</style>
		</head>
		<body>
			<div class="header">
				<h1>{name}</h1>
				<div class="pills">
					<span>Backend:</span>
					<a class="badge" href="/?b=gemini">Gemini</a>
					<a class="badge" href="/?b=indobert">IndoBERT</a>
					<a class="badge" href="/?b=nb">Naive Bayes</a>
					<a class="badge" href="/?b=lexicon">Lexicon</a>
				</div>
			</div>
			<div class="grid">
				<div class="card kv"><span>Total Reviews</span><strong>{count_reviews}</strong></div>
				<div class="card kv"><span>Avg. Rating</span><strong>{avg_rating:.2f}/5</strong></div>
				<div class="card kv">
					<span>Avg. Trust</span>
					<strong>{avg_trust_pct:.2f}%</strong>
					<div><span class="badge {trust_badge_class}">{trust_badge_text}</span></div>
				</div>
				<div class="card kv"><span>Fake Rate</span><strong>{fake_rate:.2%}</strong></div>
				<div class="card kv"><span>30 Hari Terakhir</span><strong>{last_cnt}</strong></div>
			</div>

			<div class="cols" style="margin-top:16px">
				<div class="card">
					<h3>Ringkasan Positif</h3>
					<p>{pos_sum}</p>
					<h4>Kelebihan (Pros)</h4>
					<ul class="compact pros">
						{"".join(f"<li>{p}</li>" for p in pros)}
					</ul>
				</div>
				<div class="card">
					<h3>Ringkasan Negatif</h3>
					<p>{neg_sum}</p>
					<h4>Kekurangan (Cons)</h4>
					<ul class="compact cons">
						{"".join(f"<li>{c}</li>" for c in cons)}
					</ul>
				</div>
			</div>

			<div class="card" style="margin-top:16px">
				<h3>Quick Links ({backend_label})</h3>
				<ul>
					<li><a href="{_l('/table/reviews')}">Tabel Review</a></li>
					<li><a href="{_l('/charts')}">Charts</a></li>
					<li><a href="{_l('/tags')}">Tag Komentar</a></li>
					<li><a href="{_l('/api/product')}">API product_trust.json</a></li>
					<li><a href="{_l('/api/summary')}">API summary.json</a></li>
					<li><a href="{_l('/api/reviews')}">API review_trust (JSON)</a></li>
				</ul>
				<p>Output dir: {paths["outdir"]}</p>
			</div>
		</body></html>
	""", mimetype="text/html")

@app.get("/api/reviews")
def api_reviews():
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	df = _read_csv_safe(paths["reviews"])
	if df is None:
		return jsonify({"error": f"not found: {paths['reviews']}"}), 404
	# pagination
	page = int(request.args.get("page", 1))
	size = int(request.args.get("size", 50))
	size = max(1, min(size, 500))
	total = len(df)
	pages = max(1, math.ceil(total / size))
	page = max(1, min(page, pages))
	start = (page-1)*size
	end = start + size
	return jsonify({
		"backend": b or "default", "page": page, "size": size, "total": total, "pages": pages,
		"data": df.iloc[start:end].to_dict(orient="records")
	})

@app.get("/api/product")
def api_product():
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	if not os.path.exists(paths["product"]):
		return jsonify({"error": f"not found: {paths['product']}"}), 404
	with open(paths["product"], "r", encoding="utf-8") as f:
		return jsonify(json.load(f))

@app.get("/api/summary")
def api_summary():
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	if not os.path.exists(paths["summary"]):
		return jsonify({"error": f"not found: {paths['summary']}"}), 404
	with open(paths["summary"], "r", encoding="utf-8") as f:
		return jsonify(json.load(f))

@app.get("/table/reviews")
def table_reviews():
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	df = _read_csv_safe(paths["reviews"])
	if df is None:
		return Response(f"<h3>File tidak ditemukan: {paths['reviews']}</h3>", mimetype="text/html")
	cols = list(df.columns)
	show_cols = [c for c in cols if c in (
		"username","comment","comment_clean","create_time",
		"product_name","product_type","product_label",
		"rating","likes","sentiment","sentiment_confidence","fake_pred","fake_score","trust_score"
	)]
	if not show_cols:
		show_cols = cols[:15]
	html = df[show_cols].to_html(classes="table table-sm", index=False, escape=False)
	return Response(f"""
	<html>
		<head>
			<title>Tabel Review ({b or 'default'})</title>
			<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
			<meta charset="utf-8"/>
		</head>
		<body>
			<h2>review_trust.csv — backend: {b or 'default'}</h2>
			{html}
		</body>
	</html>
	""", mimetype="text/html")

@app.get("/charts")
def charts():
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	df = _read_csv_safe(paths["reviews"])
	if df is None:
		return Response(f"<h3>review_trust.csv tidak ditemukan ({paths['reviews']})</h3>", mimetype="text/html")
	# sentiment distribution
	sent_counts = df.get("sentiment", pd.Series([])).astype(str).str.lower().value_counts().to_dict()
	# trust histogram
	trust = pd.to_numeric(df.get("trust_score", 0), errors="coerce").fillna(0).clip(0,100).tolist()
	# fake metrics (dihitung dari fake_score dengan threshold 0.6)
	total = int(len(df))
	fs_series = pd.to_numeric(df.get("fake_score", df.get("suspicion_score", 0)), errors="coerce").fillna(0).clip(0, 1)
	mask_fake = (fs_series >= FAKE_THRESHOLD)
	fake_count = int(mask_fake.sum())
	real_count = max(0, total - fake_count)
	fake_rate = float(fake_count/total) if total else 0.0

	# fake_score histogram (0..1)
	edges = [i/10 for i in range(11)]
	labels = [f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(10)]
	cat = pd.cut(fs_series, bins=edges, include_lowest=True, right=True, labels=labels)
	hist_counts = cat.value_counts().reindex(labels, fill_value=0).tolist()

	thr = float(FAKE_THRESHOLD)
	bar_colors = []
	for i in range(10):
		mid = (edges[i] + edges[i+1]) / 2.0
		bar_colors.append("#d62728" if mid >= thr else "#59a14f")

	return Response(f"""
	<html>
		<head>
			<title>Charts ({b or 'default'})</title>
			<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
			<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
			<meta charset="utf-8"/>
			<style>
				.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
				@media(max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
				.caption {{ color:#555; font-size: 14px; }}
			</style>
		</head>
		<body>
			<h2>Charts — backend: {b or 'default'}</h2>
			<div class="grid">
				<div>
					<canvas id="sentChart" height="300"></canvas>
				</div>
				<div>
					<canvas id="trustHist" height="300"></canvas>
				</div>
				<div>
					<canvas id="fakePie" height="300"></canvas>
					<p class="caption">Fake rate dihitung dari jumlah baris dengan fake_score ≥ {thr:.2f} dibagi total review.</p>
				</div>
				<div>
					<canvas id="fakeHist" height="300"></canvas>
					<p class="caption">Histogram fake_score (0..1). Batas klasifikasi = <b>{thr:.2f}</b>; bar di atas ambang berwarna merah.</p>
				</div>
			</div>
			<p style="margin-top:8px">Fake rate: <b>{fake_rate:.2%}</b> (fake = {fake_count} / total = {total}), threshold = {thr:.2f}</p>
			<script>
				const sentData = {json.dumps(sent_counts, ensure_ascii=False)};
				const trustData = {json.dumps(trust)};
				const fakeCounts = {json.dumps([real_count, fake_count])};
				const fakeLabels = ["Genuine","Fake"];
				const fakeScoreBins = {json.dumps(labels)};
				const fakeScoreCounts = {json.dumps(hist_counts)};
				const fakeScoreColors = {json.dumps(bar_colors)};

				new Chart(document.getElementById('sentChart'), {{
					type: 'bar',
					data: {{ labels: Object.keys(sentData), datasets: [{{ label: 'Sentiment', data: Object.values(sentData), backgroundColor: '#4e79a7' }}] }},
					options: {{ plugins: {{ legend: {{ display:false }} }}, scales: {{ y: {{ beginAtZero:true }} }} }}
				}});

				const bins = new Array(10).fill(0);
				trustData.forEach(v => {{ const i = Math.min(9, Math.floor(v/10)); bins[i]++; }});
				new Chart(document.getElementById('trustHist'), {{
					type: 'bar',
					data: {{ labels: ['0-10','10-20','20-30','30-40','40-50','50-60','60-70','70-80','80-90','90-100'], datasets: [{{ label: 'Reviews', data: bins, backgroundColor: '#f28e2b' }}] }},
					options: {{ plugins: {{ legend: {{ display:false }} }}, scales: {{ y: {{ beginAtZero:true }} }} }}
				}});

				new Chart(document.getElementById('fakePie'), {{
					type: 'doughnut',
					data: {{ labels: fakeLabels, datasets: [{{ data: fakeCounts, backgroundColor: ['#59a14f','#d62728'] }}] }},
					options: {{ plugins: {{ legend: {{ position:'bottom' }} }} }}
				}});

				new Chart(document.getElementById('fakeHist'), {{
					type: 'bar',
					data: {{ labels: fakeScoreBins, datasets: [{{ label: 'Count', data: fakeScoreCounts, backgroundColor: fakeScoreColors }}] }},
					options: {{ plugins: {{ legend: {{ display:false }} }}, scales: {{ y: {{ beginAtZero:true }} }} }}
				}});
			</script>
		</body>
	</html>
	""", mimetype="text/html")

# --- helpers untuk halaman Tag Komentar ---
def _tokenize_words(text: str):
	import re
	return re.findall(r"[a-zA-Z]{2,}", (text or "").lower())

_STOPWORDS_ID = {
	"yg","yang","buat","untuk","itu","dan","di","ke","dengan","ada","jadi","sangat","banget","real","pict","aja","juga","udah","sih","saja","serta","atau","kan","nih","lah",
	"warna","hitam","abu","merah","biru","putih","tas","barang","produk","banget","keren","oke","ok","mantap","item","itu","ini"
}

def _extract_phrases(texts: list[str], n=12):
	# coba TF-IDF 2–3 gram, fallback ke frekuensi
	texts = [t for t in (texts or []) if isinstance(t, str) and t.strip()]
	if not texts:
		return []
	try:
		from sklearn.feature_extraction.text import TfidfVectorizer
		vec = TfidfVectorizer(
			ngram_range=(2,3),
			min_df=2,
			max_features=1000,
			token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b"
		)
		X = vec.fit_transform(texts)
		import numpy as np
		scores = X.mean(axis=0).A1
		feats = vec.get_feature_names_out()
		cands = [(feats[i], scores[i]) for i in range(len(feats))]
		cands.sort(key=lambda x: x[1], reverse=True)
		out, seen = [], set()
		for p,_ in cands:
			# filter stop/filler
			toks = [w for w in p.split() if w not in _STOPWORDS_ID]
			pp = " ".join(toks)
			if not pp or pp in seen:
				continue
			seen.add(pp); out.append(pp)
			if len(out) >= n: break
		return out
	except Exception:
		from collections import Counter
		bi = Counter(); tri = Counter()
		for t in texts:
			ws = [w for w in _tokenize_words(t) if w not in _STOPWORDS_ID]
			for i in range(len(ws)-1):
				bi[(ws[i], ws[i+1])] += 1
			for i in range(len(ws)-2):
				tri[(ws[i], ws[i+1], ws[i+2])] += 1
		cands = [" ".join(k) for k,_ in tri.most_common(n*2)] + [" ".join(k) for k,_ in bi.most_common(n*2)]
		out, seen = [], set()
		for p in cands:
			if p and p not in seen:
				seen.add(p); out.append(p)
			if len(out) >= n: break
		return out

def _stars(r):
	try:
		val = int(round(float(r or 0)))
		val = max(0, min(5, val))
	except Exception:
		val = 0
	return "★"*val + "☆"*(5-val)

def _chip_tags(text: str, topics: list[str], limit=3):
	text = (text or "").lower()
	tags = []
	for t in topics:
		if t and t in text:
			tags.append(t)
		if len(tags) >= limit:
			break
	return tags

def _importance_score(row):
	# skor sederhana untuk seleksi "penting"
	tokens_count = int(row.get("tokens_count") or 0)
	likes = float(row.get("likes") or 0)
	trust = float(row.get("trust_score") or 0)
	rating = float(row.get("rating") or 0)
	return (trust/100.0)*0.5 + (likes/10.0)*0.3 + (1.0 if rating>=5 and tokens_count>=8 else 0)*0.2

def _build_cards(df: pd.DataFrame, title: str, topics_pos: list[str], topics_neg: list[str], topics_all: list[str], limit=12):
	# buat grid card HTML
	rows = []
	for _, r in df.head(limit).iterrows():
		user = str(r.get("username") or "")
		comment = str(r.get("comment_clean") or r.get("comment") or "")
		rating = r.get("rating")
		likes = int(pd.to_numeric(r.get("likes"), errors="coerce") or 0)
		ts = float(pd.to_numeric(r.get("trust_score"), errors="coerce") or 0)
		sent = str(r.get("sentiment") or "").lower()
		ctime = str(r.get("create_time") or "")
		label = r.get("product_label") or r.get("variant_name") or ""
		# pilih topik chips sesuai sentimen
		topic_pool = topics_pos if sent == "positive" else (topics_neg if sent == "negative" else (topics_pos[:2] + topics_neg[:2]))
		chips = _chip_tags(comment, topic_pool, limit=3)
		# tags lengkap untuk filtering (semua topik yang muncul di komentar)
		tags_full = _chip_tags(comment, topics_all, limit=999)
		# tag kategori
		tag_cat = "Positif" if sent == "positive" else ("Negatif" if sent == "negative" else "Netral")
		rows.append(f"""
			<div class="card comment-card" data-tags='{json.dumps(tags_full, ensure_ascii=False)}'>
				<div style="display:flex; justify-content:space-between; align-items:center;">
					<strong>{user}</strong>
					<span>{_stars(rating)} ({rating})</span>
				</div>
				<p style="margin:6px 0; color:#111;">{comment}</p>
				<div style="display:flex; gap:6px; flex-wrap:wrap; margin:6px 0;">
					<span class="badge">{tag_cat}</span>
					{''.join(f'<span class="badge">{t}</span>' for t in chips)}
				</div>
				<div style="display:flex; justify-content:space-between; font-size:12px; color:#555;">
					<span>Likes: {likes}</span>
					<span>Trust: {ts:.2f}</span>
					<span>{label or '-'}</span>
					<span>{ctime or ''}</span>
				</div>
			</div>
		""")
	if not rows:
		rows = ["<p>Tidak ada data.</p>"]
	return f"""
		<h3 style="margin-top:18px;">{title}</h3>
		<div class="grid">{''.join(rows)}</div>
	"""

@app.get("/tags")
def page_tags():
	# backend-aware
	b = _backend_name(request.args.get("b"))
	paths = _paths(b)
	df = _read_csv_safe(paths["reviews"])
	if df is None:
		return Response(f"<h3>File tidak ditemukan: {paths['reviews']}</h3>", mimetype="text/html")
	# pastikan tokens_count ada
	if "tokens_count" not in df.columns:
		tc = df.get("comment_clean", df.get("comment", "")).astype(str).apply(lambda s: len([w for w in s.split() if w]))
		df["tokens_count"] = tc
	# ekstrak topik
	txt_col = "comment_clean" if "comment_clean" in df.columns else "comment"
	all_texts = df[txt_col].astype(str).tolist()
	topics_all = _extract_phrases(all_texts, n=20)
	pos_texts = df.loc[df.get("sentiment", "").astype(str).str.lower().eq("positive"), txt_col].astype(str).tolist()
	neg_texts = df.loc[df.get("sentiment", "").astype(str).str.lower().eq("negative"), txt_col].astype(str).tolist()
	topics_pos = _extract_phrases(pos_texts, n=12)
	topics_neg = _extract_phrases(neg_texts, n=12)

	# pilih komentar penting: skor gabungan (trust, likes, panjang, rating)
	df_imp = df.copy()
	df_imp["__imp"] = df_imp.apply(_importance_score, axis=1)
	df_imp = df_imp.sort_values(["__imp","trust_score","likes"], ascending=False)

	# kelompok sentimen
	df_pos = df.loc[df.get("sentiment","").astype(str).str.lower().eq("positive")].sort_values(["trust_score","likes"], ascending=False)
	df_neg = df.loc[df.get("sentiment","").astype(str).str.lower().eq("negative")].sort_values(["likes","trust_score"], ascending=[False, True])
	df_neu = df.loc[df.get("sentiment","").astype(str).str.lower().eq("neutral")].sort_values(["likes"], ascending=False)

	# link helper keep backend
	def _l(path):
		return f"{path}?b={b}" if b else path

	# chips UI builder
	def _chips_html(items):
		return "".join(f'<button class="chip tag-toggle active" data-tag="{t}">{t}</button>' for t in items)

	html = f"""
	<html>
	<head>
		<title>Tag Komentar ({b or 'default'})</title>
		<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
		<meta charset="utf-8"/>
		<style>
			.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap: 12px; }}
			.card {{ padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; }}
			.badge {{ display:inline-block; padding:4px 8px; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:12px; }}
			.header {{ display:flex; justify-content:space-between; align-items:center; }}
			.pills a {{ margin-right:6px; text-decoration:none; }}
			.chips span {{ margin-right:6px; }}
			/* Tag filter chips */
			.chip {{ display:inline-block; margin:4px 6px 0 0; padding:6px 10px; border:1px solid #e5e7eb; border-radius:999px; background:#f8fafc; cursor:pointer; font-size:12px; }}
			.chip.active {{ background:#eef2ff; color:#3730a3; border-color:#c7d2fe; }}
			.toolbar {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin:6px 0; }}
			.toolbar button {{ padding:6px 10px; border-radius:6px; border:1px solid #e5e7eb; background:#fff; cursor:pointer; }}
		</style>
	</head>
	<body>
		<div class="header">
			<h2>Tag Komentar — backend: {b or 'default'}</h2>
			<div class="pills">
				<a class="badge" href="{_l('/')}">Dashboard</a>
				<a class="badge" href="{_l('/table/reviews')}">Tabel</a>
				<a class="badge" href="{_l('/charts')}">Charts</a>
			</div>
		</div>

		<div class="card">
			<h3>Filter Topik</h3>
			<div class="toolbar">
				<button id="btnSelectAll">Select All</button>
				<button id="btnUnselectAll">Unselect All</button>
				<span id="activeCount" class="badge">Semua aktif</span>
			</div>
			<div id="tagChips">
				{_chips_html(topics_all[:15])}
			</div>
			<h4>Topik Positif</h4>
			<div class="chips">
				{''.join(f'<span class="badge">{t}</span>' for t in topics_pos[:10])}
			</div>
			<h4>Topik Negatif</h4>
			<div class="chips">
				{''.join(f'<span class="badge">{t}</span>' for t in topics_neg[:10])}
			</div>
		</div>

		<div id="cardsWrap">
			{_build_cards(df_imp, "Komentar Penting", topics_pos, topics_neg, topics_all, limit=24)}
			{_build_cards(df_pos, "Komentar Positif", topics_pos, topics_neg, topics_all, limit=24)}
			{_build_cards(df_neg, "Komentar Negatif", topics_pos, topics_neg, topics_all, limit=24)}
			{_build_cards(df_neu, "Komentar Netral", topics_pos, topics_neg, topics_all, limit=24)}
		</div>

		<script>
			// in-page tag filtering
			const chips = Array.from(document.querySelectorAll('.tag-toggle'));
			const btnAll = document.getElementById('btnSelectAll');
			const btnNone = document.getElementById('btnUnselectAll');
			const activeCount = document.getElementById('activeCount');
			function selectedTags() {{ return new Set(chips.filter(c => c.classList.contains('active')).map(c => c.dataset.tag)); }}
			function updateCount() {{
				const n = selectedTags().size;
				activeCount.textContent = n === {len(topics_all[:15])} ? 'Semua aktif' : `Aktif: ${{n}}`;
			}}
			function filterCards() {{
				const sel = selectedTags();
				const cards = document.querySelectorAll('.comment-card');
				// if nothing selected, hide all
				if (sel.size === 0) {{
					cards.forEach(card => card.style.display = 'none');
					return;
				}}
				cards.forEach(card => {{
					try {{
						const tags = JSON.parse(card.getAttribute('data-tags') || '[]');
						const show = tags.some(t => sel.has(t));
						card.style.display = show ? '' : 'none';
					}} catch (e) {{
						card.style.display = '';
					}}
				}});
			}}
			chips.forEach(ch => ch.addEventListener('click', () => {{
				ch.classList.toggle('active');
				updateCount(); filterCards();
			}}));
			btnAll.addEventListener('click', () => {{
				chips.forEach(c => c.classList.add('active'));
				updateCount(); filterCards();
			}});
			btnNone.addEventListener('click', () => {{
				chips.forEach(c => c.classList.remove('active'));
				updateCount(); filterCards();
			}});
			// initial
			updateCount(); filterCards();
		</script>
	</body>
	</html>
	"""
	return Response(html, mimetype="text/html")

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000, debug=True)
