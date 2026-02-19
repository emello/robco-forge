'use client';

/**
 * Team Management Page (for Team Leads)
 * 
 * Requirements: 12.1
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { formatCurrency } from '@/lib/utils';

// Mock data - in production this would come from API
const mockTeamMembers = [
  { id: '1', name: 'Alice Johnson', email: 'alice@robco.com', role: 'engineer', current_spend: 450.00 },
  { id: '2', name: 'Bob Smith', email: 'bob@robco.com', role: 'engineer', current_spend: 320.50 },
  { id: '3', name: 'Carol Davis', email: 'carol@robco.com', role: 'contractor', current_spend: 180.00 },
];

const mockTeamBudget = {
  team_id: 'team-1',
  team_name: 'Engineering Team',
  amount: 5000.00,
  current_spend: 950.50,
  period: 'monthly' as const,
};

export default function TeamPage() {
  const budgetPercentage = (mockTeamBudget.current_spend / mockTeamBudget.amount) * 100;

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
          {'>>'} TEAM MANAGEMENT
        </h1>
        <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mt-2">
          Manage your team's budget and view member spending
        </p>
      </div>

      <div className="space-y-6">
        {/* Team Budget Overview */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">💰 Team Budget</span>
              <span className="hidden retro:inline">[TEAM BUDGET]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                  <span className="retro:hidden">Team</span>
                  <span className="hidden retro:inline">[TEAM]</span>
                </span>
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                  {mockTeamBudget.team_name}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                  <span className="retro:hidden">Current Spend</span>
                  <span className="hidden retro:inline">[CURRENT SPEND]</span>
                </span>
                <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                  {formatCurrency(mockTeamBudget.current_spend)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                  <span className="retro:hidden">Budget Limit</span>
                  <span className="hidden retro:inline">[BUDGET LIMIT]</span>
                </span>
                <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                  {formatCurrency(mockTeamBudget.amount)}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 retro:bg-black retro:border retro:border-green-700 retro:rounded-none">
                  <div
                    className={`h-4 rounded-full transition-all retro:rounded-none ${
                      budgetPercentage >= 100
                        ? 'bg-red-600 retro:bg-red-600'
                        : budgetPercentage >= 80
                        ? 'bg-yellow-600 retro:bg-yellow-600'
                        : 'bg-green-600 retro:bg-green-600'
                    }`}
                    style={{ width: `${Math.min(budgetPercentage, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    {budgetPercentage.toFixed(1)}% used
                  </span>
                  <span className="text-gray-600 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                    {formatCurrency(mockTeamBudget.amount - mockTeamBudget.current_spend)} remaining
                  </span>
                </div>
              </div>

              {/* Budget Warning */}
              {budgetPercentage >= 80 && budgetPercentage < 100 && (
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
                          Your team has used {budgetPercentage.toFixed(1)}% of the budget. Consider reviewing team workspace usage.
                        </span>
                        <span className="hidden retro:inline">
                          {budgetPercentage.toFixed(1)}% TEAM BUDGET USED. REVIEW USAGE.
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {budgetPercentage >= 100 && (
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
                          Your team has reached the budget limit. New workspace provisioning is blocked for team members.
                        </span>
                        <span className="hidden retro:inline">
                          TEAM BUDGET LIMIT REACHED. PROVISIONING BLOCKED.
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Team Members */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">👥 Team Members</span>
              <span className="hidden retro:inline">[TEAM MEMBERS]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b dark:border-gray-700 retro:border-green-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Name</span>
                      <span className="hidden retro:inline">[NAME]</span>
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Email</span>
                      <span className="hidden retro:inline">[EMAIL]</span>
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Role</span>
                      <span className="hidden retro:inline">[ROLE]</span>
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono">
                      <span className="retro:hidden">Current Spend</span>
                      <span className="hidden retro:inline">[SPEND]</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {mockTeamMembers.map((member) => (
                    <tr key={member.id} className="border-b dark:border-gray-700 retro:border-green-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-800 retro:hover:bg-green-900/10">
                      <td className="py-3 px-4 text-sm text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {member.name}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                        {member.email}
                      </td>
                      <td className="py-3 px-4 text-sm retro:font-mono">
                        <span className={`px-2 py-1 rounded text-xs font-medium retro:rounded-none ${
                          member.role === 'engineer'
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 retro:bg-transparent retro:border retro:border-blue-500 retro:text-blue-400'
                            : 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 retro:bg-transparent retro:border retro:border-purple-500 retro:text-purple-400'
                        }`}>
                          {member.role}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-right font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {formatCurrency(member.current_spend)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 dark:border-gray-700 retro:border-green-500">
                    <td colSpan={3} className="py-3 px-4 text-sm font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                      <span className="retro:hidden">Total Team Spend</span>
                      <span className="hidden retro:inline">[TOTAL SPEND]</span>
                    </td>
                    <td className="py-3 px-4 text-sm text-right font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                      {formatCurrency(mockTeamMembers.reduce((sum, m) => sum + m.current_spend, 0))}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Team Cost Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">📊 Cost Breakdown</span>
              <span className="hidden retro:inline">[COST BREAKDOWN]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockTeamMembers.map((member) => {
                const percentage = (member.current_spend / mockTeamBudget.current_spend) * 100;
                return (
                  <div key={member.id} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {member.name}
                      </span>
                      <span className="text-sm font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {formatCurrency(member.current_spend)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 retro:bg-black retro:border retro:border-green-700 retro:rounded-none">
                      <div
                        className="bg-blue-600 h-2 rounded-full retro:bg-green-600 retro:rounded-none"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 retro:text-green-600 retro:font-mono">
                      {percentage.toFixed(1)}% of team spend
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
