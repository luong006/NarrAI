# Báo Cáo Khảo Sát Kiến Trúc: Requirements #4 & #5
**Dự án**: NarrAI MVP (Nền tảng Sáng tác Tiểu thuyết & Mạng Xã hội Văn học AI)  
**Ngày thực hiện**: 2026-09-29  
**Người thực hiện**: Teamwork Explorer (`explorer_r5_survey_3`)  
**Tập lệnh & Nguồn tài liệu**: `ORIGINAL_REQUEST.md`, `backend/`, `frontend/`

---

## 1. TỔNG QUAN HIỆN TRẠNG HỆ THỐNG

### 1.1 Mục tiêu khảo sát
Đánh giá chi tiết hiện trạng kiến trúc và mức độ sẵn sàng của Backend (`e:\NarrAI\backend`) và Frontend (`e:\NarrAI\frontend`) đối với hai yêu cầu kỹ thuật trọng tâm:
1. **Requirement #4 (R4)**: Chuyên mục "Bài đăng" (Community Feed), Trình đọc tác phẩm (Truyện chữ & Manga), Nút "Lưu & Đăng bài" trên Story Editor, và Tích hợp Thuật toán Gợi ý 3 giai đoạn (Two-Tower Cosine + Multi-Armed Bandit 15% Cold-Start + MMR $\lambda = 0.7$).
2. **Requirement #5 (R5)**: Kiến trúc Frontend Phân lớp Chống Xung đột (4-Layer Collision-Free Frontend Pipeline: Layer 0 Ambient WebGL Canvas, Layer 1 Semantic DOM 3D Cards, Layer 2 Morphicons SVG Spring Physics, Layer 3 Glassmorphism Modals & Portals).

### 1.2 Bảng đối chiếu hiện trạng tổng thể

| Hạng mục chức năng | Trạng thái Backend | Trạng thái Frontend | Nhận định & Khoảng cách (Gap Analysis) |
| :--- | :--- | :--- | :--- |
| **Cơ sở dữ liệu (Models/Migrations)** | ✅ Đầy đủ 100% | N/A | Bảng `social_posts`, `post_interactions`, `user_interest_profiles`, `stories`, `comics`, `comic_panels` đã định nghĩa đầy đủ trong `backend/db/models.py`. |
| **Thuật toán Đề xuất 3 giai đoạn** | ✅ Đầy đủ 100% | ❌ Chưa kết nối | Đã triển khai hoàn chỉnh trong `backend/services/recommender_service.py` kèm test suites e2e, nhưng frontend chưa có API call để lấy feed này. |
| **Backend Routes (Social & Feed)** | ⚠️ Hoàn thành 90% | ❌ Chưa gọi API | `backend/routers/social_router.py` đã mount tại `/api/social` (`/feed`, `/publish`, `/interact`, `/post/{id}`). Cần bổ sung auto-sync bìa comic & lưu draft vào `/publish`, và trả về full text + comic panels trong `/post/{id}`. |
| **Tab điều hướng "Bài đăng"** | N/A | ❌ Chưa có UI | `page.tsx` chỉ có state tab `"setup" \| "editor" \| "comic"`. `Sidebar.tsx` chưa có nút/tab điều hướng "Bài đăng" ngang hàng với "Sáng tác" và "Truyện tranh". |
| **Community Feed UI & 3D Cards** | N/A | ❌ Chưa có UI | Chưa có component `CommunityFeed.tsx`. Component 3D Card (`InteractiveTiltCard.tsx`) đã có nhưng chưa được dùng cho bài đăng cộng đồng. |
| **Trình đọc bài đăng (Reader Modal)** | ⚠️ Thiếu endpoint data | ❌ Chưa có UI | Chưa có modal đọc truyện chữ và xem truyện tranh manga liên kết từ bài đăng feed. Backend chưa trả về full text/comic panels cho bài đăng. |
| **Nút "Lưu & Đăng bài" trên Toolbar** | ⚠️ Cần bổ sung logic | ❌ Chưa có UI | `StoryEditor.tsx` chỉ có nút "Chuyển thể Truyện tranh" và "Tải bản thảo". Chưa có nút "Lưu & Đăng bài" và handler xuất bản. |
| **Layer 0: Ambient WebGL Canvas** | N/A | ✅ Hoàn thành 100% | `ThreeAmbientCanvas.tsx` chạy shader Trống Đồng Đông Sơn + 350 hạt 3D, auto-pause khi tab ẩn hoặc ngoài viewport, GPU 0%. |
| **Layer 1: Semantic DOM 3D Cards** | N/A | ✅ Hoàn thành 100% | `InteractiveTiltCard.tsx` dùng CSS 3D Transforms `perspective: 1000px`, `transform-style: preserve-3d`, glare overlay, 60 FPS compositor. |
| **Layer 2: SVG Morphicons** | N/A | ✅ Hoàn thành 100% | `LikeButtonMorphicon.tsx`, `CoinBadgeMorphicon.tsx`, `springPhysics.ts` Euler damped harmonic oscillator + 8-ray micro-burst. |
| **Layer 3: Portals & Glassmorphism** | N/A | ✅ Hoàn thành 100% | `ClientPortal.tsx` sử dụng `ReactDOM.createPortal` với `isolation: isolate` và `z-index: 50+` (thực tế 60), chống Chromium 3D clipping & z-fighting. |

