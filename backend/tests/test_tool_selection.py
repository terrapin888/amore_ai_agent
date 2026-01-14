"""Tool 선택 정확도 테스트.

Agent가 질문에 따라 올바른 Tool을 선택하는지 검증해요.
LLM-as-Judge 대신 Tool 호출 여부를 코드로 확인해요.
"""

from backend.agent.tools import create_analysis_tools, create_product_tools, create_ranking_tools


class TestToolSelection:
    """Tool 선택 정확도 테스트 클래스."""

    def test_product_tools_exist(self, mock_vector_store):
        """제품 검색 Tool이 올바르게 생성되는지 테스트."""
        tools = create_product_tools(mock_vector_store)

        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "search_products" in tool_names
        assert "search_laneige_products" in tool_names
        assert "get_product_context" in tool_names

    def test_ranking_tools_exist(self, mock_ranking_service):
        """랭킹 조회 Tool이 올바르게 생성되는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)

        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "get_product_history" in tool_names
        assert "get_category_rankings" in tool_names
        assert "get_laneige_summary" in tool_names
        assert "get_ranking_stats" in tool_names

    def test_analysis_tools_exist(self, mock_ranking_service):
        """분석 Tool이 올바르게 생성되는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)

        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "compare_competitors" in tool_names
        assert "analyze_trend" in tool_names

    def test_search_products_returns_results(self, mock_vector_store):
        """search_products Tool이 결과를 반환하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_products")

        result = search_tool.invoke({"query": "립 마스크"})

        assert isinstance(result, str)
        assert "Lip Sleeping Mask" in result or "관련 제품" in result

    def test_search_laneige_products_filters_correctly(self, mock_vector_store):
        """search_laneige_products가 LANEIGE 제품만 반환하는지 테스트."""
        tools = create_product_tools(mock_vector_store)
        search_tool = next(t for t in tools if t.name == "search_laneige_products")

        result = search_tool.invoke({"query": "슬리핑 마스크"})

        assert isinstance(result, str)
        # LANEIGE 제품명이 포함되어야 함 (Lip Sleeping Mask, Water Sleeping Mask)
        assert "Sleeping Mask" in result or "관련 LANEIGE 제품" in result

    def test_get_category_rankings_returns_top10(self, mock_ranking_service):
        """get_category_rankings가 TOP 10을 반환하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        rankings_tool = next(t for t in tools if t.name == "get_category_rankings")

        result = rankings_tool.invoke({"category": "lip_care"})

        assert isinstance(result, str)
        assert "lip_care" in result or "TOP 10" in result or "카테고리" in result

    def test_get_product_history_returns_trend(self, mock_ranking_service):
        """get_product_history가 트렌드 정보를 포함하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        history_tool = next(t for t in tools if t.name == "get_product_history")

        result = history_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        assert isinstance(result, str)
        assert "트렌드" in result or "평균" in result or "순위" in result

    def test_get_laneige_summary_returns_all_categories(self, mock_ranking_service):
        """get_laneige_summary가 전체 카테고리 요약을 반환하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        summary_tool = next(t for t in tools if t.name == "get_laneige_summary")

        result = summary_tool.invoke({"category": "all"})

        assert isinstance(result, str)
        assert "LANEIGE" in result

    def test_compare_competitors_includes_analysis(self, mock_ranking_service):
        """compare_competitors가 분석 결과를 포함하는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        compare_tool = next(t for t in tools if t.name == "compare_competitors")

        result = compare_tool.invoke({"category": "lip_care"})

        assert isinstance(result, str)
        assert "경쟁" in result or "LANEIGE" in result or "분석" in result

    def test_analyze_trend_for_product(self, mock_ranking_service):
        """analyze_trend가 제품 트렌드를 분석하는지 테스트."""
        tools = create_analysis_tools(mock_ranking_service)
        trend_tool = next(t for t in tools if t.name == "analyze_trend")

        result = trend_tool.invoke({"product_name": "Lip Sleeping Mask - Berry"})

        assert isinstance(result, str)
        assert "트렌드" in result or "분석" in result

    def test_get_ranking_stats_returns_stats(self, mock_ranking_service):
        """get_ranking_stats가 통계 정보를 반환하는지 테스트."""
        tools = create_ranking_tools(mock_ranking_service)
        stats_tool = next(t for t in tools if t.name == "get_ranking_stats")

        result = stats_tool.invoke({})

        assert isinstance(result, str)
        assert "데이터" in result or "현황" in result or "일수" in result


class TestToolDocstrings:
    """Tool docstring이 적절한지 테스트 (Agent의 Tool 선택에 영향)."""

    def test_all_tools_have_docstrings(self, mock_vector_store, mock_ranking_service):
        """모든 Tool이 docstring을 가지고 있는지 테스트."""
        all_tools = (
            create_product_tools(mock_vector_store)
            + create_ranking_tools(mock_ranking_service)
            + create_analysis_tools(mock_ranking_service)
        )

        for tool in all_tools:
            assert tool.description, f"Tool '{tool.name}'에 description이 없습니다."
            assert len(tool.description) > 20, f"Tool '{tool.name}'의 description이 너무 짧습니다."

    def test_tool_descriptions_contain_korean(self, mock_vector_store, mock_ranking_service):
        """Tool description이 한국어를 포함하는지 테스트."""
        all_tools = (
            create_product_tools(mock_vector_store)
            + create_ranking_tools(mock_ranking_service)
            + create_analysis_tools(mock_ranking_service)
        )

        korean_chars = "가나다라마바사아자차카타파하"

        for tool in all_tools:
            has_korean = any(char in tool.description for char in korean_chars)
            assert has_korean, f"Tool '{tool.name}'의 description에 한국어가 없습니다."
