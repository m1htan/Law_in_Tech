# src/pipeline/keyword_extractor.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
from .patterns import find_legal_ids
from ..utils.vi_text import normalize_text, sentences
import os

try:
    import yake
except Exception:
    yake = None

@dataclass
class KeywordItem:
    phrase: str
    score: float
    source: str  # "yake" | "regex" | "filename"

def top_keywords_from_text(text: str, topk: int = 15) -> List[KeywordItem]:
    text = normalize_text(text)
    kws: List[KeywordItem] = []

    # 1) Bắt định danh pháp lý bằng regex → coi như keyword ưu tiên
    for hit in find_legal_ids(text):
        kws.append(KeywordItem(phrase=f"{hit['type']} {hit['code']}", score=0.0, source="regex"))

    # 2) YAKE (nếu có)
    if yake:
        extractor = yake.KeywordExtractor(lan="vi", n=1, top=topk)
        for k, score in extractor.extract_keywords(text):
            # YAKE trả về (kw, score) ; score thấp hơn = quan trọng hơn
            kws.append(KeywordItem(phrase=k, score=float(score), source="yake"))

        # thêm n-gram 2 từ (hữu ích với TV)
        extractor2 = yake.KeywordExtractor(lan="vi", n=2, top=max(5, topk//2))
        for k, score in extractor2.extract_keywords(text):
            kws.append(KeywordItem(phrase=k, score=float(score), source="yake"))
    else:
        # YAKE không có → fallback: lấy cụm từ đầu câu có độ dài vừa
        for s in sentences(text)[:50]:
            toks = s.split()
            if 1 < len(toks) <= 6:
                kws.append(KeywordItem(phrase=s, score=1.0, source="fallback"))

    # 3) lọc trùng, chuẩn hóa
    seen = set()
    deduped = []
    for kw in sorted(kws, key=lambda x: (x.score, x.phrase.lower())):
        key = kw.phrase.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(kw)

    return deduped[: max(topk, 20)]  # giữ rộng chút

def keywords_from_filename(path: str) -> List[KeywordItem]:
    base = os.path.basename(path)
    stem = os.path.splitext(base)[0]
    # ví dụ: "260nd.signed.txt" → gợi ý "Nghị định 260"
    hints: List[KeywordItem] = []
    if "nd" in stem.lower():
        hints.append(KeywordItem(phrase="nghị định", score=0.5, source="filename"))
    if "ttg" in stem.lower():
        hints.append(KeywordItem(phrase="thủ tướng chính phủ", score=0.5, source="filename"))
    if "tt" in stem.lower():
        hints.append(KeywordItem(phrase="thông tư", score=0.5, source="filename"))
    if "nq" in stem.lower():
        hints.append(KeywordItem(phrase="nghị quyết", score=0.5, source="filename"))
    return hints
