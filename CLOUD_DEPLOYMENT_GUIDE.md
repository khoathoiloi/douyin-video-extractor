# ☁️ HƯỚNG DẪN DEPLOY BACKEND LÊN CLOUD SERVER (ORACLE CLOUD FREE / VPS)

Tài liệu này hướng dẫn chi tiết cách triển khai Backend **Douyin Content Finder** lên máy chủ đám mây **Oracle Cloud Free Tier** (hoàn toàn miễn phí trọn đời) hoặc bất kỳ VPS Ubuntu/Debian nào, giúp hệ thống hoạt động 24/7 độc lập mà không cần mở máy tính cá nhân.

---

## 🏗️ 1. KIẾN TRÚC TRIỂN KHAI

```
Android App (Galaxy S9) / Web Browser
                  │
                  ▼ (HTTPS / Port 443)
┌─────────────────────────────────────────────────────────┐
│  Oracle Cloud Free Tier (Ubuntu VM)                     │
│                                                         │
│   ┌──────────────────────────────────────────────────┐  │
│   │ Nginx Reverse Proxy (SSL / Port 80, 443)         │  │
│   └───────────────────────┬──────────────────────────┘  │
│                           │ (HTTP / Port 8000)          │
│                           ▼                             │
│   ┌──────────────────────────────────────────────────┐  │
│   │ Docker Container: FastAPI Backend + AI Pipeline │  │
│   │ (FFmpeg, ASR, OCR, 20 Queries, SQLite Database)  │  │
│   └──────────────────────────────────────────────────┘  │
│                           │                             │
│                           ▼ (Volume Persistence)        │
│   ┌──────────────────────────────────────────────────┐  │
│   │ Host Storage: /data/app.db (Dữ liệu không mất)   │  │
│   └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 2. HƯỚNG DẪN 3 BƯỚC TRIỂN KHAI NHANH

### Bước 1: Tạo máy chủ Oracle Cloud Free Tier
1. Đăng ký tài khoản tại [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Vào mục **Compute** $\rightarrow$ **Instances** $\rightarrow$ **Create Instance**:
   * **Image:** Ubuntu 22.04 LTS hoặc 24.04 LTS.
   * **Shape:** 
     * Khuyên dùng: `VM.Standard.A1.Flex` (ARM Ampere: 4 OCPU, 24 GB RAM - Miễn phí).
     * Hoặc: `VM.Standard.E2.1.Micro` (AMD: 1 OCPU, 1 GB RAM - Miễn phí).
   * **SSH Keys:** Tải về private key (`.key`) để đăng nhập SSH.
3. Nhấn **Create** và chờ máy chủ cấp phát Public IP (VD: `140.238.12.34`).

---

### Bước 2: Mở Port Firewall trên Oracle Cloud Console
Mặc định Oracle Cloud chặn tất cả các cổng ngoài SSH (22). Cần mở cổng 80, 443 và 8000:
1. Trên trang chi tiết Instance, nhấn vào **Virtual Cloud Network (VCN)**.
2. Chọn **Security Lists** $\rightarrow$ **Default Security List for...**.
3. Nhấn **Add Ingress Rules** và thêm 3 rule sau:
   * **Source CIDR:** `0.0.0.0/0`
   * **IP Protocol:** `TCP`
   * **Destination Port Range:** `80, 443, 8000`
4. Nhấn **Add Ingress Rules**.

---

### Bước 3: Chạy Script Tự Động Triển Khai (1 Dòng Lệnh)
Đăng nhập SSH vào máy chủ từ Terminal / PowerShell:
```bash
ssh -i /duong-dan/private.key ubuntu@<PUBLIC_IP>
```

Sau khi đăng nhập, clone dự án và chạy script:
```bash
git clone https://github.com/khoathoiloi/douyin-video-extractor.git
cd douyin-video-extractor
sudo bash deploy.sh
```

> **Script sẽ tự động:**
> 1. Cài đặt Docker & Docker Compose mới nhất.
> 2. Cấu hình UFW Firewall và iptables mở cổng 80, 443, 8000.
> 3. Tạo thư mục lưu trữ dữ liệu vĩnh viễn (`/data`, `/uploads`).
> 4. Thiết lập dịch vụ Docker khởi động cùng hệ thống (`systemctl enable docker`).
> 5. Build và khởi chạy Docker container với 4 workers.

---

## 🔒 3. CẤU HÌNH DOMAIN & HTTPS (SSL MIỄN PHÍ)

### Cách 1: Sử dụng Tên Miền Riêng + Certbot Let's Encrypt
1. Trỏ bản ghi **A Record** của Domain về Public IP của máy chủ:
   * `api.yourdomain.com` $\rightarrow$ `140.238.12.34`
2. Trên máy chủ, cập nhật file `.env`:
   ```bash
   DOMAIN_NAME="api.yourdomain.com"
   ADMIN_EMAIL="admin@yourdomain.com"
   ```
3. Chạy lại script deploy để tự động lấy chứng chỉ SSL:
   ```bash
   sudo DOMAIN_NAME="api.yourdomain.com" bash deploy.sh
   ```
4. Khi đó API sẽ chạy an toàn tại: **`https://api.yourdomain.com/api/v1/search`**

---

### Cách 2: Sử dụng Cloudflare Proxy (Bật SSL Miễn Phí Ngay Lập Tức)
1. Thêm Domain vào Cloudflare.
2. Tạo bản ghi A: `api` trỏ về IP máy chủ, bật đám mây **Proxied (Màu cam)**.
3. Trong Cloudflare SSL/TLS, chọn chế độ **Flexible** hoặc **Full**.
4. Truy cập ngay lập tức qua HTTPS: **`https://api.yourdomain.com`**.

---

## 🔄 4. TỰ ĐỘNG KHỞI ĐỘNG LẠI SAU KHI REBOOT SERVER

Hệ thống đã được cấu hình cờ `restart: unless-stopped` trong `docker-compose.yml` và kích hoạt dịch vụ `docker.service` trên hệ điều hành.

**Kiểm tra tính năng Auto-Restart:**
1. Thử khởi động lại server:
   ```bash
   sudo reboot
   ```
2. Chờ 1 phút, kiểm tra trạng thái container:
   ```bash
   docker compose ps
   ```
   *Cả 3 container (`douyin_backend`, `douyin_nginx`, `douyin_certbot`) sẽ tự động chạy lại mà không cần bất kỳ can thiệp thủ công nào.*

---

## 📱 5. KẾT NỐI APP GALAXY S9 VÀO CLOUD BACKEND

1. Mở ứng dụng **Douyin Search** trên điện thoại Samsung Galaxy S9.
2. Vào tab **Cài đặt (Settings)** ở thanh điều hướng dưới.
3. Nhập địa chỉ Server Cloud của bạn:
   * Nếu dùng Domain HTTPS: `https://api.yourdomain.com`
   * Nếu dùng IP trực tiếp: `http://140.238.12.34:8000`
4. Nhấn **Lưu cấu hình**.
5. **Hoàn tất!** Giờ đây bạn có thể tắt máy tính hoàn toàn, ứng dụng Android vẫn tìm kiếm và phân tích video Douyin 24/7 từ bất kỳ đâu qua Wi-Fi hoặc 4G/5G.
