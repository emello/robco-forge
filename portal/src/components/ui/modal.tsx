/**
 * Modal/Dialog component
 * 
 * Requirements: 22.1
 */

'use client';

import { useEffect } from 'react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export function Modal({ isOpen, onClose, title, children, size = 'md' }: ModalProps) {
  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 retro:bg-opacity-80"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={cn(
          'relative w-full bg-white dark:bg-gray-900 rounded-lg shadow-xl',
          'retro:bg-black retro:border-2 retro:border-green-500 retro:shadow-[0_0_20px_rgba(0,255,0,0.5)] retro:rounded-none',
          sizeClasses[size]
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700 retro:border-green-500">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:uppercase retro:retro-glow">
            {'>>'} {title}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 retro:text-green-500 retro:hover:text-green-300 retro:font-mono text-2xl"
          >
            <span className="retro:hidden">×</span>
            <span className="hidden retro:inline">[X]</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto retro:font-mono">
          {children}
        </div>
      </div>
    </div>
  );
}
