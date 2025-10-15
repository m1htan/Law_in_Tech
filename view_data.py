"""
VIEW CRAWLED DATA - Xem dữ liệu đã crawl
"""
import os
import sys
from pathlib import Path
from src.database.models import DatabaseManager
from src.config import Config


def check_data_exists():
    """Kiểm tra data có tồn tại không"""
    print("\n" + "="*60)
    print("📊 KIỂM TRA DỮ LIỆU")
    print("="*60)
    
    # Check database
    db_path = Path("data/legal_documents.db")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"✅ Database: {db_path}")
        print(f"   Size: {size_mb:.2f} MB")
    else:
        print(f"❌ Database: CHƯA CÓ (Bạn chưa crawl)")
        return False
    
    # Check PDF folder
    pdf_dir = Path("data/pdf_documents")
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"✅ PDFs: {len(pdf_files)} files")
        if pdf_files:
            total_size = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
            print(f"   Total size: {total_size:.2f} MB")
    else:
        print(f"⚠️  PDFs: Folder chưa có")
    
    # Check Text folder
    text_dir = Path("data/text_documents")
    if text_dir.exists():
        text_files = list(text_dir.glob("*.txt"))
        print(f"✅ Text files: {len(text_files)} files")
        if text_files:
            total_size = sum(f.stat().st_size for f in text_files) / (1024 * 1024)
            print(f"   Total size: {total_size:.2f} MB")
    else:
        print(f"⚠️  Text files: Folder chưa có")
    
    return True


def view_database_summary():
    """Xem tóm tắt database"""
    print("\n" + "="*60)
    print("📚 DATABASE SUMMARY")
    print("="*60)
    
    try:
        db = DatabaseManager()
        stats = db.get_statistics()
        
        print(f"\n📊 THỐNG KÊ TỔNG QUAN:")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Tech documents: {stats.get('tech_documents', 0)}")
        print(f"   With PDFs: {stats.get('with_pdfs', 0)}")
        print(f"   Tech ratio: {stats.get('tech_ratio', 0):.1f}%")
        
        if stats.get('by_type'):
            print(f"\n📋 THEO LOẠI VĂN BẢN:")
            for doc_type, count in stats['by_type'].items():
                print(f"   {doc_type}: {count}")
        
        if stats.get('by_year'):
            print(f"\n📅 THEO NĂM:")
            for year, count in sorted(stats['by_year'].items(), reverse=True):
                print(f"   {year}: {count}")
        
        if stats.get('by_website'):
            print(f"\n🌐 THEO WEBSITE:")
            for website, count in stats['by_website'].items():
                print(f"   {website}: {count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Database có thể chưa có hoặc bị lỗi")
        return False


