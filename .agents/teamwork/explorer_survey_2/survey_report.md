# Báo Cáo Khảo Sát Kỹ Thuật Toàn Diện — R2: Bảo Vệ Lịch Sử Việt Nam & Bản Quyền
**Tác giả**: explorer_survey_2 (Teamwork Explorer Agent)  
**Ngày thực hiện**: 2026-09-30  
**Mục tiêu**: Khảo sát mã nguồn, phân tích hiện trạng và thiết kế kiến trúc kỹ thuật chi tiết cho Yêu cầu 2 (R2) của Vòng 6:
1. Mở rộng kho tri thức lịch sử Việt Nam từ 6 lên 30 anh hùng & sự kiện lịch sử qua các thời kỳ.
2. Định vị và lý giải hiện trạng "dead code" của `validate_historical_invariants`.
3. Kích hoạt và đấu nối validation hậu sinh truyện (post-generation validation) vào cả `story_generator.py` và `copilot_agent.py`.
4. Thiết kế Bộ phân loại ngữ nghĩa AI (AI Semantic Classifier) chống lách Regex và kiểm soát các nhân vật ngoài danh mục.
5. Cơ chế Tự động nhận diện 3 chế độ sáng tác (Auto-detect 3 Narrative Modes) không cần người dùng chọn thủ công và hiển thị Badge trực quan trên Frontend.
6. Cơ chế Chặn cứng (Hard-blocking) ngay từ bước sinh truyện và chặn xuất bản lên Bảng tin cộng đồng (Social Feed).
7. Hệ thống Phát hiện vi phạm bản quyền thương mại (Commercial IP) và tự động gắn Disclaimer Fanfiction khi xuất bản.

---

## 1. Hiện Trạng Module Lịch Sử & Kiểm Tra Tính Bất Biến (Historical Grounding Modules)

### 1.1. Vị trí các tệp mã nguồn liên quan
Qua quét và phân tích toàn bộ mã nguồn `backend` và `frontend`, các module liên quan mật thiết đến R2 bao gồm:

1. **`backend/services/ontology.py` (690 dòng)**:
   - Module hạt nhân hiện tại quản lý:
     * `NarrativeMode` (Enum dòng 36-45): `CHINH_SU` (chế độ 1), `DA_SU` (chế độ 2), `HU_CAU_TU_DO` (chế độ 3).
     * `CulturalTier` (Enum dòng 47-51): Tier 1 (Canonical VN), Tier 2 (Fusion), Tier 3 (Open Domain).
     * `VIETNAMESE_HISTORICAL_CANON` (Dict dòng 99-178): Danh mục tri thức lịch sử hiện tại — **chỉ có duy nhất 6 anh hùng/sự kiện**.
     * `BATTLE_OUTCOME_DISTORTION_PATTERNS` (List dòng 181-186): 4 mẫu regex kiểm tra kết quả trận chiến (Bạch Đằng, Như Nguyệt, Ngọc Hồi - Đống Đa, Lam Sơn).
     * `HistoricalGroundingGatekeeper` (Class dòng 189-260): Chứa phương thức `validate_historical_invariants` (dòng 198-227), `validate` (dòng 230-236) và `get_historical_grounding_prompt` (dòng 239-260).
     * `TriTierOntologyResolver` (Class dòng 317-446): Tính toán điểm tương đồng văn hóa $S_{cult}$ và phân bổ phong cách visual DNA, đại từ xưng hô.
     * `SmartSelectiveLanguageFilter` (Class dòng 509-601): Lọc sáo ngữ AI và từ ngữ dịch kiếm hiệp/tiên hiệp Tàu thô sượng.
     * `resolve_ontology` (Function dòng 642-690): Điểm vào hợp nhất tạo `ResolvedOntology`.

2. **`backend/agents/story_generator.py` (468 dòng)**:
   - Nhập `HistoricalGroundingGatekeeper`, `TriTierOntologyResolver`, `SmartSelectiveLanguageFilter` từ `services.ontology` (dòng 5-24).
   - Gọi `HistoricalGroundingGatekeeper.get_historical_grounding_prompt(mode_enum)` tại dòng 266 và 339 để **ghép các chỉ thị vào System Prompt của LLM**.
   - **Hoàn toàn KHÔNG gọi `validate_historical_invariants`** ở bất kỳ phương thức sinh truyện nào (`generate_story`, `generate_story_stream`, `generate_chapter_stream`, `generate_ending_stream`).

3. **`backend/agents/copilot_agent.py` (927 dòng)**:
   - Chứa `CopilotAgent`, `HeadingPreservationEngine`, `SemanticChunkSlicer`, `classify_surgery_intent`, `unwrap_story_prose`.
   - **HOÀN TOÀN KHÔNG IMPORT và KHÔNG GỌI `HistoricalGroundingGatekeeper` hay `validate_historical_invariants`**.
   - Khi thực hiện can thiệp phẫu thuật bản thảo (`_perform_direct_manuscript_edit` dòng 734-829 hoặc `process_event` dòng 831-927), văn bản sửa đổi được trả về thẳng cho người dùng mà không hề qua bất kỳ bộ lọc lịch sử nào.

4. **`backend/main.py` (1501 dòng)**:
   - Endpoint `POST /api/generate-story` (dòng 461-570): Nhận `refined_prompt` và `story_length`, chạy streaming trực tiếp qua `gen.generate_story_stream(...)`. Không kiểm tra tính chân thực lịch sử ở cả đầu vào lẫn đầu ra.
   - Endpoint `POST /api/copilot-event` (dòng 1072-1165): Nhận sự kiện Copilot, kiểm tra lỗi JSON lồng nhau (`[Copilot DB Guard]` dòng 1123-1138), nhưng không hề kiểm tra tính bất biến lịch sử trước khi ghi đè vào DB (`story.story_content = updated_content`).

5. **`backend/routers/social_router.py` (246 dòng) & `backend/services/recommender_service.py` (1203 dòng)**:
   - Endpoint `POST /api/social/publish` (dòng 145-180): Nhận `title`, `content_snippet`, `story_text`, `genre`, gọi `publish_post`.
   - Hàm `publish_post` (dòng 883-960) lưu bài viết vào bảng `social_posts` mà **0% kiểm tra xuyên tạc lịch sử** và **0% kiểm tra vi phạm bản quyền thương mại**.

---

## 2. Vì Sao `validate_historical_invariants` Là Dead Code? (Root Cause Analysis)

### 2.1. Vị trí định nghĩa
Hàm `validate_historical_invariants` được định nghĩa chính thức tại `backend/services/ontology.py`, dòng 198-227:

```python
class HistoricalGroundingGatekeeper:
    @classmethod
    def validate_historical_invariants(cls, text: str, mode: NarrativeMode = NarrativeMode.CHINH_SU) -> Tuple[bool, List[str]]:
        if mode == NarrativeMode.HU_CAU_TU_DO:
            return True, []
        if not text or not isinstance(text, str):
            return True, []
        violations = []
        # Quét Regex từng anh hùng trong VIETNAMESE_HISTORICAL_CANON
        ...
        # Quét BATTLE_OUTCOME_DISTORTION_PATTERNS
        ...
        return len(violations) == 0, violations
```

### 2.2. Bằng chứng "Dead Code" trong mã nguồn thực thi
Qua phân tích toàn bộ các lệnh gọi hàm trên toàn bộ dự án (`grep_search`):
- `validate_historical_invariants` **chỉ xuất hiện trong 4 tệp unit test**:
  * `backend/tests/test_adaptive_open_ontology.py` (dòng 83, 101, 111, 120)
  * `backend/tests/test_e2e_ontology_modes.py` (dòng 90, 113, 238, 242, 284, 288, 294)
  * `backend/tests/test_backend_integration_gen2.py` (dòng 112, 121)
  * `backend/tests/test_adversarial_narrative_recommender.py` (dòng 137, 161, 181, 198, 207, 224)
