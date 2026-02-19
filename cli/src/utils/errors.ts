/**
 * Error handling utilities
 * 
 * Requirements: 22.5
 */

import chalk from 'chalk';
import { ApiError } from '../types';
import { icons, formatError, formatWarning } from './colors';

/**
 * Error code to user-friendly message mapping
 */
const ERROR_MESSAGES: Record<string, { message: string; suggestion: string; example?: string }> = {
  // Authentication errors
  'AUTH_REQUIRED': {
    message: 'Authentication required',
    suggestion: 'Please log in to continue',
    example: 'forge login',
  },
  'AUTH_INVALID': {
    message: 'Invalid authentication token',
    suggestion: 'Your session may have expired. Please log in again',
    example: 'forge login',
  },
  'AUTH_EXPIRED': {
    message: 'Authentication token expired',
    suggestion: 'Please log in again',
    example: 'forge login',
  },
  
  // Authorization errors
  'PERMISSION_DENIED': {
    message: 'Permission denied',
    suggestion: 'You do not have permission to perform this action. Contact your team lead if you need access.',
  },
  'RBAC_DENIED': {
    message: 'Access denied by role-based access control',
    suggestion: 'Your role does not allow this action. Contact your administrator for access.',
  },
  
  // Budget errors
  'BUDGET_EXCEEDED': {
    message: 'Budget limit exceeded',
    suggestion: 'You have reached your budget limit. Contact your team lead to request a budget increase.',
    example: 'forge costs budget',
  },
  'BUDGET_WARNING': {
    message: 'Approaching budget limit',
    suggestion: 'You are approaching your budget limit. Review your costs and consider optimizing.',
    example: 'forge costs recommendations',
  },
  
  // Resource errors
  'WORKSPACE_NOT_FOUND': {
    message: 'Workspace not found',
    suggestion: 'The workspace ID may be incorrect. List your workspaces to find the correct ID.',
    example: 'forge list',
  },
  'BLUEPRINT_NOT_FOUND': {
    message: 'Blueprint not found',
    suggestion: 'The blueprint ID may be incorrect or you may not have access to it.',
    example: 'forge blueprints list',
  },
  'WORKSPACE_ALREADY_EXISTS': {
    message: 'Workspace already exists',
    suggestion: 'A workspace with this configuration already exists. List your workspaces to see it.',
    example: 'forge list',
  },
  
  // State errors
  'INVALID_STATE': {
    message: 'Invalid workspace state',
    suggestion: 'The workspace is not in the correct state for this operation. Check its current status.',
    example: 'forge describe <workspace-id>',
  },
  'WORKSPACE_NOT_STOPPED': {
    message: 'Workspace must be stopped',
    suggestion: 'Stop the workspace before performing this action.',
    example: 'forge stop <workspace-id>',
  },
  'WORKSPACE_NOT_AVAILABLE': {
    message: 'Workspace is not available',
    suggestion: 'Wait for the workspace to become available before connecting.',
    example: 'forge describe <workspace-id>',
  },
  
  // Capacity errors
  'CAPACITY_UNAVAILABLE': {
    message: 'Capacity unavailable',
    suggestion: 'The requested bundle type is not available in this region. Try a different region or bundle type.',
    example: 'forge launch --region us-west-2 --bundle STANDARD',
  },
  'REGION_UNAVAILABLE': {
    message: 'Region unavailable',
    suggestion: 'The requested region is not available. Try a different region.',
  },
  
  // Validation errors
  'INVALID_BUNDLE_TYPE': {
    message: 'Invalid bundle type',
    suggestion: 'Valid bundle types: STANDARD, PERFORMANCE, POWER, POWERPRO, GRAPHICS_G4DN, GRAPHICSPRO_G4DN',
    example: 'forge launch --bundle STANDARD',
  },
  'INVALID_OS': {
    message: 'Invalid operating system',
    suggestion: 'Valid operating systems: Windows, Linux',
    example: 'forge launch --os Linux',
  },
  'INVALID_REGION': {
    message: 'Invalid region',
    suggestion: 'Specify a valid AWS region.',
    example: 'forge launch --region us-east-1',
  },
  
  // Rate limiting
  'RATE_LIMIT_EXCEEDED': {
    message: 'Rate limit exceeded',
    suggestion: 'You have made too many requests. Please wait a moment and try again.',
  },
  'PROVISIONING_LIMIT_EXCEEDED': {
    message: 'Provisioning limit exceeded',
    suggestion: 'You have reached the maximum number of workspace provisioning requests per hour.',
  },
  
  // Network errors
  'NETWORK_ERROR': {
    message: 'Network error',
    suggestion: 'Cannot connect to the API. Check your network connection and API URL.',
    example: 'forge config get apiUrl',
  },
  'TIMEOUT': {
    message: 'Request timeout',
    suggestion: 'The request took too long. Please try again.',
  },
  
  // Server errors
  'INTERNAL_ERROR': {
    message: 'Internal server error',
    suggestion: 'The server encountered an error. Please try again later or contact support.',
  },
  'SERVICE_UNAVAILABLE': {
    message: 'Service unavailable',
    suggestion: 'The service is temporarily unavailable. Please try again later.',
  },
};

