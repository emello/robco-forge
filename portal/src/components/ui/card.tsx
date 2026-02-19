/**
 * Reusable Card component
 * 
 * Requirements: 22.1
 */

import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-white dark:bg-gray-900 p-6 shadow-sm',
        'retro:bg-black retro:border-green-500 retro:shadow-[0_0_10px_rgba(0,255,0,0.3)] retro:rounded-none',
        className
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return (
    <div className={cn('mb-4 retro:border-b retro:border-green-500 retro:pb-2', className)}>
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function CardTitle({ children, className }: CardTitleProps) {
  return (
    <h3
      className={cn(
        'text-lg font-semibold text-gray-900 dark:text-gray-100',
        'retro:text-green-500 retro:font-mono retro:uppercase retro:text-base retro:tracking-wider',
        className
      )}
    >
      {children}
    </h3>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn('retro:font-mono', className)}>{children}</div>;
}
