"""랭킹 프로바이더 추상 베이스 클래스 모듈.

Mock과 PA-API 구현체의 공통 인터페이스를 정의해요.
"""

from abc import ABC, abstractmethod

import pandas as pd


class RankingProvider(ABC):
    """랭킹 데이터 프로바이더의 추상 베이스 클래스.

    모든 랭킹 프로바이더는 이 클래스를 상속받아
    공통 인터페이스를 구현해야 해요.
    """

    @abstractmethod
    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """특정 카테고리의 랭킹 데이터를 조회해요.

        Args:
            category: 카테고리 (lip_care, skincare 등)
            days: 조회 기간 (일)

        Returns:
            pd.DataFrame: 다음 컬럼을 포함하는 데이터프레임
                - product_id, product_name, brand, category
                - day_1, day_2, ... day_N (일별 순위)
                - is_laneige
        """
        pass

    @abstractmethod
    def get_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """모든 카테고리의 랭킹 데이터를 조회해요.

        Args:
            days: 조회 기간 (일)

        Returns:
            dict: 카테고리명을 키로 하는 데이터프레임 딕셔너리
        """
        pass

    @abstractmethod
    def get_product_ranking_history(self, product_name: str, days: int = 30) -> dict | None:
        """특정 제품의 랭킹 히스토리를 조회해요.

        Args:
            product_name: 제품명
            days: 조회 기간 (일)

        Returns:
            dict | None: 랭킹 히스토리 (rankings, avg_rank, trend 등)
                         제품을 찾지 못하면 None
        """
        pass

    @abstractmethod
    def get_laneige_summary(self, category: str) -> dict:
        """LANEIGE 제품의 랭킹 요약을 반환해요.

        Args:
            category: 카테고리

        Returns:
            dict: 제품명을 키로 하는 통계 딕셔너리
                  (avg_rank, best_rank, worst_rank 등)
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """프로바이더 이름을 반환해요.

        Returns:
            str: 프로바이더 이름 ("mock" 또는 "paapi")
        """
        pass

    @property
    @abstractmethod
    def is_live_data(self) -> bool:
        """실시간 데이터 여부를 반환해요.

        Returns:
            bool: 실시간 데이터면 True, 시뮬레이션 데이터면 False
        """
        pass

    @abstractmethod
    def get_today_rankings(self) -> dict[str, pd.DataFrame]:
        """오늘의 랭킹 데이터를 조회해요.

        DB 저장용으로 사용돼요.

        Returns:
            dict: 카테고리별 데이터프레임 딕셔너리
                  (product_name, brand, rank, is_laneige 컬럼 포함)
        """
        pass
