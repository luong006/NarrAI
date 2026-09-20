# Kiến Trúc Khóa Cứng Tính Nhất Quán Nhân Vật Manga (R2 Analysis Report)

## 1. Tóm Tắt Khảo Sát (Executive Summary)

Yêu cầu 2 (R2) của dự án NarrAI đặt mục tiêu:
1. **Nâng cấp `DNA_EXTRACTOR_PROMPT`**: Trích xuất chi tiết cực hạn về trang phục nhận diện (loại áo, màu sắc, phụ kiện cổ/ngực), kiểu tóc chính xác và đặc điểm khuôn mặt bất biến.
2. **Cơ chế Tiêm DNA Thông Minh (Smart DNA Injection)**: Nhận diện tự động và tiêm chính xác Visual DNA của nhân vật ngay cả khi prompt hoặc lời thoại sử dụng đại từ hoặc danh từ chung (`"cô bé"`, `"anh bạn cùng bàn"`, `"học sinh"`, `"cậu ấy"`), hỗ trợ nhiều nhân vật trong cùng khung tranh mà không bị cắt đứt.
3. **Tham số Seed Đồng Bộ (Deterministic Comic Seed)**: Chuẩn hóa việc tính toán và truyền seed trong `services/cloudflare_ai.py` và `main.py` đồng bộ theo `story_id` của bộ truyện, cố định không gian tiềm ẩn (latent space) của mô hình Diffusion trên toàn bộ chuỗi khung tranh.

Khảo sát mã nguồn thực tế đã phát hiện 3 điểm nghẽn kiến trúc lớn khiến ngoại hình nhân vật bị trôi dạt (visual drift), quần áo và khuôn mặt bị biến đổi giữa các cảnh, và các đại từ tiếng Việt không được nhận diện. Báo cáo này tài liệu hóa chi tiết hiện trạng, nguyên nhân gốc rễ và đề xuất giải pháp kỹ thuật cụ thể.

---

## 2. Hiện Trạng Kiến Trúc & Vị Trí Code Liên Quan

### 2.1. Bản đồ File và Chức năng

| File Path | Dòng Code | Thành phần / Hàm | Vai trò trong luồng Manga |
|---|---|---|---|
| `backend/agents/comic_agent.py` | L18 - L34 | `DNA_EXTRACTOR_PROMPT` | Prompt hệ thống trích xuất DNA nhân vật và aliases |
| `backend/agents/comic_agent.py` | L94 - L134 | `ComicDirectorAgent.extract_character_dna` | Gọi LLM trích xuất DNA, nạp từ `StoryMemory`, fallback |
| `backend/agents/comic_agent.py` | L178 - L250 | `ComicDirectorAgent._validate_panels` | Tiêm DNA nhân vật, bối cảnh, chuẩn hóa layout và thoại |
| `backend/agents/comic_agent.py` | L252 - L293 | `ComicDirectorAgent.generate_comic_script` | Điều phối sinh kịch bản Manga beat-by-beat từ văn bản truyện |
| `backend/agents/comic_agent.py` | L294 - L334 | `ComicDirectorAgent.generate_continuation` | Điều phối sinh tiếp các khung tranh từ phần truyện mới |
| `backend/agents/comic_agent.py` | L335 - L369 | `ComicDirectorAgent._create_structured_beat_fallback` | Bộ sinh khung tranh dự phòng khi LLM lỗi |
| `backend/services/cloudflare_ai.py` | L22 - L63 | `generate_image_cf` | Gọi Cloudflare Workers AI (SDXL Lightning, LCM, SDXL Base) |
| `backend/services/cloudflare_ai.py` | L65 - L113 | `get_cached_or_generate_image` | Quản lý cache đĩa `panel_{id}.jpg`, xử lý seed, fallback Pollinations |
| `backend/main.py` | L426 - L469 | `POST /api/comic/generate` | Khởi tạo chuyển thể truyện tranh, lưu DB |
| `backend/main.py` | L470 - L527 | `POST /api/comic/continue` | Chuyển thể tiếp các đoạn truyện mới viết thêm |
| `backend/main.py` | L528 - L548 | `GET /api/comic/image/{panel_id}` | Endpoint proxy ảnh khung tranh, tính toán seed |
| `backend/db/models.py` | L40 - L62 | Models `Comic` & `ComicPanel` | Bảng DB: `Comic.story_id`, `ComicPanel.comic_id`, `image_prompt` |
| `backend/tests/run_full_system_benchmark.py` | L117 - L176 | Test 4 & Test 5 | Benchmark kiểm tra trích xuất DNA, `_validate_panels`, cache đĩa |

---

## 3. Phân Tích Nguyên Nhân Gốc Rễ (Root Cause Analysis)

