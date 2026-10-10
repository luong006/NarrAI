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
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_ENABLED=true

# Tên checkpoint (Để trống để hệ thống tự động quét và chọn model anime/manga có sẵn)
COMFYUI_CHECKPOINT=

# Tham số sinh ảnh
COMFYUI_SAMPLER_NAME=euler
COMFYUI_SCHEDULER=normal
COMFYUI_STEPS=20
COMFYUI_CFG=7.0
COMFYUI_TIMEOUT=120
```

---

## 4. API Endpoints Quản Lý ComfyUI trong NarrAI

- **`GET /api/comic/comfyui/status`**: Kiểm tra kết nối, trạng thái server, danh sách model checkpoints hiện có trong ComfyUI.
- **`POST /api/comic/comfyui/test`**: Thử nghiệm sinh 1 khung tranh manga mẫu trực tiếp từ ComfyUI.
- **`GET /api/comic/image/{panel_id}`**: Sinh ảnh khung tranh tự động cho truyện tranh theo panel_id.

---

## 5. Lưu Ý Git
Các file model nặng (`*.safetensors`, `*.ckpt`) và ảnh render cache (`static/comic_cache/`) đã được cấu hình trong `.gitignore` để tránh đẩy file dung lượng lớn lên repository Git.
