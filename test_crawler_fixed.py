"""
Test crawler with improved timeout handling and retry logic
"""
import asyncio
from src.config import Config
from src.crawlers.legal_website_crawler import LegalWebsiteCrawler
from src.utils.logger import log


async def test_with_retry():
    """Test crawler with retry logic"""
    print("\n" + "="*60)
    print("TEST: Crawler với Retry Logic & Timeout Improvements")
    print("="*60)
    
    # Validate configuration
    print("\nValidating configuration...")
    Config.validate(require_api_key=False)
    print("✓ Configuration is valid\n")
    
    print(f"Settings:")
    print(f"  - Max Retries: {Config.MAX_RETRIES}")
    print(f"  - Crawl Timeout: {Config.CRAWL_TIMEOUT}ms")
    print(f"  - Request Delay: {Config.REQUEST_DELAY}s")
    
    # Test with different websites
    test_urls = [
        {
            'name': 'Cổng Thông tin điện tử Chính phủ',
            'url': 'https://chinhphu.vn',
            'type': 'government'
        },
        {
            'name': 'Bộ Thông tin và Truyền thông',
            'url': 'https://mic.gov.vn',
            'type': 'ministry'
        },
    ]
    
    results = []
    
    for idx, website_config in enumerate(test_urls, 1):
        print(f"\n{'-'*60}")
        print(f"Test {idx}/{len(test_urls)}: {website_config['name']}")
        print(f"{'-'*60}")
        
        crawler = LegalWebsiteCrawler(website_config)
        
        result = await crawler.crawl_url(
            website_config['url'],
            extract_pdfs=False
        )
        
        if result:
            print(f"\n✓ Crawl thành công!")
            print(f"  - Title: {result['metadata'].get('title', 'N/A')[:80]}")
            print(f"  - Status: {result.get('status_code', 'N/A')}")
            print(f"  - Content: {len(result.get('markdown', ''))} characters")
            print(f"  - Relevant: {result.get('is_relevant', False)}")
            
            # Try to extract document links
            if result.get('html'):
                doc_links = crawler.extract_document_links(result['html'], website_config['url'])
                print(f"  - Document links: {len(doc_links)}")
                
                if doc_links:
                    print(f"\n  Sample links (first 3):")
                    for i, link in enumerate(doc_links[:3], 1):
                        print(f"    {i}. {link.get('title', 'N/A')[:60]}")
            
            results.append(result)
        else:
            print(f"\n✗ Crawl thất bại sau {Config.MAX_RETRIES} lần thử")
        
        # Delay between websites
        if idx < len(test_urls):
            print(f"\nWaiting {Config.REQUEST_DELAY}s before next test...")
            await asyncio.sleep(Config.REQUEST_DELAY)
    
    # Summary
    print(f"\n" + "="*60)
    print(f"SUMMARY")
    print(f"="*60)
    print(f"Total tests: {len(test_urls)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(test_urls) - len(results)}")
    print(f"Success rate: {len(results)/len(test_urls)*100:.1f}%")
    
    return results


async def test_specific_technology_page():
    """Test with a page about technology/digital transformation"""
    print("\n" + "="*60)
    print("TEST: Trang về Công nghệ/Chuyển đổi số")
    print("="*60)
    
    website_config = {
        'name': 'Bộ Thông tin và Truyền thông',
        'url': 'https://mic.gov.vn',
        'type': 'ministry'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    # MIC homepage should have tech-related content
    result = await crawler.crawl_url(
        'https://mic.gov.vn',
        extract_pdfs=False
    )
    
    if result:
        print(f"\n✓ Crawl thành công!")
        print(f"  - Title: {result['metadata'].get('title', 'N/A')}")
        print(f"  - Is Relevant: {result.get('is_relevant', False)}")
        
        # Extract tech-related links
        if result.get('html'):
            doc_links = crawler.extract_document_links(result['html'], 'https://mic.gov.vn')
            
            print(f"\n  Tech-related documents found: {len(doc_links)}")
            if doc_links:
                print(f"\n  Top documents:")
                for idx, link in enumerate(doc_links[:5], 1):
                    print(f"    {idx}. {link.get('title', 'N/A')}")
    else:
        print(f"\n✗ Crawl failed")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Vietnamese Legal Crawler - Fixed & Improved")
    print("="*60)
    
    try:
        # Test 1: Retry logic
        await test_with_retry()
        
        print("\n\n")
        await asyncio.sleep(3)
        
        # Test 2: Specific technology page
        await test_specific_technology_page()
        
        print("\n" + "="*60)
        print("✓ All tests completed!")
        print("="*60)
        print("\nImprovements made:")
        print("  ✓ Increased timeout to 60 seconds")
        print("  ✓ Added retry logic (3 attempts)")
        print("  ✓ Multiple wait strategies (networkidle, domcontentloaded, load)")
        print("  ✓ Exponential backoff between retries")
        print("  ✓ Better error handling and logging")
        print("  ✓ Stealth mode enabled (magic=True)")
        
    except Exception as e:
        log.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