### 3.1. Điểm yếu của `DNA_EXTRACTOR_PROMPT` Hiện Tại
Trong `backend/agents/comic_agent.py` (L18 - L34):
```python
DNA_EXTRACTOR_PROMPT = """You are a lead character designer for a professional manga studio.
Analyze the story text and extract the EXACT, IMMUTABLE visual physical traits and signature costume for each named character.

CRITICAL INSTRUCTIONS FOR VISUAL CONSISTENCY:
1. Exact Hair: Specific hairstyle, parting, length, and texture (e.g. 'straight jet-black hair with blunt bangs and shoulder-length bob', 'messy textured dark hair parted in middle').
2. Exact Face & Age: Specific age, facial structure, eye shape (e.g. '17yo Vietnamese student, round gentle dark eyes, delicate nose, soft jawline').
3. Exact Immutable Outfit: You MUST specify the EXACT same signature clothes, down to collars, buttons, colors, and accessories (e.g. 'wearing high school uniform: crisp white button-down short-sleeve shirt with dark blue ribbon tie, pleated dark navy skirt').
4. Aliases: List of Vietnamese and English pronouns/terms used in the text for this character (e.g. ['An', 'cô bé', 'nữ sinh', 'cô', 'she', 'girl', 'student', 'bạn cùng bàn']).
...
"""
```
**Hạn chế phát hiện:**
1. **Thiếu quy tắc bắt buộc về "phụ kiện cổ/ngực" và cấu trúc áo cụ thể**: Prompt chỉ đưa nơ cổ (`dark blue ribbon tie`) vào phần ví dụ, không bắt buộc LLM phải luôn xác định rõ loại cổ áo (collar type), phụ kiện trước ngực (cà vạt, nơ, huy hiệu, vòng cổ, trâm cài ngực) và màu sắc tách biệt giữa áo trong / áo khoác / váy quần. Khi LLM xử lý truyện tiên hiệp hoặc trinh thám, nó thường mô tả chung chung (`"black robes"`, `"leather jacket"`), dẫn đến khung 1 áo cổ chữ V, khung 2 thành áo cổ tròn, khung 3 mất viền vàng.
2. **Thiếu trường dữ liệu Giới tính (`gender`) và Vai trò (`role`) trong JSON**: Kết quả trả về chỉ gồm `{"dna": "...", "aliases": [...]}`. Không có metadata giới tính/vai trò rõ ràng khiến hàm xử lý hạ tầng (downstream python code) không thể tự động suy luận xem `"cô bé"` hay `"anh bạn cùng bàn"` thuộc về nhân vật nào nếu LLM bỏ sót danh sách aliases.
3. **Nguồn khởi tạo `existing_dna` từ StoryMemory bị nghèo nàn**:
   Ở dòng 97-103:
   ```python
   if memory and memory.story_bible and memory.story_bible.characters:
       for c in memory.story_bible.characters:
           if isinstance(c, dict) and c.get("name") and c.get("appearance"):
               existing_dna[c["name"]] = {
                   "dna": c["appearance"],
                   "aliases": [c["name"].lower()]
               }
   ```
   Nếu nạp từ `StoryMemory`, `aliases` chỉ chứa duy nhất `[c["name"].lower()]` (tên nhân vật), hoàn toàn KHÔNG có đại từ hay danh từ chung tiếng Việt!
4. **Dự phòng (Fallback) khi LLM lỗi quá sơ sài**:
   Ở dòng 128-131:
   ```python
   existing_dna["Protagonist"] = {
       "dna": "young Asian person, dark neat hair, expressive eyes, wearing casual monochrome jacket over white shirt",
       "aliases": ["protagonist", "nhân vật chính", "người", "học sinh"]
   }
   ```
   Fallback này thiếu hẳn các đại từ thường gặp như `"cô bé"`, `"cậu ấy"`, `"anh bạn cùng bàn"`, `"nữ sinh"`, `"nam sinh"`.

---

### 3.2. Điểm yếu của Smart DNA Injection Hiện Tại
Trong `backend/agents/comic_agent.py` (L200 - L220):
```python
        for i, item in enumerate(script_data):
            prompt = item.get("image_prompt", "a detailed manga scene").strip()

            # Smart Character DNA injection
            char_injected = False
            for c in char_entry_list:
                matched = any(alias in prompt.lower() for alias in c["aliases"])
                if matched and c["dna"].lower() not in prompt.lower():
                    prompt = f"{c['dna']}, {prompt}"
                    char_injected = True
                    break

            # If no alias explicitly matched but prompt depicts a human figure, inject lead character's DNA
            human_indicators = ["girl", "boy", "student", "man", "woman", "person", "character", "face", "sitting", "standing", "looking", "staring", "writing", "holding", "talking", "crying", "walking", "running"]
            if not char_injected and char_entry_list:
                if any(k in prompt.lower() for k in human_indicators):
                    lead_dna = char_entry_list[0]["dna"]
                    if lead_dna.lower() not in prompt.lower():
                        prompt = f"{lead_dna}, {prompt}"
                        char_injected = True
```

**5 Lỗi Cấu Trúc Nghiêm Trọng:**
1. **Lệnh `break` ở dòng 210 làm biến mất nhân vật thứ hai (Multi-character Drop)**:
   Khi khung tranh có 2 nhân vật (ví dụ: Lý Tiêu và Hắc Ma Quân giao chiến, hoặc An trò chuyện cùng Minh), ngay khi nhân vật đầu tiên khớp, vòng lặp `break` ngay lập tức! Nhân vật thứ hai không bao giờ được tiêm DNA, khiến họ bị vẽ thành người lạ hoàn toàn khác.
