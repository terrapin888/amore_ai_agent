"""
Ranking Repository
- Ranking data CRUD operations
- History retrieval and storage
"""

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import get_session
from .models import RankingHistory


class RankingRepository:
    """Repository class for managing ranking data storage and retrieval."""

    # Initializes the repository with an optional session.
    # @param session: SQLAlchemy Session object (optional, created lazily if not provided)
    def __init__(self, session: Session | None = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session

    # Closes the database session if it exists.
    # @return: None
    def close(self):
        if self._session:
            self._session.close()

    # Saves daily ranking data for a specific date and category.
    # @param ranking_date: The date of the rankings
    # @param category: Product category (e.g., "lip_care", "skincare")
    # @param rankings_df: DataFrame containing product_name, brand, rank, is_laneige columns
    # @return: Number of records saved
    # Note: Deletes existing data for the same date/category to prevent duplicates.
    def save_daily_rankings(self, ranking_date: date, category: str, rankings_df: pd.DataFrame) -> int:
        # Delete existing data for this date/category to prevent duplicates
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

    # Retrieves rankings for a specific date, optionally filtered by category.
    # @param ranking_date: The date to query
    # @param category: Optional category filter
    # @return: List of RankingHistory records ordered by rank
    def get_rankings_by_date(self, ranking_date: date, category: str | None = None) -> list[RankingHistory]:
        query = self.session.query(RankingHistory).filter(RankingHistory.ranking_date == ranking_date)

        if category:
            query = query.filter(RankingHistory.category == category)

        return query.order_by(RankingHistory.rank).all()

    # Retrieves rankings within a date range, optionally filtered by category.
    # @param start_date: Start date of the range (inclusive)
    # @param end_date: End date of the range (inclusive)
    # @param category: Optional category filter
    # @return: List of RankingHistory records ordered by date, category, and rank
    def get_rankings_range(self, start_date: date, end_date: date, category: str | None = None) -> list[RankingHistory]:
        query = self.session.query(RankingHistory).filter(
            RankingHistory.ranking_date >= start_date, RankingHistory.ranking_date <= end_date
        )

        if category:
            query = query.filter(RankingHistory.category == category)

        return query.order_by(RankingHistory.ranking_date, RankingHistory.category, RankingHistory.rank).all()

    # Returns category rankings as a DataFrame with day_1, day_2, ... columns.
    # @param category: Category to query
    # @param days: Number of days to retrieve (default: 30)
    # @return: DataFrame with columns: product_name, brand, is_laneige, day_1, day_2, ...
    # Note: Each day_N column contains the rank for that day in the period.
    def get_category_rankings_as_df(self, category: str, days: int = 30) -> pd.DataFrame:
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        records = self.get_rankings_range(start_date, end_date, category)

        if not records:
            return pd.DataFrame()

        # Organize data by date
        date_list = sorted({r.ranking_date for r in records})
        date_to_day = {d: i + 1 for i, d in enumerate(date_list)}

        # Collect data by product
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

        # Sort day_N columns
        base_cols = ["product_id", "product_name", "brand", "is_laneige", "price"]
        day_cols = sorted([c for c in df.columns if c.startswith("day_")], key=lambda x: int(x.split("_")[1]))
        existing_cols = [c for c in base_cols if c in df.columns]

        return df[existing_cols + day_cols]

    # Returns rankings for all categories as a dictionary of DataFrames.
    # @param days: Number of days to retrieve (default: 30)
    # @return: Dictionary mapping category names to their respective DataFrames
    def get_all_categories_as_df(self, days: int = 30) -> dict[str, pd.DataFrame]:
        categories = self.get_available_categories()
        result = {}

        for category in categories:
            df = self.get_category_rankings_as_df(category, days)
            if len(df) > 0:
                result[category] = df

        return result

    # Returns a list of all categories that have stored ranking data.
    # @return: List of category names
    def get_available_categories(self) -> list[str]:
        result = self.session.query(RankingHistory.category).distinct().all()
        return [r[0] for r in result]

    # Returns a list of all dates that have stored ranking data.
    # @param category: Optional category filter
    # @return: List of date objects in chronological order
    def get_available_dates(self, category: str | None = None) -> list[date]:
        query = self.session.query(RankingHistory.ranking_date).distinct()

        if category:
            query = query.filter(RankingHistory.category == category)

        result = query.order_by(RankingHistory.ranking_date).all()
        return [r[0] for r in result]

    # Returns the count of distinct dates with stored data.
    # @return: Integer count of unique dates
    def get_date_count(self) -> int:
        result = self.session.query(func.count(func.distinct(RankingHistory.ranking_date))).scalar()
        return result or 0

    # Checks if ranking data exists for a specific date.
    # @param ranking_date: Date to check
    # @param category: Optional category filter
    # @return: True if data exists, False otherwise
    def has_data_for_date(self, ranking_date: date, category: str | None = None) -> bool:
        query = self.session.query(RankingHistory).filter(RankingHistory.ranking_date == ranking_date)

        if category:
            query = query.filter(RankingHistory.category == category)

        return query.first() is not None

    # Retrieves detailed ranking history for a specific product.
    # @param product_name: Name of the product to query
    # @param days: Number of days to retrieve (default: 30)
    # @return: Dictionary with rankings list, dates, statistics, and trend; None if no data
    def get_product_history(self, product_name: str, days: int = 30) -> dict | None:
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

    # Returns ranking summary statistics for LANEIGE products in a category.
    # @param category: Category to query
    # @param days: Number of days to analyze (default: 30)
    # @return: Dictionary mapping product names to their statistics (avg, best, worst rank, etc.)
    def get_laneige_summary(self, category: str, days: int = 30) -> dict:
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