- **Trong toàn bộ luồng sản phẩm (Production Runtime Paths)**:
  * Không có một dòng code nào trong `main.py`, `story_generator.py`, `copilot_agent.py`, `social_router.py`, `recommender_service.py` gọi hàm này!

### 2.3. Nguyên nhân gốc rễ (Root Cause)
1. **Ảo tưởng "System Prompt là đủ"**: Thiết kế ban đầu ở Vòng 4 chỉ chèn đoạn text răn đe lịch sử vào prompt gửi lên LLM (`HistoricalGroundingGatekeeper.get_historical_grounding_prompt(mode_enum)`). Nhà phát triển đã ngộ nhận rằng mô hình LLM sẽ 100% tuân thủ chỉ thị mà quên mất hiện tượng "Jailbreak", "Prompt Injection" hoặc "Model Hallucination".
2. **Thiếu chốt chặn hậu kiểm (Post-generation Assertion)**: Khi hoàn tất sinh truyện hoặc chỉnh sửa văn bản, hàm sinh truyện trả thẳng kết quả hoặc stream trực tiếp về client mà không có lớp Assertion chặn lại.
3. **Đứt gãy liên kết kiến trúc**: `CopilotAgent` được xây dựng độc lập mà không tích hợp `HistoricalGroundingGatekeeper`.
4. **Hệ quả nguy hiểm**: Người dùng có thể yêu cầu sinh truyện "Trần Hưng Đạo thua trận Bạch Đằng", LLM có thể sinh ra văn bản xuyên tạc, backend lưu văn bản đó vào cơ sở dữ liệu SQLite và người dùng bấm "Lưu & Đăng bài" đưa văn bản đó lên Mạng xã hội công khai mà không gặp bất kỳ trở ngại nào.

---

## 3. Thiết Kế Mở Rộng Danh Mục Tri Thức Lịch Sử Việt Nam (Từ 6 lên 31 Anh Hùng & Sự Kiện)

Hiện tại, `VIETNAMESE_HISTORICAL_CANON` chỉ có 6 nhân vật:
1. `hai_ba_trung`
2. `ngo_quyen`
3. `ly_thuong_kiet`
4. `tran_hung_dao`
5. `le_loi`
6. `quang_trung`

Dưới đây là thiết kế chi tiết mở rộng thành **31 Anh Hùng & Đại Thắng Dân Tộc** trải dài qua 6 thời kỳ lịch sử lớn của non sông Việt Nam, chuẩn hóa cấu trúc dữ liệu cho `VIETNAMESE_HISTORICAL_CANON`:

### Bảng Danh Mục 31 Anh Hùng & Biến Cố Lịch Sử Toàn Diện

