"""
Specialized crawler for Vietnamese legal websites
"""
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from src.crawlers.base_crawler import BaseCrawler
from src.utils.logger import log


class LegalWebsiteCrawler(BaseCrawler):
    """
    Specialized crawler for Vietnamese legal document websites
    """
    
    def __init__(self, website_config: Dict):
        """
        Initialize crawler for a specific website
        
        Args:
            website_config: Configuration dictionary for the website
        """
        super().__init__()
        self.website_config = website_config
        self.base_url = website_config['url']
        self.website_name = website_config['name']
        self.website_type = website_config.get('type', 'unknown')
        
        log.info(f"Initialized crawler for: {self.website_name} ({self.base_url})")
    
    def extract_document_links_thuvienphapluat(self, html: str, base_url: str) -> List[Dict]:
        """
        Extract document links from thuvienphapluat.vn
        
        Args:
            html: HTML content
            base_url: Base URL
            
        Returns:
            List of document links
        """
        links = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all article/document links
        # thuvienphapluat.vn uses specific patterns
        selectors = [
            'a[href*="/van-ban/"]',
            'a[href*="/document/"]',
            '.doc-item a',
            '.document-item a',
            'a.doc-title',
            'h3 a',
            'h4 a'
        ]
        
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href', '')
                if not href:
                    continue
                
                # Build full URL
                full_url = urljoin(base_url, href)
                
                # Get title
                title = link.get_text(strip=True)
                
                # Check if link is relevant
                if self.is_relevant_document(title, ''):
                    links.append({
                        'url': full_url,
                        'title': title,
                        'source': 'thuvienphapluat.vn'
                    })
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        log.info(f"Extracted {len(unique_links)} document links from thuvienphapluat.vn")
        return unique_links
    
    def extract_document_links_chinhphu(self, html: str, base_url: str) -> List[Dict]:
        """
        Extract document links from chinhphu.vn
        
        Args:
            html: HTML content
            base_url: Base URL
            
        Returns:
            List of document links
        """
        links = []
        soup = BeautifulSoup(html, 'lxml')
        
        # chinhphu.vn specific selectors
        selectors = [
            'a[href*="/van-ban"]',
            'a[href*="/news/"]',
            '.article-title a',
            '.news-title a',
            'h2 a',
            'h3 a'
        ]
        
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href', '')
                if not href:
                    continue
                
                full_url = urljoin(base_url, href)
                title = link.get_text(strip=True)
                
                if self.is_relevant_document(title, ''):
                    links.append({
                        'url': full_url,
                        'title': title,
                        'source': 'chinhphu.vn'
                    })
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        log.info(f"Extracted {len(unique_links)} document links from chinhphu.vn")
        return unique_links
    
    def extract_document_links_generic(self, html: str, base_url: str) -> List[Dict]:
        """
        Generic document link extraction for any legal website
        
        Args:
            html: HTML content
            base_url: Base URL
            
        Returns:
            List of document links
        """
        links = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Generic patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            title = link.get_text(strip=True)
            
            # Skip empty titles or navigation links
            if not title or len(title) < 10:
                continue
            
            # Check if it looks like a document link
            if any(pattern in href.lower() for pattern in ['van-ban', 'document', 'law', 'nghi-quyet', 'nghi-dinh', 'du-thao']):
                full_url = urljoin(base_url, href)
                
                if self.is_relevant_document(title, ''):
                    links.append({
                        'url': full_url,
                        'title': title,
                        'source': self.website_name
                    })
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        log.info(f"Extracted {len(unique_links)} document links (generic)")
        return unique_links
    
    def extract_document_links(self, html: str, base_url: str) -> List[Dict]:
        """
        Extract document links based on website type
        
        Args:
            html: HTML content
            base_url: Base URL
            
        Returns:
            List of document links
        """
        # Determine which extraction method to use
        if 'thuvienphapluat' in base_url.lower():
            return self.extract_document_links_thuvienphapluat(html, base_url)
        elif 'chinhphu' in base_url.lower():
            return self.extract_document_links_chinhphu(html, base_url)
        else:
            return self.extract_document_links_generic(html, base_url)
    
    def extract_comments_and_opinions(self, html: str) -> List[Dict]:
        """
        Extract user comments and opinions from page
        
        Args:
            html: HTML content
            
        Returns:
            List of comments/opinions
        """
        comments = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Common comment patterns
        comment_selectors = [
            '.comment',
            '.opinion',
            '.feedback',
            '.user-comment',
            'div[id*="comment"]',
            'div[class*="comment"]'
        ]
        
        for selector in comment_selectors:
            for comment_elem in soup.select(selector):
                comment_text = comment_elem.get_text(strip=True)
                
                if len(comment_text) > 20:  # Minimum length
                    comments.append({
                        'text': comment_text,
                        'extracted_at': comment_elem.get('data-time', ''),
                        'html': str(comment_elem)[:500]
                    })
        
        log.info(f"Extracted {len(comments)} comments/opinions")
        return comments
    
    async def search_and_crawl(self, search_query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for documents and crawl results
        
        Args:
            search_query: Search query string
            max_results: Maximum number of results to crawl
            
        Returns:
            List of crawled documents
        """
        log.info(f"Searching for: {search_query} on {self.website_name}")
        
        # Build search URL (this is site-specific)
        search_url = self.build_search_url(search_query)
        
        if not search_url:
            log.warning(f"Search not implemented for {self.website_name}")
            return []
        
        # Crawl search results page
        search_results = await self.crawl_url(search_url, extract_pdfs=False)
        
        if not search_results:
            return []
        
        # Extract document links from search results
        doc_links = self.extract_document_links(search_results['html'], search_url)
        
        # Limit results
        doc_links = doc_links[:max_results]
        
        # Crawl individual documents
        doc_urls = [link['url'] for link in doc_links]
        crawled_docs = await self.crawl_multiple(doc_urls)
        
        # Add comments/opinions to each document
        for doc in crawled_docs:
            if doc and doc.get('html'):
                doc['comments'] = self.extract_comments_and_opinions(doc['html'])
        
        return crawled_docs
    
    def build_search_url(self, query: str) -> Optional[str]:
        """
        Build search URL for the website
        
        Args:
            query: Search query
            
        Returns:
            Search URL or None
        """
        # Site-specific search URL patterns
        if 'thuvienphapluat' in self.base_url:
            # Example: https://thuvienphapluat.vn/tim-kiem.html?keyword=chuyen+doi+so
            query_encoded = query.replace(' ', '+')
            return f"{self.base_url}/tim-kiem.html?keyword={query_encoded}"
        
        elif 'chinhphu' in self.base_url:
            # Example: https://chinhphu.vn/search?keywords=chuyen+doi+so
            query_encoded = query.replace(' ', '+')
            return f"{self.base_url}/search?keywords={query_encoded}"
        
        elif 'vanban.chinhphu' in self.base_url:
            # Example for vanban.chinhphu.vn
            query_encoded = query.replace(' ', '+')
            return f"{self.base_url}/portal/page/portal/chinhphu/NuocCHXHCNVietNam?mode=searchvanban&keyword={query_encoded}"
        
        else:
            log.warning(f"Search URL builder not implemented for: {self.base_url}")
            return None
