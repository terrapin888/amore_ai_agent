/**
 * 대시보드 페이지 컴포넌트
 * 랭킹 통계, 차트, 제품 테이블을 표시해요.
 *
 * @module components/Dashboard
 */

import { useState, useEffect } from 'react';
import { Package, Sparkles, Trophy, TrendingUp, ArrowUp, ArrowDown, Download, Loader2, RefreshCw } from 'lucide-react';
import { StatCard } from './StatCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getStats, getChartData, getRankingSummary, generateReport, syncVectorDB, type Stats } from '../services/api';

/**
 * 카테고리별 파이 차트 데이터
 * @constant {Array<{name: string, value: number, color: string}>}
 */
const categoryData = [
  { name: 'Lip Care', value: 40, color: '#1F5795' },
  { name: 'Skincare', value: 35, color: '#001C58' },
  { name: 'Makeup', value: 25, color: '#7D7D7D' },
];

/**
 * 제품 랭킹 테이블용 데이터
 *
 * @interface ProductRanking
 * @property {number} rank 순위
 * @property {string} name 제품명
 * @property {string} category 카테고리
 * @property {number} current 현재 순위
 * @property {number} average 평균 순위
 * @property {number} change 변동값
 * @property {boolean} isTop5 TOP 5 여부
 */
interface ProductRanking {
  rank: number;
  name: string;
  category: string;
  current: number;
  average: number;
  change: number;
  isTop5: boolean;
}

/**
 * 차트 렌더링용 포맷된 데이터
 *
 * @interface FormattedChartData
 * @property {string} date 날짜 (MM/DD 형식)
 * @property {number} lipMask Lip Sleeping Mask 순위
 * @property {number} waterMask Water Sleeping Mask 순위
 * @property {number} creamSkin Cream Skin Refiner 순위
 */
interface FormattedChartData {
  date: string;
  lipMask: number;
  waterMask: number;
  creamSkin: number;
}

/**
 * 대시보드 메인 컴포넌트
 *
 * @description
 * - 통계 카드 (전체 제품, 라네즈 제품, TOP 5, 평균 순위)
 * - 30일 랭킹 추이 라인 차트
 * - 카테고리별 성과 파이 차트
 * - 라네즈 제품 랭킹 테이블
 */
