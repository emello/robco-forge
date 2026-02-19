/**
 * Cost data fetching hooks
 * 
 * Requirements: 22.2
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { mockCostSummary, mockCostRecommendations, mockBudget } from '@/lib/mock-data';

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
    queryFn: async () => {
      try {
        const data = await apiClient.getCostSummary(params);
        if (!data) {
          return mockCostSummary;
        }
        return data;
      } catch (error) {
        console.warn('API failed, using mock cost data:', error);
        return mockCostSummary;
      }
    },
  });
}

// Get cost recommendations
export function useCostRecommendations() {
  return useQuery({
    queryKey: costKeys.recommendations(),
    queryFn: async () => {
      try {
        const data = await apiClient.getCostRecommendations();
        if (!data || (Array.isArray(data) && data.length === 0)) {
          return mockCostRecommendations;
        }
        return data;
      } catch (error) {
        console.warn('API failed, using mock recommendations:', error);
        return mockCostRecommendations;
      }
    },
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
    queryFn: async () => {
      try {
        const data = await apiClient.getBudget(params);
        if (!data) {
          return mockBudget;
        }
        return data;
      } catch (error) {
        console.warn('API failed, using mock budget:', error);
        return mockBudget;
      }
    },
  });
}
