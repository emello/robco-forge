/**
 * Forge API Client SDK
 * 
 * TypeScript client for the Forge API with authentication, retry logic, and error handling.
 * Requirements: 17.1
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import {
  Workspace,
  Blueprint,
  CostRecord,
  CostSummary,
  Budget,
  ApiError,
  ApiResponse,
  LucyChatResponse,
  BundleType,
  OperatingSystem,
} from '../types';

/**
 * Configuration for the Forge API client
 */
export interface ForgeClientConfig {
  apiUrl: string;
  authToken?: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
}

/**
 * Forge API Client
 * 
 * Provides methods to interact with the Forge API endpoints.
 * Handles authentication, retries, and error responses.
 */
export class ForgeClient {
  private client: AxiosInstance;
  private config: ForgeClientConfig;
  private maxRetries: number;
  private retryDelay: number;

  constructor(config: ForgeClientConfig) {
    this.config = config;
    this.maxRetries = config.maxRetries ?? 3;
    this.retryDelay = config.retryDelay ?? 1000;

    // Create axios instance with base configuration
    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: config.timeout ?? 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.config.authToken) {
          config.headers['Authorization'] = `Bearer ${this.config.authToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response) {
          // Server responded with error status
          const apiError: ApiError = {
            error: error.response.data.error || 'API Error',
            message: error.response.data.message || error.message,
            status_code: error.response.status,
            details: error.response.data.details,
          };
          return Promise.reject(apiError);
        } else if (error.request) {
          // Request made but no response
          const apiError: ApiError = {
            error: 'Network Error',
            message: 'No response from server. Please check your connection.',
            status_code: 0,
          };
          return Promise.reject(apiError);
        } else {
          // Error setting up request
          const apiError: ApiError = {
            error: 'Request Error',
            message: error.message,
            status_code: 0,
          };
          return Promise.reject(apiError);
        }
      }
    );
  }

  /**
   * Set authentication token
   */
  setAuthToken(token: string): void {
    this.config.authToken = token;
  }

  /**
   * Make request with retry logic
   */
  private async requestWithRetry<T>(
    requestFn: () => Promise<T>,
    retries: number = this.maxRetries
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error)) {
        await this.delay(this.retryDelay);
        return this.requestWithRetry(requestFn, retries - 1);
      }
      throw error;
    }
  }

  /**
   * Determine if request should be retried
   */
  private shouldRetry(error: unknown): boolean {
    if (typeof error === 'object' && error !== null && 'status_code' in error) {
      const apiError = error as ApiError;
      // Retry on network errors and 5xx server errors
      return apiError.status_code === 0 || apiError.status_code >= 500;
    }
    return false;
  }

  /**
   * Delay helper for retries
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // ==================== Workspace Management ====================

  /**
   * Provision a new workspace
   */
  async provisionWorkspace(params: {
    bundle_type: BundleType;
    operating_system: OperatingSystem;
    blueprint_id?: string;
    region?: string;
    tags?: Record<string, string>;
  }): Promise<Workspace> {
    return this.requestWithRetry(async () => {
      const response = await this.client.post<ApiResponse<Workspace>>(
        '/api/v1/workspaces',
        params
      );
      return response.data.data;
    });
  }

  /**
   * List workspaces
   */
  async listWorkspaces(params?: {
    status?: string;
    bundle_type?: BundleType;
    limit?: number;
    offset?: number;
  }): Promise<Workspace[]> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<Workspace[]>>('/api/v1/workspaces', {
        params,
      });
      return response.data.data;
    });
  }

  /**
   * Get workspace details
   */
  async getWorkspace(workspaceId: string): Promise<Workspace> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<Workspace>>(
        `/api/v1/workspaces/${workspaceId}`
      );
      return response.data.data;
    });
  }

  /**
   * Start a workspace
   */
  async startWorkspace(workspaceId: string): Promise<Workspace> {
    return this.requestWithRetry(async () => {
      const response = await this.client.post<ApiResponse<Workspace>>(
        `/api/v1/workspaces/${workspaceId}/start`
      );
      return response.data.data;
    });
  }

  /**
   * Stop a workspace
   */
  async stopWorkspace(workspaceId: string): Promise<Workspace> {
    return this.requestWithRetry(async () => {
      const response = await this.client.post<ApiResponse<Workspace>>(
        `/api/v1/workspaces/${workspaceId}/stop`
      );
      return response.data.data;
    });
  }

  /**
   * Terminate a workspace
   */
  async terminateWorkspace(workspaceId: string): Promise<void> {
    return this.requestWithRetry(async () => {
      await this.client.delete(`/api/v1/workspaces/${workspaceId}`);
    });
  }

  // ==================== Blueprint Management ====================

  /**
   * List blueprints
   */
  async listBlueprints(params?: {
    team_id?: string;
    operating_system?: OperatingSystem;
  }): Promise<Blueprint[]> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<Blueprint[]>>('/api/v1/blueprints', {
        params,
      });
      return response.data.data;
    });
  }

  /**
   * Get blueprint details
   */
  async getBlueprint(blueprintId: string): Promise<Blueprint> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<Blueprint>>(
        `/api/v1/blueprints/${blueprintId}`
      );
      return response.data.data;
    });
  }

  // ==================== Cost Management ====================

  /**
   * Get cost data
   */
  async getCosts(params?: {
    start_date?: string;
    end_date?: string;
    workspace_id?: string;
    team_id?: string;
    project_id?: string;
  }): Promise<CostRecord[]> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<CostRecord[]>>('/api/v1/costs', {
        params,
      });
      return response.data.data;
    });
  }

  /**
   * Get cost summary
   */
  async getCostSummary(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: 'workspace' | 'bundle' | 'team' | 'project';
  }): Promise<CostSummary> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<CostSummary>>('/api/v1/costs/summary', {
        params,
      });
      return response.data.data;
    });
  }

  /**
   * Get cost optimization recommendations
   */
  async getCostRecommendations(): Promise<unknown[]> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<unknown[]>>(
        '/api/v1/costs/recommendations'
      );
      return response.data.data;
    });
  }

  /**
   * Get budget information
   */
  async getBudget(params?: {
    user_id?: string;
    team_id?: string;
    project_id?: string;
  }): Promise<Budget> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<Budget>>('/api/v1/budgets', {
        params,
      });
      return response.data.data;
    });
  }

  // ==================== Lucy AI ====================

  /**
   * Send message to Lucy
   */
  async chatWithLucy(message: string, userId: string): Promise<LucyChatResponse> {
    return this.requestWithRetry(async () => {
      const response = await this.client.post<ApiResponse<LucyChatResponse>>(
        '/api/v1/lucy/chat',
        { message },
        {
          headers: {
            'X-User-ID': userId,
          },
        }
      );
      return response.data.data;
    });
  }

  /**
   * Get Lucy conversation context
   */
  async getLucyContext(userId: string): Promise<unknown> {
    return this.requestWithRetry(async () => {
      const response = await this.client.get<ApiResponse<unknown>>('/api/v1/lucy/context', {
        headers: {
          'X-User-ID': userId,
        },
      });
      return response.data.data;
    });
  }

  /**
   * Clear Lucy conversation context
   */
  async clearLucyContext(userId: string): Promise<void> {
    return this.requestWithRetry(async () => {
      await this.client.delete('/api/v1/lucy/context', {
        headers: {
          'X-User-ID': userId,
        },
      });
    });
  }

  // ==================== Health Check ====================

  /**
   * Check API health
   */
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

/**
 * Create a Forge API client instance
 */
export function createForgeClient(config: ForgeClientConfig): ForgeClient {
  return new ForgeClient(config);
}
