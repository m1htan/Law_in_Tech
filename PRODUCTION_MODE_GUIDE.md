# 🚀 PRODUCTION MODE - Crawl Toàn Bộ Văn Bản Pháp Luật VN

## 📊 Tổng quan

**Mode**: Production - Systematic Crawling  
**Target**: Toàn bộ văn bản pháp luật Việt Nam  
**Focus**: Công nghệ thông tin (CNTT)  
**Method**: Category-based crawling (không dựa vào keyword)

---

## 🎯 Mục tiêu

Crawl **toàn bộ** văn bản pháp luật VN bao gồm:
1. ✅ Văn bản quy phạm pháp luật
2. ✅ Văn bản dưới luật  
3. ✅ Nghị quyết, Nghị định, Quyết định, Thông tư
4. ✅ Luật, Pháp lệnh
5. ✅ Dự thảo văn bản

**Ưu tiên**: Mảng Công nghệ thông tin

---

## 🗂️ Database Schema

### **Table: documents**

```sql
- id (PRIMARY KEY)
- title, document_number, document_type
- issuing_agency, signer
- issued_date, effective_date
- summary, full_text
- source_url, source_website
- pdf_path, text_path
- category, subject, keywords
- is_tech_related, tech_categories, relevance_score
- status, superseded_by
- crawled_at, updated_at
- ai_analyzed, ai_analysis
```

### **Table: crawl_progress**

```sql
- website, category
- last_page, total_pages
- documents_crawled
- started_at, updated_at, completed
```

**Location**: `data/legal_documents.db` (SQLite)

---

## 🏗️ Architecture

### **Components**:

1. **DatabaseManager** (`src/database/models.py`)
   - SQLite database
   - Document model
   - CRUD operations
   - Statistics & progress tracking

2. **ProductionCrawler** (`src/crawlers/production_crawler.py`)
   - Systematic category crawling
   - Pagination handling
   - Progress saving
   - Resume capability

3. **Export Tools** (`tools/export_data.py`)
   - JSON export
   - CSV export
   - Summary reports

---

## 🚀 Cách sử dụng

### **Mode 1: Limited Crawl (Testing)**

```bash
# Crawl 50 documents, 10 pages
python3 run_production_crawl.py --mode limited \
  --category cong-nghe-thong-tin \
  --max-docs 50 \
  --max-pages 10
```

**Output:**
- ~50 documents crawled
- Saved to database
- PDFs downloaded & converted
- Progress tracked

**Time**: ~10-15 minutes

### **Mode 2: Full Crawl (Production)**

```bash
# Crawl ALL tech documents
python3 run_production_crawl.py --mode full
```

**Output:**
- ALL tech categories crawled:
  - Công nghệ thông tin
  - Thương mại điện tử
  - Sở hữu trí tuệ
  - Viễn thông
- Thousands of documents
- Complete database

**Time**: Several hours (depends on bandwidth)

⚠️ **Warning**: This will crawl A LOT of data!

### **Mode 3: Resume Crawl**

```bash
# Resume interrupted crawl
python3 run_production_crawl.py --mode resume \
  --category cong-nghe-thong-tin
```

**Features:**
- Automatically resumes from last page
- No duplicate crawling
- Progress preserved

---

## 📁 Categories Available

### **Tech Categories** (Priority):

1. **Công nghệ thông tin** (`cong-nghe-thong-tin`)
   - Priority: HIGH
   - URL: `/van-ban/Cong-nghe-thong-tin`
   - Expected: 1000+ documents

2. **Thương mại điện tử** (`thuong-mai-dien-tu`)
   - Priority: HIGH
   - URL: `/van-ban/Thuong-mai`
   - Expected: 500+ documents

3. **Sở hữu trí tuệ** (`so-huu-tri-tue`)
   - Priority: MEDIUM
   - URL: `/van-ban/So-huu-tri-tue`
   - Expected: 300+ documents

4. **Viễn thông** (`vien-thong`)
   - Priority: MEDIUM
   - Included in CNTT category

---

## 📊 Export Data

### **Export Tech Documents (JSON)**:

```bash
python3 tools/export_data.py --tech-only --format json
```

**Output**: `exports/tech_documents.json`

### **Export All Data (CSV)**:

```bash
python3 tools/export_data.py --format csv
```

**Output**: `exports/legal_docs_TIMESTAMP.csv`

### **Generate Report**:

```bash
python3 tools/export_data.py --report
```

**Output**:
```
VIETNAMESE LEGAL DOCUMENTS CRAWLER
Summary Report
============================================================

Total Documents: 150
Tech Documents: 120
Tech Ratio: 80.0%

DOCUMENTS BY TYPE
------------------------------------------------------------
Nghị định: 45
Thông tư: 38
Quyết định: 25
...
```

---

## 🔄 Workflow

### **Production Crawl Process:**

```
1. [Category Selection]
        ↓
2. [Page Crawling]
   - Get document list from page
   - Extract: title, number, type, date
        ↓
3. [Document Detail]
   - Crawl each document page
   - Extract full details
   - Download PDFs
   - Convert to text
        ↓
4. [Database Save]
   - Insert/update document
   - Save progress
        ↓
5. [Next Page/Document]
   - Continue until all pages
   - Or max limit reached
        ↓
6. [Export & Report]
   - Export to JSON/CSV
   - Generate statistics
```

---

## 📦 Data Structure

### **LegalDocument Model**:

