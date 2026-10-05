# Báo Cáo Khảo Sát Kỹ Thuật: Backend & AI Resilience Cho NarrAI (R3)

**Tác giả:** explorer_r7_backend  
**Mục tiêu:** Khảo sát toàn diện hệ thống Chat Interview / QA Refiner, cơ chế Multi-Model & Multi-Key Fallback, nâng cấp System Prompt chống câu trả lời rập khuôn, và kiến trúc Dynamic Client Fallback kèm nút Thử lại (Retry) trên Frontend.  
**Ngày thực hiện:** 2026-10-05  

---

## 1. TỔNG QUAN HIỆN TRẠNG & NGUYÊN NHÂN GỐC RỄ (EXECUTIVE SUMMARY)

Người dùng phản ánh hiện tượng: *Khi trò chuyện với AI trong màn hình phỏng vấn cốt truyện (Intake Chat), AI liên tục lặp lại một câu văn mẫu cứng nhắc, không chịu phân tích ý tưởng hoặc câu hỏi của người dùng.*

Qua quá trình điều tra mã nguồn thực tế tại `backend/agents/qa_refiner.py`, `backend/main.py`, `frontend/src/components/setup/UnifiedIntakeChat.tsx` và `frontend/src/lib/api.ts`, chúng tôi xác định chính xác **3 nguyên nhân gốc rễ liên hoàn**:

