# Law_in_Tech - Vietnam Government IT & Digital Transformation Crawler

Crawler chuyên biệt để thu thập dữ liệu từ các trang web chính phủ Việt Nam (.gov.vn) tập trung vào các chủ đề:
- Công nghệ thông tin (CNTT/ICT)
- Chuyển đổi số (Digital Transformation)
- Khoa học công nghệ (Science & Technology)

## Cấu hình đã được cập nhật

### 1. Domains được phép (config/allow_domains.json)
Chỉ crawl từ các trang .gov.vn chính thức:
- `chinhphu.vn` - Cổng thông tin Chính phủ
- `moj.gov.vn` - Bộ Tư pháp
- `mic.gov.vn` - Bộ Thông tin và Truyền thông
- `most.gov.vn` - Bộ Khoa học và Công nghệ
- `moit.gov.vn` - Bộ Công Thương
- `mpi.gov.vn` - Bộ Kế hoạch và Đầu tư
- `ega.gov.vn` - Cục Chính phủ điện tử
- `nsc.gov.vn` - Ủy ban An toàn thông tin quốc gia
- `csc.gov.vn` - Trung tâm Thông tin chỉ đạo điều hành
- `cca.gov.vn` - Cục Chứng thực số
- `nta.gov.vn` - Cơ quan Nhận dạng và Xác thực điện tử quốc gia
- `vnisa.gov.vn` - Hiệp hội An toàn thông tin Việt Nam
- `ncsc.gov.vn` - Trung tâm Ứng cứu khẩn cấp máy tính Việt Nam
- `dma.gov.vn` - Cục Quản lý dữ liệu
- `dga.gov.vn` - Cục Chính phủ số

### 2. Từ khóa mở rộng (config/keywords.txt)
358 từ khóa bao gồm:
- **Chuyển đổi số**: chuyển đổi số, chính phủ số, kinh tế số, xã hội số
- **Công nghệ thông tin**: CNTT, ICT, công nghệ thông tin, hạ tầng số
- **An toàn thông tin**: bảo mật, an ninh mạng, cybersecurity
- **AI & Machine Learning**: trí tuệ nhân tạo, học máy, artificial intelligence
- **Công nghệ mới**: blockchain, IoT, cloud computing, big data
- **Chính phủ điện tử**: e-government, dịch vụ công trực tuyến
- **Khoa học công nghệ**: innovation, startup, công nghiệp 4.0
- Và nhiều từ khóa khác...

### 3. URL Seeds (config/seeds.json)
22 URL khởi điểm từ các cơ quan chính phủ chính:
- Hệ thống văn bản pháp luật
- Dự thảo văn bản
- Các trang chủ của các bộ, ngành

### 4. URL Regex Patterns (config/url_allow_regex.json)
21 patterns regex để chỉ cho phép crawl từ các trang .gov.vn

## Cách sử dụng

### Test cấu hình
```bash
python3 test_config.py
```

### Chạy crawler (cần cài đặt crawl4ai)
```bash
python3 run_crawler.py
```

### Cài đặt dependencies
```bash
pip3 install -r requirements.txt
```

## Kết quả

Crawler sẽ lưu kết quả vào:
- `outputs/jsonl/` - Dữ liệu JSON Lines theo domain
- `outputs/pdf/` - File PDF và text được trích xuất

## Thống kê test

Với cấu hình mới:
- 20 domains được phép
- 358 từ khóa liên quan
- 22 URL seeds
- 21 URL regex patterns
- Tỷ lệ thành công test: ~60-80%

## Tính năng chính

1. **Chỉ crawl từ .gov.vn**: Đảm bảo nguồn dữ liệu chính thức
2. **Lọc theo từ khóa**: Chỉ thu thập nội dung liên quan đến IT/Digital
3. **Trích xuất PDF**: Tự động tải và trích xuất nội dung PDF
4. **Metadata đầy đủ**: Bao gồm ngày ban hành, số hiệu, trạng thái
5. **Deduplication**: Tránh trùng lặp dữ liệu

