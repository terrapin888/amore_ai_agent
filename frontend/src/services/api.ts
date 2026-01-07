/**
 * API Service for Laneige Ranking Insight Agent
 * 백엔드 API와 통신하는 서비스 레이어
 *
 * @module services/api
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

/** 제품 정보 */
export interface Product {
  product_id: number;
  product_name: string;
  brand: string;
  category: string;
  amazon_category: string;
  price: number;
  rating: number;
  ingredients?: string;
  skin_type?: string;
  features?: string;
  is_laneige: boolean;
}

/** 랭킹 요약 데이터 */
export interface RankingSummary {
  [productName: string]: {
    avg_rank: number;
    best_rank: number;
    worst_rank: number;
    top5_days: number;
  };
}

/** 차트 데이터 포인트 */
export interface ChartDataPoint {
  date: string;
  [productName: string]: string | number;
}

/** 대시보드 통계 */
export interface Stats {
  total_products: number;
  laneige_products: number;
  top5_products: number;
  average_rank: number;
}

/** 리포트 정보 */
export interface Report {
  filename: string;
  filepath: string;
  created_at: number;
  size: number;
}

/** AI 채팅 응답 */
export interface ChatResponse {
  response: string;
  context_used?: string[];
}

/** 성과 인사이트 카드 */
export interface PerformanceCard {
  type: string;
  title: string;
  description: string;
  metric: string;
  color: string;
}

/** 마케팅 인사이트 카드 */
export interface MarketingCard {
  type: string;
  title: string;
  description: string;
  details: { category?: string; avgRank?: string; status?: string; product?: string; potential?: string; current?: string }[];
  recommendations?: string[];
  color: string;
}

/** 성과 차트 데이터 */
export interface PerformanceChartData {
  week: string;
  avgRank: number;
  top5Rate: number;
}

/** 카테고리 트렌드 데이터 */
export interface CategoryTrendData {
  category: string;
  growth: number;
  color: string;
}

/** 인사이트 전체 데이터 */
export interface InsightData {
  performanceCards: PerformanceCard[];
  marketingCards: MarketingCard[];
  performanceChart: PerformanceChartData[];
  categoryTrend: CategoryTrendData[];
  lastUpdated: string;
}

