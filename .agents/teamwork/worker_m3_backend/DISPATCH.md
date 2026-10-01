## 2026-10-01T06:51:33Z
You are worker_m3_backend.
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m3_backend
You exclusively own and modify:
1. backend/db/models.py
2. backend/routers/social_router.py
3. backend/tests/test_round6_social_features.py

MANDATORY FIRST STEP:
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md before doing any work.
Also read backend/tests/test_round6_social_features.py to understand the exact schema and test contracts.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Implementation Requirements:
1. In backend/db/models.py:
   - Define and export the models required by Milestone 3 (Features 16-22):
     - `Follow`: id (PK), follower_id (FK users.id), following_id (FK users.id), created_at (DateTime, default datetime.utcnow), UniqueConstraint("follower_id", "following_id")
     - `Bookmark`: id (PK), user_id (FK users.id), post_id (FK social_posts.id), category (String(100), default="Yêu thích"), tags (Text, default="[]"), notes (Text, nullable=True), created_at (DateTime), UniqueConstraint("user_id", "post_id")
     - `Notification`: id (PK), recipient_id (FK users.id), sender_id (FK users.id), notification_type (String(50)), post_id (FK social_posts.id, nullable=True), comment_id (Integer, nullable=True), conversation_id (Integer, nullable=True), content (Text, nullable=True), is_read (Boolean, default=False), created_at (DateTime)
     - `ContentReport`: id (PK), reporter_id (FK users.id), post_id (FK social_posts.id, nullable=True), target_user_id (FK users.id, nullable=True), report_reason (String(50)), details (Text, nullable=True), status (String(30), default="PENDING"), created_at (DateTime)
     - `AuthorProfile`: id (PK), user_id (FK users.id, unique=True), bio (Text, default=""), avatar_url (String(500), nullable=True), cover_url (String(500), nullable=True), genres (Text, default="[]"), followers_count (Integer, default=0), following_count (Integer, default=0), works_count (Integer, default=0), total_likes (Integer, default=0), created_at, updated_at
     - In `PostInteraction`: ensure `parent_comment_id` column exists:
       `parent_comment_id = Column(Integer, ForeignKey("post_interactions.id"), nullable=True)`
   - Make sure all these classes are imported in `__all__` or available at top-level so `from db.models import Follow, Bookmark, Notification, ContentReport, AuthorProfile` imports cleanly and `HAS_M3_MODELS = True`.

2. In backend/routers/social_router.py:
   - Implement the complete REST APIs for the social graph:
     - Follow / Unfollow:
       - `POST /api/social/follow/{user_id}`
       - `POST /api/social/unfollow/{user_id}`
       - `feed_type="following"` query in `GET /api/social/feed` filtering by authors the user follows
     - Threaded Comments:
       - In `POST /api/social/interact`: support `parent_comment_id` when interaction_type="COMMENT"
       - In `GET /api/social/post/{post_id}`: return comments including `parent_comment_id`
     - Bookmarks / Personal Library:
       - `POST /api/social/bookmark` (accepts post_id, category, tags, notes)
       - `DELETE /api/social/bookmark/{post_id}`
       - `GET /api/social/bookmarks` (with optional `category` filter)
     - Notifications:
       - `GET /api/social/notifications` (returns notifications list & unread_count)
       - `POST /api/social/notifications/{notification_id}/read`
       - `POST /api/social/notifications/read-all`
     - Content Reports:
       - `POST /api/social/report` (accepts post_id, report_reason, details)
       - `GET /api/social/reports` (admin/mod endpoint)
       - `POST /api/social/report/{report_id}/resolve`
     - Author Profiles:
       - `GET /api/social/profile/{user_id}` (retrieves author profile with bio, stats, and works)
       - `PUT /api/social/profile` (updates authenticated user profile)
     - Trending Leaderboard:
       - `GET /api/social/trending?period=weekly|monthly`
       - Implements time-decayed velocity formula:
         `Score = (3*likes + 5*comments + 0.5*views + 4*completions) / ((age_in_hours + 2) ** 1.4)`
       - Filters posts within 7 days for weekly, 30 days for monthly, ordered by score descending.

3. Verification:
   - Run: `python -m py_compile backend/db/models.py backend/routers/social_router.py`
   - Run: `python -m unittest backend/tests/test_round6_social_features.py` (Must pass all 16 tests!).
   - Run: `python -m unittest backend/tests/test_round6_wal_performance.py` and `test_round6_e2e_integration.py` to ensure no database regressions.
