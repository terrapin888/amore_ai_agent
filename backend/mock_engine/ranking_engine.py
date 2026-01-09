"""Mock 랭킹 엔진 모듈.

다양한 시나리오 기반으로 랭킹 히스토리를 시뮬레이션해요.
날짜별 랭킹 기록을 생성하여 테스트 및 개발에 활용해요.
"""

import random
from datetime import datetime, timedelta
from enum import Enum

import pandas as pd


class RankingScenario(Enum):
    """랭킹 시나리오 열거형.

    제품의 랭킹 변화 패턴을 정의해요.

    Attributes:
        BEST_SELLER: 베스트셀러 (항상 상위권)
        RISING_STAR: 떠오르는 제품 (순위 상승 중)
        STABLE: 안정적 (순위 유지)
        DECLINING: 하락세 (순위 하락 중)
        COMPETITOR_SHOCK: 경쟁사 충격 (급변동)
        NEW_ENTRY: 신규 진입 (새로 시장에 등장)
    """

    BEST_SELLER = "best_seller"
    RISING_STAR = "rising_star"
    STABLE = "stable"
    DECLINING = "declining"
    COMPETITOR_SHOCK = "competitor_shock"
    NEW_ENTRY = "new_entry"


LANEIGE_SCENARIOS = {
    "Lip Sleeping Mask": RankingScenario.BEST_SELLER,
    "Lip Sleeping Mask Vanilla": RankingScenario.RISING_STAR,
    "Water Bank Blue Hyaluronic Cream": RankingScenario.STABLE,
    "Cream Skin Refiner": RankingScenario.RISING_STAR,
    "Water Sleeping Mask": RankingScenario.BEST_SELLER,
    "Neo Cushion Matte": RankingScenario.NEW_ENTRY,
    "Lip Glowy Balm": RankingScenario.STABLE,
    "Radian-C Cream": RankingScenario.NEW_ENTRY,
}


