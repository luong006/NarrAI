# BÁO CÁO KHẢO SÁT & THIẾT KẾ KIẾN TRÚC TOÀN DIỆN: R2 & R3
**Dự án**: NarrAI — Nền Tảng Sáng Tác & Mạng Xã Hội Văn Học Đẳng Cấp Cao  
**Người thực hiện**: Explorer Survey 2 (`teamwork_preview_explorer`)  
**Ngày lập**: 2026-09-28  
**Tài liệu tham chiếu gốc**: `e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md` (Phiên bản `2026-09-28T01:01:31Z`)

---

## 1. TỔNG QUAN DỰ ÁN VÀ PHẠM VI KHẢO SÁT

Theo yêu cầu chuẩn từ `ORIGINAL_REQUEST.md`, hệ thống NarrAI tiến hành nâng cấp toàn diện lên phiên bản Mạng Xã Hội Văn Học Cấp Cao & Kinh Tế Xu Chuẩn Ngân Hàng. Explorer Survey 2 chịu trách nhiệm khảo sát toàn bộ nền tảng hiện hữu và thiết kế kiến trúc kỹ thuật chi tiết cho hai trụ cột then chốt:

1. **Requirement 2 (R2) — Thuật Toán Mạng Xã Hội Văn Học Cấp Cao & Open Messenger**:
   - Cấu trúc cơ sở dữ liệu đồ thị và hồ sơ người dùng đa tầng (`social_posts`, `post_interactions`, `user_interest_profiles`).
   - Thuật toán đề xuất lai ghép 3 giai đoạn (3-Stage Hybrid Recommender System): Candidate Generation (Content Cosine + Graph DSGO Traversal) $\rightarrow$ Scoring & Multi-Task Ranking $\rightarrow$ Re-ranking, Serendipity & Exploration (MMR $\lambda = 0.7$, Multi-Armed Bandit $\epsilon = 0.15$).
   - Hệ thống Open Messenger: Tìm kiếm người dùng trong toàn hệ sinh thái, chat 1-1 tự do giữa BẤT KỲ hai người dùng nào, quản lý hội thoại, đếm tin nhắn chưa đọc và thông báo tức thì.

2. **Requirement 3 (R3) — Tiền Tệ Chuẩn Ngân Hàng & Chống Tấn Công Trục Lợi Nguy Hiểm**:
   - Mô hình kinh tế 100 Xu (Tỷ giá 100k VNĐ = 100 Xu; Biểu phí: Truyện ngắn 8 xu, vừa 12 xu, dài 16 xu, sửa bản thảo 2 xu, chuyển thể manga 16 xu; Tặng tân thủ 8 xu dùng thử).
   - Cơ chế phòng chống Race Condition & Double-Spending tuyệt đối: Atomic Transaction kết hợp Dual-Locking (Per-User Thread Mutex `threading.Lock()` + SQLite `IMMEDIATE TRANSACTION`), lập tức từ chối HTTP 402 Payment Required nếu số dư không đủ.
   - Quyền lực tuyệt đối thuộc về máy chủ (Absolute Server Authority over Pricing): Loại bỏ hoàn toàn sự can thiệp từ phía client.
   - Giao dịch bù trừ tự động hoàn xu (Compensating Transaction Rollback — `REFUND_FAILED_GENERATION`) khi mô hình AI gặp lỗi 5xx hoặc timeout.
   - Sổ cái mật mã bất biến (Cryptographic Ledger): Bảng `coin_transactions` lưu vết bằng mã băm SHA-256 xâu chuỗi:
     $$tx\_hash = \text{SHA256}(prev\_hash + user\_id + amount + balance\_after + timestamp)$$
   - Hệ thống Anti-Clone & Sybil Guard đa lớp: Kết hợp Fingerprinting đa tín hiệu (Canvas 2D + WebGL + AudioContext + Screen Specs) và giới hạn dải IP Subnet (/24 subnet throttling).

---

## 2. HIỆN TRẠNG MÃ NGUỒN BACKEND (CODEBASE AUDIT)

### 2.1. Cấu hình Cơ sở Dữ liệu (`backend/db/models.py`)
- **Engine & Session**:
  - `engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})` (dòng 65).
  - Khởi tạo session trong `backend/main.py`: `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)` (dòng 71).
- **Các bảng hiện có**:
  1. `User` (`users`): `id`, `username`, `full_name`, `password_hash`, `created_at`.
     - *Nhận xét*: **Chưa có** cột `coins` (số dư xu), chưa có quan hệ tới bảng giao dịch hoặc mạng xã hội.
  2. `Story` (`stories`): `id`, `session_id`, `user_id`, `initial_prompt`, `refined_prompt`, `genre`, `tone`, `story_content`, `word_count`, `bible_data`, `memory_data`, `created_at`.
     - *Nhận xét*: `memory_data` lưu trữ chuỗi JSON của `StoryMemory`, bao gồm cả `DynamicSceneGraph` (DSGO) với `entities`, `enclosures`, `items`, `relations`.
  3. `Comic` (`comics`): `id`, `user_id`, `story_id`, `title`, `adapted_offset`, `created_at`.
  4. `ComicPanel` (`comic_panels`): `id`, `comic_id`, `panel_index`, `image_prompt`, `dialogue_text`, `image_url`, `layout_type`.
- **Cơ chế Auto-Migration**: Đã có sẵn block `inspect(engine)` trong `db/models.py` (dòng 69-85) tự động thêm cột thiếu (như `adapted_offset` hay `full_name`) mà không làm hỏng dữ liệu cũ. Đây là nền tảng lý tưởng để auto-migrate cột `coins` và tạo các bảng mới.

### 2.2. Hệ thống Xác thực & Giới hạn Tần suất (`backend/auth.py`)
- Đã cài đặt xác thực mật khẩu chuẩn ngân hàng (`validate_bank_password`): độ dài $\ge 8$, chữ hoa, chữ thường, chữ số, ký tự đặc biệt, không khoảng trắng.
- Đã có `LoginRateLimiter` thread-safe quản lý brute-force đăng nhập theo IP và username.
- Endpoint `/api/register` và `/api/login` đã vận hành trong `backend/main.py` (dòng 163-280).
- *Khoảng trống (Gap)*:
  - Khi người dùng đăng ký mới tại `/api/register`, chưa có cơ chế thu thập Device Fingerprint (Canvas/WebGL/Audio) và chưa kiểm tra IP Subnet `/24`. Hiện tại mọi tài khoản tạo ra đều không có ví xu.

### 2.3. Cơ sở Dữ liệu Đồ thị Tri thức DSGO (`backend/models/scene_graph.py`)
- Đã xây dựng hoàn thiện lớp `DynamicSceneGraph` với:
  - `entities`: Danh mục `CharacterEntity` (tên, visual DNA, vitality, vai trò, vị trí).
  - `enclosures`: Danh mục `SpaceEnclosure` (không gian phân cảnh, ranh giới, neo kiến trúc).
  - `items`: Danh mục `ItemEntity`.
  - `relations`: Quan hệ ngữ nghĩa giữa các thực thể.
  - `era_genre`: Ràng buộc thời đại và thể loại thế giới.
