/**
 * Color and styling utilities with --no-color support
 * 
 * Requirements: 17.1
 */

import chalk from 'chalk';

// Check if colors should be disabled
const shouldDisableColors = process.argv.includes('--no-color') || process.env.NO_COLOR === '1';

if (shouldDisableColors) {
  chalk.level = 0; // Disable all colors
}

/**
 * Icons for visual clarity
 */
export const icons = {
  success: '✓',
  error: '✗',
  warning: '⚠',
  info: 'ℹ',
  rocket: '🚀',
  money: '💰',
  chart: '📊',
  workspace: '💻',
  clock: '⏱',
  check: '✓',
  cross: '✗',
  bullet: '•',
  arrow: '→',
};

/**
 * Status indicators with colors and icons
 */
export const statusIndicators = {
  success: chalk.green(`${icons.success}`),
  error: chalk.red(`${icons.error}`),
  warning: chalk.yellow(`${icons.warning}`),
  info: chalk.cyan(`${icons.info}`),
};

/**
 * Themed chalk instances for consistent styling
 */
export const theme = {
  // Text colors
  primary: chalk.cyan,
  success: chalk.green,
  warning: chalk.yellow,
  error: chalk.red,
  muted: chalk.gray,
  highlight: chalk.bold,
  
  // Semantic colors
  label: chalk.cyan,
  value: chalk.white,
  money: chalk.green,
  
  // Status colors
  available: chalk.green,
  starting: chalk.yellow,
  stopping: chalk.yellow,
  stopped: chalk.gray,
  failed: chalk.red,
};

/**
 * Format a success message with icon
 */
export function formatSuccess(message: string): string {
  return `${statusIndicators.success} ${chalk.green(message)}`;
}

/**
 * Format an error message with icon
 */
export function formatError(message: string): string {
  return `${statusIndicators.error} ${chalk.red(message)}`;
}

/**
 * Format a warning message with icon
 */
export function formatWarning(message: string): string {
  return `${statusIndicators.warning} ${chalk.yellow(message)}`;
}

/**
 * Format an info message with icon
 */
export function formatInfo(message: string): string {
  return `${statusIndicators.info} ${chalk.cyan(message)}`;
}

/**
 * Format a label-value pair
 */
export function formatLabelValue(label: string, value: string): string {
  return `${theme.label(label)} ${theme.value(value)}`;
}

/**
 * Format a money amount
 */
export function formatMoney(amount: number): string {
  return theme.money(`$${amount.toFixed(2)}`);
}

/**
 * Check if colors are enabled
 */
export function areColorsEnabled(): boolean {
  return chalk.level > 0;
}