---

## 2. KHẢO SÁT CHI TIẾT BACKEND (`backend/`)

### 2.1 Database Models & Migrations (`backend/db/models.py`)
Tập tin `backend/db/models.py` (293 dòng) đã khai báo hoàn chỉnh các thực thể dữ liệu cần thiết:

1. **`SocialPost` (Dòng 133–161)**:
   - Các cột: `id` (PK), `user_id` (FK `users.id`), `story_id` (FK `stories.id`, nullable), `title` (VARCHAR 255), `content_snippet` (TEXT), `cover_image_url` (VARCHAR 500), `genre` (VARCHAR 100), `tags` (TEXT - JSON list), `concept_vector` (TEXT - 128-dim JSON float array), `dsgo_entities` (TEXT - JSON list), `dsgo_spaces` (TEXT - JSON list), `completion_count` (INTEGER), `likes_count` (INTEGER), `comments_count` (INTEGER), `views_count` (INTEGER), `dwell_time_avg` (FLOAT), `created_at` (DATETIME).
   - Quan hệ: `author = relationship("User", back_populates="posts")`, `story = relationship("Story", back_populates="social_posts")`, `interactions = relationship("PostInteraction", back_populates="post", cascade="all, delete-orphan")`.

2. **`PostInteraction` (Dòng 163–190)**:
   - Các cột: `id` (PK), `user_id` (FK `users.id`), `post_id` (FK `social_posts.id`), `interaction_type` (VARCHAR 50: `LIKE`, `COMMENT`, `BOOKMARK`, `SHARE`, `CLICK`, `SCROLL_50`, `SCROLL_100`, `DWELL_TIME`), `dwell_seconds` (FLOAT), `scroll_depth` (INTEGER), `comment_text` (TEXT), `sentiment_score` (FLOAT: -1.0 đến +1.0), `extracted_entities` (TEXT - JSON list), `created_at` (DATETIME).

3. **`UserInterestProfile` (Dòng 192–207)**:
   - Các cột: `id` (PK), `user_id` (FK `users.id`, UNIQUE), `interest_vector` (TEXT - 128-dim JSON float array), `last_decay_time` (DATETIME), `genre_affinity` (TEXT - JSON key-value), `entity_affinity` (TEXT - JSON key-value), `last_active_at` (DATETIME), `updated_at` (DATETIME).

4. **`Story`, `Comic`, `ComicPanel` (Dòng 28–70)**:
   - `Story`: Chứa `story_content` (toàn văn bản thảo), `refined_prompt`, `genre`, `tone`, `word_count`, `bible_data`, `memory_data`.
   - `Comic`: Chứa `story_id` (FK `stories.id`), `title`, `adapted_offset`.
   - `ComicPanel`: Chứa `comic_id` (FK `comics.id`), `panel_index`, `image_prompt`, `dialogue_text`, `image_url` (định dạng `/api/comic/image/{panel.id}`), `layout_type`.

### 2.2 Thuật toán Gợi ý Đa tầng (`backend/services/recommender_service.py`)
Tập tin `backend/services/recommender_service.py` (1108 dòng) thực thi xuất sắc toàn bộ yêu cầu toán học:

