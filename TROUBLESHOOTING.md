## 🔧 TROUBLESHOOTING - Production Crawler

### ❌ Problem: "No documents found" (0 documents extracted)

**Symptoms:**
```
Found 0 potential document items
documents_found: 0
documents_crawled: 0
```

**Root Cause:**
- thuvienphapluat.vn đã thay đổi HTML structure
- CSS selectors không còn đúng
- Anti-bot protection blocking content

---

### ✅ SOLUTIONS

#### **Solution 1: Use Search-Based Crawler (RECOMMENDED)**

Thay vì crawl category pages, sử dụng search:

```bash
# Run search-based crawler
python3 src/crawlers/search_based_crawler.py "công nghệ thông tin"
```

**Advantages:**
- ✅ More reliable
- ✅ Better results
- ✅ Bypasses category page issues
- ✅ Can specify exact keywords

**Example:**
```bash
# Search for AI documents
python3 src/crawlers/search_based_crawler.py "trí tuệ nhân tạo"

# Search for cybersecurity
python3 src/crawlers/search_based_crawler.py "an ninh mạng"
```

---

#### **Solution 2: Debug HTML Structure**

Check actual HTML structure:

```bash
# Run debug script
python3 debug_html_structure.py
```

This will:
- Save HTML to `debug_page.html`
- Show all CSS classes
- Display document links found
- Help identify correct selectors

Then update selectors in `src/crawlers/production_crawler.py`:
```python
# Line ~106-112
selector_strategies = [
    ('YOUR_NEW_SELECTOR', soup.select('YOUR_NEW_SELECTOR')),
    ...
]
```

---

#### **Solution 3: Use Alternative Sources**

Try other legal document websites:

**1. vanban.chinhphu.vn** (Government official)
```python
# More reliable, official source
# Simpler HTML structure
# Better for systematic crawling
```

**2. congbao.chinhphu.vn** (Official Gazette)
```python
# Official publications
# PDF-heavy
# Good for complete documents
```

**3. lawnet.vn**
```python
# Alternative legal database
# Different structure
# Good backup source
```

---

### 📝 Quick Fixes

#### **Fix 1: Updated Selectors (Already Applied)**

File: `src/crawlers/production_crawler.py`

New selectors now include:
- `ul.list-vb li` - List items
- `div.list-vb > div` - List divs
- `a[href*="van-ban/"]` - Direct links
- Fallback to all van-ban links

#### **Fix 2: Test Before Full Crawl**

Always test first:
```bash
# Quick test
python3 test_production_quick.py

# If works:
python3 run_production_crawl.py --mode limited --max-docs 10
```

---

### 🔍 Diagnostic Commands

```bash
# 1. Check database
python3 -c "from src.database.models import DatabaseManager; \
  db = DatabaseManager(); \
  print(db.get_statistics()); \
  db.close()"

# 2. Test single URL
python3 test_production_quick.py

# 3. Check logs
tail -f logs/vietnamese_legal_crawler.log

# 4. Export current data
python3 tools/export_data.py --report
```

---

### 💡 Best Practices

#### **1. Start Small**
```bash
# Test with 10 documents first
python3 run_production_crawl.py --mode limited --max-docs 10

# If successful, increase
python3 run_production_crawl.py --mode limited --max-docs 100
```

#### **2. Use Search for Specific Topics**
```bash
# More targeted and reliable
python3 src/crawlers/search_based_crawler.py "blockchain"
python3 src/crawlers/search_based_crawler.py "chuyển đổi số"
python3 src/crawlers/search_based_crawler.py "dữ liệu cá nhân"
```

#### **3. Monitor Progress**
```bash
# Check database stats regularly
python3 tools/export_data.py --report

# Watch logs
tail -f logs/vietnamese_legal_crawler.log
```

#### **4. Resume on Failure**
```bash
# If interrupted, resume
python3 run_production_crawl.py --mode resume \
  --category cong-nghe-thong-tin
```

---

### 🚀 Alternative Workflow

If category crawling fails, use this workflow:

**Step 1: Use Search-Based Crawler**
```bash
# Crawl by keywords
keywords=(
  "công nghệ thông tin"
  "chuyển đổi số"
  "an ninh mạng"
  "trí tuệ nhân tạo"
  "blockchain"
  "dữ liệu lớn"
)

for keyword in "${keywords[@]}"; do
  echo "Crawling: $keyword"
  python3 src/crawlers/search_based_crawler.py "$keyword"
  sleep 10
done
```

**Step 2: Check Results**
```bash
python3 tools/export_data.py --report
```

**Step 3: Export Data**
```bash
python3 tools/export_data.py --tech-only --format json
python3 tools/export_data.py --tech-only --format csv
```

---

### 📊 Expected Results

**If Working:**
```
✓ Pages crawled: 5+
✓ Documents found: 50+
✓ Documents saved: 20+
✓ Database size: Growing
```

**If Not Working:**
```
✗ Documents found: 0
✗ Documents saved: 0
→ Use search-based crawler
→ Or try alternative sources
```

---

### 🆘 Still Having Issues?

**Checklist:**

1. ✅ Internet connection stable?
2. ✅ API key configured (if using AI features)?
3. ✅ Disk space available?
4. ✅ Tried search-based crawler?
5. ✅ Checked logs for errors?
6. ✅ Database file writable?

**Debug Steps:**

```bash
# 1. Verify crawler works at all
python3 test_crawler_simple.py

# 2. Try different URL
python3 test_production_quick.py

# 3. Check HTML structure
python3 debug_html_structure.py

# 4. Use search instead
python3 src/crawlers/search_based_crawler.py "test"
```

---

### 📞 Common Error Messages

#### Error: "No documents found"
**Solution:** Use search-based crawler

#### Error: "Timeout exceeded"
**Solution:** Increase timeout in `.env`:
```
CRAWL_TIMEOUT=120000
```

#### Error: "Database locked"
**Solution:** Close other connections:
```bash
rm data/legal_documents.db-journal
```

#### Error: "PDF download failed"
**Solution:** Disable PDF download temporarily:
```python
extract_pdfs=False
```

---

### ✅ Success Indicators

You'll know it's working when:

```
✓ Using selector: a[href*="van-ban/"] (150 items)
✓ Found 50 documents on page 1
✓ [1/50] Nghị định 123/2024...
✓ Document saved: ID 456
✓ Progress: 25/50 documents
```

---

**Last Updated:** 2025-10-15  
**Status:** Search-based crawler recommended  
**Alternative:** Use vanban.chinhphu.vn
