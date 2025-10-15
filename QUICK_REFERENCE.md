# 📖 QUICK REFERENCE - File Storage System

## 🎯 Một câu lệnh, một mục đích

---

## 🚀 CRAWL DATA

```bash
# Test (10 docs, 5 phút)
python3 run_government_crawl.py --max-docs 10

# Small (50 docs, 15 phút)
python3 run_government_crawl.py --max-docs 50

# Medium (100 docs, 30 phút)
python3 run_government_crawl.py --max-docs 100

# Large (500 docs, 2-3 giờ)
python3 run_government_crawl.py --max-docs 500
```

---

## 👀 XEM DATA

```bash
# Menu tương tác
python3 view_data.py

# Xem tóm tắt
python3 view_data.py --summary

# Xem 10 docs mới nhất
python3 view_data.py --recent 10

# Xem chi tiết 1 doc
python3 view_data.py --id "doc_id_here"

# List PDFs
python3 view_data.py --pdfs

# List texts
python3 view_data.py --texts

# Check data tồn tại
python3 view_data.py --check
```

---

## 📤 EXPORT DATA

```bash
# Export JSON
python3 tools/export_data.py --format json

# Export JSON (tech only)
python3 tools/export_data.py --format json --tech-only

# Export CSV
python3 tools/export_data.py --format csv

# Export both
python3 tools/export_data.py --format both

# Generate report
python3 tools/export_data.py --report
```

---

## 📁 TRUY CẬP FILES

```bash
# Xem metadata
cat data/metadata.json | python3 -m json.tool | less

# Xem metadata (pretty)
cat data/metadata.json | python3 -m json.tool

# Count documents
cat data/metadata.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# List PDFs
ls -lh data/pdf_documents/

# List texts
ls -lh data/text_documents/

# Open PDF folder
open data/pdf_documents/          # Mac
nautilus data/pdf_documents/      # Linux

# View a text file
cat data/text_documents/filename.txt

# Preview text
head -50 data/text_documents/filename.txt
```

---

## 🔍 SEARCH

```bash
# Search trong metadata
grep "công nghệ" data/metadata.json

# Search trong text files
grep -r "AI" data/text_documents/

# Search và show filename
grep -l "blockchain" data/text_documents/*.txt

# Search case-insensitive
grep -ri "chuyển đổi số" data/text_documents/

# Count matches
grep -r "công nghệ" data/text_documents/ | wc -l
```

---

## 📊 STATISTICS

```bash
# Quick stats
python3 view_data.py --summary

# Detailed report
python3 tools/export_data.py --report

# Count PDFs
ls data/pdf_documents/*.pdf | wc -l

# Count texts
ls data/text_documents/*.txt | wc -l

# Total PDF size
du -sh data/pdf_documents/

# Total text size
du -sh data/text_documents/
```

---

## 🔧 MAINTENANCE

```bash
# Backup everything
cp -r data/ backup_$(date +%Y%m%d)/

# Backup metadata only
cp data/metadata.json backup/metadata_$(date +%Y%m%d).json

# Compress for sharing
zip -r data_$(date +%Y%m%d).zip data/

# Clean and recrawl
rm data/metadata.json
python3 run_government_crawl.py --max-docs 10

# View logs
tail -f logs/vietnamese_legal_crawler.log

# View errors only
tail -f logs/vietnamese_legal_crawler_errors.log
```

---

## 🧪 TESTING

```bash
# Test file storage
python3 test_file_storage.py

# Test with small crawl
python3 run_government_crawl.py --max-docs 5

# Verify data
python3 view_data.py --check
```

---

## 💻 PYTHON INTEGRATION

### **Load metadata:**

```python
import json

with open('data/metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Total: {len(metadata)}")
```

---

### **Filter tech docs:**

```python
import json

with open('data/metadata.json', 'r') as f:
    metadata = json.load(f)

tech_docs = {
    doc_id: doc 
    for doc_id, doc in metadata.items() 
    if doc.get('is_tech_related')
}

print(f"Tech docs: {len(tech_docs)}")
```

---

### **Read text file:**

