/**
 * 인사이트 페이지 컴포넌트
 * 성과 및 마케팅 인사이트를 시각화해요.
 *
 * @module components/Insights
 */

import { useState, useEffect } from 'react';
import { TrendingUp, Lightbulb, Target, Users, Award, ShoppingCart, Calendar, RefreshCw, Loader2, Rocket } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { getInsights, syncVectorDB, type InsightData } from '../services/api';

/**
 * 인사이트 메인 컴포넌트
 *
 * @description
 * - 성과 인사이트 카드 및 차트
 * - 마케팅 인사이트 카드 및 권장 전략
 * - 카테고리별 순위 개선률 차트
 *
 * @returns {JSX.Element} 인사이트 화면
 *
 * @example
 * <Insights />
 */
export function Insights() {
  const [insights, setInsights] = useState<InsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsights();
  }, []);

  /**
   * 인사이트 데이터를 불러와요.
   *
   * @returns {Promise<void>}
   */
  async function loadInsights() {
    try {
      setLoading(true);
      setError(null);
      const data = await getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to load insights:', err);
      setError('인사이트를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }

  /**
   * Vector DB 동기화 후 인사이트를 갱신해요.
   *
   * @returns {Promise<void>}
   */
  async function handleSync() {
    try {
      setSyncing(true);
      await syncVectorDB();
      const data = await getInsights();
      setInsights(data);
      alert('인사이트가 갱신되었습니다!');
    } catch {
      alert('동기화에 실패했습니다.');
    } finally {
      setSyncing(false);
    }
  }

  /**
   * 카드 타입에 맞는 아이콘 컴포넌트를 반환해요.
   *
   * @param {string} type 카드 타입
   * @returns {React.ComponentType} 아이콘 컴포넌트
   */
  const getIcon = (type: string) => {
    switch (type) {
      case 'best_seller': return Award;
      case 'rising': return TrendingUp;
      case 'achievement': return Target;
      case 'competition': return Users;
      case 'opportunity': return ShoppingCart;
      case 'action': return Rocket;
      default: return TrendingUp;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#1F5795]" />
        <span className="ml-2">인사이트 분석 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={loadInsights}
          className="px-4 py-2 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58]"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl">인사이트</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm">
            <Calendar className="w-4 h-4 text-gray-600" />
            <span className="text-sm text-gray-600">최근 30일</span>
          </div>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-6 py-2 bg-[#001C58] text-white rounded-lg hover:bg-[#1F5795] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {syncing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            인사이트 갱신
          </button>
        </div>
      </div>

      {/* Performance Insights Section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#4CAF50]/10 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-[#4CAF50]" />
          </div>
          <h2 className="text-2xl">성과 인사이트</h2>
        </div>

        {/* Performance Cards */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {insights?.performanceCards.map((card, index) => {
            const Icon = getIcon(card.type);
            return (
              <div
                key={index}
                className="bg-white rounded-xl p-6 shadow-sm border-l-4"
                style={{ borderLeftColor: card.color }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${card.color}15` }}
                  >
                    <Icon className="w-6 h-6" style={{ color: card.color }} />
                  </div>
                </div>
                <h3 className="text-lg mb-2">{card.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{card.description}</p>
                <div className="flex items-center gap-2">
                  <span className="text-sm" style={{ color: card.color }}>{card.metric}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Performance Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-xl mb-6">주간 성과 추이</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={insights?.performanceChart || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="week" stroke="#666" />
              <YAxis yAxisId="left" stroke="#4CAF50" />
              <YAxis yAxisId="right" orientation="right" stroke="#E4007F" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="top5Rate"
                stroke="#4CAF50"
                strokeWidth={2}
                name="TOP 5 달성률 (%)"
                dot={{ fill: '#4CAF50' }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avgRank"
                stroke="#E4007F"
                strokeWidth={2}
                name="평균 순위"
                dot={{ fill: '#E4007F' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Marketing Insights Section */}
      <div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#FF9800]/10 flex items-center justify-center">
            <Lightbulb className="w-6 h-6 text-[#FF9800]" />
          </div>
          <h2 className="text-2xl">마케팅 인사이트</h2>
        </div>

        {/* Marketing Cards */}
        <div className="grid grid-cols-3 gap-6 mb-6">
          {insights?.marketingCards.map((card, index) => {
            const Icon = getIcon(card.type);
            return (
              <div
                key={index}
                className="bg-white rounded-xl p-6 shadow-sm border-l-4"
                style={{ borderLeftColor: card.color }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${card.color}15` }}
                  >
                    <Icon className="w-6 h-6" style={{ color: card.color }} />
                  </div>
                </div>
                <h3 className="text-lg mb-2">{card.title}</h3>
                <p className="text-sm text-gray-600 mb-3">{card.description}</p>

                {card.details && card.details.length > 0 && (
                  <div className="space-y-2 mb-4">
                    {card.details.map((detail, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">
                          {detail.category || detail.product}
                        </span>
                        <span style={{ color: card.color }}>
                          {detail.status || detail.avgRank || detail.potential}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {card.recommendations && card.recommendations.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs font-semibold text-gray-500 mb-2">권장 마케팅 전략</p>
                    <ul className="space-y-1">
                      {card.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                          <span style={{ color: card.color }}>•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Category Trend Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <h3 className="text-xl mb-6">카테고리별 순위 개선률</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={insights?.categoryTrend || []} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" stroke="#666" />
              <YAxis dataKey="category" type="category" stroke="#666" width={100} />
              <Tooltip />
              <Bar dataKey="growth" name="개선률 (%)" radius={[0, 8, 8, 0]}>
                {insights?.categoryTrend.map((entry, index) => (
                  <rect key={`bar-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Last Updated */}
      <div className="mt-8 text-right text-sm text-gray-500">
        마지막 업데이트: {insights?.lastUpdated ? new Date(insights.lastUpdated).toLocaleString('ko-KR') : '-'}
      </div>
    </div>
  );
}
