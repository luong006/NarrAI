# Empirical Verification Report: Frontend 100% Bilingual i18n & Toast System

**Challenger**: challenger_r3_m1_2  
**Target Milestone**: Milestone 1 (R1 100% i18n & Toast System)  
**Date**: 2026-09-22  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

### 1.1. Scan for Leftover `alert(` Calls (`frontend/src/`)
- Tool executed: `grep_search` across `frontend/src` for regex `\balert\s*\(`.
- **Result in `page.tsx` and setup components (`Phase1Idea`, `Phase2Interview`, `Phase3Controls`)**:
  * 0 browser `alert(` calls found.
  * 100% of browser alerts in `page.tsx` and setup components have been successfully replaced with `toast.error()`, `toast.warning()`, `toast.info()`, and `toast.success()`.
- **Result in wider `frontend/src/`**:
  * **2 leftover browser `alert(` calls found in `frontend/src/components/modals/HistoryModal.tsx`**:
    - Line 54:
      ```typescript
      alert("Không thể tải chi tiết truyện.");
      ```
    - Line 57:
      ```typescript
      alert("Lỗi tải truyện: " + e.message);
      ```

---

### 1.2. Dictionary Completeness & Symmetry (`frontend/src/lib/i18n.ts`)
- File inspected: `frontend/src/lib/i18n.ts` (lines 4–177 for `vi`, lines 178–352 for `en`).
- **Result**:
  * `translations.vi` contains exactly **95 keys**.
  * `translations.en` contains exactly **95 keys**.
  * 100% key symmetry verified. Every key in `translations.vi` is defined in `translations.en` in identical order with 0 missing keys and 0 extra keys.

---

### 1.3. Audit of Hardcoded Strings Across Target Components

1. **`ThemeToggle.tsx` (`frontend/src/components/layout/ThemeToggle.tsx`)**:
   - **PASS**:
     - `tooltip = theme === "dark" ? t.theme_light : t.theme_dark`
     - `aria-label={t.theme_toggle_aria}`
     - 0 hardcoded strings.

2. **`Sidebar.tsx` (`frontend/src/components/layout/Sidebar.tsx`)**:
   - **PASS**:
     - Uses `t.not_logged_in`, `t.logout`, `t.new_story`, `t.story_history`.
     - Passes `lang={lang}` to `ThemeToggle`.
     - 0 hardcoded strings.

3. **`LandingView.tsx` (`frontend/src/components/landing/LandingView.tsx`)**:
   - **PASS**:
     - Uses `t.pro_badge`, `t.login`, `t.hero_badge`, `t.hero_title`, `t.hero_sub`, `t.hero_cta`, `t.features_section_title`, `t.feat1_*`, `t.feat2_*`, `t.feat3_*`, `t.footer_copyright`.
     - Passes `lang={lang}` to `ThemeToggle`.
     - 0 hardcoded strings.

4. **`AICopilotPanel.tsx` (`frontend/src/components/editor/AICopilotPanel.tsx`)**:
   - **PASS**:
     - Quick prompts on lines 62–83 dynamically branch text by `lang === "vi" ? ... : ...` and use `t.quick_cmd_*`.
     - All headers, placeholders, buttons, undo tooltips use `t.*`.
     - 0 hardcoded strings.

5. **`error.tsx` (`frontend/src/app/error.tsx`)**:
   - **PASS**:
     - Reads persisted language from `storage.getLanguage()`.
     - Localizes `t.error_boundary_title`, `t.error_boundary_desc`, `t.error_boundary_retry`, `t.error_boundary_home`.
     - 0 hardcoded strings.

