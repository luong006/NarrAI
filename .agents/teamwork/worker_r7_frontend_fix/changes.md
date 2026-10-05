# Changes Log — worker_r7_frontend_fix

**Agent**: `worker_r7_frontend_fix`  
**Timestamp**: 2026-10-05T06:40:00Z  
**Target File**: `frontend/src/components/setup/UnifiedIntakeChat.tsx`  

---

## 1. Summary of Changes

Remediated heuristic false-positive genre classification and stop-word entity extraction bugs identified by `challenger_r7_ai` in `extractNarrativeConcepts`:

1. **Removed `"ai"` from `scifiKeywords`**:
   - Kept `"trí tuệ nhân tạo"`.
   - Prevented Vietnamese diphthongs containing "ai" (e.g., "hai" in Starter Prompt #4 *"Hai tâm hồn cô đơn..."*, and loanwords like *"Isekai"*) from triggering Sci-Fi classification.
2. **Removed `"thám tử tư"` from `scifiKeywords` & Anchored in `detKeywords`**:
   - `"thám tử tư"` was previously evaluated in `scifiKeywords` before detective keywords, causing detective stories to be misclassified as cyberpunk sci-fi.
   - Removed `"thám tử tư"` from `scifiKeywords` and line 193 entity check (`kw === "hacker" || kw === "robot"`).
   - Added `"thám tử tư"` to `detKeywords` with de-duplication so detective stories accurately classify as `detective` with entity `"Thám tử tư"`.
3. **Expanded Stop-Word Filtering in `capitalizedWords` Character Extraction**:
   - Added sentence-initial verbs, conjunctions, and introductory nouns:
     `"Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu", "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về", "Cuộc", "Và", "Nhưng", "Với", "Có", "Là", "Tác", "Ngày", "Ở"`.
   - Prevents sentences beginning with *"Kể về..."*, *"Viết về..."*, or *"Chuyện..."* from extracting verbs/nouns as character names.
4. **Exported Interface and Functions**:
   - Exported `ExtractedConcepts`, `extractNarrativeConcepts`, and `generateDynamicClientFallback` for composability and unit test verification.

---

## 2. Exact Diff in `frontend/src/components/setup/UnifiedIntakeChat.tsx`

```diff
-interface ExtractedConcepts {
+export interface ExtractedConcepts {
   entities: string[];
   setting?: string;
   genre: "historical" | "scifi" | "xianxia" | "detective" | "general";
 }
 
-function extractNarrativeConcepts(text: string): ExtractedConcepts {
+export function extractNarrativeConcepts(text: string): ExtractedConcepts {
   const lower = text.toLowerCase();
   const entities: string[] = [];
   let genre: ExtractedConcepts["genre"] = "general";
   let setting: string | undefined;
 
   // Lịch sử Việt Nam
...
   // Khoa học viễn tưởng / Cyberpunk
-  const scifiKeywords = ["cyberpunk", "2099", "sài gòn 2099", "saigon 2099", "robot", "ai", "trí tuệ nhân tạo", "hacker", "thám tử tư", "ký ức số", "viễn tưởng", "vũ trụ", "người máy"];
+  const scifiKeywords = ["cyberpunk", "2099", "sài gòn 2099", "saigon 2099", "robot", "trí tuệ nhân tạo", "hacker", "ký ức số", "viễn tưởng", "vũ trụ", "người máy"];
   for (const kw of scifiKeywords) {
     if (lower.includes(kw)) {
       if (genre === "general") genre = "scifi";
       if (!setting && (kw.includes("sài gòn") || kw.includes("saigon") || kw.includes("2099"))) {
         setting = "Sài Gòn 2099";
       }
-      if (kw === "hacker" || kw === "thám tử tư" || kw === "robot") {
+      if (kw === "hacker" || kw === "robot") {
         entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
       }
     }
   }
 
   // Tu chân / Tiên hiệp / Kỳ ảo
...
   // Trinh thám / Gián điệp
-  const detKeywords = ["thám tử", "án mạng", "vụ án", "giết người", "điều tra", "manh mối", "hung thủ", "bắt cóc", "mật vụ"];
+  const detKeywords = ["thám tử tư", "thám tử", "án mạng", "vụ án", "giết người", "điều tra", "manh mối", "hung thủ", "bắt cóc", "mật vụ"];
   for (const kw of detKeywords) {
     if (lower.includes(kw)) {
       if (genre === "general") genre = "detective";
-      entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
+      const cap = kw.charAt(0).toUpperCase() + kw.slice(1);
+      if (!entities.some(e => e.toLowerCase() === kw || (kw === "thám tử" && e.toLowerCase().includes("thám tử tư")))) {
+        entities.push(cap);
+      }
     }
   }
 
   // Trích xuất các danh từ riêng viết hoa tiếng Việt
   const capitalizedWords = text.match(/[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+/g);
   if (capitalizedWords) {
+    const stopWords = [
+      "Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu",
+      "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về", "Cuộc",
+      "Và", "Nhưng", "Với", "Có", "Là", "Tác", "Ngày", "Ở"
+    ];
     for (const w of capitalizedWords) {
-      if (!["Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Và", "Nhưng", "Với", "Nếu", "Có", "Là"].includes(w) && !entities.includes(w)) {
+      if (!stopWords.includes(w) && !entities.includes(w)) {
         entities.push(w);
       }
     }
   }
```
