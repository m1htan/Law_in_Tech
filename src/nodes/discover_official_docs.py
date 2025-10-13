import re
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin
import feedparser
from bs4 import BeautifulSoup
from src.utils.logger import get_logger
from src.utils.http_client import get
from src.utils.db import DB

logger = get_logger("DiscoverOfficialDocs")

LAW_REGEX = re.compile(r"(?i)\b(Luật|Nghị[ \-]?định|Thông[ \-]?tư|Dự thảo)\b")

def _discover_from_rss(base_url: str) -> List[Dict[str, Optional[str]]]:
    items = []
    # Thử các đường RSS phổ biến
    candidates = [
        base_url.rstrip("/") + "/rss",
        base_url.rstrip("/") + "/rss.aspx",
        base_url.rstrip("/") + "/rssfeed",
        base_url,  # trong trường hợp base_url chính là feed
    ]
    seen = set()
    for u in candidates:
        try:
            feed = feedparser.parse(u)
            if not feed or not feed.entries:
                continue
            for e in feed.entries:
                if hasattr(e, "link") and e.link not in seen:
                    seen.add(e.link)
                    items.append({
                        "url": e.link,
                        "title": getattr(e, "title", None),
                        "published_at": getattr(e, "published", None) or getattr(e, "updated", None)
                    })
        except Exception:
            continue
    return items

def _discover_from_sitemap(base_url: str) -> List[Dict[str, Optional[str]]]:
    items = []
    sitemap_candidates = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
    ]
    for sm in sitemap_candidates:
        resp = get(sm, timeout=15)
        if not resp:
            continue
        try:
            soup = BeautifulSoup(resp.text, "xml")
            for loc in soup.find_all("loc"):
                url = loc.text.strip()
                if LAW_REGEX.search(url):
                    items.append({"url": url, "title": None, "published_at": None})
        except Exception:
            continue
    return items

def _discover_from_static(base_url: str) -> List[Dict[str, Optional[str]]]:
    items = []
    resp = get(base_url, timeout=15)
    if not resp:
        return items
    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(" ", strip=True)
        if LAW_REGEX.search(text) or LAW_REGEX.search(href):
            items.append({"url": href, "title": text or None, "published_at": None})
    return items

def run(state: dict) -> dict:
    cfg = state["config"]
    db = DB(
        primary=cfg["database"]["primary"],
        sqlite_path=cfg["database"]["sqlite_path"],
        postgres_uri=cfg["database"]["postgres_uri"],
    )

    delay = float(cfg["graph"].get("crawl_delay_sec", 1.5))
    discovered: List[Dict[str, Any]] = []

    for s in state.get("sources", []):
        if not s.get("enabled", True):
            continue
        if s.get("type") != "official":
            continue

        base_url = s["base_url"].rstrip("/")
        method = (s.get("crawl_method") or "static").lower()

        if method == "rss":
            items = _discover_from_rss(base_url)
        elif method == "sitemap":
            items = _discover_from_sitemap(base_url)
        else:
            items = _discover_from_static(base_url)

        # Lưu vào DB, lọc chỉ văn bản/điểm có vẻ liên quan
        inserted = 0
        for it in items:
            title = it.get("title") or ""
            url = it.get("url") or ""
            if not url:
                continue
            if title and not LAW_REGEX.search(title) and not LAW_REGEX.search(url):
                # bỏ link không có dấu hiệu văn bản
                continue
            ok = db.insert_document_if_new(
                source_id=s["source_id"],
                url=url,
                title=title,
                published_at=it.get("published_at"),
            )
            if ok:
                inserted += 1
                discovered.append({
                    "source": s["name"],
                    "url": url,
                    "title": title,
                    "published_at": it.get("published_at")
                })
        logger.info(f"[{s['name']}] method={method} -> found={len(items)} inserted_new={inserted}")
        time.sleep(delay)

    state["discovered_docs"] = discovered
    return state
