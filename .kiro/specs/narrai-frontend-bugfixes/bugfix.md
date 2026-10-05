# Bugfix Requirements Document — NarrAI Frontend (7 Bugs)

## Introduction

Tài liệu này mô tả các yêu cầu sửa lỗi cho 7 bug/feature tập trung ở frontend của dự án NarrAI (Next.js 14 + TypeScript + Tailwind). Các bug ảnh hưởng đến: trải nghiệm nhập liệu chat, luồng tạo truyện chữ, luồng tạo truyện tranh, chức năng copilot AI, bố cục giao diện, bộ nhớ đệm comic, và tính năng tìm kiếm mạng xã hội.

---

## Bug Analysis

---

### BUG 1 — Mất focus & không gõ liên tiếp sau khi Enter trong UnifiedIntakeChat

#### Current Behavior (Defect)

1.1 WHEN người dùng gửi tin nhắn trong `UnifiedIntakeChat` (nhấn Enter hoặc nút gửi) THEN hệ thống set `loading=true` → textarea bị `disabled` → trình duyệt trả focus về `document.body` → khi `loading=false`, focus không được restore, khiến người dùng phải click vào textarea thủ công trước khi gõ tiếp.

1.2 WHEN thuộc tính `select-none` được áp dụng trên container bọc ngoài textarea THEN hệ thống ngăn chặn interaction (selection/focus) trên cả textarea input bên trong.

#### Expected Behavior (Correct)

2.1 WHEN quá trình gửi tin nhắn hoàn tất (khối `finally` của `handleSend`) THEN hệ thống SHALL tự động gọi `textareaRef.current?.focus()` để restore focus về textarea.

2.2 WHEN class `select-none` được áp dụng trên layout THEN hệ thống SHALL chỉ áp dụng `select-none` cho vùng chat messages, không bao gồm phần tử textarea input.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN `loading=true` THEN hệ thống SHALL CONTINUE TO disable textarea để ngăn gửi trùng lặp.

3.2 WHEN người dùng gõ và gửi tin nhắn bình thường THEN hệ thống SHALL CONTINUE TO xử lý và hiển thị tin nhắn đúng như trước.

---

### BUG 2 — Lỗi API tạo truyện chữ (streamStory endpoint)

#### Current Behavior (Defect)

2.1 WHEN `handleIntakeStartWriting` được gọi với `length === "long"` THEN hệ thống có thể gọi sai URL endpoint hoặc thiếu prefix `/api/`, dẫn đến 404.

2.2 WHEN payload gửi đến `init-story` hoặc `generate-story` thiếu field bắt buộc (`refined_prompt`, `story_length`) THEN hệ thống nhận lỗi từ backend mà không thông báo gì cho người dùng (silent fail).

2.3 WHEN streaming thất bại (network error, timeout, hoặc backend error) THEN hệ thống không hiển thị thông báo lỗi rõ ràng cho người dùng.

#### Expected Behavior (Correct)

2.1 WHEN `length === "long"` THEN hệ thống SHALL gọi đúng endpoint `/api/init-story` với payload có đầy đủ `refined_prompt` và `story_length`.

2.2 WHEN `length !== "long"` THEN hệ thống SHALL gọi đúng endpoint `/api/generate-story` với payload có đầy đủ `refined_prompt` và `story_length`.

2.3 WHEN streaming thất bại vì bất kỳ lý do gì THEN hệ thống SHALL hiển thị toast lỗi rõ ràng (ví dụ: "Tạo truyện thất bại, vui lòng thử lại.") thay vì im lặng.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN streaming thành công THEN hệ thống SHALL CONTINUE TO hiển thị nội dung truyện stream theo từng chunk.

3.2 WHEN `length` hợp lệ và payload đầy đủ THEN hệ thống SHALL CONTINUE TO gọi đúng endpoint tương ứng.

---

### BUG 3 — Lỗi tạo truyện tranh (Comic generate)

#### Current Behavior (Defect)

3.1 WHEN người dùng bấm "Chuyển thể thành Manga" nhưng `storyContent` rỗng THEN hệ thống vẫn gọi `/api/comic/generate` với `story_text` rỗng, dẫn đến lỗi backend hoặc kết quả không hợp lệ.

3.2 WHEN `storyId` chưa được khởi tạo (null/undefined) THEN hệ thống truyền giá trị không hợp lệ vào field `story_id` của request, thay vì truyền đúng `null` hoặc bỏ qua.

