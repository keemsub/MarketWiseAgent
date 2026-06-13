"""
AI 분석 모듈
"""
import re
from typing import Any
from typing_extensions import TypedDict
from openai import OpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START
from config.settings import OPENAI_API_KEY, AI_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS
from utils.security import build_system_prompt


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def count_major_news_items(text: str) -> int:
    return len(re.findall(r'^\d+\.\s', text, flags=re.MULTILINE))


def _convert_message_to_openai(message: Any) -> dict:
    if isinstance(message, dict):
        role = message.get('role', '')
        content = message.get('content', '')
        name = message.get('name')
    elif hasattr(message, 'model_dump'):
        data = message.model_dump()
        role = data.get('type', '')
        if role == 'human':
            role = 'user'
        elif role == 'ai':
            role = 'assistant'
        content = data.get('content', '')
        name = data.get('name')
    else:
        raise ValueError('Unsupported message type for OpenAI conversion.')

    normalized = {
        'role': role,
        'content': content or ''
    }
    if name:
        normalized['name'] = name
    return normalized


def _normalize_messages(messages: list[Any]) -> list[dict]:
    if not isinstance(messages, list):
        raise ValueError('Messages must be a list.')
    return [_convert_message_to_openai(message) for message in messages]


def request_completion(messages, max_tokens=AI_MAX_TOKENS):
    if not OPENAI_API_KEY:
        print('❌ OPENAI_API_KEY가 설정되지 않았습니다.')
        print('   .env 파일에 OPENAI_API_KEY를 설정해주세요.')
        return None

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        normalized_messages = _normalize_messages(messages)
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=normalized_messages,
            temperature=AI_TEMPERATURE,
            max_tokens=max_tokens
        )
        message_obj = response.choices[0].message
        content = message_obj.content if hasattr(message_obj, 'content') else message_obj['content']
        response_usage = getattr(response, 'usage', None)
        usage = None
        if response_usage is not None:
            usage = {
                'prompt_tokens': getattr(response_usage, 'prompt_tokens', 0) or 0,
                'completion_tokens': getattr(response_usage, 'completion_tokens', 0) or 0,
                'total_tokens': getattr(response_usage, 'total_tokens', 0) or 0,
            }

        return {
            'content': content,
            'usage': usage,
            'estimated_tokens': estimate_tokens(' '.join([m['content'] for m in normalized_messages]) + content)
        }
    except Exception as e:
        print(f'❌ OpenAI API 요청 실패: {e}')
        return None


def format_articles_for_prompt(articles):
    news_content = []
    for idx, article in enumerate(articles, 1):
        title = article.get('title', 'N/A')
        description = article.get('description', 'N/A')
        source = article.get('source', {}).get('name', 'N/A')
        url = article.get('url', 'N/A')
        news_content.append(
            f"{idx}. [{source}] {title}\n   {description}\n   URL: {url}"
        )
    return "\n\n".join(news_content)


def _build_analysis_prompt(system_prompt: str, news_content: str) -> ChatPromptTemplate:
    return ChatPromptTemplate(
        [
            ('system', '{system_prompt}'),
            (
                'human',
                """
다음은 어제의 미국 증시 관련 뉴스들입니다.

{news_content}

요청사항:
1. 위 뉴스들 중에서 미국 증시에 가장 영향을 미칠 만한 주요 뉴스 5가지를 선정하여 정리해주세요.
2. 각 뉴스를 1-2줄로 요약해주세요.
3. 전체적인 시장 분석 및 투자자 입장에서의 인사이트를 제공해주세요.
4. 리스크 요소와 기회 요소를 구분하여 설명해주세요.

형식:
📊 주요 뉴스 5가지
---
1. [뉴스 제목]
   요약: [1-2줄 요약]
   
2. [뉴스 제목]
   요약: [1-2줄 요약]

...

💡 시장 분석 및 투자 인사이트
---
[분석 내용]

⚠️ 리스크 요소
---
[리스크 설명]

🎯 기회 요소
---
[기회 설명]

💼 투자 전략 제언
---
[제언 내용]
"""
            ),
        ],
        input_variables=['system_prompt', 'news_content']
    )


def _build_risk_prompt(system_prompt: str, content_excerpt: str) -> ChatPromptTemplate:
    return ChatPromptTemplate(
        [
            ('system', '{system_prompt}'),
            (
                'human',
                """
다음은 이전 단계에서 생성된 미국 증시 뉴스 분석 결과입니다.

{content_excerpt}

요청사항:
1. 리스크 요소를 최대 3개로 정리해주세요.
2. 기회 요소를 최대 3개로 정리해주세요.
3. 각 항목에 간략한 설명을 추가해주세요.
4. 투자자 관점에서 중요한 포인트를 강조해주세요.

형식:
⚠️ 리스크 요소
---
- [리스크 1]
- [리스크 2]

🎯 기회 요소
---
- [기회 1]
- [기회 2]
"""
            ),
        ],
        input_variables=['system_prompt', 'content_excerpt']
    )


def summarize_news_with_insight(articles):
    if not articles:
        print('❌ 분석할 뉴스가 없습니다.')
        return None

    system_prompt = build_system_prompt()
    news_content = format_articles_for_prompt(articles)
    prompt_value = _build_analysis_prompt(system_prompt, news_content).invoke(
        {
            'system_prompt': system_prompt,
            'news_content': news_content,
        }
    )
    messages = prompt_value.to_messages()

    result = request_completion(messages)
    if result and count_major_news_items(result['content']) < 5:
        print('⚠️ 5개 주요 뉴스가 충분히 생성되지 않았습니다. 다시 요청합니다...')
        messages.append(HumanMessage(content=(
            '결과에 반드시 5개의 주요 뉴스 항목을 포함하고, 각 항목에 URL을 적어주세요. '
            '현재 5개보다 적습니다. 부족하면 5개까지 즉시 채워주세요.'
        )))
        result2 = request_completion(messages)
        if result2:
            return result2

    return result


def assess_risk_and_opportunity(analysis_text):
    if not analysis_text:
        print('❌ 평가할 분석 텍스트가 없습니다.')
        return None

    system_prompt = build_system_prompt()
    content_excerpt = analysis_text[:3000]
    prompt_value = _build_risk_prompt(system_prompt, content_excerpt).invoke(
        {
            'system_prompt': system_prompt,
            'content_excerpt': content_excerpt,
        }
    )
    messages = prompt_value.to_messages()

    return request_completion(messages, max_tokens=600)


class AnalysisWorkflowState(TypedDict, total=False):
    articles: list
    analysis_response: dict
    risk_response: dict


def run_langgraph_analysis(articles):
    def analysis_node(state: AnalysisWorkflowState):
        return {'analysis_response': summarize_news_with_insight(state['articles'])}

    def risk_node(state: AnalysisWorkflowState):
        analysis_response = state.get('analysis_response')
        if not analysis_response:
            return {'risk_response': None}
        return {'risk_response': assess_risk_and_opportunity(analysis_response['content'])}

    graph = StateGraph(AnalysisWorkflowState)
    graph.add_node('analysis', analysis_node)
    graph.add_node('risk', risk_node)
    graph.add_edge(START, 'analysis')
    graph.add_edge('analysis', 'risk')
    graph.set_entry_point('analysis')
    graph.set_finish_point('risk')

    compiled = graph.compile()
    return compiled.invoke({'articles': articles})
