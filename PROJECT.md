# project.md — Tổng quan dự án NarrAI

> Tài liệu bối cảnh cho cả con người và AI agent. Tổng hợp từ README của dự án. Xem `agent.md` để biết quy tắc làm việc.

## 1. Giới thiệu

- **Tên dự án**: NarrAI — Nền tảng đồng sáng tác văn học và mạng xã hội truyện AI thế hệ mới.
- **Mô tả**: Hệ sinh thái AI giúp tác giả trẻ chấp bút tiểu thuyết, kịch bản và truyện tranh Manga, kết hợp mạng xã hội văn học và cơ chế bảo vệ lịch sử dân tộc Việt Nam cùng bản quyền IP.
- **Bối cảnh**: Sản phẩm dự thi **iStartup 2026** (Cuộc thi Khởi nghiệp Đổi mới Sáng tạo).
- **Đội thi**: Những ngôi sao mộng mơ, Trường Quốc tế – ĐHQGHN (VNU-IS).
- **Phiên bản**: v3.0 (Production). **Trạng thái kiểm thử**: 203/203 test pass.

## 2. Vấn đề & giá trị

- **Vấn đề**: Tác giả trẻ thường cạn ý tưởng và gặp rào cản khi viết lách.
- **Giải pháp**: Đội ngũ Multi-Agent AI phối hợp từ phỏng vấn ý tưởng → viết truyện → biên tập → chuyển thể Manga, kèm cộng đồng đọc và thảo luận.
- **Điểm khác biệt**:
  - Bảo vệ lịch sử dân tộc (31 anh hùng) và gắn nhãn bản quyền cho tác phẩm phái sinh.
  - Edge AI: gợi ý bảng tin chạy ngay trên trình duyệt bằng TensorFlow.js, giảm chi phí backend.
  - Độ sẵn sàng cao nhờ ma trận dự phòng nhiều model và nhiều API key.

## 3. Đối tượng người dùng

| Nhóm | Nhu cầu |
|---|---|
| Tác giả trẻ, người viết truyện | Có ý tưởng, bản thảo, công cụ biên tập và chuyển thể |
| Độc giả | Khám phá, theo dõi tác giả, bình luận, lưu tủ sách |
| Người làm truyện tranh | Biến bản thảo thành kịch bản Manga có panel, lời thoại, prompt ảnh |

## 4. Tính năng chính

### 4.1 Bốn agent AI

| Agent | File | Nhiệm vụ cốt lõi |
|---|---|---|
| 1. Q&A Intake Refiner | `qa_refiner.py` | Phỏng vấn ý tưởng kiểu chat; Dual-Matrix Fallback (Qwen 2.5 27B → Llama-3.3-70B → Llama-3.1-8B qua 3 API key); Concept Mirroring Prompt |
| 2. Story Generator | `story_generator.py` | Viết tiểu thuyết theo 5 nhịp kịch tính; nhiều thể loại; cổng chặn xuyên tạc lịch sử |
| 3. Copilot | `copilot_agent.py` | Live Editor; sửa chính xác đoạn `selectedText`; HeadingPreservationEngine giữ mốc `## Chương X` |
| 4. Comic Director | `comic_agent.py` | Chuyển bản thảo thành kịch bản Manga: panel, lời thoại, prompt sinh ảnh |

**Thể loại hỗ trợ**: Lịch sử/Dã sử, Kỳ ảo/Tu chân, Đô thị/Chữa lành, Sci-Fi/Cyberpunk, Trinh thám/Giật gân.

**Năm nhịp kịch tính**: Hook → Rising Friction → Turning Point → Visceral Climax → Cliffhanger.

### 4.2 Bảo vệ lịch sử & IP
- Bảo hộ 31 Anh hùng Dân tộc (ví dụ: Ngô Quyền, Hai Bà Trưng, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Nguyễn Huệ – Quang Trung, Hồ Chí Minh, Võ Nguyên Giáp).
- AI Semantic Classifier chặn xuyên tạc chiến công hoặc đảo niên đại, kể cả khi người dùng lách từ ngữ.
- Ba chế độ tự nhận diện: **Chính sử**, **Dã sử**, **Hư cấu tự do**.
- Tự nhận diện thương hiệu bản quyền thương mại và gắn disclaimer cho fanfiction.

