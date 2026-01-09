"""랭킹 조회 Tool 모듈.

RankingService를 활용한 랭킹 조회 Tool을 제공해요.
"""

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from backend.ranking import RankingService


def create_ranking_tools(ranking_service: "RankingService") -> list:
    """랭킹 조회 관련 Tool을 생성해요.

    Args:
        ranking_service: 랭킹 서비스

    Returns:
        list: LangChain Tool 리스트
    """

    @tool
    def get_product_history(product_name: str, days: int = 30) -> str:
        """특정 제품의 랭킹 히스토리를 조회해요. 순위 변동 추이를 확인할 때 사용해요.

        Args:
            product_name: 제품명 (예: "Lip Sleeping Mask", "Water Bank")
            days: 조회 일수 (기본값: 30)

        Returns:
            str: 제품의 랭킹 히스토리 정보
        """
        history = ranking_service.get_product_history(product_name, days)

        if not history:
            return f"'{product_name}' 제품의 랭킹 히스토리를 찾을 수 없습니다."

        output_parts = [
            f"### {product_name} 랭킹 히스토리 ({days}일)",
            f"- 카테고리: {history.get('category', 'N/A')}",
            f"- 평균 순위: {history.get('avg_rank', 'N/A')}위",
            f"- 최고 순위: {history.get('best_rank', 'N/A')}위",
            f"- 최저 순위: {history.get('worst_rank', 'N/A')}위",
            f"- 트렌드: {history.get('trend', 'N/A')}",
        ]

        rankings = history.get("rankings", [])
        dates = history.get("dates", [])
        if rankings and dates:
            output_parts.append("\n일별 순위 변화:")
            for i, (d, r) in enumerate(zip(dates[-7:], rankings[-7:], strict=False)):
                change_str = ""
                if i < len(rankings) - 1:
                    change = rankings[i] - rankings[i + 1]
                    if change > 0:
                        change_str = f" (+{change})"
                    elif change < 0:
                        change_str = f" ({change})"
                output_parts.append(f"  {d}: {r}위{change_str}")

        return "\n".join(output_parts)

    @tool
    def get_category_rankings(category: str, days: int = 30) -> str:
        """특정 카테고리의 전체 랭킹을 조회해요. 카테고리 내 경쟁 현황을 파악할 때 사용해요.

        Args:
            category: 카테고리명 (lip_care, skincare, makeup 등)
            days: 조회 일수 (기본값: 30)

        Returns:
            str: 카테고리 랭킹 정보 (TOP 10)
        """
        df = ranking_service.get_rankings(category, days)

        if df.empty:
            return f"'{category}' 카테고리의 랭킹 데이터를 찾을 수 없습니다."

        day_cols = [c for c in df.columns if c.startswith("day_")]
        if day_cols:
            df["current_rank"] = df[day_cols[-1]]
            df = df.sort_values("current_rank")

        output_parts = [f"### {category} 카테고리 TOP 10"]

        for _, row in df.head(10).iterrows():
            is_laneige = " ⭐LANEIGE" if row.get("is_laneige", False) else ""
            output_parts.append(f"{int(row['current_rank'])}위. {row['product_name']} ({row['brand']}){is_laneige}")

        laneige_count = len(df[df["is_laneige"] == True])  # noqa: E712
        output_parts.append(f"\n(LANEIGE 제품: {laneige_count}개)")

        return "\n".join(output_parts)

    @tool
    def get_laneige_summary(category: str = "all") -> str:
        """LANEIGE 제품의 성과 요약을 조회해요. 라네즈 전체 성과를 파악할 때 사용해요.

        Args:
            category: 카테고리명 (기본값: "all"이면 전체)

        Returns:
            str: LANEIGE 제품별 성과 요약
        """
        categories = ["lip_care", "skincare", "makeup"] if category == "all" else [category]

        output_parts = ["### LANEIGE 제품 성과 요약"]

        for cat in categories:
            summary = ranking_service.get_laneige_summary(cat)
            if summary:
                output_parts.append(f"\n**{cat.replace('_', ' ').title()}**")
                for product, stats in summary.items():
                    top5_days = stats.get("top5_days", 0)
                    status = "🔥 TOP5 유지" if top5_days >= 20 else ""
                    output_parts.append(
                        f"- {product}: 평균 {stats['avg_rank']}위, 최고 {stats['best_rank']}위 {status}"
                    )

        if len(output_parts) == 1:
            return "LANEIGE 제품 데이터를 찾을 수 없습니다."

        return "\n".join(output_parts)

    @tool
    def get_ranking_stats() -> str:
        """랭킹 데이터베이스 통계를 조회해요. 데이터 현황을 파악할 때 사용해요.

        Returns:
            str: DB 통계 정보
        """
        stats = ranking_service.get_stats()

        output_parts = [
            "### 랭킹 데이터 현황",
            f"- 수집된 일수: {stats['total_dates']}일",
            f"- 카테고리: {', '.join(stats['categories'])}",
            f"- 데이터 소스: {stats['provider']}",
            f"- 실시간 데이터: {'예' if stats['is_live_data'] else '아니오 (Mock)'}",
        ]

        return "\n".join(output_parts)

    return [get_product_history, get_category_rankings, get_laneige_summary, get_ranking_stats]