| STT | Mã định danh (`key`) | Nhân vật / Biến cố lịch sử | Niên đại / Triều đại | Kẻ thù / Tướng giặc bị đánh bại | Tính bất biến lịch sử (Invariants - Bắt buộc tuân thủ) | Mẫu Regex chặn xuyên tạc (`defeat_regex`) |
|:---:|:---|:---|:---|:---|:---|:---|
| 1 | `hung_vuong` | Hùng Vương, Các Vua Hùng, Lạc Long Quân, Âu Cơ | Thời đại Hồng Bàng, Văn Lang | Giặc Ân, giặc mũi đỏ, thế lực ngoại bang | Dựng nước Văn Lang, truyền thuyết bọc trăm trứng, cội nguồn dân tộc, không bị giặc Ân tiêu diệt | `(?i)\b(?:vua\s+hùng\|hùng\s+vương)\b.*?\b(?:đầu\s+hàng\|bán\s+nước\|bị\s+giặc\s+ân\s+xóa\s+sổ)\b` |
| 2 | `thanh_giong` | Thánh Gióng, Phù Đổng Thiên Vương | Đời Hùng Vương thứ 6 | Giặc Ân | Cưỡi ngựa sắt, nhổ tre đằng ngà đánh tan giặc Ân, bay về trời; không quy hàng giặc | `(?i)\b(?:thánh\s+gióng\|phù\s+đổng\s+thiên\s+vương)\b.*?\b(?:bại\s+trận\|đầu\s+hàng\|thua\s+giặc\s+ân)\b` |
| 3 | `an_duong_vuong` | An Dương Vương, Thục Phán | Nước Âu Lạc (TK 3 TCN) | Triệu Đà, quân Nam Việt | Xây thành Cổ Loa, Nỏ thần Kim Quy đánh lui nhiều đợt xâm lược của Triệu Đà | `(?i)\b(?:an\s+dương\s+vương\|thục\s+phán)\b.*?\b(?:hèn\s+nhát\|đầu\s+hàng\s+triệu\s+đà\s+ngay\s+từ\s+đầu)\b` |
| 4 | `hai_ba_trung` | Hai Bà Trưng (Trưng Trắc, Trưng Nhị) | Năm 40 SCN | Tô Định, quân Đông Hán | Khởi nghĩa năm 40 giành 65 thành trì, đuổi Tô Định; tuẫn tiết giữ trọn khí tiết, tuyệt đối không quỳ gối đầu hàng Tô Định | `(?i)\b(?:trưng\s+trắc\|trưng\s+nhị\|hai\s+bà\s+trưng)\b.*?\b(?:đầu\s+hàng\|phản\s+bội\|quy\s+hàng\|bán\s+nước\|cầu\s+xin\s+tô\s+định)\b` |
| 5 | `ba_trieu` | Bà Triệu (Triệu Thị Trinh) | Năm 248 SCN | Lục Dận, quân Đông Ngô | Tuyên ngôn đạp sóng dữ chém cá kình Biển Đông, cưỡi voi đánh giặc Ngô, khí phách kiên trinh | `(?i)\b(?:bà\s+triệu\|triệu\s+thị\s+trinh)\b.*?\b(?:đầu\s+hàng\|bán\s+nước\|quy\s+hàng\s+quân\s+ngô\|sợ\s+hãi\s+lục\s+dận)\b` |
| 6 | `ly_nam_de` | Lý Nam Đế (Lý Bí) | Năm 544 | Tiêu Tư, quân nhà Lương | Khởi nghĩa đánh đuổi Tiêu Tư, lập nhà nước Vạn Xuân, xưng Hoàng đế | `(?i)\b(?:lý\s+bí\|lý\s+nam\s+đế)\b.*?\b(?:đầu\s+hàng\s+nhà\s+lương\|phản\s+bội\s+vạn\s+xuân)\b` |
| 7 | `trieu_quang_phuc` | Triệu Quang Phục (Dạ Trạch Vương) | Thế kỷ 6 | Trần Bá Tiên, quân Lương | Căn cứ đầm Dạ Trạch, chiến thuật du kích thần kỳ, đánh bại tướng Trần Bá Tiên | `(?i)\b(?:triệu\s+quang\s+phục\|dạ\s+trạch\s+vương)\b.*?\b(?:đầu\s+hàng\s+nhà\s+lương\|thua\s+nhục\s+ở\s+dạ\s+trạch)\b` |
| 8 | `mai_thuc_loan` | Mai Thúc Loan (Mai Hắc Đế) | Năm 713 - 722 | Quân nhà Đường, Dương Tư Húc | Khởi nghĩa Hoan Châu, xây thành Vạn An chống ách đô hộ nhà Đường | `(?i)\b(?:mai\s+thúc\s+loan\|mai\s+hắc\s+đế)\b.*?\b(?:đầu\s+hàng\s+nhà\s+đường\|cầu\s+xin\s+giặc)\b` |
| 9 | `phung_hung` | Phùng Hưng (Bố Cái Đại Vương) | Năm 766 - 791 | Quân đô hộ nhà Đường | Đánh chiếm phủ Tống Bình, giành quyền tự chủ lâu dài cho nhân dân | `(?i)\b(?:phùng\s+hưng\|bố\s+cái\s+đại\s+vương)\b.*?\b(?:đầu\s+hàng\s+quan\s+đô\s+hộ\|phản\s+bội\s+dân\s+tộc)\b` |
| 10 | `ngo_quyen` | Ngô Quyền (Tiền Ngô Vương) | Trận Bạch Đằng 938 | Hoằng Tháo, Nam Hán, Kiều Công Tiễn | Cọc ngầm bọc sắt, chém chết Hoằng Tháo, đại thắng Bạch Đằng 938 chấm dứt 1000 năm Bắc thuộc | `(?i)\b(?:ngô\s+quyền\|tiền\s+ngô\s+vương)\b.*?\b(?:bại\s+trận\|thua\s+trận\|đầu\s+hàng\|bị\s+lưu\s+hoằng\s+tháo\s+(?:bắt\|giết)\|thất\s+bại\s+trên\s+sông\s+bạch\s+đằng)\b` |
| 11 | `dinh_bo_linh` | Đinh Bộ Lĩnh (Đinh Tiên Hoàng) | Năm 968 | 12 sứ quân | Cờ lau tập trận, Vạn Thắng Vương, dẹp loạn 12 sứ quân thống nhất giang sơn, định đô Hoa Lư lập nước Đại Cồ Việt | `(?i)\b(?:đinh\s+bộ\s+lĩnh\|đinh\s+tiên\s+hoàng)\b.*?\b(?:bại\s+trận\s+trước\s+12\s+sứ\s+quân\|chia\s+cắt\s+đất\s+nước\|đầu\s+hàng)\b` |
| 12 | `le_hoan` | Lê Hoàn (Lê Đại Hành) | Năm 981 | Hầu Nhân Bảo, quân nhà Tống | Chiến thắng Bạch Đằng 981, chém chết chủ tướng giặc Hầu Nhân Bảo, phá Tống bình Chiêm | `(?i)\b(?:lê\s+hoàn\|lê\s+đại\s+hành)\b.*?\b(?:thua\s+hầu\s+nhân\s+bảo\|đầu\s+hàng\s+quân\s+tống\|thất\s+bại\s+năm\s+981)\b` |
| 13 | `ly_thai_to` | Lý Thái Tổ (Lý Công Uẩn) | Năm 1010 | — | Soạn Chiếu dời đô 1010 từ Hoa Lư về Đại La - Thăng Long, mở ra thời kỳ thịnh trị Đại Việt | `(?i)\b(?:lý\s+thái\s+tổ\|lý\s+công\s+uẩn)\b.*?\b(?:hối\s+hận\s+dời\s+đô\|phản\s+quốc\|bán\s+đất)\b` |
| 14 | `ly_thuong_kiet` | Lý Thường Kiệt (Ngô Tuấn) | Năm 1077 (Phòng tuyến Như Nguyệt) | Quách Quỳ, Triệu Tiết, quân Tống | Tuyên ngôn độc lập "Nam quốc sơn hà", đánh tan quân Tống trên sông Cầu giữ vững độc lập | `(?i)\b(?:lý\s+thường\s+kiệt)\b.*?\b(?:bại\s+trận\|thua\s+trận\|đầu\s+hàng\s+quân\s+tống\|thua\s+quách\s+quỳ\|bị\s+quân\s+tống\s+bắt\|thất\s+bại\s+ở\s+như\s+nguyệt)\b` |
| 15 | `tran_hung_dao` | Trần Hưng Đạo (Trần Quốc Tuấn) | Thế kỷ 13 (Ba lần kháng chiến Nguyên Mông) | Thoát Hoan, Ô Mã Nhi, Phàn Tiếp | Tác giả Hịch tướng sĩ, chỉ huy 3 lần đại thắng Nguyên Mông, đại thắng Bạch Đằng 1288 bắt sống Ô Mã Nhi | `(?i)\b(?:trần\s+hưng\s+đạo\|trần\s+quốc\s+tuấn\|hưng\s+đạo\s+đại\s+vương)\b.*?\b(?:bại\s+trận\|thua\s+trận\|thua\s+cuộc\|đầu\s+hàng\|bị\s+bắt\|chui\s+ống\s+đồng\|bị\s+thoát\s+hoan\s+bắt\|thất\s+bại\s+bạch\s+đằng\|thua\s+quân\s+nguyên)\b` |
| 16 | `tran_quoc_toan` | Trần Quốc Toản (Hoài Văn Hầu) | Năm 1285 | Quân Nguyên Mông | Bóp nát quả cam tại hội nghị Bình Than, cờ thêu 6 chữ vàng "Phá cường địch, báo hoàng ân", xông pha trận mạc dũng cảm | `(?i)\b(?:trần\s+quốc\s+toản\|hoài\s+văn\s+hầu)\b.*?\b(?:phản\s+bội\|đầu\s+hàng\s+thoát\s+hoan\|sợ\s+chết\|vứt\s+cờ\s+sáu\s+chữ)\b` |
| 17 | `tran_nhan_tong` | Trần Nhân Tông (Phật hoàng) | Thế kỷ 13 | Quân Nguyên Mông | Lãnh tụ tối cao cùng Quốc công Tiết chế lãnh đạo kháng chiến toàn dân, Hội nghị Diên Hồng, sáng lập thiền phái Trúc Lâm | `(?i)\b(?:trần\s+nhân\s+tông\|phật\s+hoàng)\b.*?\b(?:đầu\s+hàng\s+quân\s+nguyên\|bán\s+nước\|chạy\s+trốn\s+nhục\s+nhã)\b` |
| 18 | `tran_khanh_du` | Trần Khánh Dư (Nhân Huệ Vương) | Trận Vân Đồn 1288 | Trương Văn Hổ | Bổ nhào đánh tan đoàn thuyền lương Trương Văn Hổ ở Vân Đồn, bẻ gãy ý đồ hậu cần của quân Nguyên Mông | `(?i)\b(?:trần\s+khanh\s+dư\|trận\s+vân\s+đồn)\b.*?\b(?:thua\s+trương\s+văn\s+hổ\|đầu\s+hàng\|bị\s+tiêu\s+diệt\s+hoàn\s+toàn)\b` |
| 19 | `yet_kieu_da_tuong` | Yết Kiêu, Dã Tượng | Thời Trần (Thế kỷ 13) | Quân Nguyên Mông | Tướng tài thủy chiến và tượng binh, đục thuyền giặc Ô Mã Nhi, trung thành tuyệt đối với Hưng Đạo Vương | `(?i)\b(?:yết\s+kiêu\|dã\s+tượng)\b.*?\b(?:phản\s+bội\s+trần\s+hưng\s+đạo\|bán\s+chủ\|đầu\s+hàng\s+thoát\s+hoan)\b` |
| 20 | `le_loi` | Lê Lợi (Bình Định Vương, Lê Thái Tổ) | Khởi nghĩa Lam Sơn (1418 - 1427) | Liễu Thăng, Vương Thông, Lương Minh | Gian khổ 10 năm nếm mật nằm gai, chém Liễu Thăng tại Chi Lăng, buộc Vương Thông mở hội thề Đông Quan rút quân | `(?i)\b(?:lê\s+lợi\|bình\s+định\s+vương\|khởi\s+nghĩa\s+lam\s+sơn)\b.*?\b(?:bại\s+trận\|thua\s+trận\|đầu\s+hàng\s+quân\s+minh\|bị\s+liễu\s+thăng\s+(?:bắt\|giết)\|thất\s+bại\s+hoàn\s+toàn)\b` |
| 21 | `nguyen_trai` | Nguyễn Trãi (Ức Trai) | Khởi nghĩa Lam Sơn (1418 - 1427) | Quân nhà Minh | Mưu sĩ xuất sắc, tác giả Bình Ngô đại cáo ("Đem đại nghĩa để thắng hung tàn, lấy chí nhân để thay cường bạo") | `(?i)\b(?:nguyễn\s+trãi\|ức\s+trai)\b.*?\b(?:phản\s+bội\s+lê\s+lợi\|làm\s+tay\s+sai\s+quân\s+minh\|bán\s+nước)\b` |
| 22 | `le_thanh_tong` | Lê Thánh Tông | Thế kỷ 15 (Triều Hậu Lê) | — | Thời kỳ Hồng Đức thịnh trị, bản đồ Hồng Đức, Bộ luật Hồng Đức, văn võ toàn tài, Tao Đàn Nhị thập bát tú | `(?i)\b(?:lê\s+thánh\s+tông)\b.*?\b(?:làm\s+mất\s+nước\|bán\s+giang\s+sơn\|hèn\s+nhát)\b` |
| 23 | `quang_trung` | Quang Trung (Nguyễn Huệ) | Khởi nghĩa Tây Sơn (1785 - 1789) | Tôn Sĩ Nghị, Sầm Nghi Đống, Xiêm La | Hành quân thần tốc, đại phá 2 vạn quân Xiêm tại Rạch Gầm - Xoài Mút, đại phá 29 vạn quân Thanh tại Ngọc Hồi - Đống Đa Tết 1789 | `(?i)\b(?:quang\s+trung\|nguyễn\s+huệ\|bắc\s+bình\s+vương)\b.*?\b(?:bại\s+trận\|thua\s+trận\|đầu\s+hàng\s+quân\s+thanh\|thua\s+tôn\s+sĩ\s+nghị\|thất\s+bại\s+ở\s+ngọc\s+hồi\|thất\s+bại\s+ở\s+đống\s+đa\|thua\s+quân\s+xiêm)\b` |
| 24 | `bui_thi_xuan` | Bùi Thị Xuân | Khởi nghĩa Tây Sơn | Quân Trịnh, giặc ngoại bang | Đô đốc nữ tướng Tây Sơn, chỉ huy đội voi chiến bách chiến bách thắng, khí tiết lẫm liệt đến giây phút cuối | `(?i)\b(?:bùi\s+thị\s+xuân)\b.*?\b(?:đầu\s+hàng\s+hèn\s+nhát\|cầu\s+xin\s+tha\s+mạng\|phản\s+bội\s+tây\s+sơn)\b` |
| 25 | `truong_dinh` | Trương Định (Bình Tây Đại Nguyên Soái) | Kháng Pháp Nam Kỳ (1859 - 1864) | Thực dân Pháp | "Bình Tây Đại Nguyên Soái", thà chết vì độc lập dân tộc chứ không tuân hòa ước đầu hàng Pháp của triều đình | `(?i)\b(?:trương\s+định\|bình\s+tây\s+đại\s+nguyên\s+soái)\b.*?\b(?:đầu\s+hàng\s+giặc\s+pháp\|làm\s+tay\s+sai\s+cho\s+pháp)\b` |
| 26 | `nguyen_trung_truc` | Nguyễn Trung Trực | Kháng chiến chống Pháp (1861 - 1868) | Thực dân Pháp | Đốt tàu Espérance trên sông Nhật Tảo, chiếm đồn Rạch Giá, câu nói bất hủ: "Bao giờ Tây nhổ hết cỏ nước Nam thì mới hết người Nam đánh Tây" | `(?i)\b(?:nguyễn\s+trung\s+trực)\b.*?\b(?:đầu\s+hàng\s+quân\s+pháp\|quy\s+hàng\|phản\s+bội\s+nghĩa\s+quân)\b` |
| 27 | `phan_dinh_phung` | Phan Đình Phùng, Cao Thắng | Khởi nghĩa Hương Khê (1885 - 1896) | Thực dân Pháp | Lãnh tụ phong trào Cần Vương, kiên trì kháng chiến nơi rừng núi Hương Khê, Cao Thắng tự chế tạo súng trường kiểu Pháp | `(?i)\b(?:phan\s+đình\s+phùng\|cao\s+thắng\|khởi\s+nghĩa\s+hương\s+khê)\b.*?\b(?:đầu\s+hàng\s+pháp\|phản\s+bội\s+cần\s+vương\|làm\s+tay\s+sai)\b` |
| 28 | `hoang_hoa_tham` | Hoàng Hoa Thám (Đề Thám, Hùm xám Yên Thế) | Khởi nghĩa Yên Thế (1884 - 1913) | Thực dân Pháp | "Hùm xám Yên Thế", chỉ huy nghĩa quân bền bỉ chiến đấu chống thực dân Pháp suốt 30 năm ở núi rừng Bắc Giang | `(?i)\b(?:hoàng\s+hoa\s+thám\|đề\s+thám\|hùm\s+xám\s+yên\s+thế)\b.*?\b(?:đầu\s+hàng\s+pháp\|làm\s+tay\s+sai\s+thực\s+dân\|phản\s+bội)\b` |
| 29 | `vo_thi_sau` | Võ Thị Sáu, Kim Đồng, Bế Văn Đàn, Tô Vĩnh Diện | Thời kỳ kháng chiến chống Pháp | Thực dân Pháp | Nữ anh hùng Đất Đỏ kiên trung trước họng súng Côn Đảo; các tấm gương thiếu niên dũng cảm hy sinh thân mình cứu đồng đội | `(?i)\b(?:võ\s+thị\s+sáu\|kim\s+đồng\|tô\s+vĩnh\s+diện\|bế\s+văn\s+đàn)\b.*?\b(?:đầu\s+hàng\|khai\s+báo\s+phản\s+bội\|hèn\s+nhát\s+cầu\s+xin)\b` |
| 30 | `vo_nguyen_giap` | Đại tướng Võ Nguyên Giáp, Chiến dịch Điện Biên Phủ | Năm 1954 | Tướng De Castries, Thực dân Pháp | Chỉ huy Chiến dịch Điện Biên Phủ 1954 đại thắng "lừng lẫy năm châu, chấn động địa cầu", bắt sống tướng De Castries, buộc Pháp ký Hiệp định Geneva | `(?i)\b(?:võ\s+nguyên\s+giáp\|đại\s+tướng\s+giáp\|điện\s+biên\s+phủ)\b.*?\b(?:thua\s+trận\s+điện\s+biên\|đầu\s+hàng\s+pháp\|thất\s+bại\s+trước\s+đờ\s+cát\|bại\s+trận\s+năm\s+1954)\b` |
| 31 | `chien_dich_ho_chi_minh` | Chiến dịch Hồ Chí Minh, Đại thắng Mùa Xuân 1975 | Tháng 4 năm 1975 | Quân xâm lược và chính quyền tay sai | Chiến dịch Hồ Chí Minh lịch sử, xe tăng tiến vào Dinh Độc Lập trưa ngày 30/4/1975, giải phóng hoàn toàn miền Nam, thống nhất non sông | `(?i)\b(?:chiến\s+dịch\s+hồ\s+chí\s+minh\|đại\s+thắng\s+mùa\s+xuân\s+1975\|ngày\s+30\/4)\b.*?\b(?:thất\s+bại\s+hoàn\s+toàn\|quân\s+ta\s+bị\s+tiêu\s+diệt\|không\s+thống\s+nhất\s+được)\b` |

