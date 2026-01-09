"""제품 검색 Tool 모듈.

VectorStore를 활용한 제품 검색 Tool을 제공해요.
"""

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from backend.agent.vector_store import ProductVectorStore


def create_product_tools(vector_store: "ProductVectorStore") -> list:
    """제품 검색 관련 Tool을 생성해요.

    Args:
        vector_store: 제품 벡터 스토어

    Returns:
        list: LangChain Tool 리스트
    """

    @tool
    def search_products(query: str, n_results: int = 5) -> str:
        """제품 정보를 검색해요. 제품 성분, 특징, 브랜드 등을 찾을 때 사용해요.

        Args:
            query: 검색 쿼리 (예: "비타민C 함유 립 제품", "보습 크림 추천")
            n_results: 반환할 결과 수 (기본값: 5)

        Returns:
            str: 검색된 제품 정보
        """
        results = vector_store.search(query, n_results=n_results)

        if not results:
            return "관련 제품 정보를 찾을 수 없습니다."

        output_parts = []
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            output_parts.append(
                f"[{i}] {metadata['product_name']} ({metadata['brand']})\n"
                f"    카테고리: {metadata.get('category', 'N/A')}\n"
                f"    관련도: {result['relevance_score']:.1%}"
            )

        return "\n\n".join(output_parts)

    @tool
    def search_laneige_products(query: str, n_results: int = 5) -> str:
        """LANEIGE 제품만 검색해요. 라네즈 제품 정보가 필요할 때 사용해요.

        Args:
            query: 검색 쿼리 (예: "립 슬리핑 마스크", "워터뱅크")
            n_results: 반환할 결과 수 (기본값: 5)

        Returns:
            str: 검색된 라네즈 제품 정보
        """
        results = vector_store.search(query, n_results=n_results, filter_laneige=True)

        if not results:
            return "관련 LANEIGE 제품 정보를 찾을 수 없습니다."

        output_parts = []
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            output_parts.append(
                f"[{i}] {metadata['product_name']}\n"
                f"    카테고리: {metadata.get('category', 'N/A')}\n"
                f"    가격: ${metadata.get('price', 'N/A')}\n"
                f"    관련도: {result['relevance_score']:.1%}"
            )

        return "\n\n".join(output_parts)

    @tool
    def get_product_context(query: str) -> str:
        """질문에 관련된 제품 컨텍스트를 가져와요. 상세 정보가 필요할 때 사용해요.

        Args:
            query: 검색 쿼리

        Returns:
            str: 관련 제품들의 상세 컨텍스트
        """
        return vector_store.get_product_context(query, n_results=3)

    return [search_products, search_laneige_products, get_product_context]