### 4.3 Mạng xã hội văn học
- Community Feed: khám phá, lọc theo thể loại, tìm kiếm.
- Follow/Unfollow tác giả; bình luận phân cấp (threaded).
- Tủ sách cá nhân (Bookmarks) có phân loại.
- Leaderboard/Trending theo tuần và tháng.
- Trình đọc: truyện chữ và Manga fullscreen lật trang.
- Hệ thống tiền tệ **Xu** (`banking_service.py`), nhắn tin nội bộ (`messenger_router.py`), xuất bản thảo `.txt`, `.md`, `.pdf` (`export_router.py`).

### 4.4 Tối ưu hiệu năng
- TensorFlow.js Hybrid: gợi ý cá nhân hóa phía client, cache IndexedDB ≤ 15MB.
- SQLite WAL mode + composite indexes.
- GZip middleware cho API.

## 5. Công nghệ

| Lớp | Công nghệ |
|---|---|
| Frontend | Next.js 14.2 (React), TypeScript, Tailwind CSS, TensorFlow.js |
| Backend | Python (3.11 / 3.12), FastAPI 0.110+ |
| Cơ sở dữ liệu | SQLite (WAL mode) |
| LLM | Groq Cloud: Qwen 2.5 27B, Llama 3.3 70B Versatile, Llama 3.1 8B Instant |
| Xác thực | JWT |
| Triển khai | Backend: Render · Frontend: Vercel |

## 6. Kiến trúc

```
Frontend (Next.js + TF.js)
  ├─ Intake Chat · Live Editor · Manga Viewer · Social · Edge Recommender
  ▼ REST / Stream
Backend (FastAPI + Auth Middleware)
  ├─ QARefiner · StoryGenerator · CopilotAgent · ComicAgent
  ├─ Routers: social, messenger, export
  ├─ Services: banking, cache, recommender
  ▼
Groq Cloud (Qwen 2.5 27B / Llama 3.3 70B / Llama 3.1 8B)   +   SQLite WAL
```

### Luồng sáng tác điển hình
1. Tác giả trò chuyện với Agent 1 để làm rõ ý tưởng.
2. Agent 2 sinh bản thảo (qua cổng kiểm tra lịch sử/IP).
3. Tác giả chỉnh sửa trong Live Editor với Agent 3 (sửa theo vùng bôi đen).
4. Agent 4 chuyển thể thành kịch bản Manga.
5. Xuất bản lên cộng đồng; độc giả đọc, bình luận, theo dõi; bảng tin được cá nhân hóa bằng TF.js.

## 7. Cấu trúc thư mục (rút gọn)

```
NarrAI/
├── backend/
│   ├── agents/      # qa_refiner, story_generator, copilot_agent, comic_agent
│   ├── db/          # database.py (WAL), models.py
│   ├── llm/         # groq_client.py
│   ├── routers/     # social, messenger, export
│   ├── services/    # banking, cache, recommender
│   ├── tests/       # run_all_tests.py + các suite
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/         # layout.tsx, page.tsx
│       ├── components/  # setup, editor, comic, social, landing, layout
│       ├── services/    # tfjsRecommender.ts, indexedDBCache.ts
│       └── lib/         # api.ts, i18n.ts, types.ts
├── agent.md
├── project.md
└── README.md
```

## 8. Thiết lập môi trường

**Yêu cầu**: Python ≥ 3.10 (khuyên 3.11/3.12), Node.js ≥ 18, Groq API key (đăng ký tại console.groq.com).

**Biến môi trường backend** (`backend/.env`):

| Biến | Mô tả |
|---|---|
| `GROQ_API_KEY` | Key Groq chung |
| `GROQ_API_KEY_BIBLE` | Key cho luồng sinh truyện/bible |
| `GROQ_API_KEY_COPILOT` | Key cho Copilot |
| `GROQ_API_KEY_COMIC` | Key cho Comic Director |
| `JWT_SECRET` | Khóa ký JWT (đặt giá trị mạnh, không commit) |
| `NARRAI_MODERATOR_USERNAMES` | Danh sách username kiểm duyệt, phân tách bằng dấu phẩy |
| `DATABASE_URL` | Mặc định `sqlite:///./narrai.db` |

