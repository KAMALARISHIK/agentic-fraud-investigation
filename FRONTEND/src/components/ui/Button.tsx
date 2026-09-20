import React from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    let variantStyles = '';

    if (variant === 'primary') {
      variantStyles =
        'bg-[#D97757] text-white hover:bg-[#C4623F] active:bg-[#B35231] shadow-xs focus:ring-[#D97757]/30 border-transparent';
    } else if (variant === 'secondary') {
      variantStyles =
        'bg-white text-[#141413] border-[#E8E6DC] hover:bg-[#FAF9F5] hover:border-[#D5D3C8] active:bg-[#F0EFEB] shadow-2xs focus:ring-[#141413]/20';
    } else if (variant === 'ghost') {
      variantStyles =
        'bg-transparent text-[#6B6A65] hover:text-[#141413] hover:bg-[#F0EFEB] active:bg-[#E8E6DC] border-transparent';
    } else if (variant === 'danger') {
      variantStyles =
        'bg-[#C0392B] text-white hover:bg-[#A93226] active:bg-[#922B21] shadow-xs focus:ring-[#C0392B]/30 border-transparent';
    } else if (variant === 'outline') {
      variantStyles =
        'bg-transparent text-[#D97757] border-[#D97757] hover:bg-[#F5E6DF] active:bg-[#E8C5B8] focus:ring-[#D97757]/30';
    }

    const sizeStyles = {
      sm: 'text-xs px-2.5 py-1.5 h-8 gap-1.5 rounded-lg',
      md: 'text-sm px-4 py-2 h-10 gap-2 rounded-xl',
      lg: 'text-base px-5 py-2.5 h-12 gap-2.5 rounded-xl font-medium',
      icon: 'p-2 h-10 w-10 justify-center rounded-xl',
    }[size];

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`inline-flex items-center justify-center font-medium border transition-all duration-150 cursor-pointer focus:outline-hidden focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98] ${variantStyles} ${sizeStyles} ${className}`}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children}
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';
