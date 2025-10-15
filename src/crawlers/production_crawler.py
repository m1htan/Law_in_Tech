"""
Production Crawler for Vietnamese Legal Documents
Systematic crawling - không dựa vào keyword search
"""
import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime

from src.crawlers.base_crawler import BaseCrawler
from src.database.models import DatabaseManager, LegalDocument
from src.config import Config
from src.utils.logger import log


class ThuvienPhapLuatProductionCrawler(BaseCrawler):
    """
    Production crawler for thuvienphapluat.vn
    Crawl systematically by categories/pagination
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize production crawler
        
        Args:
            db_manager: Database manager instance
        """
        super().__init__()
        self.db = db_manager
        self.base_url = "https://thuvienphapluat.vn"
        
        # Categories for IT/Tech documents
        self.tech_categories = {
            "cong-nghe-thong-tin": {
                "name": "Công nghệ thông tin",
                "url": "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin",
                "priority": "high"
            },
            "thuong-mai-dien-tu": {
                "name": "Thương mại điện tử",
                "url": "https://thuvienphapluat.vn/van-ban/Thuong-mai",
                "priority": "high"
            },
            "so-huu-tri-tue": {
                "name": "Sở hữu trí tuệ",
                "url": "https://thuvienphapluat.vn/van-ban/So-huu-tri-tue",
                "priority": "medium"
            },
            "vien-thong": {
                "name": "Viễn thông",
                "url": "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin",  # Same as CNTT
                "priority": "medium"
            }
        }
        
        log.info(f"Production crawler initialized for {self.base_url}")
        log.info(f"Tech categories: {len(self.tech_categories)}")
    
    async def crawl_category_page(self, category_url: str, page: int = 1) -> Optional[Dict]:
        """
        Crawl a single category page
        
        Args:
            category_url: Base category URL
            page: Page number
            
        Returns:
            Dictionary with page data
        """
        # Build paginated URL
        url = f"{category_url}/trang{page}.html" if page > 1 else f"{category_url}.html"
        
        log.info(f"Crawling category page: {url}")
        
        result = await self.crawl_url(url, extract_pdfs=False, retry=2)
        
        if not result or not result.get('html'):
            return None
        
        return result
    
    def extract_document_list(self, html: str, base_url: str) -> List[Dict]:
        """
        Extract list of documents from category page
        
        Args:
            html: HTML content
            base_url: Base URL for resolving links
            
        Returns:
            List of document info dictionaries
        """
        documents = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Find document items - thuvienphapluat.vn specific selectors
        doc_items = soup.select('.item-vanban, .search-result-item, .doc-item')
        
        if not doc_items:
            # Try alternative selectors
            doc_items = soup.select('div[class*="doc"], div[class*="item"]')
        
        log.info(f"Found {len(doc_items)} potential document items")
        
        for item in doc_items:
            try:
                # Extract document link
                link = item.select_one('a[href*="/van-ban/"], a.doc-title, h3 a, h4 a')
                if not link or not link.get('href'):
                    continue
                
                doc_url = urljoin(base_url, link['href'])
                title = link.get_text(strip=True)
                
                if not title or len(title) < 10:
                    continue
                
                # Extract document number if present
                doc_number = ""
                number_elem = item.select_one('.doc-number, .number, span[class*="number"]')
                if number_elem:
                    doc_number = number_elem.get_text(strip=True)
                
                # Extract document type
                doc_type = ""
                type_elem = item.select_one('.doc-type, .type, span[class*="type"]')
                if type_elem:
                    doc_type = type_elem.get_text(strip=True)
                
                # Extract issuing date
                issued_date = None
                date_elem = item.select_one('.doc-date, .date, span[class*="date"]')
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # Try to parse date
                    issued_date = self._parse_date(date_text)
                
                documents.append({
                    'url': doc_url,
                    'title': title,
                    'document_number': doc_number,
                    'document_type': doc_type,
                    'issued_date': issued_date
                })
                
            except Exception as e:
                log.warning(f"Error extracting document from item: {e}")
                continue
        
        log.info(f"Extracted {len(documents)} documents from page")
        return documents
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """
        Parse Vietnamese date to ISO format
        
        Args:
            date_text: Date string (e.g., "14/10/2024")
            
        Returns:
            ISO formatted date string or None
        """
        try:
            # Try DD/MM/YYYY format
            match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
            if match:
                day, month, year = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Try YYYY-MM-DD format
            match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_text)
            if match:
                return match.group(0)
        except:
            pass
        
        return None
    
    async def crawl_document_detail(self, doc_url: str) -> Optional[LegalDocument]:
        """
        Crawl detailed document page
        
        Args:
            doc_url: Document detail URL
            
        Returns:
            LegalDocument instance or None
        """
        # Check if already in database
        existing = self.db.get_document_by_url(doc_url)
        if existing and existing.ai_analyzed:
            log.info(f"Document already analyzed, skipping: {doc_url}")
            return existing
        
        log.info(f"Crawling document detail: {doc_url}")
        
        result = await self.crawl_url(doc_url, extract_pdfs=True, retry=2)
        
        if not result or not result.get('html'):
            return None
        
        # Parse document details
        doc = self._parse_document_detail(result['html'], doc_url)
        
        if doc:
            # Add PDF/text paths if downloaded
            if result.get('pdf_links'):
                for pdf_link in result['pdf_links']:
                    if pdf_link.get('processing_result', {}).get('success'):
                        pdf_result = pdf_link['processing_result']
                        doc.pdf_path = pdf_result.get('pdf_path', '')
                        doc.text_path = pdf_result.get('text_path', '')
                        doc.full_text = pdf_result.get('text_content', '')[:10000]  # First 10k chars
                        break
            
            # Set source
            doc.source_url = doc_url
            doc.source_website = "thuvienphapluat.vn"
            
            # Save to database
            doc_id = self.db.insert_document(doc)
            doc.id = doc_id
            
            log.info(f"Document saved to database: ID {doc_id}")
        
        return doc
    
    def _parse_document_detail(self, html: str, url: str) -> Optional[LegalDocument]:
        """
        Parse document detail page
        
        Args:
            html: HTML content
            url: Document URL
            
        Returns:
            LegalDocument instance or None
        """
        soup = BeautifulSoup(html, 'lxml')
        doc = LegalDocument()
        
        try:
            # Extract title
            title_elem = soup.select_one('h1, .doc-title, .title')
            if title_elem:
                doc.title = title_elem.get_text(strip=True)
            
            # Extract document number
            number_elem = soup.select_one('.doc-number, .number')
            if number_elem:
                doc.document_number = number_elem.get_text(strip=True)
            
            # Extract document type
            type_elem = soup.select_one('.doc-type, .type')
            if type_elem:
                doc.document_type = type_elem.get_text(strip=True)
            
            # Extract issuing agency
            agency_elem = soup.select_one('.issuing-agency, .agency')
            if agency_elem:
                doc.issuing_agency = agency_elem.get_text(strip=True)
            
            # Extract dates
            date_elems = soup.select('.doc-date, .date')
            for elem in date_elems:
                text = elem.get_text()
                if 'ban hành' in text.lower() or 'ngày' in text.lower():
                    date = self._parse_date(text)
                    if date:
                        doc.issued_date = date
                elif 'hiệu lực' in text.lower():
                    date = self._parse_date(text)
                    if date:
                        doc.effective_date = date
            
            # Extract summary
            summary_elem = soup.select_one('.doc-summary, .summary, .abstract')
            if summary_elem:
                doc.summary = summary_elem.get_text(strip=True)[:500]
            
            # Extract full text content
            content_elem = soup.select_one('.doc-content, .content, .doc-body')
            if content_elem:
                doc.full_text = content_elem.get_text(strip=True)[:5000]  # First 5k chars
            
            return doc
            
        except Exception as e:
            log.error(f"Error parsing document detail: {e}")
            return None
    
    async def crawl_category_systematic(
        self,
        category_key: str,
        start_page: int = 1,
        max_pages: Optional[int] = None,
        max_documents: Optional[int] = None
    ) -> Dict:
        """
        Systematically crawl a category
        
        Args:
            category_key: Category key from tech_categories
            start_page: Starting page number
            max_pages: Maximum pages to crawl (None = all)
            max_documents: Maximum documents to crawl (None = all)
            
        Returns:
            Crawl statistics
        """
        if category_key not in self.tech_categories:
            raise ValueError(f"Unknown category: {category_key}")
        
        category = self.tech_categories[category_key]
        category_url = category['url']
        category_name = category['name']
        
        log.info("="*60)
        log.info(f"SYSTEMATIC CRAWL: {category_name}")
        log.info(f"URL: {category_url}")
        log.info(f"Start page: {start_page}")
        log.info(f"Max pages: {max_pages or 'unlimited'}")
        log.info(f"Max documents: {max_documents or 'unlimited'}")
        log.info("="*60)
        
        stats = {
            'category': category_name,
            'pages_crawled': 0,
            'documents_found': 0,
            'documents_crawled': 0,
            'documents_saved': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat()
        }
        
        current_page = start_page
        documents_count = 0
        
        while True:
            # Check limits
            if max_pages and stats['pages_crawled'] >= max_pages:
                log.info(f"Reached max pages limit: {max_pages}")
                break
            
            if max_documents and documents_count >= max_documents:
                log.info(f"Reached max documents limit: {max_documents}")
                break
            
            # Crawl category page
            log.info(f"\nCrawling page {current_page}...")
            page_result = await self.crawl_category_page(category_url, current_page)
            
            if not page_result:
                log.warning(f"Failed to crawl page {current_page}, stopping")
                break
            
            stats['pages_crawled'] += 1
            
            # Extract document list
            doc_list = self.extract_document_list(page_result['html'], category_url)
            
            if not doc_list:
                log.info("No more documents found, stopping")
                break
            
            stats['documents_found'] += len(doc_list)
            log.info(f"Found {len(doc_list)} documents on page {current_page}")
            
            # Crawl each document
            for idx, doc_info in enumerate(doc_list, 1):
                if max_documents and documents_count >= max_documents:
                    break
                
                log.info(f"\n[{idx}/{len(doc_list)}] {doc_info['title'][:60]}...")
                
                try:
                    doc = await self.crawl_document_detail(doc_info['url'])
                    
                    if doc:
                        stats['documents_crawled'] += 1
                        stats['documents_saved'] += 1
                        documents_count += 1
                        
                        log.info(f"✓ Document saved: ID {doc.id}")
                    else:
                        stats['errors'] += 1
                        log.warning(f"✗ Failed to crawl document")
                    
                    # Update progress
                    self.db.update_progress(
                        website="thuvienphapluat.vn",
                        category=category_name,
                        last_page=current_page,
                        total_pages=current_page,
                        documents_crawled=stats['documents_crawled']
                    )
                    
                    # Delay between documents
                    await asyncio.sleep(Config.REQUEST_DELAY)
                    
                except Exception as e:
                    log.error(f"Error crawling document: {e}")
                    stats['errors'] += 1
            
            # Move to next page
            current_page += 1
            
            # Delay between pages
            await asyncio.sleep(Config.REQUEST_DELAY * 2)
        
        stats['completed_at'] = datetime.now().isoformat()
        
        log.info("\n" + "="*60)
        log.info("CRAWL COMPLETED")
        log.info("="*60)
        for key, value in stats.items():
            log.info(f"{key}: {value}")
        
        return stats


# Convenience function
async def run_production_crawl(
    category: str = "cong-nghe-thong-tin",
    max_pages: int = 10,
    max_documents: int = 50
):
    """
    Run production crawl
    
    Args:
        category: Category to crawl
        max_pages: Maximum pages
        max_documents: Maximum documents
    """
    db = DatabaseManager()
    crawler = ThuvienPhapLuatProductionCrawler(db)
    
    stats = await crawler.crawl_category_systematic(
        category_key=category,
        max_pages=max_pages,
        max_documents=max_documents
    )
    
    # Show database stats
    db_stats = db.get_statistics()
    log.info("\n" + "="*60)
    log.info("DATABASE STATISTICS")
    log.info("="*60)
    for key, value in db_stats.items():
        log.info(f"{key}: {value}")
    
    db.close()
    
    return stats
