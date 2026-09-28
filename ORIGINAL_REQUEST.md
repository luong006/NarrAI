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

## 2026-09-28T01:01:31Z

Nâng cấp toàn diện nền tảng NarrAI trở thành Nền Tảng Sáng Tác & Mạng Xã Hội Văn Học Đẳng Cấp Cao:
1. Kiến trúc **Adaptive Open-Ontology** (Vừa tôn vinh văn hóa Việt Nam, vừa linh hoạt xử lý 100% dữ liệu ngoài miền OOD/ngoại lai mà không bị gò bó hay gãy vỡ).
2. Hệ thống **Mạng Xã Hội với Thuật Toán Đề Xuất Thông Minh 3 Giai Đoạn** (Two-Tower Embedding, Multi-Armed Bandit giải quyết Cold-Start, MMR chống Echo Chamber, phân tích tín hiệu ẩn Dwell-time và ngữ nghĩa comment).
3. Hệ thống **Open Messenger** kết nối chat tự do giữa mọi người dùng.
4. **Kinh Tế Xu & An Ninh Tiền Tệ Chuẩn Ngân Hàng** (Chống Race Condition, Double-Spending, bù trừ tự động, sổ cái SHA-256 bất biến) kết hợp **Anti-Clone Đa Lớp (Browser Fingerprint + IP Subnet)**.
5. **Kiến Trúc Frontend Phân Lớp Không Xung Đột** (Render Pipeline Isolation kết hợp mượt mà giữa ThreeUI WebGL Canvas 3D và Morphicons SVG Spring Physics, tối ưu 60 FPS, chống context loss).

Working directory: e:\NarrAI
Integrity mode: demo

---

## Technical Specifications & Architecture

### R1. Kiến Trúc Sáng Tác Linh Động: Adaptive Open-Ontology, Phân Ranh Lịch Sử Chuẩn & Hư Cấu Cá Nhân

Hệ thống phân định rạch ròi giữa **Sáng tác Lịch sử Dân tộc** và **Sáng tác Cá nhân Tự do**, đảm bảo vừa tôn trọng sự thật lịch sử, vừa chắp cánh tối đa cho trí tưởng tượng cá nhân:

1. **Ba Chế Độ Sáng Tác Lịch Sử & Hư Cấu (3 Narrative Modes):**
   - **Chế độ 1 — Chính Sử & Tôn Trọng Sự Thật Lịch Sử (Strict Historical Authenticity):**
     - Áp dụng khi người dùng viết về các nhân vật, sự kiện lịch sử có thật (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Quang Trung, trận Bạch Đằng, Như Nguyệt, Ngọc Hồi...).
     - Kích hoạt **Historical Grounding Gatekeeper**: Bắt buộc tuân thủ đúng niên đại, tiến trình chiến dịch, tính cách nhân vật lịch sử và đại cục quốc gia. Tuyệt đối cấm xuyên tạc, làm sai lệch lịch sử (ví dụ: không thể viết "Trần Hưng Đạo bại trận Bạch Đằng").
   - **Chế độ 2 — Dã Sử & Phóng Tác Góc Nhìn Cá Nhân (Historical Fiction / Alternative Lens):**
     - Bối cảnh và thời đại là có thật (thời Lý, thời Trần, kháng chiến...), nhân vật lịch sử giữ đúng cốt cách, nhưng nhân vật chính và cốt truyện là **hư cấu do người dùng tự nghĩ** (ví dụ: chuyện tình của một đôi trai gái thời chiến, góc nhìn của một người lính vô danh trong đội quân cấm vệ, hoặc một nghĩa sĩ thầm lặng).
     - Cho phép tự do sáng tạo biến cố vi mô nhưng neo giữ vững chắc không gian và tinh thần thời đại.
   - **Chế độ 3 — Hư Cấu Cá Nhân Hoàn Toàn Tự Do (Free Personal Fiction / Non-Historical):**
     - Dành cho các câu chuyện hiện đại, tình cảm đô thị, khoa học viễn tưởng, ma pháp, isekai...
     - **Cơ chế Thả Lỏng Hoàn Toàn (Complete Semantic Relaxation):** 100% tự do sáng tạo, không áp đặt bất kỳ sự kiện lịch sử, nhân vật lịch sử hay quy chuẩn cổ phong nào.

