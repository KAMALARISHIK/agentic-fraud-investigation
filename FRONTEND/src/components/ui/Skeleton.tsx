import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', variant = 'rect' }) => {
  const variantStyles = {
    text: 'h-4 rounded-md',
    rect: 'rounded-xl',
    circle: 'rounded-full',
  }[variant];

  return (
    <div
      className={`animate-pulse bg-[#E8E6DC]/60 ${variantStyles} ${className}`}
    />
  );
};

export const CardSkeleton: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = '',
}) => {
  return (
    <div className={`bg-white rounded-[14px] border border-[#E8E6DC] p-5 space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <Skeleton className="h-8 w-1/2" />
      <div className="space-y-2 pt-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className={`h-3.5 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} />
        ))}
      </div>
    </div>
  );
};
