'use client';

/**
 * Cost Dashboard Page
 * 
 * Requirements: 11.2, 11.3, 11.5
 */

import { useState } from 'react';
import { useCostSummary, useCostRecommendations, useBudget } from '@/hooks/use-costs';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';

type TimePeriod = 'daily' | 'weekly' | 'monthly' | 'custom';

export default function CostsPage() {
  const [timePeriod, setTimePeriod] = useState<TimePeriod>('monthly');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Calculate date range based on period
  const getDateRange = () => {
    const end = new Date();
    const start = new Date();
    
    if (timePeriod === 'daily') {
      start.setDate(end.getDate() - 1);
    } else if (timePeriod === 'weekly') {
      start.setDate(end.getDate() - 7);
    } else if (timePeriod === 'monthly') {
      start.setMonth(end.getMonth() - 1);
    } else if (timePeriod === 'custom' && startDate && endDate) {
      return { start: startDate, end: endDate };
    }
    
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    };
  };

  const dateRange = getDateRange();
  const { data: costSummary, isLoading, error } = useCostSummary({
    start_date: dateRange.start,
    end_date: dateRange.end,
  });
  const { data: recommendations, isLoading: isLoadingRecs } = useCostRecommendations();
  const { data: budget, isLoading: isLoadingBudget } = useBudget();

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
          {'>>'} COST DASHBOARD
        </h1>
        <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mt-2">
          Track and analyze workspace spending
        </p>
      </div>

      {/* Time Period Selector */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
                <span className="retro:hidden">Time Period</span>
                <span className="hidden retro:inline">[TIME PERIOD]</span>
              </label>
              <div className="flex gap-2">
                {(['daily', 'weekly', 'monthly', 'custom'] as TimePeriod[]).map((period) => (
                  <button
                    key={period}
                    onClick={() => setTimePeriod(period)}
                    className={`px-4 py-2 rounded-lg transition-colors retro:rounded-none retro:font-mono ${
                      timePeriod === period
                        ? 'bg-blue-600 text-white retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600 retro:bg-black retro:border retro:border-green-700 retro:text-green-500 retro:hover:border-green-500'
                    }`}
                  >
                    {period.charAt(0).toUpperCase() + period.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {timePeriod === 'custom' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
                    <span className="retro:hidden">Start Date</span>
                    <span className="hidden retro:inline">[START]</span>
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
                    <span className="retro:hidden">End Date</span>
                    <span className="hidden retro:inline">[END]</span>
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                  />
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              <span className="retro:hidden">Loading cost data...</span>
              <span className="hidden retro:inline">[LOADING COST DATA...]</span>
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
              <span className="retro:hidden">Failed to load cost data</span>
              <span className="hidden retro:inline">[ERROR: LOAD FAILED]</span>
            </div>
          </CardContent>
        </Card>
      ) : costSummary ? (
        <div className="space-y-6">
          {/* Budget Status */}
          {!isLoadingBudget && budget && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <span className="retro:hidden">💰 Budget Status</span>
                  <span className="hidden retro:inline">[BUDGET STATUS]</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Current Spend</span>
                      <span className="hidden retro:inline">[CURRENT SPEND]</span>
                    </span>
                    <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                      {formatCurrency(budget.current_spend)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Budget Limit</span>
                      <span className="hidden retro:inline">[BUDGET LIMIT]</span>
                    </span>
                    <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                      {formatCurrency(budget.amount)}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-2">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 retro:bg-black retro:border retro:border-green-700 retro:rounded-none">
                      <div
                        className={`h-4 rounded-full transition-all retro:rounded-none ${
                          budget.current_spend >= budget.amount
                            ? 'bg-red-600 retro:bg-red-600'
                            : budget.current_spend >= budget.amount * 0.8
                            ? 'bg-yellow-600 retro:bg-yellow-600'
                            : 'bg-green-600 retro:bg-green-600'
                        }`}
                        style={{ width: `${Math.min((budget.current_spend / budget.amount) * 100, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                        {((budget.current_spend / budget.amount) * 100).toFixed(1)}% used
                      </span>
                      <span className="text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                        {formatCurrency(budget.amount - budget.current_spend)} remaining
                      </span>
                    </div>
                  </div>

                  {/* Warning at 80% */}
                  {budget.current_spend >= budget.amount * 0.8 && budget.current_spend < budget.amount && (
                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded retro:bg-black retro:border-yellow-500 retro:rounded-none">
                      <div className="flex items-start gap-2">
                        <span className="text-yellow-600 dark:text-yellow-400 retro:text-yellow-500 text-xl retro:hidden">⚠️</span>
                        <span className="hidden retro:inline text-yellow-500 font-mono">[!]</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200 retro:text-yellow-500 retro:font-mono">
                            <span className="retro:hidden">Budget Warning</span>
                            <span className="hidden retro:inline">[WARNING: BUDGET THRESHOLD]</span>
                          </p>
                          <p className="text-sm text-yellow-700 dark:text-yellow-300 retro:text-yellow-400 retro:font-mono mt-1">
                            <span className="retro:hidden">
                              You've used {((budget.current_spend / budget.amount) * 100).toFixed(1)}% of your budget. Consider reviewing your workspace usage.
                            </span>
                            <span className="hidden retro:inline">
                              {((budget.current_spend / budget.amount) * 100).toFixed(1)}% BUDGET USED. REVIEW USAGE.
                            </span>
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Block at 100% */}
                  {budget.current_spend >= budget.amount && (
                    <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded retro:bg-black retro:border-red-500 retro:rounded-none">
                      <div className="flex items-start gap-2">
                        <span className="text-red-600 dark:text-red-400 retro:text-red-500 text-xl retro:hidden">🚫</span>
                        <span className="hidden retro:inline text-red-500 font-mono">[X]</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-red-800 dark:text-red-200 retro:text-red-500 retro:font-mono">
                            <span className="retro:hidden">Budget Exceeded</span>
                            <span className="hidden retro:inline">[ERROR: BUDGET EXCEEDED]</span>
                          </p>
                          <p className="text-sm text-red-700 dark:text-red-300 retro:text-red-400 retro:font-mono mt-1">
                            <span className="retro:hidden">
                              You've reached your budget limit. New workspace provisioning is blocked until next period or budget increase.
                            </span>
                            <span className="hidden retro:inline">
                              BUDGET LIMIT REACHED. PROVISIONING BLOCKED.
                            </span>
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cost Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    <span className="retro:hidden">Total Cost</span>
                    <span className="hidden retro:inline">[TOTAL COST]</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {formatCurrency(costSummary.total_cost)}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    <span className="retro:hidden">Compute</span>
                    <span className="hidden retro:inline">[COMPUTE]</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {formatCurrency(costSummary.compute_cost)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    {((costSummary.compute_cost / costSummary.total_cost) * 100).toFixed(1)}% of total
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    <span className="retro:hidden">Storage</span>
                    <span className="hidden retro:inline">[STORAGE]</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {formatCurrency(costSummary.storage_cost)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    {((costSummary.storage_cost / costSummary.total_cost) * 100).toFixed(1)}% of total
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    <span className="retro:hidden">Data Transfer</span>
                    <span className="hidden retro:inline">[DATA TRANSFER]</span>
                  </div>
                  <div className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    {formatCurrency(costSummary.data_transfer_cost)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    {((costSummary.data_transfer_cost / costSummary.total_cost) * 100).toFixed(1)}% of total
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cost Breakdown by Bundle Type */}
          {costSummary.breakdown_by_bundle && Object.keys(costSummary.breakdown_by_bundle).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <span className="retro:hidden">Cost by Bundle Type</span>
                  <span className="hidden retro:inline">[COST BY BUNDLE TYPE]</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(costSummary.breakdown_by_bundle)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([bundle, cost]) => {
                      const percentage = ((cost as number) / costSummary.total_cost) * 100;
                      return (
                        <div key={bundle} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                              {bundle}
                            </span>
                            <span className="text-sm font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                              {formatCurrency(cost as number)}
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 retro:bg-black retro:border retro:border-green-700 retro:rounded-none">
                            <div
                              className="bg-blue-600 h-2 rounded-full retro:bg-green-600 retro:rounded-none"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                            {percentage.toFixed(1)}% of total
                          </div>
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cost Breakdown by Team */}
          {costSummary.breakdown_by_team && Object.keys(costSummary.breakdown_by_team).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <span className="retro:hidden">Cost by Team</span>
                  <span className="hidden retro:inline">[COST BY TEAM]</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(costSummary.breakdown_by_team)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([team, cost]) => (
                      <div key={team} className="flex justify-between items-center py-2 border-b dark:border-gray-700 retro:border-green-700 last:border-0">
                        <span className="text-sm text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {team}
                        </span>
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {formatCurrency(cost as number)}
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cost Breakdown by Project */}
          {costSummary.breakdown_by_project && Object.keys(costSummary.breakdown_by_project).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <span className="retro:hidden">Cost by Project</span>
                  <span className="hidden retro:inline">[COST BY PROJECT]</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(costSummary.breakdown_by_project)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([project, cost]) => (
                      <div key={project} className="flex justify-between items-center py-2 border-b dark:border-gray-700 retro:border-green-700 last:border-0">
                        <span className="text-sm text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {project}
                        </span>
                        <span className="text-sm font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {formatCurrency(cost as number)}
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cost Optimization Recommendations */}
          {!isLoadingRecs && recommendations && recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>
                  <span className="retro:hidden">💡 Cost Optimization Recommendations</span>
                  <span className="hidden retro:inline">[OPTIMIZATION RECOMMENDATIONS]</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 retro:bg-black retro:border-green-500 retro:rounded-none"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                              Workspace: {rec.workspace_id}
                            </span>
                            <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded retro:bg-black retro:border retro:border-blue-500 retro:text-blue-400 retro:font-mono retro:rounded-none">
                              {rec.type === 'right_sizing' ? 'Right-Sizing' : 'Billing Mode'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                            {rec.reason}
                          </p>
                        </div>
                        <div className="text-right ml-4">
                          <div className="text-lg font-bold text-green-600 dark:text-green-400 retro:text-green-500 retro:font-mono">
                            <span className="retro:hidden">💰 </span>
                            {formatCurrency(rec.estimated_savings)}
                          </div>
                          <div className="text-xs text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                            <span className="retro:hidden">potential savings</span>
                            <span className="hidden retro:inline">[SAVINGS/MONTH]</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Current:
                        </span>
                        <span className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {rec.current}
                        </span>
                        <span className="text-gray-400 retro:text-green-600 retro:font-mono">→</span>
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Recommended:
                        </span>
                        <span className="font-medium text-blue-600 dark:text-blue-400 retro:text-green-300 retro:font-mono">
                          {rec.recommended}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded retro:bg-black retro:border retro:border-green-700 retro:rounded-none">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Total Potential Savings:</span>
                      <span className="hidden retro:inline">[TOTAL SAVINGS POTENTIAL]:</span>
                    </span>
                    <span className="text-lg font-bold text-green-600 dark:text-green-400 retro:text-green-500 retro:font-mono">
                      {formatCurrency(recommendations.reduce((sum, rec) => sum + rec.estimated_savings, 0))}
                      <span className="text-sm font-normal text-gray-600 dark:text-gray-400 retro:text-green-600 ml-1">
                        /month
                      </span>
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <div className="text-6xl mb-4 retro:hidden">💰</div>
              <div className="hidden retro:block text-green-500 text-4xl font-mono mb-4">[NO DATA]</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono mb-2">
                No cost data available
              </h3>
              <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                Cost data will appear once workspaces are provisioned
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
