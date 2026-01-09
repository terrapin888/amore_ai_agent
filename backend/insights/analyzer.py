import json
import os
from datetime import datetime
from typing import Any

import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


INSIGHT_SYSTEM_PROMPT = """당신은 아모레퍼시픽의 글로벌 뷰티 시장 분석 전문가입니다.
Amazon US 뷰티 제품 랭킹 데이터를 분석하고 마케팅 인사이트를 제공합니다.

당신의 역할:
1. 라네즈(LANEIGE) 제품의 랭킹 성과 분석
2. 경쟁사 대비 강점/약점 파악
3. 구체적이고 실행 가능한 마케팅 전략 제안
4. 데이터 기반의 객관적 인사이트 도출

반드시 JSON 형식으로 응답하세요. 다른 텍스트 없이 순수 JSON만 출력하세요.
"""


class InsightAnalyzer:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.last_updated = None

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None
            print("Warning: ANTHROPIC_API_KEY not set. Using rule-based insights.")

    def analyze(self, ranking_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        self.last_updated = datetime.now().isoformat()

        ranking_summary = self._summarize_ranking_data(ranking_data)
        rag_context = self._get_rag_context()

        if self.client:
            return self._generate_ai_insights(ranking_summary, rag_context)
        else:
            return self._generate_rule_based_insights(ranking_data)

    def _summarize_ranking_data(self, ranking_data: dict[str, pd.DataFrame]) -> str:
        summary_parts = []

        for category, df in ranking_data.items():
            laneige_df = df[df["is_laneige"]]
            day_cols = [c for c in df.columns if c.startswith("day_")]

            if len(laneige_df) == 0:
                continue

            category_name = category.replace("_", " ").title()
            summary_parts.append(f"\n### {category_name} 카테고리")

            for _, row in laneige_df.iterrows():
                product_name = row["product_name"]
                rankings = [row[col] for col in day_cols if pd.notna(row[col])]

                if not rankings:
                    continue

                avg_rank = sum(rankings) / len(rankings)
                best_rank = min(rankings)
                max(rankings)
                recent_rank = rankings[-1] if rankings else 0

                if len(rankings) >= 14:
                    recent_avg = sum(rankings[-7:]) / 7
                    prev_avg = sum(rankings[-14:-7]) / 7
                    trend = "상승" if recent_avg < prev_avg else "하락" if recent_avg > prev_avg else "유지"
                    trend_value = round(prev_avg - recent_avg, 1)
                else:
                    trend = "데이터 부족"
                    trend_value = 0

                top5_days = sum(1 for r in rankings if r <= 5)

                summary_parts.append(
                    f"- {product_name}: 현재 {int(recent_rank)}위, 평균 {avg_rank:.1f}위, "
                    f"최고 {int(best_rank)}위, TOP5 {top5_days}일, 트렌드: {trend}({trend_value:+.1f})"
                )

            non_laneige = df[~df["is_laneige"]].head(3)
            if len(non_laneige) > 0:
                summary_parts.append("\n  주요 경쟁사:")
                for _, row in non_laneige.iterrows():
                    rankings = [row[col] for col in day_cols if pd.notna(row[col])]
                    if rankings:
                        avg = sum(rankings) / len(rankings)
                        summary_parts.append(f"  - {row['product_name'][:40]}: 평균 {avg:.1f}위")

        return "\n".join(summary_parts)

    def _get_rag_context(self) -> str:
        if not self.vector_store:
            return ""

        try:
            context = self.vector_store.get_product_context("라네즈 제품 특징 성분 마케팅", n_results=5)
            return str(context)
        except Exception as e:
            print(f"RAG context error: {e}")
            return ""

    def _generate_ai_insights(self, ranking_summary: str, rag_context: str) -> dict[str, Any]:
        prompt = f"""다음 랭킹 데이터와 제품 정보를 분석하여 마케팅 인사이트를 생성해주세요.

## 30일 랭킹 데이터 요약
{ranking_summary}

## 제품 상세 정보
{rag_context if rag_context else "제품 상세 정보 없음"}

## 요청사항
위 데이터를 분석하여 다음 JSON 구조로 인사이트를 생성해주세요:

{{
  "performanceCards": [
    {{
      "type": "best_seller|rising|achievement",
      "title": "카드 제목",
      "description": "구체적인 분석 내용 (제품명, 수치 포함)",
      "metric": "핵심 지표",
      "color": "#4CAF50|#E4007F|#4285F4"
    }}
  ],
  "marketingCards": [
    {{
      "type": "competition|opportunity|action",
      "title": "카드 제목",
      "description": "분석 내용",
      "details": [
        {{"category": "카테고리명", "avgRank": "순위", "status": "상태"}}
      ],
      "recommendations": [
        "구체적인 마케팅 액션 1",
        "구체적인 마케팅 액션 2"
      ],
      "color": "#FF9800|#9C27B0|#2196F3"
    }}
  ],
  "performanceChart": [
    {{"week": "1주차", "avgRank": 5.2, "top5Rate": 45}},
    {{"week": "2주차", "avgRank": 4.8, "top5Rate": 52}},
    {{"week": "3주차", "avgRank": 4.5, "top5Rate": 58}},
    {{"week": "4주차", "avgRank": 4.2, "top5Rate": 62}}
  ],
  "categoryTrend": [
    {{"category": "Lip Care", "growth": 15, "color": "#E4007F"}},
    {{"category": "Skincare", "growth": 8, "color": "#4285F4"}}
  ]
}}

주의사항:
1. performanceCards는 3개 생성 (베스트셀러, 급상승/주목 제품, 성과 지표)
2. marketingCards는 3개 생성 (경쟁 분석, 성장 기회, 마케팅 액션 플랜)
3. recommendations는 구체적이고 실행 가능한 마케팅 전략으로 작성
4. 실제 데이터의 제품명과 수치를 정확히 반영
5. 한국어로 작성

JSON만 출력하세요."""

        try:
            assert self.client is not None
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=INSIGHT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = response.content[0].text.strip()

            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            insights: dict[str, Any] = json.loads(response_text)
            insights["lastUpdated"] = self.last_updated

            return insights

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response: {response_text[:500]}")
            return self._generate_rule_based_insights_from_summary(ranking_summary)
        except Exception as e:
            print(f"AI insight generation error: {e}")
            return self._generate_rule_based_insights_from_summary(ranking_summary)

    def _generate_rule_based_insights(self, ranking_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        performance_cards = []
        marketing_cards = []
        performance_chart = []
        category_trend = []

        best_seller = self._find_best_seller(ranking_data)
        if best_seller:
            performance_cards.append(
                {
                    "type": "best_seller",
                    "title": "베스트 셀러",
                    "description": f"{best_seller['name']}이(가) {best_seller['category']} 카테고리에서 평균 {best_seller['avg_rank']:.1f}위를 기록하고 있습니다.",
                    "metric": f"최고 순위: {best_seller['best_rank']}위",
                    "color": "#4CAF50",
                }
            )

        top5_stats = self._calculate_top5_stats(ranking_data)
        performance_cards.append(
            {
                "type": "achievement",
                "title": "TOP 5 달성률",
                "description": f"라네즈 제품 {top5_stats['top5_products']}개가 TOP 5에 진입했습니다.",
                "metric": f"달성률: {top5_stats['rate']:.0f}%",
                "color": "#4285F4",
            }
        )

        performance_chart = self._generate_performance_chart(ranking_data)
        category_trend = self._generate_category_trend(ranking_data)

        marketing_cards.append(
            {
                "type": "action",
                "title": "마케팅 액션 플랜",
                "description": "현재 랭킹 데이터 기반 마케팅 전략입니다.",
                "details": [],
                "recommendations": [
                    "TOP 5 제품 중심 크로스셀링 캠페인 진행",
                    "리뷰 마케팅 강화로 신뢰도 향상",
                    "시즌별 키워드 광고 최적화",
                ],
                "color": "#2196F3",
            }
        )

        return {
            "performanceCards": performance_cards,
            "marketingCards": marketing_cards,
            "performanceChart": performance_chart,
            "categoryTrend": category_trend,
            "lastUpdated": self.last_updated,
        }

    def _generate_rule_based_insights_from_summary(self, _ranking_summary: str) -> dict[str, Any]:
        return {
            "performanceCards": [
                {
                    "type": "best_seller",
                    "title": "성과 분석",
                    "description": "AI 분석 중 오류가 발생했습니다. 기본 인사이트를 표시합니다.",
                    "metric": "재시도 필요",
                    "color": "#4CAF50",
                }
            ],
            "marketingCards": [
                {
                    "type": "action",
                    "title": "마케팅 제안",
                    "description": "인사이트 갱신 버튼을 눌러 다시 시도해주세요.",
                    "details": [],
                    "recommendations": ["인사이트 갱신 버튼 클릭"],
                    "color": "#2196F3",
                }
            ],
            "performanceChart": [
                {"week": "1주차", "avgRank": 10, "top5Rate": 30},
                {"week": "2주차", "avgRank": 10, "top5Rate": 30},
                {"week": "3주차", "avgRank": 10, "top5Rate": 30},
                {"week": "4주차", "avgRank": 10, "top5Rate": 30},
            ],
            "categoryTrend": [],
            "lastUpdated": self.last_updated,
        }

    def _find_best_seller(self, ranking_data: dict[str, pd.DataFrame]) -> dict | None:
        best = None

        for category, df in ranking_data.items():
            laneige_df = df[df["is_laneige"]]
            day_cols = [c for c in df.columns if c.startswith("day_")]

            for _, row in laneige_df.iterrows():
                rankings = [row[col] for col in day_cols if pd.notna(row[col])]
                if not rankings:
                    continue

                avg_rank = sum(rankings) / len(rankings)
                best_rank = min(rankings)

                if best is None or avg_rank < best["avg_rank"]:
                    best = {
                        "name": row["product_name"],
                        "category": category.replace("_", " ").title(),
                        "avg_rank": avg_rank,
                        "best_rank": int(best_rank),
                    }

        return best

    def _calculate_top5_stats(self, ranking_data: dict[str, pd.DataFrame]) -> dict:
        total = 0
        top5 = 0

        for _category, df in ranking_data.items():
            laneige_df = df[df["is_laneige"]]
            day_cols = [c for c in df.columns if c.startswith("day_")]

            for _, row in laneige_df.iterrows():
                total += 1
                rankings = [row[col] for col in day_cols if pd.notna(row[col])]
                if rankings and sum(rankings) / len(rankings) <= 5:
                    top5 += 1

        return {"total_products": total, "top5_products": top5, "rate": (top5 / total * 100) if total > 0 else 0}

    def _generate_performance_chart(self, ranking_data: dict[str, pd.DataFrame]) -> list[dict]:
        chart = []
        weeks = ["1주차", "2주차", "3주차", "4주차"]

        for week_idx, week_name in enumerate(weeks):
            week_ranks = []

            for _category, df in ranking_data.items():
                laneige_df = df[df["is_laneige"]]
                day_cols = [c for c in df.columns if c.startswith("day_")]

                start = week_idx * 7 + 1
                end = min((week_idx + 1) * 7, 30)
                week_cols = [f"day_{d}" for d in range(start, end + 1) if f"day_{d}" in day_cols]

                for _, row in laneige_df.iterrows():
                    for col in week_cols:
                        if col in row and pd.notna(row[col]):
                            week_ranks.append(row[col])

            avg = sum(week_ranks) / len(week_ranks) if week_ranks else 0
            top5_rate = (sum(1 for r in week_ranks if r <= 5) / len(week_ranks) * 100) if week_ranks else 0

            chart.append({"week": week_name, "avgRank": round(avg, 1), "top5Rate": round(top5_rate, 0)})

        return chart

    def _generate_category_trend(self, ranking_data: dict[str, pd.DataFrame]) -> list[dict]:
        trends = []
        colors = {"lip_care": "#E4007F", "skincare": "#4285F4", "lip_makeup": "#4CAF50", "face_powder": "#FF9800"}

        for category, df in ranking_data.items():
            laneige_df = df[df["is_laneige"]]
            day_cols = [c for c in df.columns if c.startswith("day_")]

            if len(laneige_df) == 0 or len(day_cols) < 7:
                continue

            first_week = []
            last_week = []

            for _, row in laneige_df.iterrows():
                for col in day_cols[:7]:
                    if pd.notna(row[col]):
                        first_week.append(row[col])
                for col in day_cols[-7:]:
                    if pd.notna(row[col]):
                        last_week.append(row[col])

            if first_week and last_week:
                first_avg = sum(first_week) / len(first_week)
                last_avg = sum(last_week) / len(last_week)
                improvement = ((first_avg - last_avg) / first_avg * 100) if first_avg > 0 else 0

                trends.append(
                    {
                        "category": category.replace("_", " ").title(),
                        "growth": round(improvement, 0),
                        "color": colors.get(category, "#666666"),
                    }
                )

        trends.sort(key=lambda x: x["growth"], reverse=True)
        return trends
