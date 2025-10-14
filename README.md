# Law in Tech - Hệ thống Thu thập và Phân tích Văn bản Pháp luật về Công nghệ Số

## 📋 Tổng quan

Dự án này xây dựng một hệ thống tự động thu thập, phân tích văn bản pháp luật Việt Nam liên quan đến công nghệ số, chuyển đổi số và các chính sách thúc đẩy công nghệ. Hệ thống sử dụng AI Agent với **LangChain/LangGraph** và **Google Gemini** để tự động discovery và phân tích dữ liệu.

## 🎯 Mục tiêu

1. Thu thập có chọn lọc văn bản pháp luật Việt Nam về công nghệ, chuyển đổi số
2. Liên kết các cuộc thảo luận trên mạng với từng văn bản cụ thể
3. Phân tích cảm xúc/quan điểm và chủ đề thảo luận
4. Đưa ra khuyến nghị cho nhà hoạch định chính sách

## 🏗️ Kiến trúc hệ thống

### Pipeline tổng thể (9 bước)

1. **Discovery & Metadata** ✅ (BƯỚC HIỆN TẠI)
2. Bộ từ khóa & Bộ lọc
3. Crawler văn bản (PDF/HTML)
4. Chuyển đổi/Trích xuất
5. Lưu kho dữ liệu chuẩn hóa
6. Discovery thảo luận
7. Crawler thảo luận
8. NLP (cảm xúc, chủ đề, lập trường)
9. Báo cáo & Khuyến nghị

## 📦 Cài đặt

### Yêu cầu

- Python 3.9+
- Google API Key (cho Gemini)

### Bước 1: Clone và cài đặt dependencies

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt Playwright (cho web scraping nâng cao)
playwright install
```

### Bước 2: Cấu hình

1. Sao chép file `.env` và cập nhật API key:

```bash
# Mở file .env và thêm Google API Key của bạn
GOOGLE_API_KEY=your_actual_api_key_here
```

2. Xem và tùy chỉnh cấu hình (nếu cần):
   - `config/keywords.yaml` - Bộ từ khóa lọc
   - `config/sources.yaml` - Nguồn dữ liệu

## 🚀 Sử dụng

### BƯỚC 1: Discovery & Metadata (Hiện tại)

Chạy AI Agent để tự động tìm kiếm và trích xuất metadata từ vanban.chinhphu.vn:

```bash
# Chạy với cấu hình mặc định
python run_metadata_discovery.py

# Chạy với từ khóa tùy chỉnh
python run_metadata_discovery.py --keywords "AI" "blockchain" "dữ liệu cá nhân"

# Giới hạn số lượng văn bản
python run_metadata_discovery.py --max-documents 30
```

### Kết quả

Sau khi chạy xong, bạn sẽ có:

1. **Metadata JSON**: `data/metadata/metadata_vanban_chinhphu_YYYYMMDD_HHMMSS.json`
   - Chứa metadata đầy đủ của tất cả văn bản tìm được
   - Bao gồm: doc_id, title, doc_type, doc_number, issuer, dates, keywords, url

2. **Metadata CSV**: `data/metadata/metadata_vanban_chinhphu_YYYYMMDD_HHMMSS.csv`
   - Định dạng bảng để dễ xem và phân tích
   - Có thể mở bằng Excel/Google Sheets

3. **Logs**: `logs/metadata_discovery.log`
   - Chi tiết quá trình thực thi

## 📁 Cấu trúc dự án

```
Law_in_Tech/
├── config/                      # Cấu hình
│   ├── keywords.yaml           # Bộ từ khóa lọc
│   └── sources.yaml            # Nguồn dữ liệu
├── data/                        # Dữ liệu
│   ├── metadata/               # Metadata văn bản
│   ├── raw/                    # Dữ liệu thô
│   │   ├── pdfs/              # PDF files
│   │   └── html/              # HTML files
│   ├── processed/             # Dữ liệu đã xử lý
│   │   ├── docs/              # Văn bản đã parse
│   │   └── discussions/       # Thảo luận
│   ├── index/                 # Indexes & embeddings
│   └── database/              # SQLite database
├── logs/                       # Log files
├── src/                        # Source code
│   ├── agents/                # LangGraph agents
│   │   └── metadata_agent.py # Metadata discovery agent
│   ├── config/                # Config management
│   ├── tools/                 # LangGraph tools
│   │   └── web_scraper.py    # Web scraping tools
│   └── utils/                 # Utilities
│       └── text_processing.py # Vietnamese text processing
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── run_metadata_discovery.py  # Main script
```

## 🤖 AI Agent Architecture

### LangGraph Workflow

```
[Initialize] 
    ↓
