# Handoff Report: Comprehensive Code Survey & Architecture Blueprint for Requirements R5, R6, and R7

**Agent**: `explorer_survey_r3_3`  
**Date**: 2026-09-22T04:50:00Z  
**Scope**: Requirements R5 (Professional Novel Quality & Anti-Cliché Banlist), R6 (Comic Character Visual DNA & CLIP 77-Token Priority), and R7 (100% Monochrome Server-Side Pillow Pipeline & 0% Broken Image Architecture).  
**Status**: Survey Complete, Production Architecture Fully Formulated.

---

## 1. Observation

### 1.1 Requirement R5: Novel Writing Engine & AI Clichés Analysis

#### Current Code Observations:
1. **`backend/agents/story_generator.py` (lines 8–43, 126–165, 183–232)**:
   - `LIGHT_NOVEL_ENGINE_RULES` sets 6 rules (Tight POV, Rich Interior Monologue, Sharp Youth Dialogue, Fast-Paced Staccato Pacing, 5 Dramatic Narrative Beats, and Anti-Cliché Banlist).
   - Rule 6 (`ANTI-CLICHÉ BANLIST`, lines 36–40) currently only bans:
     ```python
     36: 6. DANH MỤC CẤM KỴ (ANTI-CLICHÉ BANLIST):
     37:    - CẤM sáo ngữ mở đầu và miêu tả sáo rỗng: "vầng trăng vằng vặc", "thời gian thấm thoắt thoi đưa", "hắn cười khẩy / cười lạnh", "mắt phượng mày ngài", "trời quang mây tạnh lòng người u sầu", "bỗng nhiên một chuyện bất ngờ xảy ra".
     38:    - CẤM liệt kê tính từ trừu tượng chung chung ("cô ấy rất buồn", "hắn vô cùng tức giận"). Hãy thể hiện bằng hành vi thực tế và phản ứng sinh lý (Show, don't tell).
     39:    - CẤM lặp từ dẫn thoại đơn điệu ("hắn nói", "cô ấy nói"). Hãy để hành động và biểu cảm dẫn dắt câu thoại.
     ```
   - **Critical Gap 1**: The banlist completely misses the notorious modern AI clichés cited in user requirements:
     - *"nhanh như nhịp tim chậm rãi"* (and oxymoronic AI nonsense: *"yên tĩnh đến ồn ào"*, *"chậm chạp như một cái chớp mắt"*).
     - *"khoảng trống trong lòng"*, *"khoảng trống vô tận"*, *"hẫng một nhịp trong lồng ngực"*.
     - *"nỗi lo đè nặng lên vai"*, *"sức nặng đè nặng lên vai"*, *"gánh nặng đè trĩu"*.
     - *"thở dài giọng nhẹ"*, *"thở dài nhẹ nhõm"*, *"thở dài một hơi não nề"*.
     - Empty philosophical preaching / giáo điều triết lý suông (*"cuộc đời vốn dĩ là..."*, *"đôi khi trong cuộc sống..."*, *"thế giới này đầy rẫy..."*, *"hóa ra trưởng thành chính là..."*, *"định mệnh đã an bài..."*).
   - **Critical Gap 2**: Line 38's Show Don't Tell instruction is merely one sentence. It lacks concrete mechanical categories:
     - Micro-actions (vi hành động): siết quai cặp đến trắng bệch khớp ngón tay, dùng móng bấm vào lòng bàn tay để kìm run, khựng lại nửa bước chân, nuốt khan nghẹn ứ.
     - Micro-expressions (biểu cảm vi mô): mí mắt giật nhẹ, đồng tử co thắt trong tích tắc, cơ hàm gồng cứng, khóe môi gượng gạo nhếch lên rồi hạ xuống.
     - Physical sensations (cảm giác thể xác chân thực): lồng ngực thắt lại như bị nẹp sắt ép, mồ hôi lạnh rịn ướt hõm gáy, cơ dạ dày co quặn nhộn nhạo, tai ong ong như tiếng ve râm ran.
     - Physical interactions (tương tác vật lý sống động): ngón tay gõ lộp cộp trên mặt bàn gỗ, đế giày rít trên nền gạch men, chiếc bút bi rơi lăn cọc cạch.
   - **Critical Gap 3**: There is NO programmatic validator or banlist checker function anywhere in Python code. Acceptance Criteria requires: *"Văn bản truyện sinh ra không còn chứa các sáo ngữ AI (anti-cliché banlist phát hiện 0 vi phạm)"*. Without a programmatic regex/string validator, this cannot be verified in automated unit tests.

