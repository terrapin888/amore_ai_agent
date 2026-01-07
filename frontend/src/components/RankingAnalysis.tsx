/**
 * 랭킹 분석 페이지 컴포넌트
 * 제품별 랭킹 추이와 상세 분석을 제공해요.
 *
 * @module components/RankingAnalysis
 */

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Award, Calendar, Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getChartData, getRankingSummary, type ChartDataPoint } from '../services/api';

/**
 * 제품 데이터 인터페이스
 *
 * @interface ProductData
 * @property {string} id 제품 고유 ID
 * @property {string} name 제품명
 * @property {string} category 카테고리
 * @property {number} currentRank 현재 순위
 * @property {number} bestRank 최고 순위
 * @property {number} worstRank 최저 순위
 * @property {number} avgRank 평균 순위
 * @property {number} change30d 30일 변동
 * @property {string} color 차트 색상
 */
interface ProductData {
  id: string;
  name: string;
  category: string;
  currentRank: number;
  bestRank: number;
  worstRank: number;
  avgRank: number;
  change30d: number;
  color: string;
}

/**
 * 제품별 차트 색상 매핑
 * @constant {Record<string, string>}
 */
const PRODUCT_COLORS: Record<string, string> = {
  'Lip_Sleeping_Mask': '#1F5795',
  'Water_Sleeping_Mask': '#001C58',
  'Cream_Skin_Refiner': '#7D7D7D',
  'Neo_Cushion_Matte': '#1F5795',
  'Radian-C_Cream': '#001C58',
  'Water_Bank_Blue_Hyaluronic_Cream': '#7D7D7D',
  'Lip_Glowy_Balm': '#1F5795',
  'Bouncy_&_Firm_Sleeping_Mask': '#001C58',
  'Water_Bank_Hydro_Essence': '#7D7D7D',
  'Lip_Sleeping_Mask_Vanilla': '#1F5795',
};

/**
 * 랭킹 분석 메인 컴포넌트
 *
 * @description
 * - TOP 10 진입, 순위 상승/하락 요약 카드
 * - 제품별 랭킹 추이 라인 차트
 * - 정렬 및 필터 가능한 상세 테이블
 *
 * @returns {JSX.Element} 랭킹 분석 화면
 *
 * @example
 * <RankingAnalysis />
 */