1. **Lỗ hổng đơn điểm tại Backend (`qa_refiner.py:7`)**:
   - `QARefiner` chỉ khởi tạo duy nhất một mô hình `qwen/qwen3.8-27b` với một khóa API đơn lẻ `GROQ_API_KEY_BIBLE`.
   - Khi mô hình chính gặp sự cố, bị hạ trần (decommissioned/maintenance), vượt quá Token Per Minute (TPM 8000 limit của Groq) hoặc khóa API hết hạn, `GroqClient` ném ngoại lệ `Exception`.
   - Backend không có bất kỳ cơ chế thử lại (retry) hay chuyển tiếp sang mô hình dự phòng (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`), cũng không luân chuyển sang các khóa API khác (`GROQ_API_KEY`, `GROQ_API_KEY_COPILOT`).
2. **Cơ chế bẫy lỗi sai lệch tại Frontend (`UnifiedIntakeChat.tsx:289-311`)**:
   - Khi Backend gặp lỗi và trả về `status: "error"`, hoặc khi mạng bị gián đoạn, Frontend lập tức tự động gán một tin nhắn tĩnh từ phía AI:
     > *"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."*
     hoặc:
     > *"Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ hoặc bấm 'Bắt đầu viết truyện ngay'..."*
   - Câu nói này **không phải do mô hình AI sinh ra**, mà là văn mẫu bị hardcode ở khối `else` và `catch` của component. Người dùng lầm tưởng AI "thiểu năng" lặp lại một câu nói, trong khi thực tế là backend bị sập/rate-limit và frontend nuốt chửng lỗi mà không cho người dùng biết trạng thái kết nối hay nút "Thử lại".
3. **System Prompt tại `qa_refiner.py:14-44` thiếu kỹ thuật "Mirroring"**:
   - Dù có hướng dẫn phong cách, prompt cũ không bắt buộc AI phải trích xuất trực tiếp danh xưng, bối cảnh hay từ khóa của tác giả, dẫn đến trường hợp khi LLM phản hồi thành công thì vẫn dễ mở đầu bằng các câu chào hỏi xã giao sáo rỗng.

---

## 2. KHẢO SÁT CHI TIẾT MÃ NGUỒN HIỆN TẠI

### 2.1. Backend Endpoint: `/api/chat-interview` (`backend/main.py:397-407`)

```python
# File: backend/main.py (lines 397-406)
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

**Nhận định kỹ thuật:**
- Endpoint nhận `request.chat_history: list` (danh sách `{role, content}`).
- Gọi `qa.chat_interview()`.
- Khi xảy ra lỗi (LLM lỗi, rate limit, timeout), endpoint bắt ngoại lệ và trả về `{ "status": "error", "message": str(e) }` với mã HTTP 200.
- Điểm yếu: Không có thông tin phân loại lỗi (`error_type`), không ghi log chi tiết mô hình nào bị lỗi, và không trả về gợi ý khắc phục.

### 2.2. QA Refiner Agent (`backend/agents/qa_refiner.py`)

```python
# File: backend/agents/qa_refiner.py (lines 5-8, 46-54)
class QARefiner:
    def __init__(self):
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))
    
    def chat_interview(self, chat_history: list) -> str:
        # ... system_prompt ...
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        response = self.llm.chat(
            messages, 
            temperature=0.7, 
            max_tokens=300
        )
        return response
```

**Nhận định kỹ thuật:**
- `self.llm` cố định cứng: `model_name="qwen/qwen3.8-27b"`, `api_key=GROQ_API_KEY_BIBLE`.
- Khóa `GROQ_API_KEY_BIBLE` nếu bị hết quota hoặc chưa cấp đúng trong một số môi trường, `GroqClient` sẽ văng lỗi ngay lập tức mà không thử `GROQ_API_KEY` hay `GROQ_API_KEY_COPILOT`.
- `max_tokens=300` tương đối chật hẹp đối với văn phong tiếng Việt (khoảng 150-200 từ), dễ làm câu trả lời bị đứt đoạn lưng chừng nếu LLM diễn giải dài.
- Trong `test_light_novel_engine.py:287`, kiểm thử gán trực tiếp: `refiner.llm.chat = mock_chat`. Do đó, thuộc tính `self.llm` và phương thức `self.llm.chat` **phải được bảo lưu nguyên vẹn** để không gây vỡ unit test hiện có!

### 2.3. Frontend Client & API Layer (`frontend/src/lib/api.ts:147-156`)

```typescript
// File: frontend/src/lib/api.ts (lines 147-155)
  // Setup Flow
  async chatInterview(history: Array<{role: string; content: string}>): Promise<InterviewResponse> {
    const res = await fetch(`${API_BASE_URL}/chat-interview`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ chat_history: history }),
    });
    return res.json();
  },
```

**Nhận định kỹ thuật:**
- Không có khối `try...catch` bọc quanh `fetch`. Nếu server backend chưa bật hoặc ngắt kết nối mạng (Network Error / Failed to fetch), hàm ném unhandled exception ra ngoài.
- Không kiểm tra `res.ok`. Nếu backend trả về HTTP 500 HTML hoặc lỗi mạng, `res.json()` sẽ throw cú pháp JSON parse error.

### 2.4. Frontend UI: Nguồn Gốc Của Tin Nhắn Cứng Nhắc (`UnifiedIntakeChat.tsx:274-314`)

```tsx
// File: frontend/src/components/setup/UnifiedIntakeChat.tsx (lines 274-313)
    try {
      const res = await api.chatInterview(newHistory);
      if (res.status === "success" && res.message) {
        const cleanMsg = res.message.replace(/\[READY\]/g, "").trim();
        const isReadyFlag = !!(res.is_ready || res.message.includes("[READY]"));
        if (isReadyFlag) {
          setHasReadySignal(true);
        }

        const updatedHistory: ChatMessage[] = [
          ...newHistory,
          { role: "assistant", content: cleanMsg, is_ready: isReadyFlag }
        ];
        setMessages(updatedHistory);
      } else {
        // === VĂN MẪU BỊ HARDCODE SỐ 1 ===
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
    } catch (err: any) {
      console.error("Chat interview error:", err);
      // === VĂN MẪU BỊ HARDCODE SỐ 2 ===
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: lang === "vi"
            ? "Đang kết nối lại với trợ lý NarrAI. Bạn có thể tiếp tục chia sẻ hoặc bấm 'Bắt đầu viết truyện ngay' ở góc trên để khởi tạo bản thảo ngay lập tức!"
            : "Reconnecting to NarrAI Assistant. You can continue detailing or click 'Start writing story now' above to jump straight to drafting!"
        }
      ]);
    } finally {
      setLoading(false);
    }
```

**Hậu quả:**
- Khi người dùng gửi: *"Thánh Gióng"* -> Backend bị 429 Rate Limit -> Frontend rơi vào nhánh `else` -> AI hiện câu: *"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm..."*
- Người dùng gửi tiếp: *"Tôi muốn thời Cyberpunk 2099"* -> Backend vẫn 429 -> Frontend lại rơi vào `else` -> AI lại hiện câu: *"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm..."*
- Người dùng gửi tiếp: *"Nhân vật tên là Lâm"* -> AI vẫn hiện đúng câu trên!
- Người dùng hoàn toàn không hề biết server đang gặp sự cố kết nối, và kết luận rằng hệ thống bị hỏng / AI ngớ ngẩn lặp từ.
- Lịch sử trò chuyện `messages` bị nhiễm bẩn bởi các câu văn mẫu này, khiến khi kết nối lại, ngữ cảnh gửi lên LLM bị loãng.

---

## 3. THIẾT KẾ KIẾN TRÚC BACKEND RESILIENCE (R3 BACKEND)

### 3.1. Chuỗi Multi-Model & Multi-Key Fallback Ma Trận 2 Chiều

Hệ thống cần thiết lập ma trận dự phòng kép:
- **Chuỗi Mô Hình (Model Fallback Chain)**:
  1. `qwen/qwen3.8-27b` (Chất lượng văn học cao nhất, tư duy ngữ cảnh sắc bén)
  2. `llama-3.3-70b-versatile` (Độ ổn định cao, ngữ cảnh lớn 128k, thông minh tương đương GPT-4o)
  3. `llama-3.1-8b-instant` (Tốc độ phản hồi cực nhanh, TPM dồi dào, tỉ lệ rate limit cực thấp)
- **Chuỗi Khóa API (Key Rotation Chain)**:
  1. `GROQ_API_KEY_BIBLE` (Khóa chuyên trách cho Phỏng vấn cốt truyện & Trích xuất ký ức)
  2. `GROQ_API_KEY` (Khóa chính hệ thống sáng tác)
  3. `GROQ_API_KEY_COPILOT` (Khóa điều phối viên dự phòng)

#### Ma Trận Điều Phối (Dispatch Matrix):

```
       [Yêu cầu Chat Interview]
                  │
                  ▼
         [Thử self.llm trước] (Giữ nguyên tương thích Unit Test)
                  │
            (Thành công?) ── Có ──► [Trả về kết quả]
                  │ Không (Lỗi / Rate Limit)
                  ▼
      ┌─────────────────────────────────────────────────────────┐
      │ Vòng lặp Mô hình (Model Loop):                           │
      │ 1. qwen/qwen3.8-27b                                      │
      │ 2. llama-3.3-70b-versatile                               │
      │ 3. llama-3.1-8b-instant                                  │
      └───────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
      ┌─────────────────────────────────────────────────────────┐
      │ Vòng lặp Khóa API (Key Loop):                            │
      │ 1. GROQ_API_KEY_BIBLE                                   │
      │ 2. GROQ_API_KEY                                         │
      │ 3. GROQ_API_KEY_COPILOT                                 │
      └───────────────────────────┬─────────────────────────────┘
                                  │
                                  ▼
                    [Thực hiện client.chat()]
                                  │
            (Thành công?) ── Có ──► [Trả về kết quả + model_used]
                                  │
                                Không (Log warning & thử cặp tiếp theo)
                                  │
                                  ▼
      (Hết ma trận?) ── Có ──► [Kích hoạt Heuristic Fallback / Báo lỗi]
```

### 3.2. Cấu Trúc Mã Nguồn Đề Xuất Cho `backend/agents/qa_refiner.py`

```python
import os
import json
import logging
from llm.groq_client import GroqClient

logger = logging.getLogger("narrai.qa_refiner")

class QARefiner:
    MODELS = [
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    
    KEY_ENV_VARS = [
        "GROQ_API_KEY_BIBLE",
        "GROQ_API_KEY",
        "GROQ_API_KEY_COPILOT",
    ]

    def __init__(self):
        # Khởi tạo primary client để bảo lưu tương thích test_light_novel_engine.py
        primary_key = (
            os.environ.get("GROQ_API_KEY_BIBLE") 
            or os.environ.get("GROQ_API_KEY") 
            or "dummy_key_for_init"
        )
        self.llm = GroqClient(model_name=self.MODELS[0], api_key=primary_key)
        self._client_pool = {}

    @classmethod
    def get_available_keys(cls) -> list[str]:
        keys = []
        for var in cls.KEY_ENV_VARS:
            val = os.environ.get(var)
            if val and val.strip() and val.strip() not in keys:
                keys.append(val.strip())
        if not keys and os.environ.get("GROQ_API_KEY"):
            keys.append(os.environ.get("GROQ_API_KEY").strip())
        return keys

    def _get_client(self, model_name: str, api_key: str) -> GroqClient:
        cache_key = (model_name, api_key)
        if cache_key not in self._client_pool:
            self._client_pool[cache_key] = GroqClient(model_name=model_name, api_key=api_key)
        return self._client_pool[cache_key]

    def _chat_with_resilience(self, messages: list, temperature: float = 0.7, max_tokens: int = 400) -> tuple[str, str]:
        """
        Thực hiện gọi LLM với khả năng tự phục hồi 2 chiều:
        Thử self.llm trước (nếu bị mock trong test sẽ trả về ngay).
        Nếu lỗi, duyệt qua ma trận [Models x Keys].
        Trả về tuple: (response_text, model_name_used).
        """
        # 1. Thử self.llm trước (bảo vệ các unit tests vá mock refiner.llm.chat)
        try:
            res = self.llm.chat(messages, temperature=temperature, max_tokens=max_tokens)
            if res and res.strip():
                return res, getattr(self.llm, "model", self.MODELS[0])
        except Exception as first_err:
            logger.warning(f"[QARefiner] Primary client failed: {first_err}. Initiating multi-model & multi-key fallback...")

        # 2. Duyệt qua chuỗi Fallback ma trận
        candidate_keys = self.get_available_keys()
        last_error = None

        for model in self.MODELS:
            for key in candidate_keys:
                try:
                    client = self._get_client(model, key)
                    resp = client.chat(messages, temperature=temperature, max_tokens=max_tokens)
                    if resp and resp.strip():
                        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "key"
                        logger.info(f"[QARefiner Fallback SUCCESS] Model: {model}, Key: {masked_key}")
                        return resp, model
                except Exception as err:
                    last_error = err
                    logger.warning(f"[QARefiner Fallback] Model '{model}' with key failed ({err}). Trying next candidate...")

        # 3. Nếu toàn bộ ma trận thất bại, ném ngoại lệ rõ ràng
        raise RuntimeError(f"Tất cả mô hình và khóa API trong chuỗi dự phòng đều thất bại: {last_error}")
```

### 3.3. Tinh Chỉnh System Prompt Chống Văn Mẫu Rập Khuôn (Anti-Boilerplate Prompt)

Nâng cấp system prompt trong `chat_interview`:

```python
    def chat_interview(self, chat_history: list) -> str:
        system_prompt = """Bạn là Chuyên gia Đồng sáng tác Văn học & Cố vấn Cốt truyện NarrAI cao cấp, mang phong cách trò chuyện thông minh, sâu sắc, súc tích và khơi gợi cảm hứng như Gemini và ChatGPT.

NHIỆM VỤ: Lắng nghe ý tưởng của tác giả, phân tích sâu và đặt câu hỏi gợi mở để cùng hoàn thiện một cốt truyện độc đáo.

QUY TẮC PHẢN HỒI BẮT BUỘC (TUYỆT ĐỐI TUÂN THỦ):
1. TRÍCH XUẤT & PHẢN CHIẾU TỪ KHÓA CỐT LÕI (CONCEPT MIRRORING):
   - Luôn bắt đầu phản hồi bằng việc điểm danh và phân tích trực tiếp 1-2 từ khóa/chi tiết độc đáo mà tác giả vừa chia sẻ (ví dụ: bối cảnh cụ thể, nhân vật, năng lực, bi kịch, hoặc mâu thuẫn).
   - NGHIÊM CẤM 100% các câu mở đầu sáo rỗng, khuôn mẫu kiểu AI như: "Ý tưởng của bạn rất hay/thú vị/cuốn hút!", "Chào bạn, đây là một tiền đề tuyệt vời", "Tôi rất hào hứng được hỗ trợ bạn". Hãy đi thẳng vào chất liệu câu chuyện!

2. ĐẶT ĐÚNG 1 ĐẾN 2 CÂU HỎI GỢI MỞ SÂU SẮC (DEEP NARRATIVE PROBE):
   - Đặt từ 1 đến 2 câu hỏi mở đánh thẳng vào nút thắt kịch tính:
     + Xung đột nội tâm / Cái giá phải trả / Điểm yếu chí mạng của nhân vật chính.
     + Động cơ bí mật của thế lực phản diện / Quy luật khắc nghiệt của thế giới.
     + Biến cố bùng nổ (inciting incident) đẩy nhân vật vào thế đường cùng.
   - Luôn kèm theo 2 phương án gợi ý tương phản trong ngoặc đơn để kích thích trí tưởng tượng cho tác giả (ví dụ: "(Nhân vật hy sinh ký ức để lấy sức mạnh, hay bị chính người mình tin tưởng nhất phản bội?)").

3. NGUYÊN TẮC THỂ LOẠI & BẢN QUYỀN:
   - Hư cấu cá nhân: 100% tự do sáng tạo, không gán ghép quy chuẩn lịch sử nếu tác giả viết thể loại hiện đại/viễn tưởng/ma pháp.
   - Lịch sử Dân tộc: Bắt buộc tôn trọng sự thật lịch sử nếu viết Chính sử (Hai Bà Trưng, Ngô Quyền, Lý Thường Kiệt, Trần Hưng Đạo, Lê Lợi, Quang Trung...); giữ vững phong vị và hào khí thời đại nếu viết Dã sử.
   - Bản quyền IP: Nếu tác giả nhắc đến các IP nổi tiếng (Marvel, Anime, Harry Potter...), hãy khéo léo gợi ý biến tấu thành hệ thống độc bản của riêng tác giả.

4. NHẬN DIỆN MỐC SẴN SÀNG ([READY]):
   - Khi câu chuyện đã hội tụ đủ 3 yếu tố: (1) Nhân vật chính, (2) Xung đột cốt lõi, (3) Bối cảnh thế giới; HOẶC bất cứ khi nào tác giả ra lệnh ("bắt đầu viết", "tạo truyện luôn", "chốt dàn ý", "viết thôi", "let's write"):
   - Tóm tắt sắc sảo 1 câu định vị linh hồn câu chuyện và KẾT THÚC BẰNG MÃ: [READY] ở cuối cùng.

TUYỆT ĐỐI CHỈ SỬ DỤNG TIẾNG VIỆT TỰ NHIÊN, VĂN PHONG VĂN HỌC SẮC BẢO, KHÔNG TRỘN TIẾNG ANH."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        
        response, used_model = self._chat_with_resilience(
            messages, 
            temperature=0.7, 
            max_tokens=400
        )
        return response
```

---

## 4. THIẾT KẾ KIẾN TRÚC FRONTEND RESILIENCE (R3 FRONTEND)

### 4.1. Nâng Cấp API Layer (`frontend/src/lib/api.ts`)

Bảo vệ hàm `chatInterview` không để ném ngoại lệ chưa bắt:

```typescript
  // File: frontend/src/lib/api.ts
  async chatInterview(history: Array<{role: string; content: string}>): Promise<InterviewResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/chat-interview`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ chat_history: history }),
      });
      if (!res.ok) {
        const errorText = await res.text();
        let message = `Lỗi máy chủ (${res.status})`;
        try {
          const parsed = JSON.parse(errorText);
          message = parsed.message || parsed.detail || message;
        } catch {}
        return { status: 'error', message };
      }
      return await res.json();
    } catch (err: any) {
      return { 
        status: 'error', 
        message: err?.message || 'Không thể kết nối với máy chủ AI (Lỗi mạng hoặc máy chủ ngoại tuyến)' 
      };
    }
  },
