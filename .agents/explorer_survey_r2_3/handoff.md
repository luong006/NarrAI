# HANDOFF REPORT — R3: ĐỒNG BỘ HÓA TUYỆT ĐỐI TEXT-TO-IMAGE & LOẠI BỎ ẢO GIÁC KHUNG TRANH MANGA

- **Agent**: `explorer_survey_r2_3`
- **Handoff Type**: Hard (Task Complete)
- **Target Recipient**: Orchestrator / Implementer (`3095f755-04d9-4da7-bb70-b02b1e63c909`)
- **Working Directory**: `e:\NarrAI\.agents\explorer_survey_r2_3`

---

## 1. OBSERVATION (Quan sát trực tiếp)

1. **Bỏ lọt Setting Anchor ở đa số Panel**:
   - Vị trí: `backend/agents/comic_agent.py`, dòng 626–630:
     ```python
     # Blend setting anchor to preserve background consistency across panels
     if setting_anchor and setting_anchor.lower() not in prompt.lower():
         raw_layout_check = str(item.get("layout_type", "square")).lower()
         if raw_layout_check == "wide" or i == 0 or "background" not in prompt.lower():
             prompt = f"{prompt}, setting: {setting_anchor}"
     ```
     Đối với các panel hội thoại thông thường (layout `square` hoặc `tall`, `i > 0`), nếu LLM sinh chuỗi `prompt` có chứa chữ `"background"` (ví dụ: `"blurred background"` hoặc `"classroom background"`), điều kiện trên trả về `False` và `setting_anchor` bị bỏ rơi hoàn toàn.

2. **Ô nhiễm ví dụ Cổ phong trong Prompt trích xuất**:
   - Vị trí: `backend/agents/comic_agent.py`, dòng 24–26 trong `DNA_EXTRACTOR_PROMPT`:
     ```python
     24:    - Exact garment type & cut: e.g. crisp button-up short-sleeve school uniform shirt, tailored blazer, high-collar martial arts robes (huyền bào), trench coat.
     25:    - Specific fabric texture & colors: e.g. pure white cotton, dark navy pleated skirt, black silk with gold embroidered dragon hem, crimson red mantle.
     26:    - Collar, Neck & Chest Accessories (ABSOLUTELY REQUIRED): ... (ribbon tie, bow tie, pendant, brooch, collar pin, chest badge, jade pendant on red cord).
     ```
     Việc chứa các ví dụ "huyền bào", "dragon hem", "jade pendant" dẫn đến hiện tượng in-context priming, khiến LLM gán trang phục cổ trang kiếm hiệp vào các truyện học đường hiện đại.

3. **Negative Prompt chưa ngăn chặn Cổ trang, Phong cách Âu Mỹ và Chữ rác**:
   - Vị trí: `backend/services/cloudflare_ai.py`, dòng 51:
     ```python
     "negative_prompt": "color, colorful, vibrant, saturated, photorealistic, photograph, photo, realistic, 3d render, digital painting, oil painting, watercolor, bright colors, rainbow, neon, warm tones, cool tones, skin color, blue sky, green grass, red, blue, yellow, orange, purple, pink, colored, CGI, real person, real face, real photo, camera"
     ```
     Negative prompt hoàn toàn không có từ khóa cấm trang phục cổ trang/vũ khí (`armor, historical robes, sword`), không cấm phong cách truyện tranh phương Tây (`western comic, american comic`), và không cấm chữ/bong bóng thoại vẽ đè lên canvas (`text, speech bubble, dialog balloon, watermark`).

4. **Style Prefix & Suffix chưa khóa chặt phong cách Manga học đường**:
   - Vị trí: `backend/agents/comic_agent.py`, dòng 9–10:
     ```python
     STYLE_PREFIX = "black and white manga, Japanese manga comic art, monochrome ink drawing on paper, "
     STYLE_SUFFIX = ", manga panel, screentone shading, bold ink outlines, high contrast black ink, clean lineart, no color, hand drawn 2D illustration, no photograph, no 3D render"
     ```
     Chưa chỉ định rõ trường phái học đường hiện đại (`Japanese high school manga aesthetic`), nét mực G-pen mảnh sạch (`clean G-pen lineart`) và họa tiết chấm tram sắc nét (`fine dot pattern tones`).