1. **Khởi tạo và Vector không gian 128 chiều (Dòng 40–180)**:
   - `VECTOR_DIM = 128`, chuẩn hóa vector đơn vị L2 $\lVert V \rVert_2 = 1.0$ qua hàm `normalize_vector`.
   - `cosine_similarity(vec_a, vec_b)` tính tích vô hướng cosin kẹp trong $[0.0, 1.0]$.
   - `generate_concept_vector(text_content, genre, tags)` chiếu hash đa tần số (SHA-256 slicing) tạo vector phân bổ dày đặc.

2. **Stage 1: Candidate Generation (Dòng 431–528)**:
   - Funnel 1: Lấy top 40 bài viết tương đồng Cosine cao nhất giữa User Interest Vector và Post Concept Vector.
   - Funnel 2: Lấy top 20 bài viết duyệt đồ thị DSGO (Graph-Based DSGO Traversal) dựa trên độ trùng khớp thực thể (`dsgo_entities`) và không gian (`dsgo_spaces`) người dùng yêu thích.
   - Hợp nhất và loại trùng lặp.

3. **Stage 2: Scoring & Multi-Task Ranking (Dòng 530–625)**:
   - Công thức chấm điểm tổng hợp:
     $$\text{Score}(p, u) = 0.35 \times \text{CosineSim}(U_u, V_p) + 0.25 \times \text{ImplicitAffinity}(u, p) + 0.20 \times \text{Freshness}(p) + 0.20 \times \text{QualityScore}(p)$$
   - Trong đó:
     - $\text{Freshness}(p) = \frac{1}{1 + 0.02 \times \text{hours\_old}}$
     - $\text{QualityScore}(p) = 0.40 \times \text{CompletionRate} + 0.30 \times \text{LikeRatio} + 0.30 \times \text{DwellNorm}$

4. **Stage 3: Re-ranking, Serendipity & Exploration (Dòng 627–767)**:
   - **Multi-Armed Bandit (15% Exploration)**: Dành $15\%$ số vị trí feed (slots) cho nhóm tác phẩm Cold-Start ($\text{views} < 30$), áp dụng thuật toán **Thompson Sampling** lấy mẫu từ phân phối Beta $\text{Beta}(\alpha, \beta)$ với $\alpha = 1 + \text{likes} + \text{completions}$, $\beta = 1 + \max(0, \text{views} - \text{likes})$.
   - **Maximal Marginal Relevance (MMR)**: Áp dụng tham số $\lambda_{\text{MMR}} = 0.70$ để tối ưu hóa sự đa dạng thể loại và ngăn chặn hiện tượng buồng vang (echo chamber):
     $$\text{MMR} = \operatorname{argmax}_{p \in R \setminus S} \left[ \lambda \cdot \text{Score}(p) - (1 - \lambda) \max_{s \in S} \text{Sim}(p, s) \right]$$

5. **Phân tích Cảm xúc & Suy giảm theo thời gian (Dòng 182–418)**:
   - `extract_sentiment_and_entities`: Phân tích từ điển cảm xúc tiếng Việt & Anh (tuyệt vời, cuốn hút, dở tệ, nhạt...) trả về điểm cảm xúc $[-1.0, 1.0]$.
   - `apply_exponential_decay`: Suy giảm trọng số theo hàm số mũ $\lambda = 0.05/\text{ngày}$ ($e^{-\lambda \Delta t}$).

### 2.3 Hiện trạng API Routes (`backend/routers/social_router.py` & `main.py`)
Router được gắn vào ứng dụng tại `backend/main.py`:
```python
# backend/main.py line 88 & 92
from routers.social_router import router as social_router
app.include_router(social_router, prefix="/api/social", tags=["Social"])
```
Các endpoints hiện có:
- `GET /api/social/feed`: Trả về danh sách bài đăng đề xuất cá nhân hóa.
- `POST /api/social/publish`: Xuất bản bài viết vào bảng `social_posts`.
- `POST /api/social/interact`: Ghi nhận tín hiệu tương tác độc giả (Like, Comment, Scroll, Dwell-time).
- `GET /api/social/post/{post_id}` & `GET /api/social/posts/{post_id}`: Lấy chi tiết bài viết và danh sách bình luận.

