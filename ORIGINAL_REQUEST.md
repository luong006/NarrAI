# Original User Request

## 2026-09-19T13:33:05Z

Hệ thống NarrAI tiến hành sửa chữa triệt để lỗi hiển thị raw JSON trong Editor khi Copilot can thiệp trực tiếp, khóa cứng tính nhất quán nhân vật Manga (khuôn mặt, kiểu tóc, trang phục, deterministic seed) và loại bỏ hoàn toàn việc cắt xén đối thoại bằng dấu "....." khi truyện quá dài.

Working directory: E:\NarrAI
Integrity mode: development

## Requirements

### R1. Triệt Tiêu Lỗi Hiển Thị Raw JSON Trong Editor Khi Copilot Sửa Bản Thảo
- Khi AI Co-pilot thực hiện hành động edit_story_direct, nội dung cập nhật (updated_story_content) phải được làm sạch và giải mã triệt để ở cả backend (copilot_agent.py) và frontend (page.tsx).
- Ngăn chặn triệt để tình trạng chuỗi JSON bị lồng nhau ({"updated_story_content": "..."}) hoặc các ký tự thoát (\n\n) hiển thị nguyên bản lên màn hình Editor.
- Vùng soạn thảo Editor chỉ hiển thị văn xuôi thuần túy tiếng Việt định dạng Markdown sạch sẽ.

### R2. Khóa Cứng Tính Nhất Quán Nhân Vật Manga (Khuôn Mặt, Kiểu Tóc, Trang Phục)
- Nâng cấp DNA_EXTRACTOR_PROMPT: Yêu cầu trích xuất chi tiết cực hạn về trang phục nhận diện (loại áo, màu sắc, phụ kiện cổ/ngực), kiểu tóc chính xác và đặc điểm khuôn mặt bất biến.
- Bổ sung cơ chế tiêm DNA thông minh (Smart DNA Injection): Ngay cả khi prompt miêu tả dùng đại từ hoặc danh từ chung ("cô bé", "anh bạn cùng bàn", "học sinh", "cậu ấy"), hệ thống phải tự động nhận diện và gắn đầy đủ Visual DNA của nhân vật tương ứng vào image_prompt.
- Bổ sung tham số seed đồng bộ (Deterministic Comic Seed) trong services/cloudflare_ai.py theo ID bộ truyện để mô hình diffusion tạo ra nét mặt, trang phục và phong cách vẽ đồng nhất trên toàn bộ các khung tranh.

### R3. Chấm Dứt Hoàn Toàn Tình Trạng Cắt Xén Dấu "....." Trong Truyện Tranh
- Xóa bỏ triệt để mọi logic tự động cắt ngắn từ ngữ và nối đuôi + "..." trong comic_agent.py (cả ở chế độ LLM chính và chế độ fallback).
- Khi truyện dài hoặc đoạn văn dài: Tự động phân rã văn bản theo ranh giới câu trọn vẹn (Sentence Boundaries) và tạo đủ số lượng khung tranh tuần tự (Sequential Panels) tương ứng với nhịp diễn biến.
- Lời thoại và phụ đề dưới mỗi khung tranh luôn là câu nói hoàn chỉnh, giàu cảm xúc, không bị đứt đoạn lửng lơ.

## Acceptance Criteria

### Functional & Visual Consistency Criteria
- [ ] Khi ra lệnh "tôi muốn một mở đầu khác" hoặc bất kỳ lệnh can thiệp nào cho Co-pilot, Editor lập tức cập nhật đúng văn xuôi mới, 0% xuất hiện dấu ngoặc nhọn { hay chuỗi "updated_story_content".
- [ ] Các panel truyện tranh sinh ra cùng một nhân vật có trang phục và đặc điểm nhận diện khuôn mặt đồng nhất, không bị thay đổi quần áo giữa các cảnh.
- [ ] Dưới mỗi khung truyện tranh, lời thoại/phụ đề dẫn chuyện hiển thị trọn câu, hoàn toàn không có dấu ..... cắt cụt chữ.
- [ ] Toàn bộ Backend (py_compile) và Frontend (npm run build) biên dịch thành công không lỗi.
