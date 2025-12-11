"""
Comment Tagger: Extract tags/labels from comments based on keywords.
Tags are derived from the most frequently mentioned topics in comments.
"""

import json
import re
from typing import List, Dict, Optional
from collections import Counter

# Dictionary of common issue keywords and their tags
KEYWORD_MAPPING = {
    # Pengiriman (Shipping)
    'pengiriman': 'Pengiriman Buruk',
    'kurir': 'Pengiriman Buruk',
    'ongkir': 'Pengiriman Buruk',
    'lambat': 'Pengiriman Buruk',
    'hilang': 'Pengiriman Buruk',
    'rusak': 'Barang Rusak',
    'packing': 'Pengiriman Buruk',
    'packaging': 'Pengiriman Buruk',
    
    # Kualitas (Quality)
    'kualitas': 'Kualitas Buruk',
    'jelek': 'Kualitas Buruk',
    'buruk': 'Kualitas Buruk',
    'bagus': 'Kualitas Bagus',
    'bagus sekali': 'Kualitas Bagus',
    'sempurna': 'Kualitas Bagus',
    
    # Barang Tidak Sesuai (Product Mismatch)
    'tidak sesuai': 'Barang Tidak Sesuai',
    'beda': 'Barang Tidak Sesuai',
    'palsu': 'Barang Tidak Sesuai',
    'tidak original': 'Barang Tidak Sesuai',
    'fake': 'Barang Tidak Sesuai',
    'replika': 'Barang Tidak Sesuai',
    'kw': 'Barang Tidak Sesuai',
    
    # Harga (Price)
    'mahal': 'Harga Mahal',
    'murah': 'Harga Murah',
    'harga': 'Harga',
    'promo': 'Promo/Diskon',
    'diskon': 'Promo/Diskon',
    
    # Penjual (Seller)
    'penjual': 'Masalah Penjual',
    'respon': 'Respon Lambat',
    'tidak respon': 'Respon Lambat',
    'customer service': 'Layanan Customer Service',
    'cs': 'Layanan Customer Service',
    'komunikasi': 'Komunikasi Buruk',
    
    # Ukuran/Ukuran (Size)
    'ukuran': 'Masalah Ukuran',
    'ketat': 'Masalah Ukuran',
    'longgar': 'Masalah Ukuran',
    'size': 'Masalah Ukuran',
    
    # Warna (Color)
    'warna': 'Warna Tidak Sesuai',
    'pudar': 'Warna Tidak Sesuai',
    'merah': 'Warna',
    'biru': 'Warna',
    
    # Pendapat Positif (Positive)
    'rekomendasi': 'Direkomendasikan',
    'rekomen': 'Direkomendasikan',
    'beli lagi': 'Akan Beli Lagi',
    'beli ulang': 'Akan Beli Lagi',
    'puas': 'Puas',
    'memuaskan': 'Puas',
    'senang': 'Senang',
    'suka': 'Senang',
    
    # Masalah Lainnya
    'cacat': 'Barang Cacat',
    'tidak berfungsi': 'Tidak Berfungsi',
    'error': 'Tidak Berfungsi',
    'expired': 'Produk Expired',
}

def _clean_text(text: str) -> str:
    """Normalize text for keyword matching."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    return text.strip()

def _extract_keywords(text: str) -> List[str]:
    """Extract keywords from text."""
    cleaned = _clean_text(text)
    words = cleaned.split()
    keywords = []
    
    # Check for multi-word keywords first
    for i in range(len(words)):
        for j in range(i + 1, min(i + 4, len(words) + 1)):  # max 3-word phrases
            phrase = ' '.join(words[i:j])
            if phrase in KEYWORD_MAPPING:
                keywords.append(phrase)
    
    # Check single words
    for word in words:
        if word in KEYWORD_MAPPING and word not in keywords:
            keywords.append(word)
    
    return keywords

def _get_tags_from_comment(comment_text: str) -> List[str]:
    """Extract tags from a single comment."""
    if not comment_text:
        return []
    
    keywords = _extract_keywords(comment_text)
    tags = []
    
    for keyword in keywords:
        if keyword in KEYWORD_MAPPING:
            tag = KEYWORD_MAPPING[keyword]
            if tag not in tags:
                tags.append(tag)
    
    return tags

def tag_comments(reviews: List[Dict], source_field: str = 'comment') -> List[Dict]:
    """
    Add tags to each comment based on keyword extraction.
    
    Args:
        reviews: List of review dicts
        source_field: Field name containing comment text (default: 'comment')
    
    Returns:
        List of reviews with 'tags' field added
    """
    tagged_reviews = []
    all_tags_counter = Counter()
    
    for review in reviews:
        review_copy = dict(review)
        comment_text = review.get(source_field, '')
        tags = _get_tags_from_comment(comment_text)
        review_copy['tags'] = tags
        tagged_reviews.append(review_copy)
        
        # Count tags for statistics
        for tag in tags:
            all_tags_counter[tag] += 1
    
    return tagged_reviews

def get_tag_statistics(reviews: List[Dict]) -> Dict[str, int]:
    """
    Get statistics on tags across all reviews.
    
    Returns:
        Dict mapping tag name to count
    """
    all_tags = Counter()
    for review in reviews:
        tags = review.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                all_tags[tag] += 1
    
    return dict(all_tags.most_common())

def get_top_tags(reviews: List[Dict], top_n: int = 10) -> List[tuple]:
    """
    Get top N most frequent tags.
    
    Returns:
        List of (tag, count) tuples
    """
    stats = get_tag_statistics(reviews)
    return sorted(stats.items(), key=lambda x: x[1], reverse=True)[:top_n]

if __name__ == '__main__':
    # Test
    test_reviews = [
        {'comment': 'Pengiriman lambat, barang sampai rusak. Sangat kecewa!'},
        {'comment': 'Barang bagus sekali, puas dengan pembelian ini.'},
        {'comment': 'Tidak sesuai deskripsi, ternyata palsu.'},
        {'comment': 'Kualitas buruk, harga mahal. Tidak recommended.'},
        {'comment': 'Kurir tidak respon, pengiriman hilang.'},
    ]
    
    tagged = tag_comments(test_reviews, source_field='comment')
    print(json.dumps(tagged, indent=2, ensure_ascii=False))
    
    print("\nTag Statistics:")
    stats = get_tag_statistics(tagged)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
