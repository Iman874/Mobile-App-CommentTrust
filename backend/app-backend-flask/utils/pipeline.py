import os
import json
import re
from typing import Optional
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_BASE = os.path.join(BASE_DIR, "output")
COMMENT_ROOT = os.path.join(OUT_BASE, "comment")
REVIEW_ROOT = os.path.join(OUT_BASE, "review")
PROD_ROOT = os.path.join(OUT_BASE, "produk")
os.makedirs(COMMENT_ROOT, exist_ok=True)
os.makedirs(REVIEW_ROOT, exist_ok=True)
os.makedirs(PROD_ROOT, exist_ok=True)


def _comment_outdir(backend: str, product_id: str):
    b = (backend or "auto").lower()
    p = os.path.join(COMMENT_ROOT, product_id, b)
    os.makedirs(p, exist_ok=True)
    return p

def _review_outdir(product_id: str):
    p = os.path.join(REVIEW_ROOT, product_id)
    os.makedirs(p, exist_ok=True)
    return p


def _clean_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"http\S+|www\S+", "", s)
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def step_preprocess(review_csv: str, out_dir: str):
    df = pd.read_csv(review_csv, encoding="utf-8-sig")
    if "comment" not in df.columns:
        raise SystemExit("Kolom 'comment' wajib ada pada input CSV.")
    df["comment_clean"] = df["comment"].astype(str).apply(_clean_text)
    out = os.path.join(out_dir, "review_clean.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def step_tokenize(clean_csv: str, out_dir: str):
    df = pd.read_csv(clean_csv, encoding="utf-8-sig")
    def _tok(s):
        return [t for t in str(s).split() if t]
    toks = df["comment_clean"].astype(str).apply(_tok)
    df["tokens"] = toks.apply(lambda xs: " ".join(xs))
    df["tokens_count"] = toks.apply(len)
    out = os.path.join(out_dir, "review_tokens.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def _lexicon_polarity(text: str):
    POS = {"bagus","keren","mantap","cepat","recommended","puas","cocok","tebal","rapi","sesuai"}
    NEG = {"jelek","lama","buruk","tipis","rusak","mengecewakan","tidak","kurang"}
    t = set((text or "").lower().split())
    sp = len(t & POS); sn = len(t & NEG)
    if sp > sn and sp > 0: return "positive", 0.75
    if sn > sp and sn > 0: return "negative", 0.75
    return "neutral", 0.55


def _try_indobert_sentiment(input_csv: str, out_csv: str) -> bool:
    """Attempt IndoBERT-based sentiment using Transformers. Returns True on success."""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
        import torch
    except Exception:
        return False
    try:
        df = pd.read_csv(input_csv, encoding="utf-8-sig")
    except Exception:
        return False
    text_col = "tokens" if "tokens" in df.columns else ("comment_clean" if "comment_clean" in df.columns else "comment")
    texts = df[text_col].astype(str).tolist()
    device = 0 if torch.cuda.is_available() else -1
    candidates = [
        "indobenchmark/indobert-base-p2",
        "ayameRushia/indobert-base-p1-sentiment",
        "cahya/bert-base-indonesian-1.5G-sentiment",
        "w11wo/indonesian-roberta-base-sentiment-classification",
    ]
    pipe = None
    for ckpt in candidates:
        try:
            tok = AutoTokenizer.from_pretrained(ckpt)
            mdl = AutoModelForSequenceClassification.from_pretrained(ckpt)
            pipe = TextClassificationPipeline(model=mdl, tokenizer=tok, device=device, return_all_scores=False)
            break
        except Exception:
            pipe = None
            continue
    if pipe is None:
        return False
    def _map(lbl: str) -> str:
        s = (lbl or "").strip().lower()
        # Common 3-class conventions
        if s in ("positive","pos","label_2"): return "positive"
        if s in ("negative","neg","label_0"): return "negative"
        if s in ("neutral","neu","label_1"): return "neutral"
        # Generalize label_N (including 4 or 5-class checkpoints)
        try:
            id2 = {int(k): v for k,v in getattr(pipe.model.config, 'id2label', {}).items()}
            n_classes = len(id2) if id2 else None
            # If label_N style, compress to 3 buckets by index
            import re as _re
            m = _re.match(r"label[_\- ]?(\d+)", s)
            if m:
                k = int(m.group(1))
                if n_classes and n_classes >= 4:
                    # Map extremes to neg/pos, middle to neutral
                    if n_classes == 4:
                        # 0:neg, 1:neutral-ish, 2-3:positive
                        if k <= 0: return "negative"
                        if k == 1: return "neutral"
                        return "positive"
                    if n_classes >= 5:
                        # 0-1:neg, 2:neutral, 3-4:pos
                        if k <= 1: return "negative"
                        if k == 2: return "neutral"
                        return "positive"
                # Fallback heuristic by index
                if k == 0: return "negative"
                if k == 1: return "neutral"
                return "positive"
            # If labels are words like 'very positive', normalize
            vv = [str(v).lower() for v in (id2.values() if id2 else [])]
            if s in vv:
                if 'pos' in s: return "positive"
                if 'neg' in s: return "negative"
                if 'neu' in s: return "neutral"
        except Exception:
            pass
        return "neutral"
    outs = []
    bs = 32
    for i in range(0, len(texts), bs):
        batch = texts[i:i+bs]
        try:
            res = pipe(batch)
        except Exception:
            res = []
            for t in batch:
                try:
                    res.append(pipe(t))
                except Exception:
                    res.append({"label":"neutral","score":0.5})
        for r in res:
            if isinstance(r, dict) and 'label' in r:
                outs.append({"label": r['label'], "score": float(r.get('score',0.6))})
            elif isinstance(r, list) and r and isinstance(r[0], dict):
                r0 = max(r, key=lambda x: x.get('score',0))
                outs.append({"label": r0.get('label','neutral'), "score": float(r0.get('score',0.6))})
            else:
                outs.append({"label":"neutral","score":0.5})
    lbls = [_map(o.get('label','neutral')) for o in outs]
    confs = [float(o.get('score',0.6)) for o in outs]
    df["sentiment"] = lbls
    df["sentiment_confidence"] = pd.to_numeric(pd.Series(confs), errors="coerce").fillna(0.6).clip(0,1)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    return True

def step_sentiment(in_csv: str, out_dir: str, backend: str = "auto"):
    out = os.path.join(out_dir, "review_sentiment.csv")
    if (backend or '').lower() in {"indobert","indoberta","indo","indobert-base"}:
        if _try_indobert_sentiment(in_csv, out):
            return out
    # fallback lexicon
    df = pd.read_csv(in_csv, encoding="utf-8-sig")
    text_col = "tokens" if "tokens" in df.columns else ("comment_clean" if "comment_clean" in df.columns else "comment")
    sents, confs = [], []
    for s in df[text_col].astype(str).tolist():
        lab, conf = _lexicon_polarity(s)
        sents.append(lab); confs.append(conf)
    df["sentiment"] = sents
    df["sentiment_confidence"] = confs
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def _char_repeat_ratio(text: str) -> float:
    if not isinstance(text, str) or not text:
        return 0.0
    repeats = sum(1 for i in range(1, len(text)) if text[i] == text[i-1])
    return repeats / max(1, len(text))


def _token_repeat_ratio(text: str) -> float:
    if not isinstance(text, str) or not text.strip():
        return 0.0
    toks = text.split()
    from collections import Counter
    cnt = Counter(toks)
    more2 = sum(v for v in cnt.values() if v >= 2)
    return more2 / max(1, len(toks))


def _sentiment_rating_mismatch(sentiment: str, rating: float) -> float:
    s = (sentiment or "").lower()
    try:
        r = float(rating)
    except Exception:
        r = None
    if r is None:
        return 0.0
    if r >= 4 and s == "negative":
        return 1.0
    if r <= 2 and s == "positive":
        return 1.0
    return 0.0


def step_fake_detect(in_csv: str, out_dir: str, threshold: float = 0.6):
    df = pd.read_csv(in_csv, encoding="utf-8-sig")
    txt = "tokens" if "tokens" in df.columns else ("comment_clean" if "comment_clean" in df.columns else "comment")
    df["text_len"] = df[txt].fillna("").astype(str).str.len()
    df["tokens_count"] = df.get("tokens_count", df[txt].fillna("").astype(str).apply(lambda s: len(s.split())))
    df["char_repeat_ratio"] = df[txt].astype(str).apply(_char_repeat_ratio)
    df["token_repeat_ratio"] = df[txt].astype(str).apply(_token_repeat_ratio)
    # duplication score within file
    vc = df[txt].fillna("").astype(str).str.strip().value_counts()
    df["dup_score"] = df[txt].fillna("").astype(str).str.strip().map(lambda t: 0.0 if t == "" else (min(1.0, (vc.get(t, 1)-1)/5.0)))
    # robust mismatch assignment (avoid DataFrame assignment errors)
    mismatch_series = df.apply(lambda r: _sentiment_rating_mismatch(r.get("sentiment",""), r.get("rating", None)), axis=1)
    if hasattr(mismatch_series, "ndim") and getattr(mismatch_series, "ndim", 1) > 1:
        # if somehow returns DataFrame, take first column
        try:
            mismatch_series = mismatch_series.iloc[:,0]
        except Exception:
            mismatch_series = pd.Series([0.0]*len(df))
    df["mismatch"] = pd.to_numeric(mismatch_series, errors="coerce").fillna(0.0)
    short_penalty = (df["text_len"] < 8).astype(float) * 0.6 + (df["text_len"].between(8, 15)).astype(float) * 0.2
    score = (0.25*df["char_repeat_ratio"].clip(0,1) + 0.25*df["token_repeat_ratio"].clip(0,1) + 0.30*df["dup_score"].clip(0,1) + 0.20*df["mismatch"].clip(0,1) + short_penalty.clip(0,1))
    df["fake_score"] = score.clip(0,1)
    df["fake_pred"] = (df["fake_score"] >= float(threshold)).astype(int)
    out = os.path.join(out_dir, "review_fake.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return out


def _read_product_name_for(product_id: Optional[str]) -> Optional[str]:
    if not product_id:
        return None
    try:
        pjson = os.path.join(_review_outdir(product_id), "product.json")
        if not os.path.exists(pjson):
            return None
        obj = json.load(open(pjson, 'r', encoding='utf-8'))
        if isinstance(obj, dict):
            if 'name' in obj and obj['name']:
                return str(obj['name'])
            for k in ('item','data'):
                if isinstance(obj.get(k), dict) and obj[k].get('name'):
                    return str(obj[k]['name'])
        return None
    except Exception:
        return None

def step_trust(fake_csv: str, out_dir: str, product_id: Optional[str] = None):
    import numpy as np
    df = pd.read_csv(fake_csv, encoding="utf-8-sig")
    # Handle completely empty dataframe (no rows) gracefully: assign empty trust_score and summary file
    if df.empty:
        df["trust_score"] = []
        out = os.path.join(out_dir, "review_trust.csv")
        df.to_csv(out, index=False, encoding="utf-8-sig")
        summary = {
            "product": {"id": product_id, "name": _read_product_name_for(product_id)},
            "metrics": {
                "count_reviews": 0,
                "fake_rate": 0.0,
                "avg_trust_score": 0.0,
                "avg_rating": 0.0
            }
        }
        with open(os.path.join(out_dir, "product_trust.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        return out
    # Coerce all numeric-relevant columns early to avoid object dtypes producing math errors
    for col in ["likes", "rating", "fake_score", "fake_pred", "sentiment_confidence"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # likes/rating may come as strings with separators or blank; ensure clean numeric
    df["likes"] = df.get("likes", 0).fillna(0).astype(float)
    df["rating"] = df.get("rating", 0).fillna(0).astype(float)
    def _sent_val(s):
        s = (str(s) if s is not None else '').lower()
        if s == 'positive': return 1.0
        if s == 'negative': return 0.0
        return 0.5
    # sentiment_confidence fallback and numeric cast
    df["sentiment"] = df.get("sentiment", "neutral").fillna("neutral").astype(str)
    df["sentiment_confidence"] = pd.to_numeric(df.get("sentiment_confidence", 0.5), errors="coerce").fillna(0.5).clip(0,1)
    df["fake_score"] = pd.to_numeric(df.get("fake_score", 0), errors="coerce").fillna(0.0)
    df["fake_pred"] = pd.to_numeric(df.get("fake_pred", 0), errors="coerce").fillna(0).astype(int)
    # Final enforcement of numeric dtypes (object -> float/int) before calculations
    df["likes"] = pd.to_numeric(df["likes"], errors="coerce").fillna(0).astype(float)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(float)
    df["fake_score"] = pd.to_numeric(df["fake_score"], errors="coerce").fillna(0).astype(float)
    df["fake_pred"] = pd.to_numeric(df["fake_pred"], errors="coerce").fillna(0).astype(int)
    df["sentiment_confidence"] = pd.to_numeric(df["sentiment_confidence"], errors="coerce").fillna(0.5).astype(float).clip(0,1)
    sent_val = df["sentiment"].apply(_sent_val)
    likes_term = 0.2*(1 - np.exp(-df["likes"]/10.0))
    rating_term = 0.2*(df["rating"]/5.0)
    penalty = 0.6*df["fake_pred"] + 0.3*df["fake_score"]
    raw = 0.6*sent_val + likes_term + rating_term
    trust = (raw*(1-penalty)).clip(0,1)
    df["trust_score"] = (trust*100).round(2)
    out = os.path.join(out_dir, "review_trust.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    # product summary minimal
    n = len(df)
    fake_rate = float((df["fake_pred"]>0).mean()) if n else 0.0
    avg_trust = float(pd.to_numeric(df.get("trust_score", 0), errors="coerce").fillna(0).mean()) if n else 0.0
    avg_rating = float(pd.to_numeric(df.get("rating", 0), errors="coerce").fillna(0).mean()) if n else 0.0
    summary = {
        "product": {"id": product_id, "name": _read_product_name_for(product_id)},
        "metrics": {
            "count_reviews": n,
            "fake_rate": round(fake_rate,4),
            "avg_trust_score": round(avg_trust,2),
            "avg_rating": round(avg_rating,2)
        }
    }
    with open(os.path.join(out_dir, "product_trust.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return out


def step_summarize(trust_csv: str, out_dir: str):
    df = pd.read_csv(trust_csv, encoding="utf-8-sig")
    txt = "comment_clean" if "comment_clean" in df.columns else "comment"
    sent = df.get("sentiment", "neutral").astype(str).str.lower()
    pos_texts = df.loc[sent.eq("positive"), txt].astype(str).tolist()
    neg_texts = df.loc[sent.eq("negative"), txt].astype(str).tolist()
    def _top_words(texts, n=5):
        from collections import Counter
        import re
        c = Counter()
        for t in texts:
            ws = re.findall(r"[a-zA-Z]{2,}", str(t).lower())
            c.update(ws)
        return [w for w,_ in c.most_common(n)]
    result = {
        "positive_summary": " ".join(_top_words(pos_texts, n=8)) or "",
        "negative_summary": " ".join(_top_words(neg_texts, n=8)) or "",
        "pros": _top_words(pos_texts, n=5),
        "cons": _top_words(neg_texts, n=5),
        "generated_at": datetime.utcnow().isoformat()
    }
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def ensure_review_csv(src_dir: str, out_dir: str, product_id: str):
    """Materialize reviews CSV from review.json when available; otherwise reuse existing CSV.
    This ensures fresh analysis each run if new review.json is produced by scraper.
    """
    csv_path = os.path.join(out_dir, f"review-{product_id}.csv")
    json_path = os.path.join(src_dir, "review.json")
    # If JSON exists, always rebuild CSV from it (overwrite old CSV)
    if not os.path.exists(json_path):
        # No JSON: reuse CSV if it exists, else create empty frame
        if os.path.exists(csv_path):
            return csv_path
        df = pd.DataFrame(columns=["username","comment","rating","likes","create_time"])  # empty
        os.makedirs(out_dir, exist_ok=True)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return csv_path
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
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return csv_path


def run_pipeline(source_dir: str, product_id: str, backend: str = "auto", progress=None):
    """Run E2E pipeline using inputs in source_dir. Returns out_dir."""
    # separate raw review directory and analysis output
    review_dir = _review_outdir(product_id)
    out_dir = _comment_outdir(backend, product_id)
    # Clean previous outputs for deterministic re-runs
    try:
        for fname in [
            "review_clean.csv","review_tokens.csv","review_sentiment.csv",
            "review_fake.csv","review_trust.csv","summary.json","product_trust.json"
        ]:
            p = os.path.join(out_dir, fname)
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        pass
    if progress: progress(5, "init: resolve input")
    csv_in = ensure_review_csv(source_dir, review_dir, product_id)
    if progress: progress(10, "[01] preprocess")
    clean_csv = step_preprocess(csv_in, out_dir)
    if progress: progress(20, "[01b] tokenize")
    tokens_csv = step_tokenize(clean_csv, out_dir)
    if progress: progress(40, "[03] sentiment")
    sent_csv = step_sentiment(tokens_csv, out_dir, backend=backend)
    if progress: progress(70, "[04] fake detect")
    fake_csv = step_fake_detect(sent_csv, out_dir)
    if progress: progress(90, "[05] trust score")
    trust_csv = step_trust(fake_csv, out_dir, product_id=product_id)
    if progress: progress(98, "[06] summarize")
    step_summarize(trust_csv, out_dir)
    
    # Step 7: Apply tagging to reviews in review.json
    if progress: progress(99, "[07] tagging comments")
    try:
        from utils.comment_tagger import tag_comments, get_tag_statistics
        review_file = os.path.join(review_dir, 'review.json')
        if os.path.exists(review_file):
            with open(review_file, 'r', encoding='utf-8') as f:
                reviews = json.load(f)
                if not isinstance(reviews, list):
                    reviews = []
            
            # Apply tagging
            tagged_reviews = tag_comments(reviews, source_field='comment')
            
            # Save tagged reviews back
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump(tagged_reviews, f, ensure_ascii=False, indent=2)
            
            # Save tag statistics
            tag_stats = get_tag_statistics(tagged_reviews)
            stats_file = os.path.join(review_dir, 'tag_statistics.json')
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(tag_stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # Tagging is optional, don't fail pipeline if it errors
        pass
    
    if progress: progress(100, "done")
    return out_dir
