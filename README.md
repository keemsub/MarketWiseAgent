# MarketWiseAgent
간단한 토이 프로젝트: 미국 증시 관련 뉴스 수집과 간단한 투자 인사이트 제공 에이전트

요약
- 이 레포는 뉴스 수집 → 전처리 → 분석 → 캐시 저장 → 알림 흐름으로 동작하는 소형 에이전트입니다.

프로젝트 흐름
1. `utils/news_fetcher.py`에서 외부 뉴스(웹/API)를 주기적으로 수집
2. 원시 텍스트를 `utils/ai_analyzer.py`로 전송해 요약/감성/핵심 키워드 추출
3. 분석 결과를 `utils/semantic_cache.py`/`cache/analysis_cache.json`에 저장
4. 특정 조건(예: 중요도 높은 이벤트) 발생 시 `utils/email_sender.py`로 알림 발송
5. `agent/us_market_agent.py`는 위 기능을 조합해 전체 파이프라인을 조율

주요 파일/디렉터리
- `main.py`: 로컬에서 파이프라인을 실행하는 진입점
- `agent/`: 에이전트 제어 로직
- `utils/`: 뉴스 수집, 분석, 메일 전송, 보안 관련 유틸
- `config/`: 설정값 및 환경 관련 코드
- `cache/`: 분석 결과 캐시
- `notebook/`: 실험과 시각화를 위한 노트북

의존성 설치
```
python -m pip install -r requirements.txt
```