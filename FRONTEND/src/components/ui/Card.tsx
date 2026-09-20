import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  hoverEffect = false,
  ...props
}) => {
  return (
    <div
      className={`bg-white rounded-[14px] border border-[#E8E6DC] shadow-[0_1px_3px_rgba(0,0,0,0.02),0_1px_2px_rgba(0,0,0,0.03)] ${
        hoverEffect
          ? 'transition-all duration-200 hover:shadow-[0_4px_12px_rgba(0,0,0,0.05)] hover:border-[#D5D3C8]'
          : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}> = ({ title, subtitle, action, className = '', children }) => {
  if (children) {
    return <div className={`p-5 pb-3 border-b border-[#E8E6DC] ${className}`}>{children}</div>;
  }
  return (
    <div
      className={`p-5 pb-3 border-b border-[#E8E6DC] flex items-center justify-between gap-4 ${className}`}
    >
      <div>
        {title && (
          <h3 className="font-serif text-lg font-medium text-[#141413] tracking-tight">{title}</h3>
        )}
        {subtitle && <p className="text-xs text-[#6B6A65] mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};

export const CardContent: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => {
  return <div className={`p-5 ${className}`}>{children}</div>;
};

export const CardFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => {
  return (
    <div
      className={`p-4 px-5 border-t border-[#E8E6DC] bg-[#FAF9F5]/50 rounded-b-[13px] flex items-center justify-between gap-4 ${className}`}
    >
      {children}
    </div>
  );
};
