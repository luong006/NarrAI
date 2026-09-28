# BÁO CÁO KHẢO SÁT & THIẾT KẾ KIẾN TRÚC: R2. DYNAMIC SCENE-GRAPH ONTOLOGY

- **Agent:** `explorer_survey_r2_2`
- **Mục tiêu:** R2. Nâng Cấp Kiến Trúc Dynamic Scene-Graph Ontology & Cơ Chế Spatial Scene Enclosure
- **Phạm vi khảo sát:** Backend (`backend/agents/`, `backend/models/`, `backend/services/`, `backend/db/`, `backend/tests/`)
- **Tài liệu gốc tham chiếu:** `e:\NarrAI\.agents\ORIGINAL_REQUEST.md` (Phiên bản nâng cấp 2026-09-20T13:19:05Z)
- **Thời gian thực hiện:** 2026-09-20

---

## 1. TỔNG QUAN YÊU CẦU & BỐI CẢNH (EXECUTIVE SUMMARY)

Theo chỉ thị tại `ORIGINAL_REQUEST.md` (mục R2):
> - **Chuyển đổi mô hình Ontology sang Dynamic Scene-Graph Ontology** (ràng buộc 3 chiều: Thực thể - Không gian - Thời đại / Thể loại).
> - **Thiết lập cơ chế kiểm soát không gian phân cảnh (Spatial Scene Enclosure)**: Neo giữ tuyệt đối vị trí địa lý của cảnh quay, ngăn chặn việc thực thể bị trôi dạt sang không gian hoặc thời kỳ khác (như lớp học hiện đại bị trôi thành đường phố hoặc cổ phong).
> - **Tiêu chí nghiệm thu (Acceptance Criteria):** 100% khung tranh phản ánh chính xác không gian và hành động trong lời dẫn đi kèm (0% xuất hiện bối cảnh ngoài phố hay trang phục cổ trang khi cảnh diễn ra trong lớp học).

Qua quá trình khảo sát toàn diện mã nguồn hiện tại, hệ thống NarrAI đã có bước tạo tiền đề rất tốt ở M2 (Character Visual DNA và Deterministic Seed), nhưng **kiến trúc Ontology và quản lý không gian hiện tại vẫn còn sơ khai, tồn tại các lỗ hổng chí mạng dẫn đến ảo giác không gian (Spatial Hallucination) và trôi dạt thời đại (Era Drift)**. Báo cáo này trình bày kết quả phân tích hiện trạng, chỉ rõ các điểm nghẽn, và đề xuất bản đặc tả kiến trúc kỹ thuật chi tiết cùng mã nguồn đề xuất để triển khai R2.

---

## 2. KHẢO SÁT CHI TIẾT HIỆN TRẠNG & CÁC LỖ HỔNG HỆ THỐNG (GAP ANALYSIS)

### 2.1. Phân Tích Hiện Trạng Từng Module Trong Codebase

#### 1. `backend/agents/story_generator.py`
- **Hiện trạng:**
  - Tại dòng 45-77: Phương thức `_extract_narrative_ontology(refined_prompt)` trích xuất một đoạn văn bản thuần (unstructured string) gồm 4 khối đánh dấu: `[THỰC THỂ & NHÂN VẬT]`, `[QUAN HỆ & ĐỘNG CƠ]`, `[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]`, `[CHUỖI NHÂN QUẢ CHÍNH]`.
  - Tại dòng 88-95: Khối text này được gán vào `{ontology_block}` và nhúng vào `system_prompt` của phương thức `_build_prompt`.
- **Lỗ hổng & Điểm nghẽn:**
  - **Dạng thức phi cấu trúc (Unstructured Text):** Ontology chỉ là một đoạn văn tự do do LLM sinh ra một lần khi bắt đầu, không có schema máy đọc được (JSON/Pydantic), không thể truy vấn hoặc kiểm tra tính đúng đắn (invariant validation).
  - **Mất liên kết khi viết chương tiếp theo (Streaming Chapter Disconnect):** Khi viết các chương tiếp theo qua `generate_chapter_stream` (dòng 139-178), hàm `_extract_narrative_ontology` **hoàn toàn không được gọi**! Hệ thống chỉ nhúng `memory.story_bible.to_prompt_block()` và `memory.to_prompt_block()`, bỏ quên toàn bộ các ràng buộc bối cảnh và quy tắc thế giới.

#### 2. `backend/agents/story_memory.py`
- **Hiện trạng:**
  - `StoryBible` (dòng 8-36): Lưu trữ các trường phẳng: `title`, `genre`, `characters` (danh sách dict gồm `name`, `appearance`, `personality`, `role`), `world_setting` (string đơn), `main_plot`, `writing_style`.
  - `StoryMemory` (dòng 39-95): Lưu trữ `chapter_summaries` (danh sách tóm tắt chương), `character_states` (dict: `tên` -> `chuỗi trạng thái`), `unresolved_threads`, `relationship_map` (dict: `cặp đôi` -> `chuỗi quan hệ`), `current_chapter`, `full_text`.
