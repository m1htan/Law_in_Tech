"""
Production Crawler - Main Entry Point
Crawl toàn bộ văn bản pháp luật VN (focus CNTT)
"""
import asyncio
import argparse
from pathlib import Path

from src.crawlers.production_crawler import ThuvienPhapLuatProductionCrawler
from src.database.models import DatabaseManager
from src.utils.logger import log


async def run_full_crawl():
    """Crawl tất cả categories CNTT"""
    print("\n" + "="*60)
    print("PRODUCTION CRAWL - Vietnamese Legal Documents")
    print("Focus: Công nghệ thông tin")
    print("="*60)
    
    db = DatabaseManager()
    crawler = ThuvienPhapLuatProductionCrawler(db)
    
    all_stats = []
    
    # Crawl all tech categories
    for category_key, category_info in crawler.tech_categories.items():
        print(f"\n{'='*60}")
        print(f"CATEGORY: {category_info['name']}")
        print(f"{'='*60}\n")
        
        stats = await crawler.crawl_category_systematic(
            category_key=category_key,
            max_pages=None,  # Unlimited
            max_documents=None  # Unlimited
        )
        
        all_stats.append(stats)
        
        # Delay between categories
        await asyncio.sleep(10)
    
    # Final summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    
    total_docs = sum(s['documents_saved'] for s in all_stats)
    total_pages = sum(s['pages_crawled'] for s in all_stats)
    total_errors = sum(s['errors'] for s in all_stats)
    
    print(f"Total categories crawled: {len(all_stats)}")
    print(f"Total pages crawled: {total_pages}")
    print(f"Total documents saved: {total_docs}")
    print(f"Total errors: {total_errors}")
    
    # Database stats
    db_stats = db.get_statistics()
    print(f"\nDatabase statistics:")
    for key, value in db_stats.items():
        print(f"  {key}: {value}")
    
    db.close()


async def run_limited_crawl(category: str, max_pages: int = 10, max_docs: int = 50):
    """Crawl limited for testing"""
    print(f"\n{'='*60}")
    print(f"LIMITED CRAWL - Testing Mode")
    print(f"Category: {category}")
    print(f"Max pages: {max_pages}")
    print(f"Max documents: {max_docs}")
    print(f"{'='*60}\n")
    
    db = DatabaseManager()
    crawler = ThuvienPhapLuatProductionCrawler(db)
    
    stats = await crawler.crawl_category_systematic(
        category_key=category,
        max_pages=max_pages,
        max_documents=max_docs
    )
    
    print("\n" + "="*60)
    print("CRAWL SUMMARY")
    print("="*60)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Database stats
    db_stats = db.get_statistics()
    print(f"\nDatabase statistics:")
    for key, value in db_stats.items():
        print(f"  {key}: {value}")
    
    db.close()
    
    return stats


async def resume_crawl(category: str):
    """Resume interrupted crawl"""
    print(f"\n{'='*60}")
    print(f"RESUMING CRAWL")
    print(f"Category: {category}")
    print(f"{'='*60}\n")
    
    db = DatabaseManager()
    crawler = ThuvienPhapLuatProductionCrawler(db)
    
    # Get progress
    progress = db.get_progress("thuvienphapluat.vn", category)
    
    if progress:
        start_page = progress['last_page'] + 1
        print(f"Resuming from page: {start_page}")
        print(f"Documents already crawled: {progress['documents_crawled']}")
    else:
        start_page = 1
        print("No previous progress found, starting from beginning")
    
    stats = await crawler.crawl_category_systematic(
        category_key=category,
        start_page=start_page,
        max_pages=None,
        max_documents=None
    )
    
    db.close()
    return stats


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Production Crawler for Vietnamese Legal Documents"
    )
    
    parser.add_argument(
        '--mode',
        choices=['full', 'limited', 'resume'],
        default='limited',
        help='Crawl mode (default: limited)'
    )
    
    parser.add_argument(
        '--category',
        default='cong-nghe-thong-tin',
        help='Category to crawl (default: cong-nghe-thong-tin)'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help='Maximum pages to crawl (limited mode, default: 10)'
    )
    
    parser.add_argument(
        '--max-docs',
        type=int,
        default=50,
        help='Maximum documents to crawl (limited mode, default: 50)'
    )
    
    args = parser.parse_args()
    
    # Run based on mode
    if args.mode == 'full':
        print("\n⚠️  WARNING: This will crawl ALL tech documents!")
        print("This may take several hours and use significant bandwidth.")
        confirm = input("\nContinue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
        asyncio.run(run_full_crawl())
    
    elif args.mode == 'limited':
        asyncio.run(run_limited_crawl(
            category=args.category,
            max_pages=args.max_pages,
            max_docs=args.max_docs
        ))
    
    elif args.mode == 'resume':
        asyncio.run(resume_crawl(category=args.category))


if __name__ == "__main__":
    main()
