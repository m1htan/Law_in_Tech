"""
VIEW CRAWLED DATA - Xem dữ liệu đã crawl (File-based, NO DATABASE)
"""
import os
import sys
from pathlib import Path
from src.storage.file_storage import FileStorageManager
from src.config import Config


def check_data_exists():
    """Kiểm tra data có tồn tại không"""
    print("\n" + "="*60)
    print("📊 KIỂM TRA DỮ LIỆU")
    print("="*60)
    
    # Check metadata
    metadata_path = Path("data/metadata.json")
    if metadata_path.exists():
        size_kb = metadata_path.stat().st_size / 1024
        print(f"✅ Metadata: {metadata_path}")
        print(f"   Size: {size_kb:.2f} KB")
    else:
        print(f"❌ Metadata: CHƯA CÓ (Bạn chưa crawl)")
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


def view_storage_summary():
    """Xem tóm tắt storage"""
    print("\n" + "="*60)
    print("📚 STORAGE SUMMARY")
    print("="*60)
    
    try:
        storage = FileStorageManager()
        stats = storage.get_statistics()
        
        print(f"\n📊 THỐNG KÊ TỔNG QUAN:")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Tech documents: {stats.get('tech_documents', 0)}")
        print(f"   With PDFs: {stats.get('with_pdfs', 0)}")
        print(f"   With texts: {stats.get('with_texts', 0)}")
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Metadata có thể chưa có hoặc bị lỗi")
        return False