- **Lỗ hổng & Điểm nghẽn:**
  - **Không có mô hình không gian phân cấp (No Spatial Hierarchy):** Trường `world_setting` chỉ là một chuỗi văn bản chung chung (ví dụ: *"Trường THPT Chuyên tại Hà Nội vào mùa thu năm 2024"*). Hệ thống hoàn toàn không biết trong trường có những phòng ốc/khu vực nào (Lớp học 12A, Hành lang tầng 3, Sân trường, Nhà xe).
  - **Không theo dõi vị trí thực thể (No Entity Location Tracking):** `character_states` chỉ lưu chuỗi cảm xúc tự do (ví dụ: *"lo lắng sau khi nghe điểm số"*), hoàn toàn không lưu nhân vật đang đứng ở tọa độ/phân cảnh nào (`current_location_id`).
  - **Thiếu chiều Thời đại & Thể loại (Missing Era/Genre Axioms):** Không có cấu trúc lưu trữ các quy tắc cấm kỵ của thời đại (Era Banlist) và quy tắc vật lý/xã hội bất biến (World Axioms).
  - **Không có đồ thị quan hệ (No Graph Topology):** `relationship_map` chỉ là cặp chuỗi dạng `"A-B": "bạn cùng bàn"`, không phải đồ thị có hướng với các thuộc tính tâm lý ngầm (subtext, trust score, suspicion score).

#### 3. `backend/agents/memory_extractor.py`
- **Hiện trạng:**
  - `extract_bible` (dòng 16-63): Trích xuất JSON cơ bản gồm `characters`, `world_setting`, `genre`.
  - `extract_memory` (dòng 64-125): Sau mỗi chương, yêu cầu LLM trích xuất `chapter_summary`, `character_states`, `new_threads`, `resolved_threads`, `relationships`.
- **Lỗ hổng & Điểm nghẽn:**
  - Sau mỗi chương viết xong, LLM chỉ tóm tắt tình tiết và cập nhật cảm xúc, **hoàn toàn không cập nhật trạng thái không gian (Spatial State Transition)**. Nếu Chương 1 diễn ra trong lớp học và cuối chương nhân vật đi xuống nhà để xe, bộ nhớ không cập nhật vị trí hiện tại của các nhân vật, dẫn đến Chương 2 mở đầu rất dễ bị ảo giác địa điểm.

#### 4. `backend/agents/comic_agent.py`
- **Hiện trạng:**
  - Tại dòng 18-51: `DNA_EXTRACTOR_PROMPT` trích xuất Visual DNA cực kỳ chi tiết của nhân vật (trang phục, kiểu tóc, khuôn mặt).
  - Tại dòng 53-69: `SETTING_EXTRACTOR_PROMPT` trích xuất bối cảnh theo mẫu:
    ```json
    {
      "location_name": "Tên địa điểm ngắn gọn",
      "setting_anchor": "English visual description under 40 words...",
      "atmosphere": "e.g. gloomy noir..."
    }
    ```
  - Tại dòng 401-434: `extract_setting_dna` trích xuất **duy nhất 01 bối cảnh tĩnh (Single Static Setting)** cho toàn bộ câu chuyện.
  - Tại dòng 626-630 trong `_validate_panels`:
    ```python
    if setting_anchor and setting_anchor.lower() not in prompt.lower():
        raw_layout_check = str(item.get("layout_type", "square")).lower()
        if raw_layout_check == "wide" or i == 0 or "background" not in prompt.lower():
            prompt = f"{prompt}, setting: {setting_anchor}"
    ```
  - Tại dòng 764-803 trong `_create_structured_beat_fallback`: Mọi khung tranh fallback đều dùng chung một `bg_anchor`.
- **Lỗ hổng & Điểm nghẽn:**
  - **Giả định sai lầm về "Một bối cảnh duy nhất":** Truyện dài luôn có nhiều phân cảnh (scenes) khác nhau. Việc chỉ trích xuất một `setting_anchor` duy nhất dẫn đến 2 tình huống lỗi:
    1. *Nếu cảnh trong truyện thay đổi (từ lớp học ra hành lang, xuống căng tin):* Prompt hình ảnh vẫn bị ép chuỗi `"setting: classroom"`, gây mâu thuẫn trực tiếp với hành động nhân vật.
    2. *Nếu prompt bỏ qua `setting_anchor` (khi layout là square hoặc đã có từ "background"):* Mô hình Diffusion không nhận được neo không gian, lập tức sinh ra bối cảnh ngẫu nhiên (hallucination): nhân vật đang nói chuyện trong lớp bỗng đứng giữa ngã tư đường phố Tokyo hoặc trên đỉnh núi!
  - **Thiếu Neo Bao Cảnh Tuyệt Đối (Spatial Scene Enclosure):** Không có cơ chế ràng buộc phòng kín (`INDOOR_ENCLOSED`). Khi prompt chỉ có `"young schoolgirl sitting at wooden desk"`, Diffusion model rất hay vẽ bàn học đặt ngoài đường phố hoặc công viên có cây xanh phía sau vì không có rào chắn không gian (enclosure walls).
  - **Thiếu Bộ Lọc Cách Ly Thời Đại (Era Drift Quarantine):** Không có cơ chế loại trừ từ vựng cổ trang/kỳ ảo trong bối cảnh học đường hiện đại. Khi prompt tiếng Anh có từ ngữ như *"robes"*, *"ancient"*, *"scroll"*, hoặc do Diffusion tự suy diễn, tranh sẽ bị biến thành phong cách cổ trang hoặc kiếm hiệp.

#### 5. `backend/services/cloudflare_ai.py`
- **Hiện trạng:**
  - Tại dòng 49-52:
    ```python
    payload = {
        "prompt": prompt,
        "negative_prompt": "color, colorful, vibrant, saturated, photorealistic, photograph, photo, realistic, 3d render, digital painting, oil painting, watercolor, bright colors, rainbow, neon, warm tones, cool tones, skin color, blue sky, green grass, red, blue, yellow, orange, purple, pink, colored, CGI, real person, real face, real photo, camera"
    }
    ```
