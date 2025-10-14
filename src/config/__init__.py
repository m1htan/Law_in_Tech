"""Configuration management for Law in Tech project"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration manager"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.root_dir / "config"
        self.data_dir = self.root_dir / "data"
        
        # Load configurations
        self.keywords = self._load_yaml("keywords.yaml")
        self.sources = self._load_yaml("sources.yaml")
        
        # API Keys
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Paths
        self.metadata_dir = Path(os.getenv("METADATA_DIR", self.data_dir / "metadata"))
        self.raw_pdf_dir = Path(os.getenv("RAW_PDF_DIR", self.data_dir / "raw/pdfs"))
        self.raw_html_dir = Path(os.getenv("RAW_HTML_DIR", self.data_dir / "raw/html"))
        self.processed_docs_dir = Path(os.getenv("PROCESSED_DOCS_DIR", self.data_dir / "processed/docs"))
        self.processed_discussions_dir = Path(os.getenv("PROCESSED_DISCUSSIONS_DIR", self.data_dir / "processed/discussions"))
        self.embeddings_dir = Path(os.getenv("EMBEDDINGS_DIR", self.data_dir / "index/embeddings"))
        self.logs_dir = Path(os.getenv("LOGS_DIR", self.root_dir / "logs"))
        self.db_path = Path(os.getenv("DB_PATH", self.data_dir / "database/law_discussions.db"))
        
        # Crawling settings
        self.user_agent = os.getenv("USER_AGENT", "Mozilla/5.0")
        self.crawl_delay = int(os.getenv("CRAWL_DELAY", "2"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("TIMEOUT", "30"))
        
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        filepath = self.config_dir / filename
        if not filepath.exists():
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_all_keywords(self) -> List[str]:
        """Get all keywords from all categories"""
        keywords = []
        tech_keywords = self.keywords.get('tech_digital_keywords', {})
        
        for category, terms in tech_keywords.items():
            if isinstance(terms, list):
                keywords.extend(terms)
        
        return list(set(keywords))  # Remove duplicates
    
    def get_exclude_keywords(self) -> List[str]:
        """Get exclude keywords"""
        return self.keywords.get('exclude_keywords', [])
    
    def get_document_types(self) -> List[str]:
        """Get document types to collect"""
        return self.keywords.get('document_types', [])
    
    def get_enabled_sources(self) -> Dict[str, Any]:
        """Get enabled sources for crawling"""
        sources = self.sources.get('sources', {})
        return {k: v for k, v in sources.items() if v.get('enabled', False)}

# Global config instance
config = Config()
