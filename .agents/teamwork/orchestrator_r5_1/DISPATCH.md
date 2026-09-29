## 2026-09-29T03:11:54Z

Bạn là Project Orchestrator (Round 5) cho dự án NarrAI.
Working Directory của bạn: e:\NarrAI\.agents\teamwork\orchestrator_r5_1
Đường dẫn yêu cầu gốc: e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md
Thư mục dự án: e:\NarrAI

Nhiệm vụ của bạn là lập kế hoạch, phân rã công việc thành các milestone rõ ràng, điều phối các subagents chuyên biệt (workers, reviewers, testers) để triển khai và hoàn thiện 100% yêu cầu sau:

1. **Biên tập Bản thảo Đa mục tiêu Linh hoạt (Copilot Flexible Manuscript Surgery):**
   - Loại bỏ cơ chế cứng nhắc chỉ sửa mở đầu. Hỗ trợ 5 mục tiêu can thiệp chính xác:
     + Target 1 — Sửa Mở đầu (Opening/Hook): Viết lại mở đầu giật gân, giữ nguyên tiêu đề và mạch truyện.
     + Target 2 — Sửa/Đổi Nhân vật & Lời thoại (Character & Dialogue Surgery): Thay tên, đổi đại từ xưng hô, cập nhật khẩu ngữ hiện đại, subtext và phản ứng sinh lý trong toàn bộ hoặc một phân đoạn.
     + Target 3 — Sửa/Chèn Diễn biến Thân bài (Middle Beats & Scene Insertion): Thêm biến cố, đẩy nhanh nhịp độ (Pacing), chèn tình huống nguy nan hoặc đào sâu nội tâm ở giữa truyện mà không xáo trộn mở đầu và kết thúc.
     + Target 4 — Sửa Đoạn Kết (Climax & Ending): Xây dựng Lingering Cliffhanger nghẹt thở hoặc kết thúc dâng trào cảm xúc, giữ vững logic đã thiết lập.
     + Target 5 — Chuyển Đổi Phong Cách & Giọng Văn Toàn Bản Thảo (Tone Shift & Style Restyling): Viết lại toàn bộ truyện theo phong cách chỉ định (u tối, giật gân, hài hước, trinh thám, cổ trang) bảo toàn nguyên vẹn chuỗi sự kiện chính và nhân vật.
   - Dynamic Semantic Chunk Slicing: `prefix` -> `window_to_edit` -> `suffix`.
   - Bảo toàn tuyệt đối nhãn tiêu đề `**[TÊN TIÊU ĐỀ]**` và các chương `## Chương X`.

2. **Giao diện Chat Tiếp nhận Tối giản Chuẩn ChatGPT / Gemini (Unified Intake Chat):**
   - Loại bỏ hoàn toàn lưới chọn thể loại/chủ đề thịnh hành dạng lưới tĩnh cũ (Phase 1 Idea chips) và bỏ phỏng vấn chia giai đoạn (Phase 2 Interview).
   - Thiết kế giao diện AI Intake Chat tối giản, tinh tế, sang trọng theo chuẩn Gemini / ChatGPT: khung chat toàn màn hình, input bar nổi bật ở đáy, bong bóng chat thoáng đãng.
   - Trợ lý Q&A am hiểu sâu sắc thể loại văn học, quy tắc hư cấu cá nhân (tự do sáng tạo), quy tắc lịch sử Việt Nam (tôn trọng sự thật, phân định chính sử / dã sử), và quy tắc bản quyền / sở hữu trí tuệ (tránh sao chép y nguyên IP bảo hộ).

3. **Chuyển giao Liền mạch Sang Chấp bút Bản thảo:**
   - Không qua bước trung gian cứng nhắc: khi người dùng bấm "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" hoặc khi đã đủ ý tưởng, AI cô đọng Dàn ý Phác thảo (Refined Narrative Bible) chỉ trong 1-2 giây.
   - Tự động chuyển thẳng sang màn hình Story Editor và kích hoạt tiến trình chấp bút thời gian thực (Streaming Generation), cấp phát story_id ngay lập tức.

4. **Chuyên mục "Bài đăng" (Community Feed) & Nút "Lưu và đăng bài":**
   - Bổ sung tab điều hướng "Bài đăng" (bên cạnh "Sáng tác" và "Truyện tranh").
   - Hiển thị danh sách các tác phẩm xuất bản của cộng đồng và cá nhân: Thẻ 3D Parallax Tilt (tiêu đề, ảnh bìa manga nếu có, trích đoạn, thể loại, tác giả, metrics), cho phép đọc truyện chữ & lướt xem khung tranh manga, tương tác Like Morphicon, bình luận, chia sẻ.
   - Kết nối với Thuật toán đề xuất 3 giai đoạn (Two-Tower Cosine + Multi-Armed Bandit 15% Cold-Start + MMR lambda=0.7).
   - Nút "Lưu & Đăng bài" trên thanh công cụ StoryEditor.tsx: tự động lưu bản thảo chữ mới nhất, đồng bộ hình ảnh manga (nếu có), xuất bản vào bảng `social_posts` qua API `POST /api/social/publish`, hiển thị thông báo thành công kèm link xem ngay bài đăng.

5. **Kiến trúc Frontend Phân lớp Chống Xung đột Tuyệt đối:**
   - Tách biệt rõ ràng 4 tầng:
     + Layer 0: ThreeUI 3D WebGL Canvas nền đơn nhất (tự pause khi tab ẩn hoặc ra khỏi màn hình, GPU 0%).
     + Layer 1: Semantic DOM & 3D Interactive Cards (CSS 3D Transforms).
     + Layer 2: Morphicons SVG spring physics.
     + Layer 3: Modals & Chat Portals dùng React Portals với `isolation: isolate` và `z-index: 50+`, loại bỏ hoàn toàn z-fighting hay giật lag.

Tiêu chí nghiệm thu bắt buộc:
- Backend Python biên dịch sạch (py_compile) 0 lỗi.
- Frontend Next.js biên dịch sản xuất sạch (npm run build) 0 lỗi.
- Toàn bộ test suite tự động kiểm thử đạt 100% PASS.
