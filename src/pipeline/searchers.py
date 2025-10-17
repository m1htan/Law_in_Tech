# src/pipeline/searchers.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import time

try:
    from ddgs import DDGS
except Exception:
    DDGS = None

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str          # engine name
    published: Optional[str] = None
    extra: Optional[dict] = None

class WebSearcher:
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        raise NotImplementedError

class DDGSearcher(WebSearcher):
    def __init__(self, safesearch: str = "moderate", region: str = "vn-vi"):
        self.safesearch = safesearch
        self.region = region

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        if DDGS is None:
            raise RuntimeError("duckduckgo_search chưa được cài. pip install duckduckgo-search")
        out: List[SearchResult] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, region=self.region, safesearch=self.safesearch, max_results=max_results):
                out.append(SearchResult(
                    title=r.get("title") or "",
                    url=r.get("href") or r.get("url") or "",
                    snippet=r.get("body") or "",
                    source="ddg",
                ))
        return out

class DDGNewsSearcher(WebSearcher):
    def __init__(self, safesearch: str = "moderate", region: str = "vn-vi"):
        self.safesearch = safesearch
        self.region = region
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        if DDGS is None:
            raise RuntimeError("duckduckgo_search chưa được cài.")
        out: List[SearchResult] = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, region=self.region, safesearch=self.safesearch, max_results=max_results):
                out.append(SearchResult(
                    title=r.get("title") or "",
                    url=r.get("url") or "",
                    snippet=r.get("body") or "",
                    source="ddg_news",
                    published=r.get("date"),
                    extra={"source": r.get("source")}
                ))
        return out

class DDGVideoSearcher(WebSearcher):
    def __init__(self, region: str = "vn-vi"):
        self.region = region
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        if DDGS is None:
            raise RuntimeError("duckduckgo_search chưa được cài.")
        out: List[SearchResult] = []
        with DDGS() as ddgs:
            for r in ddgs.videos(query, region=self.region, max_results=max_results):
                out.append(SearchResult(
                    title=r.get("title") or "",
                    url=r.get("content") or r.get("url") or "",
                    snippet=r.get("description") or "",
                    source="ddg_video",
                    extra={"duration": r.get("duration")}
                ))
        return out
