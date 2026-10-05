# agent.md — Hướng dẫn cho AI Agent làm việc trong repo NarrAI

> Đọc file này và `project.md` trước khi sửa bất kỳ thứ gì. Đây là các quy tắc bắt buộc khi viết code, sửa lỗi hoặc thêm tính năng cho NarrAI.

## 1. Vai trò

Bạn là kỹ sư full-stack hỗ trợ dự án **NarrAI** (FastAPI + Next.js 14 + TensorFlow.js). Ưu tiên:

1. Không làm hỏng 4 agent AI, hệ thống bảo vệ lịch sử và bộ test hiện có.
2. Thay đổi nhỏ, đúng phạm vi, dễ review.
3. Tuân thủ quy ước đã có trong repo, không tự áp phong cách mới.

## 2. Bản đồ repo (nơi nào làm gì)

| Cần sửa | Đi tới |
|---|---|
| Phỏng vấn ý tưởng, fallback model | `backend/agents/qa_refiner.py` |
| Sinh truyện, bảo vệ lịch sử, 3 chế độ sáng tác | `backend/agents/story_generator.py` |
| Biên tập bản thảo, `selectedText`, giữ tiêu đề chương | `backend/agents/copilot_agent.py` |
| Chuyển thể Manga (panel, lời thoại, prompt ảnh) | `backend/agents/comic_agent.py` |
| Gọi Groq, token budget, retry | `backend/llm/groq_client.py` |
| Schema DB, kết nối SQLite | `backend/db/models.py`, `backend/db/database.py` |
| API xã hội, nhắn tin, xuất file | `backend/routers/*.py` |
| Xu, cache, vector gợi ý | `backend/services/*.py` |
| Giao diện chat, editor, comic, feed | `frontend/src/components/**` |
| Gợi ý phía client | `frontend/src/services/tfjsRecommender.ts`, `indexedDBCache.ts` |
| API client, i18n, types | `frontend/src/lib/api.ts`, `i18n.ts`, `types.ts` |

## 3. Quy tắc bất khả xâm phạm (Hard rules)

### 3.1 Bảo vệ lịch sử dân tộc & IP
- **Không** làm yếu, bỏ qua hoặc vòng qua bộ chặn xuyên tạc lịch sử (danh sách 31 anh hùng dân tộc và AI Semantic Classifier trong `story_generator.py`).
- Giữ nguyên hành vi 3 chế độ: *Chính sử* (bảo toàn 100% sự kiện, nhân vật), *Dã sử* (cho phép nhân vật hư cấu trong bối cảnh thật), *Hư cấu tự do*. Logic auto-detect không được đổi hành vi mặc định mà không có test.
- Giữ cơ chế nhận diện thương hiệu bản quyền và gắn disclaimer cho fanfiction.
- Khi thêm prompt hoặc luồng sinh nội dung mới, phải đi qua cùng cổng kiểm tra lịch sử/IP.

### 3.2 Copilot (Agent 3)
- Với yêu cầu có `selectedText`: **chỉ** sửa đúng vùng được chọn, giữ nguyên phần còn lại của bản thảo.
- **HeadingPreservationEngine**: thứ tự và vị trí các mốc `## Chương X` phải được bảo toàn tuyệt đối. Mọi thay đổi ở Copilot phải được kiểm tra bằng test về tiêu đề chương.

### 3.3 Độ bền LLM (Agent 1 và `groq_client.py`)
- Giữ chuỗi fallback: `Qwen 2.5 27B` → `Llama-3.3-70B` → `Llama-3.1-8B`, xoay vòng qua nhiều Groq API key.
- Giữ **Concept Mirroring Prompt**: bóc từ khóa cụ thể của tác giả, hỏi ngược 1–2 câu gợi mở, tránh văn mẫu sáo rỗng.
- Mọi lệnh gọi LLM phải có xử lý timeout, rate limit và retry; không để lỗi một model làm sập request.
- Agent 2 phải giữ cấu trúc **5 nhịp kịch tính**: Hook → Rising Friction → Turning Point → Visceral Climax → Cliffhanger.

### 3.4 Bảo mật
- **Không** hard-code API key, `JWT_SECRET` hay bất kỳ bí mật nào vào code hoặc commit. Chỉ dùng biến môi trường (`GROQ_API_KEY`, `GROQ_API_KEY_BIBLE`, `GROQ_API_KEY_COPILOT`, `GROQ_API_KEY_COMIC`, `JWT_SECRET`, `DATABASE_URL`).
- Không commit `.env`, `narrai.db`, `venv/`, `node_modules/`, `.next/`.
- Các giá trị trong README chỉ là ví dụ; không dùng làm giá trị thật.

### 3.5 Cơ sở dữ liệu
- SQLite phải giữ **WAL mode** (`journal_mode=WAL`, `synchronous=NORMAL`). Không bỏ pragma này.
- Khi đổi schema trong `models.py`, kiểm tra tác động lên các composite index hiện có và các router xã hội.
- Không xóa hoặc đổi tên bảng/cột đang dùng nếu chưa được yêu cầu.

