'use client';

/**
 * Blueprints Management Page
 * 
 * Requirements: 2.4, 2.5
 */

import { useState } from 'react';
import { useBlueprints } from '@/hooks/use-blueprints';
import { Card, CardContent } from '@/components/ui/card';
import { CreateBlueprintModal } from '@/components/blueprints/create-blueprint-modal';
import { OperatingSystem } from '@/types';

export default function BlueprintsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [osFilter, setOsFilter] = useState<string>('all');
  const [teamFilter, setTeamFilter] = useState<string>('all');

  const { data: blueprints, isLoading, error } = useBlueprints();

  // Filter blueprints
  const filteredBlueprints = blueprints?.items
    .filter((bp) => {
      if (osFilter !== 'all' && bp.operating_system !== osFilter) return false;
      if (teamFilter === 'team' && !bp.team_id) return false;
      if (teamFilter === 'global' && bp.team_id) return false;
      return true;
    }) || [];

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
          {'>>'} BLUEPRINTS
        </h1>
        <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mt-2">
          Pre-configured workspace templates with software and settings
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent>
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex flex-wrap gap-4">
              {/* OS Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Operating System
                </label>
                <select
                  value={osFilter}
                  onChange={(e) => setOsFilter(e.target.value)}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                >
                  <option value="all">All OS</option>
                  <option value={OperatingSystem.WINDOWS}>Windows</option>
                  <option value={OperatingSystem.LINUX}>Linux</option>
                </select>
              </div>

              {/* Team Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-1">
                  Scope
                </label>
                <select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  className="px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                >
                  <option value="all">All Blueprints</option>
                  <option value="team">Team Blueprints</option>
                  <option value="global">Global Blueprints</option>
                </select>
              </div>
            </div>

            <button 
              onClick={() => setIsCreateModalOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black retro:font-mono retro:font-bold retro:rounded-none retro:hover:bg-green-500"
            >
              <span className="retro:hidden">+ New Blueprint</span>
              <span className="hidden retro:inline">[+ NEW BLUEPRINT]</span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Blueprints List */}
      {isLoading ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-gray-500 dark:text-gray-400 retro:text-green-400 retro:font-mono">
              <span className="retro:hidden">Loading blueprints...</span>
              <span className="hidden retro:inline">[LOADING BLUEPRINTS...]</span>
            </div>
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent>
            <div className="text-center py-12 text-red-600 dark:text-red-400 retro:text-red-500 retro:font-mono">
              <span className="retro:hidden">Failed to load blueprints</span>
              <span className="hidden retro:inline">[ERROR: LOAD FAILED]</span>
            </div>
          </CardContent>
        </Card>
      ) : filteredBlueprints.length === 0 ? (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <div className="text-6xl mb-4 retro:hidden">📋</div>
              <div className="hidden retro:block text-green-500 text-4xl font-mono mb-4">[EMPTY]</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono mb-2">
                No blueprints found
              </h3>
              <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mb-4">
                Create a blueprint to standardize workspace configurations
              </p>
              <button 
                onClick={() => setIsCreateModalOpen(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 retro:bg-green-600 retro:border-2 retro:border-green-500 retro:text-black retro:font-mono retro:font-bold retro:rounded-none retro:hover:bg-green-500"
              >
                <span className="retro:hidden">Create Blueprint</span>
                <span className="hidden retro:inline">[CREATE BLUEPRINT]</span>
              </button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredBlueprints.map((blueprint) => (
            <Card key={blueprint.blueprint_id} className="hover:shadow-lg transition-shadow">
              <CardContent>
                <div className="space-y-4">
                  {/* Header */}
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {blueprint.name}
                      </h3>
                      {blueprint.team_id ? (
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded retro:bg-black retro:border retro:border-blue-500 retro:text-blue-400 retro:font-mono retro:rounded-none">
                          <span className="retro:hidden">Team</span>
                          <span className="hidden retro:inline">[TEAM]</span>
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded retro:bg-black retro:border retro:border-green-500 retro:text-green-400 retro:font-mono retro:rounded-none">
                          <span className="retro:hidden">Global</span>
                          <span className="hidden retro:inline">[GLOBAL]</span>
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                      {blueprint.description}
                    </p>
                  </div>

                  {/* Details */}
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                        OS:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        {blueprint.operating_system}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                        Version:
                      </span>
                      <span className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                        v{blueprint.version}
                      </span>
                    </div>
                  </div>

                  {/* Software List */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 retro:text-green-400 retro:font-mono mb-2">
                      <span className="retro:hidden">Installed Software:</span>
                      <span className="hidden retro:inline">[SOFTWARE]:</span>
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {blueprint.software_manifest.slice(0, 5).map((software, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded retro:bg-black retro:border retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
                        >
                          {software}
                        </span>
                      ))}
                      {blueprint.software_manifest.length > 5 && (
                        <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded retro:bg-black retro:border retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none">
                          +{blueprint.software_manifest.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <button className="flex-1 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 retro:bg-green-600 retro:border retro:border-green-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-green-500">
                      <span className="retro:hidden">Use Blueprint</span>
                      <span className="hidden retro:inline">[USE]</span>
                    </button>
                    <button className="px-3 py-2 text-sm border rounded hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-950">
                      <span className="retro:hidden">Details</span>
                      <span className="hidden retro:inline">[INFO]</span>
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Results Count */}
      {!isLoading && !error && filteredBlueprints.length > 0 && (
        <div className="mt-6 text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
          Showing {filteredBlueprints.length} of {blueprints?.items.length || 0} blueprints
        </div>
      )}

      {/* Create Blueprint Modal */}
      <CreateBlueprintModal 
        isOpen={isCreateModalOpen} 
        onClose={() => setIsCreateModalOpen(false)} 
      />
    </div>
  );
}
