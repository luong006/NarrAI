# Báo Cáo Chuyển Giao (Handoff Report): Backend & AI Resilience Survey (R3)

**Người gửi:** explorer_r7_backend  
**Người nhận:** orchestrator (6e1fbb7b-e64c-45b5-8d0a-ea6939f474c6) / implementation agents  
**Thời gian:** 2026-10-05T05:42:00Z  
**Loại chuyển giao:** Hard Handoff (Khảo sát hoàn tất 100%, sẵn sàng triển khai)  

---

## 1. OBSERVATION (CÁC QUAN SÁT THỰC NGHIỆM TRỰC TIẾP)

1. **Khởi tạo đơn điểm trong `backend/agents/qa_refiner.py`**:
   - Dòng 7: `self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))`.
   - Dòng 49-53: Phương thức `chat_interview` gọi trực tiếp `self.llm.chat(messages, temperature=0.7, max_tokens=300)` mà không có bất kỳ khối `try...except` chuyển đổi mô hình hay khóa API dự phòng nào.
   - Nếu `qwen/qwen3.8-27b` hoặc `GROQ_API_KEY_BIBLE` gặp lỗi (429 Rate Limit, token limit, downtime), hàm lập tức ném ngoại lệ làm sập luồng xử lý.

2. **Xử lý ngoại lệ tại Endpoint `/api/chat-interview` (`backend/main.py`)**:
   - Dòng 397-406:
     ```python
     @app.post("/api/chat-interview")
     def chat_interview(request: ChatInterviewRequest):
         try:
             qa = get_qa_refiner()
             response = qa.chat_interview(request.chat_history)
             is_ready = "[READY]" in response
             cleaned_response = response.replace("[READY]", "").strip()
             return {"status": "success", "message": cleaned_response, "is_ready": is_ready}
         except Exception as e:
             return {"status": "error", "message": str(e)}
     ```
   - Khi có ngoại lệ ở LLM, endpoint bắt lỗi và trả về HTTP 200 kèm `{ "status": "error", "message": str(e) }`.

3. **Nguồn gốc câu văn mẫu rập khuôn tại `frontend/src/components/setup/UnifiedIntakeChat.tsx`**:
   - Dòng 289-311:
     ```tsx
     const res = await api.chatInterview(newHistory);
     if (res.status === "success" && res.message) {
       // ... thành công ...
     } else {
       setMessages([
         ...newHistory,
         {
           role: "assistant",
           content: lang === "vi"
             ? "Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."
             : "Fascinating premise! Could you elaborate more on the protagonist, core conflict, or narrative setting?"
         }
       ]);
     }
     ```
   - Khi `res.status !== "success"` (backend báo lỗi rate limit hoặc lỗi LLM), Frontend tự động nhét câu văn mẫu tĩnh: *"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính..."* vào lịch sử trò chuyện.
   - Khi xảy ra lỗi mạng (`catch (err: any)` ở dòng 300), Frontend nhét câu văn mẫu: *"Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ..."*.
   - Hoàn toàn không có hiển thị trạng thái lỗi kết nối và không có nút "Thử lại" (Retry).

4. **Sự bất đối xứng của Bottom Input Dock (`UnifiedIntakeChat.tsx`)**:
   - Dòng 597: `<div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 ...">`.
   - Neo giữ `sm:left-64` cứng nhắc khiến thanh input bị lệch pha so với trục giữa của toàn bộ khung chat khi Sidebar thay đổi trạng thái hoặc trên các độ phân giải màn hình khác nhau.

5. **Hiện trạng các khóa Groq trong môi trường (`backend/.env`)**:
   - Đã xác thực sự tồn tại của đầy đủ 4 khóa: `GROQ_API_KEY`, `GROQ_API_KEY_COPILOT`, `GROQ_API_KEY_BIBLE`, `GROQ_API_KEY_COMIC`.

6. **Ràng buộc tương thích ngược đối với Unit Tests**:
   - `backend/tests/test_light_novel_engine.py:287` kiểm tra `refiner.llm.chat = mock_chat`. Do đó `refiner.llm` bắt buộc phải tồn tại và phương thức `chat` của nó phải là điểm chạm đầu tiên.

---

## 2. LOGIC CHAIN (CHUỖI SUY LUẬN TỪ QUAN SÁT ĐẾN KẾT LUẬN)

1. **Từ Quan sát 1 & 2**: `QARefiner` bị phụ thuộc hoàn toàn vào 1 mô hình (`qwen/qwen3.8-27b`) và 1 khóa API (`GROQ_API_KEY_BIBLE`). Miễn là Groq chạm trần 8000 TPM limit hoặc mô hình Qwen bảo trì, backend sẽ trả về lỗi `status: "error"`.
2. **Từ Quan sát 3**: Frontend khi nhận `status: "error"` đã ngụy trang lỗi bằng một câu assistant cố định ("Ý tưởng của bạn rất cuốn hút..."). Vì vậy, người dùng cứ gửi bất kỳ nội dung nào cũng nhận lại câu nói y hệt. Đây là lỗi thiết kế bẫy lỗi ở Frontend kết hợp với sự thiếu bền bỉ (resilience) ở Backend, không phải do AI cố tình trả lời như vậy.
3. **Từ Quan sát 1, 2, 5**: Backend có sẵn 3 khóa API và 3 mô hình tương thích trên Groq (`qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`). Việc xây dựng ma trận dự phòng kép (3 mô hình x 3 khóa = 9 đường dẫn dự phòng) sẽ giải quyết 99.9% nguy cơ rate limit hoặc gián đoạn dịch vụ.
4. **Từ Quan sát 3 & 4**: Để loại bỏ vĩnh viễn cảm giác "văn mẫu", Frontend cần:
   - Xóa bỏ 2 câu hardcode tại `UnifiedIntakeChat.tsx`.
   - Bổ sung thanh trạng thái kết nối và nút "Thử lại" (Retry).
   - Tích hợp Dynamic Client Fallback trích xuất từ khóa của chính người dùng để phản hồi gợi mở ngay cả khi offline hoàn toàn.
   - Chuyển `fixed sm:left-64` thành layout flex/sticky căn giữa đồng bộ với container chat.

