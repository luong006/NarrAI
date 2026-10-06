# Tổng quan dự án NarrAI

Tài liệu này tóm tắt mục tiêu sản phẩm, kiến trúc và trạng thái các tính năng chính. Quy tắc làm việc dành cho agent được lưu trong `agent.md`.

## 1. Giới thiệu

- **Tên dự án**: NarrAI — Nền tảng đồng sáng tác văn học và mạng xã hội truyện AI thế hệ mới.
- **Mô tả**: Hệ sinh thái AI giúp tác giả trẻ chấp bút tiểu thuyết, kịch bản và truyện tranh Manga, kết hợp mạng xã hội văn học và cơ chế bảo vệ lịch sử dân tộc Việt Nam cùng bản quyền IP.
- **Bối cảnh**: Sản phẩm dự thi **iStartup 2026** (Cuộc thi Khởi nghiệp Đổi mới Sáng tạo).
- **Đội thi**: Những ngôi sao mộng mơ, Trường Quốc tế – ĐHQGHN (VNU-IS).
- **Trạng thái**: Đang phát triển. Kết quả kiểm thử phụ thuộc vào từng bộ test; xem mục 9.

## 2. Vấn đề & giá trị

- **Vấn đề**: Tác giả trẻ thường cạn ý tưởng và gặp rào cản khi viết lách.
- **Giải pháp**: Đội ngũ Multi-Agent AI phối hợp từ phỏng vấn ý tưởng → viết truyện → biên tập → chuyển thể Manga, kèm cộng đồng đọc và thảo luận.
- **Điểm khác biệt**:
  - Bảo vệ lịch sử dân tộc (31 anh hùng) và gắn nhãn bản quyền cho tác phẩm phái sinh.
  - Edge AI: gợi ý bảng tin chạy ngay trên trình duyệt bằng TensorFlow.js, giảm chi phí backend.
  - Dự phòng model và API key giúp xử lý một số lỗi hoặc giới hạn từ nhà cung cấp.

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
| 1. Q&A Intake Refiner | `qa_refiner.py` | Phỏng vấn ý tưởng; chuyển model hoặc API key khi cần; làm rõ ý tưởng bằng câu hỏi dựa trên nội dung người viết |
| 2. Story Generator | `story_generator.py` | Viết truyện theo 5 nhịp kịch tính; nhiều thể loại; kiểm tra nội dung lịch sử; lưu bản nháp khi luồng sinh bị gián đoạn |
| 3. Copilot | `copilot_agent.py` | Live Editor; sửa chính xác đoạn `selectedText`; HeadingPreservationEngine giữ mốc `## Chương X` |
| 4. Comic Director | `comic_agent.py` | Chuyển bản thảo thành kịch bản Manga; duy trì thông tin nhân vật và bối cảnh; hỗ trợ tải lại ảnh lỗi |

**Thể loại hỗ trợ**: Lịch sử/Dã sử, Kỳ ảo/Tu chân, Đô thị/Chữa lành, Sci-Fi/Cyberpunk, Trinh thám/Giật gân.

**Năm nhịp kịch tính**: Hook → Rising Friction → Turning Point → Visceral Climax → Cliffhanger.

### 4.2 Bảo vệ lịch sử & IP
- Bảo hộ 31 Anh hùng Dân tộc (ví dụ: Ngô Quyền, Hai Bà Trưng, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Nguyễn Huệ – Quang Trung, Hồ Chí Minh, Võ Nguyên Giáp).
- Bộ kiểm tra phát hiện một số dạng xuyên tạc chiến công hoặc đảo ngược kết quả trận chiến. Quy tắc nhận diện chuẩn hóa dấu để xử lý cả văn bản tiếng Việt không dấu.
- Ba chế độ tự nhận diện: **Chính sử**, **Dã sử**, **Hư cấu tự do**.
- Tự nhận diện thương hiệu bản quyền thương mại và gắn disclaimer cho fanfiction.

### 4.3 Mạng xã hội văn học
- Community Feed: bảng tin đề xuất và theo dõi, tìm kiếm, lọc nhiều thể loại và tải thêm nội dung.
- Chia sẻ liên kết tác phẩm, thích và theo dõi tác giả; hỗ trợ đề xuất và xu hướng.
- Follow/Unfollow tác giả; bình luận phân cấp (threaded).
- Tủ sách cá nhân (Bookmarks) có phân loại.
- Leaderboard/Trending theo tuần và tháng.
- Trình đọc: truyện chữ và Manga fullscreen lật trang.
- Hệ thống tiền tệ **Xu** (`banking_service.py`), nhắn tin nội bộ (`messenger_router.py`), xuất bản thảo `.txt`, `.md`, `.pdf` (`export_router.py`).
- Nạp Xu đang ở chế độ demo MVP và chưa yêu cầu xác minh giao dịch.

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
├── PROJECT.md
├── PRODUCT.md
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

## 9. Kiểm thử và xác minh

Các kiểm thử hồi quy gần đây đã chạy thành công:

| Phạm vi | Kết quả |
|---|---|
| Bộ backend tích hợp (`run_all_tests.py`) | 204 test đạt |
| Lịch sử và chế độ sáng tác (3 bộ test) | 57 test đạt |
| Truyện tranh | 69 test đạt |
| Mạng xã hội (2 bộ test) | 92 test đạt |
| Tiếp tục luồng sinh truyện | 3 test đạt |
| Frontend | `npm run build` thành công |

Đây là kết quả kiểm thử local; chúng không xác nhận thay đổi đã được triển khai lên production.

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

## 12. Lưu ý vận hành

- Python tối thiểu 3.10; khuyến nghị dùng Python 3.11 hoặc 3.12.
- Không dùng giá trị mẫu trong `.env.example` làm khóa bí mật production.
- Các thay đổi trên nhánh làm việc cần được triển khai riêng trước khi xác minh trên production.

## 13. Lộ trình gợi ý

- Tiếp tục cải thiện độ tin cậy tạo và tải ảnh Manga.
- Mở rộng danh sách nhân vật/sự kiện lịch sử được bảo hộ.
- Tăng độ phủ test cho frontend.
- Theo dõi chi phí và rate limit Groq khi người dùng tăng.

## 14. Liên hệ

- **Team**: Những ngôi sao mộng mơ – VNU-IS
- **Bản quyền**: © 2026 NarrAI Team
