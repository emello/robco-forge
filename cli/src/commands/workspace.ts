/**
 * Workspace management commands
 * 
 * Requirements: 17.2, 17.3, 17.4
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { createForgeClient } from '../api';
import { getAuthToken, getUserId, requireAuth } from '../api/auth';
import { getConfig } from '../config';
import { withErrorHandling, createMissingOptionError, createValidationError } from '../utils/errors';
import { formatOutput, formatWorkspaceDetails, createSpinnerText } from '../utils/format';
import { icons, formatSuccess, formatError, formatWarning } from '../utils/colors';
import { BundleType, OperatingSystem } from '../types';

/**
 * Create workspace management command
 */
export function createWorkspaceCommand(): Command {
  const command = new Command('workspace')
    .alias('ws')
    .description('Manage workspaces');

  // Add subcommands
  command.addCommand(createLaunchCommand());
  command.addCommand(createListCommand());
  command.addCommand(createDescribeCommand());
  command.addCommand(createStartCommand());
  command.addCommand(createStopCommand());
  command.addCommand(createTerminateCommand());

  return command;
}

/**
 * Launch command - Provision a new workspace
 */
function createLaunchCommand(): Command {
  return new Command('launch')
    .description('Provision a new workspace')
    .option('-b, --bundle <type>', 'Bundle type (STANDARD, PERFORMANCE, POWER, POWERPRO, GRAPHICS_G4DN, GRAPHICSPRO_G4DN)')
    .option('-o, --os <os>', 'Operating system (Windows, Linux)')
    .option('-p, --blueprint <id>', 'Blueprint ID')
    .option('-r, --region <region>', 'AWS region')
    .option('-t, --tags <tags>', 'Tags as JSON string')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        // Get bundle type
        const bundleType = options.bundle || config.defaultBundle;
        if (!bundleType) {
          createMissingOptionError(
            '--bundle',
            'Bundle type is required to provision a workspace.',
            'forge launch --bundle STANDARD --os Linux'
          );
        }

        // Validate bundle type
        if (!Object.values(BundleType).includes(bundleType as BundleType)) {
          throw createValidationError(
            'bundle type',
            `Must be one of: ${Object.values(BundleType).join(', ')}`,
            'forge launch --bundle STANDARD'
          );
        }

        // Get OS
        const os = options.os || config.defaultOs || OperatingSystem.LINUX;
        if (!Object.values(OperatingSystem).includes(os as OperatingSystem)) {
          throw createValidationError(
            'operating system',
            `Must be one of: ${Object.values(OperatingSystem).join(', ')}`,
            'forge launch --os Linux'
          );
        }

        // Parse tags if provided
        let tags: Record<string, string> | undefined;
        if (options.tags) {
          try {
            tags = JSON.parse(options.tags as string) as Record<string, string>;
          } catch (error) {
            throw createValidationError(
              'tags',
              'Tags must be valid JSON',
              'forge launch --tags \'{"project":"demo","team":"engineering"}\''
            );
          }
        }

        const spinner = ora(createSpinnerText('Provisioning workspace')).start();

        try {
          const workspace = await client.provisionWorkspace({
            bundle_type: bundleType as BundleType,
            operating_system: os as OperatingSystem,
            blueprint_id: options.blueprint as string | undefined,
            region: options.region as string | undefined,
            tags,
          });

          spinner.succeed(formatSuccess('Workspace provisioned successfully!'));
          console.log(formatWorkspaceDetails(workspace));
          console.log(
            '\n' +
              formatWarning('Note: Workspace may take a few minutes to become available.')
          );
        } catch (error) {
          spinner.fail(chalk.red('Failed to provision workspace'));
          throw error;
        }
      })
    );
}

/**
 * List command - List workspaces
 */
function createListCommand(): Command {
  return new Command('list')
    .alias('ls')
    .description('List your workspaces')
    .option('-s, --status <status>', 'Filter by status')
    .option('-b, --bundle <type>', 'Filter by bundle type')
    .option('-l, --limit <number>', 'Limit number of results', '50')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Fetching workspaces')).start();

        try {
          const workspaces = await client.listWorkspaces({
            status: options.status as string | undefined,
            bundle_type: options.bundle as BundleType | undefined,
            limit: parseInt(options.limit as string, 10),
          });

          spinner.stop();

          const format = options.json ? 'json' : config.outputFormat || 'table';
          console.log(formatOutput(workspaces, format));
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch workspaces'));
          throw error;
        }
      })
    );
}

/**
 * Describe command - Get workspace details
 */
function createDescribeCommand(): Command {
  return new Command('describe')
    .description('Get workspace details')
    .argument('<workspace-id>', 'Workspace ID')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (workspaceId: string, options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Fetching workspace details', workspaceId)).start();

        try {
          const workspace = await client.getWorkspace(workspaceId);
          spinner.stop();

          const format = options.json ? 'json' : config.outputFormat || 'table';
          console.log(formatOutput(workspace, format));
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch workspace details'));
          throw error;
        }
      })
    );
}

/**
 * Start command - Start a workspace
 */
function createStartCommand(): Command {
  return new Command('start')
    .description('Start a workspace')
    .argument('<workspace-id>', 'Workspace ID')
    .action(
      withErrorHandling(async (workspaceId: string) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Starting workspace', workspaceId)).start();

        try {
          const workspace = await client.startWorkspace(workspaceId);
          spinner.succeed(formatSuccess(`Workspace ${workspaceId} is starting`));
          console.log(formatWorkspaceDetails(workspace));
        } catch (error) {
          spinner.fail(chalk.red('Failed to start workspace'));
          throw error;
        }
      })
    );
}

/**
 * Stop command - Stop a workspace
 */
function createStopCommand(): Command {
  return new Command('stop')
    .description('Stop a workspace')
    .argument('<workspace-id>', 'Workspace ID')
    .action(
      withErrorHandling(async (workspaceId: string) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Stopping workspace', workspaceId)).start();

        try {
          const workspace = await client.stopWorkspace(workspaceId);
          spinner.succeed(formatSuccess(`Workspace ${workspaceId} is stopping`));
          console.log(formatWorkspaceDetails(workspace));
        } catch (error) {
          spinner.fail(chalk.red('Failed to stop workspace'));
          throw error;
        }
      })
    );
}

/**
 * Terminate command - Terminate a workspace
 */
function createTerminateCommand(): Command {
  return new Command('terminate')
    .alias('delete')
    .description('Terminate a workspace')
    .argument('<workspace-id>', 'Workspace ID')
    .option('-f, --force', 'Skip confirmation prompt')
    .action(
      withErrorHandling(async (workspaceId: string, options) => {
        requireAuth();

        // Confirmation prompt (unless --force)
        if (!options.force) {
          console.log(
            chalk.yellow('Warning: ') +
              `This will permanently delete workspace ${chalk.bold(workspaceId)}`
          );
          console.log(
            chalk.gray('Use --force to skip this confirmation in the future.')
          );
          
          // In a real implementation, we'd use a proper prompt library
          // For now, we'll just require --force
          console.error(
            chalk.red('\nTermination cancelled. ') +
              'Use ' +
              chalk.cyan(`forge workspace terminate ${workspaceId} --force`) +
              ' to confirm.'
          );
          process.exit(1);
        }

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Terminating workspace', workspaceId)).start();

        try {
          await client.terminateWorkspace(workspaceId);
          spinner.succeed(formatSuccess(`Workspace ${workspaceId} has been terminated`));
        } catch (error) {
          spinner.fail(formatError('Failed to terminate workspace'));
          throw error;
        }
      })
    );
}
