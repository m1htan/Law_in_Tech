"""
Configuration module for Vietnamese Legal Documents Crawler
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the crawler system"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # Crawling Configuration
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))
    REQUEST_DELAY = int(os.getenv("REQUEST_DELAY", "2"))
    USER_AGENT = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    
    # Data Storage Paths
    BASE_DIR = Path(__file__).parent.parent
    PDF_OUTPUT_DIR = BASE_DIR / os.getenv("PDF_OUTPUT_DIR", "data/pdf_documents")
    TEXT_OUTPUT_DIR = BASE_DIR / os.getenv("TEXT_OUTPUT_DIR", "data/text_documents")
    LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
    
    # Date Range
    START_YEAR = int(os.getenv("START_YEAR", "2022"))
    END_YEAR = int(os.getenv("END_YEAR", "2024"))
    
    # Target websites for crawling
    TARGET_WEBSITES = [
        # Nhóm 1: Chính phủ & Bộ ngành
        {
            "name": "Cổng Thông tin điện tử Chính phủ",
            "url": "https://chinhphu.vn",
            "priority": "high",
            "type": "government"
        },
        {
            "name": "Hệ thống văn bản Chính phủ",
            "url": "https://vanban.chinhphu.vn",
            "priority": "high",
            "type": "government"
        },
        {
            "name": "Bộ Thông tin và Truyền thông",
            "url": "https://mic.gov.vn",
            "priority": "high",
            "type": "ministry"
        },
        {
            "name": "Bộ Khoa học và Công nghệ",
            "url": "https://most.gov.vn",
            "priority": "high",
            "type": "ministry"
        },
        # Nhóm 2: Cơ sở dữ liệu pháp luật
        {
            "name": "Luật Minh Khuê",
            "url": "https://thuvienphapluat.vn",
            "priority": "high",
            "type": "legal_database"
        },
        {
            "name": "LawNet",
            "url": "https://lawnet.vn",
            "priority": "medium",
            "type": "legal_database"
        },
        {
            "name": "Công báo Chính phủ",
            "url": "https://congbao.chinhphu.vn",
            "priority": "medium",
            "type": "government"
        },
        # Nhóm 3: Trang lấy ý kiến dự thảo
        {
            "name": "Dự thảo văn bản Chính phủ",
            "url": "https://duthaovanban.chinhphu.vn",
            "priority": "high",
            "type": "draft"
        },
        # Nhóm 4: Quốc hội
        {
            "name": "Trang Quốc hội",
            "url": "https://quochoi.vn",
            "priority": "high",
            "type": "parliament"
        }
    ]
    
    # Keywords for filtering (focusing on technology and digital transformation)
    TECH_KEYWORDS = [
        "công nghệ",
        "chuyển đổi số",
        "số hóa",
        "trí tuệ nhân tạo",
        "AI",
        "dữ liệu",
        "an toàn thông tin",
        "an ninh mạng",
        "internet",
        "viễn thông",
        "công nghệ thông tin",
        "CNTT",
        "phát triển công nghệ",
        "khoa học công nghệ",
        "đổi mới sáng tạo",
        "startup",
        "khởi nghiệp",
        "blockchain",
        "big data",
        "cloud computing",
        "điện toán đám mây",
        "5G",
        "IoT",
        "thương mại điện tử"
    ]
    
    # Document types to crawl
    DOCUMENT_TYPES = [
        "nghị quyết",
        "nghị định",
        "quyết định",
        "thông tư",
        "chỉ thị",
        "luật",
        "dự thảo",
        "dự án luật",
        "văn bản"
    ]
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEXT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls, require_api_key: bool = True):
        """
        Validate configuration
        
        Args:
            require_api_key: Whether to require Google API key (needed for AI Agent, not for basic crawling)
        """
        if require_api_key:
            if not cls.GOOGLE_API_KEY or cls.GOOGLE_API_KEY == "your_google_api_key_here":
                raise ValueError(
                    "GOOGLE_API_KEY is not set. Please add your API key to the .env file"
                )
        
        cls.ensure_directories()
        return True

# Initialize directories on import
Config.ensure_directories()
