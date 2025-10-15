#!/usr/bin/env python3
"""
Script test cấu hình mới cho crawler .gov.vn
"""

import os
import json
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def load_config():
    """Load cấu hình từ các file config"""
    config_dir = 'config'
    
    def _load_list(path):
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.json'):
                return json.load(f)
            return [line.strip() for line in f if line.strip()]
    
    return {
        'domains': set(_load_list(os.path.join(config_dir, 'allow_domains.json'))),
        'keywords': [k.lower() for k in _load_list(os.path.join(config_dir, 'keywords.txt'))],
        'seeds': _load_list(os.path.join(config_dir, 'seeds.json')),
        'url_regex': [re.compile(p, re.I) for p in _load_list(os.path.join(config_dir, 'url_allow_regex.json'))]
    }

def is_allowed_url(url, url_regex):
    """Kiểm tra URL có được phép không"""
    return any(r.match(url) for r in url_regex)

def get_domain(url):
    """Lấy domain từ URL"""
    return urlparse(url).netloc.replace('www.', '')

def has_relevant_keywords(text, keywords):
    """Kiểm tra text có chứa từ khóa liên quan không"""
    text_lower = text.lower()
    found_keywords = [k for k in keywords if k in text_lower]
    return found_keywords

def test_url(url, config):
    """Test một URL xem có phù hợp với cấu hình không"""
    print(f"\n🔍 Testing: {url}")
    
    # Check domain
    domain = get_domain(url)
    if domain not in config['domains']:
        print(f"   ❌ Domain '{domain}' không trong danh sách cho phép")
        return False
    
    # Check URL regex
    if not is_allowed_url(url, config['url_regex']):
        print(f"   ❌ URL không match với regex patterns")
        return False
    
    print(f"   ✅ Domain và URL pattern hợp lệ")
    
    # Try to fetch content
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title and text content
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Get main content (remove script, style tags)
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text()
        
        # Check for relevant keywords
        all_text = f"{title_text} {text_content}"
        found_keywords = has_relevant_keywords(all_text, config['keywords'])
        
        if found_keywords:
            print(f"   ✅ Tìm thấy {len(found_keywords)} từ khóa liên quan:")
            for kw in found_keywords[:5]:  # Show first 5 keywords
                print(f"      - {kw}")
            if len(found_keywords) > 5:
                print(f"      ... và {len(found_keywords)-5} từ khóa khác")
            return True
        else:
            print(f"   ⚠️  Không tìm thấy từ khóa liên quan nào")
            return False
            
    except Exception as e:
        print(f"   ❌ Lỗi khi fetch URL: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Test cấu hình crawler mới cho .gov.vn")
    print("=" * 50)
    
    # Load config
    config = load_config()
    
    print(f"📋 Cấu hình đã load:")
    print(f"   - {len(config['domains'])} domains được phép")
    print(f"   - {len(config['keywords'])} từ khóa")
    print(f"   - {len(config['seeds'])} URL seeds")
    print(f"   - {len(config['url_regex'])} URL regex patterns")
    
    # Test some seed URLs
    print(f"\n🧪 Test một số URL seeds:")
    successful_urls = []
    
    # Test first few seeds
    test_seeds = config['seeds'][:5]  # Test first 5 seeds
    
    for url in test_seeds:
        if test_url(url, config):
            successful_urls.append(url)
    
    print(f"\n📊 Kết quả:")
    print(f"   - Đã test: {len(test_seeds)} URLs")
    print(f"   - Thành công: {len(successful_urls)} URLs")
    print(f"   - Tỷ lệ thành công: {len(successful_urls)/len(test_seeds)*100:.1f}%")
    
    if successful_urls:
        print(f"\n✅ URLs thành công:")
        for url in successful_urls:
            print(f"   - {url}")
    
    return len(successful_urls)

if __name__ == "__main__":
    result = main()
    print(f"\n🏁 Hoàn thành test với {result} URLs thành công!")