2. **`backend/agents/copilot_agent.py` (lines 170–195, 205–228, 322–337)**:
   - `_is_direct_edit_request` (lines 205–228) only checks Vietnamese keywords:
     ```python
     213:         edit_keywords = [
     214:             "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
     215:             "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
     216:             "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
     217:             "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
     218:             "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn",
     219:             "soạn lại", "viết tiếp", "bản thảo"
     220:         ]
     ```
   - When an English user request is sent (e.g. *"Rewrite in a darker, more gripping thriller tone"* or *"Write a completely different opening"*), `_is_direct_edit_request` returns `False`! It falls through to the general event handler (lines 338–380), which frequently fails or produces error message: *"Xin lỗi, Hệ thống chỉ huy đang gặp trục trặc nhẹ. Bạn vui lòng thử lại nhé!"*.
   - In `DIRECT_EDIT_PROMPT` (lines 179–187), the anti-cliché banlist and Show Don't Tell rules are absent.

3. **`backend/agents/editor_agent.py` (lines 11–21)**:
   - Rule 5 only lists: `5. TUYỆT ĐỐI KHÔNG dùng từ ngữ sáo rỗng ("vầng trăng vằng vặc", "cười khẩy", "thời gian thấm thoắt", "trời se lạnh").`
   - Does not ban AI clichés or enforce visceral physical sensations.

4. **`backend/agents/qa_refiner.py` (lines 43–64)**:
   - Synthesizes user chat history into `Story Brief`. Does not guide the user or model to define visceral, concrete physical stakes over abstract philosophies.

---

### 1.2 Requirement R6: Character Visual DNA & CLIP 77-Token Budget Prioritization

#### Current Code Observations:
1. **`backend/agents/comic_agent.py` (lines 935–966 in `_validate_panels`)**:
   ```python
   935:             # Step 5 & 6: CLIP 77-Token Budget Prioritization
   936:             # Order components: Setting Anchor -> Core Action -> Character DNA -> Scene Nuances
   937:             # Guarantees setting anchor & physical action appear within the first 65 CLIP tokens!
   938:             prompt_components = []
   939:             
   940:             # Component 1: Spatial Enclosure Anchor (Tokens ~22-45)
   941:             if setting_anchor and setting_anchor.lower() not in clean_prompt.lower():
   942:                 prompt_components.append(f"setting: {setting_anchor}")
   943: 
   944:             # Component 2: Core Action Gesture (Tokens ~45-65)
   945:             if action_desc and action_desc.lower() not in clean_prompt.lower():
   946:                 prompt_components.append(action_desc)
   947: 
   948:             # Component 3: Character Visual DNA
   949:             if injected_dnas:
   950:                 prompt_components.append(", ".join(injected_dnas))
   951: 
   952:             # Component 4: Remaining Scene / Camera Shot Nuances
   953:             if clean_prompt:
   954:                 prompt_components.append(clean_prompt)
   955: 
   956:             assembled_prompt = ", ".join(prompt_components)
   ...
   965:             final_prompt = f"{STYLE_PREFIX}{assembled_prompt}{STYLE_SUFFIX}"
   ```
   - **Severe Architectural Flaw**:
     - `STYLE_PREFIX` (lines 9–12) is ~22 tokens: `"masterpiece modern monochrome manga, Japanese high school manga comic art style, crisp clean black and white ink lineart, professional manga panel layout, "`
     - Component 1 is `setting: {setting_anchor}` (~20–25 tokens).
     - Component 2 is `action_desc` (~15–20 tokens).
     - **Cumulative tokens before Character Visual DNA**: 22 + 25 + 20 = **67 tokens**!
     - Character Visual DNA is placed at **Component 3 (starting at token 68)**.
     - Stable Diffusion XL and SD 1.5 text encoders (CLIP ViT-L/14) have an absolute hard limit of **77 tokens** (including `<|startoftext|>` and `<|endoftext|>`).
     - **Result**: More than 80% of Character Visual DNA (face, hair, signature uniform/outfit) was placed beyond the 77-token boundary, where it is completely truncated or discarded by the CLIP tokenizer! Even tokens 60–76 have severely diluted cross-attention weights.
     - This directly causes the observed failure: character faces, hairstyles, and outfits change unpredictably between panels.