2. **Chỉ kiểm tra `prompt.lower()`, bỏ qua hoàn toàn `dialogue_text`**:
   `BEAT_DIRECTOR_PROMPT` yêu cầu `image_prompt` viết bằng tiếng Anh (dưới 65 từ), còn `dialogue_text` viết bằng tiếng Việt.
   Trong rất nhiều trường hợp, đạo diễn kịch bản viết:
   `image_prompt`: `"Over-the-shoulder shot, turning around with a surprised look"` (không có tên nhân vật).
   `dialogue_text`: `"Anh bạn cùng bàn khẽ cười: 'Cậu làm xong bài chưa?'"` hoặc `"Cô bé ngạc nhiên."`
   Vì code chỉ tìm trong `prompt.lower()`, đại từ `"anh bạn cùng bàn"` và `"cô bé"` trong `dialogue_text` bị bỏ qua 100%! Sau đó code nhảy xuống `human_indicators`, thấy có chữ `"shot"` hoặc `"turning"` không khớp, hoặc khớp chữ `"face"` thì LUÔN LUÔN tiêm DNA của nhân vật số 0 (`char_entry_list[0]`), dẫn đến khung tranh thoại của Minh lại bị vẽ thành mặt của An!
3. **So khớp chuỗi con (`substring in`) gây ra False Positive tai hại**:
   `matched = any(alias in prompt.lower() for alias in c["aliases"])`
   Nếu nhân vật tên `"An"` (rất phổ biến tại VN), từ `"an"` sẽ khớp với:
   `"an establishing shot"`, `"another"`, `"clean"`, `"panoramic"`!
   Nếu alias có `"he"` hoặc `"cô"`, `"he"` khớp với `"the"`, `"when"`, `"where"`, `"sheet"`.
   Bất kỳ khung tranh nào có chữ `"an"` mạo từ tiếng Anh đều bị nhận nhầm là nhân vật An! Bắt buộc phải dùng Regex Word Boundaries (`\b`).
4. **Không có Từ điển Phân giải Ngữ nghĩa Đại từ (Semantic Pronoun Dictionary)**:
   Nếu tác giả viết: `"cô bé"`, `"anh bạn cùng bàn"`, `"học sinh"`, `"cậu ấy"`:
   - `"cô bé"`, `"cô ấy"`, `"nữ sinh"` cần được tự động map tới nhân vật Nữ / Nữ sinh.
   - `"anh bạn cùng bàn"`, `"bạn cùng bàn"` cần được map tới nhân vật Bạn cùng bàn / Nam sinh.
   - `"cậu ấy"`, `"nam sinh"`, `"chàng trai"` cần được map tới nhân vật Nam.
   Hiện tại nếu LLM quên sinh một trong các từ này vào `aliases`, hệ thống không có lớp heuristic fallback nào để ánh xạ.
5. **Thiếu làm sạch trùng lặp khi DNA được tiêm nhiều lần**:
   Nếu prompt đã có một phần mô tả, việc nối thô có thể làm dài prompt quá giới hạn 77 tokens của CLIP/SDXL.

---

### 3.3. Điểm yếu của Cơ chế Seed Hiện Tại
Trong `backend/services/cloudflare_ai.py` (L84 - L95):
```python
    # 2. Generate via Cloudflare Workers AI with deterministic seed
    img_bytes = None
    panel_seed = seed if seed is not None else (4289000 + (panel_id % 1000))
    try:
        img_bytes = generate_image_cf(prompt, seed=panel_seed)
    ...
```
Trong `backend/main.py` (L536 - L547):
```python
@app.get("/api/comic/image/{panel_id}")
def get_comic_image(panel_id: int, db: Session = Depends(get_db)):
    ...
    try:
        comic_id = panel.comic_id or 1
        comic_seed = (comic_id * 7919) % 1000000 + 42
        img_bytes, media_type = get_cached_or_generate_image(panel.id, panel.image_prompt, seed=comic_seed)
        return Response(content=img_bytes, media_type=media_type)
```

**Vấn đề phát hiện:**
1. **Thiếu hỗ trợ `story_id` trong `services/cloudflare_ai.py`**:
   Hàm `get_cached_or_generate_image(panel_id, prompt, seed=None)` không nhận `story_id`. Khi `seed` không được truyền vào (như trong các module kiểm thử hoặc các hàm gọi khác), nó mặc định tính:
   `panel_seed = (4289000 + (panel_id % 1000))`
   Vì mỗi khung tranh có `panel_id` tăng dần (1, 2, 3, 4, ...), mỗi khung tranh nhận một seed hoàn toàn khác nhau!