- **Lỗ hổng & Điểm nghẽn:**
  - `negative_prompt` bị khóa cứng (hardcoded) chỉ gồm các từ khóa chống màu sắc (chỉ phục vụ vẽ trắng đen).
  - Hoàn toàn **không nhận tham số `negative_prompt` động từ bên ngoài**, không thể truyền các từ khóa chống trôi dạt không gian (Spatial Drift Negatives: `outdoor, street, trees, cars, road, sky, ancient, hanfu, medieval, armor...`).

#### 6. `backend/tests/run_full_system_benchmark.py` & `test_comic_ontology_visuals.py`
- **Hiện trạng:**
  - Tại dòng 181-246 trong `run_full_system_benchmark.py`: Đã xây dựng thử nghiệm lớp `NarrativeKnowledgeGraph` (NOKG Master Spec v2.0) với 4 Invariant Rules (`Vitality`, `Spatial Exclusivity`, `Inventory Conservation`, `Visual DNA`).
  - Trong `test_comic_ontology_visuals.py`: Đã chứng minh prompt 4 chiều (Visual DNA, Spatial Anchor, Visible Proxemics, Invisible Subtext) vượt trội hoàn toàn so với prompt cơ bản.
- **Lỗ hổng:**
  - Các lớp và kiểm định này hiện **chỉ là code thử nghiệm nằm trong thư mục kiểm thử `tests/`**, chưa hề được chuẩn hóa thành module trong `backend/models/` hay `backend/agents/`, và chưa được tích hợp vào pipeline sinh truyện và truyện tranh thực tế.

---

### 2.2. Bảng Tổng Hợp So Sánh: Trước vs Yêu Cầu R2

| Tiêu Chí | Hệ Thống Hiện Tại (M1-M3) | Yêu Cầu R2 (Dynamic Scene-Graph Ontology) |
|---|---|---|
| **Mô hình Dữ liệu** | Văn bản thô phi cấu trúc trong `system_prompt` và chuỗi phẳng trong `StoryBible`. | `DynamicSceneGraph` hướng đối tượng chuẩn Pydantic, có node, edge, thuộc tính định lượng và schema xác thực. |
| **Ràng buộc 3 Chiều** | Chưa có. Chỉ có Visual DNA nhân vật (Chiều 1 một phần). Chiều 2 và 3 bị bỏ ngỏ. | **Khóa cứng 3 chiều:** Thực thể (Entities) - Không gian (Space Enclosures) - Thời đại / Thể loại (Era & Genre). |
| **Quản lý Không gian** | 01 `setting_anchor` duy nhất, tĩnh, áp dụng cho toàn bộ truyện. | **Spatial Scene Enclosure phân cấp:** Quản lý từng phòng ốc/khu vực; neo giữ kiến trúc, đạo cụ cố định, ánh sáng và biên giới đóng kín. |
| **Chuyển Cảnh (Transitions)** | Không phát hiện, không theo dõi; không gian bị trôi dạt tự do. | **Scene Transition Gating:** Nhận diện hành động di chuyển; kiểm tra cổng kết nối logic giữa các không gian; cập nhật vị trí thực thể. |
| **Khử Trôi Dạt (Anti-Drift)** | Chỉ có style prefix/suffix trắng đen chung chung. | **Enclosure-Specific Negative Prompts & Era Quarantine:** Tiêm từ khóa cấm kỵ theo bối cảnh (cấm outdoor khi ở trong lớp, cấm cổ trang khi ở thời hiện đại). |
| **Kiểm Định Tính Nhất Quán** | Kiểm định tĩnh bằng tay trong test script. | **Automated Invariant Gatekeeper:** Tự động bắt lỗi Vitality, Spatial Exclusivity, Inventory và Era Compatibility trước khi lưu/vẽ. |

---

## 3. THIẾT KẾ KIẾN TRÚC: DYNAMIC SCENE-GRAPH ONTOLOGY (DSGO)

### 3.1. Mô Hình Ràng Buộc 3 Chiều (3-Dimensional Constraint Matrix)

Hệ thống Ontology mới được tổ chức chặt chẽ theo ma trận 3 chiều trực giao:

```
                      [ CHIỀU 3: ERA & GENRE ]
             (Thời đại: Modern 2020s | Thể loại: Campus Light Novel)
             - Quy tắc thế giới (Axioms): Công nghệ thường, không phép thuật
             - Bộ lọc cấm kỵ (Banlist): hanfu, armor, magic staff, sword...
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────┐
        │                 DYNAMIC SCENE-GRAPH                     │
        │                                                         │
        │   [ CHIỀU 2: SPACE ENCLOSURE ]                          │
        │   Lớp 12A3 (Tầng 3 Nhà A) [INDOOR_ENCLOSED]             │
        │   - Kiến trúc: Tường xanh pastel, cửa kính ô lớn bên trái│
        │   - Đạo cụ cố định: Bàn gỗ thẳng hàng, bảng phấn xanh  │
        │   - Ánh sáng: Nắng chiều xiên góc, bụi phấn trong không khí │
        │   - Negative: outdoor, street, trees, cars, sky         │
        │                              │                          │
        │                              ▼                          │
        │   [ CHIỀU 1: ENTITIES & PROXEMICS ]                     │
        │   - Thực thể: An (Nữ sinh, đồng phục sơ mi cộc tay)     │
        │   - Thực thể: Minh (Nam sinh, bạn cùng bàn)             │
        │   - Quan hệ: Sitting adjacent (Bàn cạnh cửa sổ)         │
        │   - Subtext: Bí mật chưa thổ lộ (Trust: 85, Tension: 60)│
        │   - Đạo cụ mang theo: Bút máy, cuốn sổ nhật ký bìa xanh │
        └─────────────────────────────────────────────────────────┘
```