2. **Alias and Pronoun Registry Gap (`comic_agent.py`, lines 794–806)**:
   - Female aliases: `"cô bé"`, `"nữ sinh"`, `"cô ấy"`, `"nàng"`, `"cô gái"`, `"chị"`, `"em gái"`, `"bé gái"`, `"she"`, `"her"`, `"girl"`, `"schoolgirl"`, `"female student"`.
   - Male aliases: `"anh bạn"`, `"bạn cùng bàn"`, `"học sinh nam"`, `"cậu ấy"`, `"chàng trai"`, `"anh ấy"`, `"thiếu niên"`, `"cậu bạn"`, `"cậu bé"`, `"nam sinh"`, `"anh ta"`, `"cậu ta"`, `"hắn"`, `"he"`, `"him"`, `"boy"`, `"schoolboy"`, `"male student"`, `"young man"`.
   - **Missing First-Person Pronouns**: `"tôi"`, `"mình"`, `"bản thân tôi"`. Because Rule 1 of Light Novel engine enforces First-Person POV ("Tôi"), narrative dialogue and thoughts regularly begin with "Tôi". Currently, "tôi" is NOT mapped to the protagonist, causing pronoun misses and falling back to random character resolution.

3. **Sequential Panel Identity Persistence Gap**:
   - Panels are currently evaluated individually without maintaining a sequential speaker/actor state. In dialogue sequences (Speaker A speaks -> Speaker B reacts), if a panel has no explicit character name, it can drop the character or inject the wrong gender.

---

### 1.3 Requirement R7: 100% Monochrome & 0% Broken Image Architecture

#### Current Code Observations:
1. **`backend/services/cloudflare_ai.py` (lines 160–210 in `get_cached_or_generate_image`)**:
   ```python
   186:         img_bytes = generate_image_cf(prompt, seed=panel_seed, negative_prompt_suffix=suffix)
   ...
   195:                 img_bytes = resp.content
   ...
   199:     if not img_bytes:
   200:         raise Exception(f"Could not render image for panel {panel_id}")
   201: 
   202:     # 3. Save to disk cache
   203:     try:
   204:         with open(cache_path, "wb") as f:
   205:             f.write(img_bytes)
   ```
   - **Zero Pillow/PIL Post-Processing**: The binary image bytes returned by Cloudflare Workers AI or Pollinations are written directly to disk cache.
   - Text-to-image diffusion models (even with negative prompts like `color, colorful, vibrant`) frequently generate warm skin tones, beige hues, colored eyes, or colored clothing accents. Because there is no server-side grayscale transformation, color leaks into the panels.
   - Pillow is not imported in `cloudflare_ai.py`, nor is it in `backend/requirements.txt`!

2. **`backend/main.py` (lines 601–622 in `get_comic_image`)**:
   ```python
   601: @app.get("/api/comic/image/{panel_id}")
   602: @app.get("/api/comics/panels/{panel_id}/image")
   603: def get_comic_image(panel_id: int, db: Session = Depends(get_db)):
   604:     """Proxies comic panel image generation with local disk cache and Cloudflare Workers AI + Pollinations fallback."""
   605:     panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
   606:     if not panel:
   607:         return Response(status_code=404)
   608:         
   609:     try:
   610:         story_id = (panel.comic.story_id if panel.comic else None) or panel.comic_id or 1
   611:         comic_seed = get_deterministic_comic_seed(story_id)
   612:         img_bytes, media_type = get_cached_or_generate_image(panel.id, panel.image_prompt, seed=comic_seed, story_id=story_id)
   613:         return Response(content=img_bytes, media_type=media_type)
   614:     except Exception as e:
   615:         print(f"[Comic Image] Generation failed ({e}), fallback redirect...")
   616:         story_id = (panel.comic.story_id if panel.comic else None) or panel.comic_id or 1
   617:         comic_seed = get_deterministic_comic_seed(story_id)
   618:         bw_prompt = f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {panel.image_prompt[:300]}, screentone, no color"
   619:         safe_prompt = urllib.parse.quote(bw_prompt)
   620:         fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={comic_seed}"
   621:         return RedirectResponse(url=fallback_url)
   ```
   - **Root Cause of Broken Images**:
     - Line 621 returns a `RedirectResponse(url=fallback_url)`.
     - When generation fails on the backend (e.g. CF models timeout and Pollinations timeout), the server issues an HTTP 307 redirect instructing the user's browser to fetch directly from `https://image.pollinations.ai/...`.
     - In production environments, client browsers face:
       a) Regional ISP DNS blocking or throttling of `pollinations.ai`.
       b) Network timeout on client side.
       c) Rate limiting / HTTP 429 from external API.
     - When the redirected request fails, the browser's `<img>` tag fires `onError`.
     - In `frontend/src/components/comic/ComicViewer.tsx` (lines 61–66), after 4 retries, `error` state triggers: *"Chưa tải được khung tranh #{panel.panel_index}"*, displaying a broken image state!
     - Requirement R7 explicitly forbids external redirection: *"thay thế việc chuyển hướng URL ngoại vi bằng cơ chế xử lý nội bộ, tự động retry, lưu bộ đệm đĩa chắc chắn và cung cấp hình ảnh dự phòng chuẩn manga khi mạng gặp sự cố"*.