class MockRankingEngine:
    """Mock 랭킹 시뮬레이션 엔진.

    제품별 시나리오를 기반으로 날짜별 랭킹 히스토리를 생성해요.

    Attributes:
        products: 제품 데이터프레임
        ranking_history (dict): 카테고리별 랭킹 히스토리
    """

    def __init__(self, products_df: pd.DataFrame):
        """MockRankingEngine을 초기화해요.

        Args:
            products_df: 제품 정보가 담긴 데이터프레임
        """
        self.products = products_df.copy()
        self.ranking_history: dict[str, pd.DataFrame] = {}

    def _apply_scenario(self, scenario: RankingScenario, day_index: int, total_days: int, base_rank: int = 50) -> int:
        """시나리오에 따른 랭킹을 계산해요.

        Args:
            scenario: 적용할 랭킹 시나리오
            day_index: 현재 일차 인덱스 (0부터 시작)
            total_days: 전체 일수
            base_rank: 기본 순위 (기본값: 50)

        Returns:
            int: 해당 일차의 순위
        """
        progress = day_index / max(total_days - 1, 1)

        if scenario == RankingScenario.BEST_SELLER:
            return random.randint(1, 5)

        elif scenario == RankingScenario.RISING_STAR:
            start_rank = 50
            end_rank = random.randint(5, 15)
            current_rank = int(start_rank - (start_rank - end_rank) * progress)
            return max(1, current_rank + random.randint(-3, 3))

        elif scenario == RankingScenario.STABLE:
            return random.randint(15, 25)

        elif scenario == RankingScenario.DECLINING:
            start_rank = 10
            end_rank = 40
            current_rank = int(start_rank + (end_rank - start_rank) * progress)
            return min(100, current_rank + random.randint(-2, 5))

        elif scenario == RankingScenario.COMPETITOR_SHOCK:
            if progress < 0.3:
                return random.randint(10, 15)
            elif progress < 0.6:
                return random.randint(30, 50)
            else:
                return random.randint(15, 25)

        elif scenario == RankingScenario.NEW_ENTRY:
            if progress < 0.2:
                return random.randint(80, 100)
            elif progress < 0.5:
                return random.randint(40, 60)
            else:
                return random.randint(20, 35)

        return base_rank

    def generate_ranking_history(
        self, category: str, days: int = 30, start_date: datetime | None = None
    ) -> pd.DataFrame:
        """카테고리별 랭킹 히스토리를 생성해요.

        Args:
            category: Amazon 카테고리 이름
            days: 생성할 일수 (기본값: 30)
            start_date: 시작 날짜 (기본값: None, 현재 날짜 - days)

        Returns:
            pd.DataFrame: 날짜별 랭킹 기록이 담긴 데이터프레임
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        category_products = self.products[self.products["amazon_category"] == category].copy()

        if len(category_products) == 0:
            category_products = self.products[
                self.products["category"].str.lower().str.contains(category.lower().replace("_", " "))
            ].copy()

        if len(category_products) == 0:
            return pd.DataFrame()

        dates = [start_date + timedelta(days=i) for i in range(days)]
        history_records = []

        for day_idx, date in enumerate(dates):
            daily_rankings = []

            for _, product in category_products.iterrows():
                product_name = product["product_name"]
                is_laneige = product.get("is_laneige", False)

                if is_laneige and product_name in LANEIGE_SCENARIOS:
                    scenario = LANEIGE_SCENARIOS[product_name]
                elif is_laneige:
                    scenario = RankingScenario.STABLE
                else:
                    scenario = random.choice(
                        [
                            RankingScenario.STABLE,
                            RankingScenario.RISING_STAR,
                            RankingScenario.DECLINING,
                        ]
                    )

                rank = self._apply_scenario(scenario, day_idx, days)

                daily_rankings.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "product_id": product.get("product_id", 0),
                        "product_name": product_name,
                        "brand": product["brand"],
                        "rank": rank,
                        "category": category,
                        "is_laneige": is_laneige,
                        "scenario": scenario.value if is_laneige else "competitor",
                    }
                )

            daily_rankings.sort(key=lambda x: x["rank"])
            for i, record in enumerate(daily_rankings):
                record["rank"] = i + 1
                history_records.append(record)

        history_df = pd.DataFrame(history_records)
        self.ranking_history[category] = history_df

        return history_df

    def generate_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """모든 카테고리의 랭킹 히스토리를 생성해요.

        Args:
            days: 생성할 일수 (기본값: 30)

        Returns:
            dict: 카테고리명을 키로 하는 데이터프레임 딕셔너리
        """
        categories = ["lip_care", "skincare", "lip_makeup", "face_powder"]
        results = {}

        for category in categories:
            df = self.generate_ranking_history(category, days)
            if len(df) > 0:
                results[category] = df

        return results

    def get_laneige_summary(self, category: str) -> dict:
        """LANEIGE 제품의 랭킹 요약을 반환해요.

        Args:
            category: 카테고리

        Returns:
            dict: 제품명을 키로 하는 통계 딕셔너리
        """
        if category not in self.ranking_history:
            return {}

        df = self.ranking_history[category]
        laneige_df = df[df["is_laneige"]]

        if len(laneige_df) == 0:
            return {}

        summary = {}
        for product_name in laneige_df["product_name"].unique():
            product_df = laneige_df[laneige_df["product_name"] == product_name]

            ranks = product_df["rank"].values
            summary[product_name] = {
                "avg_rank": round(ranks.mean(), 1),
                "best_rank": int(ranks.min()),
                "worst_rank": int(ranks.max()),
                "current_rank": int(ranks[-1]) if len(ranks) > 0 else None,
                "trend": "rising" if len(ranks) > 1 and ranks[-1] < ranks[0] else "declining",
                "top5_days": int(sum(ranks <= 5)),
                "top10_days": int(sum(ranks <= 10)),
            }

        return summary

    def generate_insight(self, category: str, product_name: str) -> str:
        """특정 제품에 대한 인사이트 리포트를 생성해요.

        Args:
            category: 카테고리
            product_name: 제품명

        Returns:
            str: 인사이트 리포트 텍스트
        """
        if category not in self.ranking_history:
            return "데이터가 없습니다."

        summary = self.get_laneige_summary(category)

        if product_name not in summary:
            return f"{product_name} 제품의 데이터가 없습니다."

        stats = summary[product_name]

        insight = f"""
[{product_name}] 랭킹 분석 리포트

- 평균 순위: {stats["avg_rank"]}위
- 최고 순위: {stats["best_rank"]}위
- 현재 순위: {stats["current_rank"]}위
- TOP 5 유지 일수: {stats["top5_days"]}일
- TOP 10 유지 일수: {stats["top10_days"]}일
- 트렌드: {"상승세" if stats["trend"] == "rising" else "하락세"}
"""

        if stats["best_rank"] <= 3:
            insight += f"\n{product_name}은(는) 해당 카테고리에서 TOP 3에 진입한 베스트셀러입니다!"

        if stats["top5_days"] >= 7:
            insight += f"\n{stats['top5_days']}일 연속 TOP 5를 유지하며 강력한 성과를 보이고 있습니다."

        if stats["trend"] == "rising":
            insight += "\n상승 트렌드를 보이며, 향후 순위 상승이 기대됩니다."

        return insight.strip()


if __name__ == "__main__":
    from src.data.loader import load_all_products

    print("Loading products...")
    products = load_all_products()

    print("Generating rankings...")
    engine = MockRankingEngine(products)

    lip_care_history = engine.generate_ranking_history("lip_care", days=30)
    print(f"\nLip Care rankings generated: {len(lip_care_history)} records")

    summary = engine.get_laneige_summary("lip_care")
    print("\n=== LANEIGE Lip Care Summary ===")
    for product, stats in summary.items():
        print(f"\n{product}:")
        print(f"  Avg Rank: {stats['avg_rank']}")
        print(f"  Best Rank: {stats['best_rank']}")
        print(f"  TOP 5 Days: {stats['top5_days']}")

    print("\n=== Insight ===")
    print(engine.generate_insight("lip_care", "Lip Sleeping Mask"))
