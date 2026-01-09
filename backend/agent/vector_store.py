"""제품 벡터 스토어 모듈.

ChromaDB를 사용한 제품 정보 벡터 저장 및 검색 기능을 제공해요.
"""

from pathlib import Path
from typing import Any

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer


class ProductVectorStore:
    """제품 정보 벡터 스토어.

    ChromaDB와 SentenceTransformer를 활용하여
    제품 정보를 벡터화하고 유사도 검색을 제공해요.

    Attributes:
        persist_dir (Path): 데이터 저장 경로
        client: ChromaDB 클라이언트
        embedding_model: SentenceTransformer 임베딩 모델
        collection: ChromaDB 컬렉션
    """

    def __init__(
        self,
        persist_dir: str = "data/chroma_db",
        collection_name: str = "products",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """ProductVectorStore를 초기화해요.

        Args:
            persist_dir (str): 데이터 저장 경로 (기본값: data/chroma_db)
            collection_name (str): 컬렉션 이름 (기본값: products)
            embedding_model (str): 임베딩 모델 (기본값: all-MiniLM-L6-v2)
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.persist_dir))

        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)

        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"description": "Beauty product information for RAG"}
        )

    def _create_document(self, product: dict) -> str:
        """제품 정보를 문서 형태로 변환해요.

        Args:
            product (dict): 제품 정보 딕셔너리

        Returns:
            str: 임베딩용 텍스트 문서
        """
        parts = []

        parts.append(f"Product: {product.get('product_name', 'Unknown')}")
        parts.append(f"Brand: {product.get('brand', 'Unknown')}")

        if product.get("category"):
            parts.append(f"Category: {product['category']}")

        if product.get("features"):
            parts.append(f"Features: {product['features']}")

        if product.get("ingredients"):
            ingredients = str(product["ingredients"])
            if len(ingredients) > 500:
                ingredients = ingredients[:500] + "..."
            parts.append(f"Ingredients: {ingredients}")

        if product.get("skin_type"):
            parts.append(f"Suitable for: {product['skin_type']} skin")

        if product.get("price"):
            parts.append(f"Price: ${product['price']}")

        return "\n".join(parts)

    def add_products(self, products_df: pd.DataFrame, batch_size: int = 100) -> None:
        """제품 데이터를 벡터 스토어에 추가해요.

        Args:
            products_df (pd.DataFrame): 제품 데이터
            batch_size (int): 배치 크기 (기본값: 100)
        """
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        ids: list[str] = []

        for idx, row in products_df.iterrows():
            product = row.to_dict()

            doc = self._create_document(product)
            documents.append(doc)

            metadata: dict[str, Any] = {
                "product_name": str(product.get("product_name", "")),
                "brand": str(product.get("brand", "")),
                "category": str(product.get("category", "")),
                "amazon_category": str(product.get("amazon_category", "")),
                "price": float(product.get("price", 0)) if product.get("price") else 0.0,
                "is_laneige": bool(product.get("is_laneige", False)),
            }
            metadatas.append(metadata)

            product_id = product.get("product_id", idx)
            ids.append(f"product_{product_id}")

        total = len(documents)
        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            batch_docs = documents[i:end]
            batch_metas = metadatas[i:end]
            batch_ids = ids[i:end]

            embeddings: list[list[float]] = self.embedding_model.encode(batch_docs).tolist()

            self.collection.add(documents=batch_docs, metadatas=batch_metas, ids=batch_ids, embeddings=embeddings)  # type: ignore[arg-type]

            print(f"Added {end}/{total} products")

    def search(
        self, query: str, n_results: int = 5, filter_laneige: bool | None = None, filter_category: str | None = None
    ) -> list[dict]:
        """쿼리와 유사한 제품을 검색해요.

        Args:
            query (str): 검색 쿼리
            n_results (int): 반환할 결과 수 (기본값: 5)
            filter_laneige (bool | None): LANEIGE 필터 (기본값: None)
            filter_category (str | None): 카테고리 필터 (기본값: None)

        Returns:
            list[dict]: 검색 결과 목록 (document, metadata, distance, relevance_score)
        """
        query_embedding = self.embedding_model.encode([query]).tolist()

        where: dict[str, bool | str] = {}
        if filter_laneige is not None:
            where["is_laneige"] = filter_laneige
        if filter_category:
            where["amazon_category"] = filter_category

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where if where else None,  # type: ignore[arg-type]
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        documents = results.get("documents")
        metadatas = results.get("metadatas")
        distances = results.get("distances")
        if documents and metadatas and distances:
            for i, doc in enumerate(documents[0]):
                result = {
                    "document": doc,
                    "metadata": metadatas[0][i],
                    "distance": distances[0][i],
                    "relevance_score": 1 - distances[0][i],
                }
                search_results.append(result)

        return search_results

    def search_similar_products(self, product_name: str, n_results: int = 5) -> list[dict]:
        """유사 제품을 검색해요.

        Args:
            product_name (str): 제품명
            n_results (int): 반환할 결과 수 (기본값: 5)

        Returns:
            list[dict]: 유사 제품 목록
        """
        results = self.collection.query(query_texts=[product_name], n_results=1)

        documents = results.get("documents")
        if not documents or not documents[0]:
            return []

        product_doc = documents[0][0]
        return self.search(product_doc, n_results=n_results + 1)[1:]

    def get_product_context(self, query: str, n_results: int = 3) -> str:
        """질문에 관련된 제품 컨텍스트를 생성해요.

        Args:
            query (str): 검색 쿼리
            n_results (int): 반환할 결과 수 (기본값: 3)

        Returns:
            str: 관련 제품 컨텍스트
        """
        results = self.search(query, n_results=n_results)

        if not results:
            return "관련 제품 정보를 찾을 수 없습니다."

        context_parts = ["### 관련 제품 정보:\n"]

        for i, result in enumerate(results, 1):
            context_parts.append(f"**[{i}] {result['metadata']['product_name']}** ({result['metadata']['brand']})")
            context_parts.append(result["document"])
            context_parts.append(f"관련도: {result['relevance_score']:.2%}\n")

        return "\n".join(context_parts)

    def update_with_ranking_data(self, ranking_data: dict[str, pd.DataFrame]) -> int:
        """랭킹 데이터로 벡터 스토어를 업데이트해요.

        Args:
            ranking_data (dict[str, pd.DataFrame]): 카테고리별 랭킹 데이터

        Returns:
            int: 업데이트된 제품 수
        """
        print("Updating vector store with ranking data...")
        updated_count = 0

        for category, df in ranking_data.items():
            for _, row in df.iterrows():
                product_id = f"product_{row.get('product_id', row.name)}"

                day_cols = [c for c in df.columns if c.startswith("day_")]
                if day_cols:
                    ranks = [row[col] for col in day_cols if pd.notna(row[col])]
                    current_rank = ranks[-1] if ranks else None
                    avg_rank = sum(ranks) / len(ranks) if ranks else None
                    min_rank = min(ranks) if ranks else None
                    max_rank = max(ranks) if ranks else None

                    if len(ranks) >= 2:
                        trend = "상승" if ranks[-1] < ranks[0] else ("하락" if ranks[-1] > ranks[0] else "유지")
                    else:
                        trend = "데이터 부족"
                else:
                    current_rank = row.get("current_rank")
                    avg_rank = row.get("avg_rank")
                    min_rank = row.get("min_rank")
                    max_rank = row.get("max_rank")
                    trend = row.get("trend", "정보 없음")

                doc_parts = [
                    f"Product: {row.get('product_name', 'Unknown')}",
                    f"Brand: {row.get('brand', 'Unknown')}",
                    f"Category: {category}",
                    f"Amazon Category: {row.get('amazon_category', category)}",
                ]

                if current_rank:
                    doc_parts.append(f"Current Rank: #{int(current_rank)}")
                if avg_rank:
                    doc_parts.append(f"Average Rank (30 days): #{avg_rank:.1f}")
                if min_rank and max_rank:
                    doc_parts.append(f"Rank Range: #{int(min_rank)} ~ #{int(max_rank)}")
                if trend:
                    doc_parts.append(f"Trend: {trend}")

                if row.get("is_laneige"):
                    doc_parts.append("LANEIGE Product: Yes")
                    if current_rank and current_rank <= 5:
                        doc_parts.append("Status: TOP 5 Best Seller")
                    elif current_rank and current_rank <= 10:
                        doc_parts.append("Status: TOP 10 Best Seller")

                if day_cols:
                    doc_parts.append("\n=== 30일 랭킹 히스토리 ===")
                    for col in day_cols:
                        day_num = col.split("_")[1]
                        rank_value = row[col]
                        if pd.notna(rank_value):
                            doc_parts.append(f"Day {day_num}: #{int(rank_value)}")

                document = "\n".join(doc_parts)

                metadata: dict[str, Any] = {
                    "product_name": str(row.get("product_name", "")),
                    "brand": str(row.get("brand", "")),
                    "category": category,
                    "amazon_category": str(row.get("amazon_category", category)),
                    "is_laneige": bool(row.get("is_laneige", False)),
                    "current_rank": int(current_rank) if current_rank else 0,
                    "avg_rank": float(avg_rank) if avg_rank else 0.0,
                    "trend": str(trend) if trend else "",
                    "price": float(row.get("price", 0)) if row.get("price") else 0.0,
                }

                embedding: list[float] = self.embedding_model.encode([document]).tolist()[0]

                self.collection.upsert(
                    ids=[product_id],
                    documents=[document],
                    metadatas=[metadata],
                    embeddings=[embedding],  # type: ignore[arg-type]
                )
                updated_count += 1

        print(f"Vector store updated: {updated_count} products with ranking data")
        return updated_count

    def clear(self) -> None:
        """벡터 스토어를 초기화해요."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, metadata={"description": "Beauty product information for RAG"}
        )

    def count(self) -> int:
        """저장된 제품 수를 반환해요.

        Returns:
            int: 제품 수
        """
        return int(self.collection.count())


def build_vector_store(products_df: pd.DataFrame, persist_dir: str = "data/chroma_db") -> ProductVectorStore:
    """벡터 스토어를 빌드해요.

    Args:
        products_df (pd.DataFrame): 제품 데이터
        persist_dir (str): 저장 경로 (기본값: data/chroma_db)

    Returns:
        ProductVectorStore: 빌드된 벡터 스토어
    """
    store = ProductVectorStore(persist_dir=persist_dir)

    if store.count() > 0:
        print(f"Vector store already has {store.count()} products")
        return store

    print("Building vector store...")
    store.add_products(products_df)
    print(f"Vector store built with {store.count()} products")

    return store
