"""Web scraping tools for LangGraph"""

import requests
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
import logging

from src.config import config
from src.utils.text_processing import (
    normalize_vietnamese_text,
    clean_html_text,
    validate_url
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
def fetch_webpage(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch webpage content from URL
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with status, content, and error information
    """
    if not validate_url(url):
        return {
            "success": False,
            "error": "Invalid URL format",
            "url": url,
            "status_code": None,
            "content": None
        }
    
    try:
        headers = {
            'User-Agent': config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Add delay to respect rate limiting
        time.sleep(config.crawl_delay)
        
        return {
            "success": True,
            "error": None,
            "url": url,
            "status_code": response.status_code,
            "content": response.text,
            "encoding": response.encoding
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {url}")
        return {
            "success": False,
            "error": "Request timeout",
            "url": url,
            "status_code": None,
            "content": None
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "status_code": getattr(e.response, 'status_code', None),
            "content": None
        }


@tool
def parse_html_content(html_content: str, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Parse HTML content using BeautifulSoup
    
    Args:
        html_content: HTML content as string
        selectors: Optional CSS selectors for specific elements
        
    Returns:
        Parsed content dictionary
    """
    if not html_content:
        return {
            "success": False,
            "error": "Empty HTML content",
            "data": None
        }
    
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        
        result = {
            "success": True,
            "error": None,
            "title": soup.title.string if soup.title else "",
            "text_content": clean_html_text(soup.get_text()),
            "data": {}
        }
        
        # If selectors provided, extract specific elements
        if selectors:
            for key, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    result["data"][key] = [
                        {
                            "text": clean_html_text(elem.get_text()),
                            "html": str(elem),
                            "attrs": elem.attrs
                        }
                        for elem in elements
                    ]
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing HTML: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


@tool
def search_vanban_chinhphu(keywords: List[str], max_pages: int = 5) -> Dict[str, Any]:
    """
    Search for legal documents on vanban.chinhphu.vn
    
    Args:
        keywords: List of keywords to search for
        max_pages: Maximum number of pages to scrape
        
    Returns:
        Dictionary with search results
    """
    base_url = "https://vanban.chinhphu.vn"
    
    try:
        # For the initial implementation, we'll use a direct approach
        # In production, you might need to handle search forms, AJAX, etc.
        
        # Example: Search page or list all documents
        search_url = f"{base_url}/?pageid=27160"  # Example URL for document list
        
        logger.info(f"Searching vanban.chinhphu.vn with keywords: {keywords}")
        
        result = fetch_webpage.invoke({"url": search_url})
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "documents": [],
                "total_found": 0
            }
        
        # Parse the HTML
        soup = BeautifulSoup(result["content"], 'lxml')
        
        # This is a simplified example - actual selectors need to be verified
        # by inspecting the real website
        documents = []
        
        # Find document items (selectors need to be adjusted based on actual HTML structure)
        doc_items = soup.find_all('div', class_=['vb-item', 'document-item', 'list-item'])
        
        if not doc_items:
            # Try alternative selectors
            doc_items = soup.find_all('tr', class_=['row-item', 'vb-row'])
        
        logger.info(f"Found {len(doc_items)} potential document items")
        
        for item in doc_items[:50]:  # Limit to first 50 items
            try:
                doc_data = {
                    "title": "",
                    "doc_number": "",
                    "doc_type": "",
                    "issuer": "",
                    "issue_date": "",
                    "url": "",
                    "raw_html": str(item)
                }
                
                # Extract title
                title_elem = item.find(['a', 'h3', 'h4'])
                if title_elem:
                    doc_data["title"] = clean_html_text(title_elem.get_text())
                    if title_elem.get('href'):
                        doc_data["url"] = requests.compat.urljoin(base_url, title_elem['href'])
                
                # Extract other fields (adjust based on actual HTML)
                text_content = clean_html_text(item.get_text())
                doc_data["text_content"] = text_content
                
                # Only add if we have at least a title
                if doc_data["title"]:
                    documents.append(doc_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing document item: {str(e)}")
                continue
        
        return {
            "success": True,
            "error": None,
            "documents": documents,
            "total_found": len(documents),
            "keywords_used": keywords
        }
        
    except Exception as e:
        logger.error(f"Error searching vanban.chinhphu.vn: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "documents": [],
            "total_found": 0
        }


@tool  
def extract_document_metadata(raw_document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured metadata from raw document data
    
    Args:
        raw_document: Raw document data from web scraping
        
    Returns:
        Structured metadata dictionary
    """
    from src.utils.text_processing import (
        extract_document_number,
        extract_date,
        extract_document_type,
        generate_doc_id
    )
    
    try:
        metadata = {
            "title": raw_document.get("title", ""),
            "doc_number": "",
            "doc_type": "",
            "issuer": raw_document.get("issuer", ""),
            "issue_date": "",
            "effective_date": "",
            "status": "unknown",
            "url": raw_document.get("url", ""),
            "source": "vanban_chinhphu",
            "topics": [],
            "keywords": [],
            "doc_id": ""
        }
        
        # Extract document number from title or content
        full_text = f"{metadata['title']} {raw_document.get('text_content', '')}"
        doc_number = extract_document_number(full_text)
        if doc_number:
            metadata["doc_number"] = doc_number
        
        # Extract document type
        valid_types = config.get_document_types()
        doc_type = extract_document_type(full_text, valid_types)
        if doc_type:
            metadata["doc_type"] = doc_type
        
        # Extract dates
        issue_date = extract_date(full_text)
        if issue_date:
            metadata["issue_date"] = issue_date
        
        # Generate document ID
        if metadata["doc_type"] and metadata["doc_number"] and metadata["issue_date"]:
            metadata["doc_id"] = generate_doc_id(
                source="vanban_chinhphu",
                doc_type=metadata["doc_type"],
                doc_number=metadata["doc_number"],
                issue_date=metadata["issue_date"]
            )
        
        # Match keywords
        all_keywords = config.get_all_keywords()
        matched_keywords = []
        full_text_lower = full_text.lower()
        
        for keyword in all_keywords:
            if keyword.lower() in full_text_lower:
                matched_keywords.append(keyword)
        
        metadata["keywords"] = matched_keywords[:20]  # Limit to top 20
        
        return {
            "success": True,
            "error": None,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "metadata": None
        }


@tool
def filter_relevant_documents(documents: List[Dict[str, Any]], min_keyword_matches: int = 2) -> Dict[str, Any]:
    """
    Filter documents based on keyword relevance
    
    Args:
        documents: List of documents with metadata
        min_keyword_matches: Minimum number of keyword matches required
        
    Returns:
        Filtered documents
    """
    from src.utils.text_processing import contains_keywords
    
    try:
        all_keywords = config.get_all_keywords()
        exclude_keywords = config.get_exclude_keywords()
        
        filtered_docs = []
        
        for doc in documents:
            # Get searchable text
            searchable_text = f"{doc.get('title', '')} {doc.get('text_content', '')}"
            
            # Check if contains exclude keywords
            if contains_keywords(searchable_text, exclude_keywords, threshold=1):
                logger.info(f"Excluding document: {doc.get('title', '')[:50]} (contains exclude keywords)")
                continue
            
            # Check if contains enough relevant keywords
            if contains_keywords(searchable_text, all_keywords, threshold=min_keyword_matches):
                filtered_docs.append(doc)
                logger.info(f"Including document: {doc.get('title', '')[:50]}")
        
        return {
            "success": True,
            "error": None,
            "filtered_documents": filtered_docs,
            "total_filtered": len(filtered_docs),
            "total_original": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error filtering documents: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "filtered_documents": [],
            "total_filtered": 0,
            "total_original": len(documents)
        }