2. **Cơ Chế Phân Luồng Bản Thảo 3 Cấp Độ (Tri-Tier Ontology Resolver):**
   - **Tier 1 — Canonical Vietnamese Cultural Domain (Độ tương đồng văn hóa >= 0.7):**
     - Kích hoạt toàn bộ tri thức lịch sử & truyền thống Việt Nam: Đại từ xưng hô chuẩn mực (*Bệ hạ/khanh, chàng/nàng, u/con, tía/má, đồng chí...*), thực thể văn hóa (*Trống đồng, Nỏ thần, Gươm báu, Cổng làng, Bến sông...*), và Comic Visual DNA cổ phục (*Áo Ngũ Thân, Áo Nhật Bình, Áo Tấc, Khăn Đóng, Áo Bà Ba, Nón Lá*).
     - Áp dụng Master Negative chặn méo mó văn hóa (*Hanfu, Kimono, Hanbok, Samurai, Ninja*).
   - **Tier 2 — Cultural Fusion / Hybrid Domain (0.3 <= Tương đồng < 0.7):**
     - Xử lý các thể loại lai ghép độc đáo (ví dụ: *Cyberpunk Thăng Long 2099*, *Việt Nam Hậu Tận Thế*, *Steampunk Triều Nguyễn*).
     - Giữ nguyên hồn cốt văn hóa cốt lõi nhưng tự động nới lỏng các ràng buộc thời đại (Era Constraints) để dung nạp công nghệ tương lai hoặc phép thuật giả tưởng.
   - **Tier 3 — Open-Domain Adaptive Graph (Tương đồng < 0.3 — Hoàn toàn ngoài miền văn hóa Việt):**
     - Khi người dùng viết truyện trinh thám phương Tây, Cyberpunk New York, Fantasy Ma pháp, hệ thống tự động vô hiệu hóa các bộ lọc phong kiến Việt và không áp đặt trang phục cổ truyền Việt Nam!
     - Kích hoạt **Dynamic Ephemeral Node Extraction**: Mô hình tự động trích xuất thực thể, không gian và thời đại dựa trên ngữ cảnh tự nhiên của câu chuyện người dùng đưa vào.

3. **Bộ Lọc Ngôn Ngữ Thông Minh Có Chọn Lọc:**
   - Bộ lọc chỉ loại bỏ sáo ngữ kiếm hiệp/tiên hiệp Tàu dịch sượng (*"tiêu sái", "tà mị", "lãnh khốc", "bản tọa", "đế tôn"*) khi bối cảnh là thuần Việt hoặc văn học nghiêm túc.
   - Nếu người dùng chủ động chọn thể loại Tiên hiệp hoặc Kiếm hiệp, bộ lọc tự động hạ cấp xuống chế độ cho phép để phục vụ đúng ý đồ sáng tác cá nhân.

---

### R2. Thuật Toán Mạng Xã Hội Văn Học Cấp Cao (Next-Gen Recommendation Engine & Open Messenger)

Xây dựng hệ thống mạng xã hội thông minh tương đương thuật toán hiện đại, vượt xa mức so sánh Cosine thô sơ:

