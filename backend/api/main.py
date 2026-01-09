"""LANEIGE Ranking Insight API 서버 모듈.

FastAPI 기반 REST API 서버로 랭킹 분석, AI 채팅,
리포트 생성 기능을 제공해요.
"""

import math
import os
import sys
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.chat.chat_engine import ChatEngine
from backend.data.loader import load_all_products
from backend.db import init_db
from backend.insights import InsightAnalyzer
from backend.rag.vector_store import ProductVectorStore
from backend.ranking import RankingService, get_ranking_provider
from backend.ranking.base import RankingProvider
from backend.report.excel_generator import ExcelReportGenerator

app = FastAPI(
    title="Laneige Ranking Insight API",
    description="Global beauty platform ranking analysis AI agent API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

products_df: pd.DataFrame | None = None
ranking_provider: RankingProvider | None = None
ranking_service: RankingService | None = None
vector_store: ProductVectorStore | None = None
chat_engine: ChatEngine | None = None
insight_analyzer: InsightAnalyzer | None = None
ranking_data_cache: dict[str, pd.DataFrame] | None = None
insights_cache: dict[str, Any] | None = None
is_initialized: bool = False


def refresh_ranking_cache(days: int = 30) -> dict[str, pd.DataFrame]:
    """랭킹 캐시를 갱신해요.

    Args:
        days (int): 조회할 일수 (기본값: 30)

    Returns:
        dict: 카테고리별 랭킹 데이터
    """
    global ranking_data_cache, insights_cache

    assert ranking_service is not None
    assert ranking_provider is not None

    print("Checking today's ranking data...")
    was_collected = ranking_service.ensure_today_data()
    if was_collected:
        print("Today's ranking data collected and saved to DB")
    else:
        print("Today's data already exists in DB")

    print(f"Loading ranking history ({days} days)...")
    ranking_data_cache = ranking_service.get_all_categories(days=days)

    if not ranking_data_cache:
        print("No history in DB, generating initial data...")
        ranking_data_cache = ranking_provider.get_all_categories(days=days)

    print(f"Ranking cache refreshed: {len(ranking_data_cache)} categories")

    if insight_analyzer and ranking_data_cache:
        print("Generating insights...")
        insights_cache = insight_analyzer.analyze(ranking_data_cache)
        print("Insights generated successfully")

    return ranking_data_cache


class ChatRequest(BaseModel):
    """AI 채팅 요청 모델.

    Attributes:
        message (str): 사용자 메시지
    """

    message: str


class ChatResponse(BaseModel):
    """AI 채팅 응답 모델.

    Attributes:
        response (str): AI 응답 메시지
        context_used (list[str] | None): 사용된 컨텍스트 목록
    """

    response: str
    context_used: list[str] | None = None


class ReportGenerateRequest(BaseModel):
    """리포트 생성 요청 모델.

    Attributes:
        days (int): 리포트에 포함할 일수 (기본값: 30)
    """

    days: int = 30


class ProductResponse(BaseModel):
    """제품 응답 모델.

    Attributes:
        product_id (int): 제품 ID
        product_name (str): 제품명
        brand (str): 브랜드명
        category (str): 카테고리
        price (float): 가격
        rating (float): 평점
        is_laneige (bool): 라네즈 제품 여부
    """

    product_id: int
    product_name: str
    brand: str
    category: str
    price: float
    rating: float
    is_laneige: bool


class RankingResponse(BaseModel):
    """랭킹 응답 모델.

    Attributes:
        category (str): 카테고리명
        rankings (list[dict]): 랭킹 목록
    """

    category: str
    rankings: list[dict]


@app.on_event("startup")
async def startup_event() -> None:
    global products_df, ranking_provider, ranking_service, vector_store, chat_engine, insight_analyzer, is_initialized

    print("=" * 50)
    print("Initializing Laneige Ranking Insight API...")
    print("=" * 50)

    init_db()
    print("Database initialized")

    products_df = load_all_products()
    print(f"Loaded {len(products_df)} products")

    ranking_provider = get_ranking_provider(products_df)
    print(f"Ranking provider ready: {ranking_provider.provider_name} (live={ranking_provider.is_live_data})")

    ranking_service = RankingService(ranking_provider)
    print("Ranking service ready (DB history enabled)")

    vector_store = ProductVectorStore()
    if vector_store.count() == 0:
        laneige_products = products_df[products_df["is_laneige"]]
        vector_store.add_products(laneige_products)
    print(f"Vector store: {vector_store.count()} products")

    insight_analyzer = InsightAnalyzer(vector_store=vector_store)
    print(
        "Insight analyzer ready (AI RAG enabled)" if insight_analyzer.client else "Insight analyzer ready (rule-based)"
    )

    refresh_ranking_cache(days=30)

    chat_engine = ChatEngine(vector_store=vector_store, ranking_engine=ranking_provider)
    print("Chat engine ready")

    db_stats = ranking_service.get_stats()
    print(f"DB stats: {db_stats['total_dates']} days of history")

    is_initialized = True
    print("=" * 50)
    print("API server initialized successfully!")
    print("=" * 50)


@app.get("/")
async def root() -> dict[str, Any]:
    return {"status": "ok", "message": "Laneige Ranking Insight API is running", "initialized": is_initialized}


@app.get("/api/products", response_model=list[dict])
async def get_products(category: str | None = None, laneige_only: bool = False, limit: int = 100) -> list[dict]:
    if not is_initialized or products_df is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    df = products_df.copy()

    if laneige_only:
        df = df[df["is_laneige"]]

    if category:
        df = df[df["amazon_category"] == category]

    df = df.head(limit)

    result: list[dict] = df.to_dict(orient="records")
    return result


@app.get("/api/products/laneige")
async def get_laneige_products() -> list[dict]:
    if not is_initialized or products_df is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    laneige = products_df[products_df["is_laneige"]]
    result: list[dict] = laneige.to_dict(orient="records")
    return result


@app.get("/api/rankings")
async def get_rankings(category: str = "all", days: int = 30) -> dict[str, Any]:
    if not is_initialized or ranking_data_cache is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    if category == "all":
        result: dict[str, Any] = {}
        for cat, df in ranking_data_cache.items():
            result[cat] = df.to_dict(orient="records")
        return result
    else:
        if category in ranking_data_cache:
            return {category: ranking_data_cache[category].to_dict(orient="records")}
        else:
            return {category: []}


@app.get("/api/rankings/summary")
async def get_ranking_summary() -> dict[str, Any]:
    if not is_initialized or ranking_data_cache is None or ranking_service is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    summaries: dict[str, Any] = {}
    for category in ranking_data_cache:
        summaries[category] = ranking_service.get_laneige_summary(category)

    return summaries


@app.get("/api/rankings/chart-data")
async def get_chart_data(days: int = 30) -> list[dict[str, Any]]:
    if not is_initialized or ranking_data_cache is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    ranking_data = ranking_data_cache
    chart_data: list[dict[str, Any]] = []

    first_category = list(ranking_data.values())[0]
    date_columns = [col for col in first_category.columns if col.startswith("day_")]

    for date_col in date_columns:
        day_num = int(date_col.split("_")[1])
        data_point = {"date": f"Day {day_num}"}

        for _category, df in ranking_data.items():
            laneige_rows = df[df["is_laneige"]]
            for _, row in laneige_rows.iterrows():
                product_name = row["product_name"].replace(" ", "_")
                data_point[product_name] = row[date_col]

        chart_data.append(data_point)

    return chart_data


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not is_initialized or chat_engine is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    response = chat_engine.chat(request.message)

    return ChatResponse(response=response, context_used=[])


@app.get("/api/reports")
async def list_reports() -> list[dict[str, Any]]:
    output_dir = "output"

    if not os.path.exists(output_dir):
        return []

    reports: list[dict[str, Any]] = []
    for filename in os.listdir(output_dir):
        if filename.endswith(".xlsx"):
            filepath = os.path.join(output_dir, filename)
            stat = os.stat(filepath)
            reports.append(
                {"filename": filename, "filepath": filepath, "created_at": stat.st_mtime, "size": stat.st_size}
            )

    reports.sort(key=lambda x: x["created_at"], reverse=True)

    return reports


@app.post("/api/reports/generate")
async def generate_report(request: ReportGenerateRequest) -> dict[str, Any]:
    if not is_initialized or ranking_data_cache is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    generator = ExcelReportGenerator()
    filepath = generator.create_ranking_report(ranking_data_cache)

    return {"success": True, "filepath": filepath, "filename": os.path.basename(filepath)}


@app.get("/api/reports/download/{filename}")
async def download_report(filename: str) -> FileResponse:
    filepath = os.path.join("output", filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/vectordb/sync")
async def sync_vector_db() -> dict[str, Any]:
    if not is_initialized or ranking_service is None or vector_store is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    print("Force collecting today's rankings...")
    ranking_service.collect_today_rankings()

    ranking_data = refresh_ranking_cache(days=30)

    updated_count = vector_store.update_with_ranking_data(ranking_data)

    db_stats = ranking_service.get_stats()

    return {
        "success": True,
        "updated_count": updated_count,
        "history_days": db_stats["total_dates"],
        "message": f"Sync complete! {updated_count} products, {db_stats['total_dates']} days of history",
    }


@app.get("/api/db/stats")
async def get_db_stats() -> dict[str, Any]:
    if not is_initialized or ranking_service is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    return ranking_service.get_stats()


@app.get("/api/insights")
async def get_insights() -> dict[str, Any]:
    if not is_initialized or insight_analyzer is None or ranking_data_cache is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    if insights_cache is None:
        return insight_analyzer.analyze(ranking_data_cache)

    return insights_cache


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    if not is_initialized or products_df is None or ranking_data_cache is None:
        raise HTTPException(status_code=503, detail="Server not initialized")

    total_products = len(products_df)
    laneige_products = len(products_df[products_df["is_laneige"]])

    top5_count = 0

    for _category, df in ranking_data_cache.items():
        laneige = df[df["is_laneige"]]
        for _, row in laneige.iterrows():
            avg_rank = row[[c for c in df.columns if c.startswith("day_")]].mean()
            if avg_rank <= 5:
                top5_count += 1

    avg_ranks: list[float] = []
    for _category, df in ranking_data_cache.items():
        laneige = df[df["is_laneige"]]
        for _, row in laneige.iterrows():
            avg_rank = row[[c for c in df.columns if c.startswith("day_")]].mean()
            if not math.isnan(avg_rank):
                avg_ranks.append(float(avg_rank))

    overall_avg_rank = sum(avg_ranks) / len(avg_ranks) if avg_ranks else 0.0

    if math.isnan(overall_avg_rank):
        overall_avg_rank = 0.0

    return {
        "total_products": int(total_products),
        "laneige_products": int(laneige_products),
        "top5_products": int(top5_count),
        "average_rank": round(float(overall_avg_rank), 1),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