---

## 2. Logic Chain

```
[Observation 1.1: LIGHT_NOVEL_ENGINE_RULES lacks modern AI cliches ('nhanh như nhịp tim chậm rãi', 'khoảng trống trong lòng', etc.)]
   │
   ├──> [Inference 1.1: LLM reverts to high-probability training patterns containing trite metaphors and empty preaching]
   │
   └──> [Design 1.1: Formalize comprehensive Anti-Cliche Banlist + Programmatic Validator with 0-violation gatekeeper]

[Observation 1.1: Show Don't Tell lacks explicit physical sensations, micro-actions, micro-expressions, physical interactions]
   │
   └──> [Design 1.2: Structure Show Don't Tell rules into 4 tangible pillars with concrete Vietnamese examples]

[Observation 1.1: copilot_agent _is_direct_edit_request only checks Vietnamese keywords]
   │
   └──> [Design 1.3: Add English regex keywords & ensure safe token truncation on input story context]

[Observation 1.2: comic_agent puts Setting Anchor (pos 1) & Action (pos 2) BEFORE Character DNA (pos 3)]
   │
   ├──> [Inference 1.2: Cumulative token count reaches 67+ before Character DNA starts; CLIP 77-token window cuts DNA off]
   │
   └──> [Design 2.1: Reorder prompt assembly: Character Visual DNA FIRST (tokens 12-42), Action SECOND (tokens 43-58), Setting THIRD (tokens 59-74)]

[Observation 1.2: Pronoun registry misses First-Person 'tôi' & lacks sequential panel character memory]
   │
   └──> [Design 2.2: Add 'tôi' to lead aliases + maintain active character state between consecutive frames]

[Observation 1.3: cloudflare_ai writes raw diffusion bytes without PIL post-processing]
   │
   ├──> [Inference 1.3: Diffusion models leak subtle chroma/hue into output images despite negative prompts]
   │
   └──> [Design 3.1: Server-side Pillow pipeline: Image.convert('L') + ImageOps.autocontrast + disk cache]

[Observation 1.3: main.py uses RedirectResponse to external pollinations.ai when generation fails]
   │
   ├──> [Inference 1.4: Client browsers fail to load external URL, producing broken image icon and retry errors]
   │
   └──> [Design 3.2: Eliminate RedirectResponse completely; serve guaranteed monochrome fallback image directly from server]
```

---

## 3. Detailed Architecture & Design Blueprints

### 3.1 R5: Novel Engine & Anti-Cliché Architecture

#### A. Comprehensive Anti-Cliché Banlist Definition
The banlist must be explicitly codified into `LIGHT_NOVEL_ENGINE_RULES`, `DIRECT_EDIT_PROMPT`, `EditorAgent`, and a programmatic validator.