```python
from pathlib import Path

doc_id = "Nghi_dinh_15_2024_abc123"
text_file = Path(f"data/text_documents/{doc_id}.txt")

if text_file.exists():
    with open(text_file, 'r') as f:
        content = f.read()
    print(content[:500])
```

---

### **Use FileStorageManager:**

```python
from src.storage.file_storage import FileStorageManager

storage = FileStorageManager()

# Get stats
stats = storage.get_statistics()
print(f"Total: {stats['total_documents']}")

# Get all docs
docs = storage.get_all_documents()

# Get one doc
doc = storage.get_document("doc_id_here")

# Export
storage.export_to_json(Path("export.json"))
```

---

## 📂 FILE LOCATIONS

```
data/
├── metadata.json               # All document info
├── pdf_documents/              # Original PDFs
│   └── *.pdf
└── text_documents/             # Converted texts
    └── *.txt

exports/
├── tech_documents.json         # Exported JSON
├── tech_documents.csv          # Exported CSV
└── report_*.txt                # Reports

logs/
├── vietnamese_legal_crawler.log         # All logs
└── vietnamese_legal_crawler_errors.log  # Errors only
```

---

## 🎯 COMMON WORKFLOWS

### **Workflow 1: Quick test**

```bash
python3 run_government_crawl.py --max-docs 10
python3 view_data.py --summary
python3 tools/export_data.py --format json
cat exports/tech_documents.json | python3 -m json.tool
```

---

### **Workflow 2: Production crawl**

```bash
python3 run_government_crawl.py --max-docs 100
python3 view_data.py --summary
python3 tools/export_data.py --report
python3 tools/export_data.py --format both
```

---

### **Workflow 3: Inspect data**

```bash
python3 view_data.py
# Choose option 2 (summary)
# Choose option 3 (recent docs)
# Choose option 4 (detail by ID)
```

---

### **Workflow 4: Share with colleague**

```bash
# Create archive
zip -r legal_docs_$(date +%Y%m%d).zip data/

# Share the zip file
# Colleague just unzips and has everything!
```

---

## ⚡ ONE-LINERS

```bash
# Total documents
cat data/metadata.json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"

# Tech documents
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.values() if x['is_tech_related']))"

# Documents by year 2024
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.values() if x.get('issued_date','').startswith('2024')))"

# List all titles
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(x['title']) for x in d.values()]"

# Documents from vanban.chinhphu.vn
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for x in d.values() if 'vanban.chinhphu.vn' in x.get('source_website','')))"
```

---

## 🆘 TROUBLESHOOTING

### **Problem: No data**

```bash
# Solution: Crawl first
python3 run_government_crawl.py --max-docs 10
```

---

### **Problem: Metadata file corrupted**

```bash
# Solution: Delete and recrawl
rm data/metadata.json
python3 run_government_crawl.py --max-docs 10
```

---

### **Problem: Can't find document ID**

```bash
# Solution: List all IDs
cat data/metadata.json | python3 -c "import json,sys; d=json.load(sys.stdin); [print(k) for k in d.keys()]"
```

---

### **Problem: Want to recrawl**

```bash
# Solution: Just crawl again, duplicates are skipped
python3 run_government_crawl.py --max-docs 50
```

---

## 📞 HELP

```bash
# Crawler help
python3 run_government_crawl.py --help

# Viewer help
python3 view_data.py --help

# Export help
python3 tools/export_data.py --help
```

---

## 🎊 SUMMARY

| Task | Command |
|------|---------|
| **Crawl** | `python3 run_government_crawl.py --max-docs N` |
| **View** | `python3 view_data.py` |
| **Summary** | `python3 view_data.py --summary` |
| **Export** | `python3 tools/export_data.py --format json` |
| **Report** | `python3 tools/export_data.py --report` |
| **Metadata** | `cat data/metadata.json \| python3 -m json.tool` |
| **Backup** | `cp -r data/ backup/` |
| **Share** | `zip -r data.zip data/` |

---

**Bookmarks:**
- `FILE_STORAGE_GUIDE.md` - Complete guide
- `QUICK_START.md` - Getting started
- `THAY_DOI_QUAN_TRONG.md` - What changed

**Simple. Fast. Effective.** 📁✨
