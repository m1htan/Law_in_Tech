import os, re, time, json, orjson, hashlib
from datetime import datetime
from typing import List, Dict, Any
from dateutil import parser as dtp
import inspect
import requests
from bs4 import BeautifulSoup
from typing import Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from src.utils.robots import can_fetch
from src.utils.text_norm import norm_space
from src.utils.pdf_utils import fetch_and_extract_pdf
from src.parsers.base import detect_doc_type, common_fields_from_markdown
from src.parsers.chinhphu import parse_chinhphu
from src.parsers.vbpl import parse_vbpl
from src.parsers.duthao_qh import parse_duthao_qh
from src.parsers.moj_dtvb import parse_moj_dtvb
from src.parsers.luatminhkhue import parse_lmk

def _make_crawler(browser_cfg: BrowserConfig) -> AsyncWebCrawler:
    """Tạo AsyncWebCrawler tương thích các phiên bản crawl4ai khác nhau."""
    params = inspect.signature(AsyncWebCrawler).parameters
    if "crawler_strategy" in params:
        # Phiên bản mới: dùng strategy
        try:
            # vị trí module có thể khác giữa các bản
            from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        except Exception:
            from crawl4ai.crawler_strategy import AsyncPlaywrightCrawlerStrategy  # fallback
        strategy = AsyncPlaywrightCrawlerStrategy(browser_config=browser_cfg)
        return AsyncWebCrawler(crawler_strategy=strategy)
    elif "browser_config" in params:
        # Phiên bản cũ: truyền thẳng browser_config
        return AsyncWebCrawler(browser_config=browser_cfg)
    else:
        # Cuối cùng: không truyền gì, để mặc định
        return AsyncWebCrawler()

def _load_list(path):
    with open(path,"r",encoding="utf-8") as f:
        if path.endswith(".json"):
            return json.load(f)
        return [line.strip() for line in f if line.strip()]

import os, re

# Lấy thư mục gốc của file hiện tại (vd: crawlers/)
BASE_DIR = os.path.dirname(__file__)

# Đường dẫn tuyệt đối tới thư mục ../config/
CONFIG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "config"))

# Định nghĩa hàm load chung (không đổi)
def _load_list(path):
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith(".json"):
            import json
            return json.load(f)
        return [line.strip() for line in f if line.strip()]

# Đọc file cấu hình từ ../config/
ALLOW_DOMAINS = set(_load_list(os.path.join(CONFIG_DIR, "allow_domains.json")))
URL_ALLOWLIST_REGEX = [re.compile(p, re.I) for p in _load_list(os.path.join(CONFIG_DIR, "url_allow_regex.json"))]
KEYWORDS = [k.lower() for k in _load_list(os.path.join(CONFIG_DIR, "keywords.txt"))]

def _allowed(url: str) -> bool:
    return any(r.match(url) for r in URL_ALLOWLIST_REGEX)

def _domain(url: str) -> str:
    return re.sub(r"^https?://(www\.)?([^/]+)/?.*$", r"\2", url)

def _is_gov_vn(url: str) -> bool:
    try:
        host = _domain(url)
    except Exception:
        return False
    return host == "gov.vn" or host.endswith(".gov.vn")

def _throttle(domain: str):
    # throttle đơn giản theo domain (250–500ms)
    time.sleep(0.35)

def _make_run_config(**kwargs):
    sig = inspect.signature(CrawlerRunConfig)
    valid = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return CrawlerRunConfig(**valid)

def _requests_extract_links(url: str) -> list[str]:
    try:
        html = requests.get(url, timeout=30).text
    except Exception:
        return []
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        href = a["href"]
        if any(r.match(href) for r in URL_ALLOWLIST_REGEX):
            links.append(href)
    return list(dict.fromkeys(links))

def _default_run_config():
    return _make_run_config(
        cache_mode=getattr(CacheMode, "BYPASS", getattr(CacheMode, "DISABLED", None)),
        # KHÔNG truyền wait_for để tránh bị hiểu là CSS selector
        link_follow=True,
        allowed_domains=list(ALLOW_DOMAINS),
        allowed_regex=[r.pattern for r in URL_ALLOWLIST_REGEX],
        max_depth=2,
        # timeout: một số bản dùng ms, bản khác dùng giây (request_timeout).
        timeout=120_000,      # nếu không hỗ trợ sẽ bị lọc
        request_timeout=120,  # giây
        page_timeout=120_000, # nếu có
        wait_for_timeout=60_000  # nếu có
    )

