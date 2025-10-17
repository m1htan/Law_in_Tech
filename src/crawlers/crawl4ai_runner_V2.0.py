# src/crawlers/crawl_runner.py
import os
import re
import json
import time
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Iterable, Optional, Tuple
import tempfile
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime, date
from pathlib import Path
import requests
import pdfplumber

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from src.parsers.mst import crawl_mst
from src.parsers.duthao_qh import crawl_duthao_qh
from src.parsers.chinhphu_duthao import crawl_chinhphu_duthao

# ========= Config =========
DATE_MIN = datetime(2022, 1, 1, tzinfo=timezone.utc)  # từ 2022 trở đi
BASE = Path(__file__).resolve().parents[2]
OUT_PDF_DIR = BASE / "outputs" / "raw" / "pdf"
OUT_JSONL = BASE / "outputs" / "raw" / "jsonl"
OUT_LOGS = BASE / "outputs" / "logs"
OUT_PDF_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSONL.mkdir(parents=True, exist_ok=True)
OUT_LOGS.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUT_LOGS / "crawl.log"

# ========= Logger =========
logger = logging.getLogger("crawler")
logger.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
fh = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
fh.setFormatter(fmt)
sh = logging.StreamHandler()
sh.setFormatter(fmt)
logger.addHandler(fh)
logger.addHandler(sh)

# ========= Dedup per run =========
SEEN_HASH: set[str] = set()
SEEN_HTML: set[str] = set()

def _json_default(o):
    # datetime / date -> ISO 8601
    if isinstance(o, (datetime, date)):
        # nếu là tz-aware, sẽ giữ offset; nếu tz-naive vẫn OK
        return o.isoformat()
    # pathlib.Path -> str
    if isinstance(o, Path):
        return str(o)
    # bytes (hiếm khi cần) -> hex rút gọn hoặc bỏ
    if isinstance(o, (bytes, bytearray)):
        return o.hex()
    # fallback: để json tự xử lý
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

def sha1_bytes(b: bytes) -> str:
    h = hashlib.sha1()
    h.update(b)
    return h.hexdigest()

def pdf_to_text(pdf_path: Path) -> tuple[str, str]:
    """
    Trả về (text, extractor_tag).
    Ưu tiên pdfplumber; nếu rỗng -> OCR fallback bằng pytesseract.
    """
    # 1) pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            parts = []
            for page in pdf.pages:
                parts.append(page.extract_text(x_tolerance=1.5) or "")
        text = "\n".join(p for p in parts if p).strip()
        if text:
            return text, "pdfplumber"
    except Exception as e:
        logger.warning(f"PDF extract (pdfplumber) failed for {pdf_path.name}: {e}")

    # 2) OCR fallback
    try:
        pages = convert_from_path(str(pdf_path))
        ocr_parts = []
        for img in pages:
            ocr_parts.append(pytesseract.image_to_string(img))
        text = "\n".join(ocr_parts).strip()
        if text:
            return text, "ocr"
    except Exception as e:
        logger.warning(f"OCR fallback failed for {pdf_path.name}: {e}")

    return "", "none"

def save_pdf(bytes_data: bytes) -> Tuple[str, str]:
    file_sha1 = sha1_bytes(bytes_data)
    p = OUT_PDF_DIR / f"{file_sha1}.pdf"
    if not p.exists():
        p.write_bytes(bytes_data)
        logger.info(f"Saved PDF: {p}")
    else:
        logger.info(f"PDF exists (dedup by sha1): {p}")
    return str(p), file_sha1

def write_jsonl(record: Dict[str, Any], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=_json_default) + "\n")

def is_after_cutoff(dt: Optional[datetime]) -> bool:
    if not isinstance(dt, datetime):
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= DATE_MIN

def iter_with_time_budget(gen, seconds: int, site_name: str):
    """Bọc một generator (crawl_*) với ngân sách thời gian, không cho treo vô hạn."""
    start = time.monotonic()
    for i, item in enumerate(gen, 1):
        if i % 20 == 0:
            elapsed = time.monotonic() - start
            logger.info(f"[{site_name}] Progress: {i} items, {elapsed:.1f}s elapsed")
        yield item
        if time.monotonic() - start > seconds:
            logger.warning(f"[{site_name}] Time budget exceeded ({seconds}s). Stop this site and continue.")
            break

def safe_write_jsonl(record: Dict[str, Any], path: Path):
    """Ghi JSONL an toàn (tự convert datetime)."""
    def _default(o):
        if isinstance(o, datetime):
            # chuẩn ISO UTC
            return o.astimezone(timezone.utc).isoformat()
        return str(o)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=_default) + "\n")