**Frontend** (`frontend/.env.local`): `NEXT_PUBLIC_API_URL=http://localhost:8000/api`

**Chạy**: backend `python main.py` (cổng 8000, Swagger tại `/docs`); frontend `npm run dev` (cổng 3000). Chi tiết lệnh xem `agent.md`.

## 9. Kiểm thử & chất lượng

| Nhóm | Kết quả |
|---|---|
| Core E2E | 111/111 |
| Round 5 Integration | 71/71 |
| Round 7 AI Resilience & Fallback | 21/21 |
| **Tổng** | **203/203** |

Frontend: `npm run build` thành công, 0 lỗi TypeScript.

## 10. Triển khai

- **Backend (Render)**: Web Service; build `pip install -r backend/requirements.txt`; start `cd backend && python main.py`.
- **Frontend (Vercel)**: Root Directory `frontend`; build `npm run build`; Output Directory để mặc định (Vercel tự động nhận diện `.next`); biến môi trường: `NEXT_PUBLIC_API_URL=https://<render-url>/api`.

## 11. Thuật ngữ

| Thuật ngữ | Ý nghĩa |
|---|---|
| Multi-Agent | Nhiều agent AI chuyên trách, phối hợp theo quy trình sáng tác |
| Dual-Matrix Fallback | Tự động chuyển model/API key khi lỗi hoặc quá giới hạn |
| Concept Mirroring | Kỹ thuật prompt phản chiếu từ khóa của tác giả để hỏi ngược |
| Chính sử / Dã sử / Hư cấu tự do | Ba chế độ sáng tác, mức ràng buộc lịch sử giảm dần |
| HeadingPreservationEngine | Cơ chế giữ nguyên các mốc chương khi biên tập |
| Xu | Đơn vị tiền tệ nội bộ của nền tảng |
| Edge AI | Mô hình gợi ý chạy ngay trên trình duyệt |

## 12. Đã xác minh & Chuẩn hóa kỹ thuật (Technical Standards)

Toàn bộ 5 điểm nghi vấn kỹ thuật đã được đối soát trực tiếp với mã nguồn và chuẩn hóa thống nhất:

1. **Phiên bản Python**: Chuẩn hóa toàn hệ thống yêu cầu `Python ≥ 3.10` (khuyên dùng Python 3.11 hoặc 3.12 trên môi trường máy chủ production).
2. **Mô hình AI**: Sử dụng tên dòng mô hình thân thiện trong tài liệu (Qwen, Llama 3.3 70B, Llama 3.1 8B, GPT-OSS); cơ chế Dual-Matrix Fallback trong `qa_refiner.py` tự động luân chuyển giữa các dòng mô hình này.
3. **Lệnh khởi chạy Render**: Thống nhất dùng lệnh `cd backend && python main.py` (file `main.py` tự động lấy biến `$PORT` từ Render và kích hoạt `uvicorn`).
4. **Cấu hình bản dựng Vercel**: Trên Vercel, ứng dụng tự động chạy chế độ Next.js native (`next.config.mjs` tự động bỏ `output: 'export'` khi biến `VERCEL` tồn tại). Để trống mục Output Directory trên Vercel Dashboard (mặc định `.next`).
5. **Bảo mật JWT**: Tệp mẫu `backend/.env.example` đã được tạo với giá trị placeholder an toàn; bổ sung cảnh báo không bao giờ sử dụng khóa mẫu trong môi trường Production.

## 13. Lộ trình gợi ý

Phần này chưa có trong README, bạn có thể điều chỉnh:

- Hoàn thiện sinh ảnh Manga từ prompt do Comic Director tạo.
- Mở rộng danh sách nhân vật/sự kiện lịch sử được bảo hộ.
- Tăng độ phủ test cho frontend.
- Theo dõi chi phí và rate limit Groq khi người dùng tăng.

## 14. Liên hệ

- **Team**: Những ngôi sao mộng mơ – VNU-IS
- **Bản quyền**: © 2026 NarrAI Team