def run_crawl(seeds: list[str]) -> list[dict]:
    # BrowserConfig: hầu hết phiên bản đều chấp nhận headless
    browser_cfg = BrowserConfig(headless=True)

    # Superset tham số; _make_run_config sẽ tự lọc cái nào không được hỗ trợ
    run_cfg = _make_run_config(
        cache_mode=getattr(CacheMode, "BYPASS", getattr(CacheMode, "DISABLED", None)),
        # Một số phiên bản hỗ trợ "wait_for" với các giá trị như "networkidle" (Playwright style)
        wait_for="networkidle",
        # Nhiều phiên bản KHÔNG còn "js_enabled" → vẫn truyền, nhưng _make_run_config sẽ tự bỏ nếu không có
        js_enabled=True,
        # Có phiên bản dùng link_follow/allowed_domains/allowed_regex
        link_follow=True,
        allowed_domains=list(ALLOW_DOMAINS),
        allowed_regex=[r.pattern for r in URL_ALLOWLIST_REGEX],
        max_depth=2,
        # Tham số timeout có phiên bản là milliseconds, có phiên bản là seconds (request_timeout)
        timeout=45_000,           # nếu không hỗ trợ sẽ bị lọc
        request_timeout=45,       # một số bản dùng request_timeout (giây)
    )

    results: list[dict] = []

    import asyncio
    async def _amain():
        browser_cfg = BrowserConfig(headless=True)  # render đầy đủ
        run_cfg = _default_run_config()

        async with _make_crawler(browser_cfg) as crawler:
            for url in seeds:
                # Chỉ thu thập từ miền .gov.vn như yêu cầu
                if not _is_gov_vn(url):
                    continue
                if not can_fetch(url):
                    continue
                _throttle(_domain(url))

                r = None
                try:
                    r = await crawler.arun(url=url, config=run_cfg)
                except Exception:
                    r = None

                # Nếu fail do wait condition (như chinhphu.vn), thử lại cấu hình an toàn:
                if (not r) or (not getattr(r, "success", False)):
                    safe_cfg = _make_run_config(
                        **{k: getattr(run_cfg, k, None) for k in dir(run_cfg) if not k.startswith("_")},
                        # thêm wait_for an toàn (nếu bản hỗ trợ thì giữ, không thì _make_run_config sẽ bỏ)
                        wait_for="domcontentloaded",
                        request_timeout=120
                    )
                    # chuyển sang text_mode để tránh các asset nặng gây treo
                    safe_browser_cfg = BrowserConfig(headless=True, text_mode=True)
                    try:
                        async with _make_crawler(safe_browser_cfg) as safe_crawler:
                            r = await safe_crawler.arun(url=url, config=safe_cfg)
                    except Exception:
                        r = None

                if not r or not getattr(r, "success", False):
                    # bỏ qua trang lỗi, tiếp tục seed khác
                    continue

                results.extend(_process_result(r))

    asyncio.run(_amain())
    return results

# --- thêm vào đầu file (import) ---
from typing import Optional

# --- helper: lấy field với danh sách tên ưu tiên ---
def _get_attr(obj, names: list[str], default=None):
    for n in names:
        # hỗ trợ cả attr lẫn dict-like metadata
        if hasattr(obj, n):
            val = getattr(obj, n)
            if val is not None:
                return val
        if isinstance(obj, dict) and n in obj and obj[n] is not None:
            return obj[n]
        # metadata dạng dict
        if hasattr(obj, "metadata"):
            meta = getattr(obj, "metadata")
            if isinstance(meta, dict) and n in meta and meta[n] is not None:
                return meta[n]
    return default

def _results_iter(r):
    # r có thể là AggregatedResult; các sub-kết quả nằm ở .results hoặc ._results
    if hasattr(r, "results") and r.results:
        return r.results
    if hasattr(r, "_results") and r._results:
        return r._results
    # fallback: coi r chính là một CrawlResult
    return [r]