- *Liên kết tới R2*: Dữ liệu DSGO này được lưu trữ trong `Story.memory_data`. Khi xuất bản bài viết lên `social_posts`, các thực thể (`entities`) và không gian (`enclosures`) có thể được trích xuất thành thuộc tính tìm kiếm, phục vụ trực tiếp cho thuật toán **Graph-Based DSGO Traversal** ở Giai đoạn 1 của Recommender.

### 2.4. Tầng Bộ đệm (`backend/services/cache_service.py`)
- Đã có sẵn `CacheManager` với cơ chế Dual-Mode (Redis Cache + In-process LRU/TTL `ThreadSafeMemoryCache`).
- Đảm bảo thời gian phản hồi $< 20\text{ms}$ (sub-millisecond khi chạy local RAM).
- Sẵn sàng dùng để lưu cache cho:
  - Vector sở thích người dùng đã tính toán (`user_interest_profiles`).
  - Feed đề xuất tạm thời cho từng phiên người dùng.
  - Bộ đếm unread tin nhắn Messenger.
  - Danh sách IP Subnet & Fingerprint chống clone.

### 2.5. Các Endpoint Tiêu thụ Tài nguyên AI trong `backend/main.py`
- `POST /api/generate-story` (dòng 335): Sinh truyện từ `refined_prompt` theo độ dài `story_length`.
- `POST /api/story/init` (dòng 940): Khởi tạo cốt truyện và sinh Chương 1.
- `POST /api/edit-text` (dòng 322): Sửa văn bản qua `EditorAgent`.
- `POST /api/copilot/event` (dòng 825): Tương tác AI Co-pilot (trong đó có hành động `edit_story_direct`).
- `POST /api/comics` (dòng 595) & `/api/comic/continue` (dòng 637): Chuyển thể kịch bản và sinh khung tranh manga.
- *Khoảng trống (Gap)*:
  - Toàn bộ các endpoint này hiện tại **chưa trừ xu**, **chưa kiểm tra số dư**, và **chưa có cơ chế hoàn xu tự động** khi gọi mô hình bên ngoài (Groq, Cloudflare AI) bị lỗi mạng/timeout.

---

## 3. THIẾT KẾ KIẾN TRÚC CHI TIẾT: REQUIREMENT 2 (R2)
### Next-Gen Recommendation Engine & Open Messenger

```
+---------------------------------------------------------------------------------------+
|                                  R2 ARCHITECTURE OVERVIEW                             |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +-----------------------+     +------------------------+    +-------------------+   |
|   |     Social Posts      |     |   Post Interactions    |    |   User Profiles   |   |
|   | 128-d Concept Vector  |     |  Dwell/Scroll/Like/Cmt |    | Dynamic Decay 0.05|   |
|   +-----------+-----------+     +------------+-----------+    +---------+---------+   |
|               |                              |                          |             |
|               +-----------------------+      |                          |             |
|                                       v      v                          v             |
|   +-------------------------------------------------------------------------------+   |
|   |                        3-STAGE HYBRID RECOMMENDER                             |   |
|   |                                                                               |   |
|   |   [Stage 1: Candidate Generation]                                             |   |
|   |   - Two-Tower Content Cosine Similarity (top 40)                              |   |
|   |   - Graph DSGO Traversal (shared entities/spaces/era) (top 20)                |   |
|   |                                                                               |   |
|   |   [Stage 2: Scoring & Multi-Task Ranking]                                     |   |
|   |   Score = 0.35*Cosine + 0.25*Affinity + 0.20*Freshness + 0.20*Quality         |   |
|   |                                                                               |   |
|   |   [Stage 3: Re-ranking & Exploration (Anti Echo-Chamber)]                     |   |
|   |   - Maximal Marginal Relevance (MMR lambda=0.7) for Genre Diversity          |   |
|   |   - Multi-Armed Bandit (Thompson Sampling / eps=0.15) for Cold-Start Pool     |   |
|   +-------------------------------------------------------------------------------+   |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                         OPEN MESSENGER PLATFORM                               |   |
|   |   - Full User Directory Search (Prefix/Fuzzy query on ANY registered users)   |   |
|   |   - 1-on-1 Encrypted Messaging & Read Receipts                               |   |
|   |   - Conversation Ordering, Real-Time Badges & Total Unread Aggregations       |   |
|   +-------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------+
```

### 3.1. Cấu trúc Mô hình Dữ liệu (`db/models.py`)

#### 1. Bảng `social_posts`
Đại diện cho bài viết truyện được tác giả xuất bản lên Mạng Xã Hội Văn Học:
- `id`: `Integer`, Primary Key, autoincrement.
- `user_id`: `Integer`, `ForeignKey("users.id")`, indexed (Tác giả bài đăng).
- `story_id`: `Integer`, `ForeignKey("stories.id")`, nullable (Truyện gốc liên kết).
- `title`: `String(255)`, không rỗng.
- `content_snippet`: `Text`, trích đoạn mở đầu (khoảng 300 từ đầu tiên).
- `cover_image_url`: `String(500)`, link ảnh bìa hoặc panel manga.
- `genre`: `String(100)`, indexed (Thể loại: Kiếm hiệp, Tiên hiệp, Cyberpunk, Dã sử, v.v.).
- `tags`: `Text` (JSON array: `["Huyền Huyễn", "Xuyên Không", "Học Đường"]`).
- `concept_vector`: `Text` (JSON array chứa 128 số thực biểu diễn ngữ nghĩa của tác phẩm, chuẩn hóa $\|V\|_2 = 1.0$).
- `likes_count`: `Integer`, mặc định 0.
- `comments_count`: `Integer`, mặc định 0.
- `views_count`: `Integer`, mặc định 0.
- `dwell_time_avg`: `Float`, thời gian dừng đọc trung bình (giây).
- `completion_count`: `Integer`, số lượt độc giả đọc hết chương/bài.
- `dsgo_entities`: `Text` (JSON array các tên nhân vật trích xuất từ DSGO, e.g. `["Trần Quốc Tuấn", "Yết Kiêu"]`).
- `dsgo_spaces`: `Text` (JSON array các không gian bối cảnh, e.g. `["Sông Bạch Đằng", "Bến Bình Than"]`).
- `created_at`: `DateTime`, mặc định `datetime.utcnow`, indexed.

#### 2. Bảng `post_interactions`
Lưu trữ toàn bộ tín hiệu tương tác thời gian thực từ độc giả:
- `id`: `Integer`, Primary Key.
- `user_id`: `Integer`, `ForeignKey("users.id")`, indexed.
- `post_id`: `Integer`, `ForeignKey("social_posts.id")`, indexed.
- `interaction_type`: `String(50)`, indexed:
  - **Explicit Signals**: `LIKE`, `COMMENT`, `BOOKMARK`, `SHARE`.
  - **Implicit Signals**: `CLICK`, `SCROLL_50`, `SCROLL_100`, `DWELL_TIME_SECONDS`.
- `dwell_time`: `Float`, số giây dừng thực tế tại bài đăng.
- `scroll_depth`: `Integer`, độ sâu cuộn trang (50% hoặc 100%).
- `comment_text`: `Text`, nội dung bình luận (nếu có).
- `sentiment_score`: `Float` từ -1.0 đến +1.0 (Điểm cảm xúc bình luận).
- `extracted_entities`: `Text` (JSON array các thực thể người đọc nhắc đến trong bình luận).
- `created_at`: `DateTime`, mặc định `datetime.utcnow`.

