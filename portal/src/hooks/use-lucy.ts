/**
 * Lucy AI data fetching hooks
 * 
 * Requirements: 22.2
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

// Query keys
export const lucyKeys = {
  all: ['lucy'] as const,
  context: (userId: string) => [...lucyKeys.all, 'context', userId] as const,
};

// Get Lucy context
export function useLucyContext(userId: string) {
  return useQuery({
    queryKey: lucyKeys.context(userId),
    queryFn: () => apiClient.getLucyContext(userId),
    enabled: !!userId,
  });
}

// Chat with Lucy
export function useChatWithLucy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ message, userId }: { message: string; userId: string }) =>
      apiClient.chatWithLucy(message, userId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: lucyKeys.context(variables.userId) });
    },
  });
}

// Clear Lucy context
export function useClearLucyContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => apiClient.clearLucyContext(userId),
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: lucyKeys.context(userId) });
    },
  });
}