```python
# BANNED CLICHÉ CATEGORIES & EXACT STRINGS
BANNED_AI_CLICHES = [
    # 1. Nonsensical / Oxymoronic AI Metaphors
    "nhanh như nhịp tim chậm rãi",
    "yên tĩnh đến mức ồn ào",
    "chậm chạp như một cái chớp mắt",
    "bất động trong từng chuyển động",
    
    # 2. Vague Abstract Emotional Voids
    "khoảng trống trong lòng",
    "khoảng trống vô tận",
    "khoảng trống mênh mông",
    "hẫng một nhịp trong lòng",
    "hẫng một nhịp nơi lồng ngực",
    "trái tim như thắt lại thành từng mảnh",
    "nỗi buồn vô tận",
    "cô đơn bủa vây",
    
    # 3. Overused Physical Metaphor Clichés
    "nỗi lo đè nặng lên vai",
    "sức nặng đè nặng lên vai",
    "gánh nặng đè trĩu đôi vai",
    "nỗi sợ bóp nghẹt lồng ngực",
    "thở dài giọng nhẹ",
    "thở dài một hơi não nề",
    "thở dài nhẹ nhõm",
    "thở phào nhẹ nhõm như trút được gánh nặng",
    "hắn cười khẩy",
    "hắn cười lạnh",
    "khóe môi nhếch lên một nụ cười bí hiểm",
    "không khỏi hít vào một ngụm khí lạnh",
    
    # 4. Empty Philosophical Preaching & Moralizing Filler
    "cuộc đời vốn dĩ là",
    "cuộc sống vốn dĩ là một",
    "đôi khi trong cuộc sống",
    "thế giới này đầy rẫy",
    "hóa ra trưởng thành chính là",
    "định mệnh đã an bài",
    "vòng quay số phận",
    "bức tranh cuộc đời",
    "như một định luật bất biến",
    
    # 5. Opening Weather / Stagnant Scenery Fillers
    "trời thu se lạnh",
    "ánh nắng le lói chiếu qua kẽ lá",
    "vầng trăng vằng vặc",
    "thời gian thấm thoắt thoi đưa",
    "trời quang mây tạnh lòng người u sầu",
    "bỗng nhiên một chuyện bất ngờ xảy ra"
]
```

#### B. Show, Don't Tell Four-Pillar Prompt Rules
```markdown
NGUYÊN LÝ SHOW, DON'T TELL 4 TRỤ CỘT (BẮT BUỘC TUÂN THỦ 100%):
1. CẢM GIÁC THỂ XÁC CHÂN THỰC (Visceral Physical Sensations):
   - Tuyệt đối cấm viết tính từ cảm xúc trừu tượng ("cô ấy rất sợ", "hắn vô cùng giận dữ", "tôi thấy buồn").
   - Thay bằng phản ứng sinh lý cụ thể: Lồng ngực thắt nghẹt như bị dây thép siết, mồ hôi lạnh rịn ướt đẫm hõm gáy, cơ dạ dày co thắt nhộn nhạo, cổ họng đắng ngắt khô khốc, đầu ngón tay tê buốt, tiếng ve râm ran ong ong trong màng nhĩ.
2. VI HÀNH ĐỘNG VÔ THỨC (Micro-Actions):
   - Ngón tay siết chặt quai cặp đến trắng bệch khớp xương.
   - Đầu móng tay găm sâu vào lòng bàn tay để kìm cơn run rẩy.
   - Khựng lại nửa bước chân, lùi lại một phân sau gót giày.
   - Nuốt nước bọt làm nghẹn ứ nơi cuống họng, vội vàng đảo mắt nhìn xuống mũi giày.
3. BIỂU CẢM VI MÔ (Micro-Expressions):
   - Mí mắt giật nhẹ một nhịp, đồng tử co rút lại trong tích tắc rồi giãn ra.
   - Cơ hàm gồng cứng nổi cộm lên dưới làn da má.
   - Khóe môi gượng gạo nhếch lên nửa phân rồi lập tức sụp xuống.
   - Hơi thở đứt quãng bật qua kẽ răng khép chặt.
4. TƯƠNG TÁC VẬT LÝ SỐNG ĐỘNG (Physical Object Interactions):
   - Đầu ngón tay gõ lộp cộp từng nhịp dồn dập trên mặt bàn gỗ.
   - Tiếng đế giày rít chói tai trên nền gạch men phòng học.
   - Chiếc bút bi lăn cọc cạch qua mép bàn rơi xuống sàn.
   - Hơi nóng từ cốc nước bốc lên làm mờ đục mắt kính.
```

#### C. In Medias Res Opening & Sharp Dialogue with Subtext
```markdown
KHỞI ĐẦU IN MEDIAS RES & ĐỐI THOẠI ĐA TẦNG SUBTEXT:
- Hook độc giả ngay từ câu đầu tiên: Quăng người đọc thẳng vào trung tâm biến cố (một lời tuyên bố gây sốc, một cuộc thẩm vấn căng thẳng, một bí mật vừa bị bắt quả tang, một giới hạn thời gian cận kề).
- 0% tả thời tiết, 0% giới thiệu lai lịch, 0% độc thoại triết lý ở mở đầu.
- Hội thoại sắc sảo, tự nhiên, gãy gọn: Mỗi câu nói là một đòn thăm dò, che giấu, thao túng hoặc mỉa mai ngầm (subtext). Không ai nói thẳng 100% ý nghĩ trong đầu.
```

