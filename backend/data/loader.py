"""데이터 로더 모듈.

Kaggle cosmetics.csv와 LANEIGE 제품 데이터를 로드하고
Amazon 카테고리 구조로 매핑해요.
"""

import pandas as pd

# Amazon category mapping (based on competition provided links)
AMAZON_CATEGORIES = {
    "all_beauty": "Beauty & Personal Care",
    "lip_care": "Lip Care",
    "skincare": "Skin Care",
    "lip_makeup": "Lip Makeup",
    "face_powder": "Face Powder",
}

# Kaggle Label → Amazon category mapping
KAGGLE_TO_AMAZON = {
    "Moisturizer": "skincare",
    "Cleanser": "skincare",
    "Face Mask": "skincare",
    "Treatment": "skincare",
    "Eye cream": "skincare",
    "Sun protect": "skincare",
}


def load_kaggle_data(file_path: str = "datasets/cosmetics.csv") -> pd.DataFrame:
    """Kaggle cosmetics.csv를 로드하고 표준화된 DataFrame으로 변환해요.

    Args:
        file_path (str): CSV 파일 경로 (기본값: datasets/cosmetics.csv)

    Returns:
        pd.DataFrame: amazon_category, skin_type 등 정규화된 컬럼을 포함한 DataFrame
    """
    df = pd.read_csv(file_path)

    # Add Amazon category mapping
    df["amazon_category"] = df["Label"].map(KAGGLE_TO_AMAZON).fillna("skincare")

    # Rename columns to standard format
    df = df.rename(
        columns={
            "Label": "category",
            "Brand": "brand",
            "Name": "product_name",
            "Price": "price",
            "Rank": "rating",
            "Ingredients": "ingredients",
        }
    )

    # Consolidate skin type columns into a single field
    skin_types = []
    for _, row in df.iterrows():
        types = []
        if row.get("Combination") == 1:
            types.append("Combination")
        if row.get("Dry") == 1:
            types.append("Dry")
        if row.get("Normal") == 1:
            types.append("Normal")
        if row.get("Oily") == 1:
            types.append("Oily")
        if row.get("Sensitive") == 1:
            types.append("Sensitive")
        skin_types.append(", ".join(types) if types else "All")

    df["skin_type"] = skin_types

    # Select only required columns
    columns = ["product_name", "brand", "category", "amazon_category", "price", "rating", "ingredients", "skin_type"]
    df = df[[c for c in columns if c in df.columns]]

    return df


