"""pytest fixture 설정.

테스트에서 사용할 Mock 데이터와 서비스를 제공해요.
"""

from datetime import date, timedelta

import pandas as pd
import pytest

# Mock 랭킹 데이터
MOCK_RANKING_DATA = {
    "lip_care": pd.DataFrame(
        {
            "product_id": ["B001", "B002", "B003", "B004", "B005"],
            "product_name": [
                "Lip Sleeping Mask - Berry",
                "Lip Glowy Balm - Berry",
                "Burt's Bees Lip Balm",
                "Vaseline Lip Therapy",
                "Aquaphor Lip Repair",
            ],
            "brand": ["LANEIGE", "LANEIGE", "Burt's Bees", "Vaseline", "Aquaphor"],
            "is_laneige": [True, True, False, False, False],
            "price": [24.0, 17.0, 5.0, 4.0, 6.0],
            "day_1": [2, 8, 1, 3, 4],
            "day_2": [2, 7, 1, 4, 3],
            "day_3": [3, 6, 1, 4, 2],
            "day_4": [2, 5, 1, 3, 4],
            "day_5": [2, 5, 1, 4, 3],
        }
    ),
    "skincare": pd.DataFrame(
        {
            "product_id": ["S001", "S002", "S003", "S004"],
            "product_name": [
                "Water Sleeping Mask",
                "CeraVe Moisturizing Cream",
                "Neutrogena Hydro Boost",
                "Cream Skin Refiner",
            ],
            "brand": ["LANEIGE", "CeraVe", "Neutrogena", "LANEIGE"],
            "is_laneige": [True, False, False, True],
            "price": [32.0, 19.0, 22.0, 35.0],
            "day_1": [12, 1, 2, 15],
            "day_2": [10, 1, 3, 14],
            "day_3": [11, 2, 1, 13],
            "day_4": [9, 1, 2, 12],
            "day_5": [8, 1, 3, 11],
        }
    ),
}

# Mock 제품 히스토리 데이터
MOCK_PRODUCT_HISTORY = {
    "Lip Sleeping Mask - Berry": {
        "product_name": "Lip Sleeping Mask - Berry",
        "category": "lip_care",
        "brand": "LANEIGE",
        "is_laneige": True,
        "rankings": [3, 2, 2, 3, 2, 2, 2],
        "dates": [
            (date.today() - timedelta(days=6)).isoformat(),
            (date.today() - timedelta(days=5)).isoformat(),
            (date.today() - timedelta(days=4)).isoformat(),
            (date.today() - timedelta(days=3)).isoformat(),
            (date.today() - timedelta(days=2)).isoformat(),
            (date.today() - timedelta(days=1)).isoformat(),
            date.today().isoformat(),
        ],
        "avg_rank": 2.3,
        "best_rank": 2,
        "worst_rank": 3,
        "trend": "rising",
    },
    "Water Sleeping Mask": {
        "product_name": "Water Sleeping Mask",
        "category": "skincare",
        "brand": "LANEIGE",
        "is_laneige": True,
        "rankings": [12, 10, 11, 9, 8],
        "dates": [
            (date.today() - timedelta(days=4)).isoformat(),
            (date.today() - timedelta(days=3)).isoformat(),
            (date.today() - timedelta(days=2)).isoformat(),
            (date.today() - timedelta(days=1)).isoformat(),
            date.today().isoformat(),
        ],
        "avg_rank": 10.0,
        "best_rank": 8,
        "worst_rank": 12,
        "trend": "rising",
    },
}

# Mock LANEIGE 요약 데이터
MOCK_LANEIGE_SUMMARY = {
    "lip_care": {
        "Lip Sleeping Mask - Berry": {
            "avg_rank": 2.3,
            "best_rank": 2,
            "worst_rank": 3,
            "current_rank": 2,
            "trend": "rising",
            "top5_days": 5,
            "top10_days": 5,
        },
        "Lip Glowy Balm - Berry": {
            "avg_rank": 6.2,
            "best_rank": 5,
            "worst_rank": 8,
            "current_rank": 5,
            "trend": "rising",
            "top5_days": 2,
            "top10_days": 5,
        },
    },
    "skincare": {
        "Water Sleeping Mask": {
            "avg_rank": 10.0,
            "best_rank": 8,
            "worst_rank": 12,
            "current_rank": 8,
            "trend": "rising",
            "top5_days": 0,
            "top10_days": 2,
        },
    },
}


