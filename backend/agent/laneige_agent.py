"""LANEIGE 랭킹 인사이트 Agent 모듈.

LangChain Agent를 활용한 AI 기반 랭킹 분석 에이전트예요.
"""

import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from pydantic import SecretStr

from .prompts import SYSTEM_PROMPT, WELCOME_MESSAGE
from .tools import create_analysis_tools, create_product_tools, create_ranking_tools

if TYPE_CHECKING:
    from backend.agent.vector_store import ProductVectorStore
    from backend.ranking import RankingService

load_dotenv()


class LaneigeAgent:
    """LANEIGE 랭킹 인사이트 Agent.

    LangChain Agent를 활용하여 AI가 적절한 도구를 선택하고
    멀티스텝 추론을 수행해요.

    Attributes:
        vector_store: 제품 벡터 스토어
        ranking_service: 랭킹 서비스
        model (str): 사용할 Claude 모델
        llm: LangChain ChatAnthropic 모델
        tools (list): Agent가 사용할 Tool 리스트
        agent: LangGraph ReAct Agent
    """

    def __init__(
        self,
        vector_store: "ProductVectorStore | None" = None,
        ranking_service: "RankingService | None" = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """LaneigeAgent를 초기화해요.

        Args:
            vector_store: 제품 벡터 스토어 (기본값: None)
            ranking_service: 랭킹 서비스 (기본값: None)
            model: Claude 모델 ID (기본값: claude-sonnet-4-20250514)
        """
        self.vector_store = vector_store
        self.ranking_service = ranking_service
        self.model = model

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Agent will use mock responses.")
            self.llm = None
            self.agent = None
            return

        self.llm = ChatAnthropic(model_name=model, api_key=SecretStr(api_key))

        self.tools = self._create_tools()

        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=SYSTEM_PROMPT,
        )

    def _create_tools(self) -> list:
        """Agent가 사용할 Tool을 생성해요.

        Returns:
            list: Tool 리스트
        """
        tools = []

        if self.vector_store:
            tools.extend(create_product_tools(self.vector_store))

        if self.ranking_service:
            tools.extend(create_ranking_tools(self.ranking_service))
            tools.extend(create_analysis_tools(self.ranking_service))

        return tools

    def chat(self, user_message: str) -> str:
        """사용자 메시지에 대한 AI 응답을 생성해요.

        Args:
            user_message: 사용자 메시지

        Returns:
            str: AI 응답 메시지
        """
        if self.agent is None:
            return self._mock_response(user_message)

        try:
            result = self.agent.invoke({"messages": [HumanMessage(content=user_message)]})

            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                return str(last_message.content)

            return "응답을 생성할 수 없습니다."

        except Exception as e:
            return f"Agent 오류: {e!s}"

    def _mock_response(self, query: str) -> str:
        """API 키가 없을 때 Mock 응답을 생성해요.

        Args:
            query: 사용자 쿼리

        Returns:
            str: Mock 응답
        """
        query_lower = query.lower()

        if "립" in query_lower or "lip" in query_lower:
            return """[Mock 응답 - API 키 설정 필요]

**Lip Sleeping Mask 분석:**

라네즈 립 슬리핑 마스크는 현재 Amazon Lip Care 카테고리에서
TOP 3 내 안정적인 순위를 유지하고 있습니다.

**주요 강점:**
- 오버나이트 트리트먼트 포지셔닝
- 비타민 C, 히알루론산 등 효능 성분
- Berry 향의 높은 선호도

실제 분석을 위해서는 .env 파일에 ANTHROPIC_API_KEY를 설정해주세요."""

        elif "순위" in query_lower or "랭킹" in query_lower:
            return """[Mock 응답 - API 키 설정 필요]

**LANEIGE 랭킹 요약:**

| 제품 | 카테고리 | 평균 순위 | 트렌드 |
|------|----------|-----------|--------|
| Lip Sleeping Mask | Lip Care | 2위 | 상승 |
| Water Sleeping Mask | Skincare | 15위 | 안정 |
| Cream Skin Refiner | Skincare | 12위 | 상승 |

실제 분석을 위해서는 .env 파일에 ANTHROPIC_API_KEY를 설정해주세요."""

        else:
            return """[Mock 응답 - API 키 설정 필요]

안녕하세요! 라네즈 글로벌 랭킹 분석 에이전트입니다.

**가능한 질문 예시:**
- "립 슬리핑 마스크 순위가 왜 떨어졌어?"
- "스킨케어 카테고리에서 라네즈 성과는?"
- "경쟁사 대비 강점이 뭐야?"
- "이번 달 랭킹 브리핑해줘"

실제 분석을 위해서는 .env 파일에 ANTHROPIC_API_KEY를 설정해주세요."""

    def get_welcome_message(self) -> str:
        """환영 메시지를 반환해요.

        Returns:
            str: 환영 메시지
        """
        return WELCOME_MESSAGE


if __name__ == "__main__":
    from backend.agent.vector_store import ProductVectorStore
    from backend.data.loader import load_all_products
    from backend.ranking import RankingService, get_ranking_provider

    print("Initializing Agent...")

    products = load_all_products()

    ranking_provider = get_ranking_provider(products)
    ranking_service = RankingService(ranking_provider)

    vector_store = ProductVectorStore()
    if vector_store.count() == 0:
        laneige_products = products[products["is_laneige"]]
        vector_store.add_products(laneige_products)

    agent = LaneigeAgent(vector_store=vector_store, ranking_service=ranking_service)

    print(agent.get_welcome_message())

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("대화를 종료합니다.")
            break

        response = agent.chat(user_input)
        print(f"\nAgent: {response}")
