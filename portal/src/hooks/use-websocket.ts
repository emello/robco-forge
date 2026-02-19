/**
 * WebSocket Hook for Real-Time Updates
 * 
 * Requirements: 22.2
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WebSocketMessage {
  type: 'workspace_update' | 'cost_update' | 'budget_alert';
  data: unknown;
}

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const queryClient = useQueryClient();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!userId) return;

    const connect = () => {
      // Use environment variable or default to localhost
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
      const ws = new WebSocket(`${wsUrl}?user_id=${userId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...');
          connect();
        }, 5000);
      };

      wsRef.current = ws;
    };

    const handleMessage = (message: WebSocketMessage) => {
      switch (message.type) {
        case 'workspace_update':
          // Invalidate workspace queries to trigger refetch
          queryClient.invalidateQueries({ queryKey: ['workspaces'] });
          console.log('Workspace update received, refreshing data');
          break;
          
        case 'cost_update':
          // Invalidate cost queries
          queryClient.invalidateQueries({ queryKey: ['costs'] });
          console.log('Cost update received, refreshing data');
          break;
          
        case 'budget_alert':
          // Invalidate budget queries and show notification
          queryClient.invalidateQueries({ queryKey: ['budget'] });
          console.log('Budget alert received:', message.data);
          // Could trigger a toast notification here
          break;
          
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId, queryClient]);

  return { isConnected };
}