6. **Setup Phases**:
   - **`Phase2Interview.tsx`**: **PASS**. Uses `t.step2_title`, `t.step2_sub`, `t.ai_thinking`, `t.chat_placeholder`, `t.skip_chat_btn`.
   - **`Phase3Controls.tsx`**: **PASS**. Uses `t.step3_title`, `t.step3_sub`, `t.story_length`, `t.creativity`, `t.pacing`, `t.val_*`, `t.start_writing_btn`.
   - **`Phase1Idea.tsx`**: **DEFECT DETECTED**:
     - In `Phase1Idea.tsx` lines 157–163:
       ```typescript
       useEffect(() => {
         api.getTrendingTopics().then((res) => {
           if (res.status === "success" && res.topics && res.topics.length > 0) {
             setTrendingTopics(res.topics);
           }
         });
       }, []);
       ```
     - In `backend/data/trending_themes.json`:
       All 7 trending topic objects contain only Vietnamese attributes: `title`, `genre`, `description`, `prompt_snippet`. None of them contain `title_en`, `genre_en`, `description_en`, or `prompt_snippet_en`.
     - In `Phase1Idea.tsx` lines 302–304:
       ```typescript
       const title = lang === "vi" ? theme.title : theme.title_en || theme.title;
       const genre = lang === "vi" ? theme.genre : theme.genre_en || theme.genre;
       const description = lang === "vi" ? theme.description : theme.description_en || theme.description;
       ```
     - **Observed Behavior**: Upon mounting, `Phase1Idea` fetches `trending_themes.json` from the backend, overwriting `FALLBACK_THEMES`. When rendered in English mode (`lang === "en"`), `theme.title_en` is undefined, causing the UI to display 100% Vietnamese cards ("Chữa lành & Bỏ phố về quê", "Trùng sinh báo thù & Nữ cường", etc.) in English mode.

7. **`AuthModal.tsx` (`frontend/src/components/modals/AuthModal.tsx`)**:
   - **DEFECT DETECTED**:
     - Line 173:
       ```typescript
       setError(rawDetail || (isLogin ? "Đăng nhập thất bại" : "Đăng ký thất bại"));
       ```
       If `rawDetail` is empty, fallback displays hardcoded Vietnamese string `"Đăng nhập thất bại"` or `"Đăng ký thất bại"` even when `lang === "en"`.

8. **Additional Component Finding (`ComicViewer.tsx`)**:
   - `frontend/src/components/comic/ComicViewer.tsx`:
     - Line 44:
       ```typescript
       <span className="text-red-500 text-xs font-semibold mb-2">Chưa tải được khung tranh #{panel.panel_index}</span>
       ```
     - Line 50:
       ```typescript
       <RefreshCw className="w-3 h-3" />
       <span>Thử lại</span>
       ```
       These are hardcoded Vietnamese strings, despite `t.panel_load_error` and `t.retry_btn` existing in `i18n.ts`.

---

## 2. Logic Chain

1. **Premise 1 (Toast Alert Replacement)**: The user request requires:
   > "Scan `frontend/src/` for any leftover `alert(` calls. Verify that 100% of browser alerts in `page.tsx` and setup components have been replaced with toast calls."
   - *Observation*: While `page.tsx` and `setup/` components have 0 alert calls, `HistoryModal.tsx` (lines 54 and 57) still executes raw browser `alert("Không thể tải chi tiết truyện.")` and `alert("Lỗi tải truyện: " + e.message)`.
   - *Deduction*: The replacement of browser alerts with the toast system is incomplete within the frontend codebase.

2. **Premise 2 (Dictionary Symmetry)**:
   - *Observation*: Both `translations.vi` and `translations.en` possess exactly 95 keys with identical names and order.
   - *Deduction*: The translation dictionary satisfies 100% completeness and symmetry.

3. **Premise 3 (Hardcoded String Elimination in English and Vietnamese modes)**:
   - *Observation A*: In `Phase1Idea.tsx`, `api.getTrendingTopics()` fetches topics from `backend/data/trending_themes.json` which completely lack English fields. This silently overwrites the bilingual `FALLBACK_THEMES` and leaks raw Vietnamese topics when the user selects English mode.
   - *Observation B*: In `AuthModal.tsx` line 173, fallback error messages `"Đăng nhập thất bại"` and `"Đăng ký thất bại"` are hardcoded Vietnamese strings.
   - *Observation C*: In `ComicViewer.tsx` lines 44 and 50, error text and retry buttons are hardcoded Vietnamese strings.
   - *Deduction*: The requirement "no hardcoded Vietnamese strings when rendered in English mode or hardcoded English in Vietnamese mode" is violated in `Phase1Idea.tsx`, `AuthModal.tsx`, and `ComicViewer.tsx`.

