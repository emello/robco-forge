/**
 * Configuration management commands
 * 
 * Requirements: 17.1
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { ConfigManager } from '../config';
import { withErrorHandling } from '../utils/errors';
import { CliConfig } from '../types';
import { icons, formatSuccess, formatWarning } from '../utils/colors';

/**
 * Create config command
 */
export function createConfigCommand(): Command {
  const command = new Command('config')
    .description('Manage CLI configuration');

  // Add subcommands
  command.addCommand(createSetCommand());
  command.addCommand(createGetCommand());
  command.addCommand(createListCommand());
  command.addCommand(createResetCommand());

  return command;
}

/**
 * Set command - Set a configuration value
 */
function createSetCommand(): Command {
  return new Command('set')
    .description('Set a configuration value')
    .argument('<key>', 'Configuration key')
    .argument('<value>', 'Configuration value')
    .action(
      withErrorHandling(async (key: string, value: string) => {
        try {
          // Convert string value to appropriate type
          let parsedValue: unknown = value;

          if (key === 'debug') {
            parsedValue = value.toLowerCase() === 'true';
          }

          ConfigManager.set(key as keyof CliConfig, parsedValue);
          console.log(formatSuccess('Configuration updated'));
          console.log(chalk.cyan(key) + ' = ' + chalk.white(value));
        } catch (error) {
          if (error instanceof Error) {
            console.error(chalk.red('Error: ') + error.message);
            console.log(
              '\n' +
                chalk.gray('Valid configuration keys:') +
                '\n  - apiUrl (string)' +
                '\n  - authToken (string)' +
                '\n  - defaultBundle (STANDARD, PERFORMANCE, POWER, POWERPRO, GRAPHICS_G4DN, GRAPHICSPRO_G4DN)' +
                '\n  - defaultOs (Windows, Linux)' +
                '\n  - outputFormat (table, json)' +
                '\n  - debug (true, false)'
            );
            process.exit(1);
          }
          throw error;
        }
      })
    );
}

/**
 * Get command - Get a configuration value
 */
function createGetCommand(): Command {
  return new Command('get')
    .description('Get a configuration value')
    .argument('<key>', 'Configuration key')
    .action(
      withErrorHandling(async (key: string) => {
        try {
          const value = ConfigManager.get(key as keyof CliConfig);
          
          if (value === undefined) {
            console.log(chalk.gray('(not set)'));
          } else {
            console.log(chalk.white(String(value)));
          }
        } catch (error) {
          if (error instanceof Error) {
            console.error(chalk.red('Error: ') + error.message);
            process.exit(1);
          }
          throw error;
        }
      })
    );
}

/**
 * List command - List all configuration values
 */
function createListCommand(): Command {
  return new Command('list')
    .alias('ls')
    .description('List all configuration values')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        const config = ConfigManager.list();

        if (options.json) {
          console.log(JSON.stringify(config, null, 2));
        } else {
          const table = new Table({
            head: [chalk.cyan('Key'), chalk.cyan('Value')],
            colWidths: [20, 60],
          });

          for (const [key, value] of Object.entries(config)) {
            const displayValue = value === undefined ? chalk.gray('(not set)') : String(value);
            table.push([key, displayValue]);
          }

          console.log(chalk.bold('\nConfiguration:\n'));
          console.log(table.toString());
          console.log(
            '\n' +
              chalk.gray('Note: ') +
              'Environment variables override these settings.'
          );
        }
      })
    );
}

/**
 * Reset command - Reset configuration to defaults
 */
function createResetCommand(): Command {
  return new Command('reset')
    .description('Reset configuration to defaults')
    .option('-f, --force', 'Skip confirmation prompt')
    .action(
      withErrorHandling(async (options) => {
        if (!options.force) {
          console.log(
            formatWarning('This will reset all configuration to default values.')
          );
          console.log(
            chalk.gray('Use --force to skip this confirmation.')
          );
          console.error(
            chalk.red('\nReset cancelled. ') +
              'Use ' +
              chalk.cyan('forge config reset --force') +
              ' to confirm.'
          );
          process.exit(1);
        }

        try {
          ConfigManager.reset();
          console.log(formatSuccess('Configuration reset to defaults'));
        } catch (error) {
          if (error instanceof Error) {
            console.error(chalk.red('Error: ') + error.message);
            process.exit(1);
          }
          throw error;
        }
      })
    );
}
