'use client';

/**
 * Dashboard Page
 * 
 * Requirements: 11.2, 11.3, 13.5, 22.1
 */

import { StatCard } from '@/components/dashboard/stat-card';
import { WorkspaceQuickActions } from '@/components/dashboard/workspace-quick-actions';
import { WorkspaceList } from '@/components/dashboard/workspace-list';
import { BudgetStatus } from '@/components/dashboard/budget-status';
import { CostRecommendations } from '@/components/dashboard/cost-recommendations';
import { RetroHeader } from '@/components/dashboard/retro-header';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { useCostSummary, useCostRecommendations } from '@/hooks/use-costs';
import { formatCurrency } from '@/lib/utils';
import { WorkspaceStatus } from '@/types';

export default function DashboardPage() {
  // Fetch data
  const { data: workspaces } = useWorkspaces();
  const { data: costSummary } = useCostSummary();
  const { data: recommendations } = useCostRecommendations();

  // Calculate stats
  const activeWorkspaces = workspaces?.filter(
    (ws) =>
      ws.status === WorkspaceStatus.AVAILABLE ||
      ws.status === WorkspaceStatus.STARTING ||
      ws.status === WorkspaceStatus.STOPPING
  ).length || 0;

  const monthlyCost = costSummary?.total_cost || 0;
  const recommendationCount = recommendations?.length || 0;

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      {/* Retro ASCII Header */}
      <RetroHeader />

      <h1 className="text-3xl font-bold mb-8 text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
        {'>>'} DASHBOARD
      </h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Active Workspaces"
          value={activeWorkspaces}
          icon="💻"
        />
        <StatCard
          title="Monthly Cost"
          value={formatCurrency(monthlyCost)}
          icon="💰"
        />
        <StatCard
          title="Budget Status"
          value="Loading..."
          icon="📊"
        />
        <StatCard
          title="Recommendations"
          value={recommendationCount}
          icon="💡"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <WorkspaceQuickActions />
        <BudgetStatus />
      </div>

      {/* Workspace List and Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WorkspaceList />
        <CostRecommendations />
      </div>
    </div>
  );
}
