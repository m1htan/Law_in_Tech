# 📁 FILE STORAGE - Lưu trữ trong folders (NO DATABASE)

## ✅ THAY ĐỔI MỚI: KHÔNG DÙNG DATABASE

**TRƯỚC:**
- ❌ SQLite database
- ❌ Phức tạp
- ❌ Khó truy cập

**SAU:**
- ✅ Chỉ folders + files
- ✅ Đơn giản
- ✅ Dễ truy cập
- ✅ 1 file `metadata.json` chứa tất cả thông tin

---

## 📂 CẤU TRÚC MỚI

```
data/
├── metadata.json               # Tất cả thông tin documents
├── pdf_documents/              # PDFs gốc từ .gov.vn
│   ├── Nghi_dinh_15_2024_abc123.pdf
│   ├── Quyet_dinh_456_def456.pdf
│   └── ...
└── text_documents/             # Text đã convert
    ├── Nghi_dinh_15_2024_abc123.txt
    ├── Quyet_dinh_456_def456.txt
    └── ...

exports/                        # Exported files
├── tech_documents.json
├── tech_documents.csv
└── report_*.txt
```

---

## 📊 metadata.json

**Cấu trúc:**

```json
{
  "Nghi_dinh_15_2024_abc123": {
    "id": "Nghi_dinh_15_2024_abc123",
    "title": "Nghị định 15/2024/NĐ-CP về chuyển đổi số",
    "document_number": "15/2024/NĐ-CP",
    "document_type": "Nghị định",
    "issuing_agency": "Chính phủ",
    "issued_date": "2024-01-15",
    "effective_date": "2024-03-01",
    "source_url": "https://vanban.chinhphu.vn/...",
    "source_website": "vanban.chinhphu.vn",
    "pdf_filename": "Nghi_dinh_15_2024_abc123.pdf",
    "text_filename": "Nghi_dinh_15_2024_abc123.txt",
    "category": "Công nghệ thông tin",
    "is_tech_related": true,
    "crawled_at": "2024-10-15T10:30:00"
  },
  "Quyet_dinh_456_def456": {
    ...
  }
}
```

**Mọi thông tin đều ở đây!**

---

## 🚀 CÁCH SỬ DỤNG

### **1. Crawl data:**

```bash
python3 run_government_crawl.py --max-docs 10
```

**Tạo ra:**
- ✅ `data/metadata.json` - Thông tin documents
- ✅ `data/pdf_documents/*.pdf` - PDFs
- ✅ `data/text_documents/*.txt` - Texts

---

### **2. Xem data:**

```bash
# Interactive menu
python3 view_data.py

# Hoặc command line
python3 view_data.py --summary
python3 view_data.py --recent 10
python3 view_data.py --id "Nghi_dinh_15_2024_abc123"
```

---

### **3. Export data:**

```bash
# Export JSON
python3 tools/export_data.py --format json

# Export CSV
python3 tools/export_data.py --format csv

# Generate report
python3 tools/export_data.py --report
```

---

## 💡 ƯU ĐIỂM

### **1. Đơn giản:**
```bash
# Xem tất cả metadata
cat data/metadata.json | python3 -m json.tool

# Xem PDFs
ls data/pdf_documents/

# Xem texts
cat data/text_documents/Nghi_dinh_*.txt
```

### **2. Portable:**
```bash
# Copy toàn bộ folder data
cp -r data/ backup/

# Share với người khác
zip -r data.zip data/
```

### **3. Dễ truy cập:**
```bash
# Không cần database tools
# Chỉ cần text editor hoặc terminal

# Search trong metadata
grep "công nghệ" data/metadata.json

# Search trong text files
grep -r "AI" data/text_documents/
```

### **4. Tích hợp dễ:**
```python
import json

# Load metadata
with open('data/metadata.json', 'r') as f:
    data = json.load(f)

# Get all documents
for doc_id, doc in data.items():
    print(f"{doc['title']} - {doc['source_website']}")
```

---

## 📊 STORAGE MANAGER

### **FileStorageManager:**

```python
from src.storage.file_storage import FileStorageManager

# Initialize
storage = FileStorageManager()

# Save document
doc_id = storage.save_document(
    title="Nghị định 15/2024",
    source_url="https://vanban.chinhphu.vn/...",
    pdf_path=Path("path/to/file.pdf"),
    text_path=Path("path/to/file.txt"),
    source_website="vanban.chinhphu.vn",
    category="Công nghệ thông tin",
    is_tech_related=True
)

# Get document
doc = storage.get_document(doc_id)

# Get all documents
all_docs = storage.get_all_documents()

# Get statistics
stats = storage.get_statistics()

# Export
storage.export_to_json(Path("export.json"), tech_only=True)
storage.export_to_csv(Path("export.csv"), tech_only=False)
```

---

## 🔍 XEM DATA

### **1. Xem metadata:**