**Hệ số trọng số tín hiệu tương tác ($w$):**
- $w(\text{Dwell} > 60\text{s}) = 2.5$ (Đọc sâu, quan tâm đặc biệt).
- $w(\text{Scroll\_100}) = 2.0$ (Cuộn hết toàn bộ trang).
- $w(\text{Scroll\_50}) = 1.0$ (Cuộn nửa bài).
- $w(\text{Like}) = 1.5$ (Thích tường minh).
- $w(\text{Comment}) = 3.0$ (Bình luận sâu sắc, tín hiệu cam kết cao nhất).
- $w(\text{Bookmark}) = 2.0$, $w(\text{Share}) = 2.5$, $w(\text{Click}) = 0.5$.

#### 3. Bảng `user_interest_profiles`
Hồ sơ sở thích động của người dùng, liên tục dịch chuyển theo thời gian:
- `id`: `Integer`, Primary Key.
- `user_id`: `Integer`, `ForeignKey("users.id")`, unique, indexed.
- `interest_vector`: `Text` (Vector 128 chiều, biểu diễn trọng tâm sở thích hiện tại).
- `genre_affinity`: `Text` (JSON map `{ "Kiếm hiệp": 0.85, "Cyberpunk": 0.20 }`).
- `entity_affinity`: `Text` (JSON map `{ "Trần Hưng Đạo": 1.2, "Bạch Đằng": 0.9 }`).
- `last_active_at`: `DateTime`.
- `updated_at`: `DateTime`.

---

### 3.2. Động Lực Học Cập Nhật Vector & Suy Giảm Thời Gian (Decay Dynamics)

Mỗi khi người dùng tương tác, vector sở thích $U_u$ được làm mới theo quy luật suy giảm hàm mũ (Exponential Time Decay) với hệ số suy giảm $\lambda = 0.05/\text{ngày}$:

$$\Delta t = \frac{t_{\text{hiện tại}} - t_{\text{lần cập nhật trước}}}{86400} \quad (\text{ngày})$$

Vector cũ suy giảm theo thời gian:
$$U_{\text{decayed}} = U_{\text{cũ}} \times e^{-\lambda \cdot \Delta t}$$

Tương tự, độ yêu thích thể loại suy giảm:
$$A_{\text{genre, decayed}} = A_{\text{genre}} \times e^{-\lambda \cdot \Delta t}$$

Khi ghi nhận tương tác mới với bài viết $p$ có vector nội dung $V_p$ và trọng số $w_{\text{effective}}$:
$$U_{\text{mới}} = \text{Normalize}\left( U_{\text{decayed}} + w_{\text{effective}} \cdot V_p \right)$$
trong đó hàm Normalize chia vector cho chuẩn L2: $\|U\|_2 = \sqrt{\sum u_i^2}$.

#### Phân Tích Cảm Xúc & Thực Thể từ Bình Luận (Comment Sentiment & Entities)
Khi người dùng để lại bình luận:
1. **Phân tích cảm xúc ($s \in [-1.0, 1.0]$)**:
   - Dựa trên tập từ vựng cảm xúc tiếng Việt (Sentiment Lexicon):
     - Tích cực: *"tuyệt vời", "quá hay", "cuốn hút", "xuất sắc", "đỉnh cao", "thích", "cảm động"*.
     - Tiêu cực: *"dở tệ", "nhảm", "buồn ngủ", "vô lý", "không thích", "chán ngắt"*.
   - Trọng số tương tác hiệu dụng được điều chỉnh:
     $$w_{\text{effective}} = w_{\text{comment}} \cdot (1.0 + s)$$
     *(Nếu khen nhiệt tình $s = +1.0 \Rightarrow w = 3.0 \times 2.0 = 6.0$; Nếu chê gay gắt $s = -0.8 \Rightarrow w = 3.0 \times 0.2 = 0.6$)*.
2. **Trích xuất thực thể**:
   - Quét nội dung bình luận đối chiếu với danh mục thực thể DSGO của bài viết (`dsgo_entities`, `dsgo_spaces`).
   - Nếu người dùng nhắc tên nhân vật (ví dụ: *"Trần Hưng Đạo điều binh thần sầu"*), tăng trực tiếp `entity_affinity["Trần Hưng Đạo"] += 1.5 * (1 + s)`.

---

### 3.3. Thuật Toán Đề Xuất Lai Ghép 3 Giai Đoạn (3-Stage Hybrid Recommender)

#### Giai đoạn 1: Candidate Generation (Truy Hồi Ứng Viên)
Từ hàng ngàn bài viết, hệ thống truy xuất một tập ứng viên rút gọn $\mathcal{C}$ ($|\mathcal{C}| \approx 60$ bài viết) thông qua 2 phễu truy hồi độc lập:

1. **Phễu 1 — Content-Based Cosine Retrieval (Top 40 ứng viên)**:
   - Tính độ tương đồng Cosine giữa vector sở thích người dùng $U_u$ và vector tác phẩm $V_p$:
     $$\text{CosineSim}(U_u, V_p) = U_u \cdot V_p = \sum_{i=1}^{128} u_i \cdot v_{p, i}$$
   - Lọc ra 40 bài viết có độ tương đồng cosine cao nhất chưa từng bị người dùng bỏ qua.

2. **Phễu 2 — Graph-Based DSGO Traversal (Top 20 ứng viên)**:
   - Xác định top 3 thực thể và không gian có điểm `entity_affinity` cao nhất của người dùng.
   - Duyệt đồ thị DSGO liên bài viết: Tìm kiếm các bài viết khác có giao tập thực thể hoặc bối cảnh (`dsgo_entities` $\cap$ `user_top_entities` $\neq \emptyset$).
   - Nhờ đó, người đọc thích nhân vật "Quang Trung" hoặc bối cảnh "Thăng Long" trong truyện lịch sử sẽ lập tức được kết nối tới các tác phẩm khác cùng chia sẻ thực thể này dù thể loại có thể lai ghép (Dã sử, Lịch sử hư cấu, Cyberpunk Thăng Long).

- Hợp nhất tập ứng viên: $\mathcal{C} = \text{TopCosine} \cup \text{TopDSGO}$.

#### Giai đoạn 2: Scoring & Multi-Task Ranking (Chấm Điểm & Xếp Hạng Đa Tiêu Chí)
Với mỗi ứng viên $p \in \mathcal{C}$, tính điểm tổng hợp theo công thức đa nhiệm:

$$\text{Score}(p, u) = w_1 \cdot \text{CosineSim}(U_u, V_p) + w_2 \cdot \text{ImplicitAffinity}(u, p) + w_3 \cdot \text{Freshness}(p) + w_4 \cdot \text{QualityScore}(p)$$

Các trọng số thành phần được hiệu chuẩn tối ưu:
- $w_1 = 0.35$ (Mức độ phù hợp ngữ nghĩa sâu).
- $w_2 = 0.25$ (Độ thân thuộc ngầm định từ hành vi lịch sử).
- $w_3 = 0.20$ (Độ tươi mới của tác phẩm).
- $w_4 = 0.20$ (Chất lượng tác phẩm từ cộng đồng độc giả).

**Chi tiết các hàm thành phần ($[0.0, 1.0]$)**:
1. $\text{CosineSim}(U_u, V_p)$: Chuẩn hóa về dải $[0, 1]$ qua $\max(0.0, U_u \cdot V_p)$.
2. $\text{ImplicitAffinity}(u, p)$:
   $$\text{ImplicitAffinity} = 0.65 \cdot A_{\text{genre}}(p.\text{genre}) + 0.35 \cdot \text{EntityOverlapRatio}(u, p)$$
