from typing import Dict
from bs4 import BeautifulSoup
import re

def parse_duthao_qh(r) -> Dict:
    html = r.cleaned_html or ""
    soup = BeautifulSoup(html, "lxml")
    out = {}

    # số hiệu, cơ quan, ngày… fallback markdown
    from src.parsers.base import common_fields_from_markdown
    import re
    out.update(common_fields_from_markdown(r.markdown or ""))

    # đếm ý kiến & link (cấu trúc có thể thay đổi; dùng select an toàn)
    # ví dụ: span.counter-comments, a[href*="ykien"]
    cnt = soup.select_one("span.counter-comments") or soup.find(string=lambda x: x and "ý kiến" in x.lower())
    so = None
    if cnt:
        m = re.search(r"(\d+)\s*ý\s*kiến", cnt.get_text(strip=True).lower()) if hasattr(cnt, "get_text") else re.search(r"(\d+)\s*ý\s*kiến", str(cnt).lower())
        if m: so = int(m.group(1))

    link = None
    a = soup.find("a", href=True, string=lambda s: s and "ý kiến" in s.lower()) or soup.find("a", href=True, attrs={"href": re.compile("ykien|y-kien|binhluan", re.I)})
    if a: link = a["href"]

    # thời hạn lấy ý kiến
    deadline = None
    dnode = soup.find(string=lambda s: s and ("hạn cuối" in s.lower() or "kết thúc lấy ý kiến" in s.lower()))
    if dnode:
        import dateutil.parser as dtp
        import re
        m = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})", dnode)
        if m:
            try: deadline = dtp.parse(m.group(1), dayfirst=True).date().isoformat()
            except: pass

    # thử liệt kê nội dung các bình luận công khai (nếu có)
    comments = []
    for c in soup.select(".comment-item, .ykien-item"):
        author = (c.select_one(".author") or c.select_one(".name") or c.select_one(".user")).get_text(strip=True) if c.select_one(".author, .name, .user") else None
        body = (c.select_one(".content") or c).get_text(" ", strip=True)
        comments.append({"author": author, "text": body})

    out.update({
        "trang_thai": "du_thao",
        "du_thao": {
            "dang_lay_y_kien": True,
            "ngay_bat_dau": None,
            "ngay_ket_thuc": deadline,
            "so_luong_y_kien": so,
            "link_y_kien": link,
            "noi_dung_y_kien": comments[:100]  # tránh quá dài
        }
    })
    return out