### 2.4 Khoảng cách kỹ thuật cần cải tiến ở Backend
1. **Thiếu Auto-Save Draft & Comic Cover Sync trong `publish_post`**:
   - Khi người dùng bấm "Lưu & Đăng bài" từ Editor, nếu bản thảo vừa được chỉnh sửa, nội dung mới nhất chưa được cập nhật vào bảng `Story`.
   - Nếu tác giả đã chuyển thể Manga trước đó, bài đăng nên tự động lấy ảnh bìa từ panel đầu tiên (`comic.panels[0].image_url`) nếu client không truyền URL ảnh bìa cụ thể.
   - **Giải pháp**: Cập nhật hàm `publish_post` trong `backend/services/recommender_service.py` để:
     - Nhận thêm tham số `story_text: Optional[str] = None`. Nếu có `story_id`, cập nhật `story.story_content = story_text`; nếu chưa có `story_id`, tự động tạo bản ghi `Story` mới và gán vào bài đăng.
     - Nếu `not cover_image_url` và có `story_id`: truy vấn bảng `Comic` liên kết với `story_id`, lấy `panel[0].image_url` làm `cover_image_url`.
2. **Thiếu Full Content & Comic Panels trong `get_post_details`**:
   - Hiện tại hàm `get_post_details` (dòng 1086–1107) chỉ trả về `content_snippet`. Độc giả trên Feed khi muốn đọc toàn văn tác phẩm không có trường `story_content` đầy đủ.
   - Độc giả cũng không nhận được danh sách `comic_panels` để lướt xem truyện tranh của tác phẩm nếu đã chuyển thể.
   - Endpoint `GET /api/stories/{story_id}` hiện có ràng buộc bảo mật `Story.user_id == current_user.id`, nên người dùng khác không thể gọi trực tiếp endpoint này để đọc truyện của tác giả khác.
   - **Giải pháp**: Cập nhật `get_post_details` trả về thêm:
     - `story_content`: Nội dung toàn văn từ `post.story.story_content` (hoặc fallback `content_snippet`).
     - `comic_id` & `comic_panels`: Truy vấn `Comic` và `ComicPanel` của `story_id` để trả về danh sách panel cho modal xem truyện tranh.

---

## 3. KHẢO SÁT CHI TIẾT FRONTEND (`frontend/`)

### 3.1 Cấu trúc Navigation & Tabs hiện tại (`src/app/page.tsx` & `src/components/layout/Sidebar.tsx`)
1. **Quản lý Tab trong `page.tsx`**:
   - Dòng 157: `const [activeTab, setActiveTab] = useState<"setup" | "editor" | "comic">("setup");`
   - Chỉ có 3 trạng thái cục bộ cho quy trình sáng tác:
     - `"setup"`: Quy trình tạo ý tưởng (Phase 1 Idea -> Phase 2 Interview -> Phase 3 Controls).
     - `"editor"`: Soạn thảo bản thảo (`StoryEditor.tsx` + `AICopilotPanel.tsx`).
     - `"comic"`: Trình xem truyện tranh tác giả vừa tạo (`ComicViewer.tsx`).
   - Hoàn toàn chưa có trạng thái `"feed"` hoặc `"community"` cho chuyên mục "Bài đăng".
2. **Cấu trúc Menu trong `Sidebar.tsx` (Dòng 95–134)**:
   - Chỉ có 3 nút hành động dọc:
     - "Tạo truyện mới" (`onNewStory`) -> Chuyển về `"setup"` Phase 1.
     - "Lịch sử tác phẩm" (`onOpenHistory`) -> Mở `HistoryModal`.
     - "Open Messenger" (`onOpenMessenger`) -> Mở `MessengerModal`.
   - Chưa có cụm chuyển đổi tab chính quy: **"Sáng tác"** (Creation / Editor), **"Truyện tranh"** (Comic), và **"Bài đăng"** (Community Feed).

### 3.2 Thanh công cụ `StoryEditor.tsx` & Nút "Lưu & Đăng bài"
Tập tin `src/components/editor/StoryEditor.tsx` (268 dòng):
- Thanh công cụ Top Bar (Dòng 161–189) hiện chỉ có 2 nút:
  1. Nút "Chuyển thể Truyện tranh" (`onAdaptToComic`) với icon `Palette`.
  2. Nút "Tải bản thảo (TXT)" (`onDownload`) với icon `Download`.
