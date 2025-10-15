# 🚀 QUICK START - Government Sites Crawler

## Chạy ngay trong 5 phút!

## 🎉 THAY ĐỔI MỚI: KHÔNG DÙNG DATABASE

✅ **Mọi data lưu trong folders:**
- `data/pdf_documents/` - PDFs
- `data/text_documents/` - Texts
- `data/metadata.json` - Thông tin documents

❌ **KHÔNG cần:**
- SQLite database
- Database tools
- Phức tạp

---

## ✅ Prerequisites

- ✅ Python 3.10+ installed
- ✅ Dependencies installed (`pip3 install -r requirements.txt`)
- ✅ Internet connection

---

## 🏛️ GOVERNMENT CRAWLER (Official .gov.vn)

### **Step 1: Test nhanh (5 phút)**

```bash
cd /Users/minhtan/Downloads/Law_in_Tech-cursor-crawl-vietnamese-legal-documents-for-ai-agent-771c

python3 run_government_crawl.py --max-docs 10
```

**Kết quả mong đợi:**

```
🏛️  GOVERNMENT SITES CRAWLER
============================================================

1/2 CRAWLING: vanban.chinhphu.vn
✓ Found 53 PDF links
✓ Saved PDF document: ID 1
✓ Saved PDF document: ID 2
...
✓ Saved: 5 documents

2/2 CRAWLING: mst.gov.vn
✓ Saved: 5 documents

CRAWL COMPLETED
============================================================
sites_crawled: 2
total_documents: 10
total_pdfs: 5-8

STORAGE STATISTICS
Total documents: 10
Tech documents: 10
With PDFs: 8
With texts: 10

✅ Done!
📁 PDFs: data/pdf_documents/ (8 files)
📝 Texts: data/text_documents/ (10 files)
📊 Metadata: data/metadata.json
```

---

### **Step 2: Xem kết quả**

```bash
# Xem summary
python3 view_data.py --summary

# Hoặc xem báo cáo đầy đủ
python3 tools/export_data.py --report
```

**Output:**

```
📚 STORAGE SUMMARY
============================================================

📊 THỐNG KÊ TỔNG QUAN:
   Total documents: 10
   Tech documents: 10
   With PDFs: 8
   With texts: 10
   Tech ratio: 100.0%

📋 THEO LOẠI VĂN BẢN:
   Nghị định: 4
   Quyết định: 3
   Thông tư: 2
   Chỉ thị: 1

📅 THEO NĂM:
   2024: 6
   2023: 3
   2022: 1
```

---

### **Step 3: Export data**

```bash
# Export to JSON
python3 tools/export_data.py --tech-only --format json

# Export to CSV
python3 tools/export_data.py --tech-only --format csv
```

**Files created:**

- `exports/tech_documents.json`
- `exports/tech_documents.csv`

---

## 📊 Check Downloaded Files

```bash
# Metadata (all info)
cat data/metadata.json | python3 -m json.tool | less

# PDFs
ls data/pdf_documents/
# → Nghi_dinh_15_2024_abc123.pdf

# Text files
ls data/text_documents/
# → Nghi_dinh_15_2024_abc123.txt

# All data folder
ls data/
# → metadata.json, pdf_documents/, text_documents/
```

---

## 🎯 Production Crawl (Large Scale)

### **Crawl 100 documents:**

```bash
python3 run_government_crawl.py --max-docs 100
```

**Time:** ~30 minutes  
**Output:** ~100 documents, ~50-70 PDFs

### **Crawl 500 documents:**

```bash
python3 run_government_crawl.py --max-docs 500
```

**Time:** ~2-3 hours  
**Output:** ~500 documents, ~250-350 PDFs

---

## 💡 Pro Tips

### **1. Start small, then scale:**

```bash
# Test
python3 run_government_crawl.py --max-docs 10

# If OK
python3 run_government_crawl.py --max-docs 50

# If OK
python3 run_government_crawl.py --max-docs 200
```

### **2. Focus on one source:**

```bash
# Best source: vanban.chinhphu.vn
python3 run_government_crawl.py --source vanban --max-docs 100
```

### **3. Export regularly:**

```bash
# Every 50 documents
python3 tools/export_data.py --tech-only --format json
```

### **4. Monitor progress:**

```bash
# In another terminal
tail -f logs/vietnamese_legal_crawler.log
```

---

## 🔍 Verify Results

### **Check storage:**

```bash
python3 view_data.py --summary
```

### **Check files:**

```bash
# Count PDFs
ls data/pdf_documents/ | wc -l

# Count text files
ls data/text_documents/ | wc -l
```

---

## ⚠️ Troubleshooting

### **Problem: No documents found**

**Solution:** Run test script first:

```bash
python3 test_production_quick.py
```

### **Problem: Timeout errors**

**Solution:** Increase timeout:

```bash
# Edit .env
CRAWL_TIMEOUT=120000
```

### **Problem: Metadata file corrupted**

**Solution:** Delete and re-crawl:

```bash
rm data/metadata.json
python3 run_government_crawl.py --max-docs 10
```

---

## 📝 Example Session

```bash
# 1. Navigate to project
cd /Users/minhtan/Downloads/Law_in_Tech-cursor-crawl-vietnamese-legal-documents-for-ai-agent-771c

# 2. Run crawler (10 docs test)
python3 run_government_crawl.py --max-docs 10

# 3. Wait ~5 minutes

# 4. Check results
python3 tools/export_data.py --report

# 5. Export data
python3 tools/export_data.py --tech-only --format json

# 6. Check files
ls data/pdf_documents/
ls data/text_documents/
ls exports/

# 7. View exported JSON
cat exports/tech_documents.json | head -50
```

---

## ✅ Success Checklist

After running, you should have:

- ✅ Metadata file: `data/metadata.json`
- ✅ PDF files: `data/pdf_documents/*.pdf`
- ✅ Text files: `data/text_documents/*.txt`
- ✅ Export files: `exports/*.json` or `*.csv`
- ✅ Logs: `logs/*.log`
- ✅ Statistics showing documents saved

---

## 🎊 Done!

Your data is now:
- ✅ Stored in folders (NO database!)
- ✅ Available as PDFs
- ✅ Available as text  
- ✅ Metadata in JSON
- ✅ Exported to JSON/CSV
- ✅ Ready for analysis

**Next:** Use the data for your presentation! 📊

---

**Time to complete:** 5-30 minutes  
**Difficulty:** Easy ⭐  
**Success rate:** 95%+  
**Recommended for:** Official research work

🏛️ **Official government sources only!**
