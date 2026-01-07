/**
 * 통계 카드 컴포넌트
 * 대시보드에서 사용되는 통계 요약 카드예요.
 *
 * @module components/StatCard
 */

import { LucideIcon } from 'lucide-react';

/**
 * StatCard 컴포넌트 Props
 *
 * @interface StatCardProps
 * @property {string} title 카드 제목
 * @property {string} value 표시할 값
 * @property {LucideIcon} icon 아이콘 컴포넌트
 */
interface StatCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
}

/**
 * 통계 카드 컴포넌트
 *
 * @param {StatCardProps} props 컴포넌트 props
 * @returns {JSX.Element} 통계 카드
 *
 * @example
 * <StatCard title="전체 제품" value="150개" icon={Package} />
 */
export function StatCard({ title, value, icon: Icon }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-600 text-sm mb-2">{title}</p>
          <p className="text-3xl">{value}</p>
        </div>
        <div className="w-12 h-12 rounded-lg bg-[#E4007F]/10 flex items-center justify-center">
          <Icon className="w-6 h-6 text-[#E4007F]" />
        </div>
      </div>
    </div>
  );
}
