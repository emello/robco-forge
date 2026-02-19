/**
 * Type definitions for RobCo Forge Portal
 */

// Workspace types
export enum WorkspaceStatus {
  PENDING = 'PENDING',
  AVAILABLE = 'AVAILABLE',
  IMPAIRED = 'IMPAIRED',
  UNHEALTHY = 'UNHEALTHY',
  REBOOTING = 'REBOOTING',
  STARTING = 'STARTING',
  REBUILDING = 'REBUILDING',
  RESTORING = 'RESTORING',
  MAINTENANCE = 'MAINTENANCE',
  ADMIN_MAINTENANCE = 'ADMIN_MAINTENANCE',
  TERMINATING = 'TERMINATING',
  TERMINATED = 'TERMINATED',
  SUSPENDED = 'SUSPENDED',
  UPDATING = 'UPDATING',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
  ERROR = 'ERROR',
}

export enum BundleType {
  STANDARD = 'STANDARD',
  PERFORMANCE = 'PERFORMANCE',
  POWER = 'POWER',
  POWERPRO = 'POWERPRO',
  GRAPHICS_G4DN = 'GRAPHICS_G4DN',
  GRAPHICSPRO_G4DN = 'GRAPHICSPRO_G4DN',
}

export enum OperatingSystem {
  WINDOWS = 'Windows',
  LINUX = 'Linux',
}

export interface Workspace {
  workspace_id: string;
  user_id: string;
  bundle_type: BundleType;
  operating_system: OperatingSystem;
  status: WorkspaceStatus;
  region: string;
  blueprint_id?: string;
  connection_url?: string;
  ip_address?: string;
  computer_name?: string;
  created_at: string;
  updated_at: string;
  tags?: Record<string, string>;
}

// Blueprint types
export interface Blueprint {
  blueprint_id: string;
  name: string;
  description: string;
  operating_system: OperatingSystem;
  software_manifest: string[];
  team_id?: string;
  version: number;
  created_at: string;
  updated_at: string;
}

// Cost types
export interface CostSummary {
  period_start: string;
  period_end: string;
  total_cost: number;
  compute_cost: number;
  storage_cost: number;
  data_transfer_cost: number;
  breakdown_by_workspace?: Record<string, number>;
  breakdown_by_bundle?: Record<string, number>;
  breakdown_by_team?: Record<string, number>;
  breakdown_by_project?: Record<string, number>;
}

export interface CostRecommendation {
  workspace_id: string;
  type: 'right_sizing' | 'billing_mode';
  current: string;
  recommended: string;
  estimated_savings: number;
  reason: string;
}

export interface Budget {
  budget_id: string;
  user_id?: string;
  team_id?: string;
  project_id?: string;
  amount: number;
  current_spend: number;
  period: 'monthly' | 'quarterly' | 'annual';
  threshold_warning: number;
  threshold_limit: number;
}

// User types
export enum UserRole {
  ENGINEER = 'engineer',
  TEAM_LEAD = 'team_lead',
  CONTRACTOR = 'contractor',
  ADMIN = 'admin',
}

export interface User {
  user_id: string;
  email: string;
  name: string;
  role: UserRole;
  team_id?: string;
  created_at: string;
}

// Lucy AI types
export interface LucyMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface LucyResponse {
  response: string;
  intent?: string;
  tool_executed?: string;
  requires_confirmation?: boolean;
}

// API Error types
export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  details?: unknown;
}

// Theme types
export type Theme = 'modern' | 'retro';

// Pagination types
export interface PaginationParams {
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}