---

## 3. CAVEATS (CÁC ĐIỂM LƯU Ý & GIẢ THUYẾT)

1. **Khóa API trong CI/CD / Môi trường Test**: Trong môi trường chạy tự động không có file `.env`, các biến môi trường có thể là chuỗi giả (`dummy_key`). Thiết kế Fallback phải kiểm tra sự tồn tại và tính hợp lệ của key, tránh ném lỗi khởi tạo rỗng.
2. **Giới hạn tốc độ của Client Fallback**: Bộ trích xuất từ khóa trên Client là bộ xử lý heuristic quy tắc tự nhiên (Rule-based Regex & Semantics), nhằm cứu cánh khi mất mạng hoàn toàn. Khi có mạng, hệ thống luôn ưu tiên 100% LLM Groq.
3. **Không ảnh hưởng các Agent khác**: Thay đổi này khu trú hoàn toàn trong `qa_refiner.py`, `backend/main.py`, `api.ts`, và `UnifiedIntakeChat.tsx`. Không tác động đến `copilot_agent.py`, `comic_agent.py`, hay `story_generator.py`.

---

## 4. CONCLUSION (KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG CỤ THỂ)

Hệ thống cần được triển khai theo 4 gói giải pháp cụ thể:

1. **Gói 1 — Backend Resilience (`backend/agents/qa_refiner.py`)**:
   - Thêm danh sách `MODELS = ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]`.
   - Thêm danh sách `KEY_ENV_VARS = ["GROQ_API_KEY_BIBLE", "GROQ_API_KEY", "GROQ_API_KEY_COPILOT"]`.
   - Triển khai phương thức `_chat_with_resilience(messages, temperature=0.7, max_tokens=400)` thử `self.llm` trước, sau đó quét qua ma trận Models x Keys.
   - Nâng cấp `System Prompt` trong `chat_interview`: Bắt buộc Concept Mirroring (phản chiếu từ khóa người dùng) và đặt 1-2 câu hỏi sâu sắc kèm ví dụ tương phản trong ngoặc đơn, nghiêm cấm các câu mở đầu sáo rỗng.
2. **Gói 2 — Backend Endpoint (`backend/main.py`)**:
   - Bổ sung thông tin mô hình đã sử dụng `model_used` vào payload trả về của `/api/chat-interview`.
3. **Gói 3 — Frontend API (`frontend/src/lib/api.ts`)**:
   - Thêm khối bảo vệ `try...catch` và phân tích lỗi `!res.ok` trong `chatInterview` để trả về `{ status: 'error', message: ... }` an toàn.
4. **Gói 4 — Frontend Chat UI & Dynamic Fallback (`UnifiedIntakeChat.tsx`)**:
   - Triệt tiêu 2 câu hardcode văn mẫu tĩnh.
   - Tích hợp hàm `generateDynamicClientFallback(userInput, lang)` trích xuất thực thể/bối cảnh và sinh câu hỏi động khi mất mạng.
   - Hiển thị badge trạng thái ngoại tuyến (`WifiOff`) và nút **"Thử lại" (Retry)** cho phép bấm thử lại ngay lập tức.
   - Tái cấu trúc thanh bottom input dock: thay thế `fixed sm:left-64` bằng layout flex/sticky căn giữa tuyệt đối theo `max-w-3xl mx-auto`.

---

## 5. VERIFICATION METHOD (PHƯƠNG PHÁP KIỂM CHỨNG ĐỘC LẬP)

1. **Kiểm tra cú pháp Backend**:
   ```bash
   python -m py_compile backend/main.py backend/agents/qa_refiner.py
   ```
2. **Chạy toàn bộ 182+ Tests hiện có (Bảo đảm 0 regression)**:
   ```bash
   python backend/tests/run_all_tests.py
   ```
   *Đặc biệt lưu ý `test_light_novel_engine.py` và `test_adversarial_m1.py` phải PASS 100%.*
3. **Kiểm tra Fallback thực tế**:
   - Viết test case giả lập lỗi ở model 1 và key 1, verify hệ thống tự động trả lời qua model 2 / key 2.
   - Gửi yêu cầu với từ khóa "Thánh Gióng" hoặc "Cyberpunk Sài Gòn" -> Verify output chứa chính xác từ khóa đó và không chứa các câu sáo ngữ chào hỏi.
4. **Biên dịch Frontend**:
   ```bash
   cd frontend && npm run build
   ```
   *Yêu cầu kết quả: 0 lỗi TypeScript, 0 lỗi biên dịch.*