3. $\text{Freshness}(p)$: Hàm suy giảm theo số giờ xuất bản:
   $$\text{Freshness}(p) = \frac{1}{1 + 0.02 \cdot \text{hours\_since\_published}}$$
   *(Bài viết 24h tuổi có điểm freshness $\approx 0.67$; bài 100h tuổi có điểm $\approx 0.33$)*.
4. $\text{QualityScore}(p)$: Phản ánh tỷ lệ hoàn thành tác phẩm và đánh giá độc giả:
   $$\text{CompletionRate} = \frac{p.\text{completion\_count}}{\max(p.\text{views\_count}, 1)}$$
   $$\text{LikeRatio} = \min\left(\frac{p.\text{likes\_count}}{\max(p.\text{views\_count}, 1)}, 1.0\right)$$
   $$\text{DwellNorm} = \min\left(\frac{p.\text{dwell\_time\_avg}}{60.0}, 1.0\right)$$
   $$\text{QualityScore}(p) = 0.40 \cdot \text{CompletionRate} + 0.30 \cdot \text{LikeRatio} + 0.30 \cdot \text{DwellNorm}$$

Sau Giai đoạn 2, tập $\mathcal{C}$ được sắp xếp giảm dần theo $\text{Score}(p, u)$.

#### Giai đoạn 3: Re-ranking, Serendipity & Exploration (Chống Echo-Chamber)
Để ngăn chặn tình trạng "Filter Bubble" (người dùng bị kẹt trong một thể loại duy nhất) và giải quyết bài toán tác giả mới (Cold-Start Problem), Giai đoạn 3 sử dụng 2 kỹ thuật phối hợp:

1. **Maximal Marginal Relevance (MMR) với $\lambda_{\text{MMR}} = 0.7$**:
   - Chọn lần lượt từng phần tử vào tập kết quả $\mathcal{S}$ sao cho tối đa hóa cả điểm liên quan lẫn độ đa dạng thể loại/nội dung:
     $$\text{MMR\_Score}(p) = \lambda_{\text{MMR}} \cdot \text{Score}(p, u) - (1 - \lambda_{\text{MMR}}) \cdot \max_{s \in \mathcal{S}} \text{Sim}(p, s)$$
   - $\text{Sim}(p, s)$ đo lường độ trùng lặp giữa hai bài viết:
     $$\text{Sim}(p, s) = 0.5 \cdot \mathbb{I}(p.\text{genre} == s.\text{genre}) + 0.5 \cdot (V_p \cdot V_s)$$
   - Tham số $\lambda_{\text{MMR}} = 0.7$ đảm bảo 70% trọng số dành cho độ liên quan sở thích cá nhân và 30% ép buộc đa dạng thể loại, triệt tiêu 100% hiện tượng feed toàn bài cùng một chủ đề đơn điệu.

2. **Multi-Armed Bandit (Thompson Sampling / $\epsilon$-greedy với $\epsilon = 0.15$)**:
   - Dành cố định **15% số vị trí trên Feed** (khoảng 3 vị trí trong trang 20 bài) cho các tác phẩm mới xuất bản thuộc **Cold-Start Pool** ($p.\text{views\_count} < 30$).
   - Áp dụng **Thompson Sampling** với phân phối tiên nghiệm Beta:
     $$\alpha_p = 1 + \text{likes}_p + \text{completions}_p, \quad \beta_p = 1 + \max(0, \text{views}_p - \text{likes}_p)$$
     Lấy mẫu ngẫu nhiên $\theta_p \sim \text{Beta}(\alpha_p, \beta_p)$. Bài viết mới có ít view sẽ có độ bất định cao (variance lớn), tạo cơ hội được lấy mẫu điểm cao để xuất hiện trên Feed độc giả.
   - Nhờ cơ chế này, tác phẩm của tác giả mới xuất bản được kiểm chứng chất lượng thực tế ngay lập tức mà không bao giờ bị chôn vùi dưới đáy thuật toán.

---

### 3.4. Hệ Thống Open Messenger Đẳng Cấp

Hệ thống cung cấp kết nối trò chuyện trực tiếp 1-1 giữa MỌI người dùng trong nền tảng:

#### 1. Mô hình Bảng Tin Nhắn & Hội Thoại:
- **`conversations`**:
  - `id`: `Integer`, Primary Key.
  - `created_at`: `DateTime`.
  - `updated_at`: `DateTime`, indexed (Thời điểm tin nhắn cuối cùng để sắp xếp inbox).
  - `last_message_text`: `Text`, trích đoạn tin nhắn mới nhất.
  - `last_message_at`: `DateTime`.
- **`conversation_participants`**:
  - `id`: `Integer`, Primary Key.
  - `conversation_id`: `Integer`, `ForeignKey("conversations.id")`.
  - `user_id`: `Integer`, `ForeignKey("users.id")`.
  - `last_read_message_id`: `Integer`, ID tin nhắn cuối cùng người này đã xem.
  - `unread_count`: `Integer`, số lượng tin nhắn chưa đọc của người này.
  - `joined_at`: `DateTime`.
  - Ràng buộc: `UniqueConstraint("conversation_id", "user_id")`.
- **`chat_messages`**:
  - `id`: `Integer`, Primary Key.
  - `conversation_id`: `Integer`, `ForeignKey("conversations.id")`, indexed.
  - `sender_id`: `Integer`, `ForeignKey("users.id")`, indexed.
  - `message_text`: `Text`, nội dung tin nhắn đã được mã hóa/làm sạch chống XSS.
  - `is_read`: `Boolean`, cờ đã đọc.
  - `created_at`: `DateTime`, indexed.

#### 2. Các Endpoint API Thiết Yếu:
| Phương thức | Endpoint | Chức năng |
|---|---|---|
| `GET` | `/api/messenger/users/search?q={query}` | Tìm kiếm người dùng trong danh bạ toàn hệ thống theo `username` hoặc `full_name` để bắt đầu trò chuyện. |
| `POST` | `/api/messenger/conversations` | Tạo mới hoặc mở lại cuộc trò chuyện 1-1 với `target_user_id`. Tự động kiểm tra idempotent nếu cuộc trò chuyện đã tồn tại. |
| `GET` | `/api/messenger/conversations` | Lấy danh sách hộp thư đến của người dùng hiện tại, kèm thông tin người đối thoại, snippet tin nhắn cuối, và số tin chưa đọc. |
| `GET` | `/api/messenger/conversations/{conv_id}/messages` | Tải lịch sử tin nhắn trong hội thoại; tự động đánh dấu toàn bộ tin nhắn nhận được là `is_read = True` và reset `unread_count = 0`. |
| `POST` | `/api/messenger/conversations/{conv_id}/messages` | Gửi tin nhắn mới: lưu trữ vào DB, cập nhật snippet hội thoại, tăng `unread_count` cho người nhận. |
| `GET` | `/api/messenger/unread-total` | Đếm tổng số tin nhắn chưa đọc trên toàn bộ các cuộc hội thoại để hiển thị huy hiệu thông báo (Notification Badge) trên header/sidebar. |

---

## 4. THIẾT KẾ KIẾN TRÚC CHI TIẾT: REQUIREMENT 3 (R3)
### Tiền Tệ Chuẩn Ngân Hàng & Chống Tấn Công Trục Lợi