/** 랭킹 아이템 (일별 순위 포함) */
export interface RankingItem {
  product_id: number;
  product_name: string;
  brand: string;
  category: string;
  amazon_category: string;
  price: number;
  is_laneige: boolean;
  [key: `day_${number}`]: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * 서버 상태를 확인해요.
 *
 * @returns {Promise<{status: string, initialized: boolean}>} 서버 상태 및 초기화 여부
 *
 * @example
 * const health = await checkHealth();
 * console.log(health.status); // 'ok'
 */
export async function checkHealth(): Promise<{ status: string; initialized: boolean }> {
  const response = await fetch(`${API_BASE_URL}/`);
  return response.json();
}

/**
 * 대시보드 통계를 조회해요.
 *
 * @returns {Promise<Stats>} 전체 제품 수, 라네즈 제품 수, TOP 5 제품 수, 평균 순위
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const stats = await getStats();
 * console.log(stats.total_products); // 150
 */
export async function getStats(): Promise<Stats> {
  const response = await fetch(`${API_BASE_URL}/api/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

/**
 * 제품 목록을 조회해요.
 *
 * @param {Object} options 필터 옵션
 * @param {string} options.category 카테고리 필터
 * @param {boolean} options.laneigeOnly 라네즈 제품만 조회
 * @param {number} options.limit 결과 개수 제한
 * @returns {Promise<Product[]>} 제품 목록
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const products = await getProducts({ category: 'lip_care', laneigeOnly: true });
 */
export async function getProducts(options?: {
  category?: string;
  laneigeOnly?: boolean;
  limit?: number;
}): Promise<Product[]> {
  const params = new URLSearchParams();
  if (options?.category) params.append('category', options.category);
  if (options?.laneigeOnly) params.append('laneige_only', 'true');
  if (options?.limit) params.append('limit', options.limit.toString());

  const response = await fetch(`${API_BASE_URL}/api/products?${params}`);
  if (!response.ok) throw new Error('Failed to fetch products');
  return response.json();
}

/**
 * 라네즈 제품만 조회해요.
 *
 * @returns {Promise<Product[]>} 라네즈 제품 목록
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const laneigeProducts = await getLaneigeProducts();
 */
export async function getLaneigeProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE_URL}/api/products/laneige`);
  if (!response.ok) throw new Error('Failed to fetch Laneige products');
  return response.json();
}

/**
 * 랭킹 데이터를 조회해요.
 *
 * @param {string} category 카테고리 (기본값: 'all')
 * @param {number} days 조회 기간 (기본값: 30)
 * @returns {Promise<Record<string, RankingItem[]>>} 카테고리별 랭킹 데이터
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const rankings = await getRankings('lip_care', 14);
 */
export async function getRankings(category: string = 'all', days: number = 30): Promise<Record<string, RankingItem[]>> {
  const params = new URLSearchParams({
    category,
    days: days.toString()
  });

  const response = await fetch(`${API_BASE_URL}/api/rankings?${params}`);
  if (!response.ok) throw new Error('Failed to fetch rankings');
  return response.json();
}

/**
 * 랭킹 요약을 조회해요.
 *
 * @returns {Promise<Record<string, RankingSummary>>} 카테고리별 제품 랭킹 요약 (평균, 최고, 최저 순위)
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const summary = await getRankingSummary();
 * console.log(summary['lip_care']['Lip Sleeping Mask'].avg_rank);
 */
export async function getRankingSummary(): Promise<Record<string, RankingSummary>> {
  const response = await fetch(`${API_BASE_URL}/api/rankings/summary`);
  if (!response.ok) throw new Error('Failed to fetch ranking summary');
  return response.json();
}

/**
 * 차트용 랭킹 데이터를 조회해요.
 *
 * @param {number} days 조회 기간 (기본값: 30)
 * @returns {Promise<ChartDataPoint[]>} 차트 렌더링용 데이터 포인트 배열
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const chartData = await getChartData(30);
 */
export async function getChartData(days: number = 30): Promise<ChartDataPoint[]> {
  const response = await fetch(`${API_BASE_URL}/api/rankings/chart-data?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch chart data');
  return response.json();
}

/**
 * AI 채팅 메시지를 전송해요.
 *
 * @param {string} message 사용자 메시지
 * @returns {Promise<ChatResponse>} AI 응답 및 사용된 컨텍스트
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const response = await sendChatMessage('립 슬리핑 마스크 순위가 왜 높아?');
 * console.log(response.response);
 */
export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) throw new Error('Failed to send chat message');
  return response.json();
}

/**
 * 리포트 목록을 조회해요.
 *
 * @returns {Promise<Report[]>} 생성된 리포트 목록
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const reports = await getReports();
 */
export async function getReports(): Promise<Report[]> {
  const response = await fetch(`${API_BASE_URL}/api/reports`);
  if (!response.ok) throw new Error('Failed to fetch reports');
  return response.json();
}

/**
 * 새 리포트를 생성해요.
 *
 * @param {number} days 리포트에 포함할 기간 (기본값: 30)
 * @returns {Promise<{success: boolean, filepath: string, filename: string}>} 생성 결과 및 파일 정보
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const result = await generateReport(30);
 * console.log(result.filename); // 'ranking_report_20240108.xlsx'
 */
export async function generateReport(days: number = 30): Promise<{ success: boolean; filepath: string; filename: string }> {
  const response = await fetch(`${API_BASE_URL}/api/reports/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ days }),
  });

  if (!response.ok) throw new Error('Failed to generate report');
  return response.json();
}

/**
 * 리포트 다운로드 URL을 생성해요.
 *
 * @param {string} filename 다운로드할 파일명
 * @returns {string} 다운로드 URL
 *
 * @example
 * const url = getReportDownloadUrl('ranking_report_20240108.xlsx');
 * window.open(url, '_blank');
 */
export function getReportDownloadUrl(filename: string): string {
  return `${API_BASE_URL}/api/reports/download/${filename}`;
}

/**
 * Vector DB를 동기화해요.
 *
 * @returns {Promise<{success: boolean, updated_count: number, message: string}>} 동기화 결과 및 업데이트 개수
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const result = await syncVectorDB();
 * console.log(result.message); // '동기화 완료'
 */
export async function syncVectorDB(): Promise<{ success: boolean; updated_count: number; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/vectordb/sync`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) throw new Error('Failed to sync Vector DB');
  return response.json();
}

/**
 * 인사이트를 조회해요.
 *
 * @returns {Promise<InsightData>} 성과 및 마케팅 인사이트 데이터
 * @throws {Error} 서버 응답 실패 시
 *
 * @example
 * const insights = await getInsights();
 * console.log(insights.performanceCards);
 */
export async function getInsights(): Promise<InsightData> {
  const response = await fetch(`${API_BASE_URL}/api/insights`);
  if (!response.ok) throw new Error('Failed to fetch insights');
  return response.json();
}
