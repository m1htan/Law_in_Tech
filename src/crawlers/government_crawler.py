"""
Government Sites Crawler - Only official .gov.vn sources
Crawl từ các trang chính phủ Việt Nam
"""
import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime

from src.crawlers.base_crawler import BaseCrawler
from src.storage.file_storage import FileStorageManager
from src.config import Config
from src.utils.logger import log


class GovernmentSitesCrawler(BaseCrawler):
    """
    Crawler for official Vietnamese government websites (.gov.vn)
    """
    
    def __init__(self, storage: FileStorageManager):
        """
        Initialize government crawler
        
        Args:
            storage: File storage manager instance
        """
        super().__init__()
        self.storage = storage
        
        # ONLY official government sources
        self.gov_sources = {
            "vanban.chinhphu.vn": {
                "name": "Hệ thống văn bản Chính phủ",
                "priority": "highest",
                "type": "government",
                "search_url": "https://vanban.chinhphu.vn/portal/page/portal/chinhphu/hethongvanban",
                "reliable": True
            },
            "chinhphu.vn": {
                "name": "Cổng thông tin Chính phủ",
                "priority": "highest",
                "type": "government",
                "search_url": "https://chinhphu.vn",
                "reliable": True
            },
            "mst.gov.vn": {
                "name": "Bộ Số hóa",
                "priority": "highest",
                "type": "ministry",
                "search_url": "https://mst.gov.vn",
                "reliable": True
            },
            "congbao.chinhphu.vn": {
                "name": "Công báo Chính phủ",
                "priority": "high",
                "type": "government",
                "search_url": "https://congbao.chinhphu.vn",
                "reliable": True
            },
            "most.gov.vn": {
                "name": "Bộ Khoa học và Công nghệ",
                "priority": "medium",
                "type": "ministry",
                "search_url": "https://most.gov.vn",
                "reliable": False  # Has SSL issues
            }
        }
        
        log.info(f"Government Sites Crawler initialized")
        log.info(f"Official sources: {len(self.gov_sources)}")
    
    async def crawl_vanban_chinhphu(
        self,
        max_pages: int = 10,
        max_documents: int = 50
    ) -> Dict:
        """
        Crawl vanban.chinhphu.vn - Official government document system
        
        Args:
            max_pages: Maximum pages to crawl
            max_documents: Maximum documents
            
        Returns:
            Crawl statistics
        """
        log.info("="*60)
        log.info("CRAWLING: vanban.chinhphu.vn (OFFICIAL)")
        log.info("="*60)
        
        stats = {
            'source': 'vanban.chinhphu.vn',
            'pages_crawled': 0,
            'documents_found': 0,
            'documents_saved': 0,
            'pdfs_downloaded': 0,
            'errors': 0,
            'started_at': datetime.now().isoformat()
        }
        
        # Strategy: Crawl homepage, extract document links
        base_url = "https://vanban.chinhphu.vn"
        
        for page in range(1, max_pages + 1):
            if stats['documents_saved'] >= max_documents:
                break
            
            log.info(f"\nPage {page}/{max_pages}")
            
            # Crawl homepage or paginated page
            url = base_url if page == 1 else f"{base_url}?page={page}"
            
            result = await self.crawl_url(url, extract_pdfs=True, retry=2)
            
            if not result or not result.get('html'):
                log.warning(f"Failed to crawl page {page}")
                stats['errors'] += 1
                continue
            
            stats['pages_crawled'] += 1
            
            # Extract document links and PDFs
            soup = BeautifulSoup(result['html'], 'lxml')
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            doc_links = []
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Filter for document pages
                if any(pattern in href.lower() for pattern in ['vanban', 'van-ban', 'document']):
                    if len(text) > 20:  # Must have meaningful text
                        doc_links.append({
                            'url': urljoin(base_url, href),
                            'title': text
                        })
            
            # Also get PDF links
            pdf_links = result.get('pdf_links', [])
            
            log.info(f"Found {len(doc_links)} document links, {len(pdf_links)} PDFs")
            stats['documents_found'] += len(doc_links)
            
            # Process PDFs first (already downloaded)
            for pdf in pdf_links:
                if stats['documents_saved'] >= max_documents:
                    break
                
                if pdf.get('processing_result', {}).get('success'):
                    pdf_result = pdf['processing_result']
                    
                    from pathlib import Path
                    
                    # Save document with PDF
                    doc_id = self.storage.save_document(
                        title=pdf.get('title', 'Document')[:200],
                        source_url=pdf.get('url', ''),
                        pdf_path=Path(pdf_result.get('pdf_path')) if pdf_result.get('pdf_path') else None,
                        text_path=Path(pdf_result.get('text_path')) if pdf_result.get('text_path') else None,
                        text_content=pdf_result.get('text_content', '')[:10000],
                        source_website='vanban.chinhphu.vn',
                        category='Công nghệ thông tin',
                        is_tech_related=True
                    )
                    
                    stats['documents_saved'] += 1
                    stats['pdfs_downloaded'] += 1
                    
                    log.info(f"✓ Saved PDF document: {doc_id}")
            
            # Process document links
            for idx, doc_link in enumerate(doc_links[:10], 1):  # Max 10 per page
                if stats['documents_saved'] >= max_documents:
                    break
                
                log.info(f"[{idx}] {doc_link['title'][:60]}...")
                
                try:
                    # Crawl detail page
                    doc_result = await self.crawl_url(
                        doc_link['url'],
                        extract_pdfs=True,
                        retry=1
                    )
                    
                    if doc_result:
                        # Parse document info
                        doc_info = self._parse_government_doc(
                            doc_result['html'],
                            doc_link['url'],
                            doc_link['title']
                        )
                        
                        if doc_info:
                            from pathlib import Path
                            
                            # Add PDF info if available
                            pdf_path = None
                            text_path = None
                            text_content = doc_info.get('full_text', '')
                            
                            if doc_result.get('pdf_links'):
                                for pdf in doc_result['pdf_links']:
                                    if pdf.get('processing_result', {}).get('success'):
                                        pdf_res = pdf['processing_result']
                                        pdf_path = Path(pdf_res.get('pdf_path')) if pdf_res.get('pdf_path') else None
                                        text_path = Path(pdf_res.get('text_path')) if pdf_res.get('text_path') else None
                                        text_content = pdf_res.get('text_content', '')[:10000]
                                        stats['pdfs_downloaded'] += 1
                                        break
                            
                            # Save document
                            doc_id = self.storage.save_document(
                                title=doc_info.get('title', '')[:200],
                                source_url=doc_info.get('source_url', ''),
                                pdf_path=pdf_path,
                                text_path=text_path,
                                text_content=text_content,
                                source_website=doc_info.get('source_website', ''),
                                issuing_agency=doc_info.get('issuing_agency', ''),
                                issued_date=doc_info.get('issued_date'),
                                category=doc_info.get('category', ''),
                                is_tech_related=doc_info.get('is_tech_related', True)
                            )
                            
                            stats['documents_saved'] += 1
                            log.info(f"✓ Saved: {doc_id}")
                    
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    log.error(f"Error processing document: {e}")
                    stats['errors'] += 1
            
            await asyncio.sleep(3)
        
        stats['completed_at'] = datetime.now().isoformat()
        
        log.info("\n" + "="*60)
        log.info("VANBAN.CHINHPHU.VN CRAWL COMPLETED")
        log.info("="*60)
        for key, value in stats.items():
            log.info(f"{key}: {value}")
        
        return stats
    
    async def crawl_mst_gov_vn(
        self,
        max_pages: int = 5,
        max_documents: int = 30
    ) -> Dict:
        """
        Crawl mst.gov.vn (Bộ Số hóa - Ministry of Science & Technology)
        
        Args:
            max_pages: Maximum pages
            max_documents: Maximum documents
            
        Returns:
            Statistics
        """
        log.info("="*60)
        log.info("CRAWLING: mst.gov.vn (Bộ Số hóa)")
        log.info("="*60)
        
        stats = {
            'source': 'mst.gov.vn',
            'pages_crawled': 0,
            'documents_saved': 0,
            'started_at': datetime.now().isoformat()
        }
        
        base_url = "https://mst.gov.vn"
        
        # Crawl main page and tech-related sections
        tech_sections = [
            "/",
            "/chuyen-doi-so",
            "/van-ban-phap-luat",
            "/tin-tuc/chuyen-doi-so"
        ]
        
        for section in tech_sections:
            if stats['documents_saved'] >= max_documents:
                break
            
            url = urljoin(base_url, section)
            log.info(f"\nCrawling section: {section}")
            
            result = await self.crawl_url(url, extract_pdfs=True, retry=2)
            
            if not result:
                continue
            
            stats['pages_crawled'] += 1
            
            # Extract documents and PDFs
            soup = BeautifulSoup(result['html'], 'lxml')
            links = soup.find_all('a', href=True)
            
            # Find document/news links
            for link in links:
                if stats['documents_saved'] >= max_documents:
                    break
                
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if len(text) < 30:
                    continue
                
                # Check if tech-related
                if not self.matches_keywords(text):
                    continue
                
                full_url = urljoin(base_url, href)
                
                # Skip if already crawled
                if self.storage.document_exists(full_url):
                    continue
                
                # Save document
                doc_id = self.storage.save_document(
                    title=text[:200],
                    source_url=full_url,
                    source_website='mst.gov.vn',
                    issuing_agency='Bộ Số hóa',
                    category='Công nghệ thông tin',
                    is_tech_related=True
                )
                
                stats['documents_saved'] += 1
                
                log.info(f"✓ Saved: {text[:60]}")
            
            await asyncio.sleep(3)
        
        stats['completed_at'] = datetime.now().isoformat()
        
        log.info("\n" + "="*60)
        log.info("MST.GOV.VN CRAWL COMPLETED")
        log.info("="*60)
        for key, value in stats.items():
            log.info(f"{key}: {value}")
        
        return stats
    
    def _parse_government_doc(
        self,
        html: str,
        url: str,
        title: str
    ) -> Optional[Dict]:
        """
        Parse government document page
        
        Args:
            html: HTML content
            url: Document URL
            title: Document title
            
        Returns:
            Dict with document info or None
        """
        soup = BeautifulSoup(html, 'lxml')
        
        doc_info = {
            'title': title[:200],
            'source_url': url,
            'source_website': urlparse(url).netloc,
            'issuing_agency': "Chính phủ Việt Nam",
            'category': "Công nghệ thông tin",
            'is_tech_related': True,
            'full_text': ''
        }
        
        # Try to extract more details
        try:
            # Find content
            content_elem = soup.select_one('.content, .doc-content, article')
            if content_elem:
                doc_info['full_text'] = content_elem.get_text(strip=True)[:5000]
            
            # Find date
            date_elems = soup.find_all(text=re.compile(r'\d{1,2}/\d{1,2}/\d{4}'))
            if date_elems:
                for date_text in date_elems:
                    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
                    if date_match:
                        day, month, year = date_match.groups()
                        doc_info['issued_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        break
        except Exception as e:
            log.warning(f"Error parsing document details: {e}")
        
        return doc_info
    
    async def crawl_all_government_sites(
        self,
        max_docs_per_site: int = 50
    ) -> Dict:
        """
        Crawl all government sources
        
        Args:
            max_docs_per_site: Max documents per site
            
        Returns:
            Overall statistics
        """
        log.info("\n" + "="*60)
        log.info("CRAWLING ALL GOVERNMENT SITES (.gov.vn)")
        log.info("="*60)
        
        all_stats = []
        
        # 1. vanban.chinhphu.vn (PRIORITY)
        log.info("\n1/2 CRAWLING: vanban.chinhphu.vn")
        stats1 = await self.crawl_vanban_chinhphu(
            max_pages=10,
            max_documents=max_docs_per_site
        )
        all_stats.append(stats1)
        
        await asyncio.sleep(5)
        
        # 2. mst.gov.vn
        log.info("\n2/2 CRAWLING: mst.gov.vn")
        stats2 = await self.crawl_mst_gov_vn(
            max_pages=5,
            max_documents=max_docs_per_site
        )
        all_stats.append(stats2)
        
        # Summary
        total_docs = sum(s.get('documents_saved', 0) for s in all_stats)
        total_pdfs = sum(s.get('pdfs_downloaded', 0) for s in all_stats)
        
        log.info("\n" + "="*60)
        log.info("ALL GOVERNMENT SITES - SUMMARY")
        log.info("="*60)
        log.info(f"Sites crawled: {len(all_stats)}")
        log.info(f"Total documents: {total_docs}")
        log.info(f"Total PDFs: {total_pdfs}")
        
        return {
            'sites_crawled': len(all_stats),
            'total_documents': total_docs,
            'total_pdfs': total_pdfs,
            'details': all_stats
        }


async def run_government_crawl(max_docs: int = 100):
    """
    Run government sites crawler
    
    Args:
        max_docs: Max documents total
    """
    print("\n" + "="*60)
    print("GOVERNMENT SITES CRAWLER")
    print("Only official .gov.vn sources")
    print("="*60)
    
    storage = FileStorageManager()
    crawler = GovernmentSitesCrawler(storage)
    
    stats = await crawler.crawl_all_government_sites(
        max_docs_per_site=max_docs // 2
    )
    
    # Storage stats
    storage_stats = storage.get_statistics()
    print("\n" + "="*60)
    print("STORAGE STATISTICS")
    print("="*60)
    for key, value in storage_stats.items():
        if key not in ['by_type', 'by_year', 'by_website']:
            print(f"{key}: {value}")
    
    return stats


if __name__ == "__main__":
    import sys
    
    max_docs = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    asyncio.run(run_government_crawl(max_docs=max_docs))