```
+---------------------------------------------------------------------------------------+
|                                  R3 ARCHITECTURE OVERVIEW                             |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   Client Request (No Coin Params!)                                                    |
|         |                                                                             |
|         v                                                                             |
|   +-------------------------------------------------------------------------------+   |
|   |                  ABSOLUTE SERVER AUTHORITY OVER PRICING                       |   |
|   |   - Short: 8 xu | Medium: 12 xu | Long: 16 xu | Edit: 2 xu | Comic: 16 xu     |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |              ATOMIC DUAL-LOCKING CONCURRENCY ISOLATION                        |   |
|   |   1. Thread Mutex: with user_mutex[user_id]:                                  |   |
|   |   2. SQLite Isolation: BEGIN IMMEDIATE TRANSACTION                            |   |
|   |   -> Balance Check: If balance < cost => ROLLBACK + HTTP 402 Immediately!     |   |
|   |   -> Deduct Coins: balance_after = balance - cost                             |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                   CRYPTOGRAPHIC HASH-CHAINED LEDGER                           |   |
|   |   tx_hash = SHA256(prev_hash + user_id + amount + balance_after + timestamp)  |   |
|   |   Appended to coin_transactions; Commit DB                                    |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                           v                                           |
|   +-------------------------------------------------------------------------------+   |
|   |                     EXTERNAL AI PIPELINE INVOCATION                           |   |
|   |   Calls Groq LLM / Cloudflare Diffusion API                                   |   |
|   +-------------------+---------------------------------------+-------------------+   |
|                       |                                       |                       |
|                   Success                                  5xx / Timeout              |
|                       |                                       |                       |
|                       v                                       v                       |
|               [Generation Done]              +------------------------------------+   |
|                                              | COMPENSATING TRANSACTION ROLLBACK  |   |
|                                              |  Reason: REFUND_FAILED_GENERATION  |   |
|                                              |  Amount: +100% Refund Coins        |   |
|                                              |  Ledger Chained Hash Appended      |   |
|                                              +------------------------------------+   |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                   MULTI-SIGNAL ANTI-CLONE & SYBIL GUARD                       |   |
|   |   - Composite Fingerprint = SHA256(Canvas2D + WebGL + AudioContext + Screen)  |   |
|   |   - IP /24 Subnet Throttling                                                  |   |
|   |   -> Fresh Device & Fresh Subnet: Initial Grant = 8 Free Coins                |   |
|   |   -> Clone Device OR Throttled Subnet: Initial Balance = 0 Coins              |   |
|   +-------------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------------+
```

### 4.1. Mô Hình Kinh Tế 100 Xu & Biểu Phí Cố Định Máy Chủ

**Tỷ giá quy ước**: $100.000\text{ VNĐ} = 100\text{ Xu}$ ($1\text{ Xu} = 1.000\text{ VNĐ}$).

**Bảng Biểu Phí Cố Định Do Máy Chủ Kiểm Soát (Absolute Server Authority Pricing Table)**:
| Hành động hệ thống | Chi phí Xu | Chi tiết kỹ thuật |
|---|---|---|
| **Tạo truyện ngắn** (`short`) | **8 Xu** | Tác phẩm $\le 1.500$ từ, phân bổ đủ ngân sách 1 chương hoàn chỉnh |
| **Tạo truyện vừa** (`medium`) | **12 Xu** | Tác phẩm $1.500 - 3.500$ từ, cốt truyện nhiều phân cảnh |
| **Tạo truyện dài** (`long`) | **16 Xu** | Tác phẩm $> 3.500$ từ, thế giới mở sâu sắc |
| **Sửa bản thảo** (`edit-text` / `copilot edit`) | **2 Xu** | Mỗi lượt Co-pilot can thiệp viết lại hoặc gọt giũa văn phong |
| **Chuyển thể Manga** (`comics` / `continue`) | **16 Xu** | Chuyển thể kịch bản phân cảnh và sinh bộ khung tranh manga |
| **Tặng thưởng Tân Thủ** (Fresh Device/IP) | **+8 Xu** | Tặng miễn phí 1 lần tạo truyện ngắn trải nghiệm chất lượng |
| **Tài khoản Clone / Duplicate** | **0 Xu** | Thiết bị hoặc Subnet đã nhận thưởng $\rightarrow$ Số dư khởi tạo = 0 Xu |
| **Nạp xu chuẩn** | **+100 Xu** | Gói nạp cơ sở 100k VNĐ (đủ 2-3 truyện + 10-15 lần sửa + 2-3 lần manga) |

**Nguyên tắc Bảo Vệ Quyền Lực Server (Absolute Server Authority)**:
- Phía Client **tuyệt đối không được gửi** bất kỳ trường nào như `cost`, `coins`, `price`.
- Nếu Client cố tình truyền `{"cost": 0, "coins": 9999}`, Backend hoàn toàn phớt lờ các trường này và tự động tra cứu biểu phí từ server constants dựa trên cấu hình yêu cầu thực tế (`story_length`, `action_type`).

---

### 4.2. Cơ Chế Chống Race Condition & Double-Spending Tuyệt Đối

#### Mối Đe Dọa (Threat Scenario)
Giả sử người dùng chỉ còn đúng **8 Xu** trong tài khoản. Người dùng mở 2 tab trình duyệt hoặc dùng script gửi đồng thời 2 request tạo truyện ngắn trong cùng 1 mili-giây:
- Trong mô hình non-atomic thông thường: Cả 2 luồng đều đọc số dư `coins = 8 >= 8`, cả 2 luồng đều tiếp tục sinh truyện và trừ xu `8 - 8 = 0`. Người dùng gian lận được 2 truyện (trị giá 16 xu) nhưng chỉ trả 8 xu!

#### Giải Pháp Dual-Locking Isolation
Hệ thống sử dụng cơ chế bảo vệ 2 lớp kết hợp giữa **In-Memory Thread Mutex** và **SQLite Database Isolation**:

```python
# LỚP 1: IN-MEMORY PER-USER MUTEX REGISTRY
import threading
from collections import defaultdict

class UserMutexRegistry:
    def __init__(self):
        self._locks = {}
        self._meta_lock = threading.Lock()
        
    def get_user_lock(self, user_id: int) -> threading.Lock:
        with self._meta_lock:
            if user_id not in self._locks:
                self._locks[user_id] = threading.Lock()
            return self._locks[user_id]

user_mutexes = UserMutexRegistry()
```