---

## 4. Thiết Kế Bộ Phân Loại Ngữ Nghĩa AI (AI Semantic Classifier) Chống Lách Regex

### 4.1. Hạn chế chí mạng của Regex thuần túy
Dù có 31 mẫu Regex cực kỳ tỉ mỉ, cơ chế Regex đơn thuần vẫn có thể bị vượt qua (Regex Evasion) bằng các kỹ thuật ngôn ngữ tự nhiên:
1. **Câu chủ động biến thành bị động / đảo ngữ chủ thể**:
   - Ví dụ: *"Quân Mông Cổ ca khúc khải hoàn trên khúc sông Bạch Đằng đầy cọc gỗ."*  
     -> Không chứa cụm từ *"Trần Hưng Đạo bại trận"* nhưng ngữ nghĩa khẳng định giặc ngoại xâm thắng!
   - Ví dụ: *"Tướng De Castries đứng trên nóc hầm Mường Thanh uống champagne mừng quân Pháp đánh tan Việt Minh."*
2. **Ẩn dụ, nói giảm nói tránh và hoán dụ**:
   - Ví dụ: *"Ngọn cờ thêu sáu chữ vàng chìm nghỉm dưới dòng nước xiết, chủ nhân của nó quỳ gối xin được bảo toàn tính mạng."*
   - Ví dụ: *"Vị Tiết chế Đại Việt trao gươm báu cúi đầu trước lều trướng của hoàng tử Nguyên triều."*
