/**
 * Output formatting utilities
 * 
 * Requirements: 17.4
 */

import Table from 'cli-table3';
import chalk from 'chalk';
import { Workspace, WorkspaceStatus, CostSummary } from '../types';
import { icons, theme, formatMoney } from './colors';

/**
 * Format workspace status with color and icon
 */
export function formatStatus(status: WorkspaceStatus): string {
  switch (status) {
    case WorkspaceStatus.AVAILABLE:
      return `${icons.success} ${chalk.green(status)}`;
    case WorkspaceStatus.STARTING:
    case WorkspaceStatus.STOPPING:
    case WorkspaceStatus.REBOOTING:
      return `${icons.clock} ${chalk.yellow(status)}`;
    case WorkspaceStatus.STOPPED:
      return `${icons.bullet} ${chalk.gray(status)}`;
    case WorkspaceStatus.ERROR:
    case WorkspaceStatus.UNHEALTHY:
    case WorkspaceStatus.IMPAIRED:
      return `${icons.error} ${chalk.red(status)}`;
    case WorkspaceStatus.TERMINATING:
    case WorkspaceStatus.TERMINATED:
      return `${icons.cross} ${chalk.red(status)}`;
    default:
      return `${icons.bullet} ${chalk.white(status)}`;
  }
}

/**
 * Format workspace list as table
 */
export function formatWorkspaceTable(workspaces: Workspace[]): string {
  if (workspaces.length === 0) {
    return chalk.yellow(`${icons.info} No workspaces found.`);
  }

  const table = new Table({
    head: [
      chalk.cyan(`${icons.workspace} ID`),
      chalk.cyan('Bundle'),
      chalk.cyan('OS'),
      chalk.cyan('Status'),
      chalk.cyan('Region'),
      chalk.cyan('Created'),
    ],
    colWidths: [18, 20, 10, 18, 15, 20],
  });

  for (const ws of workspaces) {
    table.push([
      ws.workspace_id,
      ws.bundle_type,
      ws.operating_system,
      formatStatus(ws.status),
      ws.region,
      new Date(ws.created_at).toLocaleString(),
    ]);
  }

  return table.toString();
}

/**
 * Format workspace details
 */
export function formatWorkspaceDetails(workspace: Workspace): string {
  const lines: string[] = [
    chalk.bold(`\n${icons.workspace} Workspace Details:`),
    '',
    `${chalk.cyan('ID:')}              ${workspace.workspace_id}`,
    `${chalk.cyan('Status:')}          ${formatStatus(workspace.status)}`,
    `${chalk.cyan('Bundle Type:')}     ${workspace.bundle_type}`,
    `${chalk.cyan('Operating System:')} ${workspace.operating_system}`,
    `${chalk.cyan('Region:')}          ${workspace.region}`,
    `${chalk.cyan('User ID:')}         ${workspace.user_id}`,
  ];

  if (workspace.blueprint_id) {
    lines.push(`${chalk.cyan('Blueprint:')}       ${workspace.blueprint_id}`);
  }

  if (workspace.connection_url) {
    lines.push(`${chalk.cyan('Connection URL:')}  ${chalk.underline(workspace.connection_url)}`);
  }

  if (workspace.ip_address) {
    lines.push(`${chalk.cyan('IP Address:')}      ${workspace.ip_address}`);
  }

  if (workspace.computer_name) {
    lines.push(`${chalk.cyan('Computer Name:')}   ${workspace.computer_name}`);
  }

  lines.push(
    `${chalk.cyan('Created:')}         ${new Date(workspace.created_at).toLocaleString()}`,
    `${chalk.cyan('Updated:')}         ${new Date(workspace.updated_at).toLocaleString()}`
  );

  return lines.join('\n');
}

/**
 * Format cost summary
 */
export function formatCostSummary(summary: CostSummary): string {
  const lines: string[] = [
    chalk.bold(`\n${icons.money} Cost Summary:`),
    '',
    `${chalk.cyan('Period:')}          ${new Date(summary.period_start).toLocaleDateString()} - ${new Date(summary.period_end).toLocaleDateString()}`,
    `${chalk.cyan('Total Cost:')}      ${formatMoney(summary.total_cost)}`,
    `${chalk.cyan('Compute:')}         ${formatMoney(summary.compute_cost)}`,
    `${chalk.cyan('Storage:')}         ${formatMoney(summary.storage_cost)}`,
    `${chalk.cyan('Data Transfer:')}   ${formatMoney(summary.data_transfer_cost)}`,
  ];

  if (summary.breakdown_by_workspace) {
    lines.push('', chalk.bold('By Workspace:'));
    
    const wsTable = new Table({
      head: [chalk.cyan('Workspace ID'), chalk.cyan('Cost')],
      colWidths: [40, 15],
    });
    
    for (const [wsId, cost] of Object.entries(summary.breakdown_by_workspace)) {
      wsTable.push([wsId, formatMoney(cost)]);
    }
    
    lines.push(wsTable.toString());
  }

  if (summary.breakdown_by_bundle) {
    lines.push('', chalk.bold('By Bundle Type:'));
    
    const bundleTable = new Table({
      head: [chalk.cyan('Bundle Type'), chalk.cyan('Cost')],
      colWidths: [30, 15],
    });
    
    for (const [bundle, cost] of Object.entries(summary.breakdown_by_bundle)) {
      bundleTable.push([bundle, formatMoney(cost)]);
    }
    
    lines.push(bundleTable.toString());
  }

  return lines.join('\n');
}

/**
 * Format cost recommendations as table
 */
export function formatRecommendationsTable(recommendations: Array<{
  workspace_id?: string;
  type?: string;
  current?: string;
  recommended?: string;
  estimated_savings?: number;
  reason?: string;
}>): string {
  if (recommendations.length === 0) {
    return chalk.green(`${icons.success} No cost optimization recommendations at this time.\n`) +
           chalk.gray('Your workspaces are already optimized!');
  }

  const table = new Table({
    head: [
      chalk.cyan('Workspace'),
      chalk.cyan('Type'),
      chalk.cyan('Current'),
      chalk.cyan('Recommended'),
      chalk.cyan(`${icons.money} Savings/mo`),
    ],
    colWidths: [15, 15, 20, 20, 18],
  });

  for (const rec of recommendations) {
    table.push([
      rec.workspace_id || 'N/A',
      rec.type || 'N/A',
      rec.current || 'N/A',
      chalk.green(rec.recommended || 'N/A'),
      rec.estimated_savings ? formatMoney(rec.estimated_savings) : 'N/A',
    ]);
  }

  return chalk.bold(`\n${icons.chart} Cost Optimization Recommendations:\n`) + table.toString();
}

/**
 * Format output based on format preference
 */
export function formatOutput(data: unknown, format: 'table' | 'json'): string {
  if (format === 'json') {
    return JSON.stringify(data, null, 2);
  }

  // For table format, use specific formatters based on data type
  if (Array.isArray(data) && data.length > 0 && 'workspace_id' in data[0]) {
    return formatWorkspaceTable(data as Workspace[]);
  }

  if (typeof data === 'object' && data !== null && 'workspace_id' in data) {
    return formatWorkspaceDetails(data as Workspace);
  }

  if (typeof data === 'object' && data !== null && 'total_cost' in data) {
    return formatCostSummary(data as CostSummary);
  }

  // Default to JSON for unknown types
  return JSON.stringify(data, null, 2);
}

/**
 * Create a loading spinner message
 */
export function createSpinnerText(action: string, resource?: string): string {
  if (resource) {
    return `${action} ${resource}...`;
  }
  return `${action}...`;
}