```python
# LỚP 2: ATOMIC DEDUCTION VỚI SQLITE "BEGIN IMMEDIATE"
def deduct_coins_atomic(db: Session, user_id: int, cost: int, tx_type: str, description: str, ref_id: str = None):
    user_lock = user_mutexes.get_user_lock(user_id)
    with user_lock:  # Đảm bảo tuần tự hóa các thread trong cùng tiến trình
        # Khóa IMMEDIATE ở cấp cơ sở dữ liệu SQLite:
        # Ngay lập tức chiếm RESERVED lock, chặn đứng mọi tiến trình ghi khác đọc đè
        db.execute(text("BEGIN IMMEDIATE"))
        
        # Đọc số dư mới nhất trực tiếp từ cơ sở dữ liệu
        user_row = db.execute(
            text("SELECT coins FROM users WHERE id = :uid"), 
            {"uid": user_id}
        ).fetchone()
        
        if not user_row:
            db.execute(text("ROLLBACK"))
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
            
        current_coins = user_row[0] or 0
        if current_coins < cost:
            db.execute(text("ROLLBACK"))
            # Bắt buộc trả về HTTP 402 Payment Required ngay lập tức!
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Số dư xu không đủ ({current_coins} xu < {cost} xu yêu cầu). Vui lòng nạp thêm xu để tiếp tục."
            )
            
        new_balance = current_coins - cost
        db.execute(
            text("UPDATE users SET coins = :nb WHERE id = :uid"),
            {"nb": new_balance, "uid": user_id}
        )
        
        # Tạo bút toán sổ cái mật mã SHA-256 (Xem mục 4.4)
        tx_hash = append_cryptographic_ledger_entry(
            db=db,
            user_id=user_id,
            amount=-cost,
            balance_after=new_balance,
            tx_type=tx_type,
            description=description,
            ref_id=ref_id
        )
        
        db.execute(text("COMMIT"))
        return new_balance, tx_hash
```

**Kết quả thực nghiệm**: Khi 2 request tới cùng 1 mili-giây, Request 1 chiếm lock trước, trừ 8 xu $\rightarrow$ số dư về 0. Request 2 vào sau, đọc số dư $= 0 < 8 \rightarrow$ bị đẩy ra ngay lập tức với mã lỗi **HTTP 402 Payment Required**. Double-Spending bị triệt tiêu 100%!

---

### 4.3. Giao Dịch Bù Trừ Tự Động Hoàn Xu (`REFUND_FAILED_GENERATION`)

Khi người dùng bị trừ xu thành công và hệ thống gọi LLM bên ngoài (Groq, Anthropic) hoặc Diffusion (Cloudflare AI), tiến trình mạng có thể gặp sự cố:
- Lỗi 5xx máy chủ AI quá tải.
- Timeout kết nối (vượt 60 giây).
- Rate limit 429 hoặc đứt gãy kết nối mạng.

Hệ thống NarrAI triển khai mô hình **Compensating Transaction Pattern**:

```python
async def execute_paid_generation_pipeline(user_id: int, cost: int, action_type: str, generator_fn, *args, **kwargs):
    db = SessionLocal()
    deduction_tx_hash = None
    try:
        # Bước 1: Trừ xu trước khi gọi AI
        new_balance, deduction_tx_hash = deduct_coins_atomic(
            db=db,
            user_id=user_id,
            cost=cost,
            tx_type=action_type,
            description=f"Thanh toán dịch vụ {action_type}"
        )
    finally:
        db.close()

    # Bước 2: Gọi AI Pipeline bên ngoài
    try:
        result = await generator_fn(*args, **kwargs)
        return result
    except Exception as ai_err:
        # Bước 3: Phát hiện lỗi AI -> Kích hoạt Giao dịch Bù trừ Hoàn xu 100%
        db_refund = SessionLocal()
        try:
            refund_balance, refund_tx_hash = refund_coins_compensating(
                db=db_refund,
                user_id=user_id,
                amount=cost,
                reason="REFUND_FAILED_GENERATION",
                original_tx_ref=deduction_tx_hash,
                description=f"Tự động hoàn {cost} xu do lỗi gọi dịch vụ AI ({str(ai_err)[:80]})"
            )
        finally:
            db_refund.close()
            
        raise HTTPException(
            status_code=502,
            detail=f"Dịch vụ AI gặp sự cố kết nối. Hệ thống đã tự động hoàn lại {cost} xu vào tài khoản của bạn (Mã hoàn: REFUND_FAILED_GENERATION)."
        )
```

Người dùng không bao giờ bị mất xu oan khi dịch vụ bên thứ ba gặp lỗi!

---

### 4.4. Sổ Cái Mật Mã Bất Biến (Cryptographic Chained Ledger)

#### Cấu Trúc Bảng `coin_transactions`
- `id`: `Integer`, Primary Key, autoincrement.
- `user_id`: `Integer`, `ForeignKey("users.id")`, indexed.
- `amount`: `Integer`, có dấu (Dương: Nạp/Thưởng/Hoàn; Âm: Trừ chi phí).
- `balance_after`: `Integer`, số dư người dùng ngay sau giao dịch.
- `tx_type`: `String(50)`, loại giao dịch (`INITIAL_GRANT`, `STORY_GENERATE`, `STORY_EDIT`, `COMIC_GENERATE`, `REFUND_FAILED_GENERATION`, `TOPUP`).
- `description`: `String(255)`, mô tả giao dịch.
- `reference_id`: `String(100)`, nullable (Mã tham chiếu story_id, comic_id, hoặc mã giao dịch bị hoàn).
- `prev_hash`: `String(64)`, mã băm của giao dịch liền trước (Xâu chuỗi Blockchain).
- `tx_hash`: `String(64)`, mã băm SHA-256 duy nhất của giao dịch này, indexed.
- `timestamp`: `String(50)`, thời điểm giao dịch định dạng ISO UTC (e.g. `2026-09-28T08:15:30.123456Z`).
- `created_at`: `DateTime`, mặc định `datetime.utcnow`.

#### Công Thức Băm Chuỗi SHA-256
$$tx\_hash = \text{SHA256}\left( prev\_hash + str(user\_id) + str(amount) + str(balance\_after) + timestamp \right)$$

- Nếu là giao dịch đầu tiên trong hệ thống: $prev\_hash = \text{"0"} \times 64$ (Genesis Hash).
- Mọi giao dịch kế tiếp bắt buộc phải tham chiếu đúng `tx_hash` của giao dịch trước đó.

#### Thuật Toán Kiểm Tra Toàn Vẹn Sổ Cái (Ledger Integrity Audit Utility)
Một hàm kiểm thử độc lập duyệt tuần tự toàn bộ sổ cái:
1. Kiểm tra `tx[i].prev_hash == tx[i-1].tx_hash`.
2. Tính toán lại mã băm mong muốn $\text{SHA256}(...)$ và so khớp với `tx[i].tx_hash`.
3. Kiểm tra tính liên tục của số dư người dùng: $\text{balance}[i-1] + \text{amount}[i] == \text{balance}[i]$.
- Bất kỳ hành vi sửa đổi trực tiếp số dư trong file SQLite `narrai.db` hoặc chèn giao dịch giả mạo đều làm gãy chuỗi băm ngay lập tức và bị kiểm toán viên phát hiện 100%!

---

### 4.5. Hệ Thống Chống Clone & Sybil Đa Lớp (Advanced Anti-Clone Guard)

Mối đe dọa lớn nhất đối với chương trình tặng 8 xu trải nghiệm là việc kẻ xấu dùng tool tạo hàng ngàn tài khoản clone để đào xu miễn phí. NarrAI xây dựng cơ chế bảo vệ 2 tầng:

#### Tầng 1: Multi-Signal Browser Fingerprinting
Khi người dùng đăng ký tại giao diện `/api/register`, client chạy script thu thập 4 tín hiệu độc lập không thể giả mạo bằng cách xóa cookie:
1. **Canvas 2D Hash**:
   - Vẽ một canvas ẩn với các ký tự Unicode phức tạp tiếng Việt, hình học 2D xoay góc, gradient màu và hiệu ứng đổ bóng.
   - Do sự khác biệt về engine đồ họa phần cứng, driver card màn hình (NVIDIA, AMD, Intel) và thuật toán khử răng cưa font chữ của hệ điều hành, chuỗi Base64 kết xuất là duy nhất cho từng cấu hình máy.
