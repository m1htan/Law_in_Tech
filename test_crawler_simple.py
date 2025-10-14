"""
Simple test script for Vietnamese Legal Crawler
Tests with live URLs
"""
import asyncio
from src.config import Config
from src.crawlers.legal_website_crawler import LegalWebsiteCrawler
from src.utils.logger import log


async def test_homepage_crawl():
    """Test crawling thuvienphapluat.vn homepage"""
    print("\n" + "="*60)
    print("TEST: Crawling thuvienphapluat.vn Homepage")
    print("="*60)
    
    website_config = {
        'name': 'Luật Minh Khuê',
        'url': 'https://thuvienphapluat.vn',
        'type': 'legal_database',
        'priority': 'high'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    # Test with homepage
    test_url = "https://thuvienphapluat.vn"
    
    log.info(f"Crawling: {test_url}")
    
    result = await crawler.crawl_url(test_url, extract_pdfs=False)
    
    if result:
        print(f"\n✓ Successfully crawled page")
        print(f"  - Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  - Status: {result.get('status_code', 'N/A')}")
        print(f"  - Content Length: {len(result.get('markdown', ''))} characters")
        
        # Extract document links
        doc_links = crawler.extract_document_links(result['html'], test_url)
        print(f"  - Document links found: {len(doc_links)}")
        
        # Show first 5 document links
        if doc_links:
            print(f"\n  Sample document links:")
            for idx, link in enumerate(doc_links[:5], 1):
                print(f"    {idx}. {link.get('title', 'N/A')[:80]}")
                print(f"       URL: {link.get('url', 'N/A')}")
        
        # Now crawl one of the documents
        if doc_links:
            print(f"\n  Crawling first document in detail...")
            doc_url = doc_links[0]['url']
            doc_result = await crawler.crawl_url(doc_url, extract_pdfs=True)
            
            if doc_result:
                print(f"\n  ✓ Document crawled successfully")
                print(f"    - Title: {doc_result['metadata'].get('title', 'N/A')}")
                print(f"    - Is Relevant: {doc_result.get('is_relevant', False)}")
                print(f"    - PDF Links: {len(doc_result.get('pdf_links', []))}")
                print(f"    - Comments: {len(doc_result.get('comments', []))}")
                
                # Show PDF links
                if doc_result.get('pdf_links'):
                    print(f"\n    PDF files found:")
                    for idx, pdf in enumerate(doc_result['pdf_links'][:3], 1):
                        print(f"      {idx}. {pdf.get('title', 'N/A')}")
        
        # Save results
        crawler.save_results("test_homepage_crawl.json")
        
    else:
        print(f"\n✗ Failed to crawl page")
    
    # Show statistics
    stats = crawler.get_statistics()
    print(f"\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return crawler


async def test_specific_document():
    """Test with a specific legal document URL"""
    print("\n" + "="*60)
    print("TEST: Specific Legal Document")
    print("="*60)
    
    website_config = {
        'name': 'Cổng Thông tin điện tử Chính phủ',
        'url': 'https://chinhphu.vn',
        'type': 'government',
        'priority': 'high'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    # Test with a page about digital transformation
    # Using a general page that likely exists
    test_url = "https://chinhphu.vn"
    
    log.info(f"Crawling: {test_url}")
    
    result = await crawler.crawl_url(test_url, extract_pdfs=False)
    
    if result:
        print(f"\n✓ Successfully crawled page")
        print(f"  - Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  - Status: {result.get('status_code', 'N/A')}")
        print(f"  - Content Length: {len(result.get('markdown', ''))} characters")
        
        # Extract document links
        doc_links = crawler.extract_document_links(result['html'], test_url)
        print(f"  - Document links found: {len(doc_links)}")
        
        if doc_links:
            print(f"\n  Sample document links (relevant to technology):")
            for idx, link in enumerate(doc_links[:5], 1):
                print(f"    {idx}. {link.get('title', 'N/A')[:100]}")
        
        # Save results
        crawler.save_results("test_chinhphu_crawl.json")
        
    else:
        print(f"\n✗ Failed to crawl page")
    
    # Show statistics
    stats = crawler.get_statistics()
    print(f"\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")


async def main():
    """Run tests"""
    print("\n" + "="*60)
    print("Vietnamese Legal Crawler - Simple Test")
    print("="*60)
    
    # Validate configuration
    print("\nValidating configuration...")
    Config.validate(require_api_key=False)
    print("✓ Configuration is valid\n")
    
    try:
        # Test 1: Homepage crawl
        await test_homepage_crawl()
        
        # Wait between tests
        print("\n" + "-"*60)
        await asyncio.sleep(3)
        
        # Test 2: Specific document
        await test_specific_document()
        
        print("\n" + "="*60)
        print("✓ All tests completed successfully!")
        print("="*60)
        print("\nResults saved to:")
        print(f"  - Logs: {Config.LOG_DIR}")
        print(f"  - PDFs: {Config.PDF_OUTPUT_DIR}")
        print(f"  - Text: {Config.TEXT_OUTPUT_DIR}")
        
    except Exception as e:
        log.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
