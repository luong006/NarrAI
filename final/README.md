# NarrAI - Hướng Dẫn Triển Khai Mới (Render + Vercel + ComfyUI)

Thư mục `final/` là bản đóng gói hoàn chỉnh, độc lập và tối ưu nhất của toàn bộ hệ thống **NarrAI**.

---

## 📁 Cấu Trúc Thư Mục `final/`

```text
final/
├── backend/                  # FastAPI Backend Server + ComfyUI Agent & LoRAs
│   ├── agents/               # AI Prompt Agent & Comic Director
│   ├── comfyui/              # Workflows, LoRAs & Tunnels (ngrok / free tunnel)
│   ├── routers/              # API endpoints (Auth, Stories, Comics, Social, Coins, Messenger)
│   ├── services/             # ComfyUI Service, Groq LLM, Cloudflare AI, Recommender
│   ├── main.py               # Main Application Entrypoint
│   ├── requirements.txt      # Python Dependencies
│   └── .env.example          # Mẫu cấu hình môi trường Backend
├── frontend/                 # Next.js 14 Web UI (App Router + Tailwind CSS)
│   ├── src/                  # Components, Pages, State, Styles
│   ├── package.json          # Node.js Dependencies
│   └── .env.example          # Mẫu cấu hình môi trường Frontend
├── render.yaml               # Cấu hình Render Blueprint
└── README.md                 # Hướng dẫn này
```

---

## 🚀 Bước 1: Triển Khai Backend Lên Render (Web Service Mới)

1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com).
2. Nhấn **New +** → Chọn **Web Service**.
3. Chọn kho GitHub: `https://github.com/luong006/NarrAI.git`.
4. Điền các thông tin cài đặt:
   - **Name**: `narrai-backend` (hoặc tên tuỳ thích).
   - **Region**: Singapore (hoặc Oregon / Frankfurt).
   - **Branch**: `main`.
   - **Root Directory**: `final/backend` *(Rất quan trọng!)*
   - **Runtime**: `Python 3`.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`.
5. Trong mục **Environment Variables** (Biến môi trường), thêm các biến:
   - `GROQ_API_KEY`: Key Groq của bạn (lấy tại https://console.groq.com).
   - `JWT_SECRET`: Một chuỗi ngẫu nhiên bí mật (ví dụ: `narrai_secret_key_2026_super_safe`).
   - `COMFYUI_ENABLED`: `true`
   - `COMFYUI_URL`: Link ngrok ComfyUI của bạn (Ví dụ: `https://xxxx-xx-xx.ngrok-free.app` khi mở tunnel, hoặc tạm thời để `http://127.0.0.1:8188`).
   - `CLOUDFLARE_API_TOKEN`: *(Tuỳ chọn)* Token Cloudflare Workers AI.
   - `CLOUDFLARE_ACCOUNT_ID`: *(Tuỳ chọn)* Account ID Cloudflare.
6. Nhấn **Create Web Service**. Đợi 1-2 phút Render build xong và cấp cho bạn URL (Ví dụ: `https://narrai-backend-xxxx.onrender.com`).

---

## 🌐 Bước 2: Triển Khai Frontend Lên Vercel (Project Mới)

1. Đăng nhập vào [Vercel Dashboard](https://vercel.com).
2. Nhấn **Add New...** → **Project**.
3. Chọn kho GitHub: `luong006/NarrAI`.
4. Tại mục cấu hình dự án:
   - **Project Name**: `narrai-frontend` (hoặc tuỳ chọn).
   - **Framework Preset**: `Next.js`.
   - **Root Directory**: Nhấn nút **Edit** → Chọn thư mục `final/frontend` → Nhấn **Continue**.
5. Trong mục **Environment Variables**, thêm biến:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://<ten-backend-render-cua-ban>.onrender.com/api` *(Thêm `/api` ở đuôi)*
6. Nhấn **Deploy**. Vercel sẽ build và cung cấp domain chính thức (Ví dụ: `https://narrai-frontend.vercel.app`).

---

## 🎨 Bước 3: Kết Nối ComfyUI Cục Bộ (GPU LoRAs) Với Render Backend

Khi bạn muốn dùng GPU máy tính cục bộ để Render và Vercel gọi sinh tranh Manga bằng các LoRA Việt Nam:

1. Mở ComfyUI trên máy tính (`http://127.0.0.1:8188`).
2. Mở file `final/backend/comfyui/start_ngrok_tunnel.bat` (hoặc chạy lệnh terminal: `ngrok http 8188`).
3. Copy link Forwarding dạng `https://xxxx-xx-xx.ngrok-free.app`.
4. Vào Render Dashboard → Chọn Backend Service → Tab **Environment** → Sửa biến `COMFYUI_URL` thành link ngrok vừa copy → Nhấn **Save Changes**.
5. Render sẽ tự động kết nối trực tiếp với GPU ComfyUI cục bộ để sinh tranh theo thời gian thực!