2. **`main.py` dùng `comic_id` thay vì `story_id` chuẩn**:
   Tại dòng 536, `comic_id = panel.comic_id or 1`.
   Nếu người dùng bấm "Viết tiếp truyện tranh" (Continue comic) tạo ra truyện mới hoặc các đợt chuyển thể khác nhau của cùng một câu chuyện, `comic_id` bị thay đổi.
   Trong cơ sở dữ liệu (`Comic` model ở `backend/db/models.py`), đối tượng `Comic` có trường `story_id = Column(Integer, ForeignKey('stories.id'))`.
   Cần lấy `story_id` làm gốc: `story_id = (panel.comic.story_id if panel.comic else None) or panel.comic_id or 1`.
3. **Tại sao Deterministic Seed lại quan trọng với Diffusion Manga?**
   Mô hình Diffusion (SDXL Lightning, LCM) bắt đầu quá trình khử nhiễu từ một tensor nhiễu ngẫu nhiên được sinh bởi `seed`.
   - Nếu mỗi panel có seed khác nhau: Cấu trúc khuôn mặt, đường nét cằm, tỷ lệ mắt/mũi, phong cách nét vẽ (line-weight) và hoa văn trang phục sẽ bị tái tạo ngẫu nhiên theo mỗi seed, ngay cả khi prompt giữ nguyên.
   - Nếu toàn bộ các panel trong cùng một bộ truyện dùng chung một `story_seed` đồng bộ: Tensor nhiễu nền được cố định. Mô hình sẽ giữ nguyên tỷ lệ khuôn mặt, kiểu tóc và trang phục nhận diện, sự thay đổi giữa các panel chỉ thuần túy đến từ góc máy (camera angle), hành động (action) và biểu cảm (expression) trong text prompt.

---

## 4. Đề Xuất Chiến Lược Kiến Trúc Chi Tiết

### Chiến lược 1: Nâng Cấp `DNA_EXTRACTOR_PROMPT` Đạt Độ Chi Tiết Cực Hạn

Nâng cấp `DNA_EXTRACTOR_PROMPT` trong `comic_agent.py` với các chỉ dẫn chuyên sâu:
- **Trang phục nhận diện cực hạn (Identifying Costume)**:
  - Bắt buộc xác định rõ: Kiểu áo (loại cổ: button-up collar, mandarin collar, sailor collar; tay áo: short-sleeve, long-sleeve, wide cuffs).
  - Phụ kiện cổ/ngực: Cà vạt (tie), nơ cổ (ribbon bow), dây chuyền (pendant), trâm cài (brooch), huy hiệu ngực (chest badge), hoặc thắt lưng/đai ngọc.
  - Màu sắc chuẩn xác: Trắng tinh, xanh navy, đen viền chỉ vàng kim, đỏ thẫm.
- **Kiểu tóc bất biến (Exact Hairstyle)**:
  - Kiểu cắt, độ dài, đường rẽ ngôi, tóc mái (blunt bangs, side-swept, curtain bangs), kết cấu (thẳng, lượn sóng, rối), phụ kiện tóc (dây buộc, trâm bạc, kẹp tóc).
- **Đặc điểm khuôn mặt (Immutable Facial Features)**:
  - Độ tuổi, hình dáng khuôn mặt, dáng mắt (almond eyes, round eyes, sharp gaze), đặc điểm phân biệt (vết sẹo, nốt ruồi, kính mắt).
- **Phân loại Metadata**:
  - Trả về cấu trúc JSON gồm: `dna` (chuỗi English prompt hoàn chỉnh), `aliases` (danh sách tên + đại từ VN/EN), `gender` (`female`/`male`), `role` (`protagonist`, `classmate_deskmate`, `antagonist`, v.v.).

### Chiến lược 2: Bộ Máy Tiêm DNA Thông Minh (Smart DNA Injection Engine)

Nâng cấp hàm `_validate_panels` trong `ComicDirectorAgent`:
1. **Lớp Từ Điển Đại Từ Ngữ Nghĩa (Semantic Pronoun Dictionary)**:
   Tự động bổ sung các đại từ phổ biến vào danh sách `aliases` của từng nhân vật dựa trên `gender` và `role`:
   - Nếu nhân vật là Nữ / Nữ sinh (`female`):
     Thêm: `["cô bé", "cô gái", "nữ sinh", "cô ấy", "cô", "nàng", "thiếu nữ", "bạn nữ", "girl", "schoolgirl", "female student"]`.
   - Nếu nhân vật là Nam / Nam sinh (`male`):
     Thêm: `["cậu bé", "chàng trai", "nam sinh", "cậu ấy", "anh ấy", "cậu ta", "anh ta", "hắn", "thiếu niên", "bạn nam", "boy", "schoolboy", "male student", "young man"]`.
   - Nếu vai trò liên quan bạn cùng bàn (`desk mate` / `classmate`):
     Thêm: `["anh bạn cùng bàn", "cô bạn cùng bàn", "bạn cùng bàn", "bạn học", "desk mate", "classmate"]`.
   - Nếu vai trò học sinh (`student`):
     Thêm: `["học sinh", "student"]`.
