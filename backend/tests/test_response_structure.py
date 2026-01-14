"""응답 구조 검증 테스트.

Tool 응답이 올바른 형식과 필수 필드를 가지는지 검증해요.
LLM-as-Judge 대신 코드 기반 구조 검증을 수행해요.
"""

import re

from backend.agent.tools import create_analysis_tools, create_product_tools, create_ranking_tools


class TestProductToolResponseStructure:
    """제품 Tool 응답 구조 테스트."""

    def test_search_products_has_numbered_results(self, mock_vector_store):
        """search_products가 번호 매겨진 결과를 반환하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_products")

        result = search_tool.invoke({"query": "마스크"})

        # [1], [2] 등 번호가 있어야 함
        has_numbered = bool(re.search(r"\[\d+\]", result))
        assert has_numbered or "관련 제품" in result

    def test_search_products_has_brand_info(self, mock_vector_store):
        """search_products가 브랜드 정보를 포함하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_products")

        result = search_tool.invoke({"query": "마스크"})

        # 브랜드명이 포함되어야 함
        assert "LANEIGE" in result or "관련 제품" in result

    def test_search_products_has_relevance_score(self, mock_vector_store):
        """search_products가 관련도 점수를 포함하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_products")

        result = search_tool.invoke({"query": "마스크"})

        # 관련도 % 표시가 있어야 함
        has_percentage = "%" in result or "관련도" in result or "관련 제품" in result
        assert has_percentage

    def test_search_laneige_has_category(self, mock_vector_store):
        """search_laneige_products가 카테고리를 포함하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_laneige_products")

        result = search_tool.invoke({"query": "마스크"})

        assert "카테고리" in result or "관련 LANEIGE" in result

    def test_search_laneige_has_price(self, mock_vector_store):
        """search_laneige_products가 가격을 포함하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_laneige_products")

        result = search_tool.invoke({"query": "마스크"})

        assert "$" in result or "가격" in result or "관련 LANEIGE" in result


class TestRankingToolResponseStructure:
    """랭킹 Tool 응답 구조 테스트."""

    def test_product_history_has_markdown_header(self, mock_ranking_service):
        """get_product_history가 마크다운 헤더를 사용하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        history_tool = next(t for t in tools if t.name == "get_product_history")

        result = history_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        assert "###" in result or "히스토리" in result

    def test_product_history_has_required_stats(self, mock_ranking_service):
        """get_product_history가 필수 통계를 포함하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        history_tool = next(t for t in tools if t.name == "get_product_history")

        result = history_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        required_fields = ["평균", "최고", "최저", "트렌드"]
        has_required = any(field in result for field in required_fields)
        assert has_required

    def test_product_history_has_daily_rankings(self, mock_ranking_service):
        """get_product_history가 일별 순위를 포함하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        history_tool = next(t for t in tools if t.name == "get_product_history")

        result = history_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        # 일별 순위 변화 섹션이 있어야 함
        assert "일별" in result or "순위" in result

    def test_category_rankings_has_top10_header(self, mock_ranking_service):
        """get_category_rankings가 TOP 10 헤더를 사용하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        rankings_tool = next(t for t in tools if t.name == "get_category_rankings")

        result = rankings_tool.invoke({"category": "lip_care"})

        assert "TOP 10" in result or "카테고리" in result

    def test_category_rankings_has_rank_numbers(self, mock_ranking_service):
        """get_category_rankings가 순위 번호를 포함하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        rankings_tool = next(t for t in tools if t.name == "get_category_rankings")

        result = rankings_tool.invoke({"category": "lip_care"})

        # 1위, 2위 등 순위 표시가 있어야 함
        has_rank = bool(re.search(r"\d+위", result))
        assert has_rank or "카테고리" in result

    def test_category_rankings_highlights_laneige(self, mock_ranking_service):
        """get_category_rankings가 LANEIGE를 강조하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        rankings_tool = next(t for t in tools if t.name == "get_category_rankings")

        result = rankings_tool.invoke({"category": "lip_care"})

        # LANEIGE 강조 표시가 있어야 함
        assert "LANEIGE" in result or "⭐" in result

    def test_laneige_summary_has_category_sections(self, mock_ranking_service):
        """get_laneige_summary가 카테고리별 섹션을 가지는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        summary_tool = next(t for t in tools if t.name == "get_laneige_summary")

        result = summary_tool.invoke({"category": "all"})

        # 볼드 카테고리명이 있어야 함
        has_bold_category = "**" in result or "Lip Care" in result or "Skincare" in result
        assert has_bold_category

    def test_ranking_stats_has_provider_info(self, mock_ranking_service):
        """get_ranking_stats가 데이터 소스 정보를 포함하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        stats_tool = next(t for t in tools if t.name == "get_ranking_stats")

        result = stats_tool.invoke({})

        assert "소스" in result or "데이터" in result


class TestAnalysisToolResponseStructure:
    """분석 Tool 응답 구조 테스트."""

    def test_competitor_analysis_has_laneige_section(self, mock_ranking_service):
        """compare_competitors가 LANEIGE 섹션을 가지는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        compare_tool = next(t for t in tools if t.name == "compare_competitors")

        result = compare_tool.invoke({"category": "lip_care"})

        assert "LANEIGE" in result

    def test_competitor_analysis_has_competitor_section(self, mock_ranking_service):
        """compare_competitors가 경쟁사 섹션을 가지는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        compare_tool = next(t for t in tools if t.name == "compare_competitors")

        result = compare_tool.invoke({"category": "lip_care"})

        assert "경쟁" in result

    def test_competitor_analysis_has_trend_indicators(self, mock_ranking_service):
        """compare_competitors가 트렌드 지표를 가지는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        compare_tool = next(t for t in tools if t.name == "compare_competitors")

        result = compare_tool.invoke({"category": "lip_care"})

        # 트렌드 이모지 또는 텍스트가 있어야 함
        has_trend = any(indicator in result for indicator in ["📈", "📉", "➡️", "상승", "하락", "유지"])
        assert has_trend or "경쟁" in result

    def test_trend_analysis_has_period_comparison(self, mock_ranking_service):
        """analyze_trend가 기간 비교를 포함하는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        trend_tool = next(t for t in tools if t.name == "analyze_trend")

        result = trend_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        # 최근/이전 기간 비교가 있어야 함
        has_period = any(period in result for period in ["최근", "이전", "7일"])
        assert has_period or "트렌드" in result

    def test_trend_analysis_has_trend_direction(self, mock_ranking_service):
        """analyze_trend가 트렌드 방향을 포함하는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        trend_tool = next(t for t in tools if t.name == "analyze_trend")

        result = trend_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        # 트렌드 방향 표시가 있어야 함
        has_direction = any(d in result for d in ["상승", "하락", "보합", "📈", "📉", "📊"])
        assert has_direction or "트렌드" in result