### 3.6 Frontend
- Giao diện **song ngữ Việt–Anh**: mọi chuỗi hiển thị mới phải thêm vào `lib/i18n.ts`, không viết cứng một ngôn ngữ trong component.
- Kiểu dữ liệu dùng chung đặt trong `lib/types.ts`; lệnh gọi backend đi qua `lib/api.ts` (có retry).
- Cache gợi ý TF.js dùng IndexedDB, giới hạn ≤ 15MB; không vượt ngưỡng này.
- Phải hỗ trợ cả Light/Dark theme (Theme Provider ở `layout.tsx`).
- `npm run build` phải qua với **0 lỗi TypeScript**; không dùng `any` hoặc `@ts-ignore` để che lỗi.

## 4. Quy trình làm việc

1. Đọc `project.md` và các file liên quan trong mục 2.
2. Nêu kế hoạch ngắn (2–5 bước) nếu thay đổi chạm nhiều file.
3. Sửa code theo phạm vi tối thiểu.
4. Thêm hoặc cập nhật test (mục 5).
5. Chạy kiểm tra (mục 6).
6. Tóm tắt: file đã đổi, lý do, rủi ro, việc còn lại.

## 5. Kiểm thử

- Bộ test nằm ở `backend/tests/`, chạy bằng `python tests/run_all_tests.py` (hiện **203/203 PASS**).
- Có các nhóm đáng chú ý: `test_round7_qa_resilience.py` (độ bền AI và fallback), `test_round6_social_features.py`, `test_round6_historical_protection.py`.
- Thay đổi hành vi nào thì thêm test tương ứng. Sửa agent AI, social hoặc lịch sử thì cập nhật nhóm test liên quan.
- **Không** xóa, vô hiệu hóa hay nới lỏng assertion của test đang lỗi để "cho qua". Hãy sửa nguyên nhân gốc.
- Test không được gọi Groq thật nếu có thể mock; không làm test phụ thuộc vào API key thật.

## 6. Lệnh thường dùng

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py                       # http://localhost:8000  (Swagger: /docs)
python tests/run_all_tests.py        # chạy toàn bộ test

# Frontend
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
npm run dev                          # http://localhost:3000
npm run build                        # kiểm tra TypeScript
```

Trước khi báo hoàn thành: chạy test backend, và `npm run build` nếu có đụng frontend.

## 7. Quy ước code

**Backend (Python 3.11/3.12, FastAPI)**
- Dùng type hint; hàm/biến `snake_case`, class `PascalCase`.
- Router chỉ điều phối; logic nghiệp vụ đặt ở `services/` hoặc `agents/`.
- Prompt của agent đặt thành hằng số/ template rõ ràng, không rải chuỗi prompt dài trong logic.
- Ghi log có ngữ cảnh; không nuốt exception im lặng.
- Không thêm thư viện mới vào `requirements.txt` nếu chưa cần; nếu thêm, nêu lý do.

**Frontend (TypeScript, Next.js 14, Tailwind)**
- Component `PascalCase.tsx`, hook/hàm `camelCase`.
- Dùng Tailwind theo `tailwind.config.ts`; không thêm CSS rời nếu không cần.
- Tách logic gọi API, cache, recommender ra `services/` và `lib/`, không nhồi vào component.

## 8. Git & commit

- Commit nhỏ, một mục đích. Định dạng: `<type>(<scope>): <mô tả>`
  - type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  - Ví dụ: `fix(copilot): giữ nguyên heading khi sửa nhiều chương`
- Không `git push --force`, không viết lại lịch sử nhánh chung.

## 9. Không được làm

- Không bịa tên hàm, endpoint hay thư viện; hãy kiểm tra trong code.
- Không sửa file sinh tự động hoặc build output (`.next/`, `out/`).
- Không đổi cấu hình triển khai (Render/Vercel) hay biến môi trường production khi chưa được yêu cầu.
- Không đổi tên 4 agent hoặc đường dẫn file trong mục 2 mà không cập nhật `project.md` và test.
- Không làm nội dung sinh ra vi phạm mục 3.1, kể cả khi người dùng yêu cầu rõ ràng.

## 10. Khi nào phải hỏi lại

- Yêu cầu chạm vào bộ chặn lịch sử/IP, cơ chế fallback, hoặc schema DB.
- Thay đổi ảnh hưởng nhiều router hoặc API công khai.
- Phát hiện mâu thuẫn trong tài liệu (xem mục "Điểm cần xác minh" trong `project.md`).

## 11. Định dạng phản hồi

- Trả lời bằng **tiếng Việt**, giữ nguyên thuật ngữ kỹ thuật tiếng Anh.
- Ngắn gọn; nêu rõ file đã thay đổi và kết quả test.