5. **Ngắt kết nối giữa Lời thoại tiếng Việt và Hành động của nhân vật trong khung tranh**:
   - Vị trí: `backend/agents/comic_agent.py`, dòng 795:
     ```python
     shot_desc = "expressive dialogue close-up, talking intensely" if is_dialogue else "dramatic narrative scene, engaging posture"
     ```
     Fallback của hệ thống áp đặt hành động chung chung "talking intensely", không phân tích hành vi cụ thể (ngồi tại bàn chép bài, ngắm cửa sổ, quay sang cười...) từ ngữ nghĩa tiếng Việt.

---

## 2. LOGIC CHAIN (Chuỗi suy luận từ quan sát đến kết luận)

1. Từ **Quan sát 1** (Setting Anchor chỉ gắn khi `layout=wide` hoặc `i=0` và không có từ `background`):
   -> Trong kịch bản 8–16 khung tranh, đa số các khung tranh là `square` (trung cảnh, cận cảnh thoại).
   -> Khi LLM tạo prompt không có neo bối cảnh rõ ràng, Diffusion model tự do chọn hậu cảnh ngẫu nhiên (đường phố, công viên, quán xá).
   -> Dẫn đến hiện tượng trôi dạt bối cảnh (scene-drift) vi phạm trực tiếp tiêu chí "100% khung tranh phản ánh chính xác không gian lớp học".

2. Từ **Quan sát 2** (Ví dụ huyền bào, long bào trong `DNA_EXTRACTOR_PROMPT`):
   -> LLM học theo mẫu (few-shot priming) và vô thức gán trang phục cổ phong cho nhân vật truyện học đường.
   -> Kết hợp với **Quan sát 3** (Negative Prompt không cấm cổ trang/kiếm hiệp), mô hình Diffusion không có cơ chế chặn các chi tiết áo choàng, kiếm, trang phục cổ trang xuất hiện giữa lớp học.

3. Từ **Quan sát 5** (Hành động bị hardcode hoặc LLM tự do bịa đặt prompt):
   -> Phụ đề tiếng Việt mô tả nhân vật cúi đầu cặm cụi viết vào sổ tay, nhưng tranh vẽ nhân vật lại đứng bên cửa sổ hoặc chỉ nhìn trân trân.
   -> Để triệt tiêu 100% ảo giác cử chỉ, pipeline bắt buộc phải trích xuất động từ hành động tiếng Việt (`cúi đầu chép bài`, `nhìn ra cửa sổ`, `quay sang bạn cùng bàn`) để ép thẳng vào visual action của prompt hình ảnh.

4. Từ **Quan sát 4** và **Quan sát 3** (Phong cách mỹ thuật và Negative prompt lỏng lẻo):
   -> Nâng cấp đồng bộ `STYLE_PREFIX`, `STYLE_SUFFIX` và `BASE_NEGATIVE_PROMPT + MODERN_SCHOOL_EXCLUSIONS` sẽ khóa cứng 100% nét vẽ Manga học đường đơn sắc (lineart sắc nét, screentone chuẩn mực, không lẫn chữ bẩn hay ám màu).

---

## 3. CAVEATS (Phạm vi chưa khảo sát & Giả định)

1. **Phạm vi khảo sát**: Tập trung hoàn toàn vào pipeline tạo kịch bản tranh (`comic_agent.py`), dịch vụ sinh ảnh Cloudflare (`cloudflare_ai.py`), định dạng dữ liệu DB (`models.py`) và hiển thị frontend (`ComicViewer.tsx`, `globals.css`).
2. **Giả định**: Bối cảnh chính của câu chuyện học đường hiện tại diễn ra trong khuôn viên trường học (chủ yếu là lớp học, hành lang, sân thượng). Nếu câu chuyện chuyển sang phân cảnh khác, Dynamic Scene-Graph Ontology (R2) sẽ truyền tên không gian mới vào `setting_dna`.
3. **Mô hình AI**: Cloudflare Workers AI sử dụng `@cf/bytedance/stable-diffusion-xl-lightning` và `@cf/lykon/dreamshaper-8-lcm`. Các mô hình này phản hồi rất tốt với G-pen lineart và screentone, miễn là không bị tràn 77 tokens của CLIP.

