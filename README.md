# 🎵 Douyin Video Extractor & AI Filter

**Công cụ Desktop tự động tìm kiếm, phân tích nội dung AI, lọc video triệu view và trích xuất link tải Douyin (TikTok Trung Quốc) chất lượng cao không logo (HD No-Watermark).**

---

## ✨ Tính Năng Nổi Bật

### 1. 🧠 AI Studio - Phân Tích & Sinh Từ Khóa Douyin
- Nhập ý tưởng, tóm tắt video mẫu hoặc chủ đề bạn muốn làm.
- AI tự động phân tích và sinh ra **Bộ từ khóa tiếng Trung chuẩn SEO** kèm danh sách **Hashtag `#话题` xu hướng** tối ưu cho thuật toán đề xuất của Douyin.
- Hỗ trợ cả **Google Gemini API**, **OpenAI API** hoặc bộ quy tắc **Offline Heuristic Engine** có sẵn không cần internet/API.

### 2. 🔍 Tìm Kiếm & Bộ Lọc Nâng Cao (Smart Search & Filter)
- Quét nhanh hàng chục đến hàng trăm video Douyin theo từ khóa / hashtag.
- **Bộ lọc tương tác:** Lọc theo mốc Like (10K, 50K, 100K, 500K+ tim), số bình luận, lượt chia sẻ.
- **Bộ lọc thời gian:** Lọc theo 24 giờ qua, 7 ngày qua, 30 ngày qua hoặc toàn bộ.
- **Bộ lọc thời lượng:** Phân loại video ngắn (<1 phút), video vừa (1-3 phút), video dài (>3 phút).
- **Sắp xếp linh hoạt:** Sắp xếp theo video nhiều Like nhất, nhiều bình luận nhất hoặc mới nhất.

### 3. 📥 Trích Xuất Link HD Không Logo & Tải Hàng Loạt
- Bóc tách link tải trực tiếp **chất lượng cao 1080p/720p không dính logo mờ (No Watermark)**.
- Xuất toàn bộ dữ liệu ra file **Excel (.xlsx)** định dạng đẹp, **CSV**, **Text (.txt)**.
- Sao chép toàn bộ danh sách link chỉ với 1 click.
- Tải trực tiếp hàng loạt video về máy tính với cơ chế đa luồng tốc độ cao.

### 4. 🎨 Giao Diện Desktop Hiện Đại & Đóng Gói .EXE
- Giao diện Dark/Light mode hiện đại viết bằng **CustomTkinter**.
- Kèm script `build_exe.bat` đóng gói toàn bộ ứng dụng thành 1 file chạy `.exe` độc lập trên Windows.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### Cách 1: Chạy trực tiếp bằng Python
```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Khởi chạy ứng dụng
python main.py
```
Hoặc chỉ cần nhấp đúp chuột vào file **`run.bat`**.

### Cách 2: Đóng gói thành file chạy `.exe` cho Windows
Nhấp đúp chuột vào file **`build_exe.bat`**, chương trình sẽ tự động tạo file `DouyinVideoExtractor.exe` trong thư mục `dist/DouyinVideoExtractor/`.

---

## ⚙️ Cấu Hình Nâng Cao
Vào tab **Cài Đặt** trong ứng dụng để:
- **Douyin Cookie:** Dán cookie trình duyệt Douyin nếu bạn muốn quét sâu không bị giới hạn.
- **AI API Key:** Nhập Gemini API Key hoặc OpenAI Key để kích hoạt AI phân tích trực tiếp.
- **Thư mục tải:** Chọn thư mục lưu trữ video tải về trên máy tính.

---

## 👨‍💻 Tác giả & Giấy phép
- Dự án được phát triển và lưu trữ tại [khoathoiloi/douyin-video-extractor](https://github.com/khoathoiloi/douyin-video-extractor).