- **Khoảng cách**:
  - Chưa có nút **"Lưu & Đăng bài"** (Save & Publish).
  - Cần bổ sung nút nổi bật (ví dụ màu gradient brand hoặc indigo sang trọng kèm icon `Share2` hoặc `Send`) ngay trên thanh công cụ này.
  - Khi bấm:
    1. Kích hoạt lưu bản thảo chữ mới nhất.
    2. Đồng bộ ảnh bìa truyện tranh manga (nếu có trong `comicPanels` hoặc từ backend).
    3. Gọi API `POST /api/social/publish`.
    4. Kích hoạt Toast thông báo thành công với nút hoặc liên kết chuyển thẳng sang xem bài đăng trên tab "Bài đăng".

### 3.3 Khảo sát Kiến trúc Phân lớp Chống Xung đột 4-Layer (Requirement #5)

#### Layer 0: Ambient 3D Canvas (`ThreeAmbientCanvas.tsx`)
- **Tập tin**: `src/components/canvas/ThreeAmbientCanvas.tsx` (611 dòng), mount tại `src/app/layout.tsx` dòng 22.
- **Phong cách thị giác**: Họa tiết Trống đồng Đông Sơn cổ truyền (ngôi sao mặt trời 14 cánh, vòng chấm cườm, răng cưa tam giác, chim Lạc bay ngược chiều kim đồng hồ) phối hợp 350 hạt ánh sáng 3D lơ lửng tương tác chuột.
- **Kiến trúc DOM & CSS**:
  - `position: fixed; inset: 0; z-index: 0; pointer-events: none; width: 100vw; height: 100vh;`
  - Đảm bảo nằm hoàn toàn ở tầng nền sâu nhất, không chắn chuột hay bắt sự kiện DOM.
- **Quản lý Context WebGL**:
  - Khởi tạo duy nhất 1 WebGL Context cho toàn bộ ứng dụng (Native WebGL GLSL, không load Three.js nặng nề, ~12KB footprint).
  - Có bộ lọc bắt sự kiện `webglcontextlost` và `webglcontextrestored` tự phục hồi tài nguyên.
- **Tối ưu hóa 0.0% CPU/GPU**:
  - Lắng nghe `document.visibilitychange`: Khi tab ẩn, `cancelAnimationFrame` dừng hoàn toàn vòng lặp render.
  - Sử dụng `IntersectionObserver`: Khi canvas ra khỏi màn hình, render loop tự động tạm dừng.
  - Bộ đếm thời gian rảnh (Idle watchdog 8 giây): Nếu không có thao tác chuột/phím, tự động ngủ đông, đánh thức ngay khi có sự kiện `pointermove` hoặc `scroll`.
- **Graceful Degradation**:
  - Tự động kiểm tra `prefers-reduced-motion` hoặc `navigator.hardwareConcurrency <= 2` để chuyển sang chế độ CSS radial gradient thuần túy.

#### Layer 1: Core Semantic DOM & 3D Interactive Cards (`InteractiveTiltCard.tsx`)
- **Tập tin**: `src/components/cards/InteractiveTiltCard.tsx` (163 dòng).
- **Kiến trúc kỹ thuật**:
  - CSS 3D Transforms độc lập: `perspective: 1000px; transform-style: preserve-3d`.
  - Con trỏ chuột tính toán góc nghiêng vật lý: `rotateX(rotX deg) rotateY(rotY deg) scale3d(1.02, 1.02, 1.02)`.
  - Hiệu ứng vệt sáng phản chiếu (Specular glare overlay) với `mix-blend-mode: overlay` di chuyển theo góc chiếu của con trỏ.
  - Hỗ trợ các mặt phẳng độ cao phân lớp con: `translateZ(28px)`, `translateZ(48px)` tạo chiều sâu thị giác chân thực.
  - Vận hành 100% trên luồng Compositor của trình duyệt ở 60 FPS, không can thiệp hay chia sẻ WebGL matrix của Layer 0.

