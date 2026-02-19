'use client';

/**
 * Workspaces Management Page
 * 
 * Requirements: 1.1
 */

import { useState } from 'react';
import { useWorkspaces } from '@/hooks/use-workspaces';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ProvisionModal } from '@/components/workspaces/provision-modal';
import { WorkspaceActions } from '@/components/workspaces/workspace-actions';
import { formatDate, formatCurrency, getStatusColor } from '@/lib/utils';
import { WorkspaceStatus, BundleType } from '@/types';

export default function WorkspacesPage() {
  const [isProvisionModalOpen, setIsProvisionModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [bundleFilter, setBundleFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'created' | 'status' | 'bundle'>('created');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const { data: workspaces, isLoading, error } = useWorkspaces();

  // Filter and sort workspaces
  const filteredAndSortedWorkspaces = workspaces?.items
    .filter((ws) => {
      if (statusFilter !== 'all' && ws.status !== statusFilter) return false;
      if (bundleFilter !== 'all' && ws.bundle_type !== bundleFilter) return false;
      return true;
    })
    .sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'created') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortBy === 'status') {
        comparison = a.status.localeCompare(b.status);
      } else if (sortBy === 'bundle') {
        comparison = a.bundle_type.localeCompare(b.bundle_type);
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    }) || [];

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
          {'>>'} WORKSPACES
        </h1>
        <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mt-2">
          Manage your cloud engineering workstations
        </p>
      </div>

      {/* Filters and Actions */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex flex-wrap gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Status
                </label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                >
                  <option value="all">All Statuses</option>
                  <option value={WorkspaceStatus.AVAILABLE}>Available</option>
                  <option value={WorkspaceStatus.STOPPED}>Stopped</option>
                  <option value={WorkspaceStatus.STARTING}>Starting</option>
                  <option value={WorkspaceStatus.STOPPING}>Stopping</option>
                  <option value={WorkspaceStatus.PENDING}>Pending</option>
                </select>
              </div>

              {/* Bundle Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Bundle Type
                </label>
                <select
                  value={bundleFilter}
                  onChange={(e) => setBundleFilter(e.target.value)}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                >
                  <option value="all">All Bundles</option>
                  <option value={BundleType.STANDARD}>Standard</option>
                  <option value={BundleType.PERFORMANCE}>Performance</option>
                  <option value={BundleType.POWER}>Power</option>
                  <option value={BundleType.POWERPRO}>PowerPro</option>
                  <option value={BundleType.GRAPHICS_G4DN}>Graphics G4DN</option>
                  <option value={BundleType.GRAPHICSPRO_G4DN}>GraphicsPro G4DN</option>
                </select>
              </div>

              {/* Sort By */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Sort By
                </label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as 'created' | 'status' | 'bundle')}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                >
                  <option value="created">Created Date</option>
                  <option value="status">Status</option>
                  <option value="bundle">Bundle Type</option>
                </select>
              </div>

              {/* Sort Order */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Order
                </label>
                <button
                  onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none hover:bg-gray-50 dark:hover:bg-gray-700 retro:hover:bg-green-950"
                >
                  {sortOrder === 'asc' ? '↑ Ascending' : '↓ Descending'}
                </button>
              </div>
            </div>

            <button 
              onClick={() => setIsProvisionModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black retro:font-mono retro:font-bold retro:rounded-none retro:hover:bg-green-500"
            >
              <span className="retro:hidden">+ New Workspace</span>
              <span className="hidden retro:inline">[+ NEW WORKSPACE]</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Workspaces List */}
      {isLoading ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              <span className="retro:hidden">Loading workspaces...</span>
              <span className="hidden retro:inline">[LOADING WORKSPACES...]</span>
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
              <span className="retro:hidden">Failed to load workspaces</span>
              <span className="hidden retro:inline">[ERROR: LOAD FAILED]</span>
            </div>
          </CardContent>
        </Card>
      ) : filteredAndSortedWorkspaces.length === 0 ? (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <div className="text-6xl mb-4 retro:hidden">🚀</div>
              <div className="hidden retro:block text-green-500 text-4xl font-mono mb-4">[EMPTY]</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono mb-2">
                No workspaces found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mb-4">
                Get started by creating your first workspace
              </p>
              <button 
                onClick={() => setIsProvisionModalOpen(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black retro:font-mono retro:font-bold retro:rounded-none retro:hover:bg-green-500"
              >
                <span className="retro:hidden">Create Workspace</span>
                <span className="hidden retro:inline">[CREATE WORKSPACE]</span>
              </button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredAndSortedWorkspaces.map((workspace) => (
            <Card key={workspace.workspace_id} className="hover:shadow-lg transition-shadow">
              <CardContent>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {workspace.computer_name || workspace.workspace_id}
                      </h3>
                      <span
                        className={`text-xs px-2 py-1 rounded retro:rounded-none retro:border retro:font-mono ${getStatusColor(
                          workspace.status
                        )} bg-opacity-10 retro:bg-black`}
                      >
                        [{workspace.status}]
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Bundle:
                        </span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {workspace.bundle_type}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Region:
                        </span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {workspace.region}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          OS:
                        </span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {workspace.operating_system}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Created:
                        </span>
                        <span className="ml-2 font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                          {formatDate(workspace.created_at)}
                        </span>
                      </div>
                    </div>

                    {workspace.connection_url && (
                      <div className="mt-2 text-sm">
                        <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                          Connection URL:
                        </span>
                        <a
                          href={workspace.connection_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 dark:text-blue-400 retro:text-green-300 retro:font-mono hover:underline"
                        >
                          {workspace.connection_url}
                        </a>
                      </div>
                    )}
                  </div>

                  <div className="ml-4">
                    <WorkspaceActions workspace={workspace} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Results Count */}
      {!isLoading && !error && filteredAndSortedWorkspaces.length > 0 && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
          Showing {filteredAndSortedWorkspaces.length} of {workspaces?.items.length || 0} workspaces
        </div>
      )}

      {/* Provision Modal */}
      <ProvisionModal 
        isOpen={isProvisionModalOpen} 
        onClose={() => setIsProvisionModalOpen(false)} 
      />
    </div>
  );
}
