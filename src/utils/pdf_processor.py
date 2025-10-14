"""
PDF processing utilities for Vietnamese Legal Crawler
Handles PDF download, conversion to text, and metadata extraction
"""
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests
from datetime import datetime

# PDF processing libraries
import PyPDF2
import pdfplumber
import pymupdf as fitz

from src.config import Config
from src.utils.logger import log


class PDFProcessor:
    """Process PDF files: download, convert to text, extract metadata"""
    
    def __init__(self):
        self.pdf_dir = Config.PDF_OUTPUT_DIR
        self.text_dir = Config.TEXT_OUTPUT_DIR
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.USER_AGENT
        })
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200] + ext
        
        return filename
    
    def download_pdf(self, url: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        Download PDF from URL
        
        Args:
            url: PDF URL
            filename: Optional custom filename
            
        Returns:
            Path to downloaded PDF or None if failed
        """
        try:
            log.info(f"Downloading PDF from: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                log.warning(f"URL does not appear to be a PDF: {content_type}")
            
            # Generate filename if not provided
            if not filename:
                # Try to get from URL or Content-Disposition header
                content_disposition = response.headers.get('content-disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    filename = url.split('/')[-1]
                    if not filename.endswith('.pdf'):
                        filename = f"{filename}.pdf"
            
            filename = self.sanitize_filename(filename)
            
            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            
            filepath = self.pdf_dir / filename
            
            # Save PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            log.info(f"PDF downloaded successfully: {filepath}")
            return filepath
            
        except Exception as e:
            log.error(f"Failed to download PDF from {url}: {e}")
            return None
    
    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2"""
        try:
            text = []
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            log.warning(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (better for tables)"""
        try:
            text = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return '\n'.join(text)
        except Exception as e:
            log.warning(f"pdfplumber extraction failed: {e}")
            return ""
    
    def extract_text_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF (fastest and most accurate)"""
        try:
            text = []
            doc = fitz.open(pdf_path)
            for page in doc:
                text.append(page.get_text())
            doc.close()
            return '\n'.join(text)
        except Exception as e:
            log.warning(f"PyMuPDF extraction failed: {e}")
            return ""
    
    def pdf_to_text(self, pdf_path: Path) -> Tuple[Optional[str], Optional[Path]]:
        """
        Convert PDF to text using multiple methods (fallback approach)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, text_file_path)
        """
        try:
            log.info(f"Converting PDF to text: {pdf_path}")
            
            # Try multiple extraction methods in order of preference
            text = self.extract_text_pymupdf(pdf_path)
            
            if not text or len(text.strip()) < 100:
                log.info("PyMuPDF extraction insufficient, trying pdfplumber...")
                text = self.extract_text_pdfplumber(pdf_path)
            
            if not text or len(text.strip()) < 100:
                log.info("pdfplumber extraction insufficient, trying PyPDF2...")
                text = self.extract_text_pypdf2(pdf_path)
            
            if not text or len(text.strip()) < 50:
                log.error(f"Failed to extract meaningful text from PDF: {pdf_path}")
                return None, None
            
            # Save text file
            text_filename = pdf_path.stem + '.txt'
            text_path = self.text_dir / text_filename
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            log.info(f"Text extracted successfully: {text_path} ({len(text)} characters)")
            return text, text_path
            
        except Exception as e:
            log.error(f"Failed to convert PDF to text: {e}")
            return None, None
    
    def extract_metadata(self, pdf_path: Path) -> Dict:
        """
        Extract metadata from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'filename': pdf_path.name,
            'size_bytes': pdf_path.stat().st_size,
            'created_at': datetime.fromtimestamp(pdf_path.stat().st_ctime).isoformat(),
        }
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata['num_pages'] = len(reader.pages)
                
                if reader.metadata:
                    metadata['title'] = reader.metadata.get('/Title', '')
                    metadata['author'] = reader.metadata.get('/Author', '')
                    metadata['subject'] = reader.metadata.get('/Subject', '')
                    metadata['creator'] = reader.metadata.get('/Creator', '')
        except Exception as e:
            log.warning(f"Failed to extract PDF metadata: {e}")
        
        return metadata
    
    def process_pdf(self, pdf_url: str, filename: Optional[str] = None) -> Dict:
        """
        Complete PDF processing pipeline: download, extract text, extract metadata
        
        Args:
            pdf_url: URL to PDF file
            filename: Optional custom filename
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'success': False,
            'pdf_url': pdf_url,
            'pdf_path': None,
            'text_path': None,
            'text_content': None,
            'metadata': {},
            'error': None
        }
        
        try:
            # Download PDF
            pdf_path = self.download_pdf(pdf_url, filename)
            if not pdf_path:
                result['error'] = "Failed to download PDF"
                return result
            
            result['pdf_path'] = str(pdf_path)
            
            # Extract text
            text_content, text_path = self.pdf_to_text(pdf_path)
            if not text_content:
                result['error'] = "Failed to extract text from PDF"
                return result
            
            result['text_path'] = str(text_path)
            result['text_content'] = text_content
            
            # Extract metadata
            metadata = self.extract_metadata(pdf_path)
            result['metadata'] = metadata
            
            result['success'] = True
            log.info(f"PDF processed successfully: {pdf_path.name}")
            
        except Exception as e:
            result['error'] = str(e)
            log.error(f"PDF processing failed: {e}")
        
        return result
