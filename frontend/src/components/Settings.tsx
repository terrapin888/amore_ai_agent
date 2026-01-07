/**
 * 설정 페이지 컴포넌트
 * 알림, 리포트, 계정 설정을 관리해요.
 *
 * @module components/Settings
 */

import { useState } from 'react';
import { Bell, FileText, User, Save } from 'lucide-react';

/**
 * 설정 메인 컴포넌트
 *
 * @description
 * - 알림 설정 (랭킹 변동, 일일 리포트)
 * - 리포트 설정 (자동 생성 주기, 이메일 발송)
 * - 계정 정보 조회
 *
 * @returns {JSX.Element} 설정 화면
 *
 * @example
 * <Settings />
 */
export function Settings() {
  const [rankingAlert, setRankingAlert] = useState(true);
  const [dailyReport, setDailyReport] = useState(false);
  const [threshold, setThreshold] = useState('5');
  const [reportFrequency, setReportFrequency] = useState('매주');
  const [emailReport, setEmailReport] = useState(true);
  const [email, setEmail] = useState('admin@laneige.com');

  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl">설정</h1>
      </div>

      {/* Notification Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#1F5795]/10 flex items-center justify-center">
            <Bell className="w-5 h-5 text-[#1F5795]" />
          </div>
          <h2 className="text-xl">알림 설정</h2>
        </div>

        <div className="space-y-6">
          {/* Ranking Alert Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="mb-1">랭킹 변동 알림</p>
              <p className="text-sm text-gray-600">제품 순위가 크게 변동될 때 알림을 받습니다</p>
            </div>
            <button
              onClick={() => setRankingAlert(!rankingAlert)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                rankingAlert ? 'bg-[#1F5795]' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                  rankingAlert ? 'translate-x-7' : ''
                }`}
              />
            </button>
          </div>

          {/* Daily Report Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="mb-1">일일 리포트 알림</p>
              <p className="text-sm text-gray-600">매일 리포트 요약을 받습니다</p>
            </div>
            <button
              onClick={() => setDailyReport(!dailyReport)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                dailyReport ? 'bg-[#1F5795]' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full transition-transform ${
                  dailyReport ? 'translate-x-7' : ''
                }`}
              />
            </button>
          </div>

          {/* Threshold Input */}
          <div>
            <label className="block mb-2">
              알림 임계값
            </label>
            <p className="text-sm text-gray-600 mb-3">순위 변동이 설정한 값 이상일 때만 알림</p>
            <div className="flex items-center gap-3">
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="w-32 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1F5795]"
              />
              <span className="text-gray-600">단계 이상</span>
            </div>
          </div>
        </div>
      </div>

      {/* Report Settings */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#001C58]/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-[#001C58]" />
          </div>
          <h2 className="text-xl">리포트 설정</h2>
        </div>

        <div className="space-y-6">
          {/* Report Frequency */}
          <div>
            <label className="block mb-2">
              자동 생성 주기
            </label>
            <select
              value={reportFrequency}
              onChange={(e) => setReportFrequency(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1F5795]"
            >
              <option>매일</option>
              <option>매주</option>
              <option>매월</option>
            </select>
          </div>

          {/* Email Report Checkbox */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="emailReport"
              checked={emailReport}
              onChange={(e) => setEmailReport(e.target.checked)}
              className="w-5 h-5 accent-[#1F5795]"
            />
            <label htmlFor="emailReport" className="cursor-pointer">
              이메일로 리포트 발송
            </label>
          </div>

          {/* Email Input */}
          {emailReport && (
            <div>
              <label className="block mb-2">
                수신 이메일 주소
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#1F5795]"
                placeholder="email@example.com"
              />
            </div>
          )}
        </div>
      </div>

      {/* Account Information */}
      <div className="bg-white rounded-xl p-6 shadow-sm mb-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#1F5795]/10 flex items-center justify-center">
            <User className="w-5 h-5 text-[#1F5795]" />
          </div>
          <h2 className="text-xl">계정 정보</h2>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">사용자 이름</p>
            <p className="text-lg">관리자</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">이메일</p>
            <p className="text-lg">admin@laneige.com</p>
          </div>

          <div className="flex gap-3 pt-4">
            <button className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
              비밀번호 변경
            </button>
            <button className="px-6 py-2 border border-[#F44336] text-[#F44336] rounded-lg hover:bg-[#F44336]/10 transition-colors">
              로그아웃
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-8 py-3 bg-[#1F5795] text-white rounded-lg hover:bg-[#001C58] transition-colors flex items-center gap-2">
          <Save className="w-5 h-5" />
          저장
        </button>
      </div>
    </div>
  );
}
