import re
import hashlib
import unicodedata
from datetime import datetime
from typing import Optional


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _slugify(text: str) -> str:
    text = _strip_accents(text or "").lower()
    text = re.sub(r"[^a-z0-9/\-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def _normalize_doc_number(doc_number: str) -> str:
    # Giữ chữ số và dấu '/', thay khoảng trắng bằng '-' để ổn định id
    s = (doc_number or "").strip()
    s = re.sub(r"\s+", "-", s)
    return s


def _normalize_date(d: str) -> str:
    s = (d or "").strip()
    if not s:
        return s
    # Chuẩn hóa về YYYY-MM-DD nếu có thể
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    return s  # giữ nguyên nếu không parse được


def compute_canonical_doc_id(source_code: str, doc_type: str, doc_number: str, issue_date: str) -> str:
    """Sinh doc_id chuẩn dạng: {src}_{doctype}_{docnum}_{issuedate}_{hash12}

    - source_code: mã nguồn rút gọn (vd: mic, moj, gov, vbpl)
    - doc_type: vd: nghi_dinh, luat, thong_tu, quyet_dinh, nghi_quyet, du_thao
    - doc_number: vd: 13/2023/NĐ-CP
    - issue_date: 'YYYY-MM-DD' (hoặc nhiều định dạng thông dụng)
    """
    src = _slugify(source_code)
    doctype = _slugify(doc_type)
    number = _normalize_doc_number(doc_number)
    issued = _normalize_date(issue_date)

    key = f"{src}_{doctype}_{number}_{issued}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"{src}_{doctype}_{number}_{issued}_{h}"