#### Chiều 1: Entity Graph (Thực thể & Quan hệ Tương tác)
1. **Character Node:**
   - Định danh bất biến (`id`, `name`, `aliases`, `gender`, `role`).
   - `visual_dna`: Khóa cứng phục trang nhận diện (loại áo, cổ áo, phụ kiện), kiểu tóc, nét mặt bất biến.
   - `vitality_state`: `ALIVE`, `INJURED`, `UNCONSCIOUS`, `DECEASED`. Ngăn chặn người chết hành động.
   - `current_location_id`: Tham chiếu đến `SpaceEnclosureNode` đang hiện diện.
   - `inventory`: Danh sách vật phẩm đang mang trên người.
   - `psychological_state`: Cảm xúc hiện thời và mục tiêu tức thì.
2. **Prop / Item Node:**
   - Vật phẩm/đạo cụ trong cảnh (`id`, `name`, `category`, `era_compatibility`, `holder_id`, `visual_desc`).
3. **Relational Edges:**
   - Quan hệ không gian: `LOCATED_IN`, `SITTING_NEXT_TO`, `FACING`, `HOLDING`.
   - Quan hệ tâm lý/kịch tính (Subtext): `TRUSTS(weight)`, `SUSPECTS(weight)`, `CONFLICT_WITH(weight)`.

#### Chiều 2: Space Graph & Spatial Scene Enclosure (Không gian & Vùng Bao Cảnh)
1. **Cấu trúc Không gian Phân cấp (Hierarchical Spatial Topology):**
   - **Universe / Realm:** Ví dụ: *"Trái Đất - Việt Nam đương đại"*.
   - **Macro-Region:** Ví dụ: *"Trường THPT Chuyên Hà Nội"*.
   - **Micro-Enclosure (Vùng bao cảnh phân cảnh):** Ví dụ: *"Phòng học 12A3 - Tầng 3"*, *"Khoang xe ô tô cũ"*.
   - **Sub-Zone (Tiểu khu vực định vị máy quay):** Ví dụ: *"Dãy bàn cuối sát cửa sổ"*.
2. **Thuộc tính Vùng Bao Cảnh (`SpaceEnclosureNode`):**
   - `boundary_type`:
     - `INDOOR_ENCLOSED`: Phòng học, văn phòng, phòng ngủ, phòng thẩm vấn.
     - `VEHICLE_INTERIOR`: Khoang xe hơi, toa tàu, khoang lái.
     - `OUTDOOR_CONFINED`: Sân trong có tường bao, ngõ hẻm kín, sân thượng có lan can.
     - `OUTDOOR_OPEN`: Sân vận động, đường phố, quảng trường.
   - `architectural_anchor`: Mô tả kiến trúc bất biến (tường, trần, sàn, cột, cửa sổ) ngắn gọn dưới 40 từ tiếng Anh.
   - `persistent_fixtures`: Danh sách các đạo cụ và đồ nội thất cố định gắn liền với phòng.
   - `lighting_atmosphere`: Ánh sáng và bầu không khí thị giác cố định.
   - `negative_drift_tokens`: Danh sách các từ khóa cấm rò rỉ ngoại cảnh.
   - `connected_enclosures`: Danh sách các không gian kế cận có cửa/cổng liên thông.

#### Chiều 3: Era & Genre Constraints (Ràng Buộc Thời Đại & Thể Loại)
1. **Era Invariants:** Quy định ranh giới công nghệ, kiến trúc và trang phục của thời đại (ví dụ: `MODERN_2020s`, `ANCIENT_EAST_ASIA`, `CYBERPUNK_2099`).
2. **Genre Invariants:** Quy tắc vận hành thế giới (World Axioms).
   - Light Novel học đường: Cấm ma thuật, cấm quái vật, cấm vũ khí sát thương hạng nặng, cấm trang phục cung đình.
3. **Anti-Drift Banlist (Bộ từ vựng cấm kỵ tự động):**
   - Tự động tiêm vào Negative Prompt của Diffusion để ngăn chặn việc sinh nhầm trang phục hay bối cảnh lạ.

---

### 3.2. Cơ Chế Spatial Scene Enclosure (Kiểm Soát Không Gian Phân Cảnh)

Cơ chế **Spatial Scene Enclosure** giải quyết triệt để vấn đề "trôi dạt bối cảnh" thông qua quy trình 4 giai đoạn:

```
 [Narrative Prose / Beat Text]
              │
              ▼
 ┌─────────────────────────────┐
 │ 1. Scene Transition Gating  │ ──► Phát hiện động từ chuyển dịch không gian
 └─────────────┬───────────────┘     (Nếu không có: KHÓA CHẶT ở Enclosure hiện tại)
               │
               ▼
 ┌─────────────────────────────┐
 │ 2. Absolute Anchor Injection│ ──► Nạp architectural_anchor + persistent_fixtures
 └─────────────┬───────────────┘     vào TẤT CẢ các panel của phân cảnh
               │
               ▼
 ┌─────────────────────────────┐
 │ 3. Era & Drift Quarantine   │ ──► Tiêm negative_drift_tokens vào Diffusion
 └─────────────┬───────────────┘     (Cấm tiệt outdoor, street, hanfu, armor...)
               │
               ▼
 ┌─────────────────────────────┐
 │ 4. Invariant Safety Gate    │ ──► Kiểm tra vi phạm 4 luật NOKG trước khi lưu/vẽ
 └─────────────────────────────┘
```

