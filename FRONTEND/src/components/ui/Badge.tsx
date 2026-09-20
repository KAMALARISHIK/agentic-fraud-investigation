import React from 'react';

export type BadgeVariant =
  | 'fraud'
  | 'legitimate'
  | 'uncertain'
  | 'auto'
  | 'L1'
  | 'L2'
  | 'neutral'
  | 'outline'
  | 'terracotta';

interface BadgeProps {
  variant?: BadgeVariant | string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  icon?: React.ReactNode;
  style?: React.CSSProperties;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  size = 'md',
  className = '',
  icon,
  style,
}) => {
  const normalizedVariant = (typeof variant === 'string' ? variant.toLowerCase() : 'neutral');

  let styleClasses = 'bg-[#F0EFEB] text-[#6B6A65] border-[#E8E6DC]';

  if (normalizedVariant === 'fraud' || normalizedVariant === 'closed_fraud') {
    styleClasses = 'bg-[#FBEAE7] text-[#C0392B] border-[#F5C7BE]';
  } else if (normalizedVariant === 'legitimate' || normalizedVariant === 'closed_legitimate') {
    styleClasses = 'bg-[#E6F4EA] text-[#2F855A] border-[#C3E6CB]';
  } else if (normalizedVariant === 'uncertain' || normalizedVariant === 'review_needed') {
    styleClasses = 'bg-[#FBF1DC] text-[#B7791F] border-[#F2DCA5]';
  } else if (normalizedVariant === 'auto') {
    styleClasses = 'bg-[#E6F4EA] text-[#2F855A] border-[#C3E6CB]';
  } else if (normalizedVariant === 'l1' || normalizedVariant === 'analyst') {
    styleClasses = 'bg-[#FBF1DC] text-[#B7791F] border-[#F2DCA5]';
  } else if (normalizedVariant === 'l2' || normalizedVariant === 'senior') {
    styleClasses = 'bg-[#FBEAE7] text-[#C0392B] border-[#F5C7BE]';
  } else if (normalizedVariant === 'terracotta') {
    styleClasses = 'bg-[#F5E6DF] text-[#D97757] border-[#E8C5B8]';
  } else if (normalizedVariant === 'outline') {
    styleClasses = 'bg-transparent text-[#6B6A65] border-[#E8E6DC]';
  }

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-medium',
    lg: 'text-sm px-3 py-1.5 font-medium',
  }[size];

  return (
    <span
      style={style}
      className={`inline-flex items-center gap-1.5 rounded-full border tracking-wide transition-colors ${sizeClasses} ${styleClasses} ${className}`}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </span>
  );
};
