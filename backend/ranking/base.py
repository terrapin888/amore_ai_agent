"""
Ranking Provider 추상 베이스 클래스
- Mock과 PA API 구현체의 공통 인터페이스 정의
"""

from abc import ABC, abstractmethod

import pandas as pd


class RankingProvider(ABC):
    """Abstract base class for ranking data providers."""

    # Retrieves ranking data for a specific category over a time period.
    # @param category: Product category (e.g., "lip_care", "skincare")
    # @param days: Number of days to retrieve (default: 30)
    # @return: DataFrame with columns: product_id, product_name, brand, category, day_1, day_2, ..., is_laneige
    @abstractmethod
    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """
        특정 카테고리의 랭킹 데이터 조회

        Args:
            category: 카테고리 (lip_care, skincare 등)
            days: 조회 기간 (일)

        Returns:
            DataFrame with columns:
            - product_id, product_name, brand, category
            - day_1, day_2, ... day_N (일별 순위)
            - is_laneige
        """
        pass

    # Retrieves ranking data for all available categories.
    # @param days: Number of days to retrieve (default: 30)
    # @return: Dictionary mapping category names to their respective DataFrames
    @abstractmethod
    def get_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        pass

    # Retrieves ranking history for a specific product.
    # @param product_name: Name of the product to query
    # @param days: Number of days to retrieve (default: 30)
    # @return: Dictionary with rankings list, dates, statistics, and trend; None if not found
    @abstractmethod
    def get_product_ranking_history(self, product_name: str, days: int = 30) -> dict | None:
        pass

    # Returns ranking summary statistics for LANEIGE products in a category.
    # @param category: Category to query
    # @return: Dictionary mapping product names to their statistics (avg, best, worst rank, etc.)
    @abstractmethod
    def get_laneige_summary(self, category: str) -> dict:
        pass

    # Returns the provider name identifier.
    # @return: Provider name string ("mock" or "paapi")
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    # Indicates whether the provider returns live/real data.
    # @return: True if live data, False if mock/simulated data
    @property
    @abstractmethod
    def is_live_data(self) -> bool:
        pass

    # Retrieves today's ranking data for database storage.
    # @return: Dictionary mapping categories to DataFrames with columns: product_name, brand, rank, is_laneige
    @abstractmethod
    def get_today_rankings(self) -> dict[str, pd.DataFrame]:
        pass