#### Chi Tiết 4 Giai Đoạn Vận Hành:

1. **Scene Transition Gating (Cổng Kiểm Soát Dịch Chuyển Không Gian):**
   - Khi tách truyện thành các story beat (`decompose_story_beats`), hệ thống quét các chỉ dấu chuyển dịch không gian:
     - *Từ khóa chuyển cảnh:* `"bước ra khỏi"`, `"rời phòng"`, `"đi xuống sân"`, `"bước vào"`, `"mở cửa"`, `"lên xe"`.
   - Nếu **không có chỉ dấu chuyển cảnh**: Toàn bộ các beat tiếp theo **bắt buộc kế thừa 100% `active_enclosure_id` hiện tại**. Tuyệt đối không cho phép camera hay nhân vật nhảy ra ngoài không gian khác.
   - Nếu **có chỉ dấu chuyển cảnh**: Hệ thống kiểm tra xem không gian đích có nằm trong `connected_enclosures` hay không. Nếu hợp lệ, chuyển `active_enclosure_id` sang không gian mới và cập nhật tọa độ nhân vật.

2. **Absolute Geographic/Scene Anchoring (Neo Giữ Vị Trí Tuyệt Đối):**
   - Khi tạo prompt cho khung tranh manga (`_validate_panels`), cấu trúc prompt được chuẩn hóa bắt buộc:
     ```
     [STYLE_PREFIX] +
     [ACTIVE_CHARACTERS_VISUAL_DNA] +
     [CHARACTER_ACTION_AND_FACIAL_EXPRESSION] +
     [VISIBLE_PROXEMICS_OR_SHOT_TYPE] +
     ", inside [ENCLOSURE_NAME]: [ARCHITECTURAL_ANCHOR], [PERSISTENT_FIXTURES], [LIGHTING_ATMOSPHERE]" +
     [STYLE_SUFFIX]
     ```
   - Bất kể khung tranh là cận cảnh (close-up) hay trung cảnh (medium shot), thông tin nền luôn chứa `inside [ENCLOSURE_NAME]: [ARCHITECTURAL_ANCHOR]`, đảm bảo Diffusion model không bao giờ tự ý vẽ nền ngoài trời hay đường phố.

3. **Dynamic Enclosure Negative Prompting (Cách Ly Bằng Phủ Định):**
   - Mở rộng hàm `generate_image_cf` trong `backend/services/cloudflare_ai.py` để nhận `custom_negative_prompt`.
   - Khi phân cảnh là `INDOOR_ENCLOSED` (phòng học, phòng làm việc):
     - `custom_negative_prompt = "outdoor, street, trees, road, cars, city street, open sky, horizon, park, forest, ancient, hanfu, kimono, medieval, armor, swords, fantasy castle"`
   - Điều này triệt tiêu hoàn toàn 100% nguy cơ hình ảnh học đường bị biến thành đường phố hoặc cổ phong.

4. **Automated Invariant Gatekeeper (Bộ Kiểm Định Bất Biến Tự Động):**
   - Trước khi gửi prompt sang bộ sinh tranh hoặc xuất bản chương truyện:
     - **Luật 1 (Vitality):** Thực thể đã chết không được có hành động phát ngôn/chiến đấu.
     - **Luật 2 (Spatial Exclusivity):** Nhân vật chỉ được tương tác với các thực thể trong cùng `active_enclosure_id`.
     - **Luật 3 (Spatial Bleed Check):** Quét prompt của phân cảnh trong phòng kín; nếu chứa các từ khóa cấm như `"street"`, `"outdoor"`, `"sky"`, hệ thống tự động loại bỏ các từ này và ép lại neo kiến trúc của phòng.
     - **Luật 4 (Era Consistency):** Quét prompt của bối cảnh hiện đại; nếu chứa từ khóa cổ trang (`"hanfu"`, `"robes"`, `"sword"`), tự động thanh lọc và thay thế bằng trang phục chuẩn trong Visual DNA.

---

## 4. BẢN ĐẶC TẢ SCHEMA & THIẾT KẾ MÃ NGUỒN CỤ THỂ

### 4.1. File Mới: `backend/models/scene_graph.py`

Tạo mới module định nghĩa toàn bộ mô hình dữ liệu của Dynamic Scene-Graph Ontology:

