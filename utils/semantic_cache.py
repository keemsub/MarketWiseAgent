"""
시맨틱 캐시 관리 모듈
"""
import json
import hashlib
import os
from datetime import datetime
from config.settings import CACHE_FILE


class SemanticCacheManager:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _ensure_cache_dir(self):
        directory = os.path.dirname(self.cache_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _load_cache(self):
        self._ensure_cache_dir()
        if not os.path.exists(self.cache_file):
            return {}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_cache(self):
        self._ensure_cache_dir()
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    @staticmethod
    def make_fingerprint(articles):
        normalized = []
        for article in articles:
            title = article.get('title', '').strip()
            source = article.get('source', {}).get('name', '').strip()
            published_at = article.get('publishedAt', '').strip()
            normalized.append(f"{source}|{title}|{published_at}")
        fingerprint = "\n".join(normalized)
        return hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()

    def get_cached_report(self, articles):
        fingerprint = self.make_fingerprint(articles)
        return self.cache.get(fingerprint)

    def save_report(self, articles, report_text, metadata=None):
        fingerprint = self.make_fingerprint(articles)
        self.cache[fingerprint] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'report': report_text,
            'metadata': metadata or {}
        }
        self._save_cache()
