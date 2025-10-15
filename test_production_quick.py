"""
Quick test for production crawler with improved selectors
"""
import asyncio
from bs4 import BeautifulSoup
from src.crawlers.base_crawler import BaseCrawler
from src.database.models import DatabaseManager
from src.crawlers.production_crawler import ThuvienPhapLuatProductionCrawler
from src.utils.logger import log


async def test_extract_documents():
    """Test document extraction from actual page"""
    print("\n" + "="*60)
    print("TEST: Document Extraction from thuvienphapluat.vn")
    print("="*60)
    
    crawler = BaseCrawler()
    
    # Try different URLs
    test_urls = [
        "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin.html",
        "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/trang1.html",
        "https://thuvienphapluat.vn/page/tim-van-ban.html?keyword=công+nghệ+thông+tin&page=1",
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing URL: {url}")
        print(f"{'='*60}")
        
        result = await crawler.crawl_url(url, extract_pdfs=False, retry=1)
        
        if not result or not result.get('html'):
            print("✗ Failed to crawl")
            continue
        
        print(f"✓ Crawled successfully")
        print(f"  Content: {len(result['html'])} chars")
        
        # Try to extract documents
        db = DatabaseManager()
        prod_crawler = ThuvienPhapLuatProductionCrawler(db)
        
        docs = prod_crawler.extract_document_list(result['html'], url)
        
        print(f"\n📄 Documents found: {len(docs)}")
        
        if docs:
            print("\nSample documents (first 5):")
            for idx, doc in enumerate(docs[:5], 1):
                print(f"\n{idx}. {doc.get('title', 'No title')[:80]}")
                print(f"   URL: {doc.get('url', 'No URL')[:100]}")
                print(f"   Number: {doc.get('document_number', 'N/A')}")
                print(f"   Type: {doc.get('document_type', 'N/A')}")
            
            # Test crawling one document
            print(f"\n{'='*60}")
            print("Testing document detail crawl...")
            print(f"{'='*60}")
            
            first_doc = docs[0]
            print(f"\nCrawling: {first_doc['url']}")
            
            doc_detail = await prod_crawler.crawl_document_detail(first_doc['url'])
            
            if doc_detail:
                print(f"\n✓ Document crawled successfully!")
                print(f"  ID: {doc_detail.id}")
                print(f"  Title: {doc_detail.title[:80]}")
                print(f"  Number: {doc_detail.document_number}")
                print(f"  Type: {doc_detail.document_type}")
                print(f"  Issued: {doc_detail.issued_date}")
                print(f"  PDF: {doc_detail.pdf_path or 'N/A'}")
                print(f"  Text: {doc_detail.text_path or 'N/A'}")
            else:
                print("✗ Failed to crawl document detail")
            
            # Success! Stop testing other URLs
            print(f"\n{'='*60}")
            print("✅ TEST PASSED - Documents extracted successfully!")
            print(f"{'='*60}")
            
            db.close()
            return True
        
        db.close()
    
    print(f"\n{'='*60}")
    print("❌ TEST FAILED - No documents found on any URL")
    print(f"{'='*60}")
    return False


async def test_alternative_search():
    """Test using search API instead of category"""
    print("\n" + "="*60)
    print("ALTERNATIVE: Using Search API")
    print("="*60)
    
    crawler = BaseCrawler()
    
    # Try search URL
    search_url = "https://thuvienphapluat.vn/tim-kiem.html?keyword=cong+nghe+thong+tin&area=2&type=3"
    
    print(f"\nTesting search: {search_url}")
    
    result = await crawler.crawl_url(search_url, extract_pdfs=False, retry=2)
    
    if result and result.get('html'):
        print("✓ Search page crawled")
        
        soup = BeautifulSoup(result['html'], 'lxml')
        
        # Find all links
        links = soup.find_all('a', href=True)
        doc_links = [l for l in links if '/van-ban/' in l.get('href', '')]
        
        print(f"  Found {len(doc_links)} document links via search")
        
        if doc_links:
            for idx, link in enumerate(doc_links[:5], 1):
                print(f"  {idx}. {link.get_text(strip=True)[:60]}")
                print(f"     {link['href']}")
            
            return True
    
    return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRODUCTION CRAWLER - Quick Test")
    print("="*60)
    
    # Test document extraction
    success = asyncio.run(test_extract_documents())
    
    if not success:
        print("\nTrying alternative search method...")
        asyncio.run(test_alternative_search())
