/**
 * Stat Card component for displaying key metrics
 * 
 * Requirements: 11.2, 11.3, 22.1
 */

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export function StatCard({ title, value, icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('retro:retro-border retro:bg-black', className)}>
      <CardContent>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mb-2">
              {'>>'} {title.toUpperCase()}
            </p>
            <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
              {value}
            </p>
            {trend && (
              <p
                className={cn(
                  'text-sm mt-2 retro:font-mono',
                  trend.isPositive
                    ? 'text-green-600 dark:text-green-400 retro:text-green-300'
                    : 'text-red-600 dark:text-red-400 retro:text-red-500'
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </p>
            )}
          </div>
          {icon && (
            <div className="text-3xl opacity-50 retro:text-green-500 retro:opacity-70">
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