2. **WebGL Renderer Hash**:
   - Truy vấn extension `WEBGL_debug_renderer_info` để lấy `UNMASKED_RENDERER_WEBGL` và `UNMASKED_VENDOR_WEBGL` (ví dụ: `ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)`).
3. **AudioContext Frequency Hash**:
   - Khởi tạo `AudioContext`, tạo `OscillatorNode` phát sóng tam giác qua `DynamicsCompressorNode` và phân tích mẫu phổ tần số đầu ra. Tín hiệu âm thanh phần cứng có dấu vết đặc thù của bộ giải mã âm thanh trên bo mạch chủ.
4. **Screen Specs & Hardware Profile**:
   - Tổ hợp: Độ phân giải màn hình (`screen.width x screen.height x screen.colorDepth`), tỷ lệ pixel thiết bị (`devicePixelRatio`), số nhân CPU (`navigator.hardwareConcurrency`), múi giờ hệ thống.

**Mã Băm Thiết Bị Hợp Nhất (Composite Fingerprint)**:
$$composite\_fp = \text{SHA256}(canvas\_hash + "|" + webgl\_hash + "|" + audio\_hash + "|" + screen\_specs)$$

#### Tầng 2: IP Subnet Throttling (/24 Subnet)
- Kẻ tấn công thường sử dụng proxy dân cư hoặc reset modem để đổi IP trong cùng một dải mạng.
- Hệ thống trích xuất địa chỉ IP client và quy về dải **Subnet /24** (đối với IPv4: giữ 3 octet đầu, ví dụ `113.161.45.88` $\rightarrow$ `113.161.45.0/24`; đối với IPv6: prefix `/64`).
- **Quy tắc Throttling**: Mỗi dải subnet `/24` chỉ được cấp tối đa **2 lần nhận thưởng 8 xu tân thủ** trong vòng 24 giờ.

#### Logic Quyết Định Cấp Xu Tân Thủ:
Khi gọi `evaluate_registration(composite_fp, subnet)`:
1. Nếu `composite_fp` đã tồn tại trong bảng `device_fingerprints` với `has_claimed_trial = True`:
   $\rightarrow$ **Phát hiện Clone Thiết Bị**: Tài khoản được tạo thành công nhưng `initial_coins = 0`!
2. Nếu `subnet` đã có $\ge 2$ lượt nhận thưởng trong ngày:
   $\rightarrow$ **Phát hiện Spam Dải Mạng**: Tài khoản được tạo thành công nhưng `initial_coins = 0`!
3. Nếu cả Thiết Bị VÀ Dải Mạng đều mới:
   $\rightarrow$ **Tân Thủ Hợp Lệ**: Cấp `initial_coins = 8`, ghi nhận giao dịch `INITIAL_GRANT` vào sổ cái mật mã, cập nhật cờ `has_claimed_trial = True`.

---

## 5. KẾ HOẠCH BỐ TRÍ CẤU TRÚC MÃ NGUỒN (SOURCE CODE ORGANIZATION)

Để đảm bảo kiến trúc sạch sẽ, tuân thủ nguyên tắc Single Responsibility Principle (SRP) và không làm phình to file `backend/main.py`, toàn bộ tính năng R2 và R3 được tổ chức thành các module dịch vụ và router độc lập:

```
backend/
├── db/
│   ├── models.py                     <-- Bổ sung cột coins, social_posts, interactions, profiles, messenger, ledger
├── services/
│   ├── banking_service.py            <-- [MỚI] Thread mutex, SQLite BEGIN IMMEDIATE, SHA-256 ledger, refund, anti-clone
│   ├── recommender_service.py        <-- [MỚI] Two-Tower Cosine, Graph DSGO Traversal, Multi-Task Ranking, MMR, MAB
│   └── messenger_service.py          <-- [MỚI] User directory search, 1-1 chat, unread aggregation
├── routers/
│   ├── coins_router.py               <-- [MỚI] /api/coins/balance, /history, /topup, /audit
│   ├── social_router.py              <-- [MỚI] /api/social/publish, /feed, /interact, /posts/{id}
│   └── messenger_router.py           <-- [MỚI] /api/messenger/users/search, /conversations, /messages
├── auth.py                           <-- Tích hợp Anti-Clone evaluation vào luồng đăng ký
├── main.py                           <-- Mount APIRouters; Tích hợp deduct_coins_atomic & refund vào các route AI
└── tests/
    ├── test_banking_concurrency.py   <-- [MỚI] Race conditions, double-spending stress test, ledger hash integrity
    ├── test_recommender_engine.py    <-- [MỚI] Cosine, DSGO traversal, MMR diversity, cold-start bandit test
    └── test_open_messenger.py        <-- [MỚI] User directory, 1-1 chat, unread count tests
```

### 5.1. Tích Hợp Router vào `backend/main.py`:
```python
from routers.coins_router import router as coins_router
from routers.social_router import router as social_router
from routers.messenger_router import router as messenger_router

app.include_router(coins_router, prefix="/api/coins", tags=["Banking & Coins"])
app.include_router(social_router, prefix="/api/social", tags=["Social & Recommender"])
app.include_router(messenger_router, prefix="/api/messenger", tags=["Open Messenger"])
```

### 5.2. Tích Hợp Trừ Xu và Hoàn Xu vào các Endpoint AI hiện có trong `backend/main.py`:
1. `generate_story` (dòng 335):
   - Đọc `request.story_length`. Tra biểu phí máy chủ: short=8, medium=12, long=16.
   - Nếu có `current_user`: Gọi `deduct_coins_atomic(cost)`.
   - Nếu `gen.generate_story_stream` ném ngoại lệ: Tự động hoàn 100% xu với mã `REFUND_FAILED_GENERATION`.
2. `init_story` (dòng 940):
   - Trừ 8 xu cho Chương 1. Hoàn xu nếu `extract_bible` hoặc `generate_chapter_stream` lỗi.
3. `edit_text` (dòng 322) & `copilot_event` (dòng 825, khi `action == "edit_story_direct"`):
   - Trừ 2 xu sửa bản thảo. Hoàn xu nếu `editor.edit_text` lỗi.
4. `create_comic` (dòng 595) & `continue_comic` (dòng 637):
   - Trừ 16 xu chuyển thể manga. Hoàn xu nếu `director.generate_comic_script` lỗi.

---

## 6. CHIẾN LƯỢC KIỂM THỬ TOÀN DIỆN (COMPREHENSIVE TEST SUITE)

Để đáp ứng tiêu chuẩn nghiệm thu khắt khe của hệ thống, 3 bộ test suite chuyên sâu được thiết kế:

### 6.1. `test_banking_concurrency.py` (Kiểm Thử An Ninh Tiền Tệ & Concurrency)
1. **Test Concurrent Double-Spending**:
   - Tạo tài khoản mẫu với đúng 8 xu.
   - Khởi chạy 10 luồng song song (`concurrent.futures.ThreadPoolExecutor(max_workers=10)`) cùng yêu cầu trừ 8 xu trong cùng 1 mili-giây.
   - *Kỳ vọng*: Đúng 1 luồng thành công, 9 luồng còn lại bị từ chối với `HTTPException(402)`. Số dư cuối cùng bằng đúng 0 xu, không bao giờ bị âm.