2. **So Khớp Hai Tầng An Toàn (Two-Tier Word-Boundary Matching)**:
   - Gom văn bản tìm kiếm: `search_text = f"{prompt} {dialogue_text}"`.
   - Sử dụng Regex Word Boundaries `\b` (`re.search(rf"\b{re.escape(alias)}\b", search_text, re.IGNORECASE)`):
     - Tránh tuyệt đối lỗi nhận nhầm `"an"` trong `"an establishing shot"`.
     - Nhận diện chuẩn xác các cụm từ tiếng Việt có dấu (`"cô bé"`, `"anh bạn cùng bàn"`, `"học sinh"`, `"cậu ấy"`).
3. **Hỗ Trợ Đa Nhân Vật (Multi-Character Panel Support)**:
   - Bỏ lệnh `break` tại dòng 210.
   - Thu thập tất cả nhân vật có mặt trong panel (`matched_characters`).
   - Tiêm lần lượt DNA của các nhân vật tham gia vào đầu `image_prompt`.
4. **Phân Giải Dự Phòng Theo Giới Tính (Heuristic Fallback by Gender Indicators)**:
   - Nếu không có alias nào khớp cụ thể nhưng có từ chỉ người:
     - Chứa từ chỉ nữ (`"girl"`, `"woman"`, `"cô gái"`, `"nữ"`) -> tiêm nhân vật nữ chính.
     - Chứa từ chỉ nam (`"boy"`, `"man"`, `"chàng trai"`, `"nam"`) -> tiêm nhân vật nam chính.
     - Còn lại -> tiêm nhân vật chính mặc định.

### Chiến lược 3: Deterministic Comic Seed Đồng Bộ Theo `story_id`

Nâng cấp `services/cloudflare_ai.py` và `main.py`:
1. Trong `services/cloudflare_ai.py`:
   Xây dựng hàm chuẩn:
   ```python
   def get_deterministic_comic_seed(story_id: int | None = None, comic_id: int | None = None) -> int:
       """
       Sinh seed đồng bộ, bất biến theo ID bộ truyện (hoặc ID comic)
       để khóa cứng không gian tiềm ẩn (latent noise) của mô hình diffusion.
       """
       anchor_id = story_id if (story_id is not None and story_id > 0) else (comic_id if (comic_id is not None and comic_id > 0) else 1)
       return (int(anchor_id) * 7919 + 104729) % 2147483647
   ```
2. Cập nhật `get_cached_or_generate_image`:
   - Thêm tham số `story_id: int | None = None, comic_id: int | None = None`.
   - Khi `seed is None`, tự động gọi `get_deterministic_comic_seed(story_id, comic_id)`.
   - Tuyệt đối loại bỏ công thức ngẫu nhiên `(4289000 + (panel_id % 1000))`!
3. Trong `backend/main.py`:
   Ở endpoint `GET /api/comic/image/{panel_id}`:
   - Truy vấn `panel.comic` để lấy `story_id`:
     `story_id = (panel.comic.story_id if panel.comic else None) or panel.comic_id or 1`
   - Tính seed: `comic_seed = get_deterministic_comic_seed(story_id=story_id, comic_id=panel.comic_id)`
   - Truyền `comic_seed` và `story_id` vào `get_cached_or_generate_image`.
   - Đồng bộ seed này vào cả URL chuyển hướng Pollinations dự phòng.

---

## 5. Bản Vẽ Chi Tiết Code Đề Xuất (Code Proposals)

### 5.1. Cập nhật `backend/agents/comic_agent.py`

#### A. Nâng cấp `DNA_EXTRACTOR_PROMPT`:
```python
# ==================== CHARACTER DNA EXTRACTOR ====================
DNA_EXTRACTOR_PROMPT = """You are a lead character designer and visual continuity director for a professional manga studio.
Analyze the Vietnamese story text and extract the EXACT, IMMUTABLE visual physical traits, identifying signature costume, and all aliases/pronouns for each character.

CRITICAL VISUAL CONTINUITY SPECIFICATIONS (EXTREME DETAIL REQUIRED):
1. Signature Identifying Costume (MANDATORY):
   - Exact garment type & cut: e.g. crisp button-up short-sleeve school uniform shirt, tailored blazer, high-collar martial arts robes (huyền bào), trench coat.
   - Specific fabric colors & patterns: e.g. pure white cotton, dark navy pleated skirt, black silk with gold embroidered dragon hem, crimson red mantle.
   - Collar, Neck & Chest Accessories (ABSOLUTELY REQUIRED): Specify exact collar style (button-down collar, mandarin collar, sailor collar) AND neck/chest accessories (small dark navy ribbon tie, red bow tie, gold collar pin, silver sword brooch, jade pendant on red cord, chest pocket academy badge).
   - Outerwear & layering: cardigan, cape, or sash belt if worn.
2. Exact Hairstyle & Head Details:
   - Specific cut, length, and texture: e.g. straight jet-black hair reaching collarbones, high ponytail tied with silver clasp, messy textured dark hair.
   - Bangs & parting: blunt bangs straight across forehead, curtain bangs parted in center, swept back.
   - Hair accessories: ribbon tie, hairpins, clips.
3. Immutable Facial Features:
   - Age, facial structure, eye shape and color: e.g. 17yo Vietnamese student, gentle almond dark eyes, sharp defined jawline, piercing cold amber eyes.
   - Permanent marks: beauty mark under right eye, scar across left eyebrow, glasses.
4. Comprehensive Aliases & Pronoun Registry:
   - Must include character names, nicknames.
   - Vietnamese pronouns & generic terms: "cô bé", "cậu bé", "cô gái", "chàng trai", "cậu ấy", "anh ấy", "cô ấy", "hắn", "nàng", "y", "tiểu tử", "nữ sinh", "nam sinh", "học sinh", "anh bạn cùng bàn", "bạn cùng bàn".
   - English equivalents: "she", "he", "the girl", "the boy", "schoolgirl", "schoolboy", "student", "classmate", "desk mate".
5. Metadata: Specify "gender" ("female" or "male") and primary "role" ("student", "desk_mate", "protagonist", "antagonist", "swordsman").

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{
  "An": {
    "gender": "female",
    "role": "student, desk mate, protagonist",
    "aliases": ["An", "cô bé", "nữ sinh", "cô", "cô ấy", "she", "girl", "schoolgirl", "female student", "bạn cùng bàn"],
    "dna": "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, straight jet-black hair with blunt bangs across forehead and shoulder-length bob, wearing crisp white short-sleeve school uniform button-up shirt with stiff collar, small dark navy ribbon tie pinned at collar, pleated dark navy skirt"
  }
}
"""
```