```bash
# Pretty print
cat data/metadata.json | python3 -m json.tool | less

# Count documents
cat data/metadata.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# Filter tech docs
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.values() if x['is_tech_related']))"
```

---

### **2. Xem PDFs:**

```bash
# List all
ls -lh data/pdf_documents/

# Open one
open data/pdf_documents/Nghi_dinh_15_2024_abc123.pdf

# Count
ls data/pdf_documents/*.pdf | wc -l
```

---

### **3. Xem texts:**

```bash
# View one
cat data/text_documents/Nghi_dinh_15_2024_abc123.txt

# Preview
head -50 data/text_documents/Nghi_dinh_15_2024_abc123.txt

# Search
grep -i "công nghệ" data/text_documents/*.txt

# Count
ls data/text_documents/*.txt | wc -l
```

---

## 📤 EXPORT

### **JSON Export:**

```bash
python3 tools/export_data.py --format json --tech-only
```

**Output:** `exports/tech_documents.json`

```json
[
  {
    "id": "Nghi_dinh_15_2024_abc123",
    "title": "Nghị định 15/2024/NĐ-CP",
    "document_type": "Nghị định",
    ...
  },
  ...
]
```

---

### **CSV Export:**

```bash
python3 tools/export_data.py --format csv --tech-only
```

**Output:** `exports/tech_documents.csv`

```csv
id,title,document_type,issued_date,source_website,...
Nghi_dinh_15_2024_abc123,"Nghị định 15/2024",Nghị định,2024-01-15,vanban.chinhphu.vn,...
...
```

**→ Mở bằng Excel/Google Sheets!**

---

### **Report:**

```bash
python3 tools/export_data.py --report
```

**Output:**

```
============================================================
VIETNAMESE LEGAL DOCUMENTS CRAWLER
Summary Report
============================================================

BASIC STATISTICS
------------------------------------------------------------
Total Documents: 50
Tech-Related Documents: 50
Tech Ratio: 100.0%
Documents with PDFs: 35 (70.0%)
Documents with Texts: 48 (96.0%)

DOCUMENTS BY TYPE
------------------------------------------------------------
Nghị định: 20 (40.0%)
Quyết định: 15 (30.0%)
...
```

---

## 🎯 WORKFLOW ĐẦY ĐỦ

```bash
# 1. Crawl
python3 run_government_crawl.py --max-docs 10

# Output:
# ✅ 10 documents saved
# 📁 PDFs: data/pdf_documents/ (8 files)
# 📝 Texts: data/text_documents/ (10 files)
# 📊 Metadata: data/metadata.json

# 2. Check data
python3 view_data.py --check

# 3. View summary
python3 view_data.py --summary

# 4. View recent
python3 view_data.py --recent 5

# 5. View detail
python3 view_data.py --id "Nghi_dinh_15_2024_abc123"

# 6. Export JSON
python3 tools/export_data.py --format json

# 7. View export
cat exports/tech_documents.json | python3 -m json.tool

# 8. Browse PDFs
open data/pdf_documents/

# 9. Read text
cat data/text_documents/Nghi_dinh_15_2024_abc123.txt
```

---

## 🔧 ADVANCED

### **Python Integration:**

```python
import json
from pathlib import Path

# Load metadata
with open('data/metadata.json', 'r') as f:
    metadata = json.load(f)

# Filter documents
tech_docs = {
    doc_id: doc 
    for doc_id, doc in metadata.items() 
    if doc['is_tech_related']
}

print(f"Tech documents: {len(tech_docs)}")

# Read text file
for doc_id, doc in list(tech_docs.items())[:5]:
    if doc['text_filename']:
        text_path = Path('data/text_documents') / doc['text_filename']
        if text_path.exists():
            with open(text_path, 'r') as f:
                content = f.read()
            print(f"\n{doc['title']}")
            print(f"Content: {content[:200]}...")
```

---

### **Backup:**

```bash
# Backup everything
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Backup only metadata
cp data/metadata.json backup/metadata_$(date +%Y%m%d).json

# Restore
tar -xzf backup_20241015.tar.gz
```

---

### **Share:**

```bash
# Create shareable archive
zip -r legal_docs.zip data/

# Share with colleague
# They just unzip and have everything!
```

---

## ✅ SUMMARY

| Feature | File Storage |
|---------|--------------|
| **Simplicity** | ⭐⭐⭐⭐⭐ |
| **Portability** | ⭐⭐⭐⭐⭐ |
| **Easy access** | ⭐⭐⭐⭐⭐ |
| **No tools needed** | ✅ |
| **Human readable** | ✅ |
| **Easy backup** | ✅ |
| **Easy share** | ✅ |
| **Integration** | ✅ |

**Perfect cho:**
- ✅ Small to medium datasets
- ✅ Easy sharing
- ✅ No database hassle
- ✅ Simple workflows
- ✅ Quick prototyping

---

**KHÔNG CẦN DATABASE!** 🎉

Mọi thứ trong folders + 1 file JSON! 📁