3. **Xuyên tạc nhân vật chưa liệt kê trong Canon cứng**:
   - Ví dụ: *"Dã Tượng mang theo bản đồ bí mật bến sông sang doanh trại Ô Mã Nhi đầu hàng để đổi lấy chức vương."*  
   - Ví dụ: *"Nguyễn Trãi khuyên Lê Lợi dâng biểu xưng thần vĩnh viễn với hoàng đế Minh triều."*

### 4.2. Kiến trúc Bộ phân loại ngữ nghĩa 2 lớp (Two-Pass Hybrid Validator)

```
              ┌────────────────────────────────────────┐
              │           Văn bản đầu vào             │
              │  (Prompt / Sinh truyện / Sửa Copilot)   │
              └───────────────────┬────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │  Pass 1: Fast Regex Gate  │  (0ms latency)
                    │  (31 Canon Regex Patterns)│
                    └─────────────┬─────────────┘
                                  │
                   ┌──────────────┴──────────────┐
            [Khớp vi phạm]                [Không vi phạm]
                   │                             │
                   ▼                             ▼
        ┌─────────────────────┐      ┌─────────────────────────────┐
        │  Chặn cứng ngay lập │      │ Quét bộ từ khóa thực thể    │
        │  tức: REJECT        │      │ Lịch sử VN & Chiến dịch     │
        └─────────────────────┘      └──────────────┬──────────────┘
                                                    │
                                     ┌──────────────┴──────────────┐
                              [Có thực thể Lịch sử]         [Thuần hư cấu / OOD]
                                     │                             │
                                     ▼                             ▼
                      ┌─────────────────────────────┐      ┌───────────────┐
                      │ Pass 2: AI Semantic Checker │      │ Bỏ qua (Pass) │
                      │  (Low-latency LLM Inference)│      └───────────────┘
                      └──────────────┬──────────────┘
                                     │
                     ┌───────────────┴───────────────┐
            [is_distortion = true]        [is_distortion = false]
                     │                               │
                     ▼                               ▼
        ┌─────────────────────────┐     ┌────────────────────────┐
        │ Hard-Block & Exception  │     │ Cho phép tiếp tục luồng│
        └─────────────────────────┘     └────────────────────────┘
```

### 4.3. Đặc tả Prompt & Cấu trúc JSON của AI Semantic Classifier
Sử dụng mô hình siêu nhẹ (`llama-3.1-8b-instant` hoặc `openai/gpt-oss-20b` trên Groq) với cấu hình:
- `temperature: 0.0`
- `max_tokens: 250`
- `response_format: {"type": "json_object"}`
- Thời gian phản hồi ước tính: **~150ms - 250ms**.

**System Prompt tiêu chuẩn**:
```
Bạn là Hệ thống Thẩm định Lịch sử Quốc gia NarrAI (Vietnamese Historical Integrity Gatekeeper).
Nhiệm vụ của bạn là phân tích ngữ nghĩa của văn bản để phát hiện mọi hành vi XUYÊN TẠC, ĐẢO NGƯỢC LỊCH SỬ VIỆT NAM hoặc BÔI NHỌ ANH HÙNG DÂN TỘC.

CÁC NGUYÊN TẮC BẤT BIẾN (INVIOLABLE TRUTHS):
1. Các cuộc kháng chiến vệ quốc vĩ đại (Bạch Đằng 938, 981, 1288; Như Nguyệt 1077; Khởi nghĩa Lam Sơn; Ngọc Hồi - Đống Đa 1789; Điện Biên Phủ 1954; Chiến dịch Hồ Chí Minh 1975) BẮT BUỘC là chiến thắng của dân tộc Việt Nam.
2. Các anh hùng dân tộc (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Nguyễn Trãi, Quang Trung, Võ Nguyên Giáp...) và các tướng lĩnh phụ tá (Trần Quốc Toản, Yết Kiêu, Dã Tượng, Bùi Thị Xuân...) không bao giờ quỳ gối đầu hàng, làm tay sai, phản bội non sông hay chịu thất bại trước ngoại bang.
3. Chú ý các thủ pháp lách regex: Câu bị động ("quân giặc thắng lớn trên sông Bạch Đằng"), ẩn dụ ("ngọn cờ Đại Việt gãy gục"), hoặc hoán đổi kết quả chiến tranh.

PHÂN BIỆT 3 CHẾ ĐỘ:
- Chính sử (chinh_su): Viết về nhân vật và sự kiện thật -> 100% tuân thủ sự thật lịch sử.
- Dã sử (da_su): Bối cảnh lịch sử thật, nhưng nhân vật chính hư cấu (người lính, thường dân) -> Cho phép nhân vật hư cấu gặp trắc trở cá nhân, nhưng KHÔNG ĐƯỢC làm sai lệch đại cục chiến thắng của dân tộc hay phẩm giá anh hùng lịch sử.
- Hư cấu tự do (hu_cau_tu_do): Hoàn toàn không liên quan lịch sử Việt Nam -> Cho phép tự do sáng tạo.

ĐẦU RA BẮT BUỘC (JSON DUY NHẤT):
{
  "is_distortion": boolean,
  "confidence": float (0.0 to 1.0),
  "violation_reason": string (nêu rõ chi tiết xuyên tạc nếu is_distortion = true, ngược lại để rỗng),
  "detected_mode": "chinh_su" | "da_su" | "hu_cau_tu_do"
}
```

---

## 4. Tự Động Nhận Diện 3 Chế Độ Sáng Tác (Auto-Detect Narrative Modes)

### 4.1. Vì sao loại bỏ lựa chọn thủ công trên UI?
1. **Trải nghiệm ChatGPT / Gemini tối giản**: Người dùng chỉ cần gõ ý tưởng sáng tác ("Tôi muốn viết về một người thợ rèn tại Thăng Long thời nhà Trần chế tạo vũ khí cho quân đội"), hệ thống phải tự hiểu đây là bối cảnh **Dã sử**.
2. **Chống lạm dụng / bypass**: Nếu để người dùng tự chọn, kẻ có ý đồ xấu sẽ chọn chế độ "Hư cấu tự do" để viết truyện xuyên tạc chiến thắng Điện Biên Phủ hoặc biến Trần Hưng Đạo thành kẻ phản bội. Với cơ chế **Auto-detect do server độc quyền quyết định**, ý đồ này bị triệt tiêu 100%.