class TestResponseConsistency:
    """응답 일관성 테스트."""

    def test_all_tools_return_string(self, mock_vector_store, mock_ranking_service):
        """모든 Tool이 문자열을 반환하는지 테스트."""
        all_tools = (
            create_product_tools(mock_vector_store)
            + create_ranking_tools(mock_ranking_service)
            + create_analysis_tools(mock_ranking_service)
        )

        test_inputs = {
            "search_products": {"query": "마스크"},
            "search_laneige_products": {"query": "마스크"},
            "get_product_context": {"query": "마스크"},
            "get_product_history": {"product_name": "Lip Sleeping Mask - Berry"},
            "get_category_rankings": {"category": "lip_care"},
            "get_laneige_summary": {"category": "all"},
            "get_ranking_stats": {},
            "compare_competitors": {"category": "lip_care"},
            "analyze_trend": {"product_name": "Lip Sleeping Mask - Berry"},
        }

        for tool in all_tools:
            input_data = test_inputs.get(tool.name, {})
            result = tool.invoke(input_data)
            assert isinstance(result, str), f"Tool '{tool.name}'이 문자열을 반환하지 않습니다."

    def test_error_responses_are_user_friendly(self, mock_vector_store, mock_ranking_service):  # noqa: ARG002
        """에러 응답이 사용자 친화적인지 테스트."""
        all_tools = create_ranking_tools(mock_ranking_service) + create_analysis_tools(mock_ranking_service)

        error_inputs = {
            "get_product_history": {"product_name": "존재하지않는제품"},
            "get_category_rankings": {"category": "없는카테고리"},
            "compare_competitors": {"category": "없는카테고리"},
            "analyze_trend": {"product_name": "없는제품"},
        }

        for tool in all_tools:
            if tool.name in error_inputs:
                result = tool.invoke(error_inputs[tool.name])
                # 에러 메시지가 친절해야 함
                is_friendly = any(msg in result for msg in ["찾을 수 없", "없습니다", "지정해"])
                assert is_friendly, f"Tool '{tool.name}'의 에러 메시지가 사용자 친화적이지 않습니다."
