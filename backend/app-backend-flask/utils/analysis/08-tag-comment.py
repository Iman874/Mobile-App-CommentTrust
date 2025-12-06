"""Tag extraction for Indonesian product comments using IndoBERT.

This module provides utilities to assign a list of semantic tags to each
comment and also derive the most representative global tags across a set
of comments. It is designed to be lightweight and pluggable inside the
existing pipeline sequence (after sentiment & trust computations).

Approach (heuristic + transformer):
1. Preprocess comment text (you can reuse functions from 02-text-preprocessing.py).
2. Build a candidate pool of frequent nouns / keywords via simple TF counts.
3. Use a sentence embedding model (IndoBERT) to obtain vector embeddings.
4. Score each candidate against the comment embedding using cosine similarity.
5. Select top-K tags above a similarity threshold per comment.
6. Optionally perform global clustering (averaging embeddings) to reduce
   near-duplicate tags.

Dependencies expected: transformers, torch, numpy, scikit-learn (optional for cosine similarity if you prefer), but we fallback to manual implementation if not installed.

Model suggestion: 'indobenchmark/indobert-base-p1' (masked LM). Since that
model is not a sentence embedding model by default, we average the last
hidden states as a crude embedding. For improved quality you can switch to
an Indonesian sentence embedding model if available.

Usage example:
    from 08-tag-comment import TagExtractor
    extractor = TagExtractor()
    tags_per_comment, global_tags = extractor.extract_for_comments(list_of_texts)

Returned structure for tags_per_comment:
    [ {"comment": original_text, "tags": ["Produk Asli", "Pengiriman Cepat"]}, ... ]

Integrate inside Flask: after assembling each enriched row, attach the
list under key 'tags'. Laravel ingestion already expects each row (r) to
optionally contain r['tags'].
"""

from __future__ import annotations
import re
import math
from collections import Counter
from typing import List, Dict, Tuple

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
except Exception:  # pragma: no cover - environment may not have deps yet
    torch = None
    AutoTokenizer = None
    AutoModel = None

try:
    import numpy as np
except Exception:  # fallback minimal implementation
    np = None

_DEFAULT_MODEL = "indobenchmark/indobert-base-p1"


def _simple_preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize_words(text: str) -> List[str]:
    return [t for t in _simple_preprocess(text).split() if len(t) > 2]


def _cosine(a, b):
    if np is not None:
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9
        return float(np.dot(a, b) / denom)
    # manual python fallback
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


class TagExtractor:
    def __init__(self, model_name: str = _DEFAULT_MODEL, device: str | None = None):
        self.model_name = model_name
        self.device = device or ("cuda" if torch and torch.cuda.is_available() else "cpu")
        self._load_model()

    def _load_model(self):
        if torch is None:
            self.tokenizer = None
            self.model = None
            return
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

    def _embed(self, text: str):
        if not self.model:
            # Fallback random-ish deterministic embedding by hashing tokens
            toks = _tokenize_words(text)
            vec = [0.0] * 64
            for w in toks:
                h = abs(hash(w))
                for i in range(64):
                    vec[i] += ((h >> (i % 16)) & 0xF) / 15.0
            # normalize
            mag = math.sqrt(sum(v * v for v in vec)) or 1e-9
            return [v / mag for v in vec]
        with torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            outputs = self.model(**inputs)
            # Average last hidden state -> embedding vector
            last_hidden = outputs.last_hidden_state.squeeze(0)  # (seq, hidden)
            emb = last_hidden.mean(dim=0)
            return emb.cpu().numpy().tolist()

    def build_candidates(self, comments: List[str], top_n: int = 40) -> List[str]:
        freq = Counter()
        for c in comments:
            freq.update(_tokenize_words(c))
        # basic stop words (extend as needed)
        stop = {"dan", "yang", "untuk", "dengan", "atau", "tidak", "sangat", "dari", "pada", "ini", "itu"}
        candidates = [w for w, _ in freq.most_common(top_n * 3) if w not in stop]
        # pick top_n unique
        return candidates[:top_n]

    def score_candidates(self, comment_emb, cand_embs, candidates, threshold=0.4, top_k=5) -> List[str]:
        scores = [(c, _cosine(comment_emb, ce)) for c, ce in zip(candidates, cand_embs)]
        scores.sort(key=lambda x: x[1], reverse=True)
        filtered = [c for c, s in scores if s >= threshold][:top_k]
        return filtered

    def extract_for_comments(self, comments: List[str]) -> Tuple[List[Dict], List[str]]:
        if not comments:
            return [], []
        candidates = self.build_candidates(comments)
        cand_embs = [self._embed(c) for c in candidates]
        tagged = []
        global_counter = Counter()
        for c in comments:
            emb = self._embed(c)
            tags = self.score_candidates(emb, cand_embs, candidates)
            global_counter.update(tags)
            tagged.append({"comment": c, "tags": tags})
        # global tags sorted by frequency
        global_tags = [t for t, _ in global_counter.most_common(30)]
        return tagged, global_tags


def demo():  # simple manual test
    sample_comments = [
        "Produk bagus kualitas mantap, pengiriman cepat sampai.",
        "Barang asli sesuai deskripsi, packing rapi",
        "Pengiriman lama dan kemasan rusak, kecewa",
        "Harga murah kualitas oke",
        "Respon penjual cepat dan ramah",
    ]
    extractor = TagExtractor()
    tagged, global_tags = extractor.extract_for_comments(sample_comments)
    print("Tagged:")
    for row in tagged:
        print(row)
    print("Global tags:", global_tags)


if __name__ == "__main__":
    demo()