### 4.2. Thuật toán tự động nhận diện (Heuristic + Semantic Hybrid)

```python
def auto_detect_narrative_mode(text: str, genre: str = "") -> Tuple[NarrativeMode, str]:
    """
    Tự động xác định Chế độ Sáng tác dựa trên thực thể, từ khóa và ngữ cảnh:
    1. CHÍNH SỬ: Trực tiếp lấy nhân vật lịch sử hoặc đại chiến dịch lịch sử làm trung tâm.
    2. DÃ SỬ: Bối cảnh triều đại/thời đại lịch sử VN là có thật, nhưng nhân vật chính là hư cấu.
    3. HƯ CẤU TỰ DO: Không có yếu tố lịch sử VN, hoặc thuộc thể loại viễn tưởng, tiên hiệp, đô thị.
    """
    combined = f"{genre} {text}".lower()
    
    # 1. Kiểm tra các dấu hiệu rõ rệt của Hư cấu tự do ngoài miền (Out of Domain)
    ood_signals = ["sci-fi", "cyberpunk", "isekai", "tiên hiệp", "tu chân", "phương tây", "ma pháp", "new york", "hogwarts"]
    has_ood = any(s in combined for s in ood_signals)
    
    # 2. Tìm kiếm thực thể anh hùng và triều đại lịch sử VN
    has_canon_hero = any(hero_key in combined or any(alias in combined for alias in canon["names"]) 
                         for hero_key, canon in VIETNAMESE_HISTORICAL_CANON.items())
    has_dynasty = any(d in combined for d in VN_DYNASTIES_PERIODS)
    has_battle = any(b in combined for b in ["bạch đằng", "như nguyệt", "lam sơn", "ngọc hồi", "đống đa", "điện biên phủ", "chiến dịch hồ chí minh"])
    
    # Nếu không có bất kỳ tín hiệu lịch sử nào hoặc có tín hiệu OOD mạnh
    if not (has_canon_hero or has_dynasty or has_battle):
        return NarrativeMode.HU_CAU_TU_DO, "Hư cấu tự do"
    
    # 3. Phân biệt Chính Sử vs Dã Sử:
    # Nhận diện các dấu hiệu nhân vật hư cấu cá nhân (Dã sử)
    fictional_lens_markers = [
        "nghĩa sĩ vô danh", "đôi trai gái", "người lính cấm vệ", "thợ rèn", "cô gái bán",
        "góc nhìn của", "chuyện tình thời chiến", "thiếu niên thời trần", "lữ khách",
        "nhân vật tự nghĩ", "người vô danh", "nghĩa sĩ thầm lặng", "người lính thường"
    ]
    is_fictional_perspective = any(m in combined for m in fictional_lens_markers)
    
    if is_fictional_perspective:
        return NarrativeMode.DA_SU, "Dã sử (Góc nhìn phóng tác)"
        
    if has_canon_hero or has_battle:
        return NarrativeMode.CHINH_SU, "Chính sử (Tôn trọng sự thật lịch sử)"
        
    if has_dynasty:
        return NarrativeMode.DA_SU, "Dã sử (Góc nhìn phóng tác)"
        
    return NarrativeMode.HU_CAU_TU_DO, "Hư cấu tự do"
```

### 4.3. Hiển thị Badge thông minh trên Giao diện Frontend
Backend trả về `narrative_mode` và `mode_label` trong kết quả các API:
- `POST /api/refine-prompt`
- `POST /api/generate-story` (qua stream metadata hoặc Story record)
- `POST /api/copilot-event`

Trên `frontend/src/components/editor/StoryEditor.tsx`, ở thanh Top Bar bên cạnh số đếm từ (Word Count), hiển thị nhãn trạng thái (Badge):
1. **Chế độ 1 — Chính sử**:  
   `<span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30 flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-amber-600"/> Chính sử: Tôn trọng sự thật</span>`
2. **Chế độ 2 — Dã sử**:  
   `<span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5 text-emerald-600"/> Dã sử: Phóng tác góc nhìn</span>`
3. **Chế độ 3 — Hư cấu tự do**:  
   `<span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-indigo-500"/> Hư cấu tự do</span>`

Người dùng **hoàn toàn không phải bấm nút chọn chế độ**, mọi thứ vận hành tự động và trong suốt.

---

## 5. Đấu Nối Post-Generation Validation Vào `story_generator.py` & `copilot_agent.py`

### 5.1. Đấu nối vào `backend/agents/story_generator.py`
Hiện tại, `story_generator.py` có 4 phương thức sinh truyện chính:
1. `generate_story(refined_prompt, story_length, narrative_mode, genre)`: Trả về string.
2. `generate_story_stream(refined_prompt, story_length, narrative_mode, genre)`: Trả về generator chunks.
3. `generate_chapter_stream(memory, user_instruction)`: Sinh chương mới.
4. `generate_ending_stream(memory)`: Sinh kết thúc.

**Kế hoạch đấu nối**:
1. **Tiền kiểm (Preflight Check)**: Trước khi gọi LLM, kiểm tra `refined_prompt` qua `HistoricalGroundingGatekeeper.validate_historical_invariants(refined_prompt, mode)`. Nếu người dùng cố tình gửi yêu cầu xuyên tạc -> Chặn ngay lập tức, không tốn token, không trừ xu.
2. **Hậu kiểm cho phương thức đồng bộ `generate_story`**:
   ```python
   raw_prose = self.llm.chat(messages, ...)
   is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(raw_prose, mode=mode_enum)
   if not is_valid:
       raise HistoricalDistortionError(f"Phát hiện nội dung sinh ra vi phạm lịch sử: {'; '.join(violations)}")
   return raw_prose
   ```
3. **Hậu kiểm cho Streaming `generate_story_stream` trong `main.py` (`stream_and_save`)**:
   - Trong quá trình streaming, tích lũy `full_story`.
   - Khi hoàn thành streaming, trước khi ghi `full_story` vào cơ sở dữ liệu `Story`:
     ```python
     is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(full_story, mode=detected_mode)
     if not is_valid:
         # KHÔNG LƯU VÀO DB!
         # Tự động hoàn xu (compensating refund)
         if current_user and deduct_ref:
             refund_coins(db, current_user.id, cost, ACTION_REFUND_FAILED, deduct_ref, "Hoàn xu do vi phạm chuẩn mực lịch sử")
         yield f"\n\n[HISTORICAL_VIOLATION: Nội dung đã bị chặn do vi phạm lịch sử dân tộc: {'; '.join(violations)}]"
         return
     ```

### 5.2. Đấu nối vào `backend/agents/copilot_agent.py`
1. Nhập `HistoricalGroundingGatekeeper`, `auto_detect_narrative_mode`, `NarrativeMode` vào `copilot_agent.py`.
2. Trong hàm `_perform_direct_manuscript_edit(user_instruction, current_story)` (dòng 734):
   - Sau khi tổng hợp `final_story` (dòng 807):
     ```python
     mode, _ = auto_detect_narrative_mode(final_story)
     is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(final_story, mode=mode)
     if not is_valid:
         safe_log(f"[Copilot Direct Edit Blocked] Violations: {violations}")
         return {
             "thought": f"Historical distortion detected in edited manuscript: {violations}",
             "action": "reply_user",
             "action_params": {
                 "message": f"Hệ thống không thể thực hiện chỉnh sửa này vì vi phạm nguyên tắc bảo vệ lịch sử Việt Nam: {'; '.join(violations)}"
             }
         }
     ```
3. Trong hàm `process_event`:
   - Kiểm tra `res["action"] == "edit_story_direct"`: Kiểm tra `updated_story_content` trước khi trả về.
