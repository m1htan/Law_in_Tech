# src/parsers/duthao_qh.py
import re
import time
from typing import Iterator, Tuple, Optional, Dict, Any
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import BrowserContext, Page

DATE_PAT = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})")

def parse_vi_date(s: str) -> Optional[datetime]:
    if not s:
        return None
    m = DATE_PAT.search(s)
    if not m:
        return None
    d, mth, y = map(int, m.groups())
    try:
        return datetime(y, mth, d, tzinfo=timezone.utc)
    except Exception:
        return None

def _get(session: requests.Session, url: str) -> requests.Response:
    return session.get(url, timeout=30)

def _extract_pdf(html: str, base_url: str) -> Optional[str]:
    from urllib.parse import urljoin
    s = BeautifulSoup(html, "lxml")
    # tìm link .pdf
    for a in s.select("a[href]"):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            return href if href.startswith("http") else urljoin(base_url, href)
    return None

def _extract_comments(html: str) -> list[dict]:
    s = BeautifulSoup(html, "lxml")
    comments = []
    # các khối bình luận khác nhau; đây là selector “chịu lỗi”
    for c in s.select(".comment, .comment-item, li.ykien, .ykien"):
        author = c.select_one(".author, .name")
        author = author.get_text(strip=True) if author else None
        date = c.select_one(".date, .time")
        date = date.get_text(strip=True) if date else None
        body = c.get_text(" ", strip=True)
        comments.append({"author": author, "date": date, "text": body})
    return comments

def crawl_duthao_qh(context: BrowserContext, date_min: datetime) -> Iterator[Tuple[Dict[str, Any], Optional[bytes]]]:
    base = "https://duthaoonline.quochoi.vn/"
    session = requests.Session()
    page: Page = context.new_page()
    page.goto(base, wait_until="load", timeout=60_000)

    # Xác định pattern phân trang: ưu tiên click nút "Tiếp"/số trang
    # Nếu không, fallback tự tạo ?page= i
    def collect_list_links() -> list[str]:
        soup = BeautifulSoup(page.content(), "lxml")
        links = []
        for a in soup.select("a[href]"):
            href = a["href"].strip()
            if "chi-tiet" in href or "du-thao" in href:
                if href.startswith("http"):
                    links.append(href)
                else:
                    from urllib.parse import urljoin
                    links.append(urljoin(base, href))
        # unique order
        out, seen = [], set()
        for u in links:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out

    def has_next() -> bool:
        # nhiều site dùng “>” hoặc “Trang sau”
        for sel in [
            "a.page-link[rel='next']",
            "a[aria-label='Next']",
            "a:has-text('Sau')",
            "a:has-text('Tiếp')",
            "li.next a"
        ]:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_enabled():
                return True
        return False

    def click_next() -> bool:
        for sel in [
            "a.page-link[rel='next']",
            "a[aria-label='Next']",
            "a:has-text('Sau')",
            "a:has-text('Tiếp')",
            "li.next a"
        ]:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_enabled():
                loc.first.click()
                page.wait_for_timeout(1200)
                return True
        return False

    seen_detail = set()
    page_idx = 1
    while True:
        links = collect_list_links()
        for url in links:
            if url in seen_detail:
                continue
            seen_detail.add(url)

            try:
                r = _get(session, url)
                if r.status_code != 200:
                    continue

                s = BeautifulSoup(r.text, "lxml")
                title = s.select_one("h1, .title, .detail-title")
                title = title.get_text(strip=True) if title else ""

                raw = s.get_text(" ", strip=True)
                # Mốc thời gian lấy ý kiến
                ngay_bd = None
                ngay_kt = None
                m = re.search(r"(Từ ngày|Bắt đầu)\s*:?\s*([0-9/\-]{8,10})", raw, re.I)
                if m:
                    ngay_bd = parse_vi_date(m.group(2))
                m = re.search(r"(Đến ngày|Kết thúc)\s*:?\s*([0-9/\-]{8,10})", raw, re.I)
                if m:
                    ngay_kt = parse_vi_date(m.group(2))

                ngay_any = parse_vi_date(raw)

                pdf_url = _extract_pdf(r.text, url)
                pdf_bytes = None
                if pdf_url:
                    pr = session.get(pdf_url, timeout=60)
                    if pr.ok and "pdf" in pr.headers.get("content-type", "").lower():
                        pdf_bytes = pr.content

                comments = _extract_comments(r.text)

                rec = {
                    "source": "duthaoonline.quochoi.vn",
                    "html_url": url,
                    "tieu_de": title,
                    "ngay_cong_bo": (ngay_any or ngay_bd or ngay_kt).isoformat() if (ngay_any or ngay_bd or ngay_kt) else None,
                    "ngay_cong_bo_dt": (ngay_any or ngay_bd or ngay_kt),
                    "du_thao": {
                        "dang_lay_y_kien": True,
                        "ngay_bat_dau": ngay_bd.isoformat() if ngay_bd else None,
                        "ngay_ket_thuc": ngay_kt.isoformat() if ngay_kt else None,
                        "so_luong_y_kien": len(comments),
                        "noi_dung_y_kien": comments,
                    },
                    "attachments": [{"type": "pdf", "url": pdf_url}] if pdf_url else [],
                    "trang_thai": "du_thao",
                    "crawled_at": datetime.now(timezone.utc).isoformat(),
                }
                yield rec, pdf_bytes
            except Exception:
                continue

        # next page?
        if has_next():
            if not click_next():
                break
            page_idx += 1
            continue
        else:
            break

    page.close()