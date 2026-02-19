#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ForgeApiStack } from '../lib/stacks/forge-api-stack';
import { ForgeLucyStack } from '../lib/stacks/forge-lucy-stack';
import { ForgeCostEngineStack } from '../lib/stacks/forge-cost-engine-stack';
import { ForgeMonitoringStack } from '../lib/stacks/forge-monitoring-stack';

const app = new cdk.App();

// Get environment from context or default to 'dev'
const environment = app.node.tryGetContext('environment') || 'dev';
const envConfig = app.node.tryGetContext('environments')?.[environment];

if (!envConfig) {
  throw new Error(`Environment configuration not found for: ${environment}`);
}

const env = {
  account: envConfig.account,
  region: envConfig.region,
};

// Common tags for all stacks
const tags = {
  Project: 'RobCo Forge',
  Environment: environment,
  ManagedBy: 'AWS CDK',
};

// Deploy Forge API Stack
const apiStack = new ForgeApiStack(app, `ForgeApiStack-${environment}`, {
  env,
  description: `RobCo Forge API services for ${environment}`,
  clusterName: envConfig.clusterName,
  namespace: envConfig.namespace.api,
  eksClusterArn: envConfig.eksClusterArn,
  eksOidcProviderArn: envConfig.eksOidcProviderArn,
  secretsManagerArn: envConfig.secretsManagerArn,
});

// Deploy Lucy AI Service Stack
const lucyStack = new ForgeLucyStack(app, `ForgeLucyStack-${environment}`, {
  env,
  description: `RobCo Forge Lucy AI service for ${environment}`,
  clusterName: envConfig.clusterName,
  namespace: envConfig.namespace.api,
  eksClusterArn: envConfig.eksClusterArn,
  eksOidcProviderArn: envConfig.eksOidcProviderArn,
  secretsManagerArn: envConfig.secretsManagerArn,
});

// Deploy Cost Engine Stack
const costEngineStack = new ForgeCostEngineStack(app, `ForgeCostEngineStack-${environment}`, {
  env,
  description: `RobCo Forge Cost Engine for ${environment}`,
  clusterName: envConfig.clusterName,
  namespace: envConfig.namespace.workers,
  eksClusterArn: envConfig.eksClusterArn,
  eksOidcProviderArn: envConfig.eksOidcProviderArn,
  secretsManagerArn: envConfig.secretsManagerArn,
});

// Deploy Monitoring Stack
const monitoringStack = new ForgeMonitoringStack(app, `ForgeMonitoringStack-${environment}`, {
  env,
  description: `RobCo Forge monitoring and observability for ${environment}`,
  clusterName: envConfig.clusterName,
  namespace: envConfig.namespace.system,
  eksClusterArn: envConfig.eksClusterArn,
  eksOidcProviderArn: envConfig.eksOidcProviderArn,
});

// Apply tags to all stacks
Object.entries(tags).forEach(([key, value]) => {
  cdk.Tags.of(apiStack).add(key, value);
  cdk.Tags.of(lucyStack).add(key, value);
  cdk.Tags.of(costEngineStack).add(key, value);
  cdk.Tags.of(monitoringStack).add(key, value);
});

app.synth();
