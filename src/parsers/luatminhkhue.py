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

def parse_lmk(r) -> Dict:
    """
    Parser cho luatminhkhue.vn.
    Lưu ý: nhiều bài là bản tin/phan tích, không phải VB chính thức.
    Vẫn cố gắng trích 'Số hiệu/Ngày/Cơ quan' nếu bài có nhúng bảng thông tin văn bản;
    nếu không có, fallback từ markdown (khi bài đăng kèm trích yếu văn bản).
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

    info_text = {}

    # 1) Thử tìm bảng "Thông tin văn bản" nếu có chèn lại từ nguồn
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
            elif "hiệu lực" in k:
                tmp["ngay_hieu_luc"] = v; score += 1
            elif "trạng thái" in k or "tình trạng" in k:
                tmp["trang_thai"] = v; score += 1
        if score >= 2:
            info_text.update(tmp)
            break

    # 2) Nếu bài chỉ là phân tích, có thể có đoạn tiêu đề/đoạn đầu nhắc “Theo Nghị định ... số .../..../...”
    if not info_text:
        article = soup.find("article") or soup.find("div", class_=re.compile("content|entry|post", re.I))
        text = _pick_text(article) if article else ""
        # Bắt pattern số hiệu dạng: 123/2024/NĐ-CP, 12/TT-BTTTT, v.v.
        m = re.search(r"(\b\d{1,3}/\d{4}/[A-ZĐ\-]+[A-Z\-]+|\b\d{1,3}/[A-Z]{1,5}[-/][A-Z0-9\-]+)", text)
        if m:
            info_text["so_hieu"] = m.group(1)
        # Cơ quan ban hành (heuristic)
        m2 = re.search(r"(Bộ\s+[^\.,\n]+|Chính phủ|Thủ tướng Chính phủ|Bộ Thông tin và Truyền thông|Bộ Khoa học và Công nghệ)", text, re.I)
        if m2:
            info_text["co_quan_ban_hanh"] = m2.group(1)
        # Ngày ban hành (dạng dd/mm/yyyy hoặc tháng ... năm ...)
        m3 = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", text)
        if m3:
            info_text["ngay_ban_hanh"] = m3.group(1)

    # 3) Ánh xạ & chuẩn hoá
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
            # Mặc định bài phân tích không xác định được, coi là còn hiệu lực nếu không nói ngược lại
            out["trang_thai"] = "con_hieu_luc"

    # 4) Fallback markdown
    md_fields = common_fields_from_markdown(r.markdown or "")
    for k in ["so_hieu", "co_quan_ban_hanh", "ngay_ban_hanh", "ngay_hieu_luc"]:
        if not out.get(k):
            out[k] = md_fields.get(k)

    # 5) Trạng thái cuối cùng
    if not out["trang_thai"]:
        blob = " ".join(filter(None, [r.title, r.markdown, r.extracted_text])).lower()
        if "dự thảo" in blob:
            out["trang_thai"] = "du_thao"
        elif any(x in blob for x in ["hết hiệu lực", "bãi bỏ", "thay thế"]):
            out["trang_thai"] = "het_hieu_luc"
        else:
            out["trang_thai"] = "con_hieu_luc"

    return out
