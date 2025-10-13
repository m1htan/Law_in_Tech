import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.utils.logger import get_logger

logger = get_logger("db")

class DB:
    def __init__(self, primary: str, sqlite_path: str, postgres_uri: str):
        self.primary = primary
        self.sqlite_path = sqlite_path
        self.postgres_uri = postgres_uri
        if primary == "sqlite":
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
            self.conn = sqlite3.connect(sqlite_path)
            self.conn.row_factory = sqlite3.Row
            self._init_sqlite()
        else:
            # Placeholder cho PostgreSQL (chưa sử dụng trong bước này)
            self.conn = None

    def _init_sqlite(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            source_id TEXT PRIMARY KEY,
            name TEXT, type TEXT, base_url TEXT,
            robots_policy TEXT, crawl_method TEXT, frequency TEXT,
            trust_score REAL, lang TEXT, notes TEXT, enabled INTEGER,
            auth_type TEXT, auth_secret_name TEXT, rate_limit_rpm INTEGER,
            max_concurrency INTEGER, category_tags TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documents_raw (
            doc_id TEXT PRIMARY KEY,
            source_id TEXT,
            url TEXT UNIQUE,
            title TEXT,
            published_at TEXT,
            discovered_at TEXT,
            status TEXT
        );
        """)
        self.conn.commit()

    def upsert_source(self, row: Dict[str, Any]):
        cur = self.conn.cursor()
        # ---- Coerce types an toàn cho SQLite ----
        row = dict(row)  # tránh đụng hàng tham chiếu ngoài
        # source_id từ base_url
        source_id = hashlib.sha256(row["base_url"].encode("utf-8")).hexdigest()[:16]
        row["_id"] = source_id
        # enabled: bool -> int
        row["enabled"] = 1 if bool(row.get("enabled", True)) else 0
        # category_tags: list -> "a;b;c"
        cat = row.get("category_tags")
        if isinstance(cat, list):
            row["category_tags"] = ";".join([str(x) for x in cat])
        elif cat is None:
            row["category_tags"] = ""

        # trust_score: float
        try:
            row["trust_score"] = float(row.get("trust_score", 0.8))
        except Exception:
            row["trust_score"] = 0.8

        # rate_limit_rpm/max_concurrency: int
        for k in ("rate_limit_rpm", "max_concurrency"):
            try:
                row[k] = int(row.get(k, 1))
            except Exception:
                row[k] = 1
        # -----------------------------------------

        cur.execute("""
        INSERT INTO sources (source_id, name, type, base_url, robots_policy, crawl_method, frequency, trust_score,
                             lang, notes, enabled, auth_type, auth_secret_name, rate_limit_rpm, max_concurrency, category_tags)
        VALUES (:source_id, :name, :type, :base_url, :robots_policy, :crawl_method, :frequency, :trust_score,
                :lang, :notes, :enabled, :auth_type, :auth_secret_name, :rate_limit_rpm, :max_concurrency, :category_tags)
        ON CONFLICT(source_id) DO UPDATE SET
            name=excluded.name, type=excluded.type, base_url=excluded.base_url,
            robots_policy=excluded.robots_policy, crawl_method=excluded.crawl_method, frequency=excluded.frequency,
            trust_score=excluded.trust_score, lang=excluded.lang, notes=excluded.notes, enabled=excluded.enabled,
            auth_type=excluded.auth_type, auth_secret_name=excluded.auth_secret_name, rate_limit_rpm=excluded.rate_limit_rpm,
            max_concurrency=excluded.max_concurrency, category_tags=excluded.category_tags;
        """, {
            "source_id": source_id,
            **row
        })
        self.conn.commit()
        return source_id

    def insert_document_if_new(self, source_id: str, url: str, title: str, published_at: Optional[str]) -> bool:
        cur = self.conn.cursor()
        doc_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        try:
            cur.execute("""
            INSERT INTO documents_raw (doc_id, source_id, url, title, published_at, discovered_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, source_id, url, title, published_at or None,
                datetime.utcnow().isoformat(), "new"
            ))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_recent_docs(self, limit: int = 20) -> List[dict]:
        cur = self.conn.cursor()
        cur.execute("""
        SELECT doc_id, source_id, url, title, published_at, discovered_at, status
        FROM documents_raw
        ORDER BY discovered_at DESC
        LIMIT ?
        """, (limit,))
        return [dict(r) for r in cur.fetchall()]
