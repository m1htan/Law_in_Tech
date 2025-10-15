"""
File Storage Manager - Lưu trữ data trong folders (NO DATABASE)
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from src.config import Config
from src.utils.logger import log


@dataclass
class DocumentMetadata:
    """Document metadata - lưu trong JSON"""
    id: str  # Unique ID (filename without extension)
    title: str = ""
    document_number: str = ""
    document_type: str = ""
    issuing_agency: str = ""
    signer: str = ""
    issued_date: Optional[str] = None
    effective_date: Optional[str] = None
    summary: str = ""
    source_url: str = ""
    source_website: str = ""
    pdf_filename: Optional[str] = None  # Just filename, not full path
    text_filename: Optional[str] = None
    category: str = ""
    subject: str = ""
    keywords: str = ""
    is_tech_related: bool = False
    tech_categories: str = ""
    relevance_score: float = 0.0
    status: str = "active"
    crawled_at: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class FileStorageManager:
    """
    Quản lý lưu trữ files (NO DATABASE)
    
    Structure:
        data/
        ├── pdfs/
        │   ├── doc_001.pdf
        │   └── ...
        ├── texts/
        │   ├── doc_001.txt
        │   └── ...
        └── metadata.json  # All document metadata
    """
    
    def __init__(self):
        """Initialize file storage"""
        self.pdf_dir = Path(Config.PDF_OUTPUT_DIR)
        self.text_dir = Path(Config.TEXT_OUTPUT_DIR)
        self.metadata_file = Path("data/metadata.json")
        
        # Create directories
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.metadata: Dict[str, DocumentMetadata] = self._load_metadata()
        
        log.info(f"FileStorageManager initialized")
        log.info(f"PDF dir: {self.pdf_dir}")
        log.info(f"Text dir: {self.text_dir}")
        log.info(f"Metadata file: {self.metadata_file}")
        log.info(f"Loaded {len(self.metadata)} existing documents")
    
    def _load_metadata(self) -> Dict[str, DocumentMetadata]:
        """Load metadata from JSON file"""
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DocumentMetadata objects
            metadata = {}
            for doc_id, doc_dict in data.items():
                metadata[doc_id] = DocumentMetadata(**doc_dict)
            
            return metadata
            
        except Exception as e:
            log.error(f"Error loading metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """Save metadata to JSON file"""
        try:
            # Convert to dict
            data = {
                doc_id: doc.to_dict() 
                for doc_id, doc in self.metadata.items()
            }
            
            # Save with pretty print
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            log.info(f"Metadata saved: {len(data)} documents")
            
        except Exception as e:
            log.error(f"Error saving metadata: {e}")
    
    def generate_doc_id(self, title: str, source_url: str) -> str:
        """
        Generate unique document ID from title and URL
        
        Args:
            title: Document title
            source_url: Source URL
            
        Returns:
            Unique ID (safe filename)
        """
        import hashlib
        import re
        
        # Clean title for filename
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'[\s]+', '_', clean_title)
        clean_title = clean_title[:50]  # Max 50 chars
        
        # Hash URL for uniqueness
        url_hash = hashlib.md5(source_url.encode()).hexdigest()[:8]
        
        # Combine
        doc_id = f"{clean_title}_{url_hash}"
        
        # Make unique if exists
        counter = 1
        original_id = doc_id
        while doc_id in self.metadata:
            doc_id = f"{original_id}_{counter}"
            counter += 1
        
        return doc_id
    
    def document_exists(self, source_url: str) -> bool:
        """
        Check if document already exists
        
        Args:
            source_url: Source URL to check
            
        Returns:
            True if exists
        """
        for doc in self.metadata.values():
            if doc.source_url == source_url:
                return True
        return False
    
    def save_document(
        self,
        title: str,
        source_url: str,
        pdf_path: Optional[Path] = None,
        text_path: Optional[Path] = None,
        text_content: str = "",
        **kwargs
    ) -> str:
        """
        Save document (metadata + files)
        
        Args:
            title: Document title
            source_url: Source URL
            pdf_path: Path to PDF file (if available)
            text_path: Path to text file (if available)
            text_content: Text content to save
            **kwargs: Additional metadata fields
            
        Returns:
            Document ID
        """
        # Check if already exists
        if self.document_exists(source_url):
            log.info(f"Document already exists: {source_url}")
            for doc_id, doc in self.metadata.items():
                if doc.source_url == source_url:
                    return doc_id
        
        # Generate ID
        doc_id = self.generate_doc_id(title, source_url)
        
        # Create metadata
        metadata = DocumentMetadata(
            id=doc_id,
            title=title,
            source_url=source_url,
            crawled_at=datetime.now().isoformat(),
            **kwargs
        )
        
        # Handle PDF file
        if pdf_path and pdf_path.exists():
            # Copy to our PDF dir with doc_id name
            new_pdf_name = f"{doc_id}.pdf"
            new_pdf_path = self.pdf_dir / new_pdf_name
            
            # Copy file
            import shutil
            shutil.copy2(pdf_path, new_pdf_path)
            
            metadata.pdf_filename = new_pdf_name
            log.info(f"PDF saved: {new_pdf_name}")
        
        # Handle text file
        if text_path and text_path.exists():
            # Copy to our text dir
            new_text_name = f"{doc_id}.txt"
            new_text_path = self.text_dir / new_text_name
            
            import shutil
            shutil.copy2(text_path, new_text_path)
            
            metadata.text_filename = new_text_name
            log.info(f"Text saved: {new_text_name}")
        
        elif text_content:
            # Save text content directly
            new_text_name = f"{doc_id}.txt"
            new_text_path = self.text_dir / new_text_name
            
            with open(new_text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            metadata.text_filename = new_text_name
            log.info(f"Text saved: {new_text_name}")
        
        # Save metadata
        self.metadata[doc_id] = metadata
        self._save_metadata()
        
        log.info(f"Document saved: {doc_id}")
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """Get document metadata by ID"""
        return self.metadata.get(doc_id)
    
    def get_all_documents(self) -> List[DocumentMetadata]:
        """Get all documents"""
        return list(self.metadata.values())
    
    def get_statistics(self) -> Dict:
        """Get storage statistics"""
        docs = list(self.metadata.values())
        
        total = len(docs)
        tech_docs = sum(1 for d in docs if d.is_tech_related)
        with_pdfs = sum(1 for d in docs if d.pdf_filename)
        with_texts = sum(1 for d in docs if d.text_filename)
        
        # By type
        by_type = {}
        for doc in docs:
            doc_type = doc.document_type or "Unknown"
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
        
        # By year
        by_year = {}
        for doc in docs:
            if doc.issued_date:
                year = doc.issued_date[:4]
                by_year[year] = by_year.get(year, 0) + 1
        
        # By website
        by_website = {}
        for doc in docs:
            website = doc.source_website or "Unknown"
            by_website[website] = by_website.get(website, 0) + 1
        
        return {
            'total_documents': total,
            'tech_documents': tech_docs,
            'tech_ratio': (tech_docs / total * 100) if total > 0 else 0,
            'with_pdfs': with_pdfs,
            'with_texts': with_texts,
            'by_type': by_type,
            'by_year': by_year,
            'by_website': by_website
        }
    
    def export_to_json(self, output_path: Path, tech_only: bool = False):
        """
        Export all metadata to JSON
        
        Args:
            output_path: Output file path
            tech_only: Only export tech-related documents
        """
        docs = self.get_all_documents()
        
        if tech_only:
            docs = [d for d in docs if d.is_tech_related]
        
        data = [doc.to_dict() for doc in docs]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log.info(f"Exported {len(data)} documents to {output_path}")
    
    def export_to_csv(self, output_path: Path, tech_only: bool = False):
        """
        Export metadata to CSV
        
        Args:
            output_path: Output file path
            tech_only: Only export tech-related documents
        """
        import csv
        
        docs = self.get_all_documents()
        
        if tech_only:
            docs = [d for d in docs if d.is_tech_related]
        
        if not docs:
            log.warning("No documents to export")
            return
        
        # Get all fields
        fields = list(docs[0].to_dict().keys())
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for doc in docs:
                writer.writerow(doc.to_dict())
        
        log.info(f"Exported {len(docs)} documents to {output_path}")
