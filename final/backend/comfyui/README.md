# 🎨 Hướng Dẫn Tích Hợp ComfyUI Tạo Tranh Truyện Tranh (Manga/Comic) trong NarrAI

Mô-đun này kết nối trực tiếp hệ thống **NarrAI** với **ComfyUI** cục bộ hoặc remote server để tự động tạo khung tranh truyện tranh trắng đen phong cách Manga chuyên nghiệp với độ phân giải cao và tính nhất quán hình ảnh nhân vật cao.

---

## 1. Kiến Trúc Hoạt Động

```
[Người dùng tạo Manga]
        │
        ▼
[ComicDirectorAgent] ──> Phân tích kịch bản & trích xuất DNA nhân vật / bối cảnh
        │
        ▼
[cloudflare_ai.py / comfyui_service.py]
        ├── 1. Kiểm tra ComfyUI (http://127.0.0.1:8188)
        │      ├── Nếu ON ──> Gửi prompt tới ComfyUI API (/prompt) ──> Nhận ảnh Manga
        │      └── Nếu OFF ─> Tự động Fallback về Cloudflare AI / Pollinations
        │
        ▼
[Xử lý Monochrome Pillow] ──> Khử màu, tối ưu độ tương phản nét mực G-pen
        │
        ▼
[Cache & Hiển thị trên Frontend ComicViewer]
```

---

## 2. Cài Đặt và Khởi Chạy ComfyUI

### Bước 1: Tải ComfyUI
Nếu chưa có ComfyUI, bạn có thể tải bản Portable hoặc cài bằng Git:
- **Tải ComfyUI Portable cho Windows:** [ComfyUI Releases](https://github.com/comfyanonymous/ComfyUI/releases)

### Bước 2: Tải Model Manga / Anime khuyên dùng
Đặt file model `.safetensors` vào thư mục `ComfyUI/models/checkpoints/`:
- **Khuyên dùng cho Manga SDXL:** `animagineXLV31_v31.safetensors` hoặc `sd_xl_base_1.0.safetensors`
- **Khuyên dùng cho Manga SD1.5:** `v1-5-pruned-emaonly.safetensors`, `anything-v5.0.safetensors`, hoặc `ghostmix_v20.safetensors`

### Bước 3: Chạy ComfyUI
Chạy ComfyUI với cổng mặc định `8188`:
```bash
python main.py --listen 127.0.0.1 --port 8188 --enable-cors-header
```

---

## 3. Cấu Hình Trong NarrAI (`backend/.env`)

Thêm các biến môi trường sau vào file `backend/.env`:

```env
# Kích hoạt ComfyUI
# Dùng cục bộ: COMFYUI_URL=http://127.0.0.1:8188
# Dùng qua Ngrok: COMFYUI_URL=https://your-subdomain.ngrok-free.app
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_ENABLED=true

# Tên checkpoint (Để trống để hệ thống tự động quét và chọn model anime/manga có sẵn)
COMFYUI_CHECKPOINT=

# Tham số sinh ảnh
COMFYUI_SAMPLER_NAME=euler
COMFYUI_SCHEDULER=normal
COMFYUI_STEPS=25
COMFYUI_CFG=7.5
COMFYUI_TIMEOUT=120
```

---

## 4. Hướng Dẫn Mở Tunnel Ngrok Kết Nối Vercel/Render với ComfyUI Desktop

Nếu bạn muốn deploy web lên **Vercel** (`narr-ai.vercel.app`) hoặc **Render** mà vẫn dùng ComfyUI trên máy bạn để tạo tranh:

1. **Khởi chạy ComfyUI Desktop** trên máy tính của bạn.
2. **Khởi chạy Ngrok:**
   * Cách 1: Chạy file `backend/comfyui/start_ngrok_tunnel.bat`
   * Cách 2: Mở terminal chạy lệnh:
     ```bash
     ngrok http 8188
     ```
3. **Sao chép URL Ngrok:** Lấy đường dẫn HTTPS (ví dụ `https://abc-123.ngrok-free.app`).
4. **Cài đặt biến môi trường:**
   * Trong file `backend/.env` hoặc trên Dashboard của **Render**:
     ```env
     COMFYUI_URL=https://abc-123.ngrok-free.app
     ```
   * NarrAI đã được cấu hình tự động bypass màn hình chặn của Ngrok (`ngrok-skip-browser-warning: 69420`) để truyền API mượt mà 100%.

---

## 5. API Endpoints Quản Lý ComfyUI trong NarrAI

- **`GET /api/comic/comfyui/status`**: Kiểm tra kết nối, trạng thái server, danh sách checkpoints và LoRAs hiện có.
- **`GET /api/comic/comfyui/loras`**: Liệt kê chi tiết các LoRA và từ khóa trigger phong cách.
- **`POST /api/comic/prompt-agent/generate`**: Sinh prompt manga chi tiết từ câu chuyện chữ.
- **`POST /api/comic/comfyui/test`**: Thử nghiệm sinh 1 khung tranh manga mẫu trực tiếp.
- **`GET /api/comic/image/{panel_id}`**: Sinh ảnh khung tranh tự động cho truyện tranh theo panel_id.

