# Douyin Content Finder (Web Application & AI Pipeline)

> **Hệ thống Web Application & AI Đa phương thức (Multimodal AI) tự động phân tích video, sinh 20 truy vấn tiếng Trung chuẩn thuật toán Douyin, quét và xếp hạng các video Douyin triệu view liên quan nhất.**

---

## 🌟 Tính Năng Cốt Lõi (Core Pipeline)

1. **Video Processing & Validation:**
   - Hỗ trợ tải lên video kéo-thả (Drag & Drop) định dạng `.mp4`, `.mov`, `.webm`, `.avi` lên đến 500MB.
   - Tự động trích xuất các khung hình đại diện (Keyframes) và tách Audio track bằng **FFmpeg**.

2. **Multimodal AI Analysis (ASR + OCR + Video Understanding):**
   - Bóc tách lời thoại (ASR) và chữ xuất hiện trên video (OCR).
   - Phân tích bối cảnh, nhân vật, hành động, phong cách hình ảnh và tone cảm xúc.
   - Xuất ra **Hồ sơ cấu trúc JSON (Structured Content Profile)** chuẩn 100% không hallucination.

3. **20 Chinese Douyin Search Queries & Query Expansion:**
   - Tự động sinh **20 truy vấn tiếng Trung** tự nhiên chuẩn người dùng Douyin tìm kiếm.
   - Phân loại vào 6 nhóm: `core_topic`, `people_or_objects`, `actions`, `scene`, `content_format`, `long_tail`.
   - Tự động sinh các biến thể ngữ nghĩa (Query Expansion) cho các từ khóa giá trị cao.

4. **Search Provider Abstraction & Multi-factor Ranking:**
   - Kiến trúc module độc lập `DouyinSearchProvider` (hỗ trợ cả Live Provider và Mock Provider).
   - Công thức xếp hạng đa tiêu chí:
     $$\text{Score} = 0.35 \times \text{Semantic} + 0.25 \times \text{Visual} + 0.15 \times \text{Keyword} + 0.10 \times \text{Hashtag} + 0.10 \times \text{Content Type} + 0.05 \times \text{Popularity}$$
   - LLM Reranking trên Top 30 ứng viên.
   - Khử trùng lặp video (Deduplication) dựa trên ID, URL và Title similarity.

5. **Giao diện Web SPA Hiện Đại & Async Job Engine:**
   - 4 Bước trực quan: Tải video $\rightarrow$ Xem hồ sơ AI $\rightarrow$ Quản lý/Bật tắt 20 từ khóa $\rightarrow$ Danh sách video Douyin kèm link xem trực tiếp.
   - Theo dõi tiến độ thời gian thực (Realtime Job Polling 0% - 100%).
   - Xuất kết quả ra file Excel / CSV hoặc sao chép toàn bộ link vào Clipboard.

---

## 🚀 Hướng Dẫn Khởi Động Nhanh

### Cách 1: Chạy Web Application bằng file 1-Click (Khuyên dùng)
Chỉ cần nhấp đúp chuột vào file:
```bash
run_web.bat
```
Sau đó mở trình duyệt (Chrome / Cốc Cốc / Edge) và truy cập:
👉 **`http://127.0.0.1:8000`**

---

### Cách 2: Chạy qua dòng lệnh (Command Line)
```bash
# 1. Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# 2. Khởi động Web Server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🔌 Danh Sách REST API Endpoints

- `POST /api/videos` — Tải lên video và tạo Job bất đồng bộ
- `GET /api/videos/{id}` — Lấy metadata video
- `GET /api/videos/{id}/analysis` — Lấy hồ sơ phân tích đa phương thức
- `GET /api/videos/{id}/queries` — Lấy 20 từ khóa tiếng Trung
- `POST /api/videos/{id}/queries/custom` — Thêm từ khóa tùy chỉnh
- `PATCH /api/videos/{id}/queries/{query_id}` — Bật/Tắt từ khóa
- `GET /api/videos/{id}/results` — Lấy danh sách video Douyin đã xếp hạng
- `POST /api/videos/{id}/process` — Kích hoạt lại pipeline tìm kiếm
- `GET /api/jobs/{job_id}` — Kiểm tra tiến độ xử lý realtime (0% - 100%)

---

## 🧪 Chạy Kiểm Thử (Unit & Integration Tests)

```bash
python -m unittest discover -s backend/tests -p "test_*.py"
```