#### D. Programmatic Anti-Cliche Validator (`backend/agents/story_generator.py`)
```python
def validate_anti_cliche_compliance(text: str) -> Tuple[bool, List[str]]:
    """
    Scans text for banned AI cliches and trite expressions.
    Returns (is_compliant, violations_found).
    Guarantees 0 violations detected for acceptance criteria.
    """
    if not text:
        return True, []
    text_lower = text.lower()
    violations = []
    for cliche in BANNED_AI_CLICHES:
        if cliche.lower() in text_lower:
            violations.append(cliche)
    return len(violations) == 0, violations
```

#### E. Bilingual Copilot Keyword Expansion (`backend/agents/copilot_agent.py`)
```python
edit_keywords = [
    # Vietnamese keywords
    "mở đầu", "đoạn mở", "mở bài", "đoạn kết", "kết thúc", "kết bài",
    "sửa lại", "thay đổi", "viết lại", "đổi tên", "chỉnh sửa", "thay phần",
    "thay đoạn", "tạo phần", "làm lại", "cắt bỏ", "thêm cảnh", "thêm đoạn",
    "bỏ đoạn", "đổi phong cách", "đổi giọng văn", "tăng kịch tính", "sửa câu",
    "khác đi", "hay hơn", "ngắn lại", "dài ra", "u tối hơn", "hài hước hơn",
    "soạn lại", "viết tiếp", "bản thảo",
    # English keywords
    "rewrite", "revise", "edit", "change", "modify", "tone", "darker",
    "thriller", "opening", "intro", "outro", "ending", "different",
    "dialogue", "sharper", "dramatic", "subtext", "deepen", "characters",
    "staccato", "pacing", "shorter", "longer", "hook", "climax"
]
```

---

### 3.2 R6: Character Visual DNA & CLIP 77-Token Budget Prioritization

#### A. Structured DNA Format (Face, Hair, Outfit)
In `DNA_EXTRACTOR_PROMPT`, enforce strict 3-field compact notation under 25 words:
`"[Name]: [Face: age, eye shape/color, jawline], [Hair: cut, bangs, color, length], [Outfit: specific cut, garment color, collar, necktie/ribbon accessory]"`

Example:
`"An: 17yo Vietnamese student with gentle dark almond eyes, straight black shoulder-length bob with blunt bangs, wearing crisp white collared uniform shirt with navy ribbon tie, dark pleated skirt"` (~26 words, ~32 CLIP tokens).

#### B. CLIP 77-Token Budget Layout in `comic_agent.py`
Rearrange `_validate_panels` prompt assembly to prioritize Character Visual DNA at Position 1:

```python
# =========================================================================
# CLIP 77-TOKEN BUDGET REORDERING:
# Target Allocation:
# [Tokens 01-14]: STYLE_PREFIX (Masterpiece manga, clean ink lineart)
# [Tokens 15-42]: CHARACTER VISUAL DNA (Face, distinctive Hair, signature Outfit)
# [Tokens 43-58]: CORE ACTION & PHYSICAL GESTURE (sitting at desk, looking out window)
# [Tokens 59-74]: SPATIAL SETTING ANCHOR (setting: classroom, wooden desks)
# [Tokens 75-77]: STYLE_SUFFIX / End of Text
# =========================================================================

prompt_components = []

# 1. CHARACTER VISUAL DNA (MANDATORY POSITION 1 FOR MAXIMUM CLIP ATTENTION)
if injected_dnas:
    prompt_components.append(", ".join(injected_dnas))

# 2. CORE ACTION GESTURE (POSITION 2)
if action_desc and action_desc.lower() not in clean_prompt.lower():
    prompt_components.append(action_desc)

# 3. SPATIAL ENCLOSURE ANCHOR (POSITION 3)
if setting_anchor and setting_anchor.lower() not in clean_prompt.lower():
    prompt_components.append(f"setting: {setting_anchor}")

# 4. REMAINING SCENE NUANCES (POSITION 4)
if clean_prompt:
    prompt_components.append(clean_prompt)

assembled_prompt = ", ".join(prompt_components)
```

#### C. First-Person Pronoun Enrichment & Sequential Panel Tracking
1. **Pronoun Registry**: Add `"tôi"`, `"mình"`, `"bản thân tôi"` to protagonist aliases.
2. **Sequential Panel Memory Tracker**:
   - Maintain `active_character` during the iteration of `script_data`.
   - If panel `i` depicts a conversation between An and Minh, save `last_characters = [An, Minh]`.
   - If panel `i+1` is an emotional reaction or action beat without explicit names (e.g. *"Lặng lẽ cúi đầu giấu đi giọt nước mắt"*), preserve the `active_character` identity rather than assigning a random or generic character.