def not_seen(rec: Dict[str, Any]) -> bool:
    key = rec.get("sha1_pdf") or rec.get("html_url")
    if not key:
        # no key means we accept, but warn
        logger.warning("Record without sha1_pdf/html_url key; allow this one.")
        return True
    if key in SEEN_HASH or key in SEEN_HTML:
        return False
    if rec.get("sha1_pdf"):
        SEEN_HASH.add(rec["sha1_pdf"])
    elif rec.get("html_url"):
        SEEN_HTML.add(rec["html_url"])
    return True

def attach_pdf_text(rec: Dict[str, Any], pdf_path: str):
    try:
        txt, how = pdf_to_text(Path(pdf_path))
        if txt:
            # Lưu text ra file theo sha1 để dễ tái sử dụng
            sha1 = rec.get("sha1_pdf")
            txt_path = OUT_PDF_DIR / f"{sha1}.txt" if sha1 else Path(pdf_path).with_suffix(".txt")
            txt_path.write_text(txt, encoding="utf-8")

            rec["pdf_text_path"] = str(txt_path)
            rec["pdf_text_chars"] = len(txt)
            rec["pdf_text_extractor"] = how  # "pdfplumber" hoặc "ocr"
            # Nếu muốn nhúng vào JSONL luôn thì giữ lại dòng dưới:
            rec["pdf_text"] = txt
        else:
            rec["pdf_text_extractor"] = "none"
    except Exception as e:
        logger.warning(f"attach_pdf_text failed: {e}")


def run_all():
    logger.info("=== START RUN ===")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124 Safari/537.36"
        )
        context.set_default_navigation_timeout(45_000)  # 45s
        context.set_default_timeout(45_000)  # 45s

        # 1) MST – văn bản ban hành
        out_mst = OUT_JSONL / "mst.jsonl"
        # 1) MST
        logger.info(":: Crawl MST begin")
        try:
            for rec, pdf_bytes in iter_with_time_budget(
                    crawl_mst(context, date_min=DATE_MIN),
                    seconds=12 * 60,
                    site_name="MST"
            ):
                pub = rec.get("ngay_ban_hanh_dt") or rec.get("ngay_dt")
                if not is_after_cutoff(pub):
                    continue
                if pdf_bytes:
                    pdf_path, sha1 = save_pdf(pdf_bytes)
                    rec["pdf_local"] = pdf_path
                    rec["sha1_pdf"] = rec.get("sha1_pdf") or sha1
                    attach_pdf_text(rec, pdf_path)
                if not_seen(rec):
                    safe_write_jsonl(rec, out_mst)
        except Exception as e:
            logger.exception(f"MST crawl failed: {e}")
        logger.info(":: Crawl MST end")

        # 2) Dự thảo QH
        out_qh = OUT_JSONL / "duthao_qh.jsonl"
        logger.info(":: Crawl Duthao QH begin")
        try:
            for rec, pdf_bytes in iter_with_time_budget(
                    crawl_duthao_qh(context, date_min=DATE_MIN),
                    seconds=20 * 60,
                    site_name="DuThaoQH"
            ):
                pub = rec.get("ngay_cong_bo_dt") or rec.get("ngay_dt")
                if not is_after_cutoff(pub):
                    continue
                if pdf_bytes:
                    pdf_path, sha1 = save_pdf(pdf_bytes)
                    rec["pdf_local"] = pdf_path
                    rec["sha1_pdf"] = rec.get("sha1_pdf") or sha1
                    attach_pdf_text(rec, pdf_path)
                if not_seen(rec):
                    safe_write_jsonl(rec, out_qh)
        except Exception as e:
            logger.exception(f"Duthao QH crawl failed: {e}")
        logger.info(":: Crawl Duthao QH end")

        # 3) Dự thảo Chính phủ
        out_cp = OUT_JSONL / "duthao_chinhphu.jsonl"
        logger.info(":: Crawl Duthao Chinhphu begin")
        try:
            for rec, pdf_bytes in iter_with_time_budget(
                    crawl_chinhphu_duthao(context, date_min=DATE_MIN),
                    seconds=20 * 60,
                    site_name="DuThaoCP"
            ):
                pub = rec.get("ngay_cong_bo_dt") or rec.get("ngay_dt")
                if not is_after_cutoff(pub):
                    continue
                if pdf_bytes:
                    pdf_path, sha1 = save_pdf(pdf_bytes)
                    rec["pdf_local"] = pdf_path
                    rec["sha1_pdf"] = rec.get("sha1_pdf") or sha1
                    attach_pdf_text(rec, pdf_path)
                if not_seen(rec):
                    safe_write_jsonl(rec, out_cp)
        except Exception as e:
            logger.exception(f"Duthao Chinhphu crawl failed: {e}")
        logger.info(":: Crawl Duthao Chinhphu end")

        context.close()
        browser.close()

    logger.info("=== END RUN ===")

if __name__ == "__main__":
    run_all()