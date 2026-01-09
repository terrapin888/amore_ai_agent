"""데이터베이스 모델 모듈.

랭킹 히스토리 테이블 정의를 포함해요.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 모델의 베이스 클래스."""

    pass


class RankingHistory(Base):
    """일별 랭킹 히스토리 테이블.

    날짜와 카테고리별로 제품 순위를 저장해요.
    쿼리 최적화를 위한 복합 인덱스가 설정되어 있어요.

    Attributes:
        id (int): 기본 키
        ranking_date (date): 랭킹 날짜
        category (str): 카테고리
        product_id (int | None): 제품 ID
        product_name (str): 제품명
        brand (str): 브랜드
        rank (int): 순위
        is_laneige (bool): LANEIGE 제품 여부
        price (float | None): 가격
        created_at (datetime): 생성 시각
    """

    __tablename__ = "ranking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 날짜
    ranking_date = Column(Date, nullable=False, index=True)

    # 카테고리
    category = Column(String(100), nullable=False, index=True)

    # 제품 정보
    product_id = Column(Integer, nullable=True)
    product_name = Column(String(300), nullable=False)
    brand = Column(String(100), nullable=False)

    # 순위
    rank = Column(Integer, nullable=False)

    # LANEIGE 여부
    is_laneige = Column(Boolean, default=False)

    # 추가 정보
    price = Column(Float, nullable=True)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)

    # 복합 인덱스 (날짜 + 카테고리 쿼리 최적화)
    __table_args__ = (
        Index("ix_ranking_date_category", "ranking_date", "category"),
        Index("ix_ranking_product_date", "product_name", "ranking_date"),
    )

    def __repr__(self):
        """디버깅용 문자열 표현을 반환해요.

        Returns:
            str: 날짜, 카테고리, 제품명, 순위가 포함된 문자열
        """
        return f"<RankingHistory({self.ranking_date}, {self.category}, {self.product_name}: #{self.rank})>"

    def to_dict(self):
        """레코드를 딕셔너리로 변환해요.

        JSON 직렬화에 사용해요.

        Returns:
            dict: 모든 필드를 포함하는 딕셔너리 (날짜는 ISO 포맷)
        """
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
