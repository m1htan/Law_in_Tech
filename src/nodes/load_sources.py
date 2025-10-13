import csv
import json
from typing import List, Dict, Any
from src.utils.logger import get_logger
from src.utils.db import DB

logger = get_logger("LoadSourceRegistry")

def load_sources_csv(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            # Chuẩn hóa kiểu
            r["enabled"] = str(r.get("enabled", "true")).strip().lower() in ("true", "1", "yes")
            r["trust_score"] = float(r.get("trust_score", "0.8") or 0.8)
            r["rate_limit_rpm"] = int(r.get("rate_limit_rpm", "30") or 30)
            r["max_concurrency"] = int(r.get("max_concurrency", "1") or 1)
            # category_tags giữ nguyên chuỗi JSON để DB lưu text
            r["category_tags"] = [t.strip() for t in (r.get("category_tags") or "").split(";") if t.strip()]

            rows.append(r)
    logger.info(f"Loaded {len(rows)} sources from CSV: {path}")
    return rows

def run(state: dict) -> dict:
    cfg = state["config"]
    db = DB(
        primary=cfg["database"]["primary"],
        sqlite_path=cfg["database"]["sqlite_path"],
        postgres_uri=cfg["database"]["postgres_uri"],
    )
    sources = load_sources_csv(cfg["data"]["sources_path"])
    # Upsert vào DB (sqlite)
    for s in sources:
        sid = db.upsert_source(s)
        s["source_id"] = sid
    state["sources"] = sources
    return state
