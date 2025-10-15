# Law_in_Tech - Crawl Văn Bản Pháp Luật về Công Nghệ Thông Tin & Chuyển Đổi Số

Dự án crawl và thu thập văn bản pháp luật, chính sách từ các trang web chính phủ Việt Nam (.gov.vn), tập trung vào lĩnh vực:
- Công nghệ thông tin (CNTT)
- Chuyển đổi số
- Khoa học và công nghệ
- An toàn thông tin, an ninh mạng
- Chính phủ điện tử

## Nguồn dữ liệu

Dự án chỉ crawl từ các trang web chính thống của chính phủ Việt Nam (.gov.vn):

### Cơ quan Nhà nước
- **chinhphu.vn** - Cổng thông tin điện tử Chính phủ
- **mic.gov.vn** - Bộ Thông tin và Truyền thông
- **most.gov.vn** - Bộ Khoa học và Công nghệ  
- **moj.gov.vn** - Bộ Tư pháp
- **mpi.gov.vn** - Bộ Kế hoạch và Đầu tư

### Cơ quan chuyên ngành
- **ega.gov.vn** - Cục Chính phủ điện tử
- **cic.gov.vn** - Cục Tin học hóa
- **ncsc.gov.vn** - Trung tâm An ninh mạng quốc gia
- **bkav.gov.vn** - Cục An toàn thông tin

### Tổ chức Internet & Công nghệ
- **vnnic.vn** - Trung tâm Internet Việt Nam
- **vnisa.org.vn** - Hiệp hội An toàn thông tin Việt Nam

## Từ khóa tập trung

Hệ thống lọc các văn bản theo các từ khóa liên quan đến:
- Chuyển đổi số, Chính phủ số, Kinh tế số, Xã hội số
- Công nghệ thông tin, CNTT
- An toàn thông tin, An ninh mạng, Bảo mật
- AI, Trí tuệ nhân tạo
- Khoa học và công nghệ
- Dữ liệu mở, Big data, Điện toán đám mây
- Blockchain, IoT, 5G/6G
- Chữ ký số, Định danh điện tử, Giao dịch điện tử
- Đổi mới sáng tạo, Nghiên cứu khoa học
- Công nghiệp 4.0, Make in Vietnam
- Và nhiều từ khóa khác...

## Cài đặt

```bash
# Clone repository
git clone <repository-url>
cd Law_in_Tech

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\\Scripts\\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

## Cấu hình

Các file cấu hình trong thư mục `config/`:

- **seeds.json**: Danh sách URL khởi đầu để crawl
- **allow_domains.json**: Danh sách domain được phép crawl
- **url_allow_regex.json**: Regex patterns để lọc URL
- **keywords.txt**: Danh sách từ khóa để lọc nội dung

## Sử dụng

```bash
# Chạy crawler
python src/graph.py
```

Kết quả được lưu trong thư mục `outputs/`:
- `outputs/jsonl/`: Văn bản dạng JSONL theo domain
- `outputs/pdf/`: File PDF và nội dung trích xuất

## Cấu trúc dữ liệu

Mỗi văn bản được lưu với các trường:
- `url`: URL nguồn
- `source_site`: Trang web nguồn
- `doc_type`: Loại văn bản (VAN_BAN_PHAP_LUAT, DU_THAO, TIN_TUC)
- `tieu_de`: Tiêu đề
- `noi_dung_markdown`: Nội dung dạng Markdown
- `noi_dung_text`: Nội dung dạng text
- `so_hieu`: Số hiệu văn bản (nếu có)
- `ngay_ban_hanh`: Ngày ban hành
- `co_quan_ban_hanh`: Cơ quan ban hành
- `linh_vuc`: Các lĩnh vực liên quan
- `attachments`: File đính kèm (PDF, ...)
- `crawled_at`: Thời gian crawl
- `content_hash`: Hash để theo dõi thay đổi

## License

MIT
