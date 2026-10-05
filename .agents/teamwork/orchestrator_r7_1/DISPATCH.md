# Dispatch Log

## 2026-10-05T05:30:16Z
Sender: ea484519-cdfc-4c06-ade6-6e8e07cb0790
Priority: MESSAGE_PRIORITY_HIGH

You are the Project Orchestrator (orchestrator_r7_1) for NarrAI.

Your working directory for metadata (plans, progress, reports):
`e:\NarrAI\.agents\teamwork\orchestrator_r7_1`

The project root workspace is:
`e:\NarrAI`

Authoritative User Request & Acceptance Criteria:
Refer to `e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md` (specifically the latest section timestamped 2026-10-05T05:28:19Z).

Your objective is to lead the team to resolve all 5 requirements (R1 - R5):
1. **R1. Gỡ Bỏ Hoàn Toàn Panel "Neural Style Laboratory" Khỏi Trang Chủ**:
   - Gỡ bỏ component `<NeuralVisualPreview />` khỏi `LandingView.tsx`.
   - Giữ giao diện tối giản, tập trung vào Hero, CTA "Bắt đầu sáng tác ngay", và bảng tính năng cốt lõi.
   - Không làm gãy import hay TensorFlow.js packages.
2. **R2. Cân Đối Bố Cục & Chuẩn Hóa Đối Xứng Khung Chat AI (UnifiedIntakeChat)**:
   - Căn chỉnh bố cục khung chat: avatar và tin nhắn cân đối, đối xứng.
   - Sửa bottom input dock: thay thế `fixed sm:left-64` cứng nhắc bằng layout flex/sticky ăn khớp 100% với khung chính, căn giữa hoàn hảo theo trục dọc.
   - Cân chỉnh khoảng cách 4 starter prompts thoáng đãng, cân xứng hai bên màn hình desktop.
3. **R3. Khắc Phục Lỗi Chat AI Phản Hồi Lặp Cứng Nhắc & Nâng Cấp Hệ Thống Hỏi Ngược**:
   - Backend (`qa_refiner.py` & `main.py`):
     - Multi-Model Fallback: `qwen/qwen3.8-27b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`.
     - Multi-Key Fallback: `GROQ_API_KEY_BIBLE` -> `GROQ_API_KEY` -> `GROQ_API_KEY_COPILOT`.
     - System Prompt: Luôn phân tích từ khóa cụ thể của người dùng và đặt 1-2 câu hỏi gợi mở sâu sắc ngược lại, không rập khuôn.
   - Frontend (`UnifiedIntakeChat.tsx` & `api.ts`):
     - Bỏ thông báo fallback tĩnh gây hiểu lầm; hiển thị trạng thái kết nối rõ ràng cùng nút "Thử lại".
     - Dynamic Client Fallback: Khi offline/mất kết nối hoàn toàn, tự động tạo câu hỏi gợi mở dựa trên từ khóa người dùng nhập.
4. **R4. Làm Nổi Bật & Chuẩn Hóa Mục "Mạng Xã Hội & Cộng Đồng"**:
   - Sidebar tab đổi tên từ "Bài đăng" thành "Mạng xã hội" hoặc "Cộng đồng tác giả" với icon trực quan.
   - Nút CTA "Khám phá Cộng đồng" ngay trên Landing Page.
   - Đảm bảo hiển thị đầy đủ bảng tin, thả tim, bình luận phân cấp, theo dõi tác giả, bộ lọc thể loại, ô tìm kiếm.
5. **R5. Rà Soát & Đảm Bảo Vận Hành Thông Suốt Các Chức Năng Cốt Lõi**:
   - Verify toàn bộ luồng: Intake Chat -> Story Editor -> Manga Comic -> Cộng đồng.
   - 100% 182+ backend tests PASS (`python backend/tests/run_all_tests.py`).
   - Frontend `npm run build` PASS 0 lỗi.

Maintain `progress.md` and `plan.md` in `e:\NarrAI\.agents\teamwork\orchestrator_r7_1`.
Dispatch specialist subagents, run review & adversarial verification gates, ensure all acceptance criteria are met, and report victory back to Sentinel when completed.
