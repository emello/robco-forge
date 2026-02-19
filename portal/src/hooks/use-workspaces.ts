/**
 * Workspace data fetching hooks
 * 
 * Requirements: 22.2
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { Workspace, BundleType, OperatingSystem } from '@/types';

// Query keys
export const workspaceKeys = {
  all: ['workspaces'] as const,
  lists: () => [...workspaceKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) =>
    [...workspaceKeys.lists(), filters] as const,
  details: () => [...workspaceKeys.all, 'detail'] as const,
  detail: (id: string) => [...workspaceKeys.details(), id] as const,
};

// List workspaces
export function useWorkspaces(params?: {
  status?: string;
  bundle_type?: BundleType;
  limit?: number;
}) {
  return useQuery({
    queryKey: workspaceKeys.list(params || {}),
    queryFn: () => apiClient.listWorkspaces(params),
  });
}

// Get single workspace
export function useWorkspace(workspaceId: string) {
  return useQuery({
    queryKey: workspaceKeys.detail(workspaceId),
    queryFn: () => apiClient.getWorkspace(workspaceId),
    enabled: !!workspaceId,
  });
}

// Provision workspace
export function useProvisionWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      bundle_type: BundleType;
      operating_system: OperatingSystem;
      blueprint_id?: string;
      region?: string;
      tags?: Record<string, string>;
    }) => apiClient.provisionWorkspace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
}

// Start workspace
export function useStartWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) => apiClient.startWorkspace(workspaceId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(data.workspace_id) });
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
}

// Stop workspace
export function useStopWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) => apiClient.stopWorkspace(workspaceId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(data.workspace_id) });
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
}

// Terminate workspace
export function useTerminateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) => apiClient.terminateWorkspace(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
  });
}
