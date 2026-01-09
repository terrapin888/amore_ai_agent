"""Mock 랭킹 프로바이더 모듈.

실제 API 없이 테스트용 랭킹 데이터를 시뮬레이션해요.
다양한 시나리오(베스트셀러, 상승세, 하락세 등)를 기반으로
현실적인 랭킹 패턴을 생성해요.
"""

import random
from enum import Enum

import pandas as pd

from .base import RankingProvider


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


class MockRankingProvider(RankingProvider):
    """Mock 랭킹 데이터 프로바이더.

    테스트 및 개발용으로 시뮬레이션된 랭킹 데이터를 생성해요.
    실제 Amazon API 없이도 다양한 랭킹 시나리오를 테스트할 수 있어요.

    Attributes:
        products: 제품 데이터프레임
        ranking_cache (dict): 생성된 랭킹 캐시
    """

    def __init__(self, products_df: pd.DataFrame):
        """MockRankingProvider를 초기화해요.

        Args:
            products_df: 제품 정보가 담긴 데이터프레임
        """
        self.products = products_df.copy()
        self.ranking_cache: dict[str, pd.DataFrame] = {}
        self._generated_days = 0

    @property
    def provider_name(self) -> str:
        """프로바이더 이름을 반환해요."""
        return "mock"

    @property
    def is_live_data(self) -> bool:
        """실시간 데이터 여부를 반환해요."""
        return False

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

    def _generate_category_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """카테고리별 랭킹 데이터를 생성해요.

        Args:
            category: Amazon 카테고리 이름
            days: 생성할 일수 (기본값: 30)

        Returns:
            pd.DataFrame: 일별 랭킹이 포함된 데이터프레임
        """
        category_products = self.products[self.products["amazon_category"] == category].copy()

        if len(category_products) == 0:
            category_products = self.products[
                self.products["category"].str.lower().str.contains(category.lower().replace("_", " "), na=False)
            ].copy()

        if len(category_products) == 0:
            return pd.DataFrame()

        results = []

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

            daily_ranks = {}
            for day in range(1, days + 1):
                rank = self._apply_scenario(scenario, day - 1, days)
                daily_ranks[f"day_{day}"] = rank

            results.append(
                {
                    "product_id": product.get("product_id", 0),
                    "product_name": product_name,
                    "brand": product["brand"],
                    "category": product.get("category", ""),
                    "amazon_category": category,
                    "price": product.get("price", 0),
                    "is_laneige": is_laneige,
                    **daily_ranks,
                }
            )

        df = pd.DataFrame(results)

        for day in range(1, days + 1):
            col = f"day_{day}"
            df[col] = df[col].rank(method="first").astype(int)

        return df

    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """카테고리의 랭킹 데이터를 조회해요.

        캐시된 데이터가 있으면 재사용하고, 없으면 새로 생성해요.

        Args:
            category: Amazon 카테고리 이름
            days: 조회할 일수 (기본값: 30)

        Returns:
            pd.DataFrame: 랭킹 데이터프레임
        """
        cache_key = f"{category}_{days}"

        if cache_key not in self.ranking_cache or self._generated_days != days:
            self.ranking_cache[cache_key] = self._generate_category_rankings(category, days)
            self._generated_days = days

        return self.ranking_cache[cache_key]

    def get_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """모든 카테고리의 랭킹 데이터를 조회해요.

        Args:
            days: 조회할 일수 (기본값: 30)

        Returns:
            dict: 카테고리명을 키로 하는 랭킹 데이터프레임 딕셔너리
        """
        categories = ["lip_care", "skincare", "lip_makeup", "face_powder"]
        results = {}

        for category in categories:
            df = self.get_rankings(category, days)
            if len(df) > 0:
                results[category] = df

        return results

    def get_product_ranking_history(self, product_name: str, days: int = 30) -> dict | None:
        """특정 제품의 랭킹 히스토리를 조회해요.

        Args:
            product_name: 제품명
            days: 조회할 일수 (기본값: 30)

        Returns:
            dict | None: 랭킹 히스토리 정보 또는 None (제품을 찾지 못한 경우)
        """
        all_rankings = self.get_all_categories(days)

        for category, df in all_rankings.items():
            product_row = df[df["product_name"] == product_name]

            if len(product_row) > 0:
                row = product_row.iloc[0]
                day_cols = [c for c in df.columns if c.startswith("day_")]
                rankings = [int(row[col]) for col in day_cols]

                return {
                    "product_name": product_name,
                    "category": category,
                    "rankings": rankings,
                    "avg_rank": round(sum(rankings) / len(rankings), 1),
                    "best_rank": min(rankings),
                    "worst_rank": max(rankings),
                    "trend": "rising" if rankings[-1] < rankings[0] else "declining",
                }

        return None

    def get_laneige_summary(self, category: str) -> dict:
        """LANEIGE 제품의 랭킹 요약 정보를 조회해요.

        Args:
            category: Amazon 카테고리 이름

        Returns:
            dict: 제품별 평균순위, 최고순위, 트렌드 등 요약 정보
        """
        df = self.get_rankings(category)

        if len(df) == 0:
            return {}

        laneige_df = df[df["is_laneige"]]

        if len(laneige_df) == 0:
            return {}

        summary = {}
        day_cols = [c for c in df.columns if c.startswith("day_")]

        for _, row in laneige_df.iterrows():
            product_name = row["product_name"]
            ranks = [row[col] for col in day_cols]

            summary[product_name] = {
                "avg_rank": round(sum(ranks) / len(ranks), 1),
                "best_rank": int(min(ranks)),
                "worst_rank": int(max(ranks)),
                "current_rank": int(ranks[-1]) if ranks else None,
                "trend": "rising" if ranks[-1] < ranks[0] else "declining",
                "top5_days": sum(1 for r in ranks if r <= 5),
                "top10_days": sum(1 for r in ranks if r <= 10),
            }

        return summary

    def get_today_rankings(self) -> dict[str, pd.DataFrame]:
        """오늘의 랭킹 데이터를 생성해요.

        Returns:
            dict: 카테고리별 오늘의 랭킹 데이터프레임 딕셔너리
        """
        categories = ["lip_care", "skincare", "lip_makeup", "face_powder"]
        results = {}

        for category in categories:
            df = self._generate_category_rankings(category, days=1)

            if len(df) > 0:
                if "day_1" in df.columns:
                    df = df.rename(columns={"day_1": "rank"})
                results[category] = df

        return results
