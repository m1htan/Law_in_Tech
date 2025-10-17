# src/pipeline/discussion_miner.py
from __future__ import annotations
import json, os, re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from .keyword_extractor import top_keywords_from_text, keywords_from_filename
from .patterns import find_legal_ids
from .searchers import DDGSearcher, DDGNewsSearcher, DDGVideoSearcher, SearchResult
from ..utils.vi_text import normalize_text

@dataclass
class DocDiscussion:
    doc_path: str
    doc_id: str
    legal_ids: List[Dict[str, Any]]
    queries: List[str]
    results: List[Dict[str, Any]]

def load_text(p: str) -> str:
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def build_queries(text: str, file_path: str, max_q: int = 6) -> List[str]:
    # 1) ưu tiên định danh pháp lý
    ids = find_legal_ids(text)
    queries = []
    for it in ids:
        # ví dụ: "Nghị định 260/2025/NĐ-CP thảo luận", "Nghị định ... hướng dẫn thi hành"
        base = f"{it['type']} {it['code']}"
        queries.extend([
            f'"{base}"', f'"{base}" thảo luận', f'"{base}" báo chí', f'"{base}" hướng dẫn',
            f'"{base}" tác động doanh nghiệp', f'"{base}" phân tích'
        ])

    # 2) keyword nội dung
    kw_items = top_keywords_from_text(text, topk=15) + keywords_from_filename(file_path)
    for kw in kw_items[:10]:
        q = kw.phrase.strip()
        if len(q) >= 3:
            queries.append(f'{q} chính sách pháp luật')

    # 3) làm gọn, loại trùng
    dedup = []
    seen = set()
    for q in queries:
        qn = re.sub(r"\s+", " ", q.strip().lower())
        if qn and qn not in seen:
            seen.add(qn)
            dedup.append(q)
        if len(dedup) >= max_q:
            break
    return dedup

def mine_discussion_for_file(file_path: str, max_results_per_query: int = 8) -> DocDiscussion:
    text = normalize_text(load_text(file_path))
    file_name = os.path.basename(file_path)
    doc_id = os.path.splitext(file_name)[0]

    queries = build_queries(text, file_path, max_q=8)

    web = DDGSearcher()
    news = DDGNewsSearcher()
    video = DDGVideoSearcher()

    all_results: List[Dict[str, Any]] = []
    for q in queries:
        # news trước → web → video
        for engine in (news, web, video):
            try:
                hits: List[SearchResult] = engine.search(q, max_results=max_results_per_query)
                for h in hits:
                    all_results.append({
                        "query": q,
                        "title": h.title,
                        "url": h.url,
                        "snippet": h.snippet,
                        "engine": h.source,
                        "published": h.published,
                        "extra": h.extra,
                    })
            except Exception as e:
                all_results.append({
                    "query": q, "engine": type(engine).__name__, "error": str(e)
                })

    return DocDiscussion(
        doc_path=file_path,
        doc_id=doc_id,
        legal_ids=find_legal_ids(text),
        queries=queries,
        results=all_results
    )