---

## 3. Caveats

1. **Non-Interactive Shell Environment**: In this execution environment, interactive shell commands timed out awaiting manual approval. All verification was conducted through direct AST, regex, and file analysis tools (`view_file`, `grep_search`, `find_by_name`).
2. **Review-Only Constraint**: In accordance with the Review-Only constraint for challengers, no code changes were committed directly by the challenger. Concrete, line-level remediation instructions are provided below for the worker.

---

## 4. Conclusion & Required Changes

**Verdict**: **REQUEST_CHANGES**

To achieve full approval, the worker must resolve the following 4 concrete defects:

### Action Items for Worker:

1. **Replace leftover `alert(` calls in `frontend/src/components/modals/HistoryModal.tsx`**:
   - Import `useToast` from `@/lib/toast`.
   - Replace lines 54 and 57:
     ```typescript
     // Line 54
     toast.error(lang === "vi" ? "Không thể tải chi tiết truyện." : "Failed to load story details.");
     // Line 57
     toast.error((lang === "vi" ? "Lỗi tải truyện: " : "Failed to load story: ") + e.message);
     ```
   - Also localize line 40:
     ```typescript
     setError(e.message || (lang === "vi" ? "Lỗi tải lịch sử truyện." : "Failed to load story history."));
     ```

2. **Fix Vietnamese leakage in `Phase1Idea.tsx` when rendered in English mode**:
   - In `Phase1Idea.tsx` lines 158–163: when fetching `res.topics`, merge with `FALLBACK_THEMES` by `id` so that `title_en`, `genre_en`, `description_en`, and `prompt_snippet_en` are preserved:
     ```typescript
     api.getTrendingTopics().then((res) => {
       if (res.status === "success" && res.topics && res.topics.length > 0) {
         setTrendingTopics(
           res.topics.map((t: LocalizedTopic) => {
             const fb = FALLBACK_THEMES.find((f) => f.id === t.id);
             return fb ? { ...t, title_en: fb.title_en, genre_en: fb.genre_en, description_en: fb.description_en, prompt_snippet_en: fb.prompt_snippet_en } : t;
           })
         );
       }
     });
     ```

3. **Localize fallback error strings in `AuthModal.tsx`**:
   - On line 173 of `frontend/src/components/modals/AuthModal.tsx`:
     ```typescript
     setError(
       rawDetail ||
         (isLogin
           ? (lang === "vi" ? "Đăng nhập thất bại" : "Login failed")
           : (lang === "vi" ? "Đăng ký thất bại" : "Registration failed"))
     );
     ```

4. **Eliminate hardcoded Vietnamese strings in `ComicViewer.tsx`**:
   - In `frontend/src/components/comic/ComicViewer.tsx`:
     - Line 44: Replace `"Chưa tải được khung tranh #{panel.panel_index}"` with `<span>{t.panel_load_error} #{panel.panel_index}</span>`
     - Line 50: Replace `"Thử lại"` with `<span>{t.retry_btn}</span>`

---

## 5. Verification Method

1. **Verify zero `alert(` calls in `frontend/src/`**:
   Run grep across `frontend/src`:
   ```bash
   grep -rn "alert(" frontend/src/
   ```
   *Pass criterion*: 0 matches across the entire `frontend/src` directory.

2. **Verify Dictionary Symmetry**:
   Compare keys of `translations.vi` and `translations.en` in `frontend/src/lib/i18n.ts`.
   *Pass criterion*: Exact 1:1 key match (95 keys each).

3. **Verify English Mode Rendering in Setup & Modals**:
   - Switch language to `ENG`.
   - Inspect `Phase1Idea`: all 5 trending theme cards must display English titles ("Healing & Rural Escape", "Rebirth Revenge & Powerful Female Lead", etc.).
   - Inspect `ComicViewer`: panel load error and retry button must display "Failed to load manga panel" and "Retry".
   - Inspect `HistoryModal`: no browser popup alerts appear upon story fetch errors.
