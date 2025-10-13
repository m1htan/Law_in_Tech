# Hướng dẫn Cài đặt và Chạy BƯỚC 1

## 📋 Checklist trước khi chạy

- [ ] Python 3.9+ đã cài đặt
- [ ] Đã có Google API Key cho Gemini
- [ ] Kết nối Internet ổn định

## 🔧 Bước 1: Cài đặt Dependencies

```bash
# Cài đặt các thư viện Python
pip install -r requirements.txt

# Cài đặt Playwright browsers (cho web scraping nâng cao - optional cho bước 1)
playwright install chromium
```

**Lưu ý**: Nếu gặp lỗi khi cài `underthesea` hoặc các thư viện NLP, có thể bỏ qua vì bước 1 chưa dùng đến. Sẽ cài sau khi cần.

## 🔑 Bước 2: Cấu hình Google API Key

### 2.1. Lấy Google API Key (nếu chưa có)

1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập bằng tài khoản Google
3. Click "Create API Key"
4. Copy API key

### 2.2. Cập nhật file .env

Mở file `.env` và thay thế API key:

```bash
# Mở file .env bằng editor
nano .env
# hoặc
vi .env
# hoặc mở bằng VSCode/IDE của bạn
```

Sửa dòng này:
```
GOOGLE_API_KEY=your_google_api_key_here
```

Thành:
```
GOOGLE_API_KEY=AIzaSy...actual_key_here
```

**Lưu lại file!**

## ✅ Bước 3: Kiểm tra cài đặt

Chạy test để đảm bảo mọi thứ hoạt động:

```bash
python tests/test_text_processing.py
```

Kết quả mong đợi:
```
============================================================
RUNNING TEXT PROCESSING TESTS
============================================================
✓ test_normalize_vietnamese_text passed
✓ Extracted: 13/2023/NĐ-CP
✓ Extracted: 24/2023/QH15
✓ test_extract_document_number passed
✓ Extracted date: 2023-06-17
✓ Extracted date: 2024-12-25
✓ test_extract_date passed
✓ Generated doc_id: vanban_chinhphu_abc12345
✓ test_generate_doc_id passed
✓ Found keywords in text
✓ Correctly rejected with high threshold
✓ test_contains_keywords passed
✓ Cleaned HTML: Nghị định về bảo vệ dữ liệu
✓ test_clean_html_text passed
============================================================
✓ ALL TESTS PASSED!
============================================================
```

## 🚀 Bước 4: Chạy Metadata Discovery Agent

### 4.1. Chạy với cấu hình mặc định

```bash
python run_metadata_discovery.py
```

### 4.2. Chạy với từ khóa tùy chỉnh

```bash
python run_metadata_discovery.py --keywords "AI" "trí tuệ nhân tạo" "blockchain" "dữ liệu cá nhân"
```

### 4.3. Giới hạn số lượng văn bản

```bash
python run_metadata_discovery.py --max-documents 30
```

### 4.4. Cung cấp API key qua command line

```bash
python run_metadata_discovery.py --api-key "YOUR_API_KEY"
```

## 📊 Bước 5: Kiểm tra kết quả

Sau khi chạy xong (khoảng 1-2 phút), kiểm tra các file đầu ra:

### 5.1. Metadata JSON

```bash
# Xem file metadata mới nhất
ls -lht data/metadata/

# Xem nội dung (format đẹp)
cat data/metadata/metadata_vanban_chinhphu_*.json | python -m json.tool | head -50
```

### 5.2. Metadata CSV

```bash
# Xem CSV (10 dòng đầu)
head -10 data/metadata/metadata_vanban_chinhphu_*.csv

# Hoặc mở bằng Excel/LibreOffice/Google Sheets
```

### 5.3. Logs

```bash
# Xem logs
cat logs/metadata_discovery.log

# Xem logs theo thời gian thực (nếu đang chạy)
tail -f logs/metadata_discovery.log
```

## 🎯 Kết quả mong đợi

Sau khi chạy thành công, bạn sẽ thấy:

```
============================================================
METADATA DISCOVERY RESULTS
============================================================
✓ Success!
  - Total discovered: 45
  - Total relevant: 23
  - Saved to: data/metadata/metadata_vanban_chinhphu_20251013_103045.json
============================================================
Next steps:
1. Review the metadata files in: data/metadata/
2. Check the logs in: logs/metadata_discovery.log
3. Proceed to the next pipeline step (PDF crawling)
============================================================
```

## ❌ Xử lý lỗi thường gặp

### Lỗi 1: API Key không hợp lệ

```
ERROR: Google API key not configured!
```

**Giải pháp**: Kiểm tra lại API key trong file `.env`

### Lỗi 2: Không tìm thấy module

```
ModuleNotFoundError: No module named 'langchain'
```

**Giải pháp**: Cài lại dependencies
```bash
pip install -r requirements.txt
```

### Lỗi 3: Timeout khi crawl

```
Error: Request timeout
```

**Giải pháp**: 
- Kiểm tra kết nối Internet
- Tăng timeout trong `.env`: `TIMEOUT=60`
- Thử lại sau vài phút

### Lỗi 4: Không tìm thấy văn bản

```
Total discovered: 0
```

**Giải pháp**:
- Website có thể đã thay đổi cấu trúc HTML
- Kiểm tra logs chi tiết: `cat logs/metadata_discovery.log`
- Thử với từ khóa khác

## 🔍 Debug Mode

Để xem chi tiết hơn quá trình chạy, bật debug logging:

```bash
# Sửa file run_metadata_discovery.py
# Thay đổi dòng:
logging.basicConfig(level=logging.INFO, ...)

# Thành:
logging.basicConfig(level=logging.DEBUG, ...)
```

## 📝 Xác nhận hoàn thành BƯỚC 1

Checklist để xác nhận bước 1 hoàn thành:

- [ ] Script chạy thành công không lỗi
- [ ] Có file JSON trong `data/metadata/`
- [ ] Có file CSV trong `data/metadata/`
- [ ] File JSON chứa ít nhất 5-10 văn bản
- [ ] Các văn bản có metadata đầy đủ: title, doc_number, keywords
- [ ] Logs không có lỗi nghiêm trọng

## ➡️ Bước tiếp theo

Khi BƯỚC 1 hoàn thành và đã xác nhận kết quả OK, bạn có thể:

1. **Review metadata**: Xem xét các văn bản đã thu thập
2. **Báo cáo cho team**: Chia sẻ kết quả
3. **Chuẩn bị BƯỚC 2**: Crawl PDF files từ các URL đã thu thập được

---

## 🆘 Cần trợ giúp?

Nếu gặp vấn đề:

1. Kiểm tra logs: `logs/metadata_discovery.log`
2. Chạy tests: `python tests/test_text_processing.py`
3. Kiểm tra Python version: `python --version` (cần >= 3.9)
4. Kiểm tra pip packages: `pip list | grep langchain`

---

**Chúc bạn thành công! 🎉**
