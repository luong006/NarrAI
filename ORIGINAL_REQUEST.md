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

## 2026-09-20T13:19:05Z

Hệ thống NarrAI tiến hành nâng cấp toàn diện: tái định hình văn phong truyện chữ theo tiêu chuẩn Light Novel / Web Novel hiện đại dành cho giới trẻ, xây dựng Dynamic Scene-Graph Ontology để quản lý không gian và thực thể, đồng thời khóa chặt tính nhất quán giữa nội dung kịch bản và tranh vẽ Manga.

Working directory: E:\NarrAI
Integrity mode: development

## Requirements

### R1. Tái Cấu Trúc Động Cơ Văn Phong Truyện Chữ (Modern Light Novel & Web Novel Engine)
- Cải tổ System Prompt sáng tác truyện chữ: Chuyển dịch từ văn phong miêu tả tĩnh sang phong cách Light Novel / Web Novel thịnh hành (nhịp truyện nhanh, đối thoại sắc bén tự nhiên, giàu độc thoại nội tâm, có hook mở đầu cuốn hút).
- Thiết lập cấu trúc phân nhịp kịch tính (Narrative Beats) giúp tình tiết phát triển liên tục, gia tăng chiều sâu tâm lý và sức hấp dẫn với độc giả trẻ.

### R2. Nâng Cấp Kiến Trúc Dynamic Scene-Graph Ontology
- Chuyển đổi mô hình Ontology sang Dynamic Scene-Graph Ontology (ràng buộc 3 chiều: Thực thể - Không gian - Thời đại / Thể loại).
- Thiết lập cơ chế kiểm soát không gian phân cảnh (Spatial Scene Enclosure): Neo giữ tuyệt đối vị trí địa lý của cảnh quay, ngăn chặn việc thực thể bị trôi dạt sang không gian hoặc thời kỳ khác (như lớp học hiện đại bị trôi thành đường phố hoặc cổ phong).

### R3. Đồng Bộ Hóa Tuyệt Đối Text-to-Image & Loại Bỏ Ảo Giác Khung Tranh Manga
- Khóa chặt trường phái mỹ thuật đồng nhất: Chuẩn hóa prompt hình ảnh theo phong cách Manga học đường đơn sắc hiện đại (clean lineart, screentone shading).
- Triệt tiêu 100% ảo giác lệch cảnh (Visual Hallucination): Bắt buộc prompt hình ảnh bám sát trực tiếp hành động, cử chỉ, trang phục và bối cảnh được miêu tả trong phụ đề/lời thoại của từng khung tranh.

## Acceptance Criteria

### Content & Visual Alignment Criteria
- [ ] Truyện chữ tạo ra mang nhịp độ nhanh, đối thoại sắc bén, giàu độc thoại nội tâm và có hook kịch tính theo chuẩn Light/Web Novel giới trẻ.
- [ ] 100% khung tranh phản ánh chính xác không gian và hành động trong lời dẫn đi kèm (0% xuất hiện bối cảnh ngoài phố hay trang phục cổ trang khi cảnh diễn ra trong lớp học).
- [ ] Phong cách vẽ và phục trang nhân vật duy trì tính nhất quán từ khung tranh đầu tiên đến khung tranh cuối cùng.
- [ ] Toàn bộ Backend (py_compile) và Frontend (npm run build) biên dịch thành công 0 lỗi.

## 2026-09-22T04:35:39Z

Nâng cấp toàn diện nền tảng sáng tác NarrAI: hoàn thiện song ngữ Anh - Việt 100%, bảo mật đăng nhập/đăng ký chuẩn ngân hàng kèm cơ chế bộ đệm Redis/Local Cache, khắc phục lỗi tương tác AI Co-pilot, nâng cấp chất văn tiểu thuyết chuyên nghiệp cuốn hút loại bỏ văn phong AI, và khóa cứng tính nhất quán ngoại hình nhân vật cùng chuẩn manga 100% đen trắng không lỗi ảnh.

Working directory: e:\NarrAI
Integrity mode: development

## Requirements