```python
{
    "id": 123,
    "title": "Nghị định 123/2024/NĐ-CP về...",
    "document_number": "123/2024/NĐ-CP",
    "document_type": "Nghị định",
    "issuing_agency": "Chính phủ",
    "issued_date": "2024-10-14",
    "effective_date": "2024-12-01",
    "summary": "Quy định về...",
    "full_text": "...",
    "source_url": "https://...",
    "pdf_path": "data/pdf_documents/...",
    "text_path": "data/text_documents/...",
    "category": "Công nghệ thông tin",
    "is_tech_related": true,
    "relevance_score": 9.5,
    "status": "active"
}
```

---

## 🎯 Features

### ✅ **Systematic Crawling**
- No keyword dependency
- Complete category coverage
- Pagination handling
- All document types

### ✅ **Progress Tracking**
- Save progress after each page
- Resume from interruption
- Track documents crawled
- Prevent duplicates

### ✅ **Data Persistence**
- SQLite database
- Structured schema
- Fast queries
- Easy export

### ✅ **PDF Processing**
- Auto download PDFs
- Convert to text (3 methods)
- Store both formats
- Metadata extraction

### ✅ **Classification**
- Auto detect tech-related
- Category assignment
- Relevance scoring
- Status tracking

---

## 📈 Expected Results

### **Limited Crawl (50 docs)**:

```
Pages crawled: ~10
Documents found: ~50-100
Documents saved: ~50
PDFs downloaded: ~25-50
Time: ~15 minutes
Database size: ~50 MB
```

### **Full Crawl (All tech)**:

```
Categories: 4
Pages crawled: ~200+
Documents found: ~2000+
Documents saved: ~2000+
PDFs downloaded: ~1000+
Time: ~6-10 hours
Database size: ~2-5 GB
```

---

## 🛠️ Maintenance

### **Check Progress**:

```python
from src.database.models import DatabaseManager

db = DatabaseManager()
stats = db.get_statistics()
print(stats)
```

### **Query Database**:

```python
# Get tech documents
tech_docs = db.get_tech_documents(limit=10)

# Get specific document
doc = db.get_document_by_url("https://...")
```

### **Database Location**:

```
data/legal_documents.db
```

**Tools**: SQLite Browser, DBeaver, etc.

---

## ⚙️ Configuration

File: `.env`

```env
# Crawl settings
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=2
CRAWL_TIMEOUT=60000
MAX_RETRIES=3

# Date range
START_YEAR=2022
END_YEAR=2024
```

---

## 🔍 Example Usage

### **Scenario 1: Quick Test**

```bash
# Test with 10 documents
python3 run_production_crawl.py --mode limited \
  --max-docs 10 --max-pages 2
```

### **Scenario 2: One Category Full Crawl**

```bash
# Crawl all CNTT documents
python3 run_production_crawl.py --mode limited \
  --category cong-nghe-thong-tin \
  --max-pages 100 --max-docs 1000
```

### **Scenario 3: Production (All)**

```bash
# Full production crawl
python3 run_production_crawl.py --mode full
```

### **Scenario 4: Export Results**

```bash
# Export to JSON and CSV
python3 tools/export_data.py --tech-only --format both

# Generate report
python3 tools/export_data.py --report
```

---

## 📊 Statistics & Monitoring

### **Real-time Progress**:

Logs show:
```
[1/50] Document: Nghị định 123/2024...
✓ Document saved: ID 456
Progress: Page 5/10, Documents: 25/50
```

### **Database Stats**:

```python
stats = db.get_statistics()
# {
#   'total_documents': 150,
#   'tech_documents': 120,
#   'by_type': {'Nghị định': 45, ...},
#   'by_year': {'2024': 80, ...}
# }
```

---

## 🎯 Next Steps

### **After Initial Crawl**:

1. ✅ **Analyze Data**
   - Check database stats
   - Review documents
   - Verify completeness

2. ✅ **AI Analysis** (Optional)
   - Run AI agent on saved docs
   - Add relevance scores
   - Generate summaries

3. ✅ **Export & Use**
   - Export to needed formats
   - Use in research
   - Present findings

4. ✅ **Schedule Updates**
   - Regular re-crawls
   - New documents detection
   - Status updates

---

## 🚨 Important Notes

### **Rate Limiting**:
- Delay: 2 seconds between requests
- Respect robots.txt
- Avoid overloading servers

### **Storage**:
- Database can grow large (GB+)
- PDFs take significant space
- Monitor disk usage

### **Network**:
- Stable internet required
- Several hours for full crawl
- Can resume if interrupted

### **Legal**:
- Public documents only
- Respect copyright
- Academic/research use

---

## 🎊 Summary

You now have a **PRODUCTION-READY** system that can:

✅ Crawl toàn bộ văn bản pháp luật VN  
✅ Focus on CNTT systematically  
✅ Store in structured database  
✅ Track progress & resume  
✅ Download & process PDFs  
✅ Export to multiple formats  
✅ Generate statistics & reports  

**Status**: Ready for large-scale crawling!

---

## 🚀 Quick Start

```bash
# 1. Test with limited crawl
python3 run_production_crawl.py --mode limited --max-docs 10

# 2. Check database
python3 tools/export_data.py --report

# 3. Export data
python3 tools/export_data.py --tech-only --format json

# 4. Ready for production!
python3 run_production_crawl.py --mode full
```

---

**Date**: 2025-10-14  
**Status**: ✅ PRODUCTION READY  
**Mode**: Systematic Crawling  
**Target**: Complete Legal Document Collection

🎉 **Ready to crawl!**
