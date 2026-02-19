/**
 * Workspace Quick Actions Card
 * 
 * Requirements: 11.2, 22.1
 */

'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useRouter } from 'next/navigation';

export function WorkspaceQuickActions() {
  const router = useRouter();

  const actions = [
    {
      icon: '🚀',
      retroIcon: '[LAUNCH]',
      label: 'Launch New Workspace',
      description: 'Provision a new cloud desktop',
      onClick: () => router.push('/dashboard/workspaces?action=provision'),
    },
    {
      icon: '📋',
      retroIcon: '[LIST]',
      label: 'View All Workspaces',
      description: 'Manage your existing workspaces',
      onClick: () => router.push('/dashboard/workspaces'),
    },
    {
      icon: '💬',
      retroIcon: '[LUCY]',
      label: 'Ask Lucy',
      description: 'Get help from AI assistant',
      onClick: () => router.push('/dashboard/lucy'),
    },
    {
      icon: '📊',
      retroIcon: '[COSTS]',
      label: 'View Cost Report',
      description: 'See your spending and recommendations',
      onClick: () => router.push('/dashboard/costs'),
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{'>>'} Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {actions.map((action, index) => (
            <button
              key={index}
              onClick={action.onClick}
              className="w-full p-3 text-left border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:hover:bg-green-950 retro:rounded-none transition-colors group"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl retro:hidden">{action.icon}</span>
                <span className="hidden retro:inline text-green-400 font-mono font-bold">
                  {action.retroIcon}
                </span>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:uppercase group-hover:text-blue-600 dark:group-hover:text-blue-400 retro:group-hover:text-green-300">
                    {action.label}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono retro:text-xs">
                    {action.description}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
