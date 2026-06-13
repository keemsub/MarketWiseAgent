"""
설정 및 환경 변수 관리
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=dotenv_path)


def _clean_env_value(value: str, remove_spaces: bool = False):
    if value is None:
        return None

    value = value.strip()
    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        value = value[1:-1]
    value = value.strip()

    if remove_spaces:
        value = value.replace(' ', '')

    return value


# API 키
NEWSAPI_KEY = _clean_env_value(os.getenv('NEWSAPI_KEY'))
OPENAI_API_KEY = _clean_env_value(os.getenv('OPENAI_API_KEY'))
GMAIL_EMAIL = _clean_env_value(os.getenv('GMAIL_EMAIL'))
GMAIL_PASSWORD = _clean_env_value(os.getenv('GMAIL_PASSWORD'), remove_spaces=True)
GMAIL_RECIPIENT = _clean_env_value(os.getenv('GMAIL_RECIPIENT'))

# API 엔드포인트
NEWSAPI_URL = "https://newsapi.org/v2/everything"

# 설정
MAX_NEWS_ARTICLES = 10
PREVIEW_LENGTH = 500
AI_MODEL = "gpt-3.5-turbo"
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 1200
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.9))
CACHE_DIR = "cache"
CACHE_FILE = "cache/analysis_cache.json"
GMAIL_SMTP_SERVER = os.getenv('GMAIL_SMTP_SERVER', 'smtp.gmail.com')
GMAIL_SMTP_PORT = int(os.getenv('GMAIL_SMTP_PORT', 587))

# 출력 설정
SEPARATOR = "-" * 60
DOUBLE_SEPARATOR = "=" * 60