#### B. Nâng cấp `extract_character_dna`:
```python
    def extract_character_dna(self, story_text: str, memory: StoryMemory = None) -> dict:
        """Extracts immutable visual character DNA with explicit costumes and aliases."""
        existing_dna = {}
        prior_context = ""
        if memory and memory.story_bible and memory.story_bible.characters:
            prior_context = "PRIOR KNOWN CHARACTERS FROM STORY BIBLE:\n"
            for c in memory.story_bible.characters:
                if isinstance(c, dict) and c.get("name"):
                    c_name = c["name"]
                    c_app = c.get("appearance", "")
                    c_role = c.get("role", "")
                    prior_context += f"- {c_name} ({c_role}): {c_app}\n"
                    existing_dna[c_name] = {
                        "dna": c_app,
                        "aliases": [c_name.lower()]
                    }

        try:
            sample_text = story_text[:3500]
            user_msg = f"Extract Visual DNA and signature costumes for characters in this story:\n\n{prior_context}\nSTORY EXCERPT:\n{sample_text}"
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": DNA_EXTRACTOR_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        if isinstance(v, dict) and "dna" in v:
                            existing_dna[k] = v
                        elif isinstance(v, str):
                            existing_dna[k] = {"dna": v, "aliases": [k.lower()], "gender": "unknown"}
        except Exception as e:
            print(f"[Comic] Character DNA extraction fallback ({e})")

        # Guaranteed rich fallback if nothing extracted
        if not existing_dna:
            existing_dna["Protagonist"] = {
                "gender": "unknown",
                "role": "protagonist",
                "dna": "young Asian protagonist, neat dark hair, expressive dark eyes, wearing crisp white collared shirt with small dark ribbon tie, dark jacket",
                "aliases": ["protagonist", "nhân vật chính", "người", "học sinh", "cô bé", "cậu bé", "cậu ấy", "cô ấy", "anh bạn cùng bàn", "student"]
            }

        return existing_dna
```

