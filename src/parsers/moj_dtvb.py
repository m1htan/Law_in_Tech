# parsers/moj_dtvb.py
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
from dateutil import parser as dtp
import re
from .base import common_fields_from_markdown

def _norm_date(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        return dtp.parse(s, dayfirst=True).date().isoformat()
    except Exception:
        return None

def _pick_text(el):
    return el.get_text(" ", strip=True) if el else ""

def _get_attr(obj: Any, names: List[str], default=None):
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
        if isinstance(obj, dict) and n in obj and obj[n] is not None:
            return obj[n]
        if hasattr(obj, "metadata"):
            meta = getattr(obj, "metadata")
            if isinstance(meta, dict) and n in meta and meta[n] is not None:
                return meta[n]
    return default

def _normalize_fields(res: Any, parent_url: Optional[str] = None) -> Dict[str, Optional[str]]:
    title = _get_attr(res, ["title", "page_title", "og_title"])
    markdown = _get_attr(res, ["markdown", "md", "content_markdown"])
    extracted_text = _get_attr(res, ["extracted_text", "text", "cleaned_text"])
    cleaned_html = _get_attr(res, ["cleaned_html", "html", "content_html"])
    url = _get_attr(res, ["url", "page_url"], default=parent_url)
    return {
        "title": title or "",
        "markdown": markdown or "",
        "extracted_text": extracted_text or "",
        "cleaned_html": cleaned_html or "",
        "url": url or (parent_url or "")
    }

def parse_moj_dtvb(res: Any, parent_url: Optional[str] = None) -> Dict:
    """
    Parser cho moj.gov.vn/dtvb — tương thích nhiều phiên bản Crawl4AI.
    Không truy cập trực tiếp r.title/...; dùng _normalize_fields.
    """
    norm = _normalize_fields(res, parent_url=parent_url)
    html = norm["cleaned_html"]
    md = norm["markdown"]
    title = norm["title"]
    soup = BeautifulSoup(html or "", "lxml")

    out = common_fields_from_markdown(md or "")

    # đếm ý kiến (nếu có hiển thị)
    cnt = soup.find(string=lambda s: s and "ý kiến" in s.lower())
    so = None
    if cnt:
        m = re.search(r"(\d+)\s*ý\s*kiến", cnt.lower())
        if m:
            so = int(m.group(1))

    # trạng thái dự thảo: heuristics từ title/markdown
    blob = " ".join(filter(None, [title, md, norm["extracted_text"]])).lower()
    is_draft = "dự thảo" in blob or "lấy ý kiến" in blob

    out.update({
        "trang_thai": "du_thao" if is_draft else out.get("trang_thai") or "con_hieu_luc",
        "du_thao": {
            "dang_lay_y_kien": bool(is_draft),
            "ngay_bat_dau": None,
            "ngay_ket_thuc": None,
            "so_luong_y_kien": so,
            "link_y_kien": norm["url"],
            "noi_dung_y_kien": []
        }
    })

    return out