#### Layer 2: SVG Morphing Micro-Interactions (`Morphicons`)
- **Tập tin**:
  - `src/components/morphicons/springPhysics.ts`: Bộ dao động điều hòa giảm chấn (Euler Damped Harmonic Oscillator: $F = -k \Delta x - c v$) không phụ thuộc thư viện ngoài.
  - `src/components/morphicons/LikeButtonMorphicon.tsx`: Nút Like biến hình từ viền thanh mảnh sang tim đỏ rực rỡ (`#f43f5e`), kích hoạt hiệu ứng nổ vi mô 8 tia sáng đa sắc (8-ray micro-burst).
  - `src/components/morphicons/CoinBadgeMorphicon.tsx`: Biểu tượng đồng xu 3D xoay và bung nảy hiển thị số dư xu.
  - `src/components/morphicons/ModelSelectorMorphicon.tsx`: Chuyển đổi icon Flash / Versatile / Master.
- **Tính độc lập**:
  - Chạy thuần túy trên vector DOM, không xung đột với CSS 3D transform matrix hay WebGL pipeline.

#### Layer 3: Glassmorphism Overlay & Portals (`ClientPortal.tsx`)
- **Tập tin**: `src/components/portals/ClientPortal.tsx` (58 dòng).
- **Kiến trúc kỹ thuật**:
  - Sử dụng `ReactDOM.createPortal` dịch chuyển các hộp thoại ra ngoài cây DOM chính, gắn trực tiếp vào một `div.narrai-portal-root` tại `document.body`.
  - Ràng buộc cứng:
    ```javascript
    div.style.isolation = 'isolate';
    div.style.position = 'relative';
    div.style.zIndex = String(zIndex); // 50+ (mặc định 60 cho các Modal)
    ```
  - **Triệt tiêu xung đột (Anti-Collision)**:
    - `isolation: isolate` tạo ra một Stacking Context độc lập ở gốc, ngăn ngừa triệt để lỗi render layer (z-fighting).
    - Khắc phục hoàn toàn lỗi kinh điển của trình duyệt Chromium: Khi một phần tử có `backdrop-filter: blur()` nằm bên trong một cha có `transform-style: preserve-3d` hoặc CSS 3D matrix, lớp nền mờ sẽ bị vỡ vụn hoặc bị cắt xén (3D clipping bug). `ClientPortal` cách ly hoàn toàn Modal khỏi Layer 1.

---

## 4. CHI TIẾT CÁC THÀNH PHẦN CẦN BỔ SUNG & HOÀN THIỆN

### 4.1 Frontend Client API (`src/lib/api.ts`)
Hiện tại `api.ts` chưa có các hàm gọi đến `routers/social_router.py`. Cần bổ sung:
```typescript
// Bổ sung vào src/lib/api.ts:
async getSocialFeed(params?: { limit?: number; offset?: number; genre?: string }): Promise<SocialFeedResponse> {
  const query = new URLSearchParams();
  if (params?.limit) query.append('limit', String(params.limit));
  if (params?.offset) query.append('offset', String(params.offset));
  if (params?.genre && params.genre !== 'All' && params.genre !== 'Tất cả') {
    query.append('genre', params.genre);
  }
  const res = await fetch(`${API_BASE_URL}/social/feed?${query.toString()}`, {
    headers: authHeaders(),
  });
  return res.json();
},

async publishSocialPost(payload: {
  title: string;
  content_snippet: string;
  story_id?: number | null;
  story_text?: string;
  genre?: string;
  tags?: string[];
  cover_image_url?: string | null;
}): Promise<{ success: boolean; post_id?: number; message?: string }> {
  const res = await fetch(`${API_BASE_URL}/social/publish`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  return res.json();
},

async interactSocialPost(payload: {
  post_id: number;
  interaction_type: 'LIKE' | 'COMMENT' | 'BOOKMARK' | 'SHARE' | 'CLICK' | 'SCROLL_50' | 'SCROLL_100' | 'DWELL_TIME';
  dwell_seconds?: number;
  scroll_depth?: number;
  comment_text?: string;
}): Promise<{ success: boolean; interaction_id?: number; metadata?: any }> {
  const res = await fetch(`${API_BASE_URL}/social/interact`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  return res.json();
},

async getSocialPostDetails(postId: number): Promise<{ success: boolean; data?: any }> {
  const res = await fetch(`${API_BASE_URL}/social/post/${postId}`, {
    headers: authHeaders(),
  });
  return res.json();
}
```