def view_recent_documents(limit=10):
    """Xem documents gần đây nhất"""
    print("\n" + "="*60)
    print(f"📄 {limit} DOCUMENTS GẦN NHẤT")
    print("="*60)
    
    try:
        db = DatabaseManager()
        conn = db.conn
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, title, document_type, issued_date, source_website, pdf_path
            FROM documents
            ORDER BY id DESC
            LIMIT {limit}
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("\n❌ Chưa có documents nào!")
            print("   Hãy chạy: python3 run_government_crawl.py --max-docs 10")
            db.close()
            return False
        
        for idx, row in enumerate(rows, 1):
            doc_id, title, doc_type, issued_date, website, pdf_path = row
            
            print(f"\n[{idx}] ID: {doc_id}")
            print(f"    📋 Title: {title[:80]}")
            print(f"    📂 Type: {doc_type or 'N/A'}")
            print(f"    📅 Date: {issued_date or 'N/A'}")
            print(f"    🌐 Source: {website}")
            print(f"    📄 PDF: {'✅ Yes' if pdf_path else '❌ No'}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def view_document_detail(doc_id):
    """Xem chi tiết 1 document"""
    print("\n" + "="*60)
    print(f"📄 DOCUMENT DETAIL - ID {doc_id}")
    print("="*60)
    
    try:
        db = DatabaseManager()
        conn = db.conn
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents WHERE id = ?
        """, (doc_id,))
        
        row = cursor.fetchone()
        
        if not row:
            print(f"\n❌ Document ID {doc_id} không tồn tại!")
            db.close()
            return False
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        doc = dict(zip(columns, row))
        
        # Display
        print(f"\n📋 TITLE:")
        print(f"   {doc.get('title', 'N/A')}")
        
        print(f"\n📊 METADATA:")
        print(f"   ID: {doc.get('id')}")
        print(f"   Type: {doc.get('document_type', 'N/A')}")
        print(f"   Number: {doc.get('document_number', 'N/A')}")
        print(f"   Agency: {doc.get('issuing_agency', 'N/A')}")
        print(f"   Date: {doc.get('issued_date', 'N/A')}")
        print(f"   Effective: {doc.get('effective_date', 'N/A')}")
        
        print(f"\n🌐 SOURCE:")
        print(f"   Website: {doc.get('source_website', 'N/A')}")
        print(f"   URL: {doc.get('source_url', 'N/A')[:80]}")
        
        print(f"\n📂 FILES:")
        print(f"   PDF: {doc.get('pdf_path', 'N/A')}")
        print(f"   Text: {doc.get('text_path', 'N/A')}")
        
        print(f"\n🏷️ CLASSIFICATION:")
        print(f"   Category: {doc.get('category', 'N/A')}")
        print(f"   Tech-related: {'✅ Yes' if doc.get('is_tech_related') else '❌ No'}")
        print(f"   Relevance: {doc.get('relevance_score', 0):.2f}")
        
        # Show content preview
        full_text = doc.get('full_text', '')
        if full_text:
            print(f"\n📝 CONTENT PREVIEW (first 500 chars):")
            print("-" * 60)
            print(full_text[:500])
            if len(full_text) > 500:
                print(f"\n... ({len(full_text) - 500} more characters)")
        
        # Check if files exist
        pdf_path = doc.get('pdf_path')
        if pdf_path:
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                size_kb = pdf_file.stat().st_size / 1024
                print(f"\n📄 PDF FILE EXISTS:")
                print(f"   Path: {pdf_path}")
                print(f"   Size: {size_kb:.1f} KB")
                print(f"   Open: open {pdf_path}")
            else:
                print(f"\n⚠️  PDF file not found: {pdf_path}")
        
        text_path = doc.get('text_path')
        if text_path:
            text_file = Path(text_path)
            if text_file.exists():
                size_kb = text_file.stat().st_size / 1024
                print(f"\n📝 TEXT FILE EXISTS:")
                print(f"   Path: {text_path}")
                print(f"   Size: {size_kb:.1f} KB")
                print(f"   View: cat {text_path}")
            else:
                print(f"\n⚠️  Text file not found: {text_path}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_pdf_files():
    """Liệt kê tất cả PDF files"""
    print("\n" + "="*60)
    print("📄 PDF FILES")
    print("="*60)
    
    pdf_dir = Path("data/pdf_documents")
    if not pdf_dir.exists():
        print("\n❌ Folder data/pdf_documents chưa tồn tại!")
        return False
    
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ Chưa có PDF files nào!")
        return False
    
    print(f"\nFound {len(pdf_files)} PDF files:\n")
    
    for idx, pdf_file in enumerate(pdf_files[:20], 1):  # Show first 20
        size_kb = pdf_file.stat().st_size / 1024
        print(f"[{idx}] {pdf_file.name}")
        print(f"    Size: {size_kb:.1f} KB")
        print(f"    Path: {pdf_file}")
    
    if len(pdf_files) > 20:
        print(f"\n... and {len(pdf_files) - 20} more files")
    
    print(f"\n💡 To view a PDF:")
    print(f"   Mac: open data/pdf_documents/filename.pdf")
    print(f"   Linux: xdg-open data/pdf_documents/filename.pdf")
    
    return True


def interactive_menu():
    """Interactive menu để xem data"""
    while True:
        print("\n" + "="*60)
        print("📊 DATA VIEWER - MENU")
        print("="*60)
        print("\n1. 📊 Check data exists")
        print("2. 📚 Database summary")
        print("3. 📄 View recent documents (10)")
        print("4. 🔍 View document by ID")
        print("5. 📁 List PDF files")
        print("6. 📤 Export to JSON/CSV")
        print("0. ❌ Exit")
        
        choice = input("\nChọn (0-6): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            check_data_exists()
        elif choice == "2":
            view_database_summary()
        elif choice == "3":
            view_recent_documents(limit=10)
        elif choice == "4":
            doc_id = input("Enter document ID: ").strip()
            if doc_id.isdigit():
                view_document_detail(int(doc_id))
            else:
                print("❌ Invalid ID!")
        elif choice == "5":
            list_pdf_files()
        elif choice == "6":
            print("\n📤 Export data:")
            print("   python3 tools/export_data.py --tech-only --format json")
            print("   python3 tools/export_data.py --tech-only --format csv")
            print("   python3 tools/export_data.py --report")
        else:
            print("❌ Invalid choice!")
        
        input("\nPress Enter to continue...")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View crawled data")
    parser.add_argument('--check', action='store_true', help='Check data exists')
    parser.add_argument('--summary', action='store_true', help='Show summary')
    parser.add_argument('--recent', type=int, metavar='N', help='Show N recent docs')
    parser.add_argument('--id', type=int, metavar='ID', help='View document by ID')
    parser.add_argument('--pdfs', action='store_true', help='List PDF files')
    parser.add_argument('--menu', action='store_true', help='Interactive menu')
    
    args = parser.parse_args()
    
    # If no args, show menu
    if len(sys.argv) == 1:
        interactive_menu()
        return
    
    if args.check:
        check_data_exists()
    
    if args.summary:
        view_database_summary()
    
    if args.recent:
        view_recent_documents(limit=args.recent)
    
    if args.id:
        view_document_detail(args.id)
    
    if args.pdfs:
        list_pdf_files()
    
    if args.menu:
        interactive_menu()


if __name__ == "__main__":
    main()
