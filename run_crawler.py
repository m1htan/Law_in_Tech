#!/usr/bin/env python3
"""
Script để chạy crawler với cấu hình mới tập trung vào các trang .gov.vn
về công nghệ thông tin, chuyển đổi số và khoa học công nghệ
"""

import os
import sys
import json
import orjson
from datetime import datetime

# Thêm src vào path để import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crawlers.crawl4ai_runner import run_crawl

def load_seeds():
    """Load danh sách URL seeds từ config"""
    config_path = os.path.join("config", "seeds.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_results(results, output_dir="outputs/jsonl"):
    """Lưu kết quả crawl vào file JSONL"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Group results by domain
    by_domain = {}
    for result in results:
        domain = result.get("source_site", "unknown")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(result)
    
    # Save each domain to separate file
    for domain, domain_results in by_domain.items():
        filename = f"{domain}.jsonl"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            for result in domain_results:
                f.write(orjson.dumps(result, option=orjson.OPT_INDENT_2) + b"\n")
        
        print(f"Đã lưu {len(domain_results)} kết quả từ {domain} vào {filepath}")

def main():
    """Main function"""
    print("🚀 Bắt đầu crawl các trang .gov.vn về công nghệ thông tin và chuyển đổi số...")
    print(f"⏰ Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load seeds
        seeds = load_seeds()
        print(f"📋 Đã load {len(seeds)} URL seeds:")
        for i, seed in enumerate(seeds, 1):
            print(f"   {i}. {seed}")
        
        # Run crawler
        print("\n🔍 Bắt đầu crawl...")
        results = run_crawl(seeds)
        
        print(f"\n✅ Hoàn thành crawl! Tìm thấy {len(results)} kết quả.")
        
        if results:
            # Save results
            save_results(results)
            
            # Print summary
            print("\n📊 Tóm tắt kết quả:")
            domains = {}
            doc_types = {}
            for result in results:
                domain = result.get("source_site", "unknown")
                doc_type = result.get("doc_type", "unknown")
                domains[domain] = domains.get(domain, 0) + 1
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            print("   Theo domain:")
            for domain, count in sorted(domains.items()):
                print(f"     - {domain}: {count} tài liệu")
            
            print("   Theo loại tài liệu:")
            for doc_type, count in sorted(doc_types.items()):
                print(f"     - {doc_type}: {count} tài liệu")
        else:
            print("⚠️  Không tìm thấy tài liệu nào phù hợp với tiêu chí.")
            
    except Exception as e:
        print(f"❌ Lỗi khi chạy crawler: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n⏰ Thời gian kết thúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    exit(main())