"""랭킹 서비스 모듈.

랭킹 데이터 수집, 조회, DB 저장을 관리하는 서비스 레이어예요.
"""

from datetime import date

import pandas as pd

from backend.db import RankingRepository, init_db

from .base import RankingProvider


class RankingService:
    """랭킹 데이터 서비스.

    Provider로부터 랭킹을 수집하고 DB에 저장/조회해요.

    Attributes:
        provider (RankingProvider): 랭킹 데이터 제공자
        repository (RankingRepository): DB 레포지토리
    """

    def __init__(self, provider: RankingProvider):
        """RankingService를 초기화해요.

        Args:
            provider (RankingProvider): 랭킹 데이터 제공자
        """
        self.provider = provider
        self.repository = RankingRepository()
        init_db()

    def collect_today_rankings(self) -> dict[str, int]:
        """오늘 랭킹 데이터를 수집하고 DB에 저장해요.

        Returns:
            dict[str, int]: 카테고리별 저장된 제품 수
        """
        today = date.today()
        results = {}

        today_rankings = self.provider.get_today_rankings()

        for category, df in today_rankings.items():
            if len(df) == 0:
                continue

            if "day_1" in df.columns and "rank" not in df.columns:
                df = df.rename(columns={"day_1": "rank"})

            count = self.repository.save_daily_rankings(today, category, df)
            results[category] = count
            print(f"  - {category}: {count} products saved")

        return results

    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """특정 카테고리의 랭킹 데이터를 조회해요.

        Args:
            category (str): 카테고리명
            days (int): 조회 일수 (기본값: 30)

        Returns:
            pd.DataFrame: 랭킹 데이터
        """
        return self.repository.get_category_rankings_as_df(category, days)

    def get_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """전체 카테고리의 랭킹 데이터를 조회해요.

        Args:
            days (int): 조회 일수 (기본값: 30)

        Returns:
            dict[str, pd.DataFrame]: 카테고리별 랭킹 데이터
        """
        return self.repository.get_all_categories_as_df(days)

    def get_laneige_summary(self, category: str, days: int = 30) -> dict:
        """특정 카테고리의 LANEIGE 제품 요약을 조회해요.

        Args:
            category (str): 카테고리명
            days (int): 조회 일수 (기본값: 30)

        Returns:
            dict: LANEIGE 제품별 평균/최고/최저 순위 등 요약
        """
        return self.repository.get_laneige_summary(category, days)

    def get_product_history(self, product_name: str, days: int = 30) -> dict | None:
        """특정 제품의 랭킹 히스토리를 조회해요.

        Args:
            product_name (str): 제품명
            days (int): 조회 일수 (기본값: 30)

        Returns:
            dict | None: 제품 랭킹 히스토리 또는 None
        """
        return self.repository.get_product_history(product_name, days)

    def get_stats(self) -> dict:
        """서비스 통계 정보를 조회해요.

        Returns:
            dict: 총 날짜 수, 카테고리, 가용 날짜, 프로바이더 정보
        """
        return {
            "total_dates": self.repository.get_date_count(),
            "categories": self.repository.get_available_categories(),
            "available_dates": [d.isoformat() for d in self.repository.get_available_dates()],
            "provider": self.provider.provider_name,
            "is_live_data": self.provider.is_live_data,
        }

    def has_today_data(self) -> bool:
        """오늘 데이터가 DB에 있는지 확인해요.

        Returns:
            bool: 오늘 데이터 존재 여부
        """
        return self.repository.has_data_for_date(date.today())

    def ensure_today_data(self) -> bool:
        """오늘 데이터가 없으면 수집해요.

        Returns:
            bool: 새로 수집했으면 True, 이미 있었으면 False
        """
        if self.has_today_data():
            print("Today's data already exists in DB")
            return False

        print("Collecting today's rankings...")
        self.collect_today_rankings()
        return True

    def close(self):
        """레포지토리 연결을 닫아요."""
        self.repository.close()