/**
 * Format API error for display with helpful suggestions
 */
export function formatApiError(error: ApiError): string {
  let message = formatError(error.message);

  if (error.status_code) {
    message += chalk.gray(` (HTTP ${error.status_code})`);
  }

  // Try to find a specific error code mapping
  const errorCode = error.error || getErrorCodeFromStatus(error.status_code);
  const errorInfo = ERROR_MESSAGES[errorCode];

  if (errorInfo) {
    message += '\n\n' + chalk.bold('What happened:');
    message += '\n' + errorInfo.message;
    
    message += '\n\n' + chalk.bold('What to do:');
    message += '\n' + errorInfo.suggestion;
    
    if (errorInfo.example) {
      message += '\n\n' + chalk.bold('Example:');
      message += '\n' + chalk.cyan(errorInfo.example);
    }
  }

  if (error.details) {
    message += '\n\n' + chalk.bold('Details:');
    message += '\n' + chalk.gray(JSON.stringify(error.details, null, 2));
  }

  return message;
}

/**
 * Get error code from HTTP status code
 */
function getErrorCodeFromStatus(statusCode?: number): string {
  if (!statusCode) return 'UNKNOWN_ERROR';
  
  if (statusCode === 401) return 'AUTH_REQUIRED';
  if (statusCode === 403) return 'PERMISSION_DENIED';
  if (statusCode === 404) return 'WORKSPACE_NOT_FOUND';
  if (statusCode === 429) return 'RATE_LIMIT_EXCEEDED';
  if (statusCode >= 500) return 'INTERNAL_ERROR';
  if (statusCode === 0) return 'NETWORK_ERROR';
  
  return 'UNKNOWN_ERROR';
}

/**
 * Handle error and display to user with helpful context
 */
export function handleError(error: unknown): void {
  if (isApiError(error)) {
    console.error('\n' + formatApiError(error));
  } else if (error instanceof Error) {
    console.error('\n' + formatError(error.message));
    
    // Provide context for common error patterns
    if (error.message.includes('ECONNREFUSED')) {
      console.error('\n' + formatWarning('Cannot connect to the API server.'));
      console.error(chalk.gray('Check that the API URL is correct:'));
      console.error(chalk.cyan('  forge config get apiUrl'));
    } else if (error.message.includes('ENOTFOUND')) {
      console.error('\n' + formatWarning('Cannot resolve API hostname.'));
      console.error(chalk.gray('Check your network connection and API URL.'));
    } else if (error.message.includes('ETIMEDOUT')) {
      console.error('\n' + formatWarning('Request timed out.'));
      console.error(chalk.gray('The server may be slow or unreachable. Try again later.'));
    }
  } else {
    console.error('\n' + formatError('An unexpected error occurred'));
    console.error(chalk.gray('Please try again or contact support if the problem persists.'));
  }
  
  // Add general help footer
  console.error('\n' + chalk.gray('For more help, run: ') + chalk.cyan('forge --help'));
}

/**
 * Type guard for API errors
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    'message' in error &&
    'status_code' in error
  );
}

/**
 * Wrap async command handler with error handling
 */
export function withErrorHandling<T extends unknown[]>(
  handler: (...args: T) => Promise<void>
): (...args: T) => Promise<void> {
  return async (...args: T): Promise<void> => {
    try {
      await handler(...args);
    } catch (error) {
      handleError(error);
      process.exit(1);
    }
  };
}

/**
 * Create a validation error with helpful message
 */
export function createValidationError(field: string, issue: string, example?: string): Error {
  let message = `Invalid ${field}: ${issue}`;
  
  if (example) {
    message += `\n\nExample: ${example}`;
  }
  
  return new Error(message);
}

/**
 * Create a user-friendly error for missing required options
 */
export function createMissingOptionError(option: string, description: string, example?: string): void {
  console.error(formatError(`Missing required option: ${option}`));
  console.error('\n' + chalk.bold('What you need:'));
  console.error(description);
  
  if (example) {
    console.error('\n' + chalk.bold('Example:'));
    console.error(chalk.cyan(example));
  }
  
  console.error('\n' + chalk.gray('For more help, run: ') + chalk.cyan('forge --help'));
  process.exit(1);
}

/**
 * Format a list of suggestions
 */
export function formatSuggestions(title: string, suggestions: string[]): string {
  let message = chalk.bold(title) + '\n';
  
  for (const suggestion of suggestions) {
    message += `  ${icons.bullet} ${suggestion}\n`;
  }
  
  return message;
}
