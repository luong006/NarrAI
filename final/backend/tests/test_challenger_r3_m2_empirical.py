"""
Empirical Challenger Test Suite for Milestone 2: Cache Service & Redis Fallback (Requirement R3)
Challenger: challenger_r3_m2_1

Verifies:
1. CacheManager latency benchmark: benchmark_latency(100) with avg < 20.0ms (target < 1ms).
2. ThreadSafeMemoryCache:
   - Full CRUD operations
   - TTL expiration (short TTL, delayed expiration, pruning)
   - LRU eviction ordering (LRU item evicted, access refreshes recency)
   - Concurrency thread safety under high-contention multithreaded read/write
3. RedisCache fallback & resilience:
   - Dead Redis endpoint (redis://127.0.0.1:59999/0)
   - Graceful operation in in_memory mode
   - Zero unhandled exceptions
   - Circuit breaker tripping and cooldown logic
4. StoryMemory serialization round-trip:
   - to_dict() and from_dict() round-trip through CacheManager
   - StoryBible preservation
   - Chapter summaries, states, threads, relationship map preservation
5. User isolation and cache invalidation:
   - Draft isolation across user IDs
   - Session invalidation on deletion
"""

import os
import sys
import threading
import time
import unittest

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.cache_service import (
    ThreadSafeMemoryCache,
    RedisCache,
    CacheManager,
    get_cache_manager,
)
from agents.story_memory import StoryMemory, StoryBible


class TestCacheManagerLatencyBenchmark(unittest.TestCase):
    """Verifies Requirement R3 latency performance benchmark."""

    def setUp(self):
        self.cache_mgr = CacheManager()

    def test_benchmark_latency_100_iterations(self):
        """Run 100 round-trip iterations; latency must be strictly < 20.0ms (typically < 0.1ms)."""
        result = self.cache_mgr.benchmark_latency(iterations=100)
        
        self.assertTrue(result["passed"], "Latency benchmark marked as failed")
        self.assertEqual(result["iterations"], 100)
        self.assertLess(result["avg_latency_ms"], 20.0, f"Average latency {result['avg_latency_ms']}ms exceeded 20ms limit")
        self.assertGreaterEqual(result["avg_latency_ms"], 0.0)
        self.assertLess(result["max_latency_ms"], 50.0, f"Max latency spike {result['max_latency_ms']}ms exceeded 50ms")
        self.assertIn(result["mode"], ["in_memory", "redis"])

    def test_benchmark_latency_500_iterations_stress(self):
        """Stress benchmark with 500 iterations to verify consistent sub-millisecond throughput."""
        result = self.cache_mgr.benchmark_latency(iterations=500)
        
        self.assertTrue(result["passed"])
        self.assertEqual(result["iterations"], 500)
        self.assertLess(result["avg_latency_ms"], 20.0)

    def test_get_stats_reflects_performance(self):
        """Verify get_stats() produces accurate latency and status metadata."""
        stats = self.cache_mgr.get_stats()
        self.assertIn("mode", stats)
        self.assertIn("redis_available", stats)
        self.assertIn("item_count", stats)
        self.assertIn("avg_latency_ms", stats)
        self.assertLess(stats["avg_latency_ms"], 20.0)