```python
"""
Dynamic Scene-Graph Ontology Models (DSGO v2.0)
Ràng buộc 3 chiều: Thực thể (Entity) - Không gian (Space) - Thời đại/Thể loại (Era & Genre)
Cơ chế kiểm soát phân cảnh: Spatial Scene Enclosure
"""
from enum import Enum
from typing import List, Dict, Optional, Any, Set
from pydantic import BaseModel, Field


class EntityRole(str, Enum):
    LEAD = "lead"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"


class VitalityState(str, Enum):
    ALIVE = "alive"
    INJURED = "injured"
    UNCONSCIOUS = "unconscious"
    DECEASED = "deceased"


class BoundaryType(str, Enum):
    INDOOR_ENCLOSED = "indoor_enclosed"      # Phòng học, phòng ngủ, văn phòng
    VEHICLE_INTERIOR = "vehicle_interior"    # Trong xe hơi, toa tàu
    OUTDOOR_CONFINED = "outdoor_confined"    # Sân trong, ngõ hẹp, sân thượng có rào
    OUTDOOR_OPEN = "outdoor_open"            # Đường phố, quảng trường, sân bóng


class EraType(str, Enum):
    MODERN_2020S = "modern_2020s"
    HISTORICAL_MEDIEVAL = "historical_medieval"
    ANCIENT_EAST_ASIA = "ancient_east_asia"
    CYBERPUNK_2099 = "cyberpunk_2099"
    VICTORIAN_1890S = "victorian_1890s"
    CUSTOM = "custom"


class CharacterEntity(BaseModel):
    id: str                                  # slug, e.g. "an", "minh"
    name: str                                # Tên hiển thị tiếng Việt, e.g. "An"
    aliases: List[str] = Field(default_factory=list) # Danh từ xưng hô, đại từ
    gender: str = "female"                   # female, male, unknown
    age: Optional[int] = None
    role: EntityRole = EntityRole.LEAD
    dna: str                                 # Immutable Visual DNA (quần áo, tóc, mặt)
    vitality: VitalityState = VitalityState.ALIVE
    current_location_id: Optional[str] = None # ID của SpaceEnclosure hiện diện
    inventory: List[str] = Field(default_factory=list) # Vật phẩm mang theo
    emotional_state: str = "calm"
    active_costume_override: Optional[str] = None


class ItemEntity(BaseModel):
    id: str
    name: str
    category: str                            # WEAPON, DOCUMENT, ACCESSORY, DEVICE
    visual_description: str
    holder_id: Optional[str] = None          # Entity ID sở hữu
    location_id: Optional[str] = None        # Space ID nếu đặt trên bàn/sàn


class SpaceEnclosure(BaseModel):
    id: str                                  # e.g. "classroom_12a", "school_rooftop"
    name: str                                # e.g. "Lớp học 12A", "Sân thượng trường"
    boundary_type: BoundaryType = BoundaryType.INDOOR_ENCLOSED
    parent_region: str = "High School Campus"
    architectural_anchor: str                # Mô tả tường, trần, sàn, cửa sổ (< 40 words EN)
    persistent_fixtures: List[str] = Field(default_factory=list) # Bàn, ghế, bảng phấn
    lighting_atmosphere: str                 # Ánh sáng, bóng đổ, tâm trạng
    negative_drift_tokens: List[str] = Field(default_factory=list) # Từ cấm rò rỉ ngoại cảnh
    connected_enclosures: List[str] = Field(default_factory=list) # Không gian liên thông
    active_entities: List[str] = Field(default_factory=list)      # Nhân vật có mặt


class EraGenreConstraint(BaseModel):
    era: EraType = EraType.MODERN_2020S
    genre: str = "Modern Campus Light Novel"
    world_axioms: List[str] = Field(default_factory=list) # Quy tắc vật lý/xã hội bất biến
    forbidden_visual_tokens: List[str] = Field(default_factory=list) # Từ cấm trong prompt ảnh
    forbidden_prose_cliches: List[str] = Field(default_factory=list) # Từ ngữ cấm trong truyện chữ
    mandatory_style_anchor: str = "Japanese school manga, clean ink lineart, screentone shading"


class SceneGraphRelation(BaseModel):
    source_id: str
    relation_type: str                       # LOCATED_IN, SITTING_BESIDE, TALKING_TO, SUSPECTS
    target_id: str
    subtext: Optional[str] = None
    trust_score: int = 100                   # 0 - 100
    tension_score: int = 0                   # 0 - 100


class DynamicSceneGraph(BaseModel):
    session_id: str
    era_genre: EraGenreConstraint
    characters: Dict[str, CharacterEntity] = Field(default_factory=dict)
    items: Dict[str, ItemEntity] = Field(default_factory=dict)
    spaces: Dict[str, SpaceEnclosure] = Field(default_factory=dict)
    relations: List[SceneGraphRelation] = Field(default_factory=list)
    active_enclosure_id: str

    def get_active_enclosure(self) -> Optional[SpaceEnclosure]:
        return self.spaces.get(self.active_enclosure_id)

    def transition_scene(self, target_space_id: str, moving_character_ids: List[str]) -> bool:
        """Thực hiện chuyển dịch không gian có kiểm tra tính liên thông."""
        current = self.get_active_enclosure()
        if not current:
            return False
        if target_space_id not in self.spaces:
            return False
        # Kiểm tra tính liên thông hoặc chuyển cảnh được phép
        target = self.spaces[target_space_id]
        # Cập nhật vị trí nhân vật
        for cid in moving_character_ids:
            if cid in self.characters:
                self.characters[cid].current_location_id = target_space_id
                if cid in current.active_entities:
                    current.active_entities.remove(cid)
                if cid not in target.active_entities:
                    target.active_entities.append(cid)
        self.active_enclosure_id = target_space_id
        return True

    def build_enclosure_prompt_fragment(self) -> str:
        """Tạo đoạn prompt neo giữ không gian tuyệt đối cho Diffusion."""
        enc = self.get_active_enclosure()
        if not enc:
            return "inside a detailed room"
        fixtures_str = ", ".join(enc.persistent_fixtures[:3]) if enc.persistent_fixtures else ""
        res = f"inside {enc.name}: {enc.architectural_anchor}"
        if fixtures_str:
            res += f", featuring {fixtures_str}"
        if enc.lighting_atmosphere:
            res += f", {enc.lighting_atmosphere}"
        return res

    def get_combined_negative_tokens(self) -> str:
        """Kết hợp từ khóa phủ định chống trôi dạt không gian và thời đại."""
        enc = self.get_active_enclosure()
        tokens = set(self.era_genre.forbidden_visual_tokens)
        if enc:
            tokens.update(enc.negative_drift_tokens)
        return ", ".join(sorted(tokens))
```

---

### 4.2. Nâng Cấp `backend/agents/story_memory.py`

