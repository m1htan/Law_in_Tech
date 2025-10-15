# 📊 XEM DỮ LIỆU ĐÃ CRAWL

## Data nằm ở đâu?

### 📂 **Cấu trúc thư mục:**

```
data/
├── legal_documents.db          # Database chính (SQLite)
├── pdf_documents/              # PDF files gốc
│   ├── Tai_lieu_dinh_kem_*.pdf
│   ├── Nghi_dinh_*.pdf
│   └── ...
└── text_documents/             # Text đã convert
    ├── Tai_lieu_dinh_kem_*.txt
    ├── Nghi_dinh_*.txt
    └── ...

exports/                        # Exported files
├── tech_documents.json
├── tech_documents.csv
└── report_*.txt

logs/                          # Log files
├── vietnamese_legal_crawler.log
└── vietnamese_legal_crawler_errors.log
```

---

## 🚀 CÁCH XEM DATA (NHANH NHẤT)

### **1. Interactive Menu (Khuyến nghị):**

```bash
python3 view_data.py
```

**Menu:**
```
📊 DATA VIEWER - MENU
============================================================

1. 📊 Check data exists
2. 📚 Database summary
3. 📄 View recent documents (10)
4. 🔍 View document by ID
5. 📁 List PDF files
6. 📤 Export to JSON/CSV
0. ❌ Exit

Chọn (0-6):
```

---

## 📊 COMMAND LINE OPTIONS

### **1. Kiểm tra data có tồn tại không:**

```bash
python3 view_data.py --check
```

**Output:**
```
📊 KIỂM TRA DỮ LIỆU
============================================================
✅ Database: data/legal_documents.db
   Size: 2.45 MB
✅ PDFs: 15 files
   Total size: 12.30 MB
✅ Text files: 15 files
   Total size: 0.85 MB
```

---

### **2. Xem tóm tắt database:**

```bash
python3 view_data.py --summary
```

**Output:**
```
📚 DATABASE SUMMARY
============================================================

📊 THỐNG KÊ TỔNG QUAN:
   Total documents: 50
   Tech documents: 50
   With PDFs: 35
   Tech ratio: 100.0%

📋 THEO LOẠI VĂN BẢN:
   Nghị định: 20
   Quyết định: 15
   Thông tư: 10
   Chỉ thị: 5

📅 THEO NĂM:
   2024: 30
   2023: 15
   2022: 5

🌐 THEO WEBSITE:
   vanban.chinhphu.vn: 30
   mst.gov.vn: 20
```

---

### **3. Xem documents gần nhất:**

```bash
python3 view_data.py --recent 10
```

**Output:**
```
📄 10 DOCUMENTS GẦN NHẤT
============================================================

[1] ID: 50
    📋 Title: Quyết định về chuyển đổi số quốc gia 2024
    📂 Type: Quyết định
    📅 Date: 2024-03-15
    🌐 Source: vanban.chinhphu.vn
    📄 PDF: ✅ Yes

[2] ID: 49
    📋 Title: Nghị định triển khai AI trong giáo dục
    📂 Type: Nghị định
    📅 Date: 2024-02-28
    🌐 Source: mst.gov.vn
    📄 PDF: ✅ Yes

...
```

---

### **4. Xem chi tiết 1 document:**

```bash
python3 view_data.py --id 1
```

**Output:**
```
📄 DOCUMENT DETAIL - ID 1
============================================================

📋 TITLE:
   Nghị định 15/2024/NĐ-CP về chuyển đổi số

📊 METADATA:
   ID: 1
   Type: Nghị định
   Number: 15/2024/NĐ-CP
   Agency: Chính phủ
   Date: 2024-01-15
   Effective: 2024-03-01

🌐 SOURCE:
   Website: vanban.chinhphu.vn
   URL: https://vanban.chinhphu.vn/...

📂 FILES:
   PDF: data/pdf_documents/Nghi_dinh_15_2024.pdf
   Text: data/text_documents/Nghi_dinh_15_2024.txt

🏷️ CLASSIFICATION:
   Category: Công nghệ thông tin
   Tech-related: ✅ Yes
   Relevance: 9.50

📝 CONTENT PREVIEW (first 500 chars):
------------------------------------------------------------
CHÍNH PHỦ
-------
NGHỊ ĐỊNH 15/2024/NĐ-CP
Về chuyển đổi số quốc gia giai đoạn 2024-2030

Căn cứ Luật Tổ chức Chính phủ...
[content continues]
...

📄 PDF FILE EXISTS:
   Path: data/pdf_documents/Nghi_dinh_15_2024.pdf
   Size: 245.5 KB
   Open: open data/pdf_documents/Nghi_dinh_15_2024.pdf

📝 TEXT FILE EXISTS:
   Path: data/text_documents/Nghi_dinh_15_2024.txt
   Size: 15.2 KB
   View: cat data/text_documents/Nghi_dinh_15_2024.txt
```

---

### **5. Liệt kê PDF files:**

```bash
python3 view_data.py --pdfs
```

**Output:**
```
📄 PDF FILES
============================================================

Found 15 PDF files:

[1] Nghi_dinh_15_2024.pdf
    Size: 245.5 KB
    Path: data/pdf_documents/Nghi_dinh_15_2024.pdf

[2] Quyet_dinh_123_2024.pdf
    Size: 180.2 KB
    Path: data/pdf_documents/Quyet_dinh_123_2024.pdf

...

💡 To view a PDF:
   Mac: open data/pdf_documents/filename.pdf
   Linux: xdg-open data/pdf_documents/filename.pdf
```

---

