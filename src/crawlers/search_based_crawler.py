"""
Search-based crawler for thuvienphapluat.vn
Alternative approach when category crawling doesn't work
"""
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote_plus
from bs4 import BeautifulSoup
from datetime import datetime

from src.crawlers.production_crawler import ThuvienPhapLuatProductionCrawler
from src.database.models import DatabaseManager
from src.utils.logger import log


class SearchBasedCrawler(ThuvienPhapLuatProductionCrawler):
    """
    Crawler using search functionality instead of categories
    More reliable when category pages have issues
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.search_base = "https://thuvienphapluat.vn/tim-kiem.html"
    
    async def search_documents(
        self,
        keyword: str,
        page: int = 1,
        doc_type: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Search for documents by keyword
        
        Args:
            keyword: Search keyword
            page: Page number
            doc_type: Document type filter
            
        Returns:
            Search result dictionary
        """
        # Build search URL
        params = {
            'keyword': keyword,
            'page': page,
            'area': 2  # Văn bản
        }
        
        if doc_type:
            params['type'] = doc_type
        
        # Construct URL
        param_str = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        url = f"{self.search_base}?{param_str}"
        
        log.info(f"Searching: {url}")
        
        result = await self.crawl_url(url, extract_pdfs=False, retry=2)
        
        if not result or not result.get('html'):
            return None
        
        return result
    
    async def crawl_by_search(
        self,
        keyword: str,
        max_pages: int = 10,
        max_documents: int = 50
    ) -> Dict:
        """
        Crawl documents using search
        
        Args:
            keyword: Search keyword (e.g., "công nghệ thông tin")
            max_pages: Maximum pages
            max_documents: Maximum documents
            
        Returns:
            Statistics
        """
        log.info("="*60)
        log.info(f"SEARCH-BASED CRAWL: {keyword}")
        log.info(f"Max pages: {max_pages}")
        log.info(f"Max documents: {max_documents}")
        log.info("="*60)
        
        stats = {
            'keyword': keyword,
            'pages_crawled': 0,
            'documents_found': 0,
            'documents_crawled': 0,
            'documents_saved': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat()
        }
        
        current_page = 1
        documents_count = 0
        
        while True:
            # Check limits
            if max_pages and stats['pages_crawled'] >= max_pages:
                break
            
            if max_documents and documents_count >= max_documents:
                break
            
            # Search
            log.info(f"\nSearching page {current_page}...")
            search_result = await self.search_documents(keyword, current_page)
            
            if not search_result:
                log.warning(f"Search failed for page {current_page}, stopping")
                break
            
            stats['pages_crawled'] += 1
            
            # Extract documents
            doc_list = self.extract_document_list(
                search_result['html'],
                search_result['url']
            )
            
            if not doc_list:
                log.info("No more documents found")
                break
            
            stats['documents_found'] += len(doc_list)
            log.info(f"Found {len(doc_list)} documents")
            
            # Crawl each document
            for idx, doc_info in enumerate(doc_list, 1):
                if max_documents and documents_count >= max_documents:
                    break
                
                log.info(f"[{idx}/{len(doc_list)}] {doc_info['title'][:60]}...")
                
                try:
                    doc = await self.crawl_document_detail(doc_info['url'])
                    
                    if doc:
                        stats['documents_crawled'] += 1
                        stats['documents_saved'] += 1
                        documents_count += 1
                        log.info(f"✓ Saved: ID {doc.id}")
                    else:
                        stats['errors'] += 1
                    
                    # Progress
                    self.db.update_progress(
                        website="thuvienphapluat.vn",
                        category=f"search_{keyword}",
                        last_page=current_page,
                        total_pages=current_page,
                        documents_crawled=stats['documents_crawled']
                    )
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    log.error(f"Error: {e}")
                    stats['errors'] += 1
            
            current_page += 1
            await asyncio.sleep(3)
        
        stats['completed_at'] = datetime.now().isoformat()
        
        log.info("\n" + "="*60)
        log.info("SEARCH CRAWL COMPLETED")
        log.info("="*60)
        for key, value in stats.items():
            log.info(f"{key}: {value}")
        
        return stats


async def run_search_crawl(
    keyword: str = "công nghệ thông tin",
    max_pages: int = 10,
    max_documents: int = 50
):
    """
    Run search-based crawl
    
    Args:
        keyword: Search keyword
        max_pages: Max pages
        max_documents: Max documents
    """
    db = DatabaseManager()
    crawler = SearchBasedCrawler(db)
    
    stats = await crawler.crawl_by_search(
        keyword=keyword,
        max_pages=max_pages,
        max_documents=max_documents
    )
    
    # Database stats
    db_stats = db.get_statistics()
    log.info("\nDatabase Statistics:")
    for key, value in db_stats.items():
        log.info(f"  {key}: {value}")
    
    db.close()
    
    return stats


if __name__ == "__main__":
    import sys
    
    keyword = sys.argv[1] if len(sys.argv) > 1 else "công nghệ thông tin"
    
    asyncio.run(run_search_crawl(
        keyword=keyword,
        max_pages=5,
        max_documents=20
    ))
