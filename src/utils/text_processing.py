"""Text processing utilities for Vietnamese language"""

import re
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
import unicodedata


def normalize_vietnamese_text(text: str) -> str:
    """
    Normalize Vietnamese text: standardize unicode, remove extra spaces
    
    Args:
        text: Input Vietnamese text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Normalize unicode (NFC - Canonical Decomposition, followed by Canonical Composition)
    text = unicodedata.normalize('NFC', text)
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_document_number(text: str) -> Optional[str]:
    """
    Extract document number from text
    
    Args:
        text: Text containing document number
        
    Returns:
        Extracted document number or None
    """
    if not text:
        return None
    
    # Pattern: số 123/2024/NĐ-CP or 24/2023/QH15 (support Vietnamese characters and numbers)
    pattern1 = r'(?:số\s+)?(\d+[/-]\d{4}[/-][A-ZĐ0-9\-]+)'
    match = re.search(pattern1, text, re.IGNORECASE | re.UNICODE)
    if match:
        return match.group(1)
    
    # Pattern: 123/2024/NĐ-CP
    pattern2 = r'(\d+[/-]\d{4}[/-][A-ZĐ0-9\-]+)'
    match = re.search(pattern2, text, re.UNICODE)
    if match:
        return match.group(1)
    
    # Fallback: more permissive pattern
    pattern3 = r'(\d+[/-]\d{4}[/-][^\s,;.]+)'
    match = re.search(pattern3, text)
    if match:
        return match.group(1)
    
    return None


def extract_date(text: str) -> Optional[str]:
    """
    Extract date from Vietnamese text
    
    Args:
        text: Text containing date
        
    Returns:
        Date in ISO format (YYYY-MM-DD) or None
    """
    if not text:
        return None
    
    # Pattern: dd/mm/yyyy
    pattern1 = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
    match = re.search(pattern1, text)
    if match:
        day, month, year = match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Pattern: ngày dd tháng mm năm yyyy
    pattern2 = r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        day, month, year = match.groups()
        try:
            date_obj = datetime(int(year), int(month), int(day))
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return None


def generate_doc_id(source: str, doc_type: str, doc_number: str, issue_date: str) -> str:
    """
    Generate unique document ID
    
    Args:
        source: Source name (e.g., 'vanban_chinhphu')
        doc_type: Document type (e.g., 'Nghị định')
        doc_number: Document number (e.g., '13/2023/NĐ-CP')
        issue_date: Issue date (YYYY-MM-DD)
        
    Returns:
        Unique document ID
    """
    # Clean inputs
    source = re.sub(r'[^a-z0-9_]', '_', source.lower())
    doc_type = re.sub(r'[^a-z0-9_]', '_', doc_type.lower())
    doc_number_clean = re.sub(r'[^a-z0-9]', '_', doc_number.lower())
    issue_date_clean = issue_date.replace('-', '')
    
    # Create base ID
    base_id = f"{source}_{doc_type}_{doc_number_clean}_{issue_date_clean}"
    
    # Generate hash to ensure uniqueness and reasonable length
    hash_suffix = hashlib.md5(base_id.encode()).hexdigest()[:8]
    
    return f"{source}_{hash_suffix}"


def contains_keywords(text: str, keywords: List[str], threshold: int = 1) -> bool:
    """
    Check if text contains at least threshold keywords
    
    Args:
        text: Text to check
        keywords: List of keywords to search for
        threshold: Minimum number of keywords that must be found
        
    Returns:
        True if text contains enough keywords
    """
    if not text or not keywords:
        return False
    
    text_lower = text.lower()
    count = 0
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            count += 1
            if count >= threshold:
                return True
    
    return False


def extract_document_type(text: str, valid_types: List[str]) -> Optional[str]:
    """
    Extract document type from text
    
    Args:
        text: Text containing document type
        valid_types: List of valid document types
        
    Returns:
        Extracted document type or None
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    for doc_type in valid_types:
        if doc_type.lower() in text_lower:
            return doc_type
    
    return None


def clean_html_text(text: str) -> str:
    """
    Clean HTML text: remove tags, decode entities, normalize
    
    Args:
        text: HTML text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # Normalize
    text = normalize_vietnamese_text(text)
    
    return text


def validate_url(url: str) -> bool:
    """
    Validate if string is a valid URL
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL
    """
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None
