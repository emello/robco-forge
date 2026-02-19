/**
 * Workspace List component with status indicators
 * 
 * Requirements: 11.2, 11.3, 22.1
 */

'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { formatRelativeTime, getStatusColor } from '@/lib/utils';
import { WorkspaceStatus } from '@/types';

export function WorkspaceList() {
  const { data: workspaces, isLoading, error } = useWorkspaces({ limit: 5 });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Active Workspaces</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
            <span className="retro:hidden">Loading workspaces...</span>
            <span className="hidden retro:inline">[LOADING...]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{'>>'} Active Workspaces</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
            <span className="retro:hidden">Failed to load workspaces</span>
            <span className="hidden retro:inline">[ERROR: LOAD FAILED]</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const activeWorkspaces = workspaces?.filter(
    (ws) =>
      ws.status === WorkspaceStatus.AVAILABLE ||
      ws.status === WorkspaceStatus.STARTING ||
      ws.status === WorkspaceStatus.STOPPING
  ) || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{'>>'} Active Workspaces</CardTitle>
      </CardHeader>
      <CardContent>
        {activeWorkspaces.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
            <span className="retro:hidden">No active workspaces</span>
            <span className="hidden retro:inline">[NO ACTIVE WORKSPACES]</span>
          </div>
        ) : (
          <div className="space-y-3">
            {activeWorkspaces.map((workspace) => (
              <div
                key={workspace.workspace_id}
                className="p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:hover:bg-green-950 retro:rounded-none transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {workspace.computer_name || workspace.workspace_id.slice(0, 8)}
                      </span>
                      <span
                        className={`text-xs px-2 py-1 rounded retro:rounded-none retro:border retro:font-mono ${getStatusColor(
                          workspace.status
                        )} bg-opacity-10 retro:bg-black`}
                      >
                        [{workspace.status}]
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono retro:text-xs mt-1">
                      {workspace.bundle_type} • {workspace.region}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 retro:text-green-600 retro:font-mono mt-1">
                      Created {formatRelativeTime(workspace.created_at)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