### 4.2 Component Community Feed (`src/components/feed/CommunityFeed.tsx`)
Cần tạo mới component này để đáp ứng trọn vẹn Requirement #4:
- **Thanh lọc Thể loại (Genre Tabs)**: Tất cả, Tiên hiệp, Kiếm hiệp, Mạt thế, Khoa học viễn tưởng, Lịch sử, Đô thị, Lãng mạn, Kinh dị dân gian.
- **Lưới hiển thị Thẻ bài 3D (3D Interactive Cards Grid)**:
  - Bọc trong `InteractiveTiltCard` (Layer 1).
  - Hiển thị ảnh bìa Manga (hoặc poster nghệ thuật chữ ấn tượng), huy hiệu thể loại.
  - Huy hiệu "Khám phá mới" (Cold-start exploration tag) từ thuật toán Multi-Armed Bandit.
  - Tiêu đề tác phẩm, trích đoạn lôi cuốn, tên tác giả, ngày đăng.
  - Cụm tương tác: `LikeButtonMorphicon` (Layer 2) gọi `interactSocialPost('LIKE')`, số bình luận, số lượt xem, thời gian dừng đọc trung bình.
- **Trạng thái Trống & Đang tải**: Skeleton loader với hiệu ứng shimmer sang trọng.

### 4.3 Component Trình Đọc Tác Phẩm (`src/components/modals/PostReaderModal.tsx`)
Bọc trong `ClientPortal` (Layer 3: `isolation: isolate`, `z-index: 60`), bao gồm 2 chế độ xem:
1. **Chế độ Đọc Truyện Chữ (Novel Reading Mode)**:
   - Toàn văn tác phẩm với font serif (Merriweather), cỡ chữ co giãn, chế độ sáng/tối.
   - Theo dõi tín hiệu ẩn (Implicit Tracking):
     - Đồng hồ đếm thời gian dừng đọc thực tế (`dwell_seconds`).
     - Lắng nghe sự kiện cuộn trang để ghi nhận `SCROLL_50` và `SCROLL_100` (đọc xong chương) gửi lên `POST /api/social/interact`.
2. **Chế độ Xem Truyện Tranh (Manga Adaptation Mode)**:
   - Nếu tác phẩm có truyện tranh chuyển thể (`comic_panels`), chuyển sang hiển thị lưới tranh Manga đen trắng chuẩn mực với bóng thoại (Speech bubble) và huy hiệu số thứ tự phân cảnh.
3. **Cột Bình luận & Thảo luận**:
   - Danh sách bình luận thời gian thực kèm điểm đánh giá cảm xúc (`sentiment_score`).
   - Ô nhập bình luận độc giả gửi đến `POST /api/social/interact`.
   - Nút chia sẻ (Share) sao chép đường dẫn bài viết.

### 4.4 Cập nhật Navigation trong `Sidebar.tsx` và `page.tsx`
1. Trong `Sidebar.tsx`:
   - Bổ sung nhóm nút chuyển đổi 3 chuyên mục chính:
     - ✍️ **"Sáng tác"** (`creation`): Soạn thảo truyện và chỉ đạo Copilot.
     - 🎨 **"Truyện tranh"** (`comic`): Trình xem Manga chuyển thể.
     - 🌐 **"Bài đăng"** (`feed`): Mạng xã hội cộng đồng tác giả.
2. Trong `page.tsx`:
   - Mở rộng state: `const [activeTab, setActiveTab] = useState<"setup" | "editor" | "comic" | "feed">("feed");`
   - Bổ sung thanh điều hướng tab nhỏ gọn, tinh tế ở đầu workspace hoặc trong sidebar.
   - Khi ở `activeTab === "feed"`, render `<CommunityFeed />`.
   - Tích hợp liên kết nhanh: Khi người dùng bấm "Lưu & Đăng bài" từ Editor, toast hiển thị nút "Xem bài viết" -> tự động chuyển sang tab `"feed"` và mở `PostReaderModal` cho bài viết vừa đăng.

---

## 5. BẢN ĐỒ KIẾN TRÚC FRONTEND 4 LỚP (RENDER PIPELINE ISOLATION)

