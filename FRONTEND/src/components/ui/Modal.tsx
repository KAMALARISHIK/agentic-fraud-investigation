import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  description?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = 'md',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const widthClass = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-2xl',
  }[maxWidth];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div
        className="fixed inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className={`relative w-full ${widthClass} bg-white rounded-2xl border border-[#E8E6DC] shadow-xl overflow-hidden z-10 flex flex-col`}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-start justify-between p-5 pb-3 border-b border-[#E8E6DC]">
          <div>
            <h3 className="font-serif text-xl font-medium text-[#141413]">{title}</h3>
            {description && <p className="text-xs text-[#6B6A65] mt-1">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#6B6A65] hover:text-[#141413] hover:bg-[#F0EFEB] transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto max-h-[70vh] text-sm text-[#141413]">
          {children}
        </div>

        {footer && (
          <div className="p-4 px-5 bg-[#FAF9F5] border-t border-[#E8E6DC] flex items-center justify-end gap-3 rounded-b-2xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
