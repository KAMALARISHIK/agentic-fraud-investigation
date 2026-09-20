import React from 'react';

interface LogoProps {
  size?: number;
  className?: string;
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ size = 28, className = '', showText = false }) => {
  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0 transition-transform duration-200 hover:scale-105"
      >
        {/* Editorial Terracotta Shield Mark with Intersecting Graph Node Star */}
        <path
          d="M16 3L6 7V14.5C6 21.2 10.3 27.4 16 29C21.7 27.4 26 21.2 26 14.5V7L16 3Z"
          fill="#D97757"
        />
        <path
          d="M16 8V24M8 16H24M10.5 10.5L21.5 21.5M21.5 10.5L10.5 21.5"
          stroke="#FAF9F5"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <circle cx="16" cy="16" r="3.2" fill="#FAF9F5" />
        <circle cx="16" cy="16" r="1.6" fill="#D97757" />
      </svg>
      {showText && (
        <div className="flex flex-col">
          <span className="font-serif text-lg font-semibold tracking-tight text-[#141413] leading-none">
            FraudSight <span className="text-[#D97757] font-normal text-sm ml-0.5">Agent</span>
          </span>
          <span className="text-[10px] tracking-wider uppercase text-[#6B6A65] font-medium mt-0.5">
            Graph-Powered Investigation
          </span>
        </div>
      )}
    </div>
  );
};