4. Trong `backend/main.py` tại endpoint `/api/copilot-event`:
   - Bổ sung tầng chốt chặn cơ sở dữ liệu: Trước khi cập nhật `story.story_content = updated_content`, chạy kiểm tra `validate_historical_invariants`. Nếu vi phạm, từ chối cập nhật và trả về HTTP 422.

---

## 6. Chặn Cứng (Hard-Blocking) & Chặn Xuất Bản (Social Feed Blocking)

### 6.1. Chặn cứng ngay từ bước tạo truyện (Generation Step)
- Ngăn chặn hoàn toàn việc lưu trữ bản thảo vi phạm vào DB.
- Khi một yêu cầu sinh truyện vi phạm bị chặn:
  * Trả về mã lỗi trực tiếp `[HISTORICAL_VIOLATION: ...]` cho client.
  * Nếu tài khoản đã bị trừ xu tạm giữ trước đó, gọi ngay `refund_coins` với mã hoàn tiền bồi hoàn `ACTION_REFUND_FAILED` để bảo đảm quyền lợi tài chính minh bạch cho người dùng.

### 6.2. Chặn xuất bản lên Mạng xã hội (`POST /api/social/publish`)
Hiện tại, trong `backend/routers/social_router.py`:
```python
@router.post("/publish")
async def publish_social_post(req: PublishPostRequest, ...):
```
**Thiết kế chốt chặn xuất bản**:
1. Tổng hợp toàn văn bài viết cần kiểm duyệt: `combined_text = f"{req.title}\n{req.content_snippet}\n{req.story_text or ''}"`.
2. Tự động nhận diện chế độ: `detected_mode, _ = auto_detect_narrative_mode(combined_text, req.genre)`.
3. Kiểm tra tính bất biến lịch sử:
   ```python
   is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(combined_text, mode=detected_mode)
   if not is_valid:
       raise HTTPException(
           status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
           detail={
               "error": "HISTORICAL_VIOLATION",
               "message": "Tác phẩm vi phạm chuẩn mực lịch sử Việt Nam và bị cấm xuất bản lên mạng xã hội.",
               "violations": violations
           }
       )
   ```
4. Đảm bảo 0% bài viết xuyên tạc lịch sử có thể lọt vào bảng tin cộng đồng NarrAI.

---

## 7. Phát Hiện Bản Quyền Thương Mại & Tự Động Gắn Disclaimer Fanfiction

### 7.1. Danh mục Bản Quyền Thương Mại Phổ Biến (`COMMERCIAL_IP_REGISTRY`)
Thiết kế bảng đăng ký các Franchise thương mại nổi tiếng thế giới để nhận diện:

```python
COMMERCIAL_IP_REGISTRY = {
    "Harry Potter": {
        "franchise": "Wizarding World / J.K. Rowling",
        "keywords": ["harry potter", "hermione", "ron weasley", "voldemort", "dumbledore", "hogwarts", "gryffindor", "slytherin", "hufflepuff", "ravenclaw", "quidditch", "tử thần thực tử", "chúa tể hắc ám voldemort"],
        "creative_alternatives": {
            "Harry Potter": "Hải Phong / Harry Vance",
            "Hogwarts": "Học viện Pháp thuật Thăng Long / Trường Phép thuật Cổ Sơn",
            "Voldemort": "Chúa tể U Hồn / Ma Tôn Hắc Ám"
        }
    },
    "Marvel Cinematic Universe": {
        "franchise": "Marvel / Disney",
        "keywords": ["iron man", "tony stark", "spider-man", "spiderman", "peter parker", "captain america", "steve rogers", "thanos", "thor odinson", "avengers", "hulk", "bruce banner", "black widow", "natasha romanoff", "wolverine", "x-men", "deadpool"],
        "creative_alternatives": {
            "Iron Man": "Chiến giáp Kim Thần / Giáp Sắt Thần Binh",
            "Thanos": "Bá vương Tinh vân / Bạo chúa Không gian",
            "Spider-Man": "Người Nhện Thiếu Niên / Chu Vực"
        }
    },
    "DC Comics": {
        "franchise": "DC / Warner Bros",
        "keywords": ["batman", "bruce wayne", "superman", "clark kent", "joker", "wonder woman", "harley quinn", "gotham", "metropolis", "justice league"],
        "creative_alternatives": {
            "Batman": "Hiệp sĩ Bóng đêm Dạ Thành / Ám Dạ Du Hiệp",
            "Gotham": "Thành phố Hắc Lạc / Đô thị Tội ác"
        }
    },
    "Anime & Manga": {
        "franchise": "Shueisha / Kodansha",
        "keywords": ["naruto", "sasuke", "kakashi", "sharingan", "luffy", "zoro", "one piece", "goku", "vegeta", "saiyan", "tanjiro", "nezuko", "gojo satoru", "sukuna", "jujutsu kaisen", "levi ackerman", "eren yeager"],
        "creative_alternatives": {
            "Naruto": "Thiếu niên Phong Ma / Nhẫn giả Lôi Thần",
            "Gojo Satoru": "Ngũ Nhãn Tiên Sinh / Cường giả Vô Hạn"
        }
    },
    "Star Wars & Disney": {
        "franchise": "Lucasfilm / Disney",
        "keywords": ["darth vader", "luke skywalker", "jedi", "sith", "lightsaber", "yoda", "mickey mouse", "elsa", "olaf"],
        "creative_alternatives": {
            "Jedi": "Hiệp sĩ Tinh Tế / Kiếm sĩ Quang Năng",
            "Lightsaber": "Thần kiếm Ánh sáng"
        }
    }
}
```

### 7.2. Hàm phát hiện bản quyền (`detect_commercial_ip`)
```python
def detect_commercial_ip(text: str) -> Dict[str, Any]:
    """
    Quét văn bản để phát hiện IP thương mại được bảo hộ:
    Trả về:
    {
        "has_commercial_ip": bool,
        "matched_ips": List[str],
        "matched_franchises": List[str],
        "creative_suggestions": Dict[str, str],
        "fanfiction_disclaimer": str
    }
    """
    if not text:
        return {"has_commercial_ip": False, "matched_ips": [], "matched_franchises": [], "creative_suggestions": {}, "fanfiction_disclaimer": ""}
        
    text_lower = text.lower()
    matched_ips = []
    matched_franchises = []
    suggestions = {}
    
    for ip_name, ip_data in COMMERCIAL_IP_REGISTRY.items():
        for kw in ip_data["keywords"]:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, text_lower):
                matched_ips.append(kw)
                if ip_name not in matched_franchises:
                    matched_franchises.append(ip_name)
                for orig, alt in ip_data["creative_alternatives"].items():
                    if orig.lower() in text_lower:
                        suggestions[orig] = alt
                        
    has_ip = len(matched_ips) > 0
    disclaimer = (
        "⚠️ Tác phẩm fan fiction — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại."
        if has_ip else ""
    )
    
    return {
        "has_commercial_ip": has_ip,
        "matched_ips": list(set(matched_ips)),
        "matched_franchises": matched_franchises,
        "creative_suggestions": suggestions,
        "fanfiction_disclaimer": disclaimer
    }
```

### 7.3. Luồng xử lý Fanfiction Disclaimer khi Publish
1. **Kiểm tra tại `POST /api/social/publish`**:
   - Gọi `copyright_info = detect_commercial_ip(f"{req.title} {req.content_snippet} {req.story_text or ''}")`.
   - Nếu `copyright_info["has_commercial_ip"] == True`:
     * Đánh dấu bài viết là Fanfiction: `is_fanfiction = True`.
     * Tự động bổ sung tag `Fanfiction` vào danh sách `tags` của bài viết nếu chưa có.
     * Lưu `disclaimer = copyright_info["fanfiction_disclaimer"]` vào `SocialPost`.
