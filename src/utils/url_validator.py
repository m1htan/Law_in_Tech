"""
URL validation utility for Vietnamese Legal Crawler
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.utils.logger import log


class URLValidator:
    """Validate URLs before crawling"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize validator
        
        Args:
            timeout: Timeout in seconds for HTTP requests
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_url(self, url: str) -> Dict:
        """
        Check if URL is accessible
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with check results
        """
        result = {
            'url': url,
            'accessible': False,
            'status_code': None,
            'redirect_url': None,
            'error': None,
            'dns_resolved': True
        }
        
        try:
            log.info(f"Checking URL: {url}")
            
            # Parse URL to check format
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                result['error'] = "Invalid URL format"
                return result
            
            # Try to make request
            async with self.session.head(url, allow_redirects=True) as response:
                result['accessible'] = True
                result['status_code'] = response.status
                
                # Check for redirects
                if str(response.url) != url:
                    result['redirect_url'] = str(response.url)
                
                log.info(f"✓ URL accessible: {url} (Status: {response.status})")
                
        except aiohttp.ClientConnectorError as e:
            result['error'] = f"DNS/Connection error: {str(e)}"
            result['dns_resolved'] = False
            log.warning(f"✗ URL not accessible (DNS error): {url}")
            
        except aiohttp.ClientError as e:
            result['error'] = f"Client error: {str(e)}"
            log.warning(f"✗ URL not accessible (Client error): {url}")
            
        except asyncio.TimeoutError:
            result['error'] = "Timeout"
            log.warning(f"✗ URL timeout: {url}")
            
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            log.error(f"✗ Error checking URL {url}: {e}")
        
        return result
    
    async def check_multiple(self, urls: List[str]) -> List[Dict]:
        """
        Check multiple URLs concurrently
        
        Args:
            urls: List of URLs to check
            
        Returns:
            List of check results
        """
        log.info(f"Checking {len(urls)} URLs...")
        
        tasks = [self.check_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                log.error(f"Exception during URL check: {r}")
            else:
                valid_results.append(r)
        
        # Summary
        accessible = sum(1 for r in valid_results if r['accessible'])
        log.info(f"URL check complete: {accessible}/{len(urls)} accessible")
        
        return valid_results
    
    def print_summary(self, results: List[Dict]):
        """
        Print summary of URL check results
        
        Args:
            results: List of check results
        """
        print("\n" + "="*60)
        print("URL Validation Summary")
        print("="*60)
        
        accessible = [r for r in results if r['accessible']]
        not_accessible = [r for r in results if not r['accessible']]
        
        print(f"\n✅ Accessible URLs ({len(accessible)}):")
        for r in accessible:
            status = r['status_code']
            redirect = f" → {r['redirect_url']}" if r['redirect_url'] else ""
            print(f"  • {r['url']} (Status: {status}){redirect}")
        
        if not_accessible:
            print(f"\n❌ Not Accessible URLs ({len(not_accessible)}):")
            for r in not_accessible:
                print(f"  • {r['url']}")
                print(f"    Error: {r['error']}")
        
        print(f"\n📊 Success Rate: {len(accessible)}/{len(results)} ({len(accessible)/len(results)*100:.1f}%)")
        print("="*60)


async def validate_config_urls():
    """Validate all URLs in config"""
    from src.config import Config
    
    urls = [w['url'] for w in Config.TARGET_WEBSITES]
    
    async with URLValidator(timeout=10) as validator:
        results = await validator.check_multiple(urls)
        validator.print_summary(results)
        
        return results


if __name__ == "__main__":
    # Test URL validator
    asyncio.run(validate_config_urls())