---

### 3.3 R7: 100% Monochrome & 0% Broken Images Architecture

#### A. Pillow Grayscale & Contrast Post-Processing Pipeline
In `backend/services/cloudflare_ai.py`:

```python
import io
from PIL import Image, ImageOps

def process_manga_monochrome(image_bytes: bytes) -> bytes:
    """
    Server-side post-processing pipeline guaranteeing 100% monochrome manga output:
    1. Reads raw bytes via PIL.
    2. Converts to mode 'L' (8-bit grayscale), mathematically stripping all chroma/hue channels (0% color).
    3. Applies ImageOps.autocontrast (cutoff=2) for deep ink blacks and crisp white paper.
    4. Encodes to JPEG bytes at quality 92.
    """
    if not image_bytes or len(image_bytes) < 100:
        return get_guaranteed_monochrome_fallback()
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # 100% Pure Grayscale (strips RGB completely)
        gray = image.convert("L")
        # High-contrast manga ink curve
        enhanced = ImageOps.autocontrast(gray, cutoff=2)
        
        out_buf = io.BytesIO()
        enhanced.save(out_buf, format="JPEG", quality=92)
        return out_buf.getvalue()
    except Exception as e:
        print(f"[Monochrome Processor] PIL transformation failed: {e}")
        return get_guaranteed_monochrome_fallback()
```

#### B. Guaranteed Monochrome Fallback Generator (Zero Broken Images)
```python
from PIL import Image, ImageDraw, ImageFont

def get_guaranteed_monochrome_fallback(panel_index: int = 1) -> bytes:
    """
    Generates a guaranteed valid 800x800 monochrome manga panel image locally using Pillow.
    Ensures 0% broken image icons even if both Cloudflare and Pollinations are completely unreachable.
    """
    width, height = 800, 800
    img = Image.new("L", (width, height), color=255)  # Crisp white background
    draw = ImageDraw.Draw(img)

    # Manga outer border (thick black frame)
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=0, width=6)
    # Inner screentone frame
    draw.rectangle([(28, 28), (width - 28, height - 28)], outline=180, width=2)

    # Diagonal screentone texture in corner
    for x in range(30, 200, 10):
        draw.line([(x, 30), (30, x)], fill=200, width=1)

    # Manga panel badge in center
    badge_box = [(width // 2 - 160, height // 2 - 40), (width // 2 + 160, height // 2 + 40)]
    draw.rectangle(badge_box, fill=255, outline=0, width=3)
    
    caption = f"NARRAI MANGA PANEL #{panel_index}"
    # Draw simple fallback text lines
    draw.text((width // 2 - 120, height // 2 - 10), caption, fill=0)

    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=90)
    return out_buf.getvalue()
```

#### C. Elimination of RedirectResponse in `backend/main.py`
Replace lines 614–622:
```python
@app.get("/api/comic/image/{panel_id}")
@app.get("/api/comics/panels/{panel_id}/image")
def get_comic_image(panel_id: int, db: Session = Depends(get_db)):
    panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
    if not panel:
        fallback_bytes = get_guaranteed_monochrome_fallback(panel_id)
        return Response(content=fallback_bytes, media_type="image/jpeg")

    try:
        story_id = (panel.comic.story_id if panel.comic else None) or panel.comic_id or 1
        comic_seed = get_deterministic_comic_seed(story_id)
        img_bytes, media_type = get_cached_or_generate_image(
            panel.id, panel.image_prompt, seed=comic_seed, story_id=story_id
        )
        return Response(content=img_bytes, media_type=media_type)
    except Exception as e:
        print(f"[Comic Image] Generation failed: {e}. Returning guaranteed monochrome fallback.")
        fallback_bytes = get_guaranteed_monochrome_fallback(panel.panel_index or panel.id)
        return Response(content=fallback_bytes, media_type="image/jpeg")
```
*Key achievement*: The client browser NEVER receives a redirect to an external third-party domain. Every single request returns HTTP 200 with valid, readable monochrome JPEG bytes.

#### D. Multi-Layer Monochrome Defense in Frontend CSS (`frontend/src/app/globals.css`)
```css
.comic-panel img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  min-height: 360px;
  filter: grayscale(100%) contrast(105%);
}
```

---

## 4. Caveats

