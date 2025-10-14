# 🚀 QUICK START - Chạy ngay BƯỚC 1

## ⚡ 3 Bước để chạy

### 1️⃣ Cấu hình Google API Key

```bash
# Mở file .env
nano .env
# hoặc
code .env
```

**Thay đổi dòng này:**
```
GOOGLE_API_KEY=your_google_api_key_here
```

**Thành API key thật của bạn:**
```
GOOGLE_API_KEY=AIzaSyAbc...xyz123
```

💡 **Lấy API key tại**: https://aistudio.google.com/app/apikey

---

### 2️⃣ Cài đặt dependencies

```bash
pip install -r requirements.txt
```

⏱️ **Thời gian**: ~2-3 phút

---

### 3️⃣ Chạy Agent

```bash
python run_metadata_discovery.py
```

⏱️ **Thời gian**: ~1-2 phút  
📊 **Output**: `data/metadata/*.json` và `*.csv`

---

## ✅ Kiểm tra kết quả

```bash
# Xem files đã tạo
ls -lh data/metadata/

# Xem nội dung JSON
cat data/metadata/*.json | python -m json.tool | head -50

# Xem CSV
cat data/metadata/*.csv
```

---

## 🆘 Nếu gặp lỗi

### ❌ "API key not configured"
→ Kiểm tra lại file `.env`

### ❌ "No module named 'langchain'"
→ Chạy: `pip install -r requirements.txt`

### ❌ "Request timeout"
→ Kiểm tra Internet, thử lại sau

---

## 📚 Đọc thêm

- **SETUP_GUIDE.md** - Hướng dẫn chi tiết
- **STEP1_SUMMARY.md** - Tổng kết BƯỚC 1
- **README.md** - Documentation đầy đủ

---

**Chúc bạn thành công! Sau khi chạy xong, báo cáo kết quả để chuyển sang BƯỚC 2! 🎉**
