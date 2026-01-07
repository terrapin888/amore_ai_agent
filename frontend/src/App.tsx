/**
 * 메인 애플리케이션 컴포넌트
 * 사이드바 네비게이션과 탭 기반 페이지 라우팅을 관리해요.
 *
 * @module App
 */

import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { Insights } from './components/Insights';
import { RankingAnalysis } from './components/RankingAnalysis';
import { AIChat } from './components/AIChat';
import { Reports } from './components/Reports';
import { Settings } from './components/Settings';

/**
 * 애플리케이션 루트 컴포넌트
 * 사이드바와 메인 콘텐츠 영역으로 구성되어 있어요.
 *
 * @returns {JSX.Element} 앱 루트 엘리먼트
 *
 * @example
 * <App />
 */
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen bg-[#F8F9FA]">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-auto">
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'insights' && <Insights />}
        {activeTab === 'ranking' && <RankingAnalysis />}
        {activeTab === 'chat' && <AIChat />}
        {activeTab === 'reports' && <Reports />}
        {activeTab === 'settings' && <Settings />}
      </main>
    </div>
  );
}