class MockRankingService:
    """Mock RankingService."""

    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:  # noqa: ARG002
        """카테고리별 랭킹을 반환해요. days 파라미터는 인터페이스 호환을 위해 유지."""
        del days  # 인터페이스 호환용 (사용하지 않음)
        return MOCK_RANKING_DATA.get(category, pd.DataFrame())

    def get_product_history(self, product_name: str, days: int = 30) -> dict | None:  # noqa: ARG002
        """제품 히스토리를 반환해요. days 파라미터는 인터페이스 호환을 위해 유지."""
        del days  # 인터페이스 호환용 (사용하지 않음)
        return MOCK_PRODUCT_HISTORY.get(product_name)

    def get_laneige_summary(self, category: str) -> dict:
        return MOCK_LANEIGE_SUMMARY.get(category, {})

    def get_stats(self) -> dict:
        return {
            "total_dates": 30,
            "categories": ["lip_care", "skincare", "makeup"],
            "provider": "MockProvider",
            "is_live_data": False,
        }


class MockVectorStore:
    """Mock VectorStore."""

    def search(self, query: str, n_results: int = 5, filter_laneige: bool = False) -> list:  # noqa: ARG002
        """제품을 검색해요. query 파라미터는 인터페이스 호환을 위해 유지."""
        del query  # 인터페이스 호환용 (사용하지 않음)
        mock_results = [
            {
                "metadata": {
                    "product_name": "Lip Sleeping Mask - Berry",
                    "brand": "LANEIGE",
                    "category": "lip_care",
                    "price": 24.0,
                    "is_laneige": True,
                },
                "relevance_score": 0.95,
            },
            {
                "metadata": {
                    "product_name": "Water Sleeping Mask",
                    "brand": "LANEIGE",
                    "category": "skincare",
                    "price": 32.0,
                    "is_laneige": True,
                },
                "relevance_score": 0.82,
            },
        ]

        if filter_laneige:
            return [r for r in mock_results if r["metadata"].get("is_laneige")]
        return mock_results[:n_results]

    def get_product_context(self, query: str, n_results: int = 3) -> str:  # noqa: ARG002
        """제품 컨텍스트를 반환해요. 파라미터는 인터페이스 호환을 위해 유지."""
        del query, n_results  # 인터페이스 호환용 (사용하지 않음)
        return "Lip Sleeping Mask: 비타민C, 히알루론산 함유. Berry 향. 오버나이트 트리트먼트."

    def count(self) -> int:
        return 10


@pytest.fixture
def mock_ranking_service():
    """Mock RankingService fixture."""
    return MockRankingService()


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore fixture."""
    return MockVectorStore()


@pytest.fixture
def mock_agent(mock_vector_store, mock_ranking_service):
    """API 키 없이 동작하는 Mock Agent fixture."""
    from backend.agent.laneige_agent import LaneigeAgent

    agent = LaneigeAgent(
        vector_store=mock_vector_store,
        ranking_service=mock_ranking_service,
    )
    return agent


# Tool 선택 테스트용 Ground Truth 데이터
TOOL_SELECTION_TEST_CASES = [
    # (질문, 예상 호출 Tool 이름들)
    ("립 슬리핑 마스크 성분이 뭐야?", ["search_products", "search_laneige_products", "get_product_context"]),
    ("스킨케어 카테고리 순위 알려줘", ["get_category_rankings"]),
    ("라네즈 전체 성과 요약해줘", ["get_laneige_summary"]),
    ("립 슬리핑 마스크 순위가 왜 떨어졌어?", ["get_product_history", "analyze_trend"]),
    ("립케어에서 경쟁사 대비 어때?", ["compare_competitors"]),
    ("데이터 현황 알려줘", ["get_ranking_stats"]),
    ("워터뱅크 제품 정보 찾아줘", ["search_products", "search_laneige_products"]),
    ("스킨케어 트렌드 분석해줘", ["analyze_trend"]),
]


@pytest.fixture
def tool_selection_test_cases():
    """Tool 선택 테스트 케이스 fixture."""
    return TOOL_SELECTION_TEST_CASES