#### Expected Behavior (Correct)

3.1 WHEN người dùng bấm nút generate comic nhưng `storyContent` rỗng THEN hệ thống SHALL hiển thị thông báo yêu cầu "Vui lòng viết truyện trước khi chuyển thể thành truyện tranh." và không gọi API.

3.2 WHEN `storyId` là null/undefined THEN hệ thống SHALL truyền `story_id: null` vào request (backend xử lý được) và `story_text` luôn phải có giá trị hợp lệ.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN `storyContent` hợp lệ và `storyId` có giá trị THEN hệ thống SHALL CONTINUE TO gọi `/api/comic/generate` với đầy đủ `story_id` và `story_text`.

3.2 WHEN tạo comic thành công THEN hệ thống SHALL CONTINUE TO hiển thị panels comic đúng như trước.

---

### BUG 4 — Nội dung copilot không cập nhật sau khi AI trả về `edit_story_direct`

#### Current Behavior (Defect)

4.1 WHEN `api.copilotEvent()` trả về `data.action === "edit_story_direct"` với `data.action_params.updated_story_content` THEN hệ thống không gọi `setStoryContent()` hoặc `unwrapStoryProseFrontend()`, khiến nội dung truyện trong editor không thay đổi.

4.2 WHEN copilot trả về nội dung đã chỉnh sửa THEN hệ thống không set `proposedText` từ `action_params.updated_story_content`, khiến `AICopilotPanel` không hiển thị preview để user review trước khi accept.

#### Expected Behavior (Correct)

4.1 WHEN `data.action === "edit_story_direct"` THEN hệ thống SHALL lấy `data.action_params?.updated_story_content`, truyền qua `unwrapStoryProseFrontend()`, rồi gọi `setStoryContent()` với kết quả.

4.2 WHEN `data.action === "edit_story_direct"` THEN hệ thống SHALL set `proposedText` bằng `data.action_params?.updated_story_content` để `AICopilotPanel` hiển thị preview cho người dùng xem xét trước khi chấp nhận.

#### Unchanged Behavior (Regression Prevention)

4.1 WHEN copilot trả về action khác `edit_story_direct` THEN hệ thống SHALL CONTINUE TO xử lý các action đó theo luồng hiện tại.

4.2 WHEN người dùng accept hoặc reject proposed text THEN hệ thống SHALL CONTINUE TO áp dụng hoặc hủy thay đổi đúng như thiết kế.

---

### BUG 5 — ModelSelectorMorphicon chiếm quá nhiều không gian trong UI

#### Current Behavior (Defect)

5.1 WHEN `AICopilotPanel` render phần "Cấp độ mô hình AI" THEN hệ thống render `ModelSelectorMorphicon` full-width với label riêng biệt, chiếm ~60px chiều cao không cần thiết.

5.2 WHEN `UnifiedIntakeChat` render controls bar THEN hệ thống hiển thị label "Mô hình:" và `ModelSelectorMorphicon` theo cách chiếm nhiều không gian.

#### Expected Behavior (Correct)

5.1 WHEN `AICopilotPanel` render phần chọn model THEN hệ thống SHALL thay thế bằng một dropdown `<select>` nhỏ gọn hoặc row 3 nút icon nhỏ, không có label riêng "Cấp độ mô hình AI", chỉ dùng tooltip để mô tả.

5.2 WHEN `UnifiedIntakeChat` render controls bar THEN hệ thống SHALL giữ selector model nhưng hiển thị compact hơn, phù hợp với không gian hạn chế của thanh controls.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN người dùng chọn model THEN hệ thống SHALL CONTINUE TO cập nhật model được sử dụng cho các request AI tiếp theo.

3.2 WHEN giao diện song ngữ được chuyển (Việt/Anh qua `lang` prop) THEN hệ thống SHALL CONTINUE TO hiển thị đúng ngôn ngữ cho các nhãn model.

---

### BUG 6 — Comic bị tạo lại mỗi khi chuyển tab

#### Current Behavior (Defect)

6.1 WHEN người dùng click tab "Truyện tranh" và `comicPanels` đã có dữ liệu THEN hệ thống vẫn gọi lại `/api/comic/generate`, tiêu tốn tài nguyên và "xu" của người dùng không cần thiết.

6.2 WHEN tab comic được activate THEN hệ thống không kiểm tra xem comic đã được tạo chưa trước khi trigger generate.

