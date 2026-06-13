"""
미국 증시 뉴스 분석 Multi-Agent Orchestrator
"""
from datetime import datetime, timedelta
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from utils import get_us_market_news, send_to_email
from utils.ai_analyzer import summarize_news_with_insight, assess_risk_and_opportunity
from utils.semantic_cache import SemanticCacheManager
from utils.security import sanitize_articles, validate_articles
from config.settings import DOUBLE_SEPARATOR, SEPARATOR, PREVIEW_LENGTH


class NewsCollectorAgent:
    def collect(self):
        print("\n📰 미국 증시 뉴스 수집 중...\n")
        articles = get_us_market_news()

        if articles is None:
            print("❌ 뉴스 수집에 실패했습니다.")
            print("   - NEWSAPI_KEY가 유효한지 확인해주세요.")
            print("   - https://newsapi.org에서 무료 API 키를 발급받으세요.")
            return None

        if len(articles) == 0:
            print("❌ 뉴스 기사 검색 결과가 없습니다.")
            print("   - 검색 쿼리 또는 날짜 범위를 확인해주세요.")
            print("   - 최근 뉴스가 없을 수 있습니다.")
            return None

        print(f"✅ {len(articles)}개의 뉴스 기사를 수집했습니다.\n")
        return articles


class NewsSanitizerAgent:
    def sanitize(self, articles):
        valid, reason = validate_articles(articles)
        if not valid:
            print(f"❌ 뉴스 검증 실패: {reason}")
            return None

        sanitized, warnings = sanitize_articles(articles)
        if warnings:
            print("⚠️ 뉴스 데이터 정제 경고:")
            for warning in warnings:
                print(f"- {warning}")
            print('')

        return sanitized


class MarketAnalystAgent:
    def analyze(self, articles):
        print("🤖 시장 분석 에이전트 실행 중...\n")
        result = summarize_news_with_insight(articles)
        if not result:
            print("❌ 시장 분석에 실패했습니다.")
            return None
        return result


class RiskAssessorAgent:
    def assess(self, analysis_text):
        print("⚖️ 리스크 분석 에이전트 실행 중...\n")
        result = assess_risk_and_opportunity(analysis_text)
        if not result:
            print("❌ 리스크/기회 평가에 실패했습니다.")
            return None
        return result


class ReportGeneratorAgent:
    def compose(self, analysis_text, risk_text, cache_hit, token_summary):
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cache_note = '예' if cache_hit else '아니요'
        prompt_tokens = token_summary.get('prompt_tokens', 0)
        completion_tokens = token_summary.get('completion_tokens', 0)
        total_tokens = token_summary.get('total_tokens', prompt_tokens + completion_tokens)

        return (
            f"📊 미국 증시 뉴스 분석 보고서\n"
            f"{DOUBLE_SEPARATOR}\n"
            f"작성일: {generated_at}\n"
            f"캐시 사용: {cache_note}\n"
            f"\n"
            f"{analysis_text}\n\n"
            f"{SEPARATOR}\n"
            f"⚠️ 리스크 및 기회 평가\n"
            f"{risk_text}\n\n"
            f"{SEPARATOR}\n"
            f"🧠 LLM 토큰 사용 요약\n"
            f"- prompt_tokens: {prompt_tokens}\n"
            f"- completion_tokens: {completion_tokens}\n"
            f"- total_tokens: {total_tokens}\n"
        )


class LLMCostTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def add(self, usage):
        if not usage:
            return

        self.prompt_tokens += usage.get('prompt_tokens', 0) or 0
        self.completion_tokens += usage.get('completion_tokens', 0) or 0
        self.total_tokens += usage.get('total_tokens', 0) or 0

    def summary(self):
        return {
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens
        }


