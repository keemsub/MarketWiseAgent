"""
뉴스 수집 모듈
"""
import requests
from datetime import datetime, timedelta
from config.settings import NEWSAPI_KEY, NEWSAPI_URL, MAX_NEWS_ARTICLES


def _fetch_news(params):
    try:
        response = requests.get(NEWSAPI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            print(f"❌ 뉴스 API 오류: {data.get('message', '알 수 없는 오류')}")
            return None
        return data.get("articles", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ 뉴스 API 요청 실패: {e}")
        return None


def get_us_market_news():
    """
    뉴스 API를 사용하여 미국 증시 뉴스를 가져옵니다.

    Returns:
        list: 뉴스 기사 리스트, 실패시 None
    """
    if not NEWSAPI_KEY:
        print("❌ NEWSAPI_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 NEWSAPI_KEY를 설정해주세요.")
        return None

    queries = [
        {
            'q': '(US market OR stocks OR NASDAQ OR S&P 500 OR DOW OR economic OR Fed) AND (stock market OR trading)',
            'sortBy': 'relevance',
            'language': 'en'
        }
    ]

    date_ranges = [
        (1, 1),
        (2, 1),
        (3, 1)
    ]

    for days_back, range_days in date_ranges:
        start_date = (datetime.now() - timedelta(days=days_back + range_days - 1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        params = {
            'q': queries[0]['q'],
            'from': start_date,
            'to': end_date,
            'sortBy': queries[0]['sortBy'],
            'language': queries[0]['language'],
            'apiKey': NEWSAPI_KEY
        }

        articles = _fetch_news(params)
        if articles is None:
            return None

        if articles:
            print(f"✅ {start_date} ~ {end_date} 사이에서 {len(articles)}개의 뉴스 기사를 수집했습니다.\n")
            return articles[:MAX_NEWS_ARTICLES]

        print(f"⚠️ {start_date} ~ {end_date} 사이에는 뉴스가 없습니다. 다음 범위를 시도합니다...")

    print("❌ 해당 기간 내에 뉴스 기사가 없습니다. 다른 날짜 범위나 검색 쿼리를 확인해주세요.")
    return []
