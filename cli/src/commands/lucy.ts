/**
 * Lucy AI integration command
 * 
 * Requirements: 17.6
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { createForgeClient } from '../api';
import { getAuthToken, getUserId, requireAuth } from '../api/auth';
import { getConfig } from '../config';
import { withErrorHandling } from '../utils/errors';
import { icons, formatSuccess, formatWarning } from '../utils/colors';

/**
 * Create Lucy command
 */
export function createLucyCommand(): Command {
  const command = new Command('ask')
    .description('Ask Lucy a question')
    .argument('<question>', 'Question to ask Lucy')
    .option('--clear', 'Clear conversation context before asking')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (question: string, options) => {
        requireAuth();

        const userId = getUserId();
        if (!userId) {
          console.error(
            chalk.red('Error: ') + 'Could not determine user ID from authentication token'
          );
          process.exit(1);
        }

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        // Clear context if requested
        if (options.clear) {
          const clearSpinner = ora('Clearing conversation context...').start();
          try {
            await client.clearLucyContext(userId);
            clearSpinner.succeed(chalk.gray('Conversation context cleared'));
          } catch (error) {
            clearSpinner.fail(chalk.yellow('Failed to clear context (continuing anyway)'));
          }
        }

        const spinner = ora('Lucy is thinking...').start();

        try {
          const response = await client.chatWithLucy(question, userId);

          spinner.stop();

          if (options.json) {
            console.log(JSON.stringify(response, null, 2));
          } else {
            // Display Lucy's response
            console.log(chalk.bold(`\n${icons.info} Lucy:`));
            console.log(response.response);

            // Show additional info if available
            if (response.intent) {
              console.log(chalk.gray(`\n(Intent: ${response.intent})`));
            }

            if (response.tool_executed) {
              console.log(chalk.gray(`(Tool executed: ${response.tool_executed})`));
            }

            if (response.requires_confirmation) {
              console.log(
                '\n' +
                  formatWarning('This action requires confirmation. Please confirm to proceed.')
              );
            }
          }
        } catch (error) {
          spinner.fail(chalk.red('Failed to get response from Lucy'));
          throw error;
        }
      })
    );

  // Add context management subcommands
  command
    .command('context')
    .description('View conversation context')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const userId = getUserId();
        if (!userId) {
          console.error(
            chalk.red('Error: ') + 'Could not determine user ID from authentication token'
          );
          process.exit(1);
        }

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora('Fetching conversation context...').start();

        try {
          const context = await client.getLucyContext(userId);
          spinner.stop();

          if (options.json) {
            console.log(JSON.stringify(context, null, 2));
          } else {
            console.log(chalk.bold('\nConversation Context:'));
            console.log(JSON.stringify(context, null, 2));
          }
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch conversation context'));
          throw error;
        }
      })
    );

  command
    .command('clear')
    .description('Clear conversation context')
    .action(
      withErrorHandling(async () => {
        requireAuth();

        const userId = getUserId();
        if (!userId) {
          console.error(
            chalk.red('Error: ') + 'Could not determine user ID from authentication token'
          );
          process.exit(1);
        }

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora('Clearing conversation context...').start();

        try {
          await client.clearLucyContext(userId);
          spinner.succeed(formatSuccess('Conversation context cleared'));
        } catch (error) {
          spinner.fail(chalk.red('Failed to clear conversation context'));
          throw error;
        }
      })
    );

  return command;
}
