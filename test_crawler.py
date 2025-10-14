"""
Test script for Vietnamese Legal Crawler
"""
import asyncio
import json
from src.config import Config
from src.crawlers.legal_website_crawler import LegalWebsiteCrawler
from src.utils.logger import log


async def test_single_page_crawl():
    """Test crawling a single page"""
    print("\n" + "="*60)
    print("TEST 1: Single Page Crawl")
    print("="*60)
    
    # Use thuvienphapluat.vn as test
    website_config = {
        'name': 'Luật Minh Khuê',
        'url': 'https://thuvienphapluat.vn',
        'type': 'legal_database',
        'priority': 'high'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    # Test with a simple page about technology law
    test_url = "https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/tin-noi-bat/45262/nhung-van-ban-ve-chuyen-doi-so-co-hieu-luc-tu-thang-12-2023"
    
    log.info(f"Testing crawler with URL: {test_url}")
    
    result = await crawler.crawl_url(test_url, extract_pdfs=True)
    
    if result:
        print(f"\n✓ Successfully crawled page")
        print(f"  - Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  - Status: {result.get('status_code', 'N/A')}")
        print(f"  - Is Relevant: {result.get('is_relevant', False)}")
        print(f"  - PDF Links Found: {len(result.get('pdf_links', []))}")
        print(f"  - Content Length: {len(result.get('markdown', ''))} characters")
        
        # Show first 500 characters of content
        print(f"\n  Content preview:")
        print(f"  {result.get('markdown', '')[:500]}...")
        
        # Show PDF links if any
        if result.get('pdf_links'):
            print(f"\n  PDF Links:")
            for idx, pdf in enumerate(result['pdf_links'][:3], 1):
                print(f"    {idx}. {pdf.get('title', 'N/A')}")
                print(f"       URL: {pdf.get('url', 'N/A')}")
    else:
        print(f"\n✗ Failed to crawl page")
    
    # Save results
    crawler.save_results("test_single_page.json")
    
    # Show statistics
    stats = crawler.get_statistics()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return crawler


async def test_search_crawl():
    """Test searching and crawling results"""
    print("\n" + "="*60)
    print("TEST 2: Search and Crawl")
    print("="*60)
    
    website_config = {
        'name': 'Luật Minh Khuê',
        'url': 'https://thuvienphapluat.vn',
        'type': 'legal_database',
        'priority': 'high'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    # Search for documents about "chuyển đổi số"
    search_query = "chuyển đổi số"
    log.info(f"Testing search: {search_query}")
    
    results = await crawler.search_and_crawl(search_query, max_results=5)
    
    print(f"\n✓ Search completed")
    print(f"  - Results found: {len(results)}")
    
    for idx, result in enumerate(results, 1):
        if result:
            print(f"\n  {idx}. {result['metadata'].get('title', 'N/A')}")
            print(f"     URL: {result.get('url', 'N/A')}")
            print(f"     Relevant: {result.get('is_relevant', False)}")
            print(f"     Comments: {len(result.get('comments', []))}")
    
    # Save results
    crawler.save_results("test_search_results.json")
    
    # Show statistics
    stats = crawler.get_statistics()
    print(f"\nStatistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    return crawler


async def test_multiple_websites():
    """Test crawling multiple websites"""
    print("\n" + "="*60)
    print("TEST 3: Multiple Websites")
    print("="*60)
    
    # Test with multiple websites from config
    websites = [
        Config.TARGET_WEBSITES[4],  # thuvienphapluat.vn
        # Add more as needed
    ]
    
    all_results = []
    
    for website_config in websites:
        print(f"\nTesting: {website_config['name']}")
        crawler = LegalWebsiteCrawler(website_config)
        
        # Try to crawl homepage
        result = await crawler.crawl_url(website_config['url'], extract_pdfs=False)
        
        if result:
            print(f"  ✓ Successfully crawled homepage")
            print(f"    - Title: {result['metadata'].get('title', 'N/A')}")
            all_results.append(result)
        else:
            print(f"  ✗ Failed to crawl homepage")
    
    print(f"\nTotal websites tested: {len(websites)}")
    print(f"Successful crawls: {len(all_results)}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Vietnamese Legal Crawler - Test Suite")
    print("="*60)
    
    # Validate configuration (API key not required for basic crawling)
    print("\nValidating configuration...")
    Config.validate(require_api_key=False)
    print("✓ Configuration is valid")
    
    # Check API key status
    if not Config.GOOGLE_API_KEY or Config.GOOGLE_API_KEY == "your_google_api_key_here":
        print("⚠ Note: Google API Key not configured (not needed for basic crawling)")
    else:
        print("✓ Google API Key is configured")
    
    # Run tests
    try:
        # Test 1: Single page crawl
        await test_single_page_crawl()
        
        # Wait a bit between tests
        await asyncio.sleep(3)
        
        # Test 2: Search and crawl
        # await test_search_crawl()
        
        # Test 3: Multiple websites
        # await test_multiple_websites()
        
        print("\n" + "="*60)
        print("All tests completed!")
        print("="*60)
        print("\nCheck the following directories for results:")
        print(f"  - PDFs: {Config.PDF_OUTPUT_DIR}")
        print(f"  - Text files: {Config.TEXT_OUTPUT_DIR}")
        print(f"  - Logs: {Config.LOG_DIR}")
        
    except Exception as e:
        log.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
