# BÁO CÁO KHẢO SÁT & ĐỀ XUẤT KỸ THUẬT: R1. TÁI CẤU TRÚC ĐỘNG CƠ VĂN PHONG TRUYỆN CHỮ (MODERN LIGHT NOVEL & WEB NOVEL ENGINE)

**Người thực hiện**: explorer_survey_r2_1 (Codebase Explorer Subagent)  
**Thời gian**: 2026-09-20  
**Thư mục làm việc**: `e:\NarrAI\.agents\explorer_survey_r2_1`  
**Căn cứ nhiệm vụ**: `e:\NarrAI\.agents\ORIGINAL_REQUEST.md` (Phiên làm việc ## 2026-09-20T13:19:05Z)

---

## 1. TỔNG QUAN VÀ MỤC TIÊU KHẢO SÁT

Hệ thống NarrAI hướng tới việc nâng cấp toàn diện chất lượng sáng tác văn xuôi, chuyển đổi từ văn phong miêu tả tĩnh, hàn lâm, cổ điển sang phong cách **Light Novel & Web Novel thịnh hành** dành cho thế hệ độc giả trẻ hiện đại:
- **Nhịp độ dồn dập (Fast-paced acceleration)**: Lược bỏ các đoạn chuyển cảnh rườm rà, nhảy cóc thẳng vào hành động và xung đột (In Medias Res).
- **Hệ thống độc thoại nội tâm đa tầng (Rich & Visceral Interior Monologue)**: Điểm nhìn chủ quan sâu sắc (POV 1 hoặc Tight POV 3), bộc lộ suy nghĩ trần trụi, phán đoán chiến thuật, phản ứng sinh lý và cảm xúc chân thật.
- **Đối thoại sắc bén, tự nhiên (Sharp Modern Dialogue & Subtext)**: Mang khẩu ngữ giới trẻ hiện đại, có cá tính riêng, giàu subtext (thao túng, đấu trí, mỉa mai, che giấu), triệt tiêu văn dịch Hán Việt sến súa.
- **Cấu trúc phân nhịp kịch tính (Dramatic Narrative Beats)**: 5 nhịp phát triển liên tục (Hook -> Complication -> Turning Point -> Climax -> Cliffhanger) cho mỗi chương/bản thảo, duy trì sức hút nghẹt thở.

---

## 2. BẢN ĐỒ KIẾN TRÚC MÃ NGUỒN HIỆN TẠI LIÊN QUAN ĐẾN R1

Qua khảo sát toàn diện backend NarrAI, các file mã nguồn trực tiếp quyết định và chi phối động cơ sinh truyện bao gồm:

| STT | File Path | Vai trò trong hệ thống | Dòng code trọng yếu |
| :--- | :--- | :--- | :--- |
| 1 | `backend/agents/story_generator.py` | **Động cơ sáng tác cốt lõi**: Định nghĩa quy tắc văn phong, trích xuất ontology, sinh truyện đơn kỳ (`generate_story_stream`) và sinh truyện nhiều chương (`generate_chapter_stream`). *(Lưu ý: mã nguồn thực tế là `story_generator.py`, không phải `story_agent.py`)* | Lines 5-38 (Rules), 45-77 (Ontology), 86-127 (_build_prompt), 139-179 (generate_chapter_stream), 180-210 (generate_ending_stream) |
| 2 | `backend/agents/copilot_agent.py` | **AI Co-pilot / Master Controller**: Trực tiếp can thiệp và sửa bản thảo (`edit_story_direct`), điều phối tác giả viết tiếp (`command_writer`). | Lines 133-168 (COPILOT_SYSTEM_PROMPT), 170-191 (DIRECT_EDIT_PROMPT), 226-298 (_perform_direct_manuscript_edit) |
| 3 | `backend/agents/editor_agent.py` | **Biên tập viên bôi đen**: Chỉnh sửa trực tiếp một đoạn văn được người dùng bôi đen trên giao diện Editor. | Lines 11-18 (system_prompt), 19-35 (edit_text) |
| 4 | `backend/agents/qa_refiner.py` | **Co-writer phỏng vấn & cô đọng cốt truyện**: Phỏng vấn tác giả và chuyển đổi thành Story Brief (Bản Phác Thảo Cốt Truyện). | Lines 14-27 (chat_interview), 43-62 (refine_prompt) |
| 5 | `backend/agents/story_memory.py` | **Hệ thống bộ nhớ truyện**: `StoryBible` (thực thể bất biến) và `StoryMemory` (trạng thái động, tóm tắt chương, mạch truyện chưa giải quyết). | Lines 8-36 (StoryBible), 39-95 (StoryMemory) |
| 6 | `backend/agents/memory_extractor.py` | **Trích xuất thông tin bộ nhớ**: Trích xuất StoryBible từ brief và trích xuất tiến trình bộ nhớ sau mỗi chương mới. | Lines 16-63 (extract_bible), 64-125 (extract_memory) |
| 7 | `backend/main.py` | **API Gateway & Session Orchestration**: Các endpoint `/api/generate-story`, `/api/init-story`, `/api/generate-chapter`, `/api/end-story`, `/api/copilot-event`. | Lines 258-299, 715-823, 824-894, 895-958, 959-1013 |
| 8 | `backend/data/trending_themes.json` | **Thư viện chủ đề xu hướng**: Chứa các prompt mẫu về chữa lành, trùng sinh, tổng tài, linh dị, hệ thống, học đường, công sở. | Lines 1-59 |
| 9 | `frontend/src/app/page.tsx` & `frontend/src/components/setup/Phase3Controls.tsx` | **Giao diện điều khiển**: Nơi người dùng tùy chỉnh độ dài (short/medium/long), sáng tạo (creativity 1-3), và nhịp độ (pacing 1-3). | `page.tsx`: Lines 314-366 (`handleStartWriting`); `Phase3Controls.tsx`: Lines 60-107 |

---

## 3. PHÂN TÍCH CHUYÊN SÂU: CÁC LỖ HỔNG VÀ HẠN CHẾ CỦA HỆ THỐNG HIỆN TẠI

### 3.1. Sai lệch về Persona và Định vị Vai trò trong System Prompt
- **Hiện trạng tại `story_generator.py` line 90**:
  ```python
  system_prompt = f"""Bạn là một đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế, chuyên sáng tác truyện bằng tiếng Việt hiện đại."""
  ```
- **Tại `story_generator.py` line 146**:
  ```python
  system_prompt = f"""Ban la tac gia dang truc tiep viet mot chuong tieu thuyet bang tieng Viet."""
  ```
- **Tại `copilot_agent.py` line 170**:
  ```python
  DIRECT_EDIT_PROMPT = """Bạn là Đại văn hào kiêm Biên tập viên hàng đầu."""
  ```
- **Hệ quả tiêu cực**:
  - Cách dùng từ xưng hô *"đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế"* và *"Đại văn hào"* kích hoạt thiên kiến phong cách văn học hàn lâm, cổ điển thế kỷ 19-20 (như Victor Hugo, Lev Tolstoy, Nam Cao).
  - Mô hình AI (GPT-oss-120b, Qwen) tự động chọn ngôi thứ ba toàn tri (Third-Person Omniscient) xa cách, tả cảnh ngụ tình lan man, giọng văn trầm mặc, thiếu sinh khí và sự gần gũi với giới trẻ.

### 3.2. Văn phong nặng về miêu tả tĩnh, thiếu vắng Độc thoại Nội tâm (Interior Monologue)
- **Hiện trạng**: Bộ quy tắc `MODERN_NOVEL_WRITING_RULES` (dòng 5-36 tại `story_generator.py`) tuy có yêu cầu *Show, don't tell*, nhưng hoàn toàn **thiếu hướng dẫn cụ thể về điểm nhìn (POV) và độc thoại nội tâm**.
- **Hệ quả tiêu cực**:
  - Nhân vật chính hành động như một "con rối" được camera quan sát từ xa, người đọc không thấy được dòng suy nghĩ trăn trở, phán đoán chiến thuật, nỗi sợ hay sự châm biếm ngầm.
  - Không có quy chuẩn định dạng cho độc thoại nội tâm (ví dụ: dùng định dạng suy nghĩ nghiêng `*(...)*` hoặc độc thoại tự vấn trực tiếp), dẫn đến việc AI hiếm khi sinh ra độc thoại nội tâm hoặc viết lộn xộn với lời dẫn chuyện.

### 3.3. Hội thoại còn cứng nhắc, mang âm hưởng dịch thuật cũ
- **Hiện trạng**: Quy tắc hiện tại chỉ nêu: *"Hội thoại đắt giá, có subtext (không nói chuyện vô thưởng vô phạt)"*.
- **Hệ quả tiêu cực**:
  - AI vẫn thường xuyên sinh ra các cấu trúc hội thoại sáo rỗng, lặp từ dẫn thoại (*"hắn nói...", "cô ta đáp..."*).
  - Dễ bị nhiễm văn dịch kiếm hiệp/ngôn tình Trung Quốc lỗi thời (*"ngươi", "hắn", "nàng", "chẳng hay", "nói đoạn"*) ngay cả trong bối cảnh thanh xuân vườn trường hay công sở Việt Nam hiện đại.

### 3.4. Hoàn toàn thiếu vắng Cấu Trúc Phân Nhịp Kịch Tính (Narrative Beats)
- **Hiện trạng**:
  - Tại `story_generator.py` lines 45-77: Hàm `_extract_narrative_ontology` chỉ trích xuất 4 mục: `[THỰC THỂ & NHÂN VẬT]`, `[QUAN HỆ & ĐỘNG CƠ]`, `[QUY TẮC THẾ GIỚI]`, `[CHUỖI NHÂN QUẢ CHÍNH]`. Không hề có **Narrative Beats**.
  - Khi sinh truyện ngắn (`short`) hoặc trung bình (`medium`): Mô hình AI được yêu cầu viết 3-4 chương hoặc 5-6 chương trong một prompt duy nhất mà **không có sườn nhịp kịch tính (Beat Sheet)** để bám theo.
  - Khi sinh từng chương (`long` - `generate_chapter_stream`): AI chỉ nhận lệnh mơ hồ: *"Chi viet DUY NHAT 1 chuong... GIAI QUYET it nhat 1 tuyen truyen dang mo va TAO RA it nhat 1 tuyen truyen moi. Ket thuc bang Cliffhanger manh me"*.
- **Hệ quả tiêu cực**:
  - Không có kiểm soát về nhịp độ trong chương: AI thường mở đầu chậm rãi, giữa chương bôi chữ, và cuối chương vội vã cắt ngang.
  - Cốt truyện dễ bị trôi dạt (narrative drift), thiếu các bước ngoặt cảm xúc dâng trào (emotional spikes) thu hút giới trẻ.

---

## 4. YÊU CẦU KỸ THUẬT & KIẾN TRÚC MỚI CHO R1

Để đạt chuẩn **Modern Light Novel & Web Novel Engine**, hệ thống cần tái cấu trúc theo 4 trụ cột kỹ thuật:

### 4.1. Cải tổ Bộ Quy Tắc Sáng Tác: `LIGHT_NOVEL_ENGINE_RULES`
Thay thế `MODERN_NOVEL_WRITING_RULES` bằng bộ quy tắc tiêu chuẩn hóa Light Novel / Web Novel:
1. **Persona Hiện Đại**: Nhà văn Web Novel / Light Novel hàng đầu, am hiểu thị hiếu giới trẻ, sở hữu văn phong sắc bén, dồn dập, giàu cảm xúc.
2. **Ngôi kể bám sát (Tight POV)**: Bắt buộc dùng Ngôi thứ nhất (POV 1 - "Tôi") hoặc Ngôi thứ ba giới hạn (Tight 3rd-Person Limited) bám sát tuyệt đối vào dòng cảm giác và nhận thức của nhân vật chính.
3. **Độc thoại nội tâm trực tiếp & sinh động**: Nhân vật chính liên tục tự vấn, phản ứng, phán đoán tình huống, cảm thán, hoặc bộc lộ tâm tư thầm kín. Quy chuẩn định dạng: suy nghĩ nội tâm được trình bày riêng biệt hoặc lồng ghép sắc nét trong văn bản.
4. **Đối thoại sắc bén & Khẩu ngữ hiện đại**: Nhịp đối đáp ngắn, đanh thép, mang cá tính rõ nét; loại bỏ 100% các từ xưng hô dịch thuật cổ lỗ sĩ trong bối cảnh hiện đại.
5. **Hook mở đầu bùng nổ (In Medias Res)**: Ném người đọc vào tâm điểm xung đột hoặc khoảnh khắc bất thường ngay trong 3 câu đầu tiên.
6. **Nhịp câu co giãn (Staccato Pacing)**: Cảnh kịch tính dùng câu ngắn (3-7 từ); đoạn văn phân tách thoáng đãng (2-4 câu/đoạn), không dùng khối chữ dày đặc gây mỏi mắt.

### 4.2. Thiết lập Cấu Trúc Ngũ Nhịp Kịch Tính (5 Dramatic Narrative Beats)
Mỗi chương truyện hoặc phân đoạn truyện chữ bắt buộc phải được quy hoạch và dẫn dắt theo cấu trúc 5 nhịp tuần hoàn:

```
[Beat 1: The Incisive Hook]       (0% - 15%)   --> Va chạm / Xung đột / Nguy cơ ngay lập tức
              ↓
[Beat 2: Rising Friction]         (15% - 40%)  --> Kế hoạch vấp trở ngại, gia tăng áp lực & ngờ vực
              ↓
[Beat 3: The Turning Point]       (40% - 70%)  --> Ngã rẽ sinh tử, quyết định mạo hiểm từ thế bị động sang chủ động
              ↓
[Beat 4: Visceral Climax]         (70% - 90%)  --> Bùng nổ đối đầu (lời thoại đanh thép / hành động nghẹt thở)
              ↓
[Beat 5: Lingering Cliffhanger]   (90% - 100%) --> Nút thắt treo nghẹt thở, mồi câu kích thích đọc chương kế tiếp
```

### 4.3. Nâng cấp Bộ nhớ Truyện (`StoryBible` & `StoryMemory`)
- Bổ sung trường `narrative_beats` vào `StoryBible` để lưu trữ sườn nhịp tổng thể của bộ truyện.
- Bổ sung `current_beat_index` và `beat_progression` vào `StoryMemory` để theo dõi tiến trình nhịp qua từng chương.

### 4.4. Đồng bộ hóa Copilot & Editor Agent
- Nâng cấp `DIRECT_EDIT_PROMPT` trong `copilot_agent.py` để khi Copilot chỉnh sửa văn bản (ví dụ: "viết lại mở đầu kịch tính hơn", "tăng kịch tính đoạn giữa"), văn bản tạo ra phải lập tức áp dụng quy chuẩn Light Novel (hook sắc bén, độc thoại nội tâm, đối thoại gãy gọn).
- Nâng cấp `EditorAgent.edit_text` để đảm bảo các đoạn văn bôi đen sửa nhanh duy trì đúng văn phong nhịp nhanh này.

---

## 5. ĐỀ XUẤT MÃ NGUỒN VÀ PROMPT CHI TIẾT (CONCRETE PROPOSED IMPLEMENTATIONS)

### 5.1. File `backend/agents/story_generator.py`

#### A. Thay thế Quy tắc Sáng tác (Lines 5-38) bằng `LIGHT_NOVEL_ENGINE_RULES`:
```python
# ==============================================================================
# MODERN LIGHT NOVEL & WEB NOVEL WRITING ENGINE RULES (VIETNAMESE EDITION)
# ==============================================================================
LIGHT_NOVEL_ENGINE_RULES = """QUY TẮC ĐỘNG CƠ SÁNG TÁC LIGHT NOVEL & WEB NOVEL THỊNH HÀNH:

1. ĐIỂM NHÌN BÁM SÁT (TIGHT POV) & KHỞI ĐẦU BÙNG NỔ (IN MEDIAS RES):
   - Sử dụng Ngôi thứ nhất ("Tôi") hoặc Ngôi thứ ba giới hạn (Tight 3rd-Person) bám chặt vào giác quan nhân vật chính.
   - HOOK ĐỘC GIẢ TRONG 3 CÂU ĐẦU: Ném nhân vật ngay vào hành động, biến cố bất thường hoặc một tình thế ngàn cân treo sợi tóc.
   - TUYỆT ĐỐI CẤM mở đầu bằng miêu tả thời tiết ("trời thu se lạnh", "nắng sớm le lói"), bình minh/hoàng hôn sáo rỗng hoặc thuyết minh lịch sử bối cảnh.

2. HỆ THỐNG ĐỘC THOẠI NỘI TÂM ĐA TẦNG (RICH INTERIOR MONOLOGUE):
   - Đan xen liên tục dòng suy nghĩ trần trụi của nhân vật chính: phán đoán chiến thuật, tự vấn cay đắng, suy luận logic hoặc những câu độc thoại mỉa mai (dry wit).
   - Thể hiện sự giằng xé tâm lý và áp lực sinh tồn/xã hội, tạo sự đồng cảm sâu sắc cho độc giả trẻ.

3. ĐỐI THOẠI SẮC BÉN, CÓ SUBTEXT & KHẨU NGỮ TỰ NHIÊN:
   - Đối thoại ngắn, đanh, tự nhiên như lời nói đời thực của giới trẻ Việt Nam hiện đại.
   - Mỗi câu thoại là một đòn thăm dò, thao túng, bảo vệ bí mật hoặc phản đòn tâm lý.
   - TUYỆT ĐỐI CẤM văn dịch Hán Việt sến súa, cổ lỗ ("ngươi/ta", "chẳng hay", "nói đoạn", "không khỏi hít vào một ngụm khí lạnh" - trừ khi bối cảnh thuần cổ trang).
   - Đan xen vi hành động (micro-actions): siết chặt ngón tay, khựng lại nửa nhịp, nuốt khan, nhếch khóe môi.

4. NHỊP ĐIỆU CÂU VĂN CO GIÃN & ĐOẠN VĂN THÔNG THOÁNG (FAST-PACED PACING):
   - Cắt gọt toàn bộ các đoạn chuyển cảnh thừa thãi (thức dậy, ăn sáng, đi lại không mục đích).
   - Cảnh căng thẳng/hành động: Câu ngắn (3-7 từ), ngắt nhịp dồn dập, tạo nhịp tim đập nhanh.
   - Trình bày đoạn văn ngắn gọn (2-4 câu/đoạn), xuống dòng dứt khoát, tối ưu cho trải nghiệm đọc lướt hiện đại.

5. CẤU TRÚC NGŨ NHỊP KỊCH TÍNH (5 DRAMATIC BEATS PER ARC/CHAPTER):
   - Nhịp 1 (0-15%): Kích ngòi xung đột & Hook tức thì.
   - Nhịp 2 (15-40%): Thắt nút, trở ngại phát sinh, gia tăng áp lực.
   - Nhịp 3 (40-70%): Ngã rẽ sinh tử, quyết định mạo hiểm đảo chiều thế cờ.
   - Nhịp 4 (70-90%): Bùng nổ va chạm đỉnh điểm (đấu trí / hành động cao trào).
   - Nhịp 5 (90-100%): Cliffhanger nghẹt thở, mở ra bí mật mới kích thích người đọc.

6. ANTI-CLICHÉ BANLIST (DANH MỤC CẤM KỴ):
   - CẤM TUYỆT ĐỐI: "vầng trăng vằng vặc", "thời gian thấm thoắt thoi đưa", "hắn cười khẩy / cười lạnh", "mắt phượng mày ngài", "trời quang mây tạnh lòng người u sầu", "bỗng nhiên một chuyện bất ngờ xảy ra".
   - CẤM lặp từ dẫn thoại đơn điệu ("hắn nói", "cô ấy nói"). Hãy để hành động và biểu cảm dẫn dắt câu thoại."""

WRITING_RULES = LIGHT_NOVEL_ENGINE_RULES
```

#### B. Nâng cấp `_extract_narrative_ontology` (Lines 45-77) để tích hợp Narrative Beats:
```python
    def _extract_narrative_ontology(self, refined_prompt: str) -> str:
        """
        Trích xuất Bộ khung Narrative Ontology & Chuỗi 5 Nhịp Kịch Tính (Dramatic Beats):
        - Thực thể & Nhân vật (Entities & Visual DNA)
        - Quan hệ & Động cơ xung đột ngầm (Conflict Matrix)
        - Quy tắc bối cảnh & Không gian neo giữ (World Axioms & Spatial Anchors)
        - Chuỗi 5 Nhịp Kịch Tính (5 Dramatic Narrative Beats)
        """
        prompt = f"""Phân tích bản phác thảo và trích xuất BỘ KHUNG NARRATIVE ONTOLOGY & NARRATIVE BEATS:
BẢN PHÁC THẢO:
{refined_prompt[:3000]}

Yêu cầu xuất ra cấu trúc chính xác sau:
[THỰC THỂ & NHÂN VẬT]: (Tên, điểm nhìn POV chính, ngoại hình nhận diện, mục tiêu ngầm, điểm yếu chí mạng)
[QUAN HỆ & ĐỘNG CƠ]: (Mối quan hệ cụ thể và điểm ngờ vực ngầm giữa các nhân vật)
[QUY TẮC THẾ GIỚI & KHÔNG GIAN BẤT BIẾN]: (Địa điểm cụ thể, thời đại, các quy tắc vật lý/xã hội không thể phá vỡ)
[CHUỖI 5 NHỊP KỊCH TÍNH (DRAMATIC NARRATIVE BEATS)]:
  + Nhịp 1 (Hook mở đầu): Biến cố hoặc xung đột kích ngòi ngay lập tức
  + Nhịp 2 (Thắt nút): Trở ngại phát sinh, áp lực dồn nén
  + Nhịp 3 (Ngã rẽ): Quyết định mạo hiểm của nhân vật chính
  + Nhịp 4 (Cao trào): Bùng nổ đối đầu hoặc sự thật chấn động
  + Nhịp 5 (Cliffhanger): Nút thắt treo nghẹt thở khép lại phần truyện
"""
```

#### C. Cải tiến `_build_prompt` (Lines 86-127):
```python
    def _build_prompt(self, refined_prompt: str, story_length: str):
        cfg = self._get_config(story_length)
        ontology_block = self._extract_narrative_ontology(refined_prompt)

        system_prompt = f"""Bạn là Cây Bút Vàng Web Novel & Light Novel Thịnh Hành, chuyên sáng tác các tác phẩm lôi cuốn, kịch tính dành cho giới trẻ bằng tiếng Việt hiện đại.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT, văn phong tự nhiên, giàu sắc thái đương đại, không lai tạp tiếng Anh.

=== BỘ KHUNG NARRATIVE ONTOLOGY & BEATS (BẤT BIẾN - TUYỆT ĐỐI TUÂN THỦ) ===
{ontology_block}
==========================================================================

{LIGHT_NOVEL_ENGINE_RULES}

NHIỆM VỤ: Dựa vào "Bộ khung Narrative Ontology" và "Chuỗi 5 Nhịp Kịch Tính", hãy viết câu chuyện hoàn chỉnh với nhịp độ dồn dập, giàu độc thoại nội tâm và đối thoại sắc bén. Triển khai đầy đủ qua các nhịp kịch tính.

ĐỘ DÀI: Khoảng {cfg['word_range']}. Phân bổ tình tiết theo đúng sườn nhịp kịch tính, đoạn văn ngắn gọn, thoáng đãng."""
```

#### D. Nâng cấp `generate_chapter_stream` (Lines 139-179):
```python
    def generate_chapter_stream(self, memory: StoryMemory, user_instruction: str = ""):
        """Viết 1 chương mới dựa trên Memory System & 5 Dramatic Narrative Beats (streaming)."""
        bible_block = memory.story_bible.to_prompt_block()
        memory_block = memory.to_prompt_block()
        short_context = memory.get_short_context(max_chars=6000)
        next_chapter = memory.current_chapter + 1

        system_prompt = f"""Bạn là tác giả Light Novel & Web Novel chuyên nghiệp đang trực tiếp chấp bút chương mới bằng tiếng Việt hiện đại.
NHIỆM VỤ CỦA BẠN LÀ VIẾT VĂN XUÔI CHƯƠNG TRUYỆN NGAY BÂY GIỜ, không phân tích, không giải thích, không hỏi lại người dùng.
TUYỆT ĐỐI KHÔNG viết lời chào, lời xin lỗi hay bất kỳ câu trò chuyện phi văn xuôi nào.
TUYỆT ĐỐI CHỈ VIẾT BẰNG TIẾNG VIỆT VĂN XUÔI NGUYÊN BẢN.

{bible_block}

{memory_block}

{LIGHT_NOVEL_ENGINE_RULES}

YÊU CẦU BẮT BUỘC CHO CHƯƠNG {next_chapter}:
- Viết DUY NHẤT 1 chương, độ dài 2000-3000 từ.
- Bắt đầu dòng 1 bằng tiêu đề Markdown: ## Chương {next_chapter}: [Tên chương gợi mở kịch tính]
- PHÂN BỔ ĐẦY ĐỦ 5 NHỊP KỊCH TÍNH TRONG CHƯƠNG:
  1. Mở đầu bằng Hook ngay lập tức (tiếp nối từ tình thế của chương trước).
  2. Phát sinh biến số hoặc áp lực mới, nội tâm dằn vặt/tính toán.
  3. Nhân vật đưa ra lựa chọn quyết liệt, đảo chiều hành động.
  4. Cao trào xung đột bùng nổ giữa các nhân vật.
  5. KẾT THÚC BẰNG MỘT CLIFFHANGER CỰC MẠNH (phát hiện mới, tiếng gõ cửa bất thường, đòn tấn công bất ngờ, hoặc câu thoại treo lơ lửng).
- Đoạn văn ngắn 2-4 câu, đối thoại có subtext, độc thoại nội tâm chân thực."""
```

---

### 5.2. File `backend/agents/copilot_agent.py`

#### Nâng cấp `DIRECT_EDIT_PROMPT` (Lines 170-191):
```python
DIRECT_EDIT_PROMPT = """Bạn là Trưởng ban Biên tập Light Novel & Web Novel đỉnh cao.
Tác giả muốn can thiệp trực tiếp vào bản thảo truyện chữ của họ.

YÊU CẦU CỦA TÁC GIẢ:
{user_instruction}

BẢN THẢO HIỆN TẠI:
{current_story}

HÃY THỰC HIỆN CHỈNH SỬA TRỰC TIẾP THEO CHUẨN LIGHT NOVEL & WEB NOVEL:
1. Áp dụng chính xác yêu cầu của tác giả (thay đổi mở đầu, sửa đoạn kết, thêm độc thoại nội tâm, làm sắc bén lời thoại...).
2. DUY TRÌ TIÊU CHUẨN VĂN PHONG LIGHT NOVEL HIỆN ĐẠI:
   - Nếu sửa mở đầu: Bắt buộc tạo Hook giật gân, ném nhân vật vào biến cố, loại bỏ hoàn toàn tả cảnh sáo rỗng.
   - Nếu sửa đối thoại: Làm câu thoại ngắn gọn, khẩu ngữ tự nhiên của giới trẻ, giàu subtext và vi hành động.
   - Nếu sửa diễn biến: Tăng cường độc thoại nội tâm, phán đoán tâm lý và nhịp độ dồn dập.
3. Ráp nối đoạn chỉnh sửa với phần còn lại của bản thảo một cách hoàn hảo, không để lại vết gãy ngữ nghĩa.
4. Xuất ra TOÀN BỘ bản thảo hoàn chỉnh sau khi đã chỉnh sửa.

ĐỊNH DẠNG ĐẦU RA (CHỈ JSON HỢP LỆ):
{{
  "updated_story_content": "Toàn văn bản thảo mới hoàn chỉnh sau khi chỉnh sửa",
  "summary_of_changes": "Tóm tắt ngắn gọn 1-2 câu về các chi tiết đã được thay đổi trong bản thảo",
  "message": "Lời nhắn gửi tác giả về sự thay đổi"
}}
"""
```

---

### 5.3. File `backend/agents/editor_agent.py`

#### Nâng cấp `edit_text` (Lines 11-18):
```python
        system_prompt = """Bạn là Biên tập viên Light Novel & Web Novel sắc sảo.
Nhiệm vụ của bạn là đọc "Đoạn văn gốc" (do người dùng bôi đen) và "Chỉ thị sửa đổi", sau đó viết lại đoạn văn đó theo văn phong Light Novel / Web Novel hiện đại:
QUY TẮC BẮT BUỘC:
1. Show, don't tell & Vi hành động: Thay tính từ chung chung bằng biểu hiện sinh lý thực tế, cử chỉ vô thức và tương tác vật lý sống động.
2. Giàu độc thoại nội tâm: Khắc họa rõ nét suy nghĩ thầm kín và cảm xúc chân thật của nhân vật.
3. Đối thoại tự nhiên, gãy gọn: Lời thoại sắc sảo, có subtext, mang khẩu ngữ đương đại.
4. TUYỆT ĐỐI KHÔNG dùng từ sáo rỗng ("vầng trăng vằng vặc", "cười khẩy", "thời gian thấm thoắt").
5. Giữ trọn vẹn ngữ cảnh xung quanh để đoạn văn ghép vào mạch truyện mượt mà.
6. CHỈ TRẢ VỀ ĐOẠN VĂN ĐÃ SỬA. KHÔNG giải thích, KHÔNG thêm lời chào, KHÔNG bọc ngoặc kép thừa."""
```

---

### 5.4. File `backend/agents/qa_refiner.py`

#### Nâng cấp `refine_prompt` (Lines 43-62) để định hình Cấu trúc Narrative Beats ngay từ khâu phác thảo:
```python
        system_prompt = """Bạn là chuyên gia biên soạn kịch bản Light Novel & Web Novel chuyên nghiệp.
TUYỆT ĐỐI CHỈ SỬ DỤNG TIẾNG VIỆT, không được pha trộn tiếng Anh.
Dựa trên toàn bộ lịch sử trò chuyện giữa người dùng và người hỏi đáp, hãy tổng hợp thành một "Bản Phác Thảo Cốt Truyện" mạch lạc, hiện đại, nhịp độ dồn dập.

Cấu trúc Bản Phác Thảo Cốt Truyện bắt buộc gồm:
1. TIÊU ĐỀ CHÍNH THỨC: Tiêu đề cuốn hút, chuẩn phong cách Light Novel / Web Novel.
2. THỂ LOẠI VÀ KHÔNG KHÍ: Liệt kê thể loại và nhịp điệu cảm xúc chủ đạo.
3. NHÂN VẬT & ĐIỂM NHÌN (POV): Tên gọi, điểm nhìn trần thuật (Ngôi 1 hoặc Tight Ngôi 3), tính cách, mục tiêu ngầm và điểm yếu chí mạng.
4. BỐI CẢNH & KHÔNG GIAN NEO GIỮ: Địa điểm cụ thể và thời đại diễn ra câu chuyện.
5. CẤU TRÚC 5 NHỊP KỊCH TÍNH (NARRATIVE BEATS):
   - Nhịp 1 (Hook mở đầu): Biến cố kích ngòi bất ngờ hoặc tình thế nguy cấp ngay dòng đầu.
   - Nhịp 2 (Thắt nút): Rắc rối nảy sinh, kế hoạch gặp trở ngại, áp lực dồn dập.
   - Nhịp 3 (Ngã rẽ): Nhân vật chính đưa ra lựa chọn liều lĩnh / bước ngoặt hành động.
   - Nhịp 4 (Cao trào): Xung đột bùng nổ đỉnh điểm (đối đầu trực tiếp / sự thật chấn động).
   - Nhịp 5 (Cliffhanger): Nút thắt treo nghẹt thở, mở ra bí ẩn tiếp diễn.

YÊU CẦU: Tôn trọng 100% các tình tiết tác giả đã chốt trong cuộc trò chuyện, không tự bịa thêm chi tiết phi lý."""
```

---

### 5.5. File `backend/agents/story_memory.py` & `memory_extractor.py`

#### A. Trong `story_memory.py`:
- Thêm trường `narrative_beats: list` vào `StoryBible`:
  ```python
  class StoryBible:
      def __init__(self, title="", genre="", characters=None, world_setting="",
                   main_plot="", writing_style="", refined_prompt="", narrative_beats=None, pov="tight_third"):
          ...
          self.narrative_beats = narrative_beats or []
          self.pov = pov
  ```
- Cập nhật `to_prompt_block()` để in ra chuỗi Narrative Beats khi tiếp nạp vào prompt sinh chương tiếp theo.
- Thêm trường `current_beat_index: int = 1` và `beat_milestones: list` vào `StoryMemory`.

#### B. Trong `memory_extractor.py`:
- Trong `extract_bible`: Prompt trích xuất thêm trường `"narrative_beats": ["Nhịp 1...", "Nhịp 2...", ...]` và `"pov": "first_person" | "tight_third"`.
- Trong `extract_memory`: Prompt phân tích chương vừa viết xem đã hoàn thành nhịp nào và gợi mở định hướng cho nhịp kế tiếp trong chương sau.

---

## 6. MỐI QUAN HỆ VÀ TÁC ĐỘNG HỖ TRỢ VỚI R2 VÀ R3

Việc thực thi chuẩn xác R1 tạo nền móng vững chắc cho toàn bộ hệ thống NarrAI:
1. **Hỗ trợ trực tiếp cho R2 (Dynamic Scene-Graph Ontology & Spatial Scene Enclosure)**:
   - Nhờ quy tắc vi hành động (micro-actions) và định cảnh cụ thể (visceral spatial anchor) của R1, câu chuyện luôn nêu rõ bối cảnh cụ thể mà nhân vật đang đứng (ví dụ: *"Tại phòng học 12A lúc hoàng hôn..."* hoặc *"Dưới bóng cây bàng sân trường..."*).
   - Dynamic Scene-Graph Ontology sẽ dễ dàng trích xuất chính xác không gian 3 chiều (Thực thể - Không gian - Thời đại), ngăn chặn triệt để tình trạng trôi dạt địa lý (spatial drift).
2. **Hỗ trợ trực tiếp cho R3 (Đồng Bộ Hóa Text-to-Image & Triệt tiêu Ảo giác Khung tranh)**:
   - Các khung thoại và hành động trong truyện chữ của R1 gãy gọn, có chủ ngữ và cử chỉ rõ ràng, giúp `BEAT_DIRECTOR_PROMPT` trong `comic_agent.py` dễ dàng phân rã thành các panel manga tuần tự (sequential panels) với lời thoại trọn vẹn, không cụt lửng, và hình ảnh bám sát 100% bối cảnh gốc.

---

## 7. BẢNG TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA MATRIX) CHO R1

| Hạng mục kiểm tra | Hiện trạng trước nâng cấp | Trạng thái sau nâng cấp đề xuất | Phương thức kiểm chứng |
| :--- | :--- | :--- | :--- |
| **Persona & Giọng văn** | "Đại tiểu thuyết gia quốc tế", văn học hàn lâm, cổ điển, trầm mặc | "Bút vàng Light Novel / Web Novel", trẻ trung, hiện đại, dồn dập | Kiểm tra `story_generator.py` line 90 & văn bản sinh ra |
| **Hook mở đầu** | Mở bài chậm rãi, tả mây trời, thời tiết, giới thiệu chung chung | Bắt đầu thẳng bằng In Medias Res trong 3 câu đầu (xung đột, tình huống khẩn) | Test prompt với các chủ đề trong `trending_themes.json` |
| **Độc thoại nội tâm** | Hiếm hoi, nhân vật hành động như con rối quan sát từ xa | Đan xen liên tục dòng suy nghĩ trần trụi, tính toán, tự vấn sâu sắc | Đếm mật độ xuất hiện suy nghĩ nội tâm trong các phân cảnh |
| **Chất lượng đối thoại** | Dễ vướng sáo ngữ Hán Việt dịch thuật ("ngươi", "hắn", "nói đoạn") | Khẩu ngữ tiếng Việt hiện đại, sắc bén, có subtext và cá tính riêng | Rà soát anti-cliché banlist trong output |
| **Cấu trúc nhịp kịch tính** | Không có sườn nhịp; chia chương tự do không định hướng | 5 Dramatic Beats rõ ràng: Hook -> Complication -> Turning Point -> Climax -> Cliffhanger | Kiểm tra sự phát triển tình tiết từng chương |
| **Khả năng can thiệp của Copilot** | Sửa bản thảo bằng prompt chung chung, dễ kéo ngược về văn tả tĩnh | Tự động áp dụng chuẩn Light Novel khi can thiệp trực tiếp vào bản thảo | Ra lệnh Co-pilot: "sửa lại mở đầu kịch tính hơn" |
| **Biên dịch & Tương thích** | Đảm bảo 100% | Toàn bộ backend (`py_compile`) và frontend (`build`) 0 lỗi | Kiểm tra cú pháp và tích hợp API |

---

## 8. KẾT LUẬN & ĐỀ XUẤT BƯỚC TIẾP THEO

Báo cáo khảo sát này đã xác định chính xác toàn bộ các mắt xích mã nguồn, định vị nguyên nhân gốc rễ của văn phong miêu tả tĩnh, và xây dựng bản thiết kế hoàn chỉnh cho **Động Cơ Văn Phong Light Novel & Web Novel** cùng **Cấu Trúc Ngũ Nhịp Kịch Tính (5 Dramatic Beats)**. 

Bản thiết kế này đã sẵn sàng để đội ngũ triển khai (Implementer) áp dụng trực tiếp vào `backend/agents/story_generator.py`, `copilot_agent.py`, `editor_agent.py`, `qa_refiner.py`, và `story_memory.py`.