## 📁 XEM FILES TRỰC TIẾP

### **1. Xem Database (SQLite):**

```bash
# Cài đặt sqlite3 (nếu chưa có)
# Mac: brew install sqlite
# Ubuntu: sudo apt-get install sqlite3

# Mở database
sqlite3 data/legal_documents.db
```

**Trong sqlite3:**
```sql
-- Xem tất cả documents
SELECT * FROM documents LIMIT 10;

-- Đếm documents
SELECT COUNT(*) FROM documents;

-- Xem theo website
SELECT source_website, COUNT(*) 
FROM documents 
GROUP BY source_website;

-- Thoát
.quit
```

---

### **2. Xem PDF files:**

```bash
# Mac
open data/pdf_documents/

# Linux
nautilus data/pdf_documents/

# Hoặc xem 1 file cụ thể
open data/pdf_documents/Nghi_dinh_15_2024.pdf
```

---

### **3. Xem Text files:**

```bash
# List all text files
ls -lh data/text_documents/

# Xem 1 file
cat data/text_documents/Nghi_dinh_15_2024.txt

# Xem 50 dòng đầu
head -50 data/text_documents/Nghi_dinh_15_2024.txt

# Search trong text
grep -i "công nghệ" data/text_documents/*.txt
```

---

## 📤 EXPORT DATA

### **1. Export to JSON:**

```bash
python3 tools/export_data.py --tech-only --format json
```

**Output:** `exports/tech_documents.json`

**View:**
```bash
cat exports/tech_documents.json | python3 -m json.tool | less
```

---

### **2. Export to CSV:**

```bash
python3 tools/export_data.py --tech-only --format csv
```

**Output:** `exports/tech_documents.csv`

**View in Excel/Google Sheets:**
```bash
# Mac
open exports/tech_documents.csv

# Or import vào Excel/Google Sheets
```

---

### **3. Generate Report:**

```bash
python3 tools/export_data.py --report
```

**Output:**
```
VIETNAMESE LEGAL DOCUMENTS CRAWLER
Summary Report
============================================================

BASIC STATISTICS
------------------------------------------------------------
Total Documents: 50
Tech-Related Documents: 50
Tech Ratio: 100.0%
Documents with PDFs: 35 (70.0%)

DOCUMENTS BY TYPE
------------------------------------------------------------
Nghị định: 20 (40.0%)
Quyết định: 15 (30.0%)
Thông tư: 10 (20.0%)
Chỉ thị: 5 (10.0%)

...
```

---

## 🔍 TÌM KIẾM DATA

### **Search by keyword:**

```bash
# Search trong database
sqlite3 data/legal_documents.db \
  "SELECT title, source_url FROM documents WHERE title LIKE '%công nghệ%';"
```

### **Search trong text files:**

```bash
# Search "AI"
grep -r "AI" data/text_documents/

# Search "chuyển đổi số"
grep -r "chuyển đổi số" data/text_documents/

# Search và show filename
grep -l "blockchain" data/text_documents/*.txt
```

---

## 💡 QUICK TIPS

### **Xem data nhanh nhất:**

```bash
# 1. Check có data chưa
python3 view_data.py --check

# 2. Xem summary
python3 view_data.py --summary

# 3. Xem 5 documents mới nhất
python3 view_data.py --recent 5

# 4. Export to JSON
python3 tools/export_data.py --tech-only --format json

# 5. Mở JSON file
cat exports/tech_documents.json | python3 -m json.tool
```

---

### **Nếu chưa có data:**

```bash
# Crawl 10 documents để test
python3 run_government_crawl.py --max-docs 10

# Đợi 5 phút, sau đó:
python3 view_data.py --summary
```

---

## 📊 DATA LOCATIONS SUMMARY

| Data Type | Location | View Command |
|-----------|----------|--------------|
| **Database** | `data/legal_documents.db` | `python3 view_data.py --summary` |
| **PDFs** | `data/pdf_documents/` | `python3 view_data.py --pdfs` |
| **Text files** | `data/text_documents/` | `ls data/text_documents/` |
| **JSON export** | `exports/tech_documents.json` | `cat exports/tech_documents.json` |
| **CSV export** | `exports/tech_documents.csv` | `open exports/tech_documents.csv` |
| **Reports** | `exports/report_*.txt` | `cat exports/report_*.txt` |
| **Logs** | `logs/*.log` | `tail -f logs/vietnamese_legal_crawler.log` |

---

## 🎯 EXAMPLE WORKFLOW

```bash
# 1. Crawl data
python3 run_government_crawl.py --max-docs 10

# 2. Check data
python3 view_data.py --check

# 3. View summary
python3 view_data.py --summary

# 4. View recent documents
python3 view_data.py --recent 10

# 5. View specific document
python3 view_data.py --id 1

# 6. Export to JSON
python3 tools/export_data.py --tech-only --format json

# 7. View JSON
cat exports/tech_documents.json | python3 -m json.tool | less

# 8. Open PDFs folder
open data/pdf_documents/
```

---

## ✅ SUMMARY

**Data được lưu ở:**
- ✅ `data/legal_documents.db` - Database
- ✅ `data/pdf_documents/` - PDF files
- ✅ `data/text_documents/` - Text files
- ✅ `exports/` - Exported JSON/CSV

**Xem data:**
- ✅ `python3 view_data.py` - Interactive menu
- ✅ `python3 view_data.py --summary` - Quick summary
- ✅ `python3 tools/export_data.py --report` - Full report
- ✅ `open data/pdf_documents/` - Browse PDFs

**Easy!** 🎉