#### Expected Behavior (Correct)

6.1 WHEN người dùng click tab "Truyện tranh" và `comicPanels.length > 0` THEN hệ thống SHALL chỉ hiển thị panels đã có, không gọi lại API generate.

6.2 WHEN người dùng bấm nút "Chuyển thể thành Manga" (lần đầu) hoặc "Tiếp tục chuyển thể" THEN hệ thống SHALL mới gọi `/api/comic/generate`.

6.3 WHEN `comicPanels.length > 0 && comicId !== null` THEN hệ thống SHALL không trigger generate lại, kể cả khi tab được switch đi rồi switch lại.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN người dùng bấm "Chuyển thể thành Manga" lần đầu với `comicPanels` rỗng THEN hệ thống SHALL CONTINUE TO gọi API và tạo comic.

3.2 WHEN comic được tạo thành công THEN hệ thống SHALL CONTINUE TO lưu panels vào state và hiển thị đúng.

---

### BUG 7 — Mạng xã hội: thiếu tìm kiếm nâng cao và filter theo genre

#### Current Behavior (Defect)

7.1 WHEN `CommunityFeedView` render danh sách genre tags THEN hệ thống hiển thị genre pills cố định riêng lẻ bên ngoài, không tích hợp với Advanced Search panel.

7.2 WHEN `filteredPosts` được tính toán THEN hệ thống chỉ filter theo `title` và `author`, không filter theo `selectedGenre`, dẫn đến kết quả lọc không chính xác khi user chọn genre.

#### Expected Behavior (Correct)

7.1 WHEN người dùng mở `CommunityFeedView` THEN hệ thống SHALL hiển thị một Advanced Search panel gồm: (1) ô tìm kiếm text (title + tên tác giả), (2) dropdown hoặc chip chọn thể loại (genre), (3) nút "Tìm kiếm" và "Xóa bộ lọc".

7.2 WHEN `filteredPosts` được tính toán với `selectedGenre` khác null/rỗng THEN hệ thống SHALL lọc posts theo genre của post khớp với `selectedGenre`.

7.3 WHEN `selectedGenre` được chọn THEN hệ thống SHALL cập nhật `filteredPosts` để phản ánh filter genre kết hợp với search query hiện tại.

7.4 WHEN genre pills được hiển thị THEN hệ thống SHALL đặt genre pills bên trong Advanced Search panel thay vì hiển thị riêng lẻ bên ngoài.

#### Unchanged Behavior (Regression Prevention)

3.1 WHEN người dùng nhập search query THEN hệ thống SHALL CONTINUE TO filter posts theo title và tên tác giả.

3.2 WHEN người dùng xóa bộ lọc THEN hệ thống SHALL CONTINUE TO hiển thị toàn bộ posts không có filter.

3.3 WHEN giao diện song ngữ Việt-Anh THEN hệ thống SHALL CONTINUE TO hiển thị đúng ngôn ngữ cho tất cả labels trong Advanced Search panel.

---

## Bug Condition Summary (Pseudocode)

### BUG 1 — Focus Lost After Send

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type ChatSendEvent
  OUTPUT: boolean
  RETURN X.messageSent = true AND X.loadingCompleted = true AND X.focusRestored = false
END FUNCTION

// Fix Checking
FOR ALL X WHERE isBugCondition(X) DO
  ASSERT textareaRef.current.isFocused = true
END FOR

// Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

### BUG 2 — API URL / Payload Error

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type StoryGenerationRequest
  OUTPUT: boolean
  RETURN X.endpointURL does NOT start with "/api/" 
      OR X.payload.refined_prompt IS NULL
      OR X.payload.story_length IS NULL
END FUNCTION
```

### BUG 3 — Comic with Empty Story

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type ComicGenerateRequest
  OUTPUT: boolean
  RETURN X.storyContent = "" OR X.storyContent IS NULL
END FUNCTION
```

### BUG 4 — Copilot edit_story_direct Not Applied

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type CopilotEventResult
  OUTPUT: boolean
  RETURN X.action = "edit_story_direct" AND setStoryContent NOT called
END FUNCTION
```

### BUG 6 — Comic Re-generated on Tab Switch

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type TabSwitchEvent
  OUTPUT: boolean
  RETURN X.tab = "comic" AND X.comicPanels.length > 0 AND generateAPIWasCalled = true
END FUNCTION
```
