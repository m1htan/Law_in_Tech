# parsers/vbpl.py
from typing import Dict, Optional, Any, List
from bs4 import BeautifulSoup
import re
from dateutil import parser as dtp
from src.parsers.base import common_fields_from_markdown

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
    """
    Lấy thuộc tính theo danh sách tên khả dĩ qua nhiều phiên bản Crawl4AI.
    Hỗ trợ cả obj.attr, obj.metadata['...'] hoặc obj như dict.
    """
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

def parse_vbpl(res: Any, parent_url: Optional[str] = None) -> Dict:
    """
    Parser cho CSDL QG VBQPPL (vbpl.vn) — tương thích nhiều phiên bản Crawl4AI.
    Không truy cập trực tiếp r.title/... nữa; dùng _normalize_fields để trích field.
    """
    norm = _normalize_fields(res, parent_url=parent_url)
    html = norm["cleaned_html"]
    md = norm["markdown"]
    title = norm["title"]

    soup = BeautifulSoup(html or "", "lxml")
    out = {
        "so_hieu": "",
        "co_quan_ban_hanh": "",
        "ngay_ban_hanh": None,
        "ngay_hieu_luc": None,
        "trang_thai": None,
    }

    info_text = {}

    # 1) Bảng thông tin văn bản (thường có nhãn: Số/Ký hiệu, Cơ quan, Ngày ban hành, Ngày có hiệu lực, Tình trạng hiệu lực)
    for table in soup.find_all("table"):
        tmp = {}
        score = 0
        for tr in table.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            k = _pick_text(tds[0]).lower()
            v = _pick_text(tds[1])
            if any(lbl in k for lbl in ["số", "ký hiệu", "số/ký hiệu", "số hiệu", "ký hiệu"]):
                tmp["so_hieu"] = v; score += 1
            elif "cơ quan" in k:
                tmp["co_quan_ban_hanh"] = v; score += 1
            elif "ngày ban hành" in k or "ban hành" in k:
                tmp["ngay_ban_hanh"] = v; score += 1
            elif "có hiệu lực" in k or "ngày hiệu lực" in k or "hiệu lực" in k:
                tmp["ngay_hieu_luc"] = v; score += 1
            elif "tình trạng hiệu lực" in k or "tình trạng" in k or "trạng thái" in k:
                tmp["trang_thai"] = v; score += 1
        if score >= 2:
            info_text.update(tmp)
            break

    # 2) Nếu không thấy bảng, thử nhãn-giá trị trong các block văn bản
    if not info_text:
        for row in soup.select("li, p, div"):
            t = _pick_text(row)
            if not t:
                continue
            tl = t.lower()
            m = re.match(r"^([^:]{2,60}):\s*(.+)$", tl)
            if m:
                key = m.group(1)
                val = t.split(":", 1)[-1].strip()
                if any(lbl in key for lbl in ["số", "ký hiệu", "số/ký hiệu", "số hiệu", "ký hiệu"]):
                    info_text.setdefault("so_hieu", val)
                elif "cơ quan" in key:
                    info_text.setdefault("co_quan_ban_hanh", val)
                elif "ngày ban hành" in key or "ban hành" in key:
                    info_text.setdefault("ngay_ban_hanh", val)
                elif "có hiệu lực" in key or "ngày hiệu lực" in key or "hiệu lực" in key:
                    info_text.setdefault("ngay_hieu_luc", val)
                elif "tình trạng hiệu lực" in key or "tình trạng" in key or "trạng thái" in key:
                    info_text.setdefault("trang_thai", val)

    # 3) Chuẩn hoá
    if info_text:
        out["so_hieu"] = info_text.get("so_hieu", "") or ""
        out["co_quan_ban_hanh"] = info_text.get("co_quan_ban_hanh", "") or ""
        out["ngay_ban_hanh"] = _norm_date(info_text.get("ngay_ban_hanh"))
        out["ngay_hieu_luc"] = _norm_date(info_text.get("ngay_hieu_luc"))
        raw_tt = (info_text.get("trang_thai") or "").lower()
        if any(x in raw_tt for x in ["hết hiệu lực", "ngưng hiệu lực", "bãi bỏ", "thay thế"]):
            out["trang_thai"] = "het_hieu_luc"
        elif "dự thảo" in raw_tt:
            out["trang_thai"] = "du_thao"
        else:
            out["trang_thai"] = "con_hieu_luc"

    # 4) Fallback từ markdown nếu thiếu
    md_fields = common_fields_from_markdown(md or "")
    for k in ["so_hieu", "co_quan_ban_hanh", "ngay_ban_hanh", "ngay_hieu_luc"]:
        if not out.get(k):
            out[k] = md_fields.get(k)

    # 5) Suy luận trạng thái nếu còn None
    if not out["trang_thai"]:
        blob = " ".join(filter(None, [title, md, norm["extracted_text"]])).lower()
        if any(x in blob for x in ["hết hiệu lực", "bãi bỏ", "thay thế", "ngưng hiệu lực"]):
            out["trang_thai"] = "het_hieu_luc"
        elif "dự thảo" in blob:
            out["trang_thai"] = "du_thao"
        else:
            out["trang_thai"] = "con_hieu_luc"

    return out