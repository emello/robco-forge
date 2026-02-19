/**
 * Cost data fetching hooks
 * 
 * Requirements: 22.2
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

// Query keys
export const costKeys = {
  all: ['costs'] as const,
  summary: (params: Record<string, unknown>) => [...costKeys.all, 'summary', params] as const,
  recommendations: () => [...costKeys.all, 'recommendations'] as const,
  budget: (params: Record<string, unknown>) => [...costKeys.all, 'budget', params] as const,
};

// Get cost summary
export function useCostSummary(params?: {
  start_date?: string;
  end_date?: string;
  group_by?: 'workspace' | 'bundle' | 'team' | 'project';
}) {
  return useQuery({
    queryKey: costKeys.summary(params || {}),
    queryFn: () => apiClient.getCostSummary(params),
  });
}

// Get cost recommendations
export function useCostRecommendations() {
  return useQuery({
    queryKey: costKeys.recommendations(),
    queryFn: () => apiClient.getCostRecommendations(),
  });
}

// Get budget
export function useBudget(params?: {
  user_id?: string;
  team_id?: string;
  project_id?: string;
}) {
  return useQuery({
    queryKey: costKeys.budget(params || {}),
    queryFn: () => apiClient.getBudget(params),
  });
}
