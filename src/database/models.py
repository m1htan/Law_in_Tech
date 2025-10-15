"""
Database models for Vietnamese Legal Document Crawler
Production mode - systematic crawling
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import json

from src.config import Config
from src.utils.logger import log


@dataclass
class LegalDocument:
    """Legal document model"""
    id: Optional[int] = None
    
    # Document info
    title: str = ""
    document_number: str = ""  # Số hiệu văn bản (VD: 123/2024/NĐ-CP)
    document_type: str = ""    # Loại văn bản (Nghị định, Thông tư, ...)
    
    # Issuing info
    issuing_agency: str = ""   # Cơ quan ban hành
    signer: str = ""           # Người ký
    issued_date: Optional[str] = None
    effective_date: Optional[str] = None
    
    # Content
    summary: str = ""
    full_text: str = ""
    
    # Source
    source_url: str = ""
    source_website: str = ""
    
    # Files
    pdf_path: Optional[str] = None
    text_path: Optional[str] = None
    
    # Classification
    category: str = ""         # Lĩnh vực (CNTT, Tài chính, ...)
    subject: str = ""          # Chủ đề
    keywords: str = ""         # Keywords (JSON array)
    
    # Tech classification
    is_tech_related: bool = False
    tech_categories: str = ""  # JSON array: ["AI", "cybersecurity", ...]
    relevance_score: float = 0.0
    
    # Status
    status: str = "active"     # active, superseded, abolished
    superseded_by: Optional[str] = None
    
    # Metadata
    crawled_at: str = ""
    updated_at: str = ""
    ai_analyzed: bool = False
    ai_analysis: str = ""      # JSON with AI analysis


class DatabaseManager:
    """Manage SQLite database for legal documents"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = Config.BASE_DIR / "data" / "legal_documents.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self.init_database()
        
        log.info(f"Database initialized: {self.db_path}")
    
    def init_database(self):
        """Initialize database and create tables"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Document info
                title TEXT NOT NULL,
                document_number TEXT,
                document_type TEXT,
                
                -- Issuing info
                issuing_agency TEXT,
                signer TEXT,
                issued_date TEXT,
                effective_date TEXT,
                
                -- Content
                summary TEXT,
                full_text TEXT,
                
                -- Source
                source_url TEXT UNIQUE,
                source_website TEXT,
                
                -- Files
                pdf_path TEXT,
                text_path TEXT,
                
                -- Classification
                category TEXT,
                subject TEXT,
                keywords TEXT,
                
                -- Tech classification
                is_tech_related BOOLEAN DEFAULT 0,
                tech_categories TEXT,
                relevance_score REAL DEFAULT 0.0,
                
                -- Status
                status TEXT DEFAULT 'active',
                superseded_by TEXT,
                
                -- Metadata
                crawled_at TEXT,
                updated_at TEXT,
                ai_analyzed BOOLEAN DEFAULT 0,
                ai_analysis TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_number ON documents(document_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON documents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_tech_related ON documents(is_tech_related)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_issued_date ON documents(issued_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_url ON documents(source_url)")
        
        # Create crawl_progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                category TEXT,
                last_page INTEGER DEFAULT 0,
                total_pages INTEGER,
                documents_crawled INTEGER DEFAULT 0,
                started_at TEXT,
                updated_at TEXT,
                completed BOOLEAN DEFAULT 0
            )
        """)
        
        # Create crawl_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crawl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                status TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        
        self.conn.commit()
        log.info("Database tables created")
    
    def insert_document(self, doc: LegalDocument) -> int:
        """
        Insert or update a document
        
        Args:
            doc: LegalDocument instance
            
        Returns:
            Document ID
        """
        cursor = self.conn.cursor()
        
        # Check if document exists
        cursor.execute(
            "SELECT id FROM documents WHERE source_url = ?",
            (doc.source_url,)
        )
        existing = cursor.fetchone()
        
        doc.updated_at = datetime.now().isoformat()
        
        if existing:
            # Update existing
            doc.id = existing['id']
            cursor.execute("""
                UPDATE documents SET
                    title = ?, document_number = ?, document_type = ?,
                    issuing_agency = ?, signer = ?, issued_date = ?, effective_date = ?,
                    summary = ?, full_text = ?,
                    source_website = ?, pdf_path = ?, text_path = ?,
                    category = ?, subject = ?, keywords = ?,
                    is_tech_related = ?, tech_categories = ?, relevance_score = ?,
                    status = ?, superseded_by = ?,
                    updated_at = ?, ai_analyzed = ?, ai_analysis = ?
                WHERE id = ?
            """, (
                doc.title, doc.document_number, doc.document_type,
                doc.issuing_agency, doc.signer, doc.issued_date, doc.effective_date,
                doc.summary, doc.full_text,
                doc.source_website, doc.pdf_path, doc.text_path,
                doc.category, doc.subject, doc.keywords,
                doc.is_tech_related, doc.tech_categories, doc.relevance_score,
                doc.status, doc.superseded_by,
                doc.updated_at, doc.ai_analyzed, doc.ai_analysis,
                doc.id
            ))
        else:
            # Insert new
            doc.crawled_at = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO documents (
                    title, document_number, document_type,
                    issuing_agency, signer, issued_date, effective_date,
                    summary, full_text,
                    source_url, source_website, pdf_path, text_path,
                    category, subject, keywords,
                    is_tech_related, tech_categories, relevance_score,
                    status, superseded_by,
                    crawled_at, updated_at, ai_analyzed, ai_analysis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.title, doc.document_number, doc.document_type,
                doc.issuing_agency, doc.signer, doc.issued_date, doc.effective_date,
                doc.summary, doc.full_text,
                doc.source_url, doc.source_website, doc.pdf_path, doc.text_path,
                doc.category, doc.subject, doc.keywords,
                doc.is_tech_related, doc.tech_categories, doc.relevance_score,
                doc.status, doc.superseded_by,
                doc.crawled_at, doc.updated_at, doc.ai_analyzed, doc.ai_analysis
            ))
            doc.id = cursor.lastrowid
        
        self.conn.commit()
        return doc.id
    
    def get_document_by_url(self, url: str) -> Optional[LegalDocument]:
        """Get document by source URL"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE source_url = ?", (url,))
        row = cursor.fetchone()
        
        if row:
            return LegalDocument(**dict(row))
        return None
    
    def get_tech_documents(self, limit: Optional[int] = None) -> List[LegalDocument]:
        """Get all tech-related documents"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM documents WHERE is_tech_related = 1 ORDER BY issued_date DESC"
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        return [LegalDocument(**dict(row)) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total documents
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = cursor.fetchone()['count']
        
        # Tech documents
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE is_tech_related = 1")
        stats['tech_documents'] = cursor.fetchone()['count']
        
        # By document type
        cursor.execute("SELECT document_type, COUNT(*) as count FROM documents GROUP BY document_type")
        stats['by_type'] = {row['document_type']: row['count'] for row in cursor.fetchall()}
        
        # By year
        cursor.execute("""
            SELECT substr(issued_date, 1, 4) as year, COUNT(*) as count 
            FROM documents 
            WHERE issued_date IS NOT NULL 
            GROUP BY year 
            ORDER BY year DESC
        """)
        stats['by_year'] = {row['year']: row['count'] for row in cursor.fetchall()}
        
        return stats
    
    def update_progress(self, website: str, category: str, last_page: int, 
                       total_pages: int, documents_crawled: int):
        """Update crawl progress"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO crawl_progress 
            (website, category, last_page, total_pages, documents_crawled, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (website, category, last_page, total_pages, documents_crawled, 
              datetime.now().isoformat()))
        
        self.conn.commit()
    
    def get_progress(self, website: str, category: str) -> Optional[Dict]:
        """Get crawl progress"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM crawl_progress 
            WHERE website = ? AND category = ?
        """, (website, category))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            log.info("Database connection closed")
