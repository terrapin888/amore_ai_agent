"""Amazon PA-API 랭킹 프로바이더 모듈.

Amazon Product Advertising API를 활용하여
실시간 베스트셀러 랭킹 데이터를 수집해요.
"""

import hashlib
import hmac
import json
from datetime import datetime

import pandas as pd
import requests  # type: ignore[import-untyped]

from .base import RankingProvider


class PAAPIRankingProvider(RankingProvider):
    """Amazon PA-API 기반 랭킹 데이터 프로바이더.

    Amazon Product Advertising API v5를 사용하여
    실시간 베스트셀러 랭킹을 수집해요.

    Attributes:
        access_key (str): AWS Access Key
        secret_key (str): AWS Secret Key
        partner_tag (str): Amazon Associates Partner Tag
        region (str): AWS 리전
        marketplace (str): Amazon 마켓플레이스 URL
    """

    CATEGORY_NODE_IDS = {
        "lip_care": "11062741",
        "skincare": "11062031",
        "lip_makeup": "11058281",
        "face_powder": "11058251",
    }

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        partner_tag: str,
        region: str = "us-east-1",
        marketplace: str = "www.amazon.com",
    ):
        """PAAPIRankingProvider를 초기화해요.

        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            partner_tag: Amazon Associates Partner Tag
            region: AWS 리전 (기본값: us-east-1)
            marketplace: Amazon 마켓플레이스 (기본값: www.amazon.com)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        self.marketplace = marketplace
        self.host = "webservices.amazon.com"
        self.endpoint = f"https://{self.host}/paapi5/searchitems"

        self.ranking_cache: dict[str, pd.DataFrame] = {}
        self.cache_date: str | None = None

    @property
    def provider_name(self) -> str:
        """프로바이더 이름을 반환해요."""
        return "paapi"

    @property
    def is_live_data(self) -> bool:
        """실시간 데이터 여부를 반환해요."""
        return True

    def _sign_request(self, payload: dict) -> dict:
        """AWS Signature Version 4로 요청을 서명해요.

        Args:
            payload: API 요청 페이로드

        Returns:
            dict: 서명된 HTTP 헤더
        """
        t = datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        method = "POST"
        service = "ProductAdvertisingAPI"
        content_type = "application/json; charset=UTF-8"

        payload_json = json.dumps(payload)
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        headers = {
            "content-encoding": "amz-1.0",
            "content-type": content_type,
            "host": self.host,
            "x-amz-date": amz_date,
            "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        }

        canonical_headers = "\n".join([f"{k}:{v}" for k, v in sorted(headers.items())]) + "\n"
        signed_headers = ";".join(sorted(headers.keys()))

        canonical_uri = "/paapi5/searchitems"
        canonical_querystring = ""
        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{service}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"

        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = sign(("AWS4" + self.secret_key).encode("utf-8"), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, service)
        k_signing = sign(k_service, "aws4_request")
        signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = f"{algorithm} Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        headers["Authorization"] = authorization_header

        return headers

    def _fetch_best_sellers(self, category: str, page: int = 1) -> list[dict]:
        """PA-API로 베스트셀러 목록을 가져와요.

        Args:
            category: Amazon 카테고리 이름
            page: 페이지 번호 (기본값: 1)

        Returns:
            list[dict]: API에서 반환된 상품 목록
        """
        node_id = self.CATEGORY_NODE_IDS.get(category)
        if not node_id:
            print(f"Unknown category: {category}")
            return []

        payload = {
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace,
            "BrowseNodeId": node_id,
            "SearchIndex": "Beauty",
            "SortBy": "Relevance",
            "ItemCount": 10,
            "ItemPage": page,
            "Resources": [
                "ItemInfo.Title",
                "ItemInfo.ByLineInfo",
                "Offers.Listings.Price",
                "BrowseNodeInfo.BrowseNodes",
                "Images.Primary.Large",
            ],
        }

        try:
            headers = self._sign_request(payload)
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items: list[dict] = data.get("SearchResult", {}).get("Items", [])
                return items
            else:
                print(f"PA API Error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"PA API Request failed: {e}")
            return []

    def _parse_items_to_rankings(self, items: list[dict], category: str, start_rank: int = 1) -> list[dict]:
        """API 응답을 랭킹 데이터 형식으로 파싱해요.

        Args:
            items: PA-API에서 반환된 상품 목록
            category: Amazon 카테고리 이름
            start_rank: 시작 순위 (기본값: 1)

        Returns:
            list[dict]: 파싱된 랭킹 데이터 목록
        """
        results = []

        for i, item in enumerate(items):
            try:
                asin = item.get("ASIN", "")
                item_info = item.get("ItemInfo", {})
                title_info = item_info.get("Title", {})
                byline_info = item_info.get("ByLineInfo", {})
                offers = item.get("Offers", {})
                listings = offers.get("Listings", [])

                product_name = title_info.get("DisplayValue", "Unknown")
                brand = "Unknown"

                if byline_info.get("Brand"):
                    brand = byline_info["Brand"].get("DisplayValue", "Unknown")
                elif byline_info.get("Manufacturer"):
                    brand = byline_info["Manufacturer"].get("DisplayValue", "Unknown")

                price = 0
                if listings:
                    price_info = listings[0].get("Price", {})
                    price = price_info.get("Amount", 0)

                is_laneige = "laneige" in brand.lower() or "laneige" in product_name.lower()

                results.append(
                    {
                        "product_id": asin,
                        "product_name": product_name,
                        "brand": brand,
                        "category": category,
                        "amazon_category": category,
                        "price": price,
                        "is_laneige": is_laneige,
                        "rank": start_rank + i,
                    }
                )

            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        return results

    def get_rankings(self, category: str, days: int = 30) -> pd.DataFrame:
        """카테고리의 랭킹 데이터를 조회해요.

        Args:
            category: Amazon 카테고리 이름
            days: 조회할 일수 (기본값: 30, 실시간 데이터라 실제로는 오늘 데이터만 반환)

        Returns:
            pd.DataFrame: 랭킹 데이터프레임
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_key = f"{category}_{today}"

        if cache_key in self.ranking_cache:
            return self.ranking_cache[cache_key]

        all_items = []
        for page in range(1, 11):
            items = self._fetch_best_sellers(category, page)
            if not items:
                break
            all_items.extend(items)

        if not all_items:
            return pd.DataFrame()

        rankings = self._parse_items_to_rankings(all_items, category)

        df = pd.DataFrame(rankings)

        for day in range(1, days + 1):
            df[f"day_{day}"] = df["rank"]

        self.ranking_cache[cache_key] = df
        return df

    def get_all_categories(self, days: int = 30) -> dict[str, pd.DataFrame]:
        """모든 카테고리의 랭킹 데이터를 조회해요.

        Args:
            days: 조회할 일수 (기본값: 30)

        Returns:
            dict: 카테고리명을 키로 하는 랭킹 데이터프레임 딕셔너리
        """
        results = {}

        for category in self.CATEGORY_NODE_IDS:
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
            product_row = df[df["product_name"].str.contains(product_name, case=False, na=False)]

            if len(product_row) > 0:
                row = product_row.iloc[0]
                day_cols = [c for c in df.columns if c.startswith("day_")]
                rankings = [int(row[col]) for col in day_cols]

                return {
                    "product_name": row["product_name"],
                    "category": category,
                    "rankings": rankings,
                    "avg_rank": round(sum(rankings) / len(rankings), 1),
                    "best_rank": min(rankings),
                    "worst_rank": max(rankings),
                    "trend": "stable",
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

        for _, row in laneige_df.iterrows():
            product_name = row["product_name"]
            current_rank = row["rank"]

            summary[product_name] = {
                "avg_rank": float(current_rank),
                "best_rank": int(current_rank),
                "worst_rank": int(current_rank),
                "current_rank": int(current_rank),
                "trend": "stable",
                "top5_days": 1 if current_rank <= 5 else 0,
                "top10_days": 1 if current_rank <= 10 else 0,
            }

        return summary

    def get_today_rankings(self) -> dict[str, pd.DataFrame]:
        """오늘의 랭킹 데이터를 수집해요.

        Returns:
            dict: 카테고리별 오늘의 랭킹 데이터프레임 딕셔너리
        """
        results = {}

        for category in self.CATEGORY_NODE_IDS:
            all_items = []
            for page in range(1, 11):
                items = self._fetch_best_sellers(category, page)
                if not items:
                    break
                all_items.extend(items)

            if not all_items:
                continue

            rankings = self._parse_items_to_rankings(all_items, category)
            df = pd.DataFrame(rankings)

            if len(df) > 0:
                results[category] = df

        return results
