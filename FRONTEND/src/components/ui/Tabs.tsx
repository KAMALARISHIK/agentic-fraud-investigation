import React from 'react';

export interface TabItem {
  id: string;
  label: string;
  badge?: React.ReactNode;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
  variant?: 'underline' | 'pills';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className = '',
  variant = 'underline',
}) => {
  if (variant === 'pills') {
    return (
      <div className={`flex flex-wrap items-center gap-1.5 p-1 bg-[#F0EFEB] rounded-xl border border-[#E8E6DC] ${className}`}>
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg transition-all cursor-pointer ${
                isActive
                  ? 'bg-white text-[#141413] shadow-xs font-semibold'
                  : 'text-[#6B6A65] hover:text-[#141413] hover:bg-white/60'
              }`}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.badge}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className={`border-b border-[#E8E6DC] ${className}`}>
      <nav className="flex space-x-6 overflow-x-auto no-scrollbar" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium whitespace-nowrap transition-colors cursor-pointer ${
                isActive
                  ? 'border-[#D97757] text-[#D97757]'
                  : 'border-transparent text-[#6B6A65] hover:text-[#141413] hover:border-[#D5D3C8]'
              }`}
            >
              {tab.icon && <span className="shrink-0">{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.badge}
            </button>
          );
        })}
      </nav>
    </div>
  );
};
