"""Tests for text processing utilities"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.text_processing import (
    normalize_vietnamese_text,
    extract_document_number,
    extract_date,
    generate_doc_id,
    contains_keywords,
    clean_html_text
)


def test_normalize_vietnamese_text():
    """Test Vietnamese text normalization"""
    text = "  Nghị   định   về   chuyển đổi số  "
    result = normalize_vietnamese_text(text)
    assert result == "Nghị định về chuyển đổi số"
    print("✓ test_normalize_vietnamese_text passed")


def test_extract_document_number():
    """Test document number extraction"""
    
    # Test pattern 1
    text1 = "Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu"
    result1 = extract_document_number(text1)
    assert result1 == "13/2023/NĐ-CP"
    print(f"✓ Extracted: {result1}")
    
    # Test pattern 2
    text2 = "Luật 24/2023/QH15"
    result2 = extract_document_number(text2)
    assert result2 == "24/2023/QH15"
    print(f"✓ Extracted: {result2}")
    
    print("✓ test_extract_document_number passed")


def test_extract_date():
    """Test date extraction"""
    
    # Test dd/mm/yyyy
    text1 = "Ngày ban hành: 17/06/2023"
    result1 = extract_date(text1)
    assert result1 == "2023-06-17"
    print(f"✓ Extracted date: {result1}")
    
    # Test Vietnamese format
    text2 = "ngày 25 tháng 12 năm 2024"
    result2 = extract_date(text2)
    assert result2 == "2024-12-25"
    print(f"✓ Extracted date: {result2}")
    
    print("✓ test_extract_date passed")


def test_generate_doc_id():
    """Test document ID generation"""
    doc_id = generate_doc_id(
        source="vanban_chinhphu",
        doc_type="Nghị định",
        doc_number="13/2023/NĐ-CP",
        issue_date="2023-06-17"
    )
    
    assert doc_id.startswith("vanban_chinhphu_")
    assert len(doc_id) > 10
    print(f"✓ Generated doc_id: {doc_id}")
    print("✓ test_generate_doc_id passed")


def test_contains_keywords():
    """Test keyword matching"""
    
    text = "Nghị định về bảo vệ dữ liệu cá nhân và an ninh mạng"
    keywords = ["dữ liệu cá nhân", "AI", "blockchain", "an ninh mạng"]
    
    # Should match at least 2 keywords
    result = contains_keywords(text, keywords, threshold=2)
    assert result == True
    print(f"✓ Found keywords in text")
    
    # Should not match with high threshold
    result2 = contains_keywords(text, keywords, threshold=10)
    assert result2 == False
    print(f"✓ Correctly rejected with high threshold")
    
    print("✓ test_contains_keywords passed")


def test_clean_html_text():
    """Test HTML cleaning"""
    html = "<p>Nghị định&nbsp;về&nbsp;<strong>bảo vệ dữ liệu</strong></p>"
    result = clean_html_text(html)
    assert "<p>" not in result
    assert "&nbsp;" not in result
    assert "Nghị định" in result
    print(f"✓ Cleaned HTML: {result}")
    print("✓ test_clean_html_text passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("RUNNING TEXT PROCESSING TESTS")
    print("=" * 60)
    
    try:
        test_normalize_vietnamese_text()
        test_extract_document_number()
        test_extract_date()
        test_generate_doc_id()
        test_contains_keywords()
        test_clean_html_text()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"✗ Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