1. **Cấu Trúc Dữ Liệu Đồ Thị & Hồ Sơ Người Dùng Đa Tầng (`db/models.py`):**
   - Bảng `social_posts`: `id`, `user_id`, `story_id`, `title`, `content_snippet`, `cover_image_url`, `genre`, `tags` (JSON), `concept_vector` (128-dim JSON embedding), `likes_count`, `comments_count`, `views_count`, `dwell_time_avg`, `created_at`.
   - Bảng `post_interactions`: Lưu vết tín hiệu tương tác chi tiết:
     - `interaction_type`: Explicit (`LIKE`, `COMMENT`, `BOOKMARK`, `SHARE`) và Implicit (`CLICK`, `SCROLL_50`, `SCROLL_100`, `DWELL_TIME_SECONDS`).
     - Trọng số tín hiệu: w(Dwell > 60s) = 2.5, w(Scroll_100) = 2.0, w(Like) = 1.5, w(Comment) = 3.0.
   - Bảng `user_interest_profiles`:
     - Lưu trữ Vector Sở thích động cập nhật liên tục với cơ chế suy giảm theo thời gian (Exponential Time Decay lambda = 0.05/ngày).
     - Phân tích cảm xúc và thực thể từ bình luận (Sentiment & Entity Extraction từ nội dung comment).

2. **Thuật Toán Đề Xuất 3 Giai Đoạn (3-Stage Hybrid Recommender System):**
   - **Giai đoạn 1 — Candidate Generation (Truy hồi ứng viên):**
     - Kết hợp Content-Based Filtering (Cosine Similarity giữa User vector và Post vector) + Graph-Based DSGO Traversal (gợi ý các truyện chia sẻ chung thực thể hoặc bối cảnh không gian liên đới).
   - **Giai đoạn 2 — Scoring & Multi-Task Ranking (Chấm điểm & Xếp hạng):**
     Score(p, u) = w1*CosineSim(U_u, V_p) + w2*ImplicitAffinity(u, p) + w3*Freshness(p) + w4*QualityScore(p)
     Trong đó QualityScore(p) tính toán dựa trên tỷ lệ đọc hết chương và đánh giá từ độc giả.
   - **Giai đoạn 3 — Re-ranking, Serendipity & Exploration (Chống Echo-Chamber):**
     - **Maximal Marginal Relevance (MMR):** Đảm bảo Feed của người dùng có độ đa dạng thể loại (lambda_MMR = 0.7), không bị ngập tràn duy nhất một thể loại.
     - **Multi-Armed Bandit (Thompson Sampling / epsilon-greedy epsilon=0.15):** Dành 15% vị trí hiển thị trên Feed để thử nghiệm các tác phẩm mới xuất bản (Giải quyết bài toán Cold-Start cho tác giả mới).

3. **Hệ Thống Open Messenger Đẳng Cấp:**
   - Hỗ trợ chat tự do giữa MỌI người dùng trong hệ thống (User Directory search theo username/họ tên).
   - Quản lý cuộc hội thoại, lưu trữ tin nhắn bảo mật, hiển thị trạng thái đã đọc và thông báo tin nhắn mới tức thì.

---

### R3. Tiền Tệ Chuẩn Ngân Hàng & Chống Tấn Công Trục Lợi Nguy Hiểm

1. **Mô Hình Kinh Tế 100 Xu:**
   - 100k VNĐ = 100 xu.
   - Tạo truyện (Ngắn 8 xu, Vừa 12 xu, Dài 16 xu); Sửa bản thảo 2 xu/lần; Chuyển thể Manga 16 xu/lần.
   - 100 xu đủ hoàn thành: 2-3 truyện + 10-15 lần sửa + 2-3 lần manga (~95 xu).