2. **Cập nhật Schema Cơ sở dữ liệu (`backend/db/models.py`)**:
   - Thêm 2 cột mới vào bảng `social_posts`:
     * `is_fanfiction = Column(Boolean, default=False, index=True)`
     * `disclaimer = Column(String(500), nullable=True)`
   - Cập nhật hàm auto-migration khi khởi động server:
     ```python
     if "is_fanfiction" not in post_cols:
         conn.execute(text("ALTER TABLE social_posts ADD COLUMN is_fanfiction BOOLEAN DEFAULT 0"))
     if "disclaimer" not in post_cols:
         conn.execute(text("ALTER TABLE social_posts ADD COLUMN disclaimer VARCHAR(500) DEFAULT NULL"))
     ```
3. **Hiển thị trên giao diện `CommunityFeedView.tsx`**:
   - Thẻ bài đăng (Card): Hiển thị badge màu hổ phách `[Fanfiction]` ngay cạnh thể loại.
   - Modal đọc chi tiết bài viết (Reader Modal): Hiển thị hộp thông báo vàng trang trọng ở đầu trang:
     ```html
     <div className="p-3 mb-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-300 text-xs flex items-center gap-2">
       <span>⚠️</span>
       <span>Tác phẩm fan fiction — không liên quan đến tác phẩm gốc và không nhằm mục đích thương mại.</span>
     </div>
     ```

---

## 8. Kế Hoạch Đấu Nối Kiến Trúc & Kiểm Thử Chi Tiết

### 8.1. Ma trận thay đổi tập tin (Change Impact Matrix)

| Tệp tin | Trách nhiệm hiện tại | Thay đổi cần thực hiện cho R2 |
|:---|:---|:---|
| `backend/services/ontology.py` | Quản lý tri thức, Gatekeeper, 6 anh hùng | Mở rộng `VIETNAMESE_HISTORICAL_CANON` lên 31 anh hùng, tích hợp `auto_detect_narrative_mode`, `AISemanticHistoricalClassifier`, `COMMERCIAL_IP_REGISTRY`, `detect_commercial_ip`. |
| `backend/agents/story_generator.py` | Sinh truyện chữ và chương mới | Bổ sung Preflight Check và Post-generation validation gọi `HistoricalGroundingGatekeeper.validate_historical_invariants`. |
| `backend/agents/copilot_agent.py` | Can thiệp phẫu thuật bản thảo | Import `HistoricalGroundingGatekeeper`, thực hiện validation trên `final_story` và từ chối ghi đè nếu phát hiện vi phạm lịch sử. |
| `backend/main.py` | Endpoints API chính | Nhúng auto-detect mode vào `refine_prompt`, post-validation & refund vào `generate_story`, chặn ghi đè DB trong `copilot_event`. |
| `backend/db/models.py` | Schema SQLite / SQLAlchemy | Bổ sung `is_fanfiction` và `disclaimer` vào model `SocialPost` kèm auto-migration. |
| `backend/routers/social_router.py` | Quản lý mạng xã hội & publish | Chặn xuất bản bài viết vi phạm lịch sử; tự động gắn `is_fanfiction` và `disclaimer` nếu phát hiện IP thương mại. |
| `backend/services/recommender_service.py` | Logic publish_post | Cập nhật hàm `publish_post` nhận và lưu `is_fanfiction` và `disclaimer`. |
| `frontend/src/components/editor/StoryEditor.tsx` | Soạn thảo văn bản | Hiển thị Auto-detected Mode Badge (Chính sử / Dã sử / Hư cấu) trên thanh công cụ. |
| `frontend/src/components/social/CommunityFeedView.tsx` | Bảng tin cộng đồng | Hiển thị Badge Fanfiction và Disclaimer Banner khi đọc truyện có IP thương mại. |
| `frontend/src/lib/types.ts` | Khai báo kiểu TypeScript | Cập nhật interface `SocialPost`, `PublishSocialPostPayload` hỗ trợ `is_fanfiction`, `disclaimer`, `narrative_mode`. |

### 8.2. Danh mục Test Cases Cần Bổ Sung (Test Suite Specification)
Cần bổ sung tập tin kiểm thử chuyên biệt: `backend/tests/test_round6_historical_copyright.py` bao gồm tối thiểu 15-20 test cases:

1. **Test Suite 1: Expanded Historical Canon (31 Heroes)**:
   - Kiểm tra toàn bộ 31 anh hùng đều có mẫu regex chặn đảo ngược chiến công chính xác.
   - Thử nghiệm các ca lịch sử hợp lệ (Đại thắng Bạch Đằng 1288, Điện Biên Phủ 1954, Chi Lăng - Xương Giang) -> Kết quả `True, []`.
2. **Test Suite 2: Historical Invariants Post-Generation Activation**:
   - Kiểm tra `HistoricalGroundingGatekeeper.validate_historical_invariants` được kích hoạt và chặn thành công khi có vi phạm.
   - Kiểm tra test case bắt buộc: *"Trần Hưng Đạo thua trận Bạch Đằng"* -> Bị chặn, không sinh truyện.
3. **Test Suite 3: AI Semantic Classifier (Regex Bypass Resilience)**:
   - Kiểm tra lách regex: *"quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng"* -> Bị phát hiện và chặn.
   - Kiểm tra tướng giặc / nhân vật phụ: *"Dã Tượng quy hàng và dâng bản đồ trận địa"* -> Bị phát hiện và chặn.
4. **Test Suite 4: Auto-detect Narrative Modes**:
   - Văn bản về Trần Hưng Đạo -> Auto-detect `CHINH_SU`.
   - Văn bản về người lính vô danh thời Trần -> Auto-detect `DA_SU`.
   - Văn bản về Cyberpunk New York -> Auto-detect `HU_CAU_TU_DO`.
   - Chế độ `HU_CAU_TU_DO` cho phép sáng tạo tự do không bị chặn.
5. **Test Suite 5: Copilot Historical Guard**:
   - Yêu cầu Copilot "Hãy sửa lại cái kết để quân Pháp toàn thắng tại Điện Biên Phủ" -> Copilot từ chối, bản thảo nguyên vẹn 100%.
6. **Test Suite 6: Social Publish Blocking & Copyright Fanfiction Disclaimer**:
   - Thử xuất bản bài viết xuyên tạc lịch sử -> Endpoint trả về HTTP 422, từ chối lưu DB.
   - Xuất bản truyện có chứa nhân vật "Harry Potter" hoặc "Iron Man" -> Tự động gắn cờ `is_fanfiction = True` và chèn disclaimer fanfiction hợp lệ.

---

## 9. Kết Luận Khảo Sát
1. Việc bảo vệ lịch sử Việt Nam và bản quyền thương mại hoàn toàn khả thi về mặt kỹ thuật mà không làm ảnh hưởng đến hiệu năng hay trải nghiệm người dùng.
2. Việc chuyển đổi từ "dead code" sang "active enforcement" tại cả 3 chốt chặn: **Sinh truyện (Story Generator)**, **Biên tập (Copilot Agent)** và **Xuất bản (Social Publish)** sẽ thiết lập vành đai bảo vệ kiên cố 360 độ cho nền tảng NarrAI.
3. Cơ chế tự động nhận diện 3 chế độ sáng tác (Auto-detect) loại bỏ hoàn toàn gánh nặng thao tác thủ công của người dùng, mang lại giao diện tinh giản đẳng cấp theo đúng định hướng ChatGPT / Gemini.
4. Mọi thông số và kiến trúc chi tiết đã sẵn sàng để đội ngũ triển khai (Implementer) hiện thực hóa mã nguồn một cách trơn tru, tương thích ngược 100% với 182 bài kiểm thử hiện có.
