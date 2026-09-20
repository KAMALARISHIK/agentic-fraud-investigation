import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface StatusBannerProps {
  isTigerGraphAsleep: boolean;
  onRefresh?: () => void;
  isChecking?: boolean;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  isTigerGraphAsleep,
  onRefresh,
  isChecking = false,
}) => {
  if (!isTigerGraphAsleep) return null;

  return (
    <div className="bg-[#FBF1DC] border-b border-[#F2DCA5] px-4 py-2.5 text-xs text-[#B7791F] flex items-center justify-between gap-3 sticky top-0 z-40">
      <div className="flex items-center gap-2 max-w-4xl mx-auto flex-1">
        <AlertTriangle className="w-4 h-4 shrink-0 text-[#B7791F]" />
        <span className="font-medium">
          The TigerGraph workspace is asleep. Resume it in Savanna, then retry.
        </span>
      </div>
      {onRefresh && (
        <button
          onClick={onRefresh}
          disabled={isChecking}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-[#F2DCA5] text-[11px] font-medium text-[#B7791F] hover:bg-[#FDFBF2] transition-colors cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3 h-3 ${isChecking ? 'animate-spin' : ''}`} />
          {isChecking ? 'Checking...' : 'Check Connection'}
        </button>
      )}
    </div>
  );
};
