/**
 * Cost management commands
 * 
 * Requirements: 17.5
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import { createForgeClient } from '../api';
import { getAuthToken, requireAuth } from '../api/auth';
import { getConfig } from '../config';
import { withErrorHandling } from '../utils/errors';
import { formatOutput, formatCostSummary, formatRecommendationsTable, createSpinnerText } from '../utils/format';
import { icons, formatSuccess, formatWarning, formatMoney } from '../utils/colors';

/**
 * Create costs command
 */
export function createCostsCommand(): Command {
  const command = new Command('costs')
    .description('View cost data and recommendations');

  // Add subcommands
  command.addCommand(createSummaryCommand());
  command.addCommand(createRecommendationsCommand());
  command.addCommand(createBudgetCommand());

  // Default action - show summary
  command.action(
    withErrorHandling(async (options) => {
      // Forward to summary command
      const summaryCmd = command.commands.find((cmd) => cmd.name() === 'summary');
      if (summaryCmd) {
        await summaryCmd.parseAsync(['node', 'forge', 'costs', 'summary']);
      }
    })
  );

  return command;
}

/**
 * Summary command - Get cost summary
 */
function createSummaryCommand(): Command {
  return new Command('summary')
    .description('Get cost summary')
    .option('-s, --start-date <date>', 'Start date (YYYY-MM-DD)')
    .option('-e, --end-date <date>', 'End date (YYYY-MM-DD)')
    .option('-g, --group-by <field>', 'Group by: workspace, bundle, team, project')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Fetching cost summary')).start();

        try {
          const summary = await client.getCostSummary({
            start_date: options.startDate as string | undefined,
            end_date: options.endDate as string | undefined,
            group_by: options.groupBy as 'workspace' | 'bundle' | 'team' | 'project' | undefined,
          });

          spinner.stop();

          const format = options.json ? 'json' : config.outputFormat || 'table';
          console.log(formatOutput(summary, format));
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch cost summary'));
          throw error;
        }
      })
    );
}

/**
 * Recommendations command - Get cost optimization recommendations
 */
function createRecommendationsCommand(): Command {
  return new Command('recommendations')
    .alias('rec')
    .description('Get cost optimization recommendations')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Fetching cost recommendations')).start();

        try {
          const recommendations = await client.getCostRecommendations();

          spinner.stop();

          const format = options.json ? 'json' : config.outputFormat || 'table';
          
          if (format === 'json') {
            console.log(JSON.stringify(recommendations, null, 2));
          } else {
            console.log(formatRecommendationsTable(recommendations as Array<{
              workspace_id?: string;
              type?: string;
              current?: string;
              recommended?: string;
              estimated_savings?: number;
              reason?: string;
            }>));
          }
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch cost recommendations'));
          throw error;
        }
      })
    );
}

/**
 * Budget command - Check budget status
 */
function createBudgetCommand(): Command {
  return new Command('budget')
    .description('Check budget status')
    .option('-u, --user-id <id>', 'User ID')
    .option('-t, --team-id <id>', 'Team ID')
    .option('-p, --project-id <id>', 'Project ID')
    .option('--json', 'Output in JSON format')
    .action(
      withErrorHandling(async (options) => {
        requireAuth();

        const config = getConfig();
        const client = createForgeClient({
          apiUrl: config.apiUrl,
          authToken: getAuthToken() || undefined,
        });

        const spinner = ora(createSpinnerText('Fetching budget information')).start();

        try {
          const budget = await client.getBudget({
            user_id: options.userId as string | undefined,
            team_id: options.teamId as string | undefined,
            project_id: options.projectId as string | undefined,
          });

          spinner.stop();

          const format = options.json ? 'json' : config.outputFormat || 'table';

          if (format === 'json') {
            console.log(JSON.stringify(budget, null, 2));
          } else {
            const percentUsed = (budget.current_spend / budget.amount) * 100;
            const remaining = budget.amount - budget.current_spend;

            console.log(chalk.bold(`\n${icons.money} Budget Status:\n`));
            console.log(chalk.cyan('Budget Amount:'), formatMoney(budget.amount));
            console.log(chalk.cyan('Current Spend:'), formatMoney(budget.current_spend));
            console.log(chalk.cyan('Remaining:'), formatMoney(remaining));
            console.log(chalk.cyan('Usage:'), `${percentUsed.toFixed(1)}%`);
            console.log(chalk.cyan('Period:'), budget.period);

            // Show warning if approaching limit
            if (percentUsed >= budget.threshold_limit) {
              console.log(
                '\n' +
                  formatWarning(`Budget limit reached! New workspace provisioning is blocked.`)
              );
            } else if (percentUsed >= budget.threshold_warning) {
              console.log(
                '\n' +
                  formatWarning(`You have used ${percentUsed.toFixed(1)}% of your budget.`)
              );
            } else {
              console.log('\n' + formatSuccess('Budget is healthy'));
            }
          }
        } catch (error) {
          spinner.fail(chalk.red('Failed to fetch budget information'));
          throw error;
        }
      })
    );
}