2. **Phòng Chống Các Cuộc Tấn Công Trục Lợi Phổ Biến & Nguy Hiểm:**
   - **Chống Race Condition & Double-Spending:** Sử dụng Atomic Transaction kèm Khóa Luồng Người Dùng (user_mutex = threading.Lock() hoặc SQLite IMMEDIATE TRANSACTION), cô lập hoàn toàn tiến trình đọc số dư và trừ xu. Nếu 2 request tạo truyện gửi đến cùng 1 mili-giây khi tài khoản chỉ còn 8 xu, chỉ duy nhất 1 request thành công, request thứ hai bị từ chối 402 Payment Required ngay lập tức.
   - **Bảo Vệ Tính Toàn Vẹn Quyền Lực Phía Server (Absolute Server Authority):** Phía client không có bất kỳ quyền hạn nào gửi số xu hay chi phí lên. Server tự phân tích payload, đếm số token/từ dự kiến và áp đặt chi phí.
   - **Compensating Transaction Rollback (Hoàn Xu Tự Động):** Trường hợp LLM hoặc Diffusion API gặp lỗi 5xx hoặc timeout sau khi đã trừ xu, hệ thống tự động hoàn lại 100% số xu kèm mã giao dịch REFUND_FAILED_GENERATION.
   - **Sổ Cái Mật Mã Bất Biến (Cryptographic Ledger):** Bảng coin_transactions lưu vết kèm mã băm SHA-256 xâu chuỗi (tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp)), ngăn chặn việc sửa đổi số dư trái phép trực tiếp trong DB.

3. **Hệ Thống Chống Clone & Sybil Đa Lớp (Advanced Anti-Clone Guard):**
   - Chỉ tặng duy nhất 8 xu dùng thử cho thiết bị và IP mới.
   - Multi-Signal Fingerprinting: Canvas 2D Hash + WebGL Renderer Hash + AudioContext Frequency Hash + Screen Specs.
   - IP Subnet Throttling: Theo dõi theo dải mạng (/24 subnet), ngăn chặn việc dùng proxy xoay IP cùng dải để tạo tài khoản clone trục lợi.
   - Tài khoản clone tạo từ thiết bị/IP đã nhận thưởng sẽ có số dư khởi tạo = 0 xu.

---

### R4. Kiến Trúc Frontend Phân Lớp Không Xung Đột (ThreeUI 3D + Morphicons Pipeline)

Giải quyết triệt để vấn đề: Làm sao tích hợp cả hiệu ứng 3D (ThreeUI) và hoạt họa SVG biến hình (Morphicons) mượt mà 60 FPS, không triệt tiêu nhau, không vỡ layout và không crash WebGL?

1. **Kiến Trúc Phân Lớp Độc Lập (Decoupled Visual Pipeline Architecture):**
   - **Layer 0 — Ambient 3D Canvas (ThreeUI):**
     - Nền 3D Canvas chạy nền phía sau (position: fixed; inset: 0; z-index: 0; pointer-events: none;).
     - **Quản Lý Context WebGL Đơn Nhất (Single Shared Canvas):** Chỉ khởi tạo duy nhất 1 WebGLRenderer cho toàn trang, tái sử dụng scene, triệt tiêu 100% nguy cơ lỗi Too many active WebGL contexts.
     - **Tối Ưu Hiệu Năng Thông Minh:** Tích hợp IntersectionObserver và requestAnimationFrame có điều kiện: khi người dùng cuộn khỏi viewport hoặc chuyển tab (document.hidden), render loop tự động tạm dừng, CPU/GPU về 0%.
     - Hiệu ứng thị giác: Mạng lưới hạt ánh sáng 3D lơ lửng tương tác nhẹ theo con trỏ chuột kết hợp họa tiết Trống đồng Đông Sơn mờ ảo sang trọng.
   - **Layer 1 — Core Semantic DOM & 3D Interactive Cards:**
     - Sử dụng CSS 3D Transforms (perspective: 1000px, transform-style: preserve-3d) cho hiệu ứng Parallax Tilt trên các Card bài đăng và Khung truyện manga. Tách biệt hoàn toàn với WebGL canvas để bảo đảm hiệu năng 60 FPS ổn định.
   - **Layer 2 — SVG Morphing Micro-Interactions (Morphicons):**
     - Hoạt động độc lập trên DOM bằng SVG path interpolation và spring physics:
       - Biểu tượng Xu (Coin) xoay và morph thành huy hiệu số dư.
       - Nút Like morphing mượt mà từ đường nét thanh mảnh sang tim rực rỡ kèm micro-burst.
       - Bộ chọn Model AI morphing icon tương ứng 3 cấp độ (Flash → Versatile → Master).
     - Morphicons chạy trên luồng vector riêng, không can thiệp hay xung đột với WebGL state hay CSS 3D matrix.
   - **Layer 3 — Glassmorphism Overlay & Portals:**
     - Modal Nạp xu, Hộp thoại Messenger và Copilot được gắn vào React Portals với isolation: isolate và z-index: 50+. Ngăn chặn hiện tượng lỗi render layer (z-fighting) và hiện tượng vỡ nền mờ khi kết hợp với CSS 3D.
