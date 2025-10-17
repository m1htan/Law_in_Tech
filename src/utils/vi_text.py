# src/utils/vi_text.py
from __future__ import annotations
import re, unicodedata
from typing import List

VI_PUNCT = r"""!"#$%&'()*+,\-./:;<=>?@[\]^_`{|}~“”‘’…"""
PUNCT_RE = re.compile(f"[{re.escape(VI_PUNCT)}]")

# Bộ stopword gọn, có thể mở rộng dần
VI_STOPWORDS = {
    "và","hoặc","là","của","các","những","được","trong","theo","tại","với",
    "đến","từ","này","kia","đã","sẽ","đang","về","khi","nếu","như","cho",
    "trên","dưới","bằng","đối","v.v","…"
}

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\u00a0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def tokenize_vi(s: str) -> List[str]:
    s = normalize_text(s.lower())
    s = PUNCT_RE.sub(" ", s)
    toks = [t for t in s.split() if t and t not in VI_STOPWORDS and not t.isdigit()]
    return toks

def sentences(s: str) -> List[str]:
    s = normalize_text(s)
    # tách thô theo . ! ? ; xuống dòng
    parts = re.split(r"[\.!?;\n]+", s)
    return [p.strip() for p in parts if p.strip()]