```
+-----------------------------------------------------------------------------------+
|  Layer 3: Modals, Reader & Portals (React Portals, isolation: isolate, z-index: 60) |
|  - PostReaderModal (Đọc truyện chữ & Xem truyện tranh)                             |
|  - MessengerModal (Chat tự do Open Messenger)                                    |
|  - AuthModal, CoinTopupModal, HistoryModal                                        |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|  Layer 2: SVG Spring Physics Morphicons (DOM Vector, Damped Harmonic Oscillator)  |
|  - LikeButtonMorphicon (Tim viền -> Tim đầy đỏ rực rỡ + 8-Ray Micro-burst)       |
|  - CoinBadgeMorphicon (Đồng xu 3D xoay nảy bung số dư)                            |
|  - ModelSelectorMorphicon (Chuyển đổi hình thái biểu tượng Model AI)              |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|  Layer 1: Semantic DOM & 3D Interactive Cards (CSS 3D perspective: 1000px, 60FPS) |
|  - CommunityFeed Cards (Thẻ bài 3D Parallax Tilt, Specular Glare)                 |
|  - ComicPanelCard (Khung tranh Manga với translateZ(28px), translateZ(48px))     |
|  - StoryEditor Manuscript Paper & AICopilotPanel                                  |
+-----------------------------------------------------------------------------------+
                                         |
+-----------------------------------------------------------------------------------+
|  Layer 0: Ambient 3D WebGL Canvas (Single Shared Context, fixed inset-0, z-index: 0)|
|  - Procedural Dong Son Drum Quad Shader (Ngôi sao 14 cánh, chim Lạc, sóng nước)  |
|  - 350 Interactive 3D Floating Particles (Cursor Repulsion + Brownian Motion)     |
|  - Auto-Pause khi ẩn tab / ngoài viewport / idle 8s (CPU/GPU 0.0%)                |
|  - Graceful Degradation: CSS Radial Gradient cho prefers-reduced-motion           |
+-----------------------------------------------------------------------------------+
```

---

## 6. KẾT LUẬN & ĐỀ XUẤT HÀNH ĐỘNG TIẾP THEO

1. **Về phía Backend**:
   - Nền tảng thuật toán và cơ sở dữ liệu đã hoàn thiện cực kỳ vững chắc, đạt chuẩn các oracle toán học khắt khe (Two-Tower Cosine, Multi-Armed Bandit Thompson Sampling 15%, MMR diversity 0.7, Exponential Time Decay 0.05).
   - Chỉ cần 2 tinh chỉnh nhỏ mang tính tương thích:
     - Trong `services/recommender_service.py` (`publish_post`): Tự động lưu `story_text` vào bản thảo và tự động đồng bộ ảnh bìa từ panel đầu tiên của `Comic` nếu chưa có `cover_image_url`.
     - Trong `services/recommender_service.py` (`get_post_details`): Trả về thêm `story_content` (toàn văn bản thảo) và `comic_panels` để hỗ trợ modal đọc bài đăng.

2. **Về phía Frontend**:
   - Hạ tầng hiệu ứng thị giác và phân tầng không xung đột (Layer 0 WebGL Canvas, Layer 1 3D Tilt Card, Layer 2 Morphicons, Layer 3 Portals) đã hoàn thành xuất sắc, cấu trúc CSS/z-index phân cấp rõ ràng (`z-0` -> `z-10` -> `z-35` -> `z-60` -> `z-[9999]`).
   - Cần triển khai các thành phần UI kết nối Requirement #4:
     - Bổ sung các phương thức gọi API Social vào `src/lib/api.ts`.
     - Xây dựng component `CommunityFeed.tsx` sử dụng `InteractiveTiltCard` và `LikeButtonMorphicon`.
     - Xây dựng modal `PostReaderModal.tsx` đọc truyện chữ và xem tranh manga liên kết qua `ClientPortal`.
     - Thêm nút "Lưu & Đăng bài" trên thanh công cụ `StoryEditor.tsx` và liên kết với Toast xem bài đăng.
     - Cập nhật tab điều hướng 3 chuyên mục: "Sáng tác" - "Truyện tranh" - "Bài đăng" trong `Sidebar.tsx` và `page.tsx`.
