import re
from typing import Dict
DOC_TYPE_PATTERNS = {
    "NGHI_DINH": r"\bNghị\s*định\b|\bND-CP\b",
    "NGHI_QUYET": r"\bNghị\s*quyết\b|\bNQ\b",
    "THONG_TU": r"\bThông\s*tư\b|\bTT\b",
    "QUYET_DINH": r"\bQuyết\s*định\b|\bQĐ\b",
    "LUAT": r"\bLuật\b",
    "DU_THAO": r"\bDự\s*thảo\b|\blấy ý kiến\b"
}
def detect_doc_type(text: str):
    for k, pat in DOC_TYPE_PATTERNS.items():
        if re.search(pat, text, flags=re.I):
            return k
    return None

def common_fields_from_markdown(md: str) -> Dict:
    import re
    def _date(s):
        import dateutil.parser as dtp
        try: return dtp.parse(s, dayfirst=True).date().isoformat()
        except: return None
    so = re.search(r"(Số[:\s]+|No\.)\s*([A-Z0-9/\-\.]+)", md, re.I)
    nb = re.search(r"(Ngày ban hành|Ban hành)\s*[:\-]?\s*([^\n]+)", md, re.I)
    nl = re.search(r"(Hiệu lực|Có hiệu lực từ)\s*[:\-]?\s*([^\n]+)", md, re.I)
    cq = re.search(r"(Cơ quan ban hành|Cơ quan)\s*[:\-]?\s*([^\n]+)", md, re.I)
    return {
        "so_hieu": so.group(2) if so else "",
        "ngay_ban_hanh": _date(nb.group(2)) if nb else None,
        "ngay_hieu_luc": _date(nl.group(2)) if nl else None,
        "co_quan_ban_hanh": cq.group(2).strip() if cq else ""
    }
