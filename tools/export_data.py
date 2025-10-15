"""
Export tools for crawled legal documents
Export to JSON, CSV, Excel formats
"""
import json
import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.database.models import DatabaseManager, LegalDocument
from src.config import Config
from src.utils.logger import log


class DataExporter:
    """Export crawled data to various formats"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize exporter"""
        self.db = db_manager or DatabaseManager()
        self.export_dir = Config.BASE_DIR / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_json(
        self,
        documents: List[LegalDocument],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export documents to JSON
        
        Args:
            documents: List of documents
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"legal_docs_{timestamp}.json"
        
        filepath = self.export_dir / filename
        
        # Convert to dict
        data = []
        for doc in documents:
            doc_dict = {
                'id': doc.id,
                'title': doc.title,
                'document_number': doc.document_number,
                'document_type': doc.document_type,
                'issuing_agency': doc.issuing_agency,
                'issued_date': doc.issued_date,
                'effective_date': doc.effective_date,
                'summary': doc.summary,
                'source_url': doc.source_url,
                'category': doc.category,
                'is_tech_related': doc.is_tech_related,
                'relevance_score': doc.relevance_score,
                'status': doc.status
            }
            data.append(doc_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        log.info(f"Exported {len(documents)} documents to JSON: {filepath}")
        return filepath
    
    def export_to_csv(
        self,
        documents: List[LegalDocument],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export documents to CSV
        
        Args:
            documents: List of documents
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"legal_docs_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        # Define fields
        fields = [
            'id', 'title', 'document_number', 'document_type',
            'issuing_agency', 'issued_date', 'effective_date',
            'summary', 'source_url', 'category',
            'is_tech_related', 'relevance_score', 'status'
        ]
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for doc in documents:
                row = {field: getattr(doc, field, '') for field in fields}
                writer.writerow(row)
        
        log.info(f"Exported {len(documents)} documents to CSV: {filepath}")
        return filepath
    
    def export_tech_documents(self, format: str = 'json') -> Path:
        """
        Export all tech-related documents
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Path to exported file
        """
        log.info("Fetching tech documents from database...")
        documents = self.db.get_tech_documents()
        
        if format == 'json':
            return self.export_to_json(documents, "tech_documents.json")
        elif format == 'csv':
            return self.export_to_csv(documents, "tech_documents.csv")
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def generate_summary_report(self) -> str:
        """
        Generate summary report
        
        Returns:
            Report text
        """
        stats = self.db.get_statistics()
        
        report = f"""
VIETNAMESE LEGAL DOCUMENTS CRAWLER
Summary Report
{'='*60}

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

OVERALL STATISTICS
{'-'*60}
Total Documents: {stats.get('total_documents', 0)}
Tech Documents: {stats.get('tech_documents', 0)}
Tech Ratio: {stats.get('tech_documents', 0) / max(stats.get('total_documents', 1), 1) * 100:.1f}%

DOCUMENTS BY TYPE
{'-'*60}
"""
        
        for doc_type, count in stats.get('by_type', {}).items():
            report += f"{doc_type or 'Unknown'}: {count}\n"
        
        report += f"""
DOCUMENTS BY YEAR
{'-'*60}
"""
        
        for year, count in sorted(stats.get('by_year', {}).items(), reverse=True):
            report += f"{year or 'Unknown'}: {count}\n"
        
        report += f"""
{'='*60}
Export Directory: {self.export_dir}
{'='*60}
"""
        
        return report


def main():
    """Main export function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export crawled legal documents"
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
        help='Export only tech-related documents'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate summary report'
    )
    
    args = parser.parse_args()
    
    exporter = DataExporter()
    
    if args.report:
        report = exporter.generate_summary_report()
        print(report)
        
        # Save report
        report_file = exporter.export_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {report_file}")
    
    if args.tech_only:
        print("\nExporting tech documents...")
        
        if args.format == 'both':
            exporter.export_tech_documents('json')
            exporter.export_tech_documents('csv')
        else:
            filepath = exporter.export_tech_documents(args.format)
            print(f"Exported to: {filepath}")
    
    print("\nExport complete!")


if __name__ == "__main__":
    main()