#### C. Nâng cấp `_validate_panels` với Smart DNA Injection:
```python
    def _validate_panels(self, script_data, character_dna_map=None, setting_dna=None):
        """Validate, normalize layout, enforce character visual DNA, background anchor, and complete dialogue."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        dna_map = character_dna_map or {}
        setting_anchor = ""
        if setting_dna and isinstance(setting_dna, dict):
            setting_anchor = setting_dna.get("setting_anchor", "").strip()

        # Build normalized character lookup list with auto-enriched semantic pronouns
        char_entry_list = []
        for name, data in dna_map.items():
            if isinstance(data, dict):
                dna_text = data.get("dna", "")
                aliases = [name.lower()] + [str(a).lower() for a in data.get("aliases", [])]
                gender = str(data.get("gender", "")).lower()
                role = str(data.get("role", "")).lower()
            else:
                dna_text = str(data)
                aliases = [name.lower()]
                gender = ""
                role = ""

            # Auto-enrich aliases based on gender and role heuristics if not present
            dna_lower = dna_text.lower()
            is_female = "female" in gender or "schoolgirl" in dna_lower or "girl" in dna_lower or "cô bé" in aliases or "nữ" in role
            is_male = "male" in gender or "schoolboy" in dna_lower or "boy" in dna_lower or "cậu bé" in aliases or "nam" in role or "anh" in role

            enriched_aliases = set(aliases)
            if is_female:
                enriched_aliases.update(["cô bé", "cô gái", "nữ sinh", "cô ấy", "cô", "nàng", "thiếu nữ", "bạn nữ", "she", "her", "girl", "schoolgirl", "female student"])
            elif is_male:
                enriched_aliases.update(["cậu bé", "chàng trai", "nam sinh", "cậu ấy", "anh ấy", "cậu ta", "anh ta", "hắn", "thiếu niên", "bạn nam", "he", "him", "boy", "schoolboy", "male student", "young man"])

            if "desk" in role or "bàn" in role or "classmate" in role or any("bàn" in a for a in aliases):
                enriched_aliases.update(["anh bạn cùng bàn", "cô bạn cùng bàn", "bạn cùng bàn", "desk mate", "classmate", "bạn học"])

            if "student" in role or "học sinh" in role or "student" in dna_lower or "học sinh" in dna_lower:
                enriched_aliases.update(["học sinh", "student"])

            char_entry_list.append({
                "name": name,
                "dna": dna_text,
                "aliases": list(enriched_aliases),
                "is_female": is_female,
                "is_male": is_male
            })

        validated = []
        for i, item in enumerate(script_data):
            prompt = item.get("image_prompt", "a detailed manga scene").strip()
            dialogue = str(item.get("dialogue_text", "")).strip()
            search_text = f"{prompt} {dialogue}".lower()

            # Smart Character DNA injection: Match across prompt AND dialogue using word boundaries
            matched_chars = []
            for c in char_entry_list:
                for alias in c["aliases"]:
                    # Safe word boundary matching
                    pattern = rf"\b{re.escape(alias)}\b"
                    if re.search(pattern, search_text, re.IGNORECASE):
                        if c not in matched_chars:
                            matched_chars.append(c)
                        break

            # Fallback: if no alias matched but prompt depicts a human figure, resolve by gender/lead
            if not matched_chars and char_entry_list:
                human_indicators = ["girl", "boy", "student", "man", "woman", "person", "character", "face", "sitting", "standing", "looking", "staring", "writing", "holding", "talking", "crying", "walking", "running"]
                female_cues = ["girl", "woman", "schoolgirl", "female", "cô gái", "cô bé"]
                male_cues = ["boy", "man", "schoolboy", "male", "chàng trai", "cậu bé"]

                if any(re.search(rf"\b{re.escape(k)}\b", search_text, re.IGNORECASE) for k in human_indicators):
                    if any(re.search(rf"\b{re.escape(k)}\b", search_text, re.IGNORECASE) for k in female_cues):
                        females = [c for c in char_entry_list if c.get("is_female")]
                        selected = females[0] if females else char_entry_list[0]
                    elif any(re.search(rf"\b{re.escape(k)}\b", search_text, re.IGNORECASE) for k in male_cues):
                        males = [c for c in char_entry_list if c.get("is_male")]
                        selected = males[0] if males else char_entry_list[0]
                    else:
                        selected = char_entry_list[0]
                    matched_chars.append(selected)

            # Inject DNA for all matched characters without dropping secondary characters
            injected_dnas = []
            for c in matched_chars:
                if c["dna"].lower() not in prompt.lower():
                    injected_dnas.append(c["dna"])

            if injected_dnas:
                prompt = f"{', '.join(injected_dnas)}, {prompt}"

            # Blend setting anchor to preserve background consistency across panels
            if setting_anchor and setting_anchor.lower() not in prompt.lower():
                raw_layout_check = str(item.get("layout_type", "square")).lower()
                if raw_layout_check == "wide" or i == 0 or "background" not in prompt.lower():
                    prompt = f"{prompt}, setting: {setting_anchor}"

            # Clean duplicate style tags
            clean_prompt = prompt
            for tag in ["manga panel", "black and white", "monochrome", "screentone", "comic art"]:
                clean_prompt = re.sub(re.escape(tag), "", clean_prompt, flags=re.IGNORECASE)
            clean_prompt = clean_prompt.strip(" ,.-")

            final_prompt = f"{STYLE_PREFIX}{clean_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type", "square")).lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            # Clean complete sentence, NEVER truncate with "..." or chop words midway
            dialogue = re.sub(r'[\.\s…]{2,}$', '', dialogue).strip()
            if dialogue and dialogue[-1] not in ['.', '!', '?', '"', '”']:
                dialogue += '.'

            validated.append({
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            })
        return validated
```

---

### 5.2. Cập nhật `backend/services/cloudflare_ai.py`