def get_laneige_products() -> pd.DataFrame:
    """LANEIGE 제품 데이터를 반환해요.

    Returns:
        pd.DataFrame: 10개 LANEIGE 제품 정보 (성분, 특징, 가격, 피부 타입 등)
    """

    laneige_products = [
        {
            "product_name": "Lip Sleeping Mask",
            "brand": "LANEIGE",
            "category": "Lip Care",
            "amazon_category": "lip_care",
            "price": 24.00,
            "rating": 4.6,
            "ingredients": "Diisostearyl Malate, Hydrogenated Polyisobutene, Phytosteryl/Isostearyl/Cetyl/Stearyl/Behenyl Dimer Dilinoleate, Hydrogenated Poly(C6-14 Olefin), Polybutene, Candelilla Cera/Candelilla Wax, Polyglyceryl-2 Triisostearate, Silica Dimethyl Silylate, Synthetic Fluorphlogopite, Methyl Methacrylate Crosspolymer, Hydrogenated Vegetable Oil, Astrocaryum Murumuru Seed Butter, Cocos Nucifera (Coconut) Oil",
            "skin_type": "All",
            "features": "Overnight lip treatment, Berry flavor, Vitamin C, Hyaluronic Acid",
        },
        {
            "product_name": "Water Bank Blue Hyaluronic Cream",
            "brand": "LANEIGE",
            "category": "Moisturizer",
            "amazon_category": "skincare",
            "price": 39.00,
            "rating": 4.5,
            "ingredients": "Water, Glycerin, Butylene Glycol, Dimethicone, 1,2-Hexanediol, Niacinamide, Hydroxyethyl Urea, Sodium Hyaluronate, Pentylene Glycol, Betaine",
            "skin_type": "Normal, Dry, Combination",
            "features": "Blue Hyaluronic Acid, 72-hour hydration, Squalane, Lightweight texture",
        },
        {
            "product_name": "Cream Skin Refiner",
            "brand": "LANEIGE",
            "category": "Treatment",
            "amazon_category": "skincare",
            "price": 38.00,
            "rating": 4.4,
            "ingredients": "Water, Glycerin, Alcohol Denat., Butylene Glycol, Caprylic/Capric Triglyceride, Cetyl Ethylhexanoate, 1,2-Hexanediol, Niacinamide",
            "skin_type": "All",
            "features": "2-in-1 toner and cream, White tea leaf water, Amino acid-rich",
        },
        {
            "product_name": "Water Sleeping Mask",
            "brand": "LANEIGE",
            "category": "Face Mask",
            "amazon_category": "skincare",
            "price": 32.00,
            "rating": 4.5,
            "ingredients": "Water, Butylene Glycol, Cyclopentasiloxane, Glycerin, Cyclohexasiloxane, Trehalose, Sodium Hyaluronate, Oenothera Biennis (Evening Primrose) Root Extract",
            "skin_type": "All",
            "features": "Overnight mask, Hydro Ionized Mineral Water, Sleep-Scent technology",
        },
        {
            "product_name": "Neo Cushion Matte",
            "brand": "LANEIGE",
            "category": "Face Powder",
            "amazon_category": "face_powder",
            "price": 38.00,
            "rating": 4.3,
            "ingredients": "Water, Cyclopentasiloxane, Titanium Dioxide, Phenyl Trimethicone, Ethylhexyl Methoxycinnamate, Butylene Glycol, PEG-10 Dimethicone",
            "skin_type": "Oily, Combination",
            "features": "Matte finish, SPF 42 PA++, Blur effect, Long-lasting coverage",
        },
        {
            "product_name": "Lip Glowy Balm",
            "brand": "LANEIGE",
            "category": "Lip Makeup",
            "amazon_category": "lip_makeup",
            "price": 18.00,
            "rating": 4.4,
            "ingredients": "Diisostearyl Malate, Hydrogenated Polyisobutene, Polybutene, Octyldodecanol, Mica, Silica, Shea Butter",
            "skin_type": "All",
            "features": "Tinted lip balm, Shea butter, Murumuru butter, Glossy finish",
        },
        {
            "product_name": "Radian-C Cream",
            "brand": "LANEIGE",
            "category": "Moisturizer",
            "amazon_category": "skincare",
            "price": 48.00,
            "rating": 4.5,
            "ingredients": "Water, Glycerin, Dimethicone, Niacinamide, Ascorbic Acid, Butylene Glycol, Betaine, Panthenol",
            "skin_type": "All",
            "features": "Vitamin C, Brightening, Dark spot care, Antioxidant",
        },
        {
            "product_name": "Bouncy & Firm Sleeping Mask",
            "brand": "LANEIGE",
            "category": "Face Mask",
            "amazon_category": "skincare",
            "price": 36.00,
            "rating": 4.4,
            "ingredients": "Water, Butylene Glycol, Glycerin, Dimethicone, Niacinamide, Adenosine, Peptides",
            "skin_type": "Normal, Dry",
            "features": "Anti-aging, Firming, Overnight treatment, Peptide complex",
        },
        {
            "product_name": "Water Bank Hydro Essence",
            "brand": "LANEIGE",
            "category": "Treatment",
            "amazon_category": "skincare",
            "price": 44.00,
            "rating": 4.5,
            "ingredients": "Water, Butylene Glycol, Glycerin, 1,2-Hexanediol, Sodium Hyaluronate, Niacinamide, Green Mineral Water",
            "skin_type": "All",
            "features": "Hydrating essence, Blue Hyaluronic Acid, Lightweight, Fast-absorbing",
        },
        {
            "product_name": "Lip Sleeping Mask Vanilla",
            "brand": "LANEIGE",
            "category": "Lip Care",
            "amazon_category": "lip_care",
            "price": 24.00,
            "rating": 4.6,
            "ingredients": "Diisostearyl Malate, Hydrogenated Polyisobutene, Phytosteryl/Isostearyl/Cetyl/Stearyl/Behenyl Dimer Dilinoleate, Shea Butter, Murumuru Butter, Coconut Oil, Vanilla Extract",
            "skin_type": "All",
            "features": "Overnight lip treatment, Vanilla flavor, Vitamin C, Hyaluronic Acid",
        },
    ]

    return pd.DataFrame(laneige_products)


def load_all_products(kaggle_path: str = "datasets/cosmetics.csv") -> pd.DataFrame:
    """Kaggle 데이터셋과 LANEIGE 제품을 합쳐서 전체 제품 데이터를 로드해요.

    Args:
        kaggle_path (str): Kaggle CSV 파일 경로 (기본값: datasets/cosmetics.csv)

    Returns:
        pd.DataFrame: product_id, is_laneige 플래그가 포함된 통합 DataFrame
    """

    # Load Kaggle data
    kaggle_df = load_kaggle_data(kaggle_path)

    # Add LANEIGE products
    laneige_df = get_laneige_products()

    # Add features column if not exists
    if "features" not in kaggle_df.columns:
        kaggle_df["features"] = ""

    # Merge datasets
    all_products = pd.concat([laneige_df, kaggle_df], ignore_index=True)

    # Generate product_id
    all_products["product_id"] = range(1, len(all_products) + 1)

    # Add is_laneige flag based on brand
    all_products["is_laneige"] = all_products["brand"] == "LANEIGE"

    return all_products


def get_products_by_category(df: pd.DataFrame, amazon_category: str) -> pd.DataFrame:
    """특정 Amazon 카테고리로 제품을 필터링해요.

    Args:
        df (pd.DataFrame): 제품 데이터 DataFrame
        amazon_category (str): 필터링할 카테고리 (예: "lip_care", "skincare")

    Returns:
        pd.DataFrame: 해당 카테고리 제품만 포함된 DataFrame
    """
    return df[df["amazon_category"] == amazon_category].copy()


def get_laneige_only(df: pd.DataFrame) -> pd.DataFrame:
    """LANEIGE 브랜드 제품만 필터링해요.

    Args:
        df (pd.DataFrame): 제품 데이터 DataFrame

    Returns:
        pd.DataFrame: LANEIGE 제품만 포함된 DataFrame
    """
    return df[df["is_laneige"]].copy()


if __name__ == "__main__":
    # Test
    print("Loading all products...")
    df = load_all_products()
    print(f"Total products: {len(df)}")
    print(f"Laneige products: {len(df[df['is_laneige']])}")
    print("\nCategories:")
    print(df["amazon_category"].value_counts())
    print("\nLaneige products:")
    print(df[df["is_laneige"]][["product_name", "category", "price"]])