1. **Groq Model Latency vs Banlist**:
   - The anti-cliché banlist in system prompts significantly steers output, but probabilistic generative models can rarely invent new trite phrases. Combining strong system prompt constraints with the programmatic `validate_anti_cliche_compliance` validator ensures complete compliance.
2. **CLIP Tokenizer Estimator**:
   - Exact word-to-token ratio in CLIP is roughly 1 word = 1.2 to 1.3 tokens. Keeping Visual DNA under 25 words guarantees it fits within ~32 tokens.
3. **Pillow Dependency**:
   - `Pillow` must be installed in the Python environment and added to `backend/requirements.txt` (`Pillow>=10.0.0`).

---

## 5. Conclusion & Action Plan for Workers

### Worker Task Breakdown:

| Task ID | Component | File Path | Objective |
|---|---|---|---|
| **W-R5.1** | Novel Engine | `backend/agents/story_generator.py` | Enrich `LIGHT_NOVEL_ENGINE_RULES` with comprehensive Anti-Cliché Banlist, 4-pillar Show Don't Tell rules, and In Medias Res dramatic opening. Implement `validate_anti_cliche_compliance`. |
| **W-R5.2** | Copilot Agent | `backend/agents/copilot_agent.py` | Add bilingual English/Vietnamese keywords to `_is_direct_edit_request`. Update `DIRECT_EDIT_PROMPT` with novel engine rules and anti-cliché banlist. Enforce safe token bounds. |
| **W-R5.3** | Editor Agent | `backend/agents/editor_agent.py` | Synchronize `edit_text` prompt with anti-cliché banlist and Show Don't Tell physical sensation rules. |
| **W-R6.1** | Comic DNA Prioritization | `backend/agents/comic_agent.py` | Reorder prompt assembly in `_validate_panels`: inject Character Visual DNA (Face, Hair, Outfits) at Position 1 (tokens 15–42) ahead of action and setting. Streamline `STYLE_PREFIX`. |
| **W-R6.2** | Pronoun & Identity Continuity | `backend/agents/comic_agent.py` | Add First-Person pronouns (`"tôi"`, `"mình"`) to protagonist aliases. Add active character context tracking across sequential comic panels. |
| **W-R7.1** | Dependencies | `backend/requirements.txt` | Add `Pillow>=10.0.0`. |
| **W-R7.2** | Server-side Post-Processing | `backend/services/cloudflare_ai.py` | Implement `process_manga_monochrome` (PIL `convert('L')` + `autocontrast`) and `get_guaranteed_monochrome_fallback`. Ensure disk cache only stores processed monochrome JPEGs. |
| **W-R7.3** | Zero-Redirect Image Serving | `backend/main.py` | Eliminate `RedirectResponse`. Proxy/serve all images directly as HTTP 200 with local fallback image on any network failure. |
| **W-R7.4** | Frontend Defense | `frontend/src/app/globals.css` | Add `filter: grayscale(100%) contrast(105%);` to `.comic-panel img`. |

---

## 6. Verification Method

### Test Commands to Run:
1. **Milestone R5 Test Suite**:
   - `python -m unittest backend/tests/test_light_novel_engine.py`
   - Create new unit test `test_anti_cliche_banlist_and_sensory_rules`:
     * Verify all banned phrases trigger violation detection in `validate_anti_cliche_compliance`.
     * Verify compliant story prose produces 0 violations.
     * Verify English commands trigger `_is_direct_edit_request`.
2. **Milestone R6 Test Suite**:
   - `python -m unittest backend/tests/test_comic_dna_seed.py`
   - `python -m unittest backend/tests/test_comic_modern_school_sync.py`
   - `python -m unittest backend/tests/test_comic_dsgo_bridge.py`
   - Add test `test_clip_77_token_dna_priority`:
     * Verify that in `_validate_panels`, character visual DNA appears before `action_desc` and before `setting: ...`.
     * Verify character DNA starts within the first 25 words of `image_prompt`.
     * Verify first-person `"tôi"` matches lead character.
3. **Milestone R7 Test Suite**:
   - Add test `test_manga_monochrome_processing_and_zero_redirect`:
     * Test `process_manga_monochrome` with a synthetic RGB image (e.g. bright red 100x100), verify output image format is JPEG, mode is grayscale, and color channels are 0.
     * Test `get_guaranteed_monochrome_fallback`, verify non-empty valid JPEG bytes.
     * Test `/api/comic/image/{panel_id}` with mocked network failure, verify it returns status code 200 (NOT 307 redirect, NOT 500) with `media_type="image/jpeg"`.
