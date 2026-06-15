# MarketWiseAgent
- 미국 증시 관련 뉴스 수집과 간단한 투자 인사이트 제공 에이전트

## highlight
- 임베딩 기반 시맨틱 캐시: OpenAI 임베딩을 생성해 뉴스정보의 평균 벡터를 계산하고, 로컬 FAISS 인덱스에서 코사인 유사도를 검사해 기존 분석 결과를 재사용합니다. 이를 통해 동일하거나 매우 유사한 뉴스셋에 대해 불필요한 LLM 호출과 토큰 비용을 절감합니다.
- 보안 가드레일: `utils/security.py`의 시스템 프롬프트와 입력 정제 로직이 뉴스 콘텐츠를 순수 데이터로만 취급하도록 하고, 프롬프트 인젝션 패턴을 차단합니다. 분석 요청은 명시적 사용자 지침만 따르며 뉴스 내 악성 지시를 무시합니다.

## 주요 파일/디렉터리
- `main.py`: 실행 진입점
- `agent/`: 워크플로우 오케스트레이션
- `utils/`: 뉴스 수집, LLM 분석, FAISS 기반 시맨틱 캐시, 이메일 전송, 그리고 프롬프트 보안 가드레일을 담당
- `config/`: 환경 변수 및 설정
- `cache/`: 임베딩/지문 기반 분석 결과 캐시 저장
- `tests/`: 유닛 테스트

## tut
1. 의존성 설치

```
python -m pip install -r requirements.txt
```

2. `.env` 설정 (레포 최상위 경로에 생성):

```
NEWSAPI_KEY=your_newsapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
GMAIL_EMAIL=youremail@gmail.com
GMAIL_PASSWORD=your_app_password_or_oauth_token
GMAIL_RECIPIENT=recipient@example.com
```

3. 로컬 실행 예시:

```
python main.py
```

테스트
- 유닛 테스트 실행:

```
python3 -m unittest discover -s tests -p 'test_*.py'
```

구성 옵션
- `config/settings.py`에서 `EMBEDDING_MODEL`, `SIMILARITY_THRESHOLD`(기본 0.9)를 설정
- FAISS를 사용하려면 `requirements.txt`에 있는 `faiss-cpu`와 `numpy`를 설치 필수
- FAISS 미설치 시 JSON 기반 폴백 동작

프로젝트 흐름
1. `utils/news_fetcher.py`에서 외부 뉴스(웹/API)를 주기적으로 수집
2. raw를 `utils/ai_analyzer.py`에서 요약/감성/핵심 키워드 추출
3. 2에서 가공된 데이터를 `utils/semantic_cache.py`/`cache/analysis_cache.json`에 저장
4. `utils/email_sender.py`로 알림 발송

의존성 설치
```
python -m pip install -r requirements.txt
```