### R1. Hoàn Thiện Song Ngữ (i18n) Toàn Diện 100% (Anh ⟷ Việt)
Hệ thống phải chuyển đổi ngôn ngữ trơn tru trên toàn bộ các thành phần giao diện người dùng: thanh điều hướng, các nút lệnh nhanh của Co-pilot (New Intro, Dramatic Outro, Change Tone, Deepen Characters), các thông báo toast, modal xác thực, màn hình phỏng vấn cốt truyện, thanh công cụ soạn thảo, và trình xem truyện tranh. Không để sót bất kỳ chuỗi ký tự cố định (hardcoded string) nào trên giao diện khi chuyển đổi qua lại giữa Tiếng Anh và Tiếng Việt.

### R2. Hệ Thống Đăng Nhập / Đăng Ký Chuẩn Bảo Mật Ngân Hàng & Họ Tên Đầy Đủ
Nâng cấp toàn diện luồng xác thực:
- Form đăng ký bổ sung trường "Họ và tên" (`full_name`) lưu trữ vào database.
- Áp dụng các quy tắc mật khẩu nghiêm ngặt chuẩn ngân hàng: độ dài tối thiểu 8-12 ký tự, bắt buộc có ít nhất 1 chữ hoa, 1 chữ thường, 1 chữ số, 1 ký tự đặc biệt, không chứa khoảng trắng.
- Giao diện có thanh đo độ mạnh mật khẩu (Password Strength Meter) và danh sách kiểm tra điều kiện (checklist) phản hồi thời gian thực, có ô xác nhận lại mật khẩu (`confirm password`).
- Chống brute-force / spam đăng nhập và thông báo lỗi rõ ràng theo từng ngôn ngữ.

### R3. Tích Hợp & Kiểm Tra Bộ Nhớ Đệm Redis (Redis Cache Layer with Fallback)
Xác thực hiện trạng Redis trong môi trường hệ thống. Xây dựng dịch vụ bộ đệm dữ liệu thông minh (`CacheManager`): kết nối và lưu trữ cache vào Redis khi dịch vụ hoạt động, đồng thời tự động chuyển đổi dự phòng (graceful fallback) sang bộ nhớ đệm an toàn trong tiến trình (in-memory LRU/TTL cache) nếu môi trường chưa cài đặt hoặc tạm dừng Redis, đảm bảo hệ thống luôn vận hành ổn định 100% không gián đoạn.

### R4. Khắc Phục Triệt Để Lỗi Tương Tác AI Co-pilot (Ảnh Minh Họa)
Giải quyết nguyên nhân gốc rễ gây ra lỗi *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"* khi người dùng bấm các lệnh nhanh hoặc chat bằng tiếng Anh (ví dụ: *"Rewrite in a darker, more gripping thriller tone"*):
- Bổ sung bộ nhận diện từ khóa lệnh can thiệp bản thảo đa ngôn ngữ (cả tiếng Anh và tiếng Việt).
- Kiểm soát chặt chẽ ngân sách token của ngữ cảnh truyện gửi lên mô hình để không vượt trần hoặc gây lỗi 413 / rate limit.
- Đảm bảo cơ chế tự động thử lại hoặc fallback thông minh khi mô hình chính gặp sự cố kết nối.

### R5. Đột Phá Chất Văn Tiểu Thuyết — Loại Bỏ Văn Phong "AI", Nâng Chuẩn Tác Giả Chuyên Nghiệp
Tái cấu trúc bộ quy chuẩn sáng tác văn học:
- Loại bỏ hoàn toàn các mẫu câu sáo rỗng, khuôn mẫu điển hình của AI (như *"nhanh như nhịp tim chậm rãi"*, *"khoảng trống trong lòng"*, *"nỗi lo đè nặng lên vai"*, *"thở dài giọng nhẹ"*, các đoạn triết lý suông không cần thiết).
- Triệt để áp dụng nguyên lý **Show, Don't Tell**: miêu tả trực diện bằng cảm giác thể xác cụ thể, vi hành động, biểu cảm vi mô và tương tác vật lý chân thực.
- Hội thoại sắc sảo, tự nhiên, mang cá tính rõ rệt của nhân vật và có hàm ý ngầm (subtext), nhịp điệu co giãn cuốn hút, khiến độc giả không thể rời mắt khỏi tác phẩm.

