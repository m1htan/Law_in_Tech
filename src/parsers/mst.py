# src/parsers/mst.py
import re
import time
import json
from typing import Iterator, Tuple, Optional, Dict, Any
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import BrowserContext, Page, TimeoutError as PWTimeout

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

def _extract_pdf_from_detail(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select("a[href]"):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            if href.startswith("http"):
                return href
            # join relative
            from urllib.parse import urljoin
            return urljoin(base_url, href)
    return None

def _get(session: requests.Session, url: str, **kw) -> requests.Response:
    return session.get(url, timeout=30, **kw)

def crawl_mst(context: BrowserContext, date_min: datetime) -> Iterator[Tuple[Dict[str, Any], Optional[bytes]]]:
    base = "https://mst.gov.vn/van-ban-phap-luat.htm"
    page: Page = context.new_page()
    session = requests.Session()
    try:
        page.goto(base, wait_until="load", timeout=60_000)
    except PWTimeout:
        page.goto(base, wait_until="domcontentloaded")

    # click "Xem thêm" cho tới khi hết hoặc đã tới trước 2022
    last_seen_count = -1
    while True:
        cards = page.locator("div.list-news div.item, div.list-post div.post, article, li").all()
        # đơn giản: nếu không tăng thì break
        if len(cards) <= last_seen_count:
            break
        last_seen_count = len(cards)

        # thử bấm "Xem thêm"
        clicked = False
        for locator in [
            page.get_by_text("Xem thêm", exact=False),
            page.locator("button:has-text('Xem thêm')"),
            page.locator("a:has-text('Xem thêm')")
        ]:
            if locator.count() > 0 and locator.first.is_visible():
                try:
                    locator.first.click(timeout=5_000)
                    page.wait_for_timeout(1500)
                    clicked = True
                    break
                except Exception:
                    pass

        # Nếu không click thêm được, dừng
        if not clicked:
            break

        # Nếu có ngày cũ hơn date_min trong trang, vẫn cần đi tiếp vì load-more thường thêm ở dưới
        # => không dừng sớm theo ngày (tránh bỏ sót)

    # Lấy toàn bộ link chi tiết có trong trang
    html = page.content()
    soup = BeautifulSoup(html, "lxml")
    detail_links = []
    for a in soup.select("a[href]"):
        href = a["href"].strip()
        # Lọc các link chi tiết khả năng cao chứa VBPL
        if ("van-ban" in href or "van-ban-phap-luat" in href or "chi-tiet" in href) and not href.endswith(".pdf"):
            if href.startswith("http"):
                detail_links.append(href)
            else:
                from urllib.parse import urljoin
                detail_links.append(urljoin(base, href))

    # unique preserve order
    seen = set()
    links = []
    for u in detail_links:
        if u not in seen:
            seen.add(u)
            links.append(u)

    # Duyệt từng chi tiết
    for url in links:
        try:
            r = _get(session, url)
            if r.status_code != 200:
                continue
            s = BeautifulSoup(r.text, "lxml")

            title = s.select_one("h1, .title-detail, .detail-title")
            title = title.get_text(strip=True) if title else ""

            # Ngày ban hành xuất hiện nhiều kiểu
            raw_text = s.get_text(" ", strip=True)
            ngay = None
            for lab in ["Ngày ban hành", "Ngày ký", "Ngày hiệu lực", "Ban hành ngày"]:
                m = re.search(lab + r"\s*:?\s*([0-9/\-]{8,10})", raw_text, re.I)
                if m:
                    ngay = parse_vi_date(m.group(1))
                    break
            if not ngay:
                # fallback: tìm date “dd/mm/yyyy” gần tiêu đề
                ngay = parse_vi_date(raw_text)

            if ngay and ngay < date_min:
                continue

            # Số hiệu
            so_hieu = None
            m = re.search(r"(Số|Số hiệu)\s*:?\s*([A-Za-z0-9/.\-]+)", raw_text, re.I)
            if m:
                so_hieu = m.group(2).strip()

            pdf_url = _extract_pdf_from_detail(r.text, url)
            pdf_bytes = None
            if pdf_url:
                try:
                    pr = session.get(pdf_url, timeout=60)
                    if pr.ok and pr.headers.get("content-type", "").lower().startswith("application/pdf"):
                        pdf_bytes = pr.content
                except Exception:
                    pdf_bytes = None

            rec = {
                "source": "mst.gov.vn",
                "html_url": url,
                "tieu_de": title,
                "so_hieu": so_hieu,
                "ngay_ban_hanh": ngay.isoformat() if ngay else None,
                "ngay_ban_hanh_dt": ngay,
                "attachments": [{"type": "pdf", "url": pdf_url}] if pdf_url else [],
                "trang_thai": "con_hieu_luc",  # văn bản ban hành
                "crawled_at": datetime.now(timezone.utc).isoformat(),
            }
            yield rec, pdf_bytes
        except Exception:
            continue
    page.close()