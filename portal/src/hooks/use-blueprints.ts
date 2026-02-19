/**
 * Blueprint data fetching hooks
 * 
 * Requirements: 22.2
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { Blueprint, OperatingSystem } from '@/types';
import { mockBlueprints } from '@/lib/mock-data';

// Query keys
export const blueprintKeys = {
  all: ['blueprints'] as const,
  lists: () => [...blueprintKeys.all, 'list'] as const,
  details: () => [...blueprintKeys.all, 'detail'] as const,
  detail: (id: string) => [...blueprintKeys.details(), id] as const,
};

// List blueprints
export function useBlueprints() {
  return useQuery({
    queryKey: blueprintKeys.lists(),
    queryFn: async () => {
      try {
        const data = await apiClient.listBlueprints();
        if (!data || (Array.isArray(data) && data.length === 0)) {
          return mockBlueprints;
        }
        return data;
      } catch (error) {
        console.warn('API failed, using mock blueprints:', error);
        return mockBlueprints;
      }
    },
  });
}

// Get single blueprint
export function useBlueprint(blueprintId: string) {
  return useQuery({
    queryKey: blueprintKeys.detail(blueprintId),
    queryFn: () => apiClient.getBlueprint(blueprintId),
    enabled: !!blueprintId,
  });
}

// Create blueprint
export function useCreateBlueprint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      name: string;
      description: string;
      operating_system: OperatingSystem;
      software_manifest: string[];
      team_id?: string;
    }) => apiClient.createBlueprint(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: blueprintKeys.lists() });
    },
  });
}

// Update blueprint
export function useUpdateBlueprint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ blueprintId, data }: { blueprintId: string; data: Partial<Blueprint> }) =>
      apiClient.updateBlueprint(blueprintId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: blueprintKeys.detail(data.blueprint_id) });
      queryClient.invalidateQueries({ queryKey: blueprintKeys.lists() });
    },
  });
}