---

## 4. CONCLUSION (Kết luận & Đề xuất hành động)

Để giải quyết triệt để R3 và đạt 100% tiêu chí nghiệm thu:
1. **Khóa cứng phong cách Manga học đường đơn sắc hiện đại**: Cập nhật `STYLE_PREFIX` và `STYLE_SUFFIX` với các token chuyên biệt (`modern monochrome manga, Japanese school manga aesthetic, clean G-pen lineart, screentone shading, fine dot pattern tones`).
2. **Triệt tiêu ảo giác lệch cảnh bằng Spatial Scene Enclosure & Quarantine Filter**:
   - Thiết lập `SPATIAL_ENCLOSURES` cho lớp học, hành lang, sân thượng.
   - Bổ sung hàm `sanitize_spatial_prompt()` lọc sạch toàn bộ từ khóa không gian rác (`street, road, highway, car, palace, temple`) trước khi render.
   - Bắt buộc gắn `setting_anchor` vào **100% khung tranh** (không ngoại lệ).
3. **Đồng bộ hóa Hành vi/Cử chỉ từ lời thoại tiếng Việt**:
   - Triển khai `ACTION_GESTURE_MAPPINGS` và `extract_action_from_prose()` để chuyển đổi trực tiếp các động từ tiếng Việt thành hành động thị giác của nhân vật tại bàn học.
4. **Mở rộng Negative Prompt trong `cloudflare_ai.py`**:
   - Thêm `BASE_NEGATIVE_PROMPT` và `MODERN_SCHOOL_EXCLUSIONS` cấm cổ trang, kiếm hiệp, truyện tranh Âu Mỹ, bong bóng thoại rác.
5. **Làm sạch `DNA_EXTRACTOR_PROMPT`**:
   - Loại bỏ hoàn toàn ví dụ về "huyền bào", "long bào", thay bằng sơ mi trắng đồng phục, cà vạt/nơ navy, chân váy/quần âu.

---

## 5. VERIFICATION METHOD (Phương pháp kiểm chứng độc lập)

1. **Kiểm tra File Phân tích & Thiết kế chi tiết**:
   - Đọc báo cáo chi tiết tại: `e:\NarrAI\.agents\explorer_survey_r2_3\report.md`.

2. **Kiểm thử Đơn vị & Tích hợp (Unit & Integration Testing)**:
   Sau khi hoàn thiện triển khai, chạy bộ test:
   ```powershell
   python -m unittest backend/tests/test_comic_zero_truncation.py
   python -m unittest backend/tests/test_comic_dna_seed.py
   python -m unittest backend/tests/test_comic_ontology_visuals.py
   ```
   Tất cả các test phải pass 100%.

3. **Tạo Test Case mới cho R3 (`test_comic_modern_school_sync.py`)**:
   - Kiểm tra: Lời dẫn `"An cặm cụi ghi chép bài"` -> prompt có `"writing attentively in a notebook at wooden desk"`.
   - Kiểm tra: Prompt thô có chữ `"street, car"` -> bộ lọc Quarantine xóa sạch, chỉ giữ lại `"modern Japanese high school classroom interior"`.
   - Kiểm tra: Không có bất kỳ token cổ trang nào rò rỉ vào prompt.

4. **Biên dịch mã nguồn**:
   - Backend: `python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py`
   - Frontend: `npm run build` trong thư mục `frontend` đạt 0 lỗi.

5. **Điều kiện vô hiệu hóa (Invalidation Conditions)**:
   - Nếu phát hiện tranh vẽ nhân vật mặc đồ cổ trang hoặc xuất hiện cảnh đường phố giữa một phân đoạn lớp học, giải pháp bị coi là thất bại và cần kiểm tra lại `sanitize_spatial_prompt`.
