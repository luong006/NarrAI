"""
Unit tests for NarrAI Cache Service (Requirement R3)
Verifies ThreadSafeMemoryCache, RedisCache graceful degradation, CacheManager façade,
latency benchmark (< 20ms), and StoryMemory round-trip serialization.
"""

import os
import sys
import threading
import time
import unittest

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.cache_service import (
    ThreadSafeMemoryCache,
    RedisCache,
    CacheManager,
    get_cache_manager,
)
from agents.story_memory import StoryMemory, StoryBible


class TestThreadSafeMemoryCache(unittest.TestCase):
    def setUp(self):
        self.cache = ThreadSafeMemoryCache(max_items=10)

    def test_basic_crud(self):
        self.cache.set("key1", "value1")
        self.assertTrue(self.cache.exists("key1"))
        self.assertEqual(self.cache.get("key1"), "value1")

        self.cache.set("key2", {"nested": "data", "count": 42})
        self.assertEqual(self.cache.get("key2"), {"nested": "data", "count": 42})

        deleted = self.cache.delete("key1")
        self.assertTrue(deleted)
        self.assertFalse(self.cache.exists("key1"))
        self.assertIsNone(self.cache.get("key1"))

        # Non-existent delete
        self.assertFalse(self.cache.delete("non_existent"))

    def test_ttl_expiry(self):
        # Set with 0.1 second TTL
        self.cache.set("temp_key", "temporary_value", ttl=0.1)
        self.assertEqual(self.cache.get("temp_key"), "temporary_value")

        time.sleep(0.15)
        self.assertIsNone(self.cache.get("temp_key"))
        self.assertFalse(self.cache.exists("temp_key"))

    def test_lru_eviction(self):
        small_cache = ThreadSafeMemoryCache(max_items=3)
        small_cache.set("a", 1)
        small_cache.set("b", 2)
        small_cache.set("c", 3)

        # Access 'a' to make it recently used; order becomes b, c, a
        _ = small_cache.get("a")

        # Insert 'd', which should evict oldest 'b'
        small_cache.set("d", 4)

        self.assertIsNone(small_cache.get("b"), "'b' should have been evicted as LRU")
        self.assertEqual(small_cache.get("a"), 1)
        self.assertEqual(small_cache.get("c"), 3)
        self.assertEqual(small_cache.get("d"), 4)

    def test_clear_and_size(self):
        self.cache.set("x", 10)
        self.cache.set("y", 20)
        self.assertEqual(self.cache.size(), 2)

        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("x"))

    def test_concurrency_thread_safety(self):
        threads = []
        errors = []

        def worker(thread_id):
            try:
                for i in range(50):
                    key = f"t_{thread_id}_{i % 5}"
                    self.cache.set(key, i)
                    val = self.cache.get(key)
                    if val is not None and not isinstance(val, int):
                        errors.append(f"Unexpected value {val}")
            except Exception as ex:
                errors.append(str(ex))

        for t in range(5):
            th = threading.Thread(target=worker, args=(t,))
            threads.append(th)
            th.start()

        for th in threads:
            th.join()

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")


class TestRedisCacheGracefulDegradation(unittest.TestCase):
    def test_offline_redis_fallback(self):
        # Connect to an invalid port where Redis is guaranteed not running
        fallback = ThreadSafeMemoryCache(max_items=100)
        redis_cache = RedisCache(
            redis_url="redis://127.0.0.1:59999/0",
            fallback_cache=fallback,
            circuit_threshold=1,
            circuit_cooldown=5.0,
        )

        # Confirm connection failed gracefully
        self.assertFalse(redis_cache.is_connected)

        # Set and get should not raise exceptions; must work via fallback
        redis_cache.set("test_key", {"status": "ok"}, ttl=60)
        val = redis_cache.get("test_key")
        self.assertEqual(val, {"status": "ok"})
        self.assertTrue(redis_cache.exists("test_key"))

        deleted = redis_cache.delete("test_key")
        self.assertTrue(deleted)
        self.assertIsNone(redis_cache.get("test_key"))