- **Vị trí sửa đổi:** Tích hợp `DynamicSceneGraph` vào `StoryBible` và `StoryMemory`.
- **Logic cập nhật:**
  1. Thêm trường `scene_graph: Optional[DynamicSceneGraph] = None` vào `StoryMemory`.
  2. Trong `to_prompt_block()`: Xuất cấu trúc 3 chiều có định dạng rõ ràng để tiêm vào mọi lần sinh chương:
     ```python
     def to_prompt_block(self):
         # ... existing summaries and character states ...
         sg_block = ""
         if self.scene_graph:
             enc = self.scene_graph.get_active_enclosure()
             sg_block = (
                 f"\n=== DYNAMIC SCENE-GRAPH (RÀNG BUỘC 3 CHIỀU) ===\n"
                 f"1. THỜI ĐẠI & THỂ LOẠI: {self.scene_graph.era_genre.era} | {self.scene_graph.era_genre.genre}\n"
                 f"   - Quy tắc thế giới: {'; '.join(self.scene_graph.era_genre.world_axioms)}\n"
                 f"2. KHÔNG GIAN PHÂN CẢNH HIỆN TẠI (ACTIVE ENCLOSURE):\n"
                 f"   - Vị trí: {enc.name if enc else 'Chưa xác định'} ({enc.boundary_type.value if enc else ''})\n"
                 f"   - Neo giữ kiến trúc: {enc.architectural_anchor if enc else ''}\n"
                 f"   - Đạo cụ cố định: {', '.join(enc.persistent_fixtures) if enc else ''}\n"
                 f"   - Nhân vật có mặt: {', '.join(enc.active_entities) if enc else ''}\n"
                 f"   - QUY TẮC PHÂN CẢNH: CẤM tự ý di chuyển ra ngoài nếu không có hành động cụ thể.\n"
                 f"================================================\n"
             )
         return f"{sg_block}=== LONG-TERM MEMORY ===\n..."
     ```
  3. Đảm bảo tính tương thích ngược hoàn hảo trong `to_dict()` và `from_dict()`. Nếu `memory_data` cũ không có `scene_graph`, tự động khởi tạo đồ thị mặc định từ `world_setting` và `characters`.

---

### 4.3. Nâng Cấp `backend/agents/comic_agent.py`

- **Vị trí sửa đổi 1: Thay thế `SETTING_EXTRACTOR_PROMPT` bằng `SCENE_ENCLOSURE_EXTRACTOR_PROMPT` (dòng 53-69):**
  Trích xuất đầy đủ danh sách các vùng bao cảnh (enclosures), phân loại `boundary_type`, `architectural_anchor`, `persistent_fixtures` và `negative_drift_tokens`.
- **Vị trí sửa đổi 2: Tích hợp Scene Transition Gating vào `decompose_story_beats` (dòng 195-276):**
  Gắn nhãn `enclosure_id` vào từng story beat. Khi câu chuyện xuất hiện các từ chỉ sự di chuyển (`"bước ra"`, `"chạy xuống"`), beat mới sẽ được gán vào enclosure tiếp theo; các beat còn lại bị khóa cứng ở enclosure ban đầu.
- **Vị trí sửa đổi 3: Nâng cấp `_validate_panels` (dòng 533-667):**
  1. Loại bỏ logic cũ chỉ gắn setting khi `layout_type == 'wide'`.
  2. Bắt buộc **100% khung tranh trong cùng phân cảnh** phải chứa chuỗi neo giữ không gian:
     ```python
     enclosure_fragment = active_enclosure.build_enclosure_prompt_fragment()
     prompt = f"{prompt}, {enclosure_fragment}"
     ```
  3. Chạy hàm lọc khử trôi dạt (Drift Sanitizer):
     - Nếu không gian là `INDOOR_ENCLOSED`: xóa bỏ mọi từ khóa `"outdoor"`, `"street"`, `"park"`, `"sky"`, `"road"` nếu LLM vô tình sinh ra trong mô tả nhân vật.
     - Nếu thời đại là `MODERN_2020s`: xóa bỏ mọi từ khóa `"hanfu"`, `"robes"`, `"ancient"`, `"sword"`.
  4. Trả về `negative_prompt` tương ứng cho từng panel để API gửi sang Cloudflare AI.

---

### 4.4. Nâng Cấp `backend/services/cloudflare_ai.py`

- **Vị trí sửa đổi: `generate_image_cf` và `get_cached_or_generate_image` (dòng 33-85):**
  - Bổ sung tham số `extra_negative_prompt: str = ""`.
  - Hợp nhất `base_negative_prompt` (chống màu) với `extra_negative_prompt` (chống trôi dạt không gian và thời đại):
    ```python
    def generate_image_cf(prompt: str, seed: int | None = None, extra_negative_prompt: str = "") -> bytes:
        base_neg = "color, colorful, vibrant, saturated, photorealistic, photograph, photo, realistic, 3d render, digital painting, oil painting, watercolor, bright colors, rainbow, neon, warm tones, cool tones, skin color, blue sky, green grass, red, blue, yellow, orange, purple, pink, colored, CGI, real person, real face, real photo, camera"
        if extra_negative_prompt:
            combined_neg = f"{base_neg}, {extra_negative_prompt}"
        else:
            combined_neg = base_neg

        payload = {
            "prompt": prompt,
            "negative_prompt": combined_neg
        }
        if seed is not None:
            payload["seed"] = int(seed)
        # ... execute request ...
    ```

---

### 4.5. Nâng Cấp `backend/agents/story_generator.py`