export function RankingAnalysis() {
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [sortConfig, setSortConfig] = useState<{ key: keyof ProductData; direction: 'asc' | 'desc' } | null>(null);
  const [selectedRow, setSelectedRow] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [productsData, setProductsData] = useState<ProductData[]>([]);
  const [summaryStats, setSummaryStats] = useState({ top10: 0, up: 0, down: 0 });

  useEffect(() => {
    loadData();
  }, []);

  /**
   * 차트 및 제품 랭킹 데이터를 불러와요.
   *
   * @returns {Promise<void>}
   */
  async function loadData() {
    try {
      setLoading(true);

      const [chartResult, summaryResult] = await Promise.all([
        getChartData(30),
        getRankingSummary()
      ]);

      const formattedChartData: ChartDataPoint[] = chartResult.map((item, index) => ({
        ...item,
        date: `Day ${index + 1}`,
      }));
      setChartData(formattedChartData);

      const products: ProductData[] = [];
      let top10Count = 0;
      let upCount = 0;
      let downCount = 0;

      for (const [category, summary] of Object.entries(summaryResult)) {
        for (const [productName, data] of Object.entries(summary)) {
          const productKey = productName.replace(/ /g, '_');
          const change = Math.round((data.worst_rank - data.best_rank));

          products.push({
            id: productKey,
            name: productName,
            category: category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
            currentRank: data.best_rank,
            bestRank: data.best_rank,
            worstRank: data.worst_rank,
            avgRank: data.avg_rank,
            change30d: change,
            color: PRODUCT_COLORS[productKey] || '#666666'
          });

          if (data.avg_rank <= 10) top10Count++;
          if (change > 0) upCount++;
          if (change < 0) downCount++;
        }
      }

      setProductsData(products);
      setSummaryStats({ top10: top10Count, up: upCount, down: downCount });

      if (products.length > 0) {
        setSelectedProducts(products.slice(0, 3).map(p => p.id));
      }

    } catch (err) {
      console.error('Failed to load ranking data:', err);
    } finally {
      setLoading(false);
    }
  }

  /**
   * 차트에 표시할 제품을 토글해요.
   *
   * @param {string} productId 제품 ID
   */
  const toggleProduct = (productId: string) => {
    setSelectedProducts((prev) =>
      prev.includes(productId) ? prev.filter((id) => id !== productId) : [...prev, productId]
    );
  };

  /**
   * 테이블 정렬을 처리해요.
   *
   * @param {keyof ProductData} key 정렬 기준 컬럼
   */
  const handleSort = (key: keyof ProductData) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const sortedProducts = [...productsData].sort((a, b) => {
    if (!sortConfig) return 0;
    const aVal = a[sortConfig.key];
    const bVal = b[sortConfig.key];
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const filteredProducts =
    selectedCategory === '전체'
      ? sortedProducts
      : sortedProducts.filter((p) => p.category.toLowerCase().includes(selectedCategory.toLowerCase()));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#1F5795]" />
        <span className="ml-2">랭킹 데이터 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl">랭킹 분석</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm">
            <Calendar className="w-4 h-4 text-gray-600" />
            <input
              type="date"
              defaultValue="2025-12-04"
              className="border-none outline-none text-sm"
            />
            <span className="text-gray-400">~</span>
            <input
              type="date"
              defaultValue="2026-01-04"
              className="border-none outline-none text-sm"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 bg-white rounded-lg shadow-sm border-none outline-none"
          >
            <option>전체</option>
            <option>Lip Care</option>
            <option>Skincare</option>
            <option>Makeup</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-2">TOP 10 진입</p>
              <p className="text-3xl">{summaryStats.top10}개</p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-[#1F5795]/10 flex items-center justify-center">
              <Award className="w-6 h-6 text-[#1F5795]" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-2">순위 상승</p>
              <p className="text-3xl">{summaryStats.up}개</p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-[#1F5795]/10 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[#1F5795]" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-gray-600 text-sm mb-2">순위 하락</p>
              <p className="text-3xl">{summaryStats.down}개</p>
            </div>
            <div className="w-12 h-12 rounded-lg bg-[#7D7D7D]/10 flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-[#7D7D7D]" />
            </div>
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl">제품별 랭킹 추이</h2>
          <div className="flex gap-4 flex-wrap">
            {productsData.slice(0, 5).map((product) => (
              <label key={product.id} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedProducts.includes(product.id)}
                  onChange={() => toggleProduct(product.id)}
                  className="w-4 h-4 accent-[#1F5795]"
                />
                <span className="text-sm" style={{ color: product.color }}>
                  {product.name}
                </span>
              </label>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" stroke="#666" />
            <YAxis reversed domain={[0, 20]} stroke="#666" />
            <Tooltip />
            <Legend />
            {productsData.filter(p => selectedProducts.includes(p.id)).map((product) => (
              <Line
                key={product.id}
                type="monotone"
                dataKey={product.id}
                stroke={product.color}
                strokeWidth={2}
                name={product.name}
                dot={{ fill: product.color }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-6 border-b">
          <h2 className="text-xl">상세 랭킹 테이블</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th
                  onClick={() => handleSort('name')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  제품명 {sortConfig?.key === 'name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('category')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  카테고리 {sortConfig?.key === 'category' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('currentRank')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  현재순위 {sortConfig?.key === 'currentRank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('bestRank')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  최고순위 {sortConfig?.key === 'bestRank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('worstRank')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  최저순위 {sortConfig?.key === 'worstRank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('avgRank')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  평균순위 {sortConfig?.key === 'avgRank' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th
                  onClick={() => handleSort('change30d')}
                  className="px-6 py-4 text-left text-sm text-gray-600 cursor-pointer hover:bg-gray-100"
                >
                  30일 변동 {sortConfig?.key === 'change30d' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map((product) => (
                <tr
                  key={product.id}
                  onClick={() => setSelectedRow(product.id)}
                  className={`border-t cursor-pointer transition-colors ${
                    selectedRow === product.id
                      ? 'bg-blue-50'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <td className="px-6 py-4">{product.name}</td>
                  <td className="px-6 py-4 text-gray-600">{product.category}</td>
                  <td className="px-6 py-4">{product.currentRank}위</td>
                  <td className="px-6 py-4 text-[#1F5795]">{product.bestRank}위</td>
                  <td className="px-6 py-4 text-[#7D7D7D]">{product.worstRank}위</td>
                  <td className="px-6 py-4 text-gray-600">{product.avgRank}위</td>
                  <td className="px-6 py-4">
                    <span
                      className={`flex items-center gap-1 ${
                        product.change30d > 0 ? 'text-[#1F5795]' : 'text-[#7D7D7D]'
                      }`}
                    >
                      {product.change30d > 0 ? (
                        <>
                          <TrendingUp className="w-4 h-4" />
                          {product.change30d}
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4" />
                          {Math.abs(product.change30d)}
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
