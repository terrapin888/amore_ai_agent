"""분석 Tool 모듈.

경쟁사 비교, 트렌드 분석 등 고급 분석 Tool을 제공해요.
"""

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from backend.ranking import RankingService


def create_analysis_tools(ranking_service: "RankingService") -> list:
    """분석 관련 Tool을 생성해요.

    Args:
        ranking_service: 랭킹 서비스

    Returns:
        list: LangChain Tool 리스트
    """

    @tool
    def compare_competitors(category: str, laneige_product: str = "") -> str:
        """LANEIGE 제품과 경쟁사 제품을 비교 분석해요. 경쟁 우위/열위를 파악할 때 사용해요.

        Args:
            category: 카테고리명 (lip_care, skincare, makeup)
            laneige_product: 비교할 라네즈 제품명 (선택사항)

        Returns:
            str: 경쟁사 비교 분석 결과
        """
        df = ranking_service.get_rankings(category, days=30)

        if df.empty:
            return f"'{category}' 카테고리 데이터를 찾을 수 없습니다."

        day_cols = [c for c in df.columns if c.startswith("day_")]
        if day_cols:
            df["current_rank"] = df[day_cols[-1]]
            df["avg_rank"] = df[day_cols].mean(axis=1)
            df = df.sort_values("current_rank")

        laneige_df = df[df["is_laneige"] == True]  # noqa: E712
        competitor_df = df[df["is_laneige"] == False].head(5)  # noqa: E712

        output_parts = [f"### {category} 경쟁 분석"]

        output_parts.append("\n**LANEIGE 제품:**")
        for _, row in laneige_df.iterrows():
            trend = _calculate_trend(row, day_cols)
            output_parts.append(
                f"- {row['product_name']}: {int(row['current_rank'])}위 (평균 {row['avg_rank']:.1f}위) {trend}"
            )

        output_parts.append("\n**주요 경쟁사 제품 (TOP 5):**")
        for _, row in competitor_df.iterrows():
            trend = _calculate_trend(row, day_cols)
            output_parts.append(f"- {row['product_name']} ({row['brand']}): {int(row['current_rank'])}위 {trend}")

        if not laneige_df.empty and not competitor_df.empty:
            avg_laneige = laneige_df["avg_rank"].mean()
            avg_competitor = competitor_df["avg_rank"].mean()
            gap = avg_laneige - avg_competitor

            output_parts.append("\n**분석:**")
            if gap < 0:
                output_parts.append(f"- LANEIGE가 경쟁사 대비 평균 {abs(gap):.1f}위 앞서 있습니다.")
            else:
                output_parts.append(f"- LANEIGE가 경쟁사 대비 평균 {gap:.1f}위 뒤쳐져 있습니다.")

        return "\n".join(output_parts)

    @tool
    def analyze_trend(product_name: str = "", category: str = "") -> str:
        """제품 또는 카테고리의 트렌드를 분석해요. 상승/하락 추세를 파악할 때 사용해요.

        Args:
            product_name: 분석할 제품명 (예: "Lip Sleeping Mask")
            category: 분석할 카테고리 (예: "lip_care", "skincare")

        Returns:
            str: 트렌드 분석 결과
        """
        if product_name:
            history = ranking_service.get_product_history(product_name, days=30)

            if not history:
                return f"'{product_name}' 제품을 찾을 수 없습니다."

            rankings = history.get("rankings", [])
            if len(rankings) < 7:
                return "트렌드 분석에 충분한 데이터가 없습니다 (최소 7일 필요)."

            recent_avg = sum(rankings[-7:]) / 7
            older_avg = sum(rankings[:7]) / 7 if len(rankings) >= 14 else sum(rankings[:-7]) / max(1, len(rankings) - 7)

            change = older_avg - recent_avg

            output_parts = [
                f"### {product_name} 트렌드 분석",
                f"- 최근 7일 평균: {recent_avg:.1f}위",
                f"- 이전 7일 평균: {older_avg:.1f}위",
            ]

            if change > 2:
                output_parts.append(f"- 트렌드: 📈 상승세 (+{change:.1f}위)")
                output_parts.append("- 분석: 순위가 크게 상승하고 있습니다.")
            elif change > 0:
                output_parts.append(f"- 트렌드: 📊 소폭 상승 (+{change:.1f}위)")
            elif change > -2:
                output_parts.append(f"- 트렌드: 📊 보합세 ({change:.1f}위)")
            else:
                output_parts.append(f"- 트렌드: 📉 하락세 ({change:.1f}위)")
                output_parts.append("- 분석: 순위가 하락하고 있어 원인 분석이 필요합니다.")

            return "\n".join(output_parts)

        elif category:
            df = ranking_service.get_rankings(category, days=30)

            if df.empty:
                return f"'{category}' 카테고리를 찾을 수 없습니다."

            day_cols = [c for c in df.columns if c.startswith("day_")]
            laneige_df = df[df["is_laneige"] == True]  # noqa: E712

            output_parts = [f"### {category} 카테고리 LANEIGE 트렌드"]

            for _, row in laneige_df.iterrows():
                trend = _calculate_trend(row, day_cols)
                output_parts.append(f"- {row['product_name']}: {trend}")

            return "\n".join(output_parts)

        return "분석할 제품명이나 카테고리를 지정해주세요."

    def _calculate_trend(row, day_cols: list) -> str:
        """순위 변동 트렌드를 계산해요."""
        if len(day_cols) < 2:
            return ""

        recent = row[day_cols[-1]]
        older = row[day_cols[0]]

        if recent < older:
            return "📈 상승"
        elif recent > older:
            return "📉 하락"
        else:
            return "➡️ 유지"

    return [compare_competitors, analyze_trend]
