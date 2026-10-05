# Handoff Report — challenger_r7_ai

**Agent**: `challenger_r7_ai`  
**Role**: Empirical Challenger (critic, specialist)  
**Date**: 2026-10-05T06:31:00Z  
**Target Milestone**: R7 AI Resilience, Layout Symmetry, and Question Generation  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

1. **`backend/agents/qa_refiner.py` Line 209**:
   ```python
   scifi_keywords = ["cyberpunk", "2099", "sài gòn 2099", "robot", "ai", "trí tuệ nhân tạo", "hacker", "thám tử tư", "ký ức", "hậu tận thế"]
   matched_scifi = [k for k in scifi_keywords if k in lower]
   ```
   `"ai"` is a 2-character raw substring in `scifi_keywords`.
   `"thám tử tư"` is included in `scifi_keywords` and evaluated before `thriller_keywords` (line 235).
   `"ký ức"` is included in `scifi_keywords` without qualification.

2. **`frontend/src/components/setup/UnifiedIntakeChat.tsx` Lines 186-198**:
   ```typescript
   const scifiKeywords = ["cyberpunk", "2099", "sài gòn 2099", "saigon 2099", "robot", "ai", "trí tuệ nhân tạo", "hacker", "thám tử tư", "ký ức số", "viễn tưởng", "vũ trụ", "người máy"];
   for (const kw of scifiKeywords) {
     if (lower.includes(kw)) {
       if (genre === "general") genre = "scifi";
       ...
     }
   }
   ```
   `lower.includes("ai")` performs a raw substring match against `lower`.

3. **`backend/agents/qa_refiner.py` Lines 247-250**:
   ```python
   caps = re.findall(r"\b[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+", latest_input)
   filtered_caps = [c for c in caps if c not in ("Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu")]
   anchor = f"nhân vật {filtered_caps[0]}" if filtered_caps else "cốt truyện của bạn"
   ```
   Only 8 specific stop-words are filtered. Sentence-initial verbs and introductory nouns (`"Chuyện"`, `"Kể"`, `"Viết"`, `"Vào"`, `"Câu"`) pass through as `filtered_caps[0]`.

4. **`backend/agents/qa_refiner.py` Lines 269-270**:
   ```python
   messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
   messages.extend(chat_history)
   ```
   Unsanitized `chat_history` containing frontend metadata flags (`is_offline_fallback`, `error_message`, `failed_prompt`, `is_ready`) is forwarded directly into `GroqClient.chat()`.

---

## 2. Logic Chain

1. **Premise (Observation 1 & 2)**: Both backend and frontend fallback generators evaluate `k in lower` / `lower.includes(kw)` where `kw == "ai"`.
2. **Linguistic Reality**: In the Vietnamese language, `"ai"` is a high-frequency diphthong present in basic numerals (*"hai"*), common verbs (*"phải"*, *"lại"*, *"giải"*, *"hại"*), prepositions (*"tại"*), nouns (*"cái"*, *"gái"*, *"trai"*, *"bài"*, *"tai"*, *"mai"*), loanwords (*"isekai"*), and pronouns (*"ai"*).
3. **Inference 1**: Any input containing any word with `"ai"` triggers `matched_scifi` / `genre = "scifi"`.
4. **Ordering Effect**: Sci-Fi is evaluated before Xianxia/Fantasy and Detective/Thriller.
5. **Concrete Failure 1**: When the user tests `"Isekai ẩm thực"` (Culinary Isekai), `"isekai"` contains `"ai"`, routing it into Sci-Fi. The output generates questions about rogue AI, memory wipes, and cyberpunk neon underworlds rather than culinary or fantasy tropes.
6. **Concrete Failure 2**: When the user clicks Starter Prompt #4 (*"Hai tâm hồn cô đơn..."*), `"Hai"` contains `"ai"`, routing this emotional urban slice-of-life story into sci-fi neon corporation dilemmas.
7. **Concrete Failure 3 (Observation 1)**: `"thám tử tư"` (private detective) in `scifi_keywords` hijacks classic detective noir into sci-fi cyberpunk.
8. **Concrete Failure 4 (Observation 3)**: Sentences beginning with `"Kể về..."`, `"Viết về..."`, or `"Chuyện về..."` treat the sentence-initial verb as a character name, yielding `"nhân vật Kể"`, `"nhân vật Viết"`, or `"nhân vật Chuyện"`.
9. **Conclusion**: While live LLM generation and model/key fallback matrix are structurally sound, the deterministic fallback logic contains systemic false-positive bugs that undermine the core user experience whenever network or API disruptions occur.

