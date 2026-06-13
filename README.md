# MarketWiseAgent
- 미국 증시 관련 뉴스 수집과 간단한 투자 인사이트 제공 에이전트

## highlight
- 임베딩 기반 시맨틱 캐시: OpenAI 임베딩을 생성해 뉴스정보의 평균 벡터를 계산하고, FAISS 인덱스에서 유사도를 검사해 기존 분석 결과를 재사용합니다. 만약 FAISS가 없으면 기존 지문 기반 폴백이 동작
- 보안 가드레일 : ㅇㅇㅇ

## 주요 파일/디렉터리
- `main.py`: 실행 진입점
- `agent/`: 워크플로우 오케스트레이션
- `utils/`: agent 로직 실행 및 비용 최적화, llm 보안 가드레일
- `config/`: 환경 변수 및 설정
- `cache/`: 지문 기반 폴백 로직
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


더 다듬어 포트폴리오용 요약(기술 스택, 스크린샷 포함)으로 만들어 드릴까요?

프로젝트 흐름
1. `utils/news_fetcher.py`에서 외부 뉴스(웹/API)를 주기적으로 수집
2. raw를 `utils/ai_analyzer.py`에서 요약/감성/핵심 키워드 추출
3. 2에서 가공된 데이터를 `utils/semantic_cache.py`/`cache/analysis_cache.json`에 저장
4. `utils/email_sender.py`로 알림 발송

의존성 설치
```
python -m pip install -r requirements.txt
```