### R6. Khóa Cứng Tính Nhất Quán Ngoại Hình Nhân Vật Truyện Tranh (Face, Hair, Outfits)
Tối ưu hóa vị trí và cấu trúc Visual DNA trong câu lệnh sinh ảnh:
- Đưa trực tiếp thông số nhận diện nhân vật (khuôn mặt, kiểu tóc đặc trưng, trang phục cố định) lên vị trí đầu tiên trong ngân sách 77 token CLIP của mô hình Stable Diffusion/Diffusion, không để bị đẩy lùi về cuối hay suy giảm trọng số sau các mô tả bối cảnh dài.
- Đồng bộ hóa định danh nhân vật qua toàn bộ các khung tranh liên tiếp, đảm bảo nhân vật giữ nguyên trang phục, kiểu tóc và đường nét gương mặt.

### R7. Triệt Tiêu 100% Tranh Màu & Khắc Phục Lỗi Khung Tranh Không Hiển Thị
- Ép buộc 100% tranh truyện là Manga đen trắng chuẩn mực (Monochrome Manga Lineart + Screentones). Sử dụng bộ lọc hậu xử lý (Grayscale / Thresholding) trên server để loại bỏ tuyệt đối bất kỳ hình ảnh nào bị vấy màu từ các nguồn sinh ảnh.
- Khắc phục lỗi khung tranh không hiển thị: thay thế việc chuyển hướng URL ngoại vi bằng cơ chế xử lý nội bộ, tự động retry, lưu bộ đệm đĩa chắc chắn và cung cấp hình ảnh dự phòng chuẩn manga khi mạng gặp sự cố.

## Acceptance Criteria

### Tính Năng Đa Ngôn Ngữ (i18n)
- [ ] 100% văn bản giao diện (tiêu đề, nút bấm, placeholder, lệnh Co-pilot, chip gợi ý, thông báo toast, modal xác thực) chuyển đổi chính xác giữa Tiếng Việt và Tiếng Anh khi người dùng chuyển ngôn ngữ.
- [ ] Không còn bất kỳ chuỗi ký tự cố định (hardcoded) nào hiển thị sai ngôn ngữ.

### Đăng Nhập & Bảo Mật Chuẩn Ngân Hàng
- [ ] Đăng ký yêu cầu đầy đủ Họ và tên, Tên đăng nhập, Mật khẩu và Xác nhận mật khẩu.
- [ ] Mật khẩu được kiểm tra đầy đủ 5 tiêu chí bảo mật (độ dài >= 8, chữ hoa, chữ thường, chữ số, ký tự đặc biệt) trên cả Frontend và Backend.
- [ ] Giao diện hiển thị trực quan thanh đo độ mạnh mật khẩu và danh sách checklist đạt chuẩn.
- [ ] Cơ sở dữ liệu tự động nâng cấp trường `full_name` tương thích ngược hoàn toàn.

### Bộ Đệm Cache & Redis
- [ ] Hệ thống có module `cache_service` hỗ trợ kết nối Redis và tự động chuyển sang local memory cache mượt mà nếu Redis không khả dụng.
- [ ] Tốc độ truy vấn dữ liệu phiên và bản thảo đạt chuẩn hiệu năng cao (< 20ms đối với dữ liệu đã cache).

### Ổn Định AI Co-pilot
- [ ] Lệnh tiếng Anh như *"Rewrite in a darker, more gripping thriller tone"* hay *"Write a completely different opening"* kích hoạt chỉnh sửa bản thảo thành công 100% mà không xuất hiện lỗi "trục trặc nhẹ".
- [ ] Ngân sách token được cắt gọt an toàn, không gây tràn bộ đệm hay lỗi kết nối.

### Chất Lượng Văn Phong Tiểu Thuyết
- [ ] Văn bản truyện sinh ra không còn chứa các sáo ngữ AI (anti-cliché banlist phát hiện 0 vi phạm).
- [ ] Tác phẩm mở đầu bằng In Medias Res kịch tính, hội thoại tự nhiên có vi hành động, câu chuyện tạo được sức lôi cuốn mạnh mẽ đối với người đọc.

### Nhất Quán Ngoại Hình & 100% Tranh Đơn Sắc
- [ ] Toàn bộ các khung tranh trong một chương truyện được kiểm tra 100% là ảnh đơn sắc (grayscale/monochrome), 0% tranh màu lọt vào.
- [ ] Nhân vật giữ nguyên kiểu tóc, trang phục nhận diện và nét mặt xuyên suốt các khung tranh.
- [ ] 0% lỗi ảnh hỏng (broken image icon) trên trình xem truyện tranh.
