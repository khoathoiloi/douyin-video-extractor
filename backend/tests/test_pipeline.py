import os
import sys
import unittest
import json
import asyncio

# Setup path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)

from backend.app.pipeline.query_generator import QueryGenerator
from backend.app.pipeline.ranking_engine import RankingEngine
from backend.app.pipeline.deduplicator import Deduplicator
from backend.app.pipeline.multimodal_analyzer import MultimodalAnalyzer
from backend.app.providers.mock_provider import MockDouyinSearchProvider
from backend.app.providers.base import NormalizedSearchResult

class TestDouyinPipeline(unittest.TestCase):
    def test_query_generation_and_categories(self):
        profile = {
            "main_topic": "Nhảy / Vũ đạo / Gái xinh",
            "content_format": "dance_cover",
            "search_concepts": ["抖音热舞", "热门卡点舞"]
        }
        queries = QueryGenerator.generate_20_queries(profile)
        self.assertEqual(len(queries), 20)
        
        categories = set(q["category"] for q in queries)
        expected_cats = {"core_topic", "people_or_objects", "actions", "scene", "content_format", "long_tail"}
        self.assertTrue(expected_cats.issubset(categories))

    def test_query_expansion(self):
        base_kw = "热门卡点舞"
        variants = QueryGenerator.expand_query(base_kw)
        self.assertTrue(len(variants) >= 3)
        self.assertTrue(all(base_kw in v or "卡点" in v for v in variants))

    def test_ranking_engine_calculation(self):
        profile = {
            "summary": "Video nhảy cô gái triệu view",
            "content_format": "dance",
            "search_concepts": ["抖音热舞", "卡点舞"]
        }
        candidate = {
            "title": "【抖音热舞】热门卡点舞高能合集",
            "description": "全网爆款卡点热舞",
            "hashtags": ["#抖音热舞", "#卡点舞"],
            "like_count": 500000,
            "search_query": "抖音热舞"
        }
        scores = RankingEngine.calculate_scores(profile, candidate)
        self.assertIn("final_score", scores)
        self.assertGreater(scores["final_score"], 0.7)
        self.assertGreaterEqual(scores["semantic_similarity"], 0.5)

    def test_deduplicator(self):
        candidates = [
            {"remote_video_id": "1001", "url": "https://douyin.com/1001", "title": "Video nhay hay 1"},
            {"remote_video_id": "1001", "url": "https://douyin.com/1001", "title": "Video nhay hay 1 duplicate"},
            {"remote_video_id": "1002", "url": "https://douyin.com/1002", "title": "Video nhay hay 2"}
        ]
        unique = Deduplicator.deduplicate(candidates)
        self.assertEqual(len(unique), 2)

    def test_search_provider_normalization(self):
        async def _test():
            provider = MockDouyinSearchProvider()
            results = await provider.search("热门卡点舞", limit=5)
            self.assertEqual(len(results), 5)
            self.assertIsInstance(results[0], NormalizedSearchResult)
            self.assertEqual(results[0].search_query, "热门卡点舞")
            self.assertTrue(results[0].url.startswith("https://www.douyin.com/video/"))
        asyncio.run(_test())

if __name__ == "__main__":
    unittest.main()