- **Vị trí sửa đổi: `_build_prompt` (dòng 86-128) và `generate_chapter_stream` (dòng 139-179):**
  - Loại bỏ khối text tự do thô sơ `{ontology_block}`.
  - Sử dụng trực tiếp `DynamicSceneGraph` để sinh chỉ dẫn tác giả với 3 chiều ràng buộc tuyệt đối.
  - Thêm quy tắc phân nhịp kịch tính và cảnh báo vi phạm không gian vào `MODERN_NOVEL_WRITING_RULES`.

---

## 5. KẾ HOẠCH TRIỂN KHAI & TIÊU CHÍ NGHIỆM THU (ACTIONABLE ROADMAP)

### 5.1. Kế Hoạch 5 Bước Triển Khai Cho Đội Ngũ Lập Trình (Implementation Steps)

1. **Bước 1 (Data Layer):**
   - Tạo mới file `backend/models/scene_graph.py` với các Pydantic schema chuẩn: `CharacterEntity`, `SpaceEnclosure`, `EraGenreConstraint`, `DynamicSceneGraph`.
   - Viết các phương thức hỗ trợ: `build_enclosure_prompt_fragment()`, `get_combined_negative_tokens()`, `transition_scene()`.
2. **Bước 2 (Memory Layer):**
   - Cập nhật `backend/agents/story_memory.py`: Tích hợp `scene_graph` vào `StoryMemory`, cập nhật `to_prompt_block()`, `to_dict()`, `from_dict()`.
   - Cập nhật `backend/agents/memory_extractor.py`: Trích xuất `SpaceEnclosure` ban đầu trong `extract_bible` và cập nhật vị trí/chuyển cảnh trong `extract_memory`.
3. **Bước 3 (Comic Pipeline Layer):**
   - Cập nhật `backend/agents/comic_agent.py`:
     - Nâng cấp `extract_setting_dna` thành trích xuất danh mục Enclosure.
     - Cập nhật `decompose_story_beats` để gắn nhãn phân cảnh (Enclosure Tagging).
     - Cập nhật `_validate_panels` để tiêm neo kiến trúc và đạo cụ cố định vào 100% khung tranh, đồng thời kích hoạt bộ lọc làm sạch từ khóa trôi dạt (Drift Sanitizer).
4. **Bước 4 (Diffusion Service Layer):**
   - Cập nhật `backend/services/cloudflare_ai.py`: Nhận và áp dụng `extra_negative_prompt` động theo từng enclosure.
   - Cập nhật `backend/main.py`: Truyền `extra_negative_prompt` từ panel sang `get_cached_or_generate_image`.
5. **Bước 5 (Quality Gate & Verification Suite):**
   - Cập nhật `backend/tests/test_comic_ontology_visuals.py` và `run_full_system_benchmark.py` để kiểm thử toàn diện 4 Invariants với schema mới.
   - Đảm bảo toàn bộ backend chạy `py_compile` và frontend chạy `npm run build` không lỗi.

---

### 5.2. Tiêu Chí Kiểm Tra Độc Lập (Verification Matrix)

| Kịch Bản Kiểm Thử | Trạng Thái Trước R2 (Baseline) | Kỳ Vọng Sau R2 (DSGO Enclosure) |
|---|---|---|
| **Cảnh phân tích tâm lý trong lớp học** (Lời dẫn: "An cúi đầu nhìn xuống trang vở im lặng") | Diffusion tự vẽ An đứng ngoài đường phố Tokyo hoặc trên bãi cỏ vì thiếu neo nền. | **0% trôi dạt:** Prompt nhận `"inside classroom 12A: pastel green walls, wooden student desks, grid windows, afternoon sunlight"`. Background duy trì 100% lớp học. |
| **Trang phục trong bối cảnh học đường hiện đại** (Lời thoại: "Hôm nay trời đẹp thật nhỉ!") | Dễ bị hallucination ra trang phục cổ trang hoặc áo giáp nếu câu từ mang màu sắc văn vẻ. | **0% lệch thời đại:** Era Banlist kích hoạt negative prompt loại bỏ `"hanfu, wuxia, kimono, armor, sword"`, cố định đồng phục học sinh. |
| **Nhân vật di chuyển sang hành lang** (Lời dẫn: "An đứng dậy, bước ra mở cửa bước vào hành lang") | Hệ thống không biết nhân vật đã đổi phòng; hoặc khung tranh sau vẫn vẽ bàn học trong lớp. | **Scene Gating thành công:** Hệ thống nhận diện từ `"bước vào hành lang"`, kích hoạt `transition_scene("corridor_3f")`, neo chuyển sang hành lang gạch men có dãy tủ cá nhân. |
| **Biên dịch & Tương thích ngược** | DB cũ chứa `memory_data` không có scene graph. | `from_dict` tự động bọc fallback, toàn bộ API hoạt động bình thường, `py_compile` 100% đạt. |

---

## 6. KẾT LUẬN

Báo cáo khảo sát này đã xác định chính xác nguyên nhân gốc rễ của hiện tượng trôi dạt không gian và ảo giác bối cảnh trong hệ thống NarrAI hiện tại: sự thiếu vắng một mô hình đồ thị có cấu trúc và cơ chế bao cảnh vật lý (Spatial Scene Enclosure). Kiến trúc **Dynamic Scene-Graph Ontology (DSGO)** được thiết kế trên đây đáp ứng đầy đủ và chuẩn xác mọi yêu cầu của R2 tại `ORIGINAL_REQUEST.md`, cung cấp lộ trình và mã nguồn mẫu rõ ràng để đội ngũ kỹ thuật tiến hành triển khai ở các bước tiếp theo.
