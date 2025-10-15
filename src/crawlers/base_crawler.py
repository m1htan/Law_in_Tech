"""
Base crawler class using Crawl4AI
"""
import asyncio
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from bs4 import BeautifulSoup

from src.config import Config
from src.utils.logger import log
from src.utils.pdf_processor import PDFProcessor


class BaseCrawler:
    """Base crawler class with Crawl4AI integration"""
    
    def __init__(self):
        self.config = Config
        self.pdf_processor = PDFProcessor()
        self.visited_urls: Set[str] = set()
        self.crawled_data: List[Dict] = []
        
    def matches_keywords(self, text: str) -> bool:
        """
        Check if text contains relevant keywords
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains at least one keyword
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check technology keywords
        for keyword in self.config.TECH_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def matches_document_type(self, text: str) -> bool:
        """
        Check if text mentions relevant document types
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains document type keywords
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        for doc_type in self.config.DOCUMENT_TYPES:
            if doc_type.lower() in text_lower:
                return True
        
        return False
    
    def extract_year_from_text(self, text: str) -> Optional[int]:
        """
        Extract year from text
        
        Args:
            text: Text to extract year from
            
        Returns:
            Year as integer or None
        """
        # Look for year patterns (2020-2024)
        year_pattern = r'20(2[0-4]|1[0-9])'
        matches = re.findall(year_pattern, text)
        
        if matches:
            years = [int('20' + match) for match in matches]
            # Return most recent year
            return max(years)
        
        return None
    
    def is_relevant_document(self, title: str, content: str) -> bool:
        """
        Determine if document is relevant based on keywords and document type
        
        Args:
            title: Document title
            content: Document content
            
        Returns:
            True if document is relevant
        """
        combined_text = f"{title} {content}"
        
        has_keywords = self.matches_keywords(combined_text)
        has_doc_type = self.matches_document_type(combined_text)
        
        return has_keywords and has_doc_type
    
    def extract_pdf_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        Extract PDF links from HTML
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries with PDF info
        """
        pdf_links = []
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's a PDF link
            if href.endswith('.pdf') or 'pdf' in href.lower():
                full_url = urljoin(base_url, href)
                
                # Get link text
                link_text = link.get_text(strip=True)
                
                pdf_links.append({
                    'url': full_url,
                    'title': link_text,
                    'context': str(link.parent)[:200] if link.parent else ''
                })
        
        log.info(f"Found {len(pdf_links)} PDF links")
        return pdf_links
    
    def extract_metadata_from_page(self, html: str, url: str) -> Dict:
        """
        Extract metadata from page
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Metadata dictionary
        """
        soup = BeautifulSoup(html, 'lxml')
        
        metadata = {
            'url': url,
            'crawled_at': datetime.now().isoformat(),
            'title': '',
            'description': '',
            'keywords': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Extract meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag:
            metadata['description'] = desc_tag.get('content', '')
        
        # Extract meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            keywords = keywords_tag.get('content', '')
            metadata['keywords'] = [k.strip() for k in keywords.split(',')]
        
        return metadata
    
    async def crawl_url(self, url: str, extract_pdfs: bool = True, retry: int = 3) -> Optional[Dict]:
        """
        Crawl a single URL with retry logic
        
        Args:
            url: URL to crawl
            extract_pdfs: Whether to extract and download PDFs
            retry: Number of retry attempts
            
        Returns:
            Dictionary with crawled data
        """
        if url in self.visited_urls:
            log.info(f"URL already visited: {url}")
            return None
        
        # Try different strategies if first attempt fails
        strategies = [
            {"wait_until": "networkidle", "timeout": 60000},  # 60s networkidle
            {"wait_until": "domcontentloaded", "timeout": 45000},  # 45s dom loaded
            {"wait_until": "load", "timeout": 30000},  # 30s basic load
        ]
        
        last_error = None
        
        for attempt in range(retry):
            try:
                strategy = strategies[min(attempt, len(strategies) - 1)]
                
                log.info(f"Crawling URL (attempt {attempt + 1}/{retry}): {url}")
                self.visited_urls.add(url)
                
                # Configure crawler with current strategy
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    markdown_generator=DefaultMarkdownGenerator(),
                    wait_until=strategy["wait_until"],
                    page_timeout=strategy["timeout"],
                    verbose=False,
                    # Add stealth mode
                    magic=True,  # Enable anti-detection
                )
            
                # Crawl the page
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(url=url, config=config)
                    
                    if not result.success:
                        last_error = result.error_message
                        log.warning(f"Attempt {attempt + 1} failed for {url}: {result.error_message}")
                        if attempt < retry - 1:
                            await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                            continue
                        else:
                            log.error(f"All attempts failed for {url}: {result.error_message}")
                            return None
                    
                    # Extract data
                    page_data = {
                        'url': url,
                        'success': result.success,
                        'status_code': result.status_code,
                        'html': result.html,
                        'markdown': result.markdown,
                        'cleaned_html': result.cleaned_html,
                        'metadata': self.extract_metadata_from_page(result.html, url),
                        'pdf_links': [],
                        'is_relevant': False,
                        'crawled_at': datetime.now().isoformat()
                    }
                    
                    # Check relevance
                    title = page_data['metadata'].get('title', '')
                    content = result.markdown[:5000]  # Check first 5000 chars
                    page_data['is_relevant'] = self.is_relevant_document(title, content)
                    
                    if not page_data['is_relevant']:
                        log.info(f"Page not relevant (no matching keywords): {url}")
                    
                    # Extract PDF links if requested
                    if extract_pdfs:
                        pdf_links = self.extract_pdf_links(result.html, url)
                        page_data['pdf_links'] = pdf_links
                        
                        # Download relevant PDFs
                        if page_data['is_relevant']:
                            for pdf_link in pdf_links[:5]:  # Limit to first 5 PDFs per page
                                log.info(f"Processing PDF: {pdf_link['title']}")
                                pdf_result = self.pdf_processor.process_pdf(
                                    pdf_link['url'],
                                    filename=pdf_link['title']
                                )
                                pdf_link['processing_result'] = pdf_result
                    
                    log.info(f"Successfully crawled: {url}")
                    return page_data
                    
            except Exception as e:
                last_error = str(e)
                log.warning(f"Attempt {attempt + 1} failed with exception for {url}: {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    log.error(f"All attempts failed for {url}: {e}")
                    return None
        
        # If we get here, all retries failed
        log.error(f"Failed to crawl {url} after {retry} attempts. Last error: {last_error}")
        return None
    
    async def crawl_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Crawl multiple URLs concurrently
        
        Args:
            urls: List of URLs to crawl
            
        Returns:
            List of crawled data
        """
        log.info(f"Starting to crawl {len(urls)} URLs")
        
        # Create tasks for concurrent crawling
        tasks = [self.crawl_url(url) for url in urls]
        
        # Run with concurrency limit
        semaphore = asyncio.Semaphore(self.config.MAX_CONCURRENT_REQUESTS)
        
        async def crawl_with_limit(task):
            async with semaphore:
                result = await task
                # Add delay between requests
                await asyncio.sleep(self.config.REQUEST_DELAY)
                return result
        
        limited_tasks = [crawl_with_limit(task) for task in tasks]
        results = await asyncio.gather(*limited_tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        log.info(f"Successfully crawled {len(valid_results)}/{len(urls)} URLs")
        self.crawled_data.extend(valid_results)
        
        return valid_results
    
    def save_results(self, filename: str = None):
        """
        Save crawled data to JSON file
        
        Args:
            filename: Output filename (default: timestamp-based)
        """
        if not self.crawled_data:
            log.warning("No data to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawl_results_{timestamp}.json"
        
        output_path = self.config.LOG_DIR / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.crawled_data, f, ensure_ascii=False, indent=2)
            
            log.info(f"Results saved to: {output_path}")
            
        except Exception as e:
            log.error(f"Failed to save results: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get crawling statistics
        
        Returns:
            Dictionary with statistics
        """
        total_crawled = len(self.crawled_data)
        relevant_docs = sum(1 for d in self.crawled_data if d.get('is_relevant', False))
        total_pdfs = sum(len(d.get('pdf_links', [])) for d in self.crawled_data)
        
        stats = {
            'total_urls_crawled': total_crawled,
            'relevant_documents': relevant_docs,
            'total_pdf_links_found': total_pdfs,
            'visited_urls_count': len(self.visited_urls)
        }
        
        return stats