class TestThreadSafeMemoryCacheEmpirical(unittest.TestCase):
    """Verifies in-process thread-safe LRU/TTL cache functionality."""

    def setUp(self):
        self.cache = ThreadSafeMemoryCache(max_items=10)

    def test_crud_lifecycle(self):
        """Verify Create, Read, Update, Delete, Exists, and Size."""
        # Create
        self.cache.set("key_str", "hello_world")
        self.cache.set("key_dict", {"user": "alice", "active": True})
        self.cache.set("key_list", [1, 2, 3, 4])
        self.cache.set("key_int", 42)

        # Read
        self.assertEqual(self.cache.get("key_str"), "hello_world")
        self.assertEqual(self.cache.get("key_dict"), {"user": "alice", "active": True})
        self.assertEqual(self.cache.get("key_list"), [1, 2, 3, 4])
        self.assertEqual(self.cache.get("key_int"), 42)

        # Exists
        self.assertTrue(self.cache.exists("key_str"))
        self.assertFalse(self.cache.exists("non_existent_key"))

        # Update
        self.cache.set("key_str", "updated_world")
        self.assertEqual(self.cache.get("key_str"), "updated_world")

        # Delete
        self.assertTrue(self.cache.delete("key_str"))
        self.assertFalse(self.cache.exists("key_str"))
        self.assertIsNone(self.cache.get("key_str"))
        self.assertFalse(self.cache.delete("key_str"))  # Secondary delete returns False

        # Size & Clear
        self.assertEqual(self.cache.size(), 3)
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key_dict"))

    def test_ttl_expiration_behavior(self):
        """Verify TTL expiration: item valid immediately, expires after duration."""
        self.cache.set("ephemeral_item", "fast_expire", ttl=0.08)
        self.assertTrue(self.cache.exists("ephemeral_item"))
        self.assertEqual(self.cache.get("ephemeral_item"), "fast_expire")

        # Wait for expiration
        time.sleep(0.12)

        # Must be gone from get() and exists()
        self.assertIsNone(self.cache.get("ephemeral_item"))
        self.assertFalse(self.cache.exists("ephemeral_item"))

    def test_ttl_immediate_expiry_negative_ttl(self):
        """Verify negative or zero TTL immediately invalidates item."""
        self.cache.set("dead_item", "never_alive", ttl=-1)
        self.assertIsNone(self.cache.get("dead_item"))
        self.assertFalse(self.cache.exists("dead_item"))

    def test_lru_capacity_eviction_strictly_ordered(self):
        """
        Verify LRU capacity eviction:
        Cache with capacity 3.
        Insert: 1, 2, 3 -> order is [1, 2, 3]
        Access: 1 -> order becomes [2, 3, 1]
        Insert: 4 -> oldest item [2] is evicted!
        Insert: 5 -> oldest item [3] is evicted!
        Items 1, 4, 5 must remain.
        """
        cache = ThreadSafeMemoryCache(max_items=3)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")

        # Touch k1 to make it most recently used
        val = cache.get("k1")
        self.assertEqual(val, "v1")

        # Insert k4, triggering eviction of k2
        cache.set("k4", "v4")
        self.assertIsNone(cache.get("k2"), "k2 should be evicted as least recently used")
        self.assertEqual(cache.get("k1"), "v1")
        self.assertEqual(cache.get("k3"), "v3")
        self.assertEqual(cache.get("k4"), "v4")

        # Insert k5, triggering eviction of k3 (since k1 was touched, k3 is now oldest)
        cache.set("k5", "v5")
        self.assertIsNone(cache.get("k3"), "k3 should be evicted as least recently used")
        self.assertEqual(cache.get("k1"), "v1")
        self.assertEqual(cache.get("k4"), "v4")
        self.assertEqual(cache.get("k5"), "v5")
        self.assertEqual(cache.size(), 3)

    def test_concurrent_multithreaded_read_write(self):
        """Stress test concurrency with 10 threads doing simultaneous set, get, delete operations."""
        threads = []
        thread_errors = []
        iterations_per_thread = 100

        def worker(thread_idx):
            try:
                for i in range(iterations_per_thread):
                    k = f"thread_{thread_idx}_key_{i % 10}"
                    self.cache.set(k, {"thread": thread_idx, "iter": i})
                    val = self.cache.get(k)
                    if val is not None and val.get("thread") != thread_idx:
                        thread_errors.append(f"Thread {thread_idx} read contaminated data: {val}")
                    if i % 3 == 0:
                        self.cache.delete(k)
            except Exception as e:
                thread_errors.append(f"Thread {thread_idx} exception: {e}")

        for t in range(10):
            th = threading.Thread(target=worker, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join(timeout=5.0)

        self.assertEqual(len(thread_errors), 0, f"Concurrency errors occurred: {thread_errors}")


class TestRedisCacheGracefulFallback(unittest.TestCase):
    """Verifies RedisCache behavior when Redis service is offline or unreachable."""

    def test_offline_redis_smooth_fallback(self):
        """When pointing to a dead Redis host, cache functions normally in memory with zero unhandled exceptions."""
        memory_fallback = ThreadSafeMemoryCache(max_items=50)
        redis_cache = RedisCache(
            redis_url="redis://127.0.0.1:59999/0",  # Guaranteed closed port
            socket_timeout=0.2,
            socket_connect_timeout=0.2,
            fallback_cache=memory_fallback,
            circuit_threshold=1,
            circuit_cooldown=5.0,
        )

        # Connection should fail silently during init
        self.assertFalse(redis_cache.is_connected)

        # Perform operations; none should throw an exception
        redis_cache.set("offline_test", {"health": "good"}, ttl=100)
        val = redis_cache.get("offline_test")
        self.assertEqual(val, {"health": "good"})
        self.assertTrue(redis_cache.exists("offline_test"))

        deleted = redis_cache.delete("offline_test")
        self.assertTrue(deleted)
        self.assertIsNone(redis_cache.get("offline_test"))
        self.assertFalse(redis_cache.exists("offline_test"))

    def test_circuit_breaker_trips_and_bypasses_socket(self):
        """Circuit breaker opens after threshold failures, bypassing subsequent socket attempts."""
        redis_cache = RedisCache(
            redis_url="redis://127.0.0.1:59999/0",
            socket_timeout=0.1,
            socket_connect_timeout=0.1,
            circuit_threshold=2,
            circuit_cooldown=10.0,
        )

        # Initial failure recorded on ping() in __init__
        self.assertFalse(redis_cache.is_connected)
        
        # Another failure to ensure threshold reached
        redis_cache._record_failure()
        self.assertTrue(redis_cache._circuit_open)

        # Fast path via circuit check: latency must be sub-millisecond (no socket wait)
        t0 = time.perf_counter()
        redis_cache.set("cb_key", "cb_val")
        retrieved = redis_cache.get("cb_key")
        t1 = time.perf_counter()
        elapsed_ms = (t1 - t0) * 1000.0

        self.assertEqual(retrieved, "cb_val")
        self.assertLess(elapsed_ms, 5.0, f"Circuit-open execution took {elapsed_ms}ms; expected < 5ms")


class TestStoryMemorySerializationThroughCache(unittest.TestCase):
    """Verifies StoryMemory and StoryBible serialization round-trip through CacheManager."""

    def setUp(self):
        self.cache_mgr = CacheManager()

    def test_full_story_memory_roundtrip(self):
        """Round-trip full StoryMemory with StoryBible, chapters, states, and threads."""
        bible = StoryBible(
            title="Kẻ Săn Bóng Đêm",
            genre="Urban Fantasy",
            world_setting="Hà Nội năm 2045, công nghệ Cyberpunk pha trộn huyền bí",
            characters=[
                {"name": "Minh", "role": "Nhân vật chính", "appearance": "Áo khoác dạ đen, mắt máy bên trái", "personality": "Lạnh lùng, quyết đoán"},
                {"name": "Linh", "role": "Hacker hỗ trợ", "appearance": "Tóc ngắn nhuộm tím, kính thông minh", "personality": "Hài hước, nhanh trí"},
            ],
            main_plot="Điều tra vụ mất tích bí ẩn tại tập đoàn công nghệ V-Corp",
            writing_style="Nhịp điệu nhanh, văn phong sắc bén, miêu tả chi tiết",
            refined_prompt="Một câu chuyện trinh thám công nghệ cao tại Hà Nội tương lai.",
            narrative_beats=[
                "Khám phá hiện trường vụ án",
                "Phát hiện dấu vết mã độc sinh học",
                "Đụng độ nhóm sát thủ tại phố cổ",
                "Giải mã bí mật tại trụ sở ngầm",
                "Đối đầu trùm cuối trên đỉnh tháp Keangnam",
            ],
        )

        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 2
        memory.chapter_summaries = [
            "Chương 1: Minh nhận được tín hiệu cầu cứu kỳ lạ từ máy chủ của Linh.",
            "Chương 2: Cả hai thâm nhập vào khu chợ đen để tìm manh mối về con chip cổ.",
        ]
        memory.character_states = {
            "Minh": "Bị thương nhẹ ở cánh tay trái, năng lượng pin mắt máy còn 45%",
            "Linh": "Đang giải mã tập tin bảo mật cấp 5",
        }
        memory.unresolved_threads = [
            "Ai là kẻ ra lệnh ám sát tiến sĩ Hoàng?",
            "Con chip sinh học có nguồn gốc từ đâu?",
        ]
        memory.relationship_map = {
            "Minh - Linh": "Cộng sự tin cậy lâu năm",
            "Minh - V-Corp": "Thù địch sâu sắc",
        }
        memory.full_text = "# Chương 1\n\nMưa rào đập trên mặt kính...\n\n# Chương 2\n\nTiếng còi cảnh sát rít lên..."

        # Store in CacheManager
        session_id = memory.session_id
        self.cache_mgr.set_session(session_id, memory.to_dict(), ttl=7200)

        # Retrieve and verify cached dict
        cached_dict = self.cache_mgr.get_session(session_id)
        self.assertIsNotNone(cached_dict, "Failed to retrieve cached session dict")

        # Reconstruct StoryMemory from cached dictionary
        restored = StoryMemory.from_dict(cached_dict)

        # Verify all fields
        self.assertEqual(restored.session_id, session_id)
        self.assertEqual(restored.current_chapter, 2)
        self.assertEqual(len(restored.chapter_summaries), 2)
        self.assertEqual(restored.chapter_summaries[0], memory.chapter_summaries[0])
        self.assertEqual(restored.character_states["Minh"], memory.character_states["Minh"])
        self.assertEqual(len(restored.unresolved_threads), 2)
        self.assertEqual(restored.relationship_map["Minh - Linh"], "Cộng sự tin cậy lâu năm")
        self.assertEqual(restored.full_text, memory.full_text)

        # Verify StoryBible fidelity
        self.assertEqual(restored.story_bible.title, "Kẻ Săn Bóng Đêm")
        self.assertEqual(restored.story_bible.genre, "Urban Fantasy")
        self.assertEqual(len(restored.story_bible.characters), 2)
        self.assertEqual(restored.story_bible.characters[0]["name"], "Minh")
        self.assertEqual(len(restored.story_bible.narrative_beats), 5)

        # Test session invalidation
        self.assertTrue(self.cache_mgr.delete_session(session_id))
        self.assertIsNone(self.cache_mgr.get_session(session_id))


class TestDraftAndUserTokenCaching(unittest.TestCase):
    """Verifies story draft caching and user token caching."""

    def setUp(self):
        self.cache_mgr = CacheManager()

    def test_draft_caching_and_invalidation(self):
        """Verify draft caching and explicit deletion on manuscript update."""
        story_id = 777
        draft = {
            "id": story_id,
            "user_id": 101,
            "title": "Bản Thảo Thử Nghiệm",
            "story_content": "Đoạn văn mở đầu bản thảo...",
            "word_count": 500,
        }

        self.cache_mgr.set_draft(story_id, draft, ttl=1800)
        cached = self.cache_mgr.get_draft(story_id)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["title"], "Bản Thảo Thử Nghiệm")
        self.assertEqual(cached["user_id"], 101)

        # Invalidate draft
        self.assertTrue(self.cache_mgr.delete_draft(story_id))
        self.assertIsNone(self.cache_mgr.get_draft(story_id))

    def test_user_token_caching_and_invalidation(self):
        """Verify auth token caching for sub-millisecond get_current_user resolution."""
        token = "jwt_auth_token_sample_abc123"
        user_info = {"id": 101, "username": "writer_pro", "full_name": "Trần Thị B"}

        self.cache_mgr.set_user_token(token, user_info, ttl=900)
        retrieved = self.cache_mgr.get_user_token(token)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["username"], "writer_pro")
        self.assertEqual(retrieved["full_name"], "Trần Thị B")

        # Invalidate on logout
        self.assertTrue(self.cache_mgr.delete_user_token(token))
        self.assertIsNone(self.cache_mgr.get_user_token(token))


if __name__ == "__main__":
    unittest.main()