def view_recent_documents(limit=10):
    """Xem documents gần đây nhất"""
    print("\n" + "="*60)
    print(f"📄 {limit} DOCUMENTS GẦN NHẤT")
    print("="*60)
    
    try:
        storage = FileStorageManager()
        docs = storage.get_all_documents()
        
        if not docs:
            print("\n❌ Chưa có documents nào!")
            print("   Hãy chạy: python3 run_government_crawl.py --max-docs 10")
            return False
        
        # Sort by crawled_at (newest first)
        docs.sort(key=lambda d: d.crawled_at, reverse=True)
        
        for idx, doc in enumerate(docs[:limit], 1):
            print(f"\n[{idx}] ID: {doc.id}")
            print(f"    📋 Title: {doc.title[:80]}")
            print(f"    📂 Type: {doc.document_type or 'N/A'}")
            print(f"    📅 Date: {doc.issued_date or 'N/A'}")
            print(f"    🌐 Source: {doc.source_website}")
            print(f"    📄 PDF: {'✅ Yes' if doc.pdf_filename else '❌ No'}")
            print(f"    📝 Text: {'✅ Yes' if doc.text_filename else '❌ No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def view_document_detail(doc_id):
    """Xem chi tiết 1 document"""
    print("\n" + "="*60)
    print(f"📄 DOCUMENT DETAIL - ID: {doc_id}")
    print("="*60)
    
    try:
        storage = FileStorageManager()
        doc = storage.get_document(doc_id)
        
        if not doc:
            print(f"\n❌ Document ID '{doc_id}' không tồn tại!")
            return False
        
        # Display
        print(f"\n📋 TITLE:")
        print(f"   {doc.title}")
        
        print(f"\n📊 METADATA:")
        print(f"   ID: {doc.id}")
        print(f"   Type: {doc.document_type or 'N/A'}")
        print(f"   Number: {doc.document_number or 'N/A'}")
        print(f"   Agency: {doc.issuing_agency or 'N/A'}")
        print(f"   Date: {doc.issued_date or 'N/A'}")
        print(f"   Effective: {doc.effective_date or 'N/A'}")
        
        print(f"\n🌐 SOURCE:")
        print(f"   Website: {doc.source_website or 'N/A'}")
        print(f"   URL: {doc.source_url[:80]}")
        
        print(f"\n📂 FILES:")
        print(f"   PDF: {doc.pdf_filename or 'N/A'}")
        print(f"   Text: {doc.text_filename or 'N/A'}")
        
        print(f"\n🏷️ CLASSIFICATION:")
        print(f"   Category: {doc.category or 'N/A'}")
        print(f"   Tech-related: {'✅ Yes' if doc.is_tech_related else '❌ No'}")
        print(f"   Relevance: {doc.relevance_score:.2f}")
        
        # Check if files exist
        if doc.pdf_filename:
            pdf_file = Path("data/pdf_documents") / doc.pdf_filename
            if pdf_file.exists():
                size_kb = pdf_file.stat().st_size / 1024
                print(f"\n📄 PDF FILE EXISTS:")
                print(f"   Path: {pdf_file}")
                print(f"   Size: {size_kb:.1f} KB")
                print(f"   Open: open {pdf_file}")
            else:
                print(f"\n⚠️  PDF file not found: {pdf_file}")
        
        if doc.text_filename:
            text_file = Path("data/text_documents") / doc.text_filename
            if text_file.exists():
                size_kb = text_file.stat().st_size / 1024
                print(f"\n📝 TEXT FILE EXISTS:")
                print(f"   Path: {text_file}")
                print(f"   Size: {size_kb:.1f} KB")
                print(f"   View: cat {text_file}")
                
                # Show preview
                print(f"\n📝 TEXT PREVIEW (first 500 chars):")
                print("-" * 60)
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(content[:500])
                    if len(content) > 500:
                        print(f"\n... ({len(content) - 500} more characters)")
            else:
                print(f"\n⚠️  Text file not found: {text_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
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
    
    if len(pdf_files) > 20:
        print(f"\n... and {len(pdf_files) - 20} more files")
    
    print(f"\n💡 To view a PDF:")
    print(f"   Mac: open data/pdf_documents/filename.pdf")
    print(f"   Linux: xdg-open data/pdf_documents/filename.pdf")
    
    return True


def list_text_files():
    """Liệt kê tất cả text files"""
    print("\n" + "="*60)
    print("📝 TEXT FILES")
    print("="*60)
    
    text_dir = Path("data/text_documents")
    if not text_dir.exists():
        print("\n❌ Folder data/text_documents chưa tồn tại!")
        return False
    
    text_files = sorted(text_dir.glob("*.txt"))
    
    if not text_files:
        print("\n❌ Chưa có text files nào!")
        return False
    
    print(f"\nFound {len(text_files)} text files:\n")
    
    for idx, text_file in enumerate(text_files[:20], 1):  # Show first 20
        size_kb = text_file.stat().st_size / 1024
        print(f"[{idx}] {text_file.name}")
        print(f"    Size: {size_kb:.1f} KB")
    
    if len(text_files) > 20:
        print(f"\n... and {len(text_files) - 20} more files")
    
    print(f"\n💡 To view a text file:")
    print(f"   cat data/text_documents/filename.txt")
    print(f"   head -50 data/text_documents/filename.txt")
    
    return True


def interactive_menu():
    """Interactive menu để xem data"""
    while True:
        print("\n" + "="*60)
        print("📊 DATA VIEWER - MENU")
        print("="*60)
        print("\n1. 📊 Check data exists")
        print("2. 📚 Storage summary")
        print("3. 📄 View recent documents (10)")
        print("4. 🔍 View document by ID")
        print("5. 📁 List PDF files")
        print("6. 📝 List text files")
        print("7. 📤 Export to JSON/CSV")
        print("0. ❌ Exit")
        
        choice = input("\nChọn (0-7): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            check_data_exists()
        elif choice == "2":
            view_storage_summary()
        elif choice == "3":
            view_recent_documents(limit=10)
        elif choice == "4":
            doc_id = input("Enter document ID: ").strip()
            if doc_id:
                view_document_detail(doc_id)
            else:
                print("❌ Invalid ID!")
        elif choice == "5":
            list_pdf_files()
        elif choice == "6":
            list_text_files()
        elif choice == "7":
            print("\n📤 Export data:")
            print("   python3 tools/export_data.py --format json")
            print("   python3 tools/export_data.py --format csv")
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
    parser.add_argument('--id', type=str, metavar='ID', help='View document by ID')
    parser.add_argument('--pdfs', action='store_true', help='List PDF files')
    parser.add_argument('--texts', action='store_true', help='List text files')
    parser.add_argument('--menu', action='store_true', help='Interactive menu')
    
    args = parser.parse_args()
    
    # If no args, show menu
    if len(sys.argv) == 1:
        interactive_menu()
        return
    
    if args.check:
        check_data_exists()
    
    if args.summary:
        view_storage_summary()
    
    if args.recent:
        view_recent_documents(limit=args.recent)
    
    if args.id:
        view_document_detail(args.id)
    
    if args.pdfs:
        list_pdf_files()
    
    if args.texts:
        list_text_files()
    
    if args.menu:
        interactive_menu()


if __name__ == "__main__":
    main()
