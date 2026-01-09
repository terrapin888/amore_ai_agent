"""랭킹 리포지토리 모듈.

랭킹 데이터의 CRUD 작업과 히스토리 조회를 담당해요.
"""

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import get_session
from .models import RankingHistory


class RankingRepository:
    """랭킹 데이터 저장 및 조회를 관리하는 리포지토리 클래스.

    데이터베이스에서 랭킹 히스토리를 저장하고 조회하는
    모든 작업을 담당해요.

    Attributes:
        _session (Session | None): SQLAlchemy 세션 (지연 초기화)
    """

    def __init__(self, session: Session | None = None):
        """RankingRepository를 초기화해요.

        Args:
            session: SQLAlchemy 세션 (기본값: None, 필요시 자동 생성)
        """
        self._session = session

    @property
    def session(self) -> Session:
        """세션을 반환해요. 없으면 새로 생성해요."""
        if self._session is None:
            self._session = get_session()
        return self._session

    def close(self):
        """데이터베이스 세션을 닫아요."""
        if self._session:
            self._session.close()

    def save_daily_rankings(self, ranking_date: date, category: str, rankings_df: pd.DataFrame) -> int:
        """일별 랭킹 데이터를 저장해요.

        중복 방지를 위해 같은 날짜/카테고리의 기존 데이터는 삭제해요.

        Args:
            ranking_date: 랭킹 날짜
            category: 카테고리
            rankings_df: product_name, brand, rank, is_laneige 컬럼이 있는 데이터프레임

        Returns:
            int: 저장된 레코드 수
        """
        # 중복 방지를 위해 기존 데이터 삭제
        self.session.query(RankingHistory).filter(
            RankingHistory.ranking_date == ranking_date, RankingHistory.category == category
        ).delete()

        count = 0
        for _, row in rankings_df.iterrows():
            record = RankingHistory(
                ranking_date=ranking_date,
                category=category,
                product_id=row.get("product_id"),
                product_name=row["product_name"],
                brand=row["brand"],
                rank=row["rank"],
                is_laneige=row.get("is_laneige", False),
                price=row.get("price"),
            )
            self.session.add(record)
            count += 1

        self.session.commit()
        return count

    def get_rankings_by_date(self, ranking_date: date, category: str | None = None) -> list[RankingHistory]:
        """특정 날짜의 랭킹을 조회해요.

        Args:
            ranking_date: 조회할 날짜
            category: 카테고리 필터 (선택)

        Returns:
            list[RankingHistory]: 순위순으로 정렬된 레코드 리스트
        """
        query = self.session.query(RankingHistory).filter(RankingHistory.ranking_date == ranking_date)

        if category:
            query = query.filter(RankingHistory.category == category)

        result: list[RankingHistory] = query.order_by(RankingHistory.rank).all()
        return result

    def get_rankings_range(self, start_date: date, end_date: date, category: str | None = None) -> list[RankingHistory]:
        """기간 내 랭킹을 조회해요.

        Args:
            start_date: 시작 날짜 (포함)
            end_date: 종료 날짜 (포함)
            category: 카테고리 필터 (선택)

        Returns:
            list[RankingHistory]: 날짜, 카테고리, 순위순으로 정렬된 레코드 리스트
        """
        query = self.session.query(RankingHistory).filter(
            RankingHistory.ranking_date >= start_date, RankingHistory.ranking_date <= end_date
        )

        if category:
            query = query.filter(RankingHistory.category == category)

        result: list[RankingHistory] = query.order_by(
            RankingHistory.ranking_date, RankingHistory.category, RankingHistory.rank
        ).all()
        return result

    def get_category_rankings_as_df(self, category: str, days: int = 30) -> pd.DataFrame:
        """카테고리 랭킹을 day_1, day_2, ... 컬럼 형태의 데이터프레임으로 반환해요.

        Args:
            category: 카테고리
            days: 조회할 일수 (기본값: 30)

        Returns:
            pd.DataFrame: product_name, brand, is_laneige, day_1, day_2, ... 컬럼을 가진 데이터프레임
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        records = self.get_rankings_range(start_date, end_date, category)

        if not records:
            return pd.DataFrame()

        # 날짜별 데이터 정리
        date_list = sorted({r.ranking_date for r in records})
        date_to_day = {d: i + 1 for i, d in enumerate(date_list)}

        # 제품별 데이터 수집
        product_data = {}
        for record in records:
            key = record.product_name
            if key not in product_data:
                product_data[key] = {
                    "product_name": record.product_name,
                    "brand": record.brand,
                    "is_laneige": record.is_laneige,
                    "product_id": record.product_id,
                    "price": record.price,
                }

            day_num = date_to_day[record.ranking_date]
            product_data[key][f"day_{day_num}"] = record.rank

        df = pd.DataFrame(list(product_data.values()))

        # day_N 컬럼 정렬
        base_cols = ["product_id", "product_name", "brand", "is_laneige", "price"]
        day_cols = sorted([c for c in df.columns if c.startswith("day_")], key=lambda x: int(x.split("_")[1]))
        existing_cols = [c for c in base_cols if c in df.columns]

        return df[existing_cols + day_cols]

    def get_all_categories_as_df(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """모든 카테고리의 랭킹을 데이터프레임 딕셔너리로 반환해요.

        Args:
            days: 조회할 일수 (기본값: 30)

        Returns:
            dict: 카테고리명을 키로 하는 데이터프레임 딕셔너리
        """
        categories = self.get_available_categories()
        result = {}

        for category in categories:
            df = self.get_category_rankings_as_df(category, days)
            if len(df) > 0:
                result[category] = df

        return result

    def get_available_categories(self) -> list[str]:
        """저장된 랭킹 데이터가 있는 카테고리 목록을 반환해요.

        Returns:
            list[str]: 카테고리명 리스트
        """
        result = self.session.query(RankingHistory.category).distinct().all()
        return [r[0] for r in result]

    def get_available_dates(self, category: str | None = None) -> list[date]:
        """저장된 랭킹 데이터가 있는 날짜 목록을 반환해요.

        Args:
            category: 카테고리 필터 (선택)

        Returns:
            list[date]: 날짜순으로 정렬된 날짜 리스트
        """
        query = self.session.query(RankingHistory.ranking_date).distinct()

        if category:
            query = query.filter(RankingHistory.category == category)

        result = query.order_by(RankingHistory.ranking_date).all()
        return [r[0] for r in result]

    def get_date_count(self) -> int:
        """저장된 데이터가 있는 고유 날짜 수를 반환해요.

        Returns:
            int: 고유 날짜 수
        """
        result = self.session.query(func.count(func.distinct(RankingHistory.ranking_date))).scalar()
        return result or 0

    def has_data_for_date(self, ranking_date: date, category: str | None = None) -> bool:
        """특정 날짜에 랭킹 데이터가 있는지 확인해요.

        Args:
            ranking_date: 확인할 날짜
            category: 카테고리 필터 (선택)

        Returns:
            bool: 데이터가 있으면 True, 없으면 False
        """
        query = self.session.query(RankingHistory).filter(RankingHistory.ranking_date == ranking_date)

        if category:
            query = query.filter(RankingHistory.category == category)

        return query.first() is not None

    def get_product_history(self, product_name: str, days: int = 30) -> dict | None:
        """특정 제품의 상세 랭킹 히스토리를 조회해요.

        Args:
            product_name: 제품명
            days: 조회할 일수 (기본값: 30)

        Returns:
            dict | None: 랭킹 리스트, 날짜, 통계, 트렌드 정보 또는 데이터가 없으면 None
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        records = (
            self.session.query(RankingHistory)
            .filter(
                RankingHistory.product_name == product_name,
                RankingHistory.ranking_date >= start_date,
                RankingHistory.ranking_date <= end_date,
            )
            .order_by(RankingHistory.ranking_date)
            .all()
        )

        if not records:
            return None

        ranks = [r.rank for r in records]

        return {
            "product_name": product_name,
            "category": records[0].category,
            "brand": records[0].brand,
            "is_laneige": records[0].is_laneige,
            "rankings": ranks,
            "dates": [r.ranking_date.isoformat() for r in records],
            "avg_rank": round(sum(ranks) / len(ranks), 1),
            "best_rank": min(ranks),
            "worst_rank": max(ranks),
            "trend": "rising" if ranks[-1] < ranks[0] else "declining",
        }

    def get_laneige_summary(self, category: str, days: int = 30) -> dict:
        """LANEIGE 제품의 랭킹 요약 통계를 반환해요.

        Args:
            category: 카테고리
            days: 분석할 일수 (기본값: 30)

        Returns:
            dict: 제품명을 키로 하는 통계 딕셔너리 (avg, best, worst 순위 등)
        """
        df = self.get_category_rankings_as_df(category, days)

        if len(df) == 0:
            return {}

        laneige_df = df[df["is_laneige"]]

        if len(laneige_df) == 0:
            return {}

        summary = {}
        day_cols = [c for c in df.columns if c.startswith("day_")]

        for _, row in laneige_df.iterrows():
            product_name = row["product_name"]
            ranks = [row[col] for col in day_cols if pd.notna(row.get(col))]

            if not ranks:
                continue

            summary[product_name] = {
                "avg_rank": round(sum(ranks) / len(ranks), 1),
                "best_rank": int(min(ranks)),
                "worst_rank": int(max(ranks)),
                "current_rank": int(ranks[-1]) if ranks else None,
                "trend": "rising" if len(ranks) > 1 and ranks[-1] < ranks[0] else "declining",
                "top5_days": sum(1 for r in ranks if r <= 5),
                "top10_days": sum(1 for r in ranks if r <= 10),
            }

        return summary