```python
def get_deterministic_comic_seed(story_id: int | None = None, comic_id: int | None = None) -> int:
    """
    Computes a synchronized, deterministic seed based on canonical story ID (or comic ID).
    Forces Diffusion latent space to remain identical across all sequential panels,
    locking character facial symmetry, line weight, and costume details.
    """
    anchor_id = story_id if (story_id is not None and story_id > 0) else (comic_id if (comic_id is not None and comic_id > 0) else 1)
    # 7919 is a large prime multiplier, 104729 is a prime offset, bounded to positive 31-bit integer
    return (int(anchor_id) * 7919 + 104729) % 2147483647


def get_cached_or_generate_image(panel_id: int, prompt: str, seed: int | None = None, story_id: int | None = None, comic_id: int | None = None) -> tuple[bytes, str]:
    """
    Fetches image from disk cache if available.
    Otherwise attempts Cloudflare Workers AI with deterministic seed synchronized by story_id,
    with fallback to Pollinations B&W manga, then writes to disk cache.
    Returns (image_bytes, media_type).
    """
    cache_path = os.path.join(CACHE_DIR, f"panel_{panel_id}.jpg")
    
    # 1. Check local persistent disk cache
    if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 1000:
        try:
            with open(cache_path, "rb") as f:
                img_bytes = f.read()
            media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
            return img_bytes, media_type
        except Exception as e:
            print(f"[Comic Cache] Failed to read cached panel_{panel_id}: {e}")

    # 2. Determine synchronized deterministic seed
    if seed is not None:
        panel_seed = int(seed)
    else:
        panel_seed = get_deterministic_comic_seed(story_id=story_id, comic_id=comic_id)

    # 3. Generate via Cloudflare Workers AI with synchronized seed
    img_bytes = None
    try:
        img_bytes = generate_image_cf(prompt, seed=panel_seed)
    except Exception as e:
        print(f"[Comic Image] Cloudflare AI unavailable ({e}). Falling back to Pollinations...")
        try:
            bw_prompt = f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {prompt[:300]}, screentone, no color"
            safe_prompt = urllib.parse.quote(bw_prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={panel_seed}"
            resp = requests.get(fallback_url, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 500:
                img_bytes = resp.content
        except Exception as p_err:
            print(f"[Comic Image] Pollinations fallback also failed ({p_err})")

    if not img_bytes:
        raise Exception(f"Could not render image for panel {panel_id}")

    # 4. Save to disk cache
    try:
        with open(cache_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        print(f"[Comic Cache] Failed to save panel_{panel_id}: {e}")

    media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
    return img_bytes, media_type
```

---

### 5.3. Cập nhật `backend/main.py`

Tại endpoint `GET /api/comic/image/{panel_id}` (L528 - L548):
```python
from services.cloudflare_ai import generate_image_cf, get_cached_or_generate_image, get_deterministic_comic_seed

@app.get("/api/comic/image/{panel_id}")
def get_comic_image(panel_id: int, db: Session = Depends(get_db)):
    """Proxies comic panel image generation with local disk cache and Cloudflare Workers AI + Pollinations fallback."""
    panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
    if not panel:
        return Response(status_code=404)
        
    try:
        comic = db.query(Comic).filter(Comic.id == panel.comic_id).first() if panel.comic_id else None
        story_id = (comic.story_id if comic else None) or panel.comic_id or 1
        comic_seed = get_deterministic_comic_seed(story_id=story_id, comic_id=panel.comic_id)

        img_bytes, media_type = get_cached_or_generate_image(
            panel.id,
            panel.image_prompt,
            seed=comic_seed,
            story_id=story_id,
            comic_id=panel.comic_id
        )
        return Response(content=img_bytes, media_type=media_type)
    except Exception as e:
        print(f"[Comic Image] Generation failed ({e}), fallback redirect...")
        comic = db.query(Comic).filter(Comic.id == panel.comic_id).first() if panel.comic_id else None
        story_id = (comic.story_id if comic else None) or panel.comic_id or 1
        comic_seed = get_deterministic_comic_seed(story_id=story_id, comic_id=panel.comic_id)

        bw_prompt = f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {panel.image_prompt[:300]}, screentone, no color"
        safe_prompt = urllib.parse.quote(bw_prompt)
        fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={comic_seed}"
        return RedirectResponse(url=fallback_url)
```

---

## 6. Kế Hoạch Xác Minh Độc Lập (Verification Plan)

Khi triển khai giải pháp, các bước xác minh bao gồm:
1. **Kiểm tra biên dịch tĩnh (Static Verification)**:
   - Backend: `python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/main.py`
   - Đảm bảo 0 lỗi cú pháp và typing.
2. **Kiểm thử đơn vị Smart DNA Injection với các đại từ**:
   - Test case 1: Prompt chứa `"cô bé"` -> Phải tiêm chính xác DNA của nhân vật nữ với áo sơ mi trắng, nơ cổ, váy xếp ly.
   - Test case 2: Prompt chứa `"anh bạn cùng bàn"` -> Phải tiêm chính xác DNA của nhân vật nam sinh cùng bàn.
   - Test case 3: Prompt chứa cả hai nhân vật đối đầu -> Cả hai DNA đều được tiêm, không bị lệnh `break` cắt bỏ nhân vật thứ hai.
   - Test case 4: Prompt có chữ `"an establishing shot"` -> Không được nhận nhầm thành nhân vật tên "An".
3. **Kiểm thử tính tất định của Seed (Deterministic Seed Test)**:
   - Hai panel khác nhau trong cùng một `story_id = 42` phải sinh ra cùng một `comic_seed`.
   - Gọi `get_cached_or_generate_image` với cùng `story_id` phải sử dụng cùng seed.
4. **Tương thích toàn bộ Benchmark Hệ thống**:
   - Chạy kiểm thử: `python backend/tests/run_full_system_benchmark.py`
   - Test 4 (Comic Beat-by-Beat & Character Visual DNA) và Test 5 (Image Disk Cache) đều phải PASS 100%.
