"""AI 채팅 엔진 모듈.

Anthropic Claude API를 활용한 RAG 기반 대화형 분석 엔진이에요.
"""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """당신은 아모레퍼시픽의 글로벌 뷰티 시장 분석 전문가입니다.
Amazon US와 @COSME JP의 뷰티 제품 랭킹 데이터를 분석하고 인사이트를 제공합니다.

주요 역할:
1. 라네즈(LANEIGE) 제품의 랭킹 변동 원인 분석
2. 경쟁사 제품 대비 강점/약점 파악
3. 시즌별/트렌드별 성과 예측
4. 마케팅 전략 제안

답변 원칙:
- 데이터에 기반한 객관적 분석 제공
- 라네즈 제품에 대한 심층적 인사이트 우선
- 간결하고 명확한 한국어로 답변
- 필요시 구체적인 수치와 비교 데이터 포함

제공된 컨텍스트 정보를 활용하여 질문에 답변하세요.
"""


class ChatEngine:
    """RAG 기반 AI 채팅 엔진.

    Vector Store와 랭킹 데이터를 컨텍스트로 활용하여
    Claude API로 대화형 분석을 제공해요.

    Attributes:
        vector_store: 제품 벡터 스토어
        ranking_engine: 랭킹 데이터 제공자
        model (str): 사용할 Claude 모델
        conversation_history (list[dict]): 대화 히스토리
        client: Anthropic API 클라이언트
    """

    def __init__(self, vector_store=None, ranking_engine=None, model: str = "claude-sonnet-4-20250514"):
        """ChatEngine을 초기화해요.

        Args:
            vector_store: 제품 벡터 스토어 (기본값: None)
            ranking_engine: 랭킹 데이터 제공자 (기본값: None)
            model (str): Claude 모델 ID (기본값: claude-sonnet-4-20250514)
        """
        self.vector_store = vector_store
        self.ranking_engine = ranking_engine
        self.model = model
        self.conversation_history: list[dict] = []

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None
            print("Warning: ANTHROPIC_API_KEY not set. Using mock responses.")

    def _get_rag_context(self, query: str) -> str:
        """RAG 컨텍스트를 조회해요.

        Args:
            query (str): 검색 쿼리

        Returns:
            str: 관련 제품 컨텍스트
        """
        if not self.vector_store:
            return ""

        return self.vector_store.get_product_context(query, n_results=5)

    def _get_ranking_context(self, query: str) -> str:
        """랭킹 컨텍스트를 조회해요.

        Args:
            query (str): 검색 쿼리

        Returns:
            str: 관련 랭킹 데이터 컨텍스트
        """
        if not self.ranking_engine:
            return ""

        context_parts = []
        query_lower = query.lower()

        laneige_products = [
            "Lip Sleeping Mask",
            "Water Sleeping Mask",
            "Cream Skin Refiner",
            "Neo Cushion Matte",
            "Lip Glowy Balm",
            "Radian-C Cream",
            "Bouncy & Firm Sleeping Mask",
            "Water Bank Hydro Essence",
            "Water Bank Blue Hyaluronic Cream",
            "Lip Sleeping Mask Vanilla",
        ]

        detected_products = []
        for product in laneige_products:
            if product.lower().replace(" ", "") in query_lower.replace(" ", ""):
                detected_products.append(product)

        categories = []
        if "립" in query_lower or "lip" in query_lower:
            categories.append("lip_care")
        if "스킨케어" in query_lower or "skincare" in query_lower or "크림" in query_lower:
            categories.append("skincare")

        if not categories:
            categories = ["lip_care", "skincare"]

        if detected_products and hasattr(self.ranking_engine, "get_product_history"):
            context_parts.append("\n### 제품별 30일 랭킹 히스토리:")
            for product in detected_products:
                history = self.ranking_engine.get_product_history(product, days=30)
                if history:
                    context_parts.append(f"\n**{product}**")
                    context_parts.append(f"- 카테고리: {history.get('category', 'N/A')}")
                    context_parts.append(f"- 평균 순위: {history.get('avg_rank', 'N/A')}위")
                    context_parts.append(f"- 최고 순위: {history.get('best_rank', 'N/A')}위")
                    context_parts.append(f"- 최저 순위: {history.get('worst_rank', 'N/A')}위")
                    context_parts.append(f"- 트렌드: {history.get('trend', 'N/A')}")

                    rankings = history.get("rankings", [])
                    dates = history.get("dates", [])
                    if rankings and dates:
                        context_parts.append("- 일별 순위 변화:")
                        for i, (d, r) in enumerate(zip(dates, rankings, strict=False)):
                            if i < len(rankings) - 1:
                                change = rankings[i] - rankings[i + 1]
                                change_str = f"(+{change})" if change > 0 else f"({change})" if change < 0 else "(=)"
                            else:
                                change_str = ""
                            context_parts.append(f"  {d}: {r}위 {change_str}")

        for category in categories:
            summary = self.ranking_engine.get_laneige_summary(category)
            if summary:
                context_parts.append(f"\n### {category.replace('_', ' ').title()} 라네즈 전체 요약:")
                for product, stats in summary.items():
                    context_parts.append(
                        f"- {product}: 평균 {stats['avg_rank']}위, "
                        f"최고 {stats['best_rank']}위, "
                        f"TOP5 {stats.get('top5_days', 0)}일"
                    )

        return "\n".join(context_parts)

    def _build_prompt(self, user_message: str) -> str:
        """RAG와 랭킹 컨텍스트를 포함한 프롬프트를 생성해요.

        Args:
            user_message (str): 사용자 메시지

        Returns:
            str: 컨텍스트가 포함된 전체 프롬프트
        """
        parts = []

        rag_context = self._get_rag_context(user_message)
        if rag_context:
            parts.append("## 관련 제품 정보")
            parts.append(rag_context)

        ranking_context = self._get_ranking_context(user_message)
        if ranking_context:
            parts.append("\n## 랭킹 데이터")
            parts.append(ranking_context)

        parts.append(f"\n## 질문\n{user_message}")

        return "\n".join(parts)

    def chat(self, user_message: str) -> str:
        """사용자 메시지에 대한 AI 응답을 생성해요.

        Args:
            user_message (str): 사용자 메시지

        Returns:
            str: AI 응답 메시지
        """
        full_prompt = self._build_prompt(user_message)

        self.conversation_history.append({"role": "user", "content": full_prompt})

        if self.client:
            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=2048, system=SYSTEM_PROMPT, messages=self.conversation_history
                )
                assistant_message = response.content[0].text
            except Exception as e:
                assistant_message = f"API 오류: {str(e)}"
        else:
            assistant_message = self._mock_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": assistant_message})

        return assistant_message

    def _mock_response(self, query: str) -> str:
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