class TestCacheManagerFacade(unittest.TestCase):
    def setUp(self):
        self.cache_mgr = CacheManager()

    def test_session_cache(self):
        session_id = "session-uuid-12345"
        memory_data = {
            "session_id": session_id,
            "current_chapter": 2,
            "chapter_summaries": ["Chuong 1 mo dau", "Chuong 2 kich tinh"],
            "full_text": "Noi dung truyen...",
        }

        self.cache_mgr.set_session(session_id, memory_data, ttl=3600)
        retrieved = self.cache_mgr.get_session(session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("current_chapter"), 2)
        self.assertEqual(len(retrieved.get("chapter_summaries", [])), 2)

        deleted = self.cache_mgr.delete_session(session_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.cache_mgr.get_session(session_id))

    def test_draft_cache(self):
        story_id = 999
        draft_data = {
            "id": 999,
            "title": "Truyện Thám Tử Siêu Phàm",
            "story_content": "Màn đêm bao trùm con hẻm nhỏ...",
            "word_count": 1500,
            "user_id": 42,
        }

        self.cache_mgr.set_draft(story_id, draft_data, ttl=1800)
        retrieved = self.cache_mgr.get_draft(story_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("title"), "Truyện Thám Tử Siêu Phàm")
        self.assertEqual(retrieved.get("word_count"), 1500)

        deleted = self.cache_mgr.delete_draft(story_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.cache_mgr.get_draft(story_id))

    def test_user_token_cache(self):
        token = "jwt_token_abc_xyz_123"
        user_info = {"id": 10, "username": "author_test", "full_name": "Nguyen Van A"}

        self.cache_mgr.set_user_token(token, user_info, ttl=900)
        retrieved = self.cache_mgr.get_user_token(token)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.get("username"), "author_test")
        self.assertEqual(retrieved.get("full_name"), "Nguyen Van A")

        self.cache_mgr.delete_user_token(token)
        self.assertIsNone(self.cache_mgr.get_user_token(token))

    def test_benchmark_latency_requirement(self):
        # Must report latency < 20.0ms
        bench = self.cache_mgr.benchmark_latency(iterations=100)
        self.assertTrue(bench["passed"])
        self.assertLess(bench["avg_latency_ms"], 20.0)
        self.assertGreaterEqual(bench["avg_latency_ms"], 0.0)
        self.assertEqual(bench["iterations"], 100)

    def test_get_stats(self):
        stats = self.cache_mgr.get_stats()
        self.assertIn("mode", stats)
        self.assertIn("redis_available", stats)
        self.assertIn("item_count", stats)
        self.assertIn("avg_latency_ms", stats)
        self.assertLess(stats["avg_latency_ms"], 20.0)

    def test_singleton_factory(self):
        inst1 = get_cache_manager()
        inst2 = get_cache_manager()
        self.assertIs(inst1, inst2)


class TestStoryMemorySerializationRoundtrip(unittest.TestCase):
    def test_story_memory_roundtrip(self):
        cache_mgr = get_cache_manager()
        bible = StoryBible(
            title="Thế Giới Giả Tưởng",
            genre="Fantasy",
            world_setting="Thành phố trên mây",
            writing_style="Light Novel",
        )
        mem = StoryMemory(story_bible=bible)
        mem.current_chapter = 3
        mem.chapter_summaries = ["Khởi đầu hành trình", "Gặp gỡ đồng đội", "Trận chiến đầu tiên"]
        mem.full_text = "# Chương 1\n\nNắng sớm chiếu rọi...\n\n# Chương 2\n\nĐối thủ xuất hiện..."

        # Serialize and cache
        cache_mgr.set_session(mem.session_id, mem.to_dict(), ttl=3600)

        # Retrieve and deserialize
        cached_dict = cache_mgr.get_session(mem.session_id)
        self.assertIsNotNone(cached_dict)

        restored_mem = StoryMemory.from_dict(cached_dict)
        self.assertEqual(restored_mem.session_id, mem.session_id)
        self.assertEqual(restored_mem.current_chapter, 3)
        self.assertEqual(restored_mem.chapter_summaries, mem.chapter_summaries)
        self.assertEqual(restored_mem.story_bible.title, "Thế Giới Giả Tưởng")
        self.assertEqual(restored_mem.story_bible.genre, "Fantasy")
        self.assertEqual(restored_mem.full_text, mem.full_text)


if __name__ == "__main__":
    unittest.main()
