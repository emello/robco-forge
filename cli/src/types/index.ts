/**
 * Type definitions for Forge CLI
 * 
 * Requirements: 17.1
 */

/**
 * Bundle types available for workspaces
 */
export enum BundleType {
  STANDARD = 'STANDARD',
  PERFORMANCE = 'PERFORMANCE',
  POWER = 'POWER',
  POWERPRO = 'POWERPRO',
  GRAPHICS_G4DN = 'GRAPHICS_G4DN',
  GRAPHICSPRO_G4DN = 'GRAPHICSPRO_G4DN',
}

/**
 * Operating system options
 */
export enum OperatingSystem {
  WINDOWS = 'Windows',
  LINUX = 'Linux',
}

/**
 * Workspace status
 */
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

/**
 * Workspace resource
 */
export interface Workspace {
  workspace_id: string;
  user_id: string;
  bundle_type: BundleType;
  operating_system: OperatingSystem;
  status: WorkspaceStatus;
  region: string;
  blueprint_id?: string;
  created_at: string;
  updated_at: string;
  connection_url?: string;
  ip_address?: string;
  computer_name?: string;
}

/**
 * Blueprint resource
 */
export interface Blueprint {
  blueprint_id: string;
  name: string;
  description: string;
  operating_system: OperatingSystem;
  software_manifest: Record<string, string>;
  team_id: string;
  version: number;
  created_at: string;
  updated_at: string;
}

/**
 * Cost record
 */
export interface CostRecord {
  workspace_id: string;
  user_id: string;
  team_id?: string;
  project_id?: string;
  bundle_type: BundleType;
  compute_cost: number;
  storage_cost: number;
  data_transfer_cost: number;
  total_cost: number;
  period_start: string;
  period_end: string;
}

/**
 * Cost summary
 */
export interface CostSummary {
  total_cost: number;
  compute_cost: number;
  storage_cost: number;
  data_transfer_cost: number;
  period_start: string;
  period_end: string;
  breakdown_by_workspace?: Record<string, number>;
  breakdown_by_bundle?: Record<string, number>;
}

/**
 * Budget information
 */
export interface Budget {
  budget_id: string;
  user_id?: string;
  team_id?: string;
  project_id?: string;
  amount: number;
  current_spend: number;
  period: string;
  threshold_warning: number;
  threshold_limit: number;
}

/**
 * CLI configuration
 */
export interface CliConfig {
  apiUrl: string;
  authToken?: string;
  defaultBundle?: BundleType;
  defaultOs?: OperatingSystem;
  outputFormat?: 'table' | 'json';
  debug?: boolean;
}

/**
 * API error response
 */
export interface ApiError {
  error: string;
  message: string;
  status_code: number;
  details?: Record<string, unknown>;
}

/**
 * API success response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

/**
 * Lucy chat message
 */
export interface LucyMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

/**
 * Lucy chat response
 */
export interface LucyChatResponse {
  response: string;
  intent?: string;
  tool_executed?: string;
  requires_confirmation?: boolean;
}
