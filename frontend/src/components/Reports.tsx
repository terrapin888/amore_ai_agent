/**
 * 리포트 페이지 컴포넌트
 * 엑셀 리포트 생성 및 다운로드를 관리해요.
 *
 * @module components/Reports
 */

import { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, Eye, Plus, Loader2, RefreshCw } from 'lucide-react';
import { getReports, generateReport, getReportDownloadUrl, type Report } from '../services/api';

/**
 * 리포트 메인 컴포넌트
 *
 * @description
 * - 생성된 리포트 목록 조회
 * - 새 리포트 생성
 * - 리포트 다운로드
 *
 * @returns {JSX.Element} 리포트 화면
 *
 * @example
 * <Reports />
 */
export function Reports() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  /**
   * 리포트 목록을 불러와요.
   *
   * @returns {Promise<void>}
   */
  async function loadReports() {
    try {
      setLoading(true);
      setError(null);
      const data = await getReports();
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
      setError('리포트 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  }

  /**
   * 새 리포트를 생성해요.
   *
   * @returns {Promise<void>}
   */
  async function handleGenerateReport() {
    try {
      setGenerating(true);
      await generateReport(30);
      await loadReports();
    } catch (err) {
      console.error('Failed to generate report:', err);
      alert('리포트 생성에 실패했습니다.');
    } finally {
      setGenerating(false);
    }
  }

  /**
   * 리포트를 다운로드해요.
   *
   * @param {string} filename 다운로드할 파일명
   */
  function handleDownload(filename: string) {
    const url = getReportDownloadUrl(filename);
    window.open(url, '_blank');
  }

  /**
   * 타임스탬프를 한국어 날짜 문자열로 변환해요.
   *
   * @param {number} timestamp Unix 타임스탬프 (초)
   * @returns {string} 포맷된 날짜 문자열
   */
  function formatDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }) + ' 생성';
  }

  /**
   * 바이트를 읽기 쉬운 크기 문자열로 변환해요.
   *
   * @param {number} bytes 파일 크기 (바이트)
   * @returns {string} 포맷된 파일 크기 (B, KB, MB)
   */
  function formatSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-[#1F5795]" />
        <span className="ml-2">리포트 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl">엑셀 리포트</h1>
        <div className="flex gap-3">
          <button
            onClick={loadReports}
            className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-5 h-5" />
            새로고침
          </button>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-6 py-3 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Plus className="w-5 h-5" />
            )}
            새 리포트 생성
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg">
          {error}
        </div>
      )}

      {reports.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-xl shadow-sm">
          <FileSpreadsheet className="w-16 h-16 text-gray-300 mb-4" />
          <p className="text-gray-500 mb-4">생성된 리포트가 없습니다.</p>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-6 py-3 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {generating ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Plus className="w-5 h-5" />
            )}
            첫 리포트 생성하기
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-6">
          {reports.map((report, index) => (
            <div key={index} className="bg-white rounded-xl p-6 shadow-sm">
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="w-12 h-12 rounded-lg bg-[#1F5795]/10 flex items-center justify-center flex-shrink-0">
                  <FileSpreadsheet className="w-6 h-6 text-[#1F5795]" />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <h3 className="text-lg mb-2">{report.filename}</h3>
                  <p className="text-sm text-gray-600 mb-1">30일 랭킹 히스토리 리포트</p>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>{formatDate(report.created_at)}</span>
                    <span>|</span>
                    <span>{formatSize(report.size)}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 mt-4">
                    <button
                      onClick={() => handleDownload(report.filename)}
                      className="flex items-center gap-2 px-4 py-2 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      다운로드
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                      <Eye className="w-4 h-4" />
                      미리보기
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