def _normalize_fields(res, parent_url: Optional[str] = None):
    # Chuẩn hoá các field chính có thể mang nhiều tên khác nhau theo phiên bản
    title = _get_attr(res, ["title", "page_title", "og_title"])
    markdown = _get_attr(res, ["markdown", "md", "content_markdown"])
    extracted_text = _get_attr(res, ["extracted_text", "text", "cleaned_text"])
    cleaned_html = _get_attr(res, ["cleaned_html", "html", "content_html"])
    url = _get_attr(res, ["url", "page_url"], default=parent_url)
    return {
        "title": title,
        "markdown": markdown,
        "extracted_text": extracted_text,
        "cleaned_html": cleaned_html,
        "url": url,
    }

def _process_result(r) -> List[Dict[str,Any]]:
    items = []
    # Lấy URL tổng nếu có
    parent_url = getattr(r, "url", None)

    # Duyệt qua từng sub-result
    for res in _results_iter(r):
        norm = _normalize_fields(res, parent_url=parent_url)
        title = norm["title"] or ""
        md = norm["markdown"] or ""
        txt = norm["extracted_text"] or ""
        html = norm["cleaned_html"] or ""
        url = norm["url"] or parent_url or ""

            # Bảo đảm chỉ nhận kết quả thuộc miền .gov.vn
            if not _is_gov_vn(url):
                continue

        # Nếu không có nội dung, bỏ qua
        if not any([title, md, txt, html]):
            continue

        text_blob = " ".join(filter(None, [title, md, txt]))
        low = text_blob.lower()

        # keyword filter
        if not any(k in low for k in KEYWORDS):
            continue

        # doc-type
        doc_type = detect_doc_type(text_blob)
        if not doc_type:
            continue

        site = _domain(url) if url else _domain(parent_url or "")

        parsed = {
            "url": url or (parent_url or ""),
            "source_site": site,
            "doc_type": doc_type,
            "tieu_de": title,
            "noi_dung_markdown": md,
            "noi_dung_text": txt,
            "attachments": [],
            "linh_vuc": sorted({k for k in KEYWORDS if k in low})
        }

        # site-specific enrich
        if site == "chinhphu.vn":
            parsed.update(parse_chinhphu(r if site=="chinhphu.vn" else res))
        elif site == "vbpl.vn":
            parsed.update(parse_vbpl(res, parent_url=parent_url))
        elif site == "duthaoonline.quochoi.vn":
            parsed.update(parse_duthao_qh(r if site=="duthaoonline.quochoi.vn" else res))
        elif site == "moj.gov.vn":
            parsed.update(parse_moj_dtvb(res, parent_url=parent_url))
        elif site == "luatminhkhue.vn":
            parsed.update(parse_lmk(r if site=="luatminhkhue.vn" else res))
        else:
            parsed.update(common_fields_from_markdown(md))

        # PDF attachments
        pdfs = _extract_pdf_links(html or "", base_url=url or (parent_url or ""))
        for purl in pdfs:
            # Chỉ tải tệp PDF từ miền .gov.vn
            if not _is_gov_vn(purl):
                continue
            loc = fetch_and_extract_pdf(purl, out_dir="../outputs/pdf")
            parsed["attachments"].append({"url": purl, "type": "pdf", **loc})

        # trạng thái
        parsed.setdefault("trang_thai", "du_thao" if parsed["doc_type"]=="DU_THAO" else "con_hieu_luc")
        parsed.setdefault("du_thao", {
            "dang_lay_y_kien": parsed["doc_type"]=="DU_THAO",
            "ngay_bat_dau": None, "ngay_ket_thuc": None,
            "so_luong_y_kien": None, "link_y_kien": None, "noi_dung_y_kien": []
        })

        now = datetime.utcnow().isoformat()+"Z"
        parsed["crawled_at"] = now

        key = (parsed.get("url","") + "|" + parsed.get("so_hieu","") + "|" + (parsed.get("ngay_ban_hanh") or "") + "|" + norm_space(parsed.get("noi_dung_text",""))[:1000])
        parsed["content_hash"] = hashlib.sha256(key.encode("utf-8")).hexdigest()
        parsed["record_valid_from"] = now
        parsed["record_valid_to"] = None
        parsed["is_current"] = True

        items.append(parsed)

    return items

def _extract_pdf_links(html: str, base_url: str) -> List[str]:
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"\.pdf(\?|$)", href, re.I):
            out.append(urljoin(base_url, href))
    return list(dict.fromkeys(out))
