import React from 'react';
import { Inbox, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-[14px] border border-dashed border-[#E8E6DC] bg-white/50 ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-[#FAF9F5] border border-[#E8E6DC] flex items-center justify-center text-[#6B6A65] mb-3.5">
        {icon || <Inbox className="w-6 h-6 text-[#6B6A65]" />}
      </div>
      <h4 className="font-serif text-base font-medium text-[#141413] tracking-tight">{title}</h4>
      {description && (
        <p className="text-xs text-[#6B6A65] max-w-sm mt-1 mb-4 leading-relaxed">{description}</p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load data',
  message = 'An error occurred while communicating with the backend API.',
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-[14px] border border-[#F5C7BE] bg-[#FDF6F5] ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-[#FBEAE7] border border-[#F5C7BE] flex items-center justify-center text-[#C0392B] mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h4 className="font-serif text-base font-medium text-[#C0392B]">{title}</h4>
      <p className="text-xs text-[#6B6A65] max-w-md mt-1 mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Retry request
        </Button>
      )}
    </div>
  );
};
