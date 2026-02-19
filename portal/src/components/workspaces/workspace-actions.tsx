/**
 * Workspace Actions Component
 * 
 * Requirements: 1.7, 1.9
 */

'use client';

import { useState } from 'react';
import { useStartWorkspace, useStopWorkspace, useTerminateWorkspace } from '@/hooks/use-workspaces';
import { Modal } from '@/components/ui/modal';
import { WorkspaceStatus, type Workspace } from '@/types';

interface WorkspaceActionsProps {
  workspace: Workspace;
}

export function WorkspaceActions({ workspace }: WorkspaceActionsProps) {
  const [showStopConfirm, setShowStopConfirm] = useState(false);
  const [showTerminateConfirm, setShowTerminateConfirm] = useState(false);

  const startMutation = useStartWorkspace();
  const stopMutation = useStopWorkspace();
  const terminateMutation = useTerminateWorkspace();

  const handleStart = () => {
    startMutation.mutate(workspace.workspace_id);
  };

  const handleStop = () => {
    stopMutation.mutate(workspace.workspace_id, {
      onSuccess: () => setShowStopConfirm(false),
    });
  };

  const handleTerminate = () => {
    terminateMutation.mutate(workspace.workspace_id, {
      onSuccess: () => setShowTerminateConfirm(false),
    });
  };

  const canStart = workspace.status === WorkspaceStatus.STOPPED;
  const canStop = workspace.status === WorkspaceStatus.AVAILABLE;
  const canTerminate = ![WorkspaceStatus.TERMINATING, WorkspaceStatus.TERMINATED].includes(workspace.status);

  return (
    <>
      <div className="flex gap-2">
        {/* Start Button */}
        {canStart && (
          <button
            onClick={handleStart}
            disabled={startMutation.isPending}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed retro:bg-green-600 retro:border retro:border-green-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-green-500"
          >
            <span className="retro:hidden">
              {startMutation.isPending ? 'Starting...' : 'Start'}
            </span>
            <span className="hidden retro:inline">
              {startMutation.isPending ? '[STARTING...]' : '[START]'}
            </span>
          </button>
        )}

        {/* Stop Button */}
        {canStop && (
          <button
            onClick={() => setShowStopConfirm(true)}
            disabled={stopMutation.isPending}
            className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed retro:bg-yellow-600 retro:border retro:border-yellow-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-yellow-500"
          >
            <span className="retro:hidden">Stop</span>
            <span className="hidden retro:inline">[STOP]</span>
          </button>
        )}

        {/* Terminate Button */}
        {canTerminate && (
          <button
            onClick={() => setShowTerminateConfirm(true)}
            disabled={terminateMutation.isPending}
            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed retro:bg-red-600 retro:border retro:border-red-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-red-500"
          >
            <span className="retro:hidden">Terminate</span>
            <span className="hidden retro:inline">[TERMINATE]</span>
          </button>
        )}
      </div>

      {/* Stop Confirmation Modal */}
      <Modal
        isOpen={showStopConfirm}
        onClose={() => setShowStopConfirm(false)}
        title="Stop Workspace"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300 retro:text-green-400">
            Are you sure you want to stop this workspace?
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-500">
            <span className="retro:hidden">
              Workspace: {workspace.computer_name || workspace.workspace_id}
            </span>
            <span className="hidden retro:inline">
              WORKSPACE: {workspace.computer_name || workspace.workspace_id}
            </span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-500">
            <span className="retro:hidden">
              You can restart it later. Your data will be preserved.
            </span>
            <span className="hidden retro:inline">
              DATA WILL BE PRESERVED. CAN RESTART LATER.
            </span>
          </p>

          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowStopConfirm(false)}
              disabled={stopMutation.isPending}
              className="px-4 py-2 border rounded hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-950"
            >
              <span className="retro:hidden">Cancel</span>
              <span className="hidden retro:inline">[CANCEL]</span>
            </button>
            <button
              onClick={handleStop}
              disabled={stopMutation.isPending}
              className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 retro:bg-yellow-600 retro:border retro:border-yellow-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-yellow-500"
            >
              <span className="retro:hidden">
                {stopMutation.isPending ? 'Stopping...' : 'Stop Workspace'}
              </span>
              <span className="hidden retro:inline">
                {stopMutation.isPending ? '[STOPPING...]' : '[STOP WORKSPACE]'}
              </span>
            </button>
          </div>

          {stopMutation.isError && (
            <p className="text-sm text-red-600 dark:text-red-400 retro:text-red-500">
              <span className="retro:hidden">
                Failed to stop workspace. Please try again.
              </span>
              <span className="hidden retro:inline">
                [ERROR: STOP FAILED. RETRY.]
              </span>
            </p>
          )}
        </div>
      </Modal>

      {/* Terminate Confirmation Modal */}
      <Modal
        isOpen={showTerminateConfirm}
        onClose={() => setShowTerminateConfirm(false)}
        title="Terminate Workspace"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-red-600 dark:text-red-400 retro:text-red-500 font-semibold">
            <span className="retro:hidden">⚠️ Warning: This action cannot be undone!</span>
            <span className="hidden retro:inline">[!] WARNING: IRREVERSIBLE ACTION</span>
          </p>
          <p className="text-gray-700 dark:text-gray-300 retro:text-green-400">
            <span className="retro:hidden">
              Are you sure you want to permanently terminate this workspace?
            </span>
            <span className="hidden retro:inline">
              CONFIRM PERMANENT TERMINATION?
            </span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-500">
            <span className="retro:hidden">
              Workspace: {workspace.computer_name || workspace.workspace_id}
            </span>
            <span className="hidden retro:inline">
              WORKSPACE: {workspace.computer_name || workspace.workspace_id}
            </span>
          </p>
          <p className="text-sm text-red-600 dark:text-red-400 retro:text-red-500">
            <span className="retro:hidden">
              All data will be permanently deleted. Your user volume will be preserved.
            </span>
            <span className="hidden retro:inline">
              DATA DELETION PERMANENT. USER VOLUME PRESERVED.
            </span>
          </p>

          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowTerminateConfirm(false)}
              disabled={terminateMutation.isPending}
              className="px-4 py-2 border rounded hover:bg-gray-50 dark:hover:bg-gray-800 retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:hover:bg-green-950"
            >
              <span className="retro:hidden">Cancel</span>
              <span className="hidden retro:inline">[CANCEL]</span>
            </button>
            <button
              onClick={handleTerminate}
              disabled={terminateMutation.isPending}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 retro:bg-red-600 retro:border retro:border-red-500 retro:text-black retro:font-mono retro:rounded-none retro:hover:bg-red-500"
            >
              <span className="retro:hidden">
                {terminateMutation.isPending ? 'Terminating...' : 'Terminate Workspace'}
              </span>
              <span className="hidden retro:inline">
                {terminateMutation.isPending ? '[TERMINATING...]' : '[TERMINATE WORKSPACE]'}
              </span>
            </button>
          </div>

          {terminateMutation.isError && (
            <p className="text-sm text-red-600 dark:text-red-400 retro:text-red-500">
              <span className="retro:hidden">
                Failed to terminate workspace. Please try again.
              </span>
              <span className="hidden retro:inline">
                [ERROR: TERMINATION FAILED. RETRY.]
              </span>
            </p>
          )}
        </div>
      </Modal>
    </>
  );
}
