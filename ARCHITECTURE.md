# MarketWiseAgent — 아키텍처 개요

## 목적
- `MarketWiseAgent`는 미국 증시 뉴스 데이터를 수집하여 LLM 기반 투자 인사이트를 생성하고, 결과를 저장·재사용·알림하는 엔드투엔드 에이전트

## 핵심 아이디어
- 목표: 최신 U.S. 시장 뉴스에 대해 자동으로 요약·평가하고, 중요한 분석 결과를 재사용하여 llm 토큰 사용 비용을 줄입니다.
- 설계 원칙: 모듈화, 명확한 데이터 흐름, 비용 최적화, 보안 방어

## 주요 구성 요소
- `agent/us_market_agent.py` — 전체 파이프라인을 오케스트레이션하는 엔트리 포인트
- `utils/news_fetcher.py` — NewsAPI 기반 미국 증시 뉴스 수집
- `utils/security.py` — 입력 뉴스 검증, 텍스트 정제, 프롬프트 인젝션 방어
- `utils/ai_analyzer.py` — 뉴스 요약 및 인사이트 생성을 위한 LLM 프롬프트 템플릿
- `utils/semantic_cache.py` — FAISS 기반 임베딩 시맨틱 캐시 및 JSON 폴백 관리
- `utils/email_sender.py` — 분석 결과를 이메일로 전송
- `config/settings.py` — API 키, 모델 설정, 캐시 임계값 등의 환경 설정
- `tests/test_semantic_cache.py` — 캐시 동작을 검증하는 유닛 테스트

## 데이터 흐름
1. **수집**: `NewsCollectorAgent`가 `get_us_market_news()`를 호출해 최신 미국 증시 뉴스 기사 목록 가져오기
2. **정제**: `NewsSanitizerAgent`가 `utils/security.py`의 `validate_articles()`와 `sanitize_articles()`를 사용해 기사 텍스트를 검증하고 정제
3. **캐시 검사**: `SemanticCacheManager`가 뉴스 세트의 임베딩을 계산하고 FAISS 인덱스에서 유사도를 조회 후 `SIMILARITY_THRESHOLD`(기본 0.9) 이상이면 이전 분석 결과를 재사용
4. **분석**: 캐시 미스 시 `utils/ai_analyzer.py`의 `summarize_news_with_insight()`를 호출해 주요 뉴스 요약과 인사이트 생성
5. **리스크 평가**: `assess_risk_and_opportunity()`를 추가 호출하여 리스크/기회 요소를 분리해 정리
6. **저장**: 최종 보고서를 텍스트 파일로 저장하고 캐시에 분석 결과와 임베딩을 기록
7. **알림**: 이메일 전송이 활성화된 경우 `send_to_email()`로 전체 보고서를 발송

## 비용 최적화
- **FAISS 기반 시맨틱 캐시**: 동일하거나 유사한 뉴스 세트에 대해 LLM 재호출을 방지해 토큰 비용 절감
- **임베딩 평균화**: 개별 기사 임베딩을 평균 계산해 뉴스 묶음 전체에 대한 대표 벡터 생성
- **캐시 폴백**: FAISS 또는 OpenAI 임베딩이 없을 때는 기존 지문 기반 캐시로 안전하게 대체
- **LLM 비용 추적**: `LLMCostTracker`가 프롬프트/완성 토큰 사용량을 수집해 분석 비용을 모니터링

## 보안 가드레일
- `utils/security.py`는 뉴스 콘텐츠를 원시 데이터로 취급하고, 프롬프트 인젝션 패턴을 감지해 차단
- 시스템 프롬프트는 LLM에게 뉴스 내용 이외의 임의 명령을 따르지 않도록 지시

## FAISS 캐시 구현
- `utils/semantic_cache.py`는 캐시 파일(`cache/analysis_cache.json`)에 분석 결과와 임베딩을 저장합니다.
- 앱 시작 시 기존 캐시에서 임베딩을 로드해 FAISS `IndexFlatIP` 인덱스 구성
- 새로운 기사 세트가 들어오면 평균 임베딩을 계산하고 FAISS에서 가장 높은 유사도를 검색
- 유사도 기준을 넘으면 기존 캐시 결과를 재사용하여 비용과 응답 시간을 절감
