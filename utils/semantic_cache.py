"""
시맨틱 캐시 관리 모듈 (FAISS 임베딩 기반 캐시)
"""
import json
import hashlib
import os
import math
from datetime import datetime, timedelta
from typing import List, Optional

from config.settings import CACHE_FILE, EMBEDDING_MODEL, OPENAI_API_KEY, SIMILARITY_THRESHOLD

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import faiss
    import numpy as np
except Exception:
    faiss = None
    np = None


def _normalize_vector(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0.0:
        return vector
    return [x / norm for x in vector]


def _avg_embeddings(embeddings: List[List[float]]) -> List[float]:
    if not embeddings:
        return []
    length = len(embeddings[0])
    avg = [0.0] * length
    for emb in embeddings:
        for i in range(length):
            avg[i] += emb[i]
    n = len(embeddings)
    return [x / n for x in avg]


class SemanticCacheManager:
    """임베딩을 사용한 시맨틱 캐시 관리.

    동작 원리:
    - 입력된 기사 목록에서 각 기사(title+description)의 임베딩을 생성
    - 기사 세트의 평균 임베딩과 캐시에 저장된 임베딩들 간 유사도 비교
    - 유사도가 `SIMILARITY_THRESHOLD` 이상이면 캐시된 결과를 재사용

    FAISS가 설치되어 있으면 로컬 벡터 인덱스를 사용하고,
    그렇지 않으면 기존 지문 기반 캐시 방식으로 폴백합니다.
    """

    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.client = None
        self.faiss_index = None
        self.faiss_fingerprints: List[str] = []
        self.faiss_dim: Optional[int] = None

        if OPENAI_API_KEY and OpenAI is not None:
            try:
                self.client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self.client = None

        self._build_faiss_index()

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

    def _embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text chunk using OpenAI."""
        if not self.client:
            return []
        try:
            resp = self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)
            data = getattr(resp, 'data', None)
            if data and len(data) > 0:
                first = data[0]
                emb = getattr(first, 'embedding', None) or first.get('embedding')
                if emb:
                    return [float(x) for x in emb]
        except Exception:
            return []
        return []

    def _articles_embedding(self, articles) -> List[float]:
        """Compute the average normalized embedding for a list of articles."""
        embeddings = []
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            text = (title + "\n" + description)[:3000]
            emb = self._embed_text(text)
            if emb:
                embeddings.append(emb)
        if not embeddings:
            return []
        return _normalize_vector(_avg_embeddings(embeddings))

    def _build_faiss_index(self):
        """Build an in-memory FAISS index from cached embeddings."""
        if faiss is None or np is None:
            return

        vectors = []
        self.faiss_fingerprints = []
        for fingerprint, entry in self.cache.items():
            emb = entry.get('embedding')
            if emb and isinstance(emb, list):
                vectors.append(_normalize_vector(emb))
                self.faiss_fingerprints.append(fingerprint)

        if not vectors:
            return

        self.faiss_dim = len(vectors[0])
        index = faiss.IndexFlatIP(self.faiss_dim)
        array = np.array(vectors, dtype='float32')
        faiss.normalize_L2(array)
        index.add(array)
        self.faiss_index = index

    def _add_embedding_to_faiss(self, fingerprint: str, embedding: List[float]):
        """Add a newly generated embedding to the FAISS index for future lookups."""
        if faiss is None or np is None:
            return

        normalized_emb = _normalize_vector(embedding)
        vector = np.array([normalized_emb], dtype='float32')
        faiss.normalize_L2(vector)

        if self.faiss_index is None:
            self.faiss_dim = len(normalized_emb)
            self.faiss_index = faiss.IndexFlatIP(self.faiss_dim)
            self.faiss_fingerprints = []

        self.faiss_index.add(vector)
        self.faiss_fingerprints.append(fingerprint)

    def get_cached_report(self, articles, similarity_threshold: float = SIMILARITY_THRESHOLD, ttl_days: int = 7):
        """Search the cache using FAISS similarity or fingerprint fallback."""
        if self.faiss_index is not None and self.client is not None:
            input_emb = self._articles_embedding(articles)
            if input_emb:
                query = np.array([input_emb], dtype='float32')
                faiss.normalize_L2(query)
                distances, indices = self.faiss_index.search(query, 1)
                if indices.shape[1] > 0:
                    idx = int(indices[0][0])
                    score = float(distances[0][0])
                    if idx != -1 and score >= similarity_threshold:
                        fingerprint = self.faiss_fingerprints[idx]
                        entry = self.cache.get(fingerprint)
                        if entry is None:
                            return None
                        entry_ts = entry.get('timestamp')
                        if entry_ts:
                            try:
                                ts = datetime.fromisoformat(entry_ts.replace('Z', ''))
                                if datetime.utcnow() - ts > timedelta(days=ttl_days):
                                    return None
                            except Exception:
                                pass
                        return entry

        fingerprint = self.make_fingerprint(articles)
        entry = self.cache.get(fingerprint)
        if entry is None:
            return None
        entry_ts = entry.get('timestamp')
        if entry_ts:
            try:
                ts = datetime.fromisoformat(entry_ts.replace('Z', ''))
                if datetime.utcnow() - ts > timedelta(days=ttl_days):
                    return None
            except Exception:
                pass
        return entry

    def save_report(self, articles, report_text, metadata=None):
        """Save the report to JSON cache and insert the embedding into FAISS."""
        fingerprint = self.make_fingerprint(articles)
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'report': report_text,
            'metadata': metadata or {}
        }

        if self.client:
            emb = self._articles_embedding(articles)
            if emb:
                entry['embedding'] = emb

        self.cache[fingerprint] = entry
        self._save_cache()

        if 'embedding' in entry and entry['embedding']:
            self._add_embedding_to_faiss(fingerprint, entry['embedding'])
