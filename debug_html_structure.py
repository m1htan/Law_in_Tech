"""
Debug script to inspect HTML structure of thuvienphapluat.vn
"""
import asyncio
from bs4 import BeautifulSoup
from src.crawlers.base_crawler import BaseCrawler
from src.utils.logger import log


async def debug_category_page():
    """Debug category page structure"""
    print("\n" + "="*60)
    print("DEBUG: thuvienphapluat.vn HTML Structure")
    print("="*60)
    
    crawler = BaseCrawler()
    
    # Test URL
    url = "https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin.html"
    
    print(f"\nCrawling: {url}")
    
    result = await crawler.crawl_url(url, extract_pdfs=False, retry=2)
    
    if not result or not result.get('html'):
        print("✗ Failed to crawl page")
        return
    
    print("✓ Page crawled successfully")
    print(f"  Status: {result.get('status_code')}")
    print(f"  Content length: {len(result.get('html', ''))} chars")
    
    # Save HTML for inspection
    html_file = "debug_page.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(result['html'])
    print(f"\n✓ HTML saved to: {html_file}")
    
    # Parse and analyze
    soup = BeautifulSoup(result['html'], 'lxml')
    
    print("\n" + "-"*60)
    print("ANALYSIS")
    print("-"*60)
    
    # Check title
    title = soup.find('title')
    print(f"\nPage Title: {title.get_text() if title else 'N/A'}")
    
    # Look for common document list patterns
    print("\n1. Checking for document list containers...")
    
    containers = [
        ('div.item-vanban', soup.select('div.item-vanban')),
        ('div.search-result-item', soup.select('div.search-result-item')),
        ('div.doc-item', soup.select('div.doc-item')),
        ('div[class*="item"]', soup.select('div[class*="item"]')),
        ('div[class*="doc"]', soup.select('div[class*="doc"]')),
        ('div[class*="result"]', soup.select('div[class*="result"]')),
        ('ul.list-vb', soup.select('ul.list-vb')),
        ('div.list-vb', soup.select('div.list-vb')),
    ]
    
    for selector, elements in containers:
        if elements:
            print(f"  ✓ Found {len(elements)} items with selector: {selector}")
            
            # Show first item structure
            if elements:
                first = elements[0]
                print(f"\n  First item preview:")
                print(f"  {str(first)[:500]}...")
                
                # Find links
                links = first.select('a')
                print(f"\n  Links in first item: {len(links)}")
                for link in links[:3]:
                    print(f"    - {link.get('href', 'no href')}: {link.get_text(strip=True)[:60]}")
        else:
            print(f"  ✗ No items found with: {selector}")
    
    # Check for links containing "van-ban"
    print("\n2. Looking for links containing 'van-ban'...")
    van_ban_links = soup.select('a[href*="van-ban"]')
    print(f"  Found {len(van_ban_links)} links")
    
    if van_ban_links:
        print("\n  Sample links:")
        for link in van_ban_links[:10]:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            print(f"    - {href[:80]}")
            print(f"      Text: {text[:60]}")
    
    # Check for pagination
    print("\n3. Checking for pagination...")
    pagination_selectors = [
        'div.pagination',
        'ul.pagination',
        'div.paging',
        'a[class*="page"]',
        'a[href*="trang"]'
    ]
    
    for selector in pagination_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"  ✓ Found pagination: {selector} ({len(elements)} items)")
    
    # Check all div classes
    print("\n4. All unique div classes on page:")
    all_divs = soup.find_all('div', class_=True)
    unique_classes = set()
    for div in all_divs:
        classes = div.get('class', [])
        for cls in classes:
            unique_classes.add(cls)
    
    print(f"  Total unique classes: {len(unique_classes)}")
    print("\n  Classes containing 'item', 'doc', 'list', or 'result':")
    for cls in sorted(unique_classes):
        if any(keyword in cls.lower() for keyword in ['item', 'doc', 'list', 'result', 'vb', 'van']):
            print(f"    - {cls}")
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
    print(f"\nNext steps:")
    print(f"1. Check {html_file} manually")
    print(f"2. Find correct selectors for document items")
    print(f"3. Update production_crawler.py with new selectors")


if __name__ == "__main__":
    asyncio.run(debug_category_page())
