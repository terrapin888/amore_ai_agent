/**
 * 사이드바 네비게이션 컴포넌트
 * 앱의 주요 네비게이션을 담당해요.
 *
 * @module components/Sidebar
 */

import { LayoutDashboard, TrendingUp, MessageSquare, FileText, Settings, User, Lightbulb } from 'lucide-react';

/**
 * Sidebar 컴포넌트 Props
 *
 * @interface SidebarProps
 * @property {string} activeTab 현재 활성화된 탭 ID
 * @property {(tab: string) => void} onTabChange 탭 변경 콜백
 */
interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

/**
 * 사이드바 컴포넌트
 *
 * @param {SidebarProps} props 컴포넌트 props
 * @returns {JSX.Element} 사이드바 네비게이션
 *
 * @example
 * <Sidebar activeTab="dashboard" onTabChange={setActiveTab} />
 */
export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: '대시보드' },
    { id: 'insights', icon: Lightbulb, label: '인사이트' },
    { id: 'ranking', icon: TrendingUp, label: '랭킹 분석' },
    { id: 'chat', icon: MessageSquare, label: 'AI 채팅' },
    { id: 'reports', icon: FileText, label: '리포트' },
    { id: 'settings', icon: Settings, label: '설정' },
  ];

  return (
    <div className="w-60 bg-[#001C58] flex flex-col h-full">
      {/* Logo */}
      <div className="p-6">
        <h1 className="text-white text-xl">LANEIGE Insight</h1>
      </div>

      {/* Menu Items */}
      <nav className="flex-1 px-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-white/70 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-white text-sm">관리자</p>
            <p className="text-white/50 text-xs">admin@laneige.com</p>
          </div>
        </div>
      </div>
    </div>
  );
}