```

### 4.2. Thuật Toán Dynamic Client Fallback (Ngoại Tuyến / Mất Mạng)

Khi client mất kết nối mạng hoàn toàn hoặc server backend ngắt kết nối, thay vì hiển thị một đoạn văn mẫu tĩnh vô nghĩa, client tự động kích hoạt **Thuật toán Trích xuất Ý niệm & Sinh Câu hỏi Ngữ nghĩa (Dynamic Semantic Client Fallback)** trực tiếp trên trình duyệt.

#### Thuật toán trích xuất từ khóa trên Client (`extractNarrativeConcepts`):

```typescript
interface ExtractedConcepts {
  entities: string[];
  setting?: string;
  genre: "historical" | "scifi" | "xianxia" | "detective" | "romance" | "general";
  conflict?: string;
}

export function extractNarrativeConcepts(text: string): ExtractedConcepts {
  const lower = text.toLowerCase();
  const entities: string[] = [];

  // 1. Phân loại Thể loại & Thực thể
  let genre: ExtractedConcepts["genre"] = "general";
  let setting: string | undefined;

  // Lịch sử Việt Nam
  const histKeywords = ["thánh gióng", "trần hưng đạo", "lý thường kiệt", "ngô quyền", "lê lợi", "quang trung", "bạch đằng", "đại việt", "nhà trần", "nhà lê", "nghĩa sĩ"];
  for (const kw of histKeywords) {
    if (lower.includes(kw)) {
      genre = "historical";
      entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
    }
  }

  // Khoa học viễn tưởng / Cyberpunk
  const scifiKeywords = ["cyberpunk", "2099", "sài gòn 2099", "saigon 2099", "robot", "ai", "trí tuệ nhân tạo", "hacker", "thám tử tư", "ký ức số"];
  for (const kw of scifiKeywords) {
    if (lower.includes(kw)) {
      genre = "scifi";
      if (!setting && (kw.includes("sài gòn") || kw.includes("saigon") || kw.includes("2099"))) {
        setting = "Sài Gòn 2099";
      }
    }
  }

  // Tu chân / Kỳ ảo
  const xianxiaKeywords = ["tu chân", "tiên hiệp", "kiếm hiệp", "đan điền", "ma pháp", "linh hồn", "cấm địa", "pháp bảo", "trận pháp"];
  for (const kw of xianxiaKeywords) {
    if (lower.includes(kw)) {
      genre = "xianxia";
      entities.push(kw);
    }
  }

  // Trinh thám / Gián điệp
  const detKeywords = ["thám tử", "án mạng", "vụ án", "giết người", "điều tra", "manh mối", "hung thủ"];
  for (const kw of detKeywords) {
    if (lower.includes(kw)) {
      genre = "detective";
    }
  }

  // 2. Trích xuất các danh từ riêng viết hoa (Proper Nouns)
  const capitalizedWords = text.match(/[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+/g);
  if (capitalizedWords) {
    for (const w of capitalizedWords) {
      if (!["Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để"].includes(w) && !entities.includes(w)) {
        entities.push(w);
      }
    }
  }

  return { entities: Array.from(new Set(entities)).slice(0, 3), setting, genre };
}
```

#### Bộ sinh câu hỏi động (`generateDynamicClientFallback`):

```typescript
export function generateDynamicClientFallback(userInput: string, lang: "vi" | "en"): string {
  const concepts = extractNarrativeConcepts(userInput);
  const isVi = lang === "vi";

  const entityStr = concepts.entities.length > 0 
    ? concepts.entities.join(", ") 
    : (isVi ? "nhân vật chính" : "the protagonist");

  if (concepts.genre === "historical") {
    return isVi
      ? `NarrAI ghi nhận đề tài lịch sử hào hùng xoay quanh **${entityStr}**.\n\nĐể khắc họa chiều sâu tác phẩm:\n1. Bạn muốn khai thác theo góc nhìn **Chính sử** bám sát sử liệu, hay **Dã sử phóng tác** từ góc nhìn của một nhân chứng bình dị bên cạnh ngài?\n2. Biến cố mang tính bước ngoặt hoặc bài học bang giao/chiến lược nào sẽ là điểm nhấn kịch tính nhất trong câu chuyện?`
      : `NarrAI captured the historic premise centered on **${entityStr}**.\n\nTo deepen this narrative:\n1. Are you aiming for strict historical fidelity, or fictional narrative through a grassroots lens?\n2. What pivotal sacrifice or turning point defines their heroic journey?`;
  }

  if (concepts.genre === "scifi") {
    const place = concepts.setting || (isVi ? "thế giới tương lai" : "the futuristic metropolis");
    return isVi
      ? `Ý tưởng khoa học viễn tưởng trong bối cảnh **${place}** rất giàu tiềm năng kịch tính!\n\nĐể định hình xung đột then chốt:\n1. **${entityStr}** đang đối đầu với thế lực nào (một tập đoàn công nghệ kiểm soát ý thức, hay một trí tuệ nhân tạo mất kiểm soát)?\n2. Nhân vật chính sở hữu năng lực đặc thù nào, và cái giá phải trả để duy trì nhân tính là gì?`
      : `High-octane sci-fi premise set in **${place}**!\n\nTo lock down the conflict:\n1. Who is the primary adversary opposing **${entityStr}** (a megacorporation controlling neural memories, or rogue synthetic AI)?\n2. What cybernetic edge or moral cost drives your protagonist forward?`;
  }

  if (concepts.genre === "xianxia") {
    return isVi
      ? `Tiền đề kỳ ảo phương Đông với yếu tố **${entityStr}** mở ra một thế giới quan rộng lớn.\n\nĐể thắt chặt mạch truyện:\n1. Đâu là bí mật cổ xưa hoặc nghịch thiên tạo hóa mà nhân vật chính tình cờ nắm giữ?\n2. Mâu thuẫn giữa các tông môn hoặc thế lực hắc ám nào sẽ đẩy nhân vật vào cuộc chiến sinh tử đầu tiên?`
      : `Rich cultivation fantasy premise involving **${entityStr}**.\n\nTo sharpen the narrative arc:\n1. What ancient artifact or forbidden soul secret does the protagonist harbor?\n2. Which sect rivalry or dark calamity will trigger their first life-or-death crisis?`;
  }

  // Trường hợp tổng quát: Tự động lồng ghép từ khóa của chính người dùng
  return isVi
    ? `NarrAI đã tiếp nhận các ý niệm then chốt của bạn: **${userInput.slice(0, 60)}...**\n\nĐể biến ý tưởng này thành một câu chuyện hoàn chỉnh:\n1. Động cơ thôi thúc mạnh mẽ nhất của **${entityStr}** trong hồi mở đầu là gì?\n2. Trở ngại hoặc biến cố bất ngờ nào xuất hiện ngay chương 1 khiến kế hoạch của nhân vật bị đảo lộn hoàn toàn?`
    : `NarrAI registered your core premise: **${userInput.slice(0, 60)}...**\n\nTo structure the dramatic hook:\n1. What urgent motivation propels **${entityStr}** in the opening sequence?\n2. What unforeseen complication disrupts their life right in Chapter 1?`;
}
```

### 4.3. Giao Diện Thông Báo Trạng Thái Kết Nối & Nút "Thử Lại" (Retry)

Trong `UnifiedIntakeChat.tsx`, khi API gặp sự cố:
1. Tin nhắn phản hồi của Assistant được gắn nhãn nhận diện `is_offline_fallback: true` và `error_message?: string`.
2. Dưới bong bóng chat của Assistant hiển thị một thanh trạng thái tinh tế:
   - Biểu tượng `WifiOff` màu hổ phách/cam (amber-500).
   - Dòng trạng thái: *"Chế độ dự phòng ngoại tuyến: Đang phản hồi từ từ khóa của bạn"* hoặc *"Mất kết nối máy chủ AI"*.
   - Nút **"Thử lại" (Retry)** với icon `RotateCcw` xoay nhẹ: Khi bấm, hệ thống gọi lại `handleSend(lastUserText)` để thử lại với toàn bộ chuỗi fallback của Backend.
3. Người dùng **vẫn có thể tiếp tục trò chuyện bình thường** nếu chưa muốn thử lại, hoặc bấm nút **"Bắt đầu viết truyện ngay"** bất kỳ lúc nào vì dàn ý đã được các câu hỏi dự phòng gọt giũa!

### 4.4. Cân Bằng Bố Cục Khung Chat & Bottom Dock (Khắc Phục R2)

Hiện tại ở dòng 597 của `UnifiedIntakeChat.tsx`:
```tsx
<div className="fixed bottom-0 left-0 right-0 sm:left-64 p-3 sm:p-5 ...">
```
Class `fixed sm:left-64` bị cứng nhắc vì neo giữ theo tọa độ tuyệt đối của toàn màn hình thay vì container cha, gây ra hiện tượng lệch pha khi Sidebar thu gọn, hoặc làm mất cân đối trục dọc so với khung chat.

**Giải pháp căn chỉnh:**
- Chuyển `UnifiedIntakeChat` thành flex column trọn vẹn:
  ```tsx
  <div className="flex flex-col h-full w-full bg-slate-50/40 dark:bg-slate-950/40 relative">
    <header className="shrink-0 ...">...</header>
    
    {/* Khu vực cuộn tin nhắn */}
    <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8">
      <div className="max-w-3xl mx-auto w-full ...">...</div>
    </div>
    
    {/* Bottom Input Dock: Sticky hoặc Flex Item cố định ở đáy, căn giữa 100% */}
    <div className="shrink-0 p-3 sm:p-5 w-full bg-gradient-to-t from-slate-50/95 via-slate-50/80 to-transparent dark:from-slate-950/95 z-20">
      <div className="max-w-3xl mx-auto w-full">
        {/* Input Capsule & Controls */}
      </div>
    </div>
  </div>
  ```
- Việc này giúp:
  1. Bottom Input Bar tự động căn giữa hoàn hảo theo trục dọc với các bong bóng chat phía trên (`max-w-3xl mx-auto`).
  2. Triệt tiêu hoàn toàn sự lệch pha `sm:left-64`.
  3. Avatar AI và Avatar User đều có kích thước chuẩn `w-8 h-8 rounded-full`, padding đối xứng `px-4 py-3.5`, khoảng cách `gap-3.5` đồng nhất.

---

## 5. BẢNG SO SÁNH TRẢI NGHIỆM TRƯỚC VÀ SAU CẢI TẠO

| Kịch bản | Trải nghiệm Cũ (Hiện tại) | Trải nghiệm Mới (Sau cải tạo) |
|---|---|---|
| **Người dùng chat: "Thánh Gióng"** | AI lặp câu cứng nhắc: *"Ý tưởng của bạn rất cuốn hút! Hãy chia sẻ thêm về nhân vật chính, xung đột cốt lõi hoặc bối cảnh không gian nhé."* | AI phản chiếu sâu: *"Hình tượng Phù Đổng Thiên Vương đánh giặc Ân là một thiên hùng ca vĩ đại. Bạn muốn hướng tác phẩm theo Chính sử hào hùng hay Dã sử từ góc nhìn một người dân? Chi tiết nào bạn muốn đào sâu nhất (sự chuyển hóa từ đứa trẻ ba tuổi hay thanh thiết mã rèn từ trăm lò lửa)?"* |
| **Người dùng chat: "Cyberpunk Sài Gòn 2099"** | Lại lặp đúng câu văn mẫu trên. | AI phản chiếu: *"Một Sài Gòn ánh đèn neon, kênh rạch số hóa và các tập đoàn công nghệ thao túng ký ức là mảnh đất màu mỡ cho xung đột. Nhân vật chính là một hacker ngầm hay một thám tử cơ khí săn lùng danh tính đã mất? Bí mật đen tối nhất dưới lòng thành phố là gì?"* |
| **Mô hình chính qwen/qwen3.8-27b bị rate limit / quá tải** | Backend crash văng lỗi 429 -> Frontend nhảy vào catch -> Hiện văn mẫu lặp lại. | Backend tự động chuyển tiếp ngầm sang `llama-3.3-70b-versatile` rồi `llama-3.1-8b-instant`. Người dùng nhận phản hồi thông suốt trong < 2 giây! |
| **Khóa GROQ_API_KEY_BIBLE hết token** | Toàn bộ chức năng intake tê liệt. | Tự động chuyển sang `GROQ_API_KEY` rồi `GROQ_API_KEY_COPILOT`. Hệ thống tiếp tục vận hành 100%. |
| **Mất kết nối mạng / Server offline hoàn toàn** | Hiện thông báo lửng lơ *"Đang kết nối lại..."*, không có nút Retry. | Kích hoạt Dynamic Client Fallback trích xuất đúng tên nhân vật/bối cảnh người dùng vừa nhập, đặt câu hỏi gợi mở kèm nhãn `WifiOff` và nút **"Thử lại"**. |

---

## 6. KẾ HOẠCH KIỂM THỬ & BẢO ĐẢM KHÔNG REGRESSION (VERIFICATION STRATEGY)

1. **Bảo tồn Unit Tests Hiện Có (182+ tests)**:
   - `test_light_novel_engine.py` vá `refiner.llm.chat`: Đảm bảo `self.llm` được duy trì để test tiếp tục PASS 100%.
   - `test_adversarial_m1.py`: Kiểm thử import và khởi tạo `QARefiner` tiếp tục PASS 100%.
2. **Bộ Test Suite Mới Cho R3 Backend**:
   - `test_qa_refiner_multi_model_fallback`: Giả lập lỗi ở `qwen/qwen3.8-27b` -> Verify tự động gọi `llama-3.3-70b-versatile`.
   - `test_qa_refiner_multi_key_fallback`: Giả lập lỗi 429 ở `GROQ_API_KEY_BIBLE` -> Verify tự động chuyển sang `GROQ_API_KEY`.
   - `test_qa_refiner_concept_mirroring_prompt`: Kiểm tra System Prompt mới có chứa các quy tắc Concept Mirroring và 1-2 Deep Probes.
   - `test_chat_interview_endpoint_resilience`: TestClient gọi `/api/chat-interview` với các tình huống lỗi và thành công.
3. **Frontend Build Check**:
   - `npm run build` trong thư mục `frontend` đạt 0 lỗi TypeScript.