**순위 변동 요인:**
- 계절성: 겨울철 보습 니즈 증가 시 순위 상승
- 경쟁사 신제품 출시 시 일시적 하락 가능

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

    def clear_history(self):
        self.conversation_history = []

    def get_welcome_message(self) -> str:
        return """
안녕하세요! 라네즈 글로벌 랭킹 인사이트 에이전트입니다.

Amazon US와 @COSME JP의 랭킹 데이터를 기반으로
라네즈 제품의 성과를 분석해드립니다.

**질문 예시:**
- "립 슬리핑 마스크 순위가 왜 떨어졌어?"
- "스킨케어 카테고리에서 라네즈 현황은?"
- "경쟁사 대비 우리 제품 강점이 뭐야?"
- "이번 주 랭킹 특이사항 브리핑해줘"

무엇이든 물어보세요! ('exit' 입력 시 종료)
"""


if __name__ == "__main__":
    from src.data.loader import load_all_products
    from src.mock_engine.ranking_engine import MockRankingEngine
    from src.rag.vector_store import ProductVectorStore

    print("Initializing...")

    products = load_all_products()

    ranking_engine = MockRankingEngine(products)
    ranking_engine.generate_all_categories(days=14)

    vector_store = ProductVectorStore()
    if vector_store.count() == 0:
        laneige_products = products[products["is_laneige"]]
        vector_store.add_products(laneige_products)

    chat_engine = ChatEngine(vector_store=vector_store, ranking_engine=ranking_engine)

    print(chat_engine.get_welcome_message())

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("대화를 종료합니다.")
            break

        response = chat_engine.chat(user_input)
        print(f"\nAgent: {response}")
