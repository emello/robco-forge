/**
 * Budget Status Card
 * 
 * Requirements: 11.2, 11.3, 13.5, 22.1
 */

'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useBudget } from '@/hooks/use-costs';
import { formatCurrency, calculatePercentage } from '@/lib/utils';
import { cn } from '@/lib/utils';

export function BudgetStatus() {
  const { data: budget, isLoading, error } = useBudget();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Budget Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
            <span className="retro:hidden">Loading budget...</span>
            <span className="hidden retro:inline">[LOADING BUDGET DATA...]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !budget) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Budget Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
            <span className="retro:hidden">No budget configured</span>
            <span className="hidden retro:inline">[NO BUDGET CONFIGURED]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const percentage = calculatePercentage(budget.current_spend, budget.amount);
  const isWarning = percentage >= budget.threshold_warning;
  const isLimit = percentage >= budget.threshold_limit;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{'>>'} Budget Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-baseline mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono retro:uppercase">
                Current Spend
              </span>
              <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
                {formatCurrency(budget.current_spend)}
              </span>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              of {formatCurrency(budget.amount)} budget
            </div>
          </div>

          {/* Progress bar */}
          <div className="relative">
            <div className="h-3 bg-gray-200 dark:bg-gray-700 retro:bg-gray-900 retro:border retro:border-green-500 rounded-full retro:rounded-none overflow-hidden">
              <div
                className={cn(
                  'h-full transition-all duration-500',
                  isLimit
                    ? 'bg-red-600'
                    : isWarning
                    ? 'bg-yellow-500'
                    : 'bg-green-600',
                  'retro:bg-green-500'
                )}
                style={{ width: `${Math.min(percentage, 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              <span>0%</span>
              <span className="font-medium">{percentage}%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Warning messages */}
          {isLimit && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 retro:bg-red-950 border border-red-200 dark:border-red-800 retro:border-red-500 rounded-lg retro:rounded-none">
              <div className="flex items-start gap-2">
                <span className="text-red-600 dark:text-red-400 retro:text-red-500 retro:hidden">⚠️</span>
                <span className="hidden retro:inline text-red-500 font-mono">[!]</span>
                <div className="flex-1 text-sm text-red-800 dark:text-red-300 retro:text-red-400 retro:font-mono">
                  <strong className="retro:uppercase">Budget limit reached!</strong> New workspace provisioning is blocked.
                </div>
              </div>
            </div>
          )}
          {isWarning && !isLimit && (
            <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 retro:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 retro:border-yellow-500 rounded-lg retro:rounded-none">
              <div className="flex items-start gap-2">
                <span className="text-yellow-600 dark:text-yellow-400 retro:text-yellow-500 retro:hidden">⚠️</span>
                <span className="hidden retro:inline text-yellow-500 font-mono">[!]</span>
                <div className="flex-1 text-sm text-yellow-800 dark:text-yellow-300 retro:text-yellow-400 retro:font-mono">
                  <strong className="retro:uppercase">Budget warning!</strong> You've used {percentage}% of your budget.
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
