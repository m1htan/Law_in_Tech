"""
Export Data Tool - Export từ file storage (NO DATABASE)
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.file_storage import FileStorageManager
from src.utils.logger import log


def export_json(storage: FileStorageManager, tech_only: bool = False, output_dir: str = "exports"):
    """Export to JSON"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = "tech_documents.json" if tech_only else "all_documents.json"
    output_file = output_path / filename
    
    storage.export_to_json(output_file, tech_only=tech_only)
    
    print(f"\n✅ Exported to: {output_file}")
    
    # Show size
    if output_file.exists():
        size_kb = output_file.stat().st_size / 1024
        print(f"   Size: {size_kb:.2f} KB")


def export_csv(storage: FileStorageManager, tech_only: bool = False, output_dir: str = "exports"):
    """Export to CSV"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = "tech_documents.csv" if tech_only else "all_documents.csv"
    output_file = output_path / filename
    
    storage.export_to_csv(output_file, tech_only=tech_only)
    
    print(f"\n✅ Exported to: {output_file}")
    
    # Show size
    if output_file.exists():
        size_kb = output_file.stat().st_size / 1024
        print(f"   Size: {size_kb:.2f} KB")


def generate_report(storage: FileStorageManager, output_dir: str = "exports"):
    """Generate summary report"""
    stats = storage.get_statistics()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"report_{timestamp}.txt"
    
    # Generate report content
    lines = []
    lines.append("=" * 60)
    lines.append("VIETNAMESE LEGAL DOCUMENTS CRAWLER")
    lines.append("Summary Report")
    lines.append("=" * 60)
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    lines.append("\n\nBASIC STATISTICS")
    lines.append("-" * 60)
    lines.append(f"Total Documents: {stats['total_documents']}")
    lines.append(f"Tech-Related Documents: {stats['tech_documents']}")
    lines.append(f"Tech Ratio: {stats['tech_ratio']:.1f}%")
    lines.append(f"Documents with PDFs: {stats['with_pdfs']} ({stats['with_pdfs']/stats['total_documents']*100:.1f}%)" if stats['total_documents'] > 0 else "Documents with PDFs: 0")
    lines.append(f"Documents with Texts: {stats['with_texts']} ({stats['with_texts']/stats['total_documents']*100:.1f}%)" if stats['total_documents'] > 0 else "Documents with Texts: 0")
    
    if stats.get('by_type'):
        lines.append("\n\nDOCUMENTS BY TYPE")
        lines.append("-" * 60)
        for doc_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
            lines.append(f"{doc_type}: {count} ({percentage:.1f}%)")
    
    if stats.get('by_year'):
        lines.append("\n\nDOCUMENTS BY YEAR")
        lines.append("-" * 60)
        for year, count in sorted(stats['by_year'].items(), reverse=True):
            percentage = (count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
            lines.append(f"{year}: {count} ({percentage:.1f}%)")
    
    if stats.get('by_website'):
        lines.append("\n\nDOCUMENTS BY SOURCE WEBSITE")
        lines.append("-" * 60)
        for website, count in sorted(stats['by_website'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
            lines.append(f"{website}: {count} ({percentage:.1f}%)")
    
    lines.append("\n" + "=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)
    
    # Write report
    report_content = "\n".join(lines)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # Also print to console
    print("\n" + report_content)
    
    print(f"\n✅ Report saved to: {report_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Export crawled data to JSON/CSV or generate reports"
    )
    
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Export format (default: json)'
    )
    
    parser.add_argument(
        '--tech-only',
        action='store_true',
        help='Only export tech-related documents'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate summary report'
    )
    
    parser.add_argument(
        '--output-dir',
        default='exports',
        help='Output directory (default: exports)'
    )
    
    args = parser.parse_args()
    
    # Load storage
    try:
        storage = FileStorageManager()
    except Exception as e:
        print(f"❌ Error loading storage: {e}")
        print(f"   Make sure you have crawled data first!")
        return
    
    # Check if has data
    stats = storage.get_statistics()
    if stats['total_documents'] == 0:
        print("\n❌ No documents found!")
        print("   Run crawler first: python3 run_government_crawl.py --max-docs 10")
        return
    
    print("\n" + "=" * 60)
    print("📤 EXPORT DATA TOOL")
    print("=" * 60)
    print(f"Total documents: {stats['total_documents']}")
    print(f"Tech documents: {stats['tech_documents']}")
    print(f"Export format: {args.format}")
    print(f"Tech only: {args.tech_only}")
    print("=" * 60)
    
    # Export
    if args.report:
        generate_report(storage, args.output_dir)
    
    elif args.format == 'json':
        export_json(storage, args.tech_only, args.output_dir)
    
    elif args.format == 'csv':
        export_csv(storage, args.tech_only, args.output_dir)
    
    elif args.format == 'both':
        export_json(storage, args.tech_only, args.output_dir)
        export_csv(storage, args.tech_only, args.output_dir)
    
    print("\n✅ Export completed!")


if __name__ == "__main__":
    main()
