import os

import pandas as pd

from .base import RankingProvider
from .mock_provider import MockRankingProvider
from .paapi_provider import PAAPIRankingProvider
from .service import RankingService


def get_ranking_provider(products_df: pd.DataFrame | None = None) -> RankingProvider:
    access_key = os.getenv("PA_API_ACCESS_KEY")
    secret_key = os.getenv("PA_API_SECRET_KEY")
    partner_tag = os.getenv("PA_API_PARTNER_TAG")
    region = os.getenv("PA_API_REGION", "us-east-1")

    if access_key and secret_key and partner_tag:
        print("[OK] PA API credentials found - using live Amazon data")
        return PAAPIRankingProvider(
            access_key=access_key, secret_key=secret_key, partner_tag=partner_tag, region=region
        )

    print("[INFO] PA API credentials not found - using mock data (demo mode)")

    if products_df is None:
        raise ValueError("products_df is required for MockRankingProvider")

    return MockRankingProvider(products_df)


def create_mock_provider(products_df: pd.DataFrame) -> MockRankingProvider:
    return MockRankingProvider(products_df)


def create_paapi_provider(
    access_key: str, secret_key: str, partner_tag: str, region: str = "us-east-1"
) -> PAAPIRankingProvider:
    return PAAPIRankingProvider(access_key=access_key, secret_key=secret_key, partner_tag=partner_tag, region=region)


__all__ = [
    "RankingProvider",
    "MockRankingProvider",
    "PAAPIRankingProvider",
    "RankingService",
    "get_ranking_provider",
    "create_mock_provider",
    "create_paapi_provider",
]
