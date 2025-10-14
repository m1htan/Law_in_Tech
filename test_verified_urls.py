"""
Test crawler with only VERIFIED URLs
"""
import asyncio
from src.config import Config
from src.crawlers.legal_website_crawler import LegalWebsiteCrawler
from src.utils.logger import log


async def test_verified_websites():
    """Test crawling with verified websites only"""
    print("\n" + "="*60)
    print("TEST: Crawling VERIFIED Vietnamese Legal Websites")
    print("="*60)
    
    # Validate configuration
    print("\nValidating configuration...")
    Config.validate(require_api_key=False)
    print("✓ Configuration is valid\n")
    
    # Get only verified websites
    verified_sites = Config.get_verified_websites()
    
    print(f"Found {len(verified_sites)} verified websites:")
    for idx, site in enumerate(verified_sites, 1):
        print(f"  {idx}. {site['name']}")
        print(f"     URL: {site['url']}")
        if site.get('note'):
            print(f"     Note: {site['note']}")
    
    print(f"\n{'-'*60}")
    print("Starting crawl tests...")
    print(f"{'-'*60}\n")
    
    results = []
    successful = 0
    failed = 0
    
    for idx, website_config in enumerate(verified_sites, 1):
        print(f"\n[{idx}/{len(verified_sites)}] Testing: {website_config['name']}")
        print(f"URL: {website_config['url']}")
        
        crawler = LegalWebsiteCrawler(website_config)
        
        try:
            result = await crawler.crawl_url(
                website_config['url'],
                extract_pdfs=False,
                retry=2  # Reduce retries for faster testing
            )
            
            if result:
                successful += 1
                print(f"✅ SUCCESS")
                print(f"   - Title: {result['metadata'].get('title', 'N/A')[:70]}")
                print(f"   - Status: {result.get('status_code', 'N/A')}")
                print(f"   - Content: {len(result.get('markdown', ''))} chars")
                print(f"   - Relevant: {result.get('is_relevant', False)}")
                
                # Extract document links
                if result.get('html'):
                    doc_links = crawler.extract_document_links(
                        result['html'],
                        website_config['url']
                    )
                    print(f"   - Doc links found: {len(doc_links)}")
                    
                    if doc_links and len(doc_links) > 0:
                        print(f"   - Sample: {doc_links[0].get('title', 'N/A')[:60]}")
                
                results.append({
                    'website': website_config['name'],
                    'url': website_config['url'],
                    'success': True,
                    'data': result
                })
            else:
                failed += 1
                print(f"❌ FAILED - No data returned")
                results.append({
                    'website': website_config['name'],
                    'url': website_config['url'],
                    'success': False
                })
                
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {str(e)[:100]}")
            results.append({
                'website': website_config['name'],
                'url': website_config['url'],
                'success': False,
                'error': str(e)
            })
        
        # Delay between requests
        if idx < len(verified_sites):
            await asyncio.sleep(Config.REQUEST_DELAY)
    
    # Print summary
    print(f"\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total verified websites: {len(verified_sites)}")
    print(f"✅ Successful crawls: {successful}")
    print(f"❌ Failed crawls: {failed}")
    print(f"📊 Success rate: {successful/len(verified_sites)*100:.1f}%")
    
    # Show successful websites
    if successful > 0:
        print(f"\n✅ Working websites:")
        for r in results:
            if r['success']:
                print(f"   • {r['website']}")
                print(f"     {r['url']}")
    
    # Show failed websites
    if failed > 0:
        print(f"\n❌ Failed websites:")
        for r in results:
            if not r['success']:
                print(f"   • {r['website']}")
                print(f"     {r['url']}")
                if 'error' in r:
                    print(f"     Error: {r['error'][:80]}")
    
    print("="*60)
    
    return results


async def test_single_high_priority():
    """Quick test with a single high-priority site"""
    print("\n" + "="*60)
    print("QUICK TEST: Single High-Priority Website")
    print("="*60)
    
    # Use chinhphu.vn - most reliable
    website_config = {
        'name': 'Cổng Thông tin điện tử Chính phủ',
        'url': 'https://chinhphu.vn',
        'type': 'government'
    }
    
    crawler = LegalWebsiteCrawler(website_config)
    
    result = await crawler.crawl_url(
        website_config['url'],
        extract_pdfs=False,
        retry=2
    )
    
    if result:
        print(f"\n✅ Crawl successful!")
        print(f"   Title: {result['metadata'].get('title', 'N/A')}")
        print(f"   Status: {result.get('status_code', 'N/A')}")
        print(f"   Relevant: {result.get('is_relevant', False)}")
        
        # Extract links
        doc_links = crawler.extract_document_links(result['html'], website_config['url'])
        print(f"   Document links: {len(doc_links)}")
        
        if doc_links:
            print(f"\n   Top 3 documents:")
            for idx, link in enumerate(doc_links[:3], 1):
                print(f"   {idx}. {link.get('title', 'N/A')[:70]}")
    else:
        print(f"\n❌ Crawl failed")


async def main():
    """Run tests"""
    print("\n" + "="*60)
    print("Vietnamese Legal Crawler - Verified URLs Test")
    print("="*60)
    
    try:
        # Quick test first
        await test_single_high_priority()
        
        print("\n\n")
        await asyncio.sleep(2)
        
        # Full test with all verified URLs
        await test_verified_websites()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        print("\n💡 Next steps:")
        print("  1. URLs are now verified and fixed")
        print("  2. Crawler has retry logic and timeout improvements")
        print("  3. Ready for Bước 3: LangGraph AI Agent integration")
        
    except Exception as e:
        log.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
