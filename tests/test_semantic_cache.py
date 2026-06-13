import os
import tempfile
import unittest
from unittest.mock import MagicMock

from utils.semantic_cache import SemanticCacheManager


class TestSemanticCacheManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_path = os.path.join(self.temp_dir.name, 'test_cache.json')
        self.manager = SemanticCacheManager(cache_file=self.cache_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fingerprint_fallback_cache_hit(self):
        articles = [
            {'title': 'Market rally', 'description': 'Stocks go up', 'source': {'name': 'Test'}, 'publishedAt': '2026-06-13T00:00:00Z'}
        ]

        self.manager.client = None
        self.manager.save_report(articles, 'cached-result', metadata={'test': True})
        cached = self.manager.get_cached_report(articles)

        self.assertIsNotNone(cached)
        self.assertEqual(cached['report'], 'cached-result')
        self.assertEqual(cached['metadata']['test'], True)

    def test_embedding_similarity_cache_hit(self):
        articles_a = [
            {'title': 'Company A earnings', 'description': 'Solid results', 'source': {'name': 'Test'}, 'publishedAt': '2026-06-13T00:00:00Z'}
        ]
        articles_b = [
            {'title': 'Company A earnings', 'description': 'Solid results', 'source': {'name': 'Test'}, 'publishedAt': '2026-06-13T00:00:00Z'}
        ]

        dummy_client = MagicMock()
        dummy_response = MagicMock()
        dummy_response.data = [{'embedding': [1.0, 0.0, 0.0]}]
        dummy_client.embeddings.create.return_value = dummy_response

        self.manager.client = dummy_client
        self.manager.save_report(articles_a, 'similar-result', metadata={'similarity': True})
        cached = self.manager.get_cached_report(articles_b, similarity_threshold=0.9)

        self.assertIsNotNone(cached)
        self.assertEqual(cached['report'], 'similar-result')
        self.assertEqual(cached['metadata']['similarity'], True)

    def test_embedding_similarity_cache_miss_for_dissimilar(self):
        articles_a = [
            {'title': 'Company A earnings', 'description': 'Solid results', 'source': {'name': 'Test'}, 'publishedAt': '2026-06-13T00:00:00Z'}
        ]
        articles_b = [
            {'title': 'Company B scandal', 'description': 'Negative news', 'source': {'name': 'Test'}, 'publishedAt': '2026-06-13T00:00:00Z'}
        ]

        dummy_client = MagicMock()
        dummy_response_a = MagicMock()
        dummy_response_a.data = [{'embedding': [1.0, 0.0, 0.0]}]
        dummy_response_b = MagicMock()
        dummy_response_b.data = [{'embedding': [0.0, 1.0, 0.0]}]

        dummy_client.embeddings.create.side_effect = [dummy_response_a, dummy_response_b]

        self.manager.client = dummy_client
        self.manager.save_report(articles_a, 'cached-result', metadata={'similarity': True})

        # The second call uses a different embedding for articles_b.
        cached = self.manager.get_cached_report(articles_b, similarity_threshold=0.9)
        self.assertIsNone(cached)


if __name__ == '__main__':
    unittest.main()