---

## 3. Caveats

- Live AI calls to Groq endpoints (`qwen/qwen3.8-27b`, `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) with active API keys operate via LLM semantic comprehension and do not execute this fallback regex. The bug manifests specifically when:
  1. Primary and secondary LLM endpoints are exhausted or rate-limited and heuristic fallback is activated.
  2. The client is disconnected from the backend and triggers `generateDynamicClientFallback`.
- The live system prompt in `qa_refiner.py` is exemplary, compliant with Concept Mirroring, anti-boilerplate rules, and historical integrity guardrails.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

Actionable work items for `worker_r7_backend` and `worker_r7_frontend`:

1. **For `backend/agents/qa_refiner.py` (`worker_r7_backend`)**:
   - In `generate_fallback_question`:
     - Remove `"ai"` from `scifi_keywords` (keep `"trí tuệ nhân tạo"`).
     - Remove `"thám tử tư"` from `scifi_keywords` (preserve it in `thriller_keywords`).
     - Change generic `"ký ức"` to `"ký ức số"`.
     - Expand `filtered_caps` stopwords to include: `"Chuyện"`, `"Câu"`, `"Viết"`, `"Kể"`, `"Vào"`, `"Đây"`, `"Đó"`, `"Về"`, `"Tác"`, `"Cuộc"`, `"Ngày"`, `"Ở"`.
   - In `chat_interview`:
     - Sanitize `chat_history` by retaining only `role` and `content` before appending to `messages`.

2. **For `frontend/src/components/setup/UnifiedIntakeChat.tsx` (`worker_r7_frontend`)**:
   - In `extractNarrativeConcepts`:
     - Remove `"ai"` from `scifiKeywords`.
     - Remove `"thám tử tư"` from `scifiKeywords`.
     - Expand stopwords in `capitalizedWords` filter to include `"Chuyện"`, `"Câu"`, `"Viết"`, `"Kể"`, `"Vào"`, `"Đây"`, `"Đó"`, `"Về"`, `"Cuộc"`.

---

## 5. Verification Method

To verify the fix independently:
1. Run test cases on `generate_fallback_question` in Python:
   - `refiner.generate_fallback_question([{"role": "user", "content": "Isekai ẩm thực"}])` -> Must NOT contain "neon" or "Sài Gòn 2099" or "thế giới tương lai".
   - `refiner.generate_fallback_question([{"role": "user", "content": "Hai tâm hồn cô đơn tại Hà Nội"}])` -> Must NOT trigger Sci-Fi.
   - `refiner.generate_fallback_question([{"role": "user", "content": "Kể về một người thợ rèn"}])` -> Must NOT produce `"nhân vật Kể"`.
   - `refiner.generate_fallback_question([{"role": "user", "content": "Thám tử tư điều tra vụ án"}])` -> Must trigger Detective, NOT Sci-Fi.
2. Run test cases on `extractNarrativeConcepts` in TypeScript:
   - `extractNarrativeConcepts("Hai tâm hồn cô đơn").genre` -> Expected `"general"`, not `"scifi"`.
   - `extractNarrativeConcepts("Isekai ẩm thực").genre` -> Expected `"general"`, not `"scifi"`.
   - `extractNarrativeConcepts("Thám tử tư điều tra").genre` -> Expected `"detective"`, not `"scifi"`.
3. Run test suites:
   - `python backend/tests/run_all_tests.py` -> 198+ tests 100% PASS.
   - `npm run build` -> Clean compile.