[Search Documents] → vanban.chinhphu.vn
    ↓
[Analyze Results] → Gemini AI phân tích
    ↓
[Extract Metadata] → Trích xuất thông tin cấu trúc
    ↓
[Filter Relevant] → Lọc văn bản liên quan
    ↓
[Save Metadata] → Lưu JSON + CSV
    ↓
[END]
```

### Tools

- `fetch_webpage`: Tải nội dung trang web
- `search_vanban_chinhphu`: Tìm kiếm văn bản
- `extract_document_metadata`: Trích xuất metadata
- `filter_relevant_documents`: Lọc văn bản liên quan

## 🔑 Các tính năng chính

### Bước 1 (Hiện tại) - Metadata Discovery

- ✅ Tự động tìm kiếm văn bản từ vanban.chinhphu.vn
- ✅ Trích xuất metadata: tiêu đề, số hiệu, loại văn bản, ngày ban hành
- ✅ Lọc theo từ khóa công nghệ số (AI, blockchain, dữ liệu cá nhân, IoT...)
- ✅ AI Agent sử dụng Gemini để phân tích kết quả
- ✅ Xuất kết quả ra JSON và CSV

### Các bước tiếp theo (Đang phát triển)

- ⏳ Crawl PDF files
- ⏳ Convert PDF to text với OCR
- ⏳ Crawl thảo luận từ báo chí, diễn đàn
- ⏳ Sentiment analysis (PhoBERT)
- ⏳ Topic modeling (BERTopic)
- ⏳ Dashboard & báo cáo

## 🔍 Nguồn dữ liệu

### Văn bản pháp luật (Ưu tiên)

- ✅ **vanban.chinhphu.vn** - Cổng thông tin điện tử Chính phủ
- ⏳ vbpl.vn - Cơ sở dữ liệu văn bản pháp luật
- ⏳ mic.gov.vn - Bộ Thông tin và Truyền thông
- ⏳ quochoi.vn - Quốc hội
- ⏳ moj.gov.vn - Bộ Tư pháp

### Thảo luận (Bước sau)

- VnExpress, Tuổi Trẻ, Thanh Niên
- Diễn đàn chuyên ngành
- duthaoonline.quochoi.vn

## 📊 Ví dụ Output

### Metadata JSON

```json
{
  "metadata": {
    "source": "vanban_chinhphu",
    "crawl_timestamp": "2025-10-13T10:30:00",
    "total_discovered": 45,
    "total_relevant": 23
  },
  "documents": [
    {
      "doc_id": "vanban_chinhphu_abc12345",
      "title": "Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân",
      "doc_type": "Nghị định",
      "doc_number": "13/2023/NĐ-CP",
      "issuer": "Chính phủ",
      "issue_date": "2023-06-17",
      "keywords": ["dữ liệu cá nhân", "bảo vệ dữ liệu", "quyền riêng tư"],
      "url": "https://vanban.chinhphu.vn/..."
    }
  ]
}
```

## 🛠️ Công nghệ sử dụng

- **LangChain/LangGraph**: Orchestration cho AI Agent
- **Google Gemini**: LLM cho phân tích và decision-making
- **BeautifulSoup + Scrapy**: Web scraping
- **Pandas**: Data processing
- **PyYAML**: Configuration management

## 📝 Ghi chú quan trọng

1. **API Key**: Đảm bảo đã cấu hình `GOOGLE_API_KEY` trong file `.env`
2. **Rate Limiting**: Hệ thống tôn trọng `robots.txt` và có delay giữa các requests
3. **Tuân thủ pháp luật**: Chỉ thu thập dữ liệu công khai, không vi phạm bản quyền

## 🐛 Debug

Nếu gặp lỗi:

1. Kiểm tra logs: `logs/metadata_discovery.log`
2. Verify API key: `cat .env | grep GOOGLE_API_KEY`
3. Kiểm tra kết nối mạng
4. Đảm bảo đã cài đủ dependencies: `pip install -r requirements.txt`

## 📮 Liên hệ & Hỗ trợ

Nếu có vấn đề hoặc câu hỏi, vui lòng tạo issue hoặc liên hệ team phát triển.

---

**Version**: 0.1.0 (Bước 1 - Metadata Discovery)
**Last Updated**: 2025-10-13
