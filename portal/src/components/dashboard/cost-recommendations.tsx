/**
 * Cost Recommendations Panel
 * 
 * Requirements: 13.5, 22.1
 */

'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useCostRecommendations } from '@/hooks/use-costs';
import { formatCurrency } from '@/lib/utils';

export function CostRecommendations() {
  const { data: recommendations, isLoading, error } = useCostRecommendations();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Cost Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
            <span className="retro:hidden">Loading recommendations...</span>
            <span className="hidden retro:inline">[LOADING RECOMMENDATIONS...]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Cost Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
            <span className="retro:hidden">Failed to load recommendations</span>
            <span className="hidden retro:inline">[ERROR: LOAD FAILED]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Cost Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-4xl mb-2 retro:hidden">✅</div>
            <div className="hidden retro:block text-green-500 text-2xl font-mono mb-2">[OK]</div>
            <div className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              <span className="retro:hidden">No optimization recommendations at this time</span>
              <span className="hidden retro:inline">[NO RECOMMENDATIONS]</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalSavings = recommendations.reduce(
    (sum, rec) => sum + rec.estimated_savings,
    0
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{'>>'} Cost Optimization</CardTitle>
          <div className="text-sm font-medium text-green-600 dark:text-green-400 retro:text-green-500 retro:font-mono">
            <span className="retro:hidden">Potential savings: {formatCurrency(totalSavings)}/mo</span>
            <span className="hidden retro:inline">[SAVE: {formatCurrency(totalSavings)}/mo]</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:hover:bg-green-950 retro:rounded-none transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:uppercase">
                      <span className="retro:hidden">
                        {rec.type === 'right_sizing' ? '📊 Right-sizing' : '💰 Billing Mode'}
                      </span>
                      <span className="hidden retro:inline">
                        {rec.type === 'right_sizing' ? '[RESIZE]' : '[BILLING]'}
                      </span>
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                      {rec.workspace_id.slice(0, 8)}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    {rec.current} → {rec.recommended}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-500 retro:text-green-600 retro:font-mono mt-1">
                    {rec.reason}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-green-600 dark:text-green-400 retro:text-green-500 retro:font-mono retro:retro-glow">
                    {formatCurrency(rec.estimated_savings)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    per month
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
