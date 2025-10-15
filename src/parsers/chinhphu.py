from typing import Dict, Optional
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

def parse_chinhphu(r) -> Dict:
    """
    Heuristic parser cho chinhphu.vn (Hệ thống văn bản / Dự thảo VBQPPL).
    Trích: số hiệu, cơ quan, ngày ban hành, ngày hiệu lực, trạng thái.
    Không xử lý phần góp ý (site này thường không public comment nội dung).
    """
    html = r.cleaned_html or ""
    soup = BeautifulSoup(html, "lxml")

    out = {
        "so_hieu": "",
        "co_quan_ban_hanh": "",
        "ngay_ban_hanh": None,
        "ngay_hieu_luc": None,
        "trang_thai": None,
    }

    # 1) Khối thông tin thường ở dạng bảng 2 cột hoặc dl/dt/dd
    # Thử các cách phổ biến:
    info_text = {}

    # a) Bảng 2 cột: "Số/Ký hiệu", "Cơ quan ban hành", "Ngày ban hành", "Ngày hiệu lực", "Trạng thái"
    for table in soup.find_all(["table"]):
        rows = table.find_all("tr")
        score = 0
        tmp = {}
        for tr in rows:
            tds = tr.find_all(["td", "th"])
            if len(tds) < 2:
                continue
            k = _pick_text(tds[0]).lower()
            v = _pick_text(tds[1])
            if any(lbl in k for lbl in ["số", "ký hiệu", "số/ký hiệu", "số hiệu", "ký hiệu"]):
                tmp["so_hieu"] = v
                score += 1
            elif "cơ quan" in k:
                tmp["co_quan_ban_hanh"] = v
                score += 1
            elif "ngày ban hành" in k or "ban hành" in k:
                tmp["ngay_ban_hanh"] = v
                score += 1
            elif "hiệu lực" in k:
                tmp["ngay_hieu_luc"] = v
                score += 1
            elif "trạng thái" in k:
                tmp["trang_thai"] = v
                score += 1
        if score >= 2:
            info_text.update(tmp)
            break

    # b) dl/dt/dd
    if not info_text:
        for dl in soup.find_all("dl"):
            items = dl.find_all(["dt", "dd"])
            if not items:
                continue
            tmp = {}
            key = None
            for el in items:
                if el.name == "dt":
                    key = _pick_text(el).lower()
                elif el.name == "dd" and key:
                    v = _pick_text(el)
                    if any(lbl in key for lbl in ["số", "ký hiệu", "số/ký hiệu", "số hiệu", "ký hiệu"]):
                        tmp["so_hieu"] = v
                    elif "cơ quan" in key:
                        tmp["co_quan_ban_hanh"] = v
                    elif "ngày ban hành" in key or "ban hành" in key:
                        tmp["ngay_ban_hanh"] = v
                    elif "hiệu lực" in key:
                        tmp["ngay_hieu_luc"] = v
                    elif "trạng thái" in key:
                        tmp["trang_thai"] = v
                    key = None
            if tmp:
                info_text.update(tmp)
                break

    # 2) Gán vào out (chuẩn hoá ngày)
    if info_text:
        out["so_hieu"] = info_text.get("so_hieu", "") or ""
        out["co_quan_ban_hanh"] = info_text.get("co_quan_ban_hanh", "") or ""
        out["ngay_ban_hanh"] = _norm_date(info_text.get("ngay_ban_hanh"))
        out["ngay_hieu_luc"] = _norm_date(info_text.get("ngay_hieu_luc"))
        raw_tt = (info_text.get("trang_thai") or "").lower()
        if any(x in raw_tt for x in ["hết hiệu lực", "bãi bỏ", "thay thế"]):
            out["trang_thai"] = "het_hieu_luc"
        elif "dự thảo" in raw_tt:
            out["trang_thai"] = "du_thao"
        else:
            out["trang_thai"] = "con_hieu_luc"

    # 3) Fallback từ markdown nếu còn thiếu
    md_fields = common_fields_from_markdown(r.markdown or "")
    for k in ["so_hieu", "co_quan_ban_hanh", "ngay_ban_hanh", "ngay_hieu_luc"]:
        if not out.get(k):
            out[k] = md_fields.get(k)

    # 4) Nếu vẫn chưa có trạng thái, suy luận nhẹ từ title/text
    if not out["trang_thai"]:
        blob = " ".join(filter(None, [r.title, r.markdown, r.extracted_text])).lower()
        if "dự thảo" in blob:
            out["trang_thai"] = "du_thao"
        elif any(x in blob for x in ["hết hiệu lực", "bãi bỏ", "thay thế"]):
            out["trang_thai"] = "het_hieu_luc"
        else:
            out["trang_thai"] = "con_hieu_luc"

    return out