2. **Khả Năng Thích Ứng Mọi Thiết Bị (Graceful Degradation):**
   - Tự động nhận diện thiết bị yếu hoặc người dùng bật prefers-reduced-motion để tự động hạ cấp xuống hiệu ứng CSS thuần túy, đảm bảo trải nghiệm luôn trơn tru trên mọi cấu hình.

---

## Acceptance Criteria

### Adaptive Ontology & Xử Lý Ngoài Miền
- [ ] Khi chủ đề là Văn hóa/Lịch sử Việt Nam: Áp dụng đúng 100% xưng hô thuần Việt, Dynamic Scene-Graph văn hóa Việt và Comic cổ phục Việt (0% Hanfu, Kimono).
- [ ] Khi chủ đề là Ngoài Miền (Sci-Fi, Cyberpunk, Tây Âu, Isekai...): Hệ thống tự động nới lỏng ràng buộc, trích xuất thực thể mở linh hoạt, không áp đặt gượng ép cổ phục hay xưng hô phong kiến Việt.

### Mạng Xã Hội, Thuật Toán Gợi Ý & Open Messenger
- [ ] Bảng social_posts, post_interactions và user_interest_profiles vận hành chuẩn xác.
- [ ] Thuật toán gợi ý kết hợp đa tín hiệu (Content Cosine, Dwell Time, Comment sentiment, MMR diversity) hoạt động ổn định và giải quyết cold-start với bandit exploration.
- [ ] Tìm kiếm người dùng và nhắn tin 1-1 tự do giữa BẤT KỲ 2 người dùng nào theo thời gian thực.

### An Ninh Tiền Tệ & Chống Clone
- [ ] Atomic Transaction loại bỏ 100% rủi ro Race condition / Double spending khi gửi request đồng thời.
- [ ] Server hoàn toàn độc quyền tính toán chi phí xu; phớt lờ mọi can thiệp từ client.
- [ ] Tự động hoàn xu (REFUND_FAILED_GENERATION) 100% khi tiến trình gọi AI gặp sự cố.
- [ ] Bảng coin_transactions lưu vết đầy đủ, có mã băm toàn vẹn tx_hash SHA-256.
- [ ] Thiết bị hoặc IP đã từng nhận thưởng tân thủ sẽ nhận 0 xu khi đăng ký tài khoản clone.

### Trải Nghiệm Frontend Không Xung Đột (Morphicons + ThreeUI)
- [ ] Single WebGL context chạy ngầm 60 FPS, tự động pause khi tab ẩn hoặc ra khỏi màn hình.
- [ ] Morphicons SVG morphing trơn tru trên nút Like, Coin counter và Model switcher.
- [ ] Thẻ bài truyện tranh có hiệu ứng 3D Parallax Tilt mượt mà, không bị xung đột layer hay vỡ layout khi mở Modal nạp xu hoặc Messenger.

### Kiểm Thử Toàn Vẹn Hệ Thống
- [ ] Toàn bộ Backend Python (py_compile) biên dịch thành công 0 lỗi.
- [ ] Toàn bộ Frontend Next.js (npm run build) build sản xuất thành công 0 lỗi.
- [ ] Bộ test suite tự động kiểm thử toàn diện logic OOD ontology, banking security, recommendation ranking và chat messenger đạt 100% passed.

