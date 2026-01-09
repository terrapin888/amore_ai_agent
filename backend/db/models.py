"""
Database Models
- Ranking history table definition
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class RankingHistory(Base):
    """
    Daily ranking history table.
    Stores product rankings by date and category with composite indexes for query optimization.
    """

    __tablename__ = "ranking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Date
    ranking_date = Column(Date, nullable=False, index=True)

    # Category
    category = Column(String(100), nullable=False, index=True)

    # Product information
    product_id = Column(Integer, nullable=True)
    product_name = Column(String(300), nullable=False)
    brand = Column(String(100), nullable=False)

    # Ranking
    rank = Column(Integer, nullable=False)

    # LANEIGE flag
    is_laneige = Column(Boolean, default=False)

    # Additional information
    price = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite indexes (optimized for date + category queries)
    __table_args__ = (
        Index("ix_ranking_date_category", "ranking_date", "category"),
        Index("ix_ranking_product_date", "product_name", "ranking_date"),
    )

    # Returns string representation of the record for debugging.
    # @return: Formatted string with date, category, product name, and rank
    def __repr__(self):
        return f"<RankingHistory({self.ranking_date}, {self.category}, {self.product_name}: #{self.rank})>"

    # Converts the record to a dictionary for JSON serialization.
    # @return: Dictionary containing all fields with ISO formatted dates
    def to_dict(self):
        return {
            "id": self.id,
            "ranking_date": self.ranking_date.isoformat() if self.ranking_date else None,
            "category": self.category,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "rank": self.rank,
            "is_laneige": self.is_laneige,
            "price": self.price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