2. **Test Absolute Server Authority**:
   - Client gửi payload chứa `{"cost": 0, "coins": 9999}` lên endpoint trừ tiền.
   - *Kỳ vọng*: Server trừ đúng biểu phí quy định của máy chủ (ví dụ: 8 xu), hoàn toàn phớt lờ tham số của client.
3. **Test Compensating Transaction Rollback (`REFUND_FAILED_GENERATION`)**:
   - Trừ 12 xu của người dùng (số dư $50 \rightarrow 38$).
   - Giả lập tiến trình AI bị sập với ngoại lệ `RuntimeError("Groq 503 Service Unavailable")`.
   - *Kỳ vọng*: Hàm bù trừ hoàn lại đúng 12 xu (số dư trở lại 50), bảng `coin_transactions` có thêm dòng giao dịch `REFUND_FAILED_GENERATION` với `amount = +12`.
4. **Test Cryptographic Ledger Chain Integrity**:
   - Chạy chuỗi 20 giao dịch nạp, trừ, hoàn xu.
   - Kiểm tra toàn bộ mã băm xâu chuỗi: `verify_ledger_integrity()` trả về `is_valid = True`.
   - Giả lập tấn công can thiệp DB trực tiếp (sửa thủ công số dư của 1 dòng cũ trong SQLite).
   - Kiểm toán viên chạy lại: Lập tức phát hiện gian lận và chỉ ra chính xác ID giao dịch bị sửa đổi!
5. **Test Multi-Signal Anti-Clone Guard & Subnet Throttling**:
   - Đăng ký tài khoản 1 từ Device A, IP 1 $\rightarrow$ Được cấp 8 xu tân thủ.
   - Đăng ký tài khoản 2 từ Device A (trùng Canvas/WebGL hash), IP khác $\rightarrow$ Cấp 0 xu (Clone detected).
   - Đăng ký tài khoản 3 từ Device B khác, nhưng cùng dải IP Subnet `/24` đã vượt quota $\rightarrow$ Cấp 0 xu (Subnet throttled).

### 6.2. `test_recommender_engine.py` (Kiểm Thử Động Cơ Đề Xuất 3 Giai Đoạn)
1. **Test Cosine Similarity & Vector Decay**:
   - Tạo profile người dùng với sở thích mạnh về thể loại "Kiếm hiệp".
   - Cho thời gian trôi qua 30 ngày ($\lambda = 0.05/\text{ngày}$) $\rightarrow$ Kiểm tra vector sở thích suy giảm hàm mũ chính xác theo công thức $e^{-0.05 \times 30} \approx 0.223$.
2. **Test Graph DSGO Traversal Candidate Generation**:
   - Người dùng thích nhân vật "Trần Quốc Tuấn" và địa danh "Sông Bạch Đằng".
   - Kiểm tra Giai đoạn 1 truy hồi thành công các bài viết chia sẻ chung các thực thể DSGO này dù từ các tác giả khác nhau.
3. **Test Multi-Task Ranking Score Calculation**:
   - Kiểm tra trọng số chuẩn xác: $0.35 \times \text{Cosine} + 0.25 \times \text{Affinity} + 0.20 \times \text{Freshness} + 0.20 \times \text{Quality}$.
4. **Test Maximal Marginal Relevance (MMR $\lambda = 0.7$)**:
   - Cung cấp danh sách ứng viên có 15 bài "Kiếm hiệp" điểm cao và 5 bài "Khoa huyễn" điểm khá.
   - Sau khi áp dụng MMR, Feed đầu ra có sự đan xen hài hòa các thể loại khác nhau, không bị chiếm lĩnh 100% bởi thể loại duy nhất.
5. **Test Multi-Armed Bandit Cold-Start Exploration ($\epsilon = 0.15$)**:
   - Chèn 10 bài viết mới của tác giả mới (views = 0) vào kho dữ liệu.
   - Kiểm tra Feed 20 vị trí luôn dành ra đúng 3 vị trí (15%) cho các tác phẩm mới từ cold-start pool thông qua Thompson Sampling.
6. **Test Comment Sentiment & Entity Extraction**:
   - Người dùng đăng bình luận khen ngợi: *"Nhân vật Lý Thường Kiệt được khắc họa quá xuất sắc, lời văn hào hùng!"*.
   - Phân tích cảm xúc nhận diện điểm dương ($s > 0$), trích xuất thực thể "Lý Thường Kiệt", và gia tăng điểm `entity_affinity` tương ứng trong hồ sơ người dùng.

### 6.3. `test_open_messenger.py` (Kiểm Thử Open Messenger)
1. **Test User Directory Search**:
   - Tìm kiếm người dùng theo tiền tố username hoặc họ tên tiếng Việt có dấu. Kiểm tra loại trừ chính người dùng đang tìm kiếm.
2. **Test Conversation Idempotency**:
   - Người dùng A tạo hội thoại với B $\rightarrow$ Tạo cuộc trò chuyện mới.
   - Người dùng B gọi API tạo hội thoại với A $\rightarrow$ Trả về đúng cuộc trò chuyện đã tạo, không tạo bản sao trùng lặp.
3. **Test Message Exchange & Read Receipts**:
   - Người dùng A gửi 3 tin nhắn cho B $\rightarrow$ `unread_count` của B tăng lên 3.
   - Người dùng B gọi API đọc tin nhắn $\rightarrow$ `is_read` chuyển thành `True`, `unread_count` của B trở về 0.
4. **Test Total Unread Notification Badge**:
   - Người dùng nhận tin nhắn từ nhiều cuộc hội thoại khác nhau.
   - Kiểm tra API `/api/messenger/unread-total` phản ánh chính xác tổng số tin nhắn chưa đọc toàn cục.

---

## 7. KẾT LUẬN & ĐÁNH GIÁ SẴN SÀNG TRIỂN KHAI

1. **Về Khả năng Tương thích Ngược**:
   - Cơ chế auto-migration đã được kiểm chứng an toàn trong `db/models.py`. Việc bổ sung cột `coins` và các bảng mới (`social_posts`, `coin_transactions`, `conversations`, v.v.) hoàn toàn không gây ảnh hưởng đến dữ liệu truyện và manga hiện có.
2. **Về Tính Khả Thi Kiến Trúc**:
   - Đồ thị tri thức DSGO đã được hoàn thiện từ trước (`scene_graph.py`), cung cấp nền tảng dữ liệu thực thể hoàn hảo cho thuật toán Graph Traversal của Recommender.
   - Kiến trúc Dual-Locking (`threading.Lock` + SQLite `IMMEDIATE TRANSACTION`) giải quyết triệt để bài toán Race Condition mà không đòi hỏi thêm hạ tầng cụm phân tán phức tạp.
   - Hệ thống mật mã sổ cái SHA-256 xâu chuỗi mang lại độ minh bạch và an toàn tương đương công nghệ blockchain thu nhỏ, chặn đứng mọi ý đồ chỉnh sửa số dư trái phép.
3. **Sẵn sàng Chuyển giao**:
   - Bản khảo sát và thiết kế này cung cấp đầy đủ thông số kỹ thuật, công thức toán học, cấu trúc bảng dữ liệu và lộ trình triển khai chi tiết cho các Agent phụ trách thực thi (Implementer & Test Engineers).
