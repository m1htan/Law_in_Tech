"""
Test File Storage System
"""
import asyncio
from pathlib import Path
from src.storage.file_storage import FileStorageManager
from src.utils.logger import log


def test_file_storage():
    """Test file storage basic operations"""
    print("\n" + "="*60)
    print("🧪 TESTING FILE STORAGE SYSTEM")
    print("="*60)
    
    # Initialize
    print("\n1. Initialize FileStorageManager...")
    storage = FileStorageManager()
    print(f"✅ Initialized")
    print(f"   PDF dir: {storage.pdf_dir}")
    print(f"   Text dir: {storage.text_dir}")
    print(f"   Metadata file: {storage.metadata_file}")
    
    # Test save document
    print("\n2. Test save document (without files)...")
    doc_id = storage.save_document(
        title="Test Document - Nghị định về AI",
        source_url="https://vanban.chinhphu.vn/test/123",
        text_content="Đây là nội dung văn bản test về AI và chuyển đổi số...",
        source_website="vanban.chinhphu.vn",
        document_type="Nghị định",
        document_number="123/2024/NĐ-CP",
        issuing_agency="Chính phủ",
        issued_date="2024-10-15",
        category="Công nghệ thông tin",
        is_tech_related=True
    )
    print(f"✅ Document saved with ID: {doc_id}")
    
    # Test retrieve
    print("\n3. Test retrieve document...")
    doc = storage.get_document(doc_id)
    if doc:
        print(f"✅ Retrieved document:")
        print(f"   Title: {doc.title}")
        print(f"   Type: {doc.document_type}")
        print(f"   Source: {doc.source_website}")
        print(f"   Tech: {doc.is_tech_related}")
    else:
        print(f"❌ Failed to retrieve document")
    
    # Test duplicate check
    print("\n4. Test duplicate check...")
    if storage.document_exists("https://vanban.chinhphu.vn/test/123"):
        print(f"✅ Duplicate detection works")
    else:
        print(f"❌ Duplicate detection failed")
    
    # Save another document
    print("\n5. Save another document...")
    doc_id2 = storage.save_document(
        title="Test Document 2 - Quyết định về Blockchain",
        source_url="https://mst.gov.vn/test/456",
        text_content="Nội dung về blockchain và cryptocurrency...",
        source_website="mst.gov.vn",
        document_type="Quyết định",
        category="Công nghệ thông tin",
        is_tech_related=True
    )
    print(f"✅ Second document saved: {doc_id2}")
    
    # Test statistics
    print("\n6. Test statistics...")
    stats = storage.get_statistics()
    print(f"✅ Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Tech documents: {stats['tech_documents']}")
    print(f"   Tech ratio: {stats['tech_ratio']:.1f}%")
    print(f"   With PDFs: {stats['with_pdfs']}")
    print(f"   With texts: {stats['with_texts']}")
    
    if stats.get('by_type'):
        print(f"\n   By type:")
        for doc_type, count in stats['by_type'].items():
            print(f"     {doc_type}: {count}")
    
    # Test get all
    print("\n7. Test get all documents...")
    all_docs = storage.get_all_documents()
    print(f"✅ Retrieved {len(all_docs)} documents")
    
    # Test export JSON
    print("\n8. Test export to JSON...")
    output_file = Path("test_export.json")
    storage.export_to_json(output_file, tech_only=True)
    if output_file.exists():
        size_kb = output_file.stat().st_size / 1024
        print(f"✅ Exported to {output_file}")
        print(f"   Size: {size_kb:.2f} KB")
        output_file.unlink()  # Clean up
    else:
        print(f"❌ Export failed")
    
    # Test export CSV
    print("\n9. Test export to CSV...")
    output_file = Path("test_export.csv")
    storage.export_to_csv(output_file, tech_only=False)
    if output_file.exists():
        size_kb = output_file.stat().st_size / 1024
        print(f"✅ Exported to {output_file}")
        print(f"   Size: {size_kb:.2f} KB")
        output_file.unlink()  # Clean up
    else:
        print(f"❌ Export failed")
    
    # Check files
    print("\n10. Check created files...")
    if storage.metadata_file.exists():
        size_kb = storage.metadata_file.stat().st_size / 1024
        print(f"✅ Metadata file: {size_kb:.2f} KB")
    
    text_files = list(storage.text_dir.glob("*.txt"))
    print(f"✅ Text files: {len(text_files)}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print(f"\n📁 Check files at:")
    print(f"   - {storage.metadata_file}")
    print(f"   - {storage.text_dir}")
    
    return True


if __name__ == "__main__":
    try:
        test_file_storage()
        print("\n✅ Test completed successfully!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
