"""
GOVERNMENT CRAWLER - Official .gov.vn sources only
Chỉ crawl từ các trang chính phủ Việt Nam
"""
import asyncio
import argparse
from src.crawlers.government_crawler import GovernmentSitesCrawler
from src.database.models import DatabaseManager
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
    
    db = DatabaseManager()
    crawler = GovernmentSitesCrawler(db)
    
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
    
    # Database statistics
    db_stats = db.get_statistics()
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Total documents: {db_stats['total_documents']}")
    print(f"Tech documents: {db_stats['tech_documents']}")
    
    if db_stats.get('by_type'):
        print("\nBy document type:")
        for doc_type, count in db_stats['by_type'].items():
            print(f"  {doc_type}: {count}")
    
    db.close()
    
    print("\n✅ Done! Check database at: data/legal_documents.db")
    print("Export data: python3 tools/export_data.py --tech-only --format json")


if __name__ == "__main__":
    asyncio.run(main())
