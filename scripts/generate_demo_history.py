"""
데모용 30일 히스토리 생성 스크립트
- 라네즈 제품별 시나리오 기반 랭킹 트렌드 생성
- BEST_SELLER, RISING_STAR, STABLE 등 의미있는 패턴
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import random
import pandas as pd
from backend.db import init_db, RankingRepository
from backend.data.loader import load_all_products

# 라네즈 제품별 시나리오 정의
LANEIGE_SCENARIOS = {
    # BEST_SELLER: 1~3위 안정 유지 (베스트셀러)
    "Lip Sleeping Mask": {"type": "best_seller", "range": (1, 2)},
    "Water Sleeping Mask": {"type": "best_seller", "range": (1, 3)},

    # RISING_STAR: 명확한 상승 트렌드
    "Lip Sleeping Mask Vanilla": {"type": "rising", "start": 35, "end": 3},
    "Cream Skin Refiner": {"type": "rising", "start": 48, "end": 6},

    # STABLE: 안정적 순위 유지
    "Water Bank Blue Hyaluronic Cream": {"type": "stable", "range": (10, 14)},
    "Lip Glowy Balm": {"type": "stable", "range": (4, 8)},
    "Eye Sleeping Mask": {"type": "stable", "range": (12, 18)},

    # NEW_ENTRY: 신제품 런칭 후 급상승
    "Neo Cushion Matte": {"type": "new_entry", "start": 85, "end": 8},
    "Radian-C Cream": {"type": "new_entry", "start": 92, "end": 15},
}

def generate_rank(scenario: dict, day_index: int, total_days: int = 30) -> int:
    """시나리오 기반 랭킹 생성"""
    progress = day_index / (total_days - 1) if total_days > 1 else 1

    if scenario["type"] == "best_seller":
        low, high = scenario["range"]
        return random.randint(low, high)

    elif scenario["type"] == "rising":
        start = scenario["start"]
        end = scenario["end"]
        # 부드러운 상승 곡선
        current = int(start - (start - end) * progress)
        # 작은 변동 (상승 추세 유지)
        noise = random.randint(-1, 1)
        return max(1, current + noise)

    elif scenario["type"] == "stable":
        low, high = scenario["range"]
        return random.randint(low, high)

    elif scenario["type"] == "new_entry":
        start = scenario["start"]
        end = scenario["end"]
        # 처음 20%는 낮은 순위로 시작, 이후 빠르게 상승
        if progress < 0.2:
            return random.randint(start - 5, start + 5)
        else:
            # 나머지 80%에서 급상승
            adjusted_progress = (progress - 0.2) / 0.8
            current = int(start - (start - end) * adjusted_progress)
            noise = random.randint(-2, 2)
            return max(1, current + noise)

    return random.randint(20, 50)


def generate_demo_history():
    """30일 데모 히스토리 생성"""

    # DB 초기화
    init_db()
    repo = RankingRepository()

    # 제품 데이터 로드
    products_df = load_all_products()

    # 기존 데이터 확인
    existing_dates = repo.get_date_count()
    if existing_dates > 0:
        print(f"Clearing existing {existing_dates} days of data...")
        # 기존 데이터 삭제를 위해 세션에서 직접 삭제
        from backend.db.models import RankingHistory
        repo.session.query(RankingHistory).delete()
        repo.session.commit()

    today = date.today()
    total_days = 30

    print(f"Generating {total_days} days of demo history...")

    # 카테고리별로 처리
    categories = {
        "lip_care": ["Lip Sleeping Mask", "Lip Sleeping Mask Vanilla"],
        "skincare": products_df[products_df["amazon_category"] == "skincare"]["product_name"].tolist(),
        "lip_makeup": ["Lip Glowy Balm"],
        "face_powder": ["Neo Cushion Matte"],
    }

    for day_index in range(total_days):
        target_date = today - timedelta(days=total_days - 1 - day_index)

        for category, product_names in categories.items():
            rankings = []

            # 카테고리 내 제품들 가져오기
            cat_products = products_df[
                (products_df["amazon_category"] == category) |
                (products_df["product_name"].isin(product_names))
            ].drop_duplicates(subset=["product_name"])

            if len(cat_products) == 0:
                continue

            for _, product in cat_products.iterrows():
                product_name = product["product_name"]
                is_laneige = product.get("is_laneige", False)

                # 라네즈 제품은 시나리오 기반
                if product_name in LANEIGE_SCENARIOS:
                    scenario = LANEIGE_SCENARIOS[product_name]
                    rank = generate_rank(scenario, day_index, total_days)
                elif is_laneige:
                    # 시나리오 없는 라네즈는 안정적
                    rank = random.randint(15, 35)
                else:
                    # 경쟁사 제품은 랜덤
                    rank = random.randint(1, len(cat_products))

                rankings.append({
                    "product_id": product.get("product_id"),
                    "product_name": product_name,
                    "brand": product["brand"],
                    "rank": rank,
                    "is_laneige": is_laneige,
                    "price": product.get("price", 0),
                })

            if rankings:
                df = pd.DataFrame(rankings)
                # 순위 정규화 (1, 2, 3, ...)
                df["rank"] = df["rank"].rank(method="first").astype(int)
                repo.save_daily_rankings(target_date, category, df)

        print(f"  {target_date}: saved")

    # 결과 확인
    print(f"\n=== Demo History Generated ===")
    print(f"Total dates: {repo.get_date_count()}")
    print(f"Date range: {min(repo.get_available_dates())} ~ {max(repo.get_available_dates())}")

    # 라네즈 제품 트렌드 확인
    print("\n=== LANEIGE Product Trends ===")
    for product_name in ["Lip Sleeping Mask", "Cream Skin Refiner", "Neo Cushion Matte", "Radian-C Cream"]:
        history = repo.get_product_history(product_name, days=30)
        if history:
            ranks = history["rankings"]
            print(f"{product_name[:25]:25s}: Day1={ranks[0]:2d} → Day30={ranks[-1]:2d} (avg={history['avg_rank']:.1f})")


if __name__ == "__main__":
    generate_demo_history()
