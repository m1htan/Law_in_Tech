"""
GOVERNMENT CRAWLER - Official .gov.vn sources only
Chỉ crawl từ các trang chính phủ Việt Nam
"""
import asyncio
import argparse
from src.crawlers.government_crawler import GovernmentSitesCrawler
from src.storage.file_storage import FileStorageManager
from src.utils.logger import log


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Government Sites Crawler - Official .gov.vn only"
    )
    
    parser.add_argument(
        '--max-docs',
        type=int,
        default=100,
        help='Maximum total documents to crawl (default: 100)'
    )
    
    parser.add_argument(
        '--source',
        choices=['all', 'vanban', 'mst'],
        default='all',
        help='Which source to crawl (default: all)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("🏛️  GOVERNMENT SITES CRAWLER")
    print("="*60)
    print(f"Only official .gov.vn sources")
    print(f"Max documents: {args.max_docs}")
    print(f"Source: {args.source}")
    print("="*60)
    
    storage = FileStorageManager()
    crawler = GovernmentSitesCrawler(storage)
    
    if args.source == 'all':
        # Crawl all government sites
        stats = await crawler.crawl_all_government_sites(
            max_docs_per_site=args.max_docs // 2
        )
        
    elif args.source == 'vanban':
        # Only vanban.chinhphu.vn
        stats = await crawler.crawl_vanban_chinhphu(
            max_pages=20,
            max_documents=args.max_docs
        )
        
    elif args.source == 'mst':
        # Only mst.gov.vn
        stats = await crawler.crawl_mst_gov_vn(
            max_pages=10,
            max_documents=args.max_docs
        )
    
    # Show results
    print("\n" + "="*60)
    print("CRAWL COMPLETED")
    print("="*60)
    
    if isinstance(stats, dict):
        for key, value in stats.items():
            if key != 'details':
                print(f"{key}: {value}")
    
    # Storage statistics
    storage_stats = storage.get_statistics()
    print("\n" + "="*60)
    print("STORAGE STATISTICS")
    print("="*60)
    print(f"Total documents: {storage_stats['total_documents']}")
    print(f"Tech documents: {storage_stats['tech_documents']}")
    print(f"With PDFs: {storage_stats['with_pdfs']}")
    print(f"With texts: {storage_stats['with_texts']}")
    
    if storage_stats.get('by_type'):
        print("\nBy document type:")
        for doc_type, count in storage_stats['by_type'].items():
            print(f"  {doc_type}: {count}")
    
    print("\n✅ Done!")
    print(f"📁 PDFs: data/pdf_documents/ ({storage_stats['with_pdfs']} files)")
    print(f"📝 Texts: data/text_documents/ ({storage_stats['with_texts']} files)")
    print(f"📊 Metadata: data/metadata.json")
    print(f"\n💡 View data: python3 view_data.py")
    print(f"💡 Export: python3 tools/export_data.py --format json")


if __name__ == "__main__":
    asyncio.run(main())