export function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [chartData, setChartData] = useState<FormattedChartData[]>([]);
  const [productData, setProductData] = useState<ProductRanking[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      const [statsData, chartDataResult, summaryData] = await Promise.all([
        getStats(),
        getChartData(30),
        getRankingSummary()
      ]);

      setStats(statsData);

      const today = new Date();
      const formattedChartData: FormattedChartData[] = chartDataResult.map((item, index) => {
        const date = new Date(today);
        date.setDate(today.getDate() - (chartDataResult.length - 1 - index));
        return {
          date: `${date.getMonth() + 1}/${date.getDate()}`,
          lipMask: Number(item['Lip_Sleeping_Mask']) || 0,
          waterMask: Number(item['Water_Sleeping_Mask']) || 0,
          creamSkin: Number(item['Cream_Skin_Refiner']) || 0,
        };
      });
      setChartData(formattedChartData);

      const products: ProductRanking[] = [];
      let rank = 1;
      for (const [category, summary] of Object.entries(summaryData)) {
        for (const [productName, data] of Object.entries(summary)) {
          products.push({
            rank: rank++,
            name: productName,
            category: category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
            current: data.best_rank,
            average: data.avg_rank,
            change: Math.round((data.avg_rank - data.best_rank) * 10) / 10,
            isTop5: data.avg_rank <= 5
          });
        }
      }
      setProductData(products.slice(0, 5));

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('데이터를 불러오는데 실패했습니다. 서버가 실행 중인지 확인해주세요.');
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateReport() {
    try {
      setGenerating(true);
      const result = await generateReport(30);
      alert(`리포트가 생성되었습니다: ${result.filename}`);
    } catch {
      alert('리포트 생성에 실패했습니다.');
    } finally {
      setGenerating(false);
    }
  }

  async function handleSyncVectorDB() {
    try {
      setSyncing(true);
      const result = await syncVectorDB();
      alert(result.message);
    } catch {
      alert('Vector DB 동기화에 실패했습니다.');
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#1F5795]" />
        <span className="ml-2">데이터 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-red-500 mb-4">{error}</p>
        <button
          onClick={loadData}
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
        <h1 className="text-3xl">대시보드</h1>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 bg-white rounded-lg shadow-sm">
            <span className="text-sm text-gray-600">2025.12.04 - 2026.01.04</span>
          </div>
          <button
            onClick={handleSyncVectorDB}
            disabled={syncing}
            className="px-6 py-2 bg-[#001C58] text-white rounded-lg hover:bg-[#1F5795] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {syncing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            AI 동기화
          </button>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-6 py-2 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            리포트 다운로드
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-6 mb-8">
        <StatCard title="전체 제품" value={`${stats?.total_products?.toLocaleString() || 0}개`} icon={Package} />
        <StatCard title="라네즈 제품" value={`${stats?.laneige_products || 0}개`} icon={Sparkles} />
        <StatCard title="TOP 5 제품" value={`${stats?.top5_products || 0}개`} icon={Trophy} />
        <StatCard title="평균 순위" value={`${stats?.average_rank || 0}위`} icon={TrendingUp} />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-5 gap-6 mb-8">
        {/* Ranking Trend Chart */}
        <div className="col-span-3 bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl mb-6">30일 랭킹 추이</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" stroke="#666" />
              <YAxis reversed domain={[0, 50]} stroke="#666" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="lipMask"
                stroke="#1F5795"
                strokeWidth={2}
                name="Lip Sleeping Mask"
                dot={{ fill: '#1F5795' }}
              />
              <Line
                type="monotone"
                dataKey="waterMask"
                stroke="#001C58"
                strokeWidth={2}
                name="Water Sleeping Mask"
                dot={{ fill: '#001C58' }}
              />
              <Line
                type="monotone"
                dataKey="creamSkin"
                stroke="#7D7D7D"
                strokeWidth={2}
                name="Cream Skin"
                dot={{ fill: '#7D7D7D' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Performance */}
        <div className="col-span-2 bg-white rounded-xl p-6 shadow-sm">
          <h2 className="text-xl mb-6">카테고리별 성과</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                label={({ name, value }) => `${name} ${value}%`}
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Product Ranking Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl">라네즈 제품 랭킹</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left text-sm text-gray-600">순위</th>
                <th className="px-6 py-4 text-left text-sm text-gray-600">제품명</th>
                <th className="px-6 py-4 text-left text-sm text-gray-600">카테고리</th>
                <th className="px-6 py-4 text-left text-sm text-gray-600">현재 순위</th>
                <th className="px-6 py-4 text-left text-sm text-gray-600">평균 순위</th>
                <th className="px-6 py-4 text-left text-sm text-gray-600">변동</th>
              </tr>
            </thead>
            <tbody>
              {productData.map((product) => (
                <tr
                  key={product.rank}
                  className={`border-t hover:bg-gray-100 transition-colors ${
                    product.isTop5 ? 'bg-blue-50' : ''
                  }`}
                >
                  <td className="px-6 py-4">{product.rank}</td>
                  <td className="px-6 py-4">{product.name}</td>
                  <td className="px-6 py-4 text-gray-600">{product.category}</td>
                  <td className="px-6 py-4">{product.current}위</td>
                  <td className="px-6 py-4 text-gray-600">{product.average}위</td>
                  <td className="px-6 py-4">
                    <span
                      className={`flex items-center gap-1 ${
                        product.change > 0 ? 'text-[#1F5795]' : 'text-[#7D7D7D]'
                      }`}
                    >
                      {product.change > 0 ? (
                        <>
                          <ArrowUp className="w-4 h-4" />
                          {product.change}
                        </>
                      ) : (
                        <>
                          <ArrowDown className="w-4 h-4" />
                          {Math.abs(product.change)}
                        </>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