class USMarketNewsAgent:
    """미국 증시 뉴스 분석 Agent 클래스"""

    def __init__(self):
        self.articles = None
        self.analysis = None
        self.output_file = None
        self.cache_hit = False
        self.cache_manager = SemanticCacheManager()
        self.cost_tracker = LLMCostTracker()
        self.collector = NewsCollectorAgent()
        self.sanitizer = NewsSanitizerAgent()
        self.analyst = MarketAnalystAgent()
        self.risk_assessor = RiskAssessorAgent()
        self.report_generator = ReportGeneratorAgent()

    def fetch_news(self):
        self.articles = self.collector.collect()
        return bool(self.articles)

    def _compile_analysis_workflow(self):
        class WorkflowState(TypedDict, total=False):
            news_items: list
            analysis_result: dict
            risk_result: dict

        def analysis_node(state: WorkflowState):
            return {'analysis_result': self.analyst.analyze(state['news_items'])}

        def risk_node(state: WorkflowState):
            analysis_result = state.get('analysis_result')
            if not analysis_result:
                return {'risk_result': None}
            return {'risk_result': self.risk_assessor.assess(analysis_result['content'])}

        graph = StateGraph(WorkflowState)
        graph.add_node('analysis', analysis_node)
        graph.add_node('risk', risk_node)
        graph.add_edge(START, 'analysis')
        graph.add_edge('analysis', 'risk')
        graph.set_entry_point('analysis')
        graph.set_finish_point('risk')

        return graph.compile()

    def analyze_news(self):
        if not self.articles:
            print('❌ 분석할 뉴스가 없습니다.')
            return False

        news_items = self.sanitizer.sanitize(self.articles)
        if not news_items:
            return False

        cached = self.cache_manager.get_cached_report(news_items)
        if cached:
            print('♻️ 캐시된 분석 결과를 사용합니다. 동일한 뉴스 세트가 이전에 분석되었습니다.\n')
            self.analysis = cached['report']
            self.cache_hit = True
            cached_usage = cached.get('metadata', {}).get('llm_usage')
            self.cost_tracker.add(cached_usage)
            return True

        analysis_workflow = self._compile_analysis_workflow()
        pipeline_result = analysis_workflow.invoke({'news_items': news_items})

        analysis_result = pipeline_result.get('analysis_result')
        risk_result = pipeline_result.get('risk_result')
        if not analysis_result or not risk_result:
            print('❌ 분석 또는 리스크 평가에 실패했습니다.')
            return False

        self.cost_tracker.add(analysis_result.get('usage'))
        self.cost_tracker.add(risk_result.get('usage'))

        self.analysis = self.report_generator.compose(
            analysis_result['content'],
            risk_result['content'],
            self.cache_hit,
            self.cost_tracker.summary()
        )

        self.cache_manager.save_report(
            news_items,
            self.analysis,
            metadata={'llm_usage': self.cost_tracker.summary(), 'cache_hit': self.cache_hit}
        )

        return True

    def save_result(self):
        if not self.analysis:
            print('❌ 저장할 분석 결과가 없습니다.')
            return False

        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_file = f'market_analysis_{timestamp}.txt'

        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(self.analysis)

            print(f"\n💾 결과가 '{self.output_file}'에 저장되었습니다.")
            return True
        except Exception as e:
            print(f'❌ 파일 저장 실패: {e}')
            return False

    def send_to_email_message(self):
        if not self.analysis or not self.output_file:
            print('❌ 전송할 분석 결과나 파일이 없습니다.')
            return False

        print('\n📧 이메일로 전송 중...\n')

        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        message_preview = (
            self.analysis[:PREVIEW_LENGTH] + '\n...(전체는 다음 메시지를 확인하세요.)\n'
            if len(self.analysis) > PREVIEW_LENGTH
            else self.analysis
        )

        message = (
            f'📊 {yesterday} 미국 증시 뉴스 분석 보고서\n\n'
            f'{message_preview}'
        )

        return send_to_email(message, subject=f'{yesterday} 미국 증시 뉴스 분석 보고서')

    def print_summary(self):
        summary = self.cost_tracker.summary()
        print('\n💰 LLM 비용 요약')
        print(SEPARATOR)
        print(f"- prompt_tokens: {summary['prompt_tokens']}")
        print(f"- completion_tokens: {summary['completion_tokens']}")
        print(f"- total_tokens: {summary['total_tokens']}")
        print(f"- 캐시 사용: {'예' if self.cache_hit else '아니요'}")
        print(SEPARATOR)

    def run(self):
        print('🚀 미국 증시 뉴스 분석 Agent 시작...\n')

        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f'📅 분석 대상: {yesterday}의 미국 증시 뉴스')
        print(SEPARATOR)

        if not self.fetch_news():
            return False

        if not self.analyze_news():
            return False

        if not self.save_result():
            return False

        print(SEPARATOR)
        print(self.analysis)
        print(SEPARATOR)

        self.print_summary()
        self.send_to_email_message()

        return True
