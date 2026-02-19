#!/usr/bin/env node

/**
 * Forge CLI - Command-line interface for RobCo Forge platform
 * 
 * Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6
 */

import { Command } from 'commander';
import { config } from 'dotenv';
import chalk from 'chalk';
import { createWorkspaceCommand } from './commands/workspace';
import { createCostsCommand } from './commands/costs';
import { createLucyCommand } from './commands/lucy';
import { createConfigCommand } from './commands/config';

// Load environment variables
config();

const program = new Command();

// CLI metadata
program
  .name('forge')
  .description('RobCo Forge - Self-service cloud engineering workstation platform')
  .version('1.0.0');

// Global options
program
  .option('--api-url <url>', 'Forge API URL', process.env.FORGE_API_URL || 'http://localhost:8000')
  .option('--no-color', 'Disable colored output')
  .option('--json', 'Output in JSON format')
  .option('--debug', 'Enable debug logging');

// Add workspace command group
program.addCommand(createWorkspaceCommand());

// Add costs command group
program.addCommand(createCostsCommand());

// Add Lucy command
program.addCommand(createLucyCommand());

// Add config command group
program.addCommand(createConfigCommand());

// Top-level convenience commands (aliases to workspace subcommands)
program
  .command('launch')
  .description('Provision a new workspace (alias for workspace launch)')
  .option('-b, --bundle <type>', 'Bundle type')
  .option('-o, --os <os>', 'Operating system')
  .option('-p, --blueprint <id>', 'Blueprint ID')
  .option('-r, --region <region>', 'AWS region')
  .option('-t, --tags <tags>', 'Tags as JSON string')
  .action(async (options) => {
    // Forward to workspace launch command
    const workspaceCmd = createWorkspaceCommand();
    const launchCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'launch');
    if (launchCmd) {
      await launchCmd.parseAsync(['node', 'forge', ...process.argv.slice(3)]);
    }
  });

program
  .command('list')
  .alias('ls')
  .description('List your workspaces (alias for workspace list)')
  .option('-s, --status <status>', 'Filter by status')
  .option('-b, --bundle <type>', 'Filter by bundle type')
  .option('-l, --limit <number>', 'Limit number of results')
  .option('--json', 'Output in JSON format')
  .action(async (options) => {
    const workspaceCmd = createWorkspaceCommand();
    const listCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'list');
    if (listCmd) {
      await listCmd.parseAsync(['node', 'forge', ...process.argv.slice(3)]);
    }
  });

program
  .command('start <workspace-id>')
  .description('Start a workspace (alias for workspace start)')
  .action(async (workspaceId: string) => {
    const workspaceCmd = createWorkspaceCommand();
    const startCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'start');
    if (startCmd) {
      await startCmd.parseAsync(['node', 'forge', workspaceId]);
    }
  });

program
  .command('stop <workspace-id>')
  .description('Stop a workspace (alias for workspace stop)')
  .action(async (workspaceId: string) => {
    const workspaceCmd = createWorkspaceCommand();
    const stopCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'stop');
    if (stopCmd) {
      await stopCmd.parseAsync(['node', 'forge', workspaceId]);
    }
  });

program
  .command('terminate <workspace-id>')
  .alias('delete')
  .description('Terminate a workspace (alias for workspace terminate)')
  .option('-f, --force', 'Skip confirmation prompt')
  .action(async (workspaceId: string, options) => {
    const workspaceCmd = createWorkspaceCommand();
    const terminateCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'terminate');
    if (terminateCmd) {
      const args = ['node', 'forge', workspaceId];
      if (options.force) args.push('--force');
      await terminateCmd.parseAsync(args);
    }
  });

program
  .command('describe <workspace-id>')
  .description('Get workspace details (alias for workspace describe)')
  .option('--json', 'Output in JSON format')
  .action(async (workspaceId: string, options) => {
    const workspaceCmd = createWorkspaceCommand();
    const describeCmd = workspaceCmd.commands.find((cmd) => cmd.name() === 'describe');
    if (describeCmd) {
      const args = ['node', 'forge', workspaceId];
      if (options.json) args.push('--json');
      await describeCmd.parseAsync(args);
    }
  });

// Placeholder commands (will be implemented in subsequent tasks)
// (None - all commands implemented!)

// Error handling
program.exitOverride();

try {
  program.parse(process.argv);
} catch (error) {
  if (error instanceof Error) {
    console.error(chalk.red('Error:'), error.message);
    process.exit(1);
  }
}

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
