# src/pipeline/patterns.py
import re

# Ví dụ: "Nghị định 260/2025/NĐ-CP", "Thông tư 19/2014/TT-BKHCN", "Quyết định 187/QĐ-TTg"
LEGAL_ID_PATTERNS = [
    re.compile(r"\b(Nghị\s*định)\s+([0-9]+\/[0-9]{4}\/NĐ-CP)\b", re.IGNORECASE),
    re.compile(r"\b(Thông\s*tư)\s+([0-9]+\/[0-9]{4}\/TT-[A-ZĐ]+)\b", re.IGNORECASE),
    re.compile(r"\b(Quyết\s*định)\s+([0-9]+\/QĐ-?[A-ZĐ]+)\b", re.IGNORECASE),
    re.compile(r"\b(Nghị\s*quyết)\s+([0-9]+\/NQ-[A-ZĐ]+)\b", re.IGNORECASE),
    re.compile(r"\b(VBHN)\s+([0-9]+\/[A-Z]+)\b", re.IGNORECASE),
    # Bản tin Chính phủ/Thông báo/Tờ trình...
    re.compile(r"\b(Thông\s*báo)\s+([0-9]+\/TB-[A-ZĐ]+)\b", re.IGNORECASE),
]

def find_legal_ids(text: str) -> list[dict]:
    hits = []
    for pat in LEGAL_ID_PATTERNS:
        for m in pat.finditer(text):
            hits.append({
                "type": m.group(1).strip(),
                "code": m.group(2).strip(),
                "span": [m.start(), m.end()],
            })
    return hits
