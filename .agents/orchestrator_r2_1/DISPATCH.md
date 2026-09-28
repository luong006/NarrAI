## 2026-09-20T13:20:14Z

You are the Project Orchestrator for the NarrAI upgrade project.

Your Working Directory: e:\NarrAI\.agents\orchestrator_r2_1
Workspace Directory: e:\NarrAI
Original Request File: e:\NarrAI\.agents\ORIGINAL_REQUEST.md

Please review the latest user request in e:\NarrAI\.agents\ORIGINAL_REQUEST.md under ## 2026-09-20T13:19:05Z:

Requirements:
- R1. Tái Cấu Trúc Động Cơ Văn Phong Truyện Chữ (Modern Light Novel & Web Novel Engine):
  * Cải tổ System Prompt sáng tác truyện chữ: Chuyển dịch từ văn phong miêu tả tĩnh sang phong cách Light Novel / Web Novel thịnh hành (nhịp truyện nhanh, đối thoại sắc bén tự nhiên, giàu độc thoại nội tâm, có hook mở đầu cuốn hút).
  * Thiết lập cấu trúc phân nhịp kịch tính (Narrative Beats) giúp tình tiết phát triển liên tục, gia tăng chiều sâu tâm lý và sức hấp dẫn với độc giả trẻ.
- R2. Nâng Cấp Kiến Trúc Dynamic Scene-Graph Ontology:
  * Chuyển đổi mô hình Ontology sang Dynamic Scene-Graph Ontology (ràng buộc 3 chiều: Thực thể - Không gian - Thời đại / Thể loại).
  * Thiết lập cơ chế kiểm soát không gian phân cảnh (Spatial Scene Enclosure): Neo giữ tuyệt đối vị trí địa lý của cảnh quay, ngăn chặn việc thực thể bị trôi dạt sang không gian hoặc thời kỳ khác (như lớp học hiện đại bị trôi thành đường phố hoặc cổ phong).
- R3. Đồng Bộ Hóa Tuyệt Đối Text-to-Image & Loại Bỏ Ảo Giác Khung Tranh Manga:
  * Khóa chặt trường phái mỹ thuật đồng nhất: Chuẩn hóa prompt hình ảnh theo phong cách Manga học đường đơn sắc hiện đại (clean lineart, screentone shading).
  * Triệt tiêu 100% ảo giác lệch cảnh (Visual Hallucination): Bắt buộc prompt hình ảnh bám sát trực tiếp hành động, cử chỉ, trang phục và bối cảnh được miêu tả trong phụ đề/lời thoại của từng khung tranh.

Acceptance Criteria:
1. Truyện chữ tạo ra mang nhịp độ nhanh, đối thoại sắc bén, giàu độc thoại nội tâm và có hook kịch tính theo chuẩn Light/Web Novel giới trẻ.
2. 100% khung tranh phản ánh chính xác không gian và hành động trong lời dẫn đi kèm (0% xuất hiện bối cảnh ngoài phố hay trang phục cổ trang khi cảnh diễn ra trong lớp học).
3. Phong cách vẽ và phục trang nhân vật duy trì tính nhất quán từ khung tranh đầu tiên đến khung tranh cuối cùng.
4. Toàn bộ Backend (py_compile) và Frontend (npm run build) biên dịch thành công 0 lỗi.

Instructions:
1. Initialize your BRIEFING.md, plan.md, and progress.md in e:\NarrAI\.agents\orchestrator_r2_1.
2. Formulate a milestone plan, decompose tasks, and dispatch specialized workers/reviewers.
3. Keep progress.md actively updated so monitoring crons can report progress.
4. Ensure all unit tests, py_compile, and frontend build pass with 0 errors.
5. When complete, write handoff.md in your working directory and notify the Sentinel.
