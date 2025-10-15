# Hệ thống AI Agent Crawl Văn bản Pháp luật Việt Nam

Dự án xây dựng hệ thống AI Agent sử dụng LangGraph để crawl và phân tích văn bản pháp luật Việt Nam, tập trung vào các chính sách công nghệ và chuyển đổi số từ năm 2022 đến nay.

## 🎯 Mục tiêu

Thu thập dữ liệu về:
- Văn bản luật, nghị định, nghị quyết, quyết định, thông tư về công nghệ
- Các dự thảo và dự án luật đang lấy ý kiến
- Phản hồi và góp ý của người dùng về các văn bản pháp luật
- Tập trung: công nghệ, chuyển đổi số, AI, dữ liệu, an ninh mạng

## 🏗️ Cấu trúc Dự án

```
vietnamese-legal-crawler/
├── data/
│   ├── pdf_documents/      # Văn bản PDF gốc
│   └── text_documents/     # Văn bản text đã convert
├── logs/                   # Log files
├── src/
│   ├── agents/            # LangGraph AI agents
│   ├── crawlers/          # Crawl4AI crawlers
│   ├── utils/             # Utility functions
│   └── config.py          # Configuration
├── .env                   # Environment variables (không commit)
├── .env.example          # Template cho .env
├── requirements.txt      # Python dependencies
└── README.md
```

## 📋 Yêu cầu Hệ thống

- Python 3.10+
- pip hoặc conda
- Kết nối internet ổn định

## 🚀 Cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd vietnamese-legal-crawler
```

### Bước 2: Tạo virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Cài đặt Playwright browsers

```bash
playwright install
```

### Bước 5: Cấu hình API Key

1. Mở file `.env`
2. Thay thế `your_google_api_key_here` bằng Google API Key của bạn:

```
GOOGLE_API_KEY=AIzaSy...YOUR_ACTUAL_KEY_HERE
```

## 🌐 Nguồn Dữ liệu

Hệ thống crawl từ các nguồn uy tín:

### Nhóm 1: Chính phủ & Bộ ngành (Ưu tiên cao)
1. **Cổng Thông tin điện tử Chính phủ** - https://chinhphu.vn
2. **Hệ thống văn bản Chính phủ** - https://vanban.chinhphu.vn
3. **Bộ Thông tin và Truyền thông** - https://mic.gov.vn
4. **Bộ Khoa học và Công nghệ** - https://most.gov.vn

### Nhóm 2: Cơ sở dữ liệu pháp luật
5. **Luật Minh Khuê** - https://thuvienphapluat.vn
6. **LawNet** - https://lawnet.vn
7. **Công báo Chính phủ** - https://congbao.chinhphu.vn

### Nhóm 3: Trang lấy ý kiến dự thảo
8. **Dự thảo văn bản Chính phủ** - https://duthaovanban.chinhphu.vn

### Nhóm 4: Quốc hội
9. **Trang Quốc hội** - https://quochoi.vn

## 🔧 Cấu hình

Chỉnh sửa file `.env` để tùy chỉnh:

```env
# Tốc độ crawl
MAX_CONCURRENT_REQUESTS=3  # Số request đồng thời
REQUEST_DELAY=2            # Delay giữa các request (giây)

# Phạm vi thời gian
START_YEAR=2022
END_YEAR=2024
```

## 🎯 Từ khóa Tìm kiếm

Hệ thống lọc văn bản theo các từ khóa công nghệ:
- Công nghệ, chuyển đổi số, số hóa
- Trí tuệ nhân tạo, AI
- Dữ liệu, Big Data
- An toàn thông tin, an ninh mạng
- Internet, viễn thông, CNTT
- Blockchain, Cloud Computing, IoT
- Thương mại điện tử
- ...và nhiều từ khóa khác

## 📝 Loại Văn bản

Hệ thống thu thập:
- Nghị quyết
- Nghị định
- Quyết định
- Thông tư
- Chỉ thị
- Luật
- Dự thảo / Dự án luật

## 🏃 Chạy Hệ thống

### **🏛️ GOVERNMENT CRAWLER (KHUYẾN NGHỊ)**

Chỉ crawl từ các trang .gov.vn chính thức:

```bash
# Test nhanh (10 documents, 5 phút)
python3 run_government_crawl.py --max-docs 10

# Production (100 documents, 30 phút)
python3 run_government_crawl.py --max-docs 100 --source all

# Chỉ văn bản Chính phủ
python3 run_government_crawl.py --source vanban --max-docs 100

# Chỉ Bộ Số hóa (tech focus)
python3 run_government_crawl.py --source mst --max-docs 50
```

### **🤖 AI AGENT MODE**

Test với AI Agent:

```bash
# Test AI Agent
python3 test_ai_agent.py

# Sử dụng AI để phân tích
# (Requires Google API Key in .env)
```

### **📊 Export & Reports**

```bash
# Xem báo cáo
python3 tools/export_data.py --report

# Export JSON
python3 tools/export_data.py --tech-only --format json

# Export CSV
python3 tools/export_data.py --tech-only --format csv
```

## 📊 Output

- **PDF Documents**: `data/pdf_documents/`
- **Text Documents**: `data/text_documents/`
- **Logs**: `logs/`

## ⚠️ Lưu ý

1. **Tuân thủ robots.txt**: Hệ thống tôn trọng quy tắc crawl của các trang web
2. **Rate limiting**: Có delay giữa các request để tránh quá tải server
3. **Legal compliance**: Chỉ thu thập dữ liệu công khai, không vi phạm bản quyền
4. **API Key**: Không chia sẻ API key của bạn

## 🔄 Tiến độ Phát triển

- [x] Bước 1: Setup môi trường
- [ ] Bước 2: Xây dựng crawler cơ bản
- [ ] Bước 3: Tích hợp LangGraph AI Agent
- [ ] Bước 4: Thêm logic lọc thông minh
- [ ] Bước 5: Test và tinh chỉnh

## 📧 Liên hệ

Dự án phục vụ mục đích nghiên cứu và tọa đàm/tham luận.

---

**Phiên bản**: 0.1.0 (Đang phát triển)
**Ngày cập nhật**: 2025-10-14
