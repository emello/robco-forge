/**
 * Configuration management
 * 
 * Requirements: 17.1
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { CliConfig, BundleType, OperatingSystem } from '../types';

/**
 * Configuration file location
 */
const CONFIG_DIR = path.join(os.homedir(), '.forge');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

/**
 * Default configuration
 */
const DEFAULT_CONFIG: CliConfig = {
  apiUrl: process.env.FORGE_API_URL || 'http://localhost:8000',
  outputFormat: 'table',
  debug: false,
};

/**
 * Configuration Manager
 * 
 * Manages CLI configuration storage and retrieval
 */
export class ConfigManager {
  /**
   * Load configuration from disk
   */
  static loadConfig(): CliConfig {
    try {
      if (!fs.existsSync(CONFIG_FILE)) {
        return { ...DEFAULT_CONFIG };
      }

      const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
      const config = JSON.parse(data) as Partial<CliConfig>;

      // Merge with defaults
      return {
        ...DEFAULT_CONFIG,
        ...config,
      };
    } catch (error) {
      // If config file is corrupted, return defaults
      return { ...DEFAULT_CONFIG };
    }
  }

  /**
   * Save configuration to disk
   */
  static saveConfig(config: CliConfig): void {
    try {
      // Ensure directory exists
      if (!fs.existsSync(CONFIG_DIR)) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true, mode: 0o700 });
      }

      // Write config file
      fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), {
        mode: 0o600,
      });
    } catch (error) {
      throw new Error(`Failed to save configuration: ${(error as Error).message}`);
    }
  }

  /**
   * Get a configuration value
   */
  static get(key: keyof CliConfig): unknown {
    const config = this.loadConfig();
    return config[key];
  }

  /**
   * Set a configuration value
   */
  static set(key: keyof CliConfig, value: unknown): void {
    const config = this.loadConfig();
    
    // Validate value based on key
    switch (key) {
      case 'apiUrl':
        if (typeof value !== 'string') {
          throw new Error('API URL must be a string');
        }
        config.apiUrl = value;
        break;
      
      case 'authToken':
        if (typeof value !== 'string' && value !== undefined) {
          throw new Error('Auth token must be a string');
        }
        config.authToken = value as string | undefined;
        break;
      
      case 'defaultBundle':
        if (!Object.values(BundleType).includes(value as BundleType)) {
          throw new Error(`Invalid bundle type. Must be one of: ${Object.values(BundleType).join(', ')}`);
        }
        config.defaultBundle = value as BundleType;
        break;
      
      case 'defaultOs':
        if (!Object.values(OperatingSystem).includes(value as OperatingSystem)) {
          throw new Error(`Invalid OS. Must be one of: ${Object.values(OperatingSystem).join(', ')}`);
        }
        config.defaultOs = value as OperatingSystem;
        break;
      
      case 'outputFormat':
        if (value !== 'table' && value !== 'json') {
          throw new Error('Output format must be "table" or "json"');
        }
        config.outputFormat = value;
        break;
      
      case 'debug':
        if (typeof value !== 'boolean') {
          throw new Error('Debug must be a boolean');
        }
        config.debug = value;
        break;
      
      default:
        throw new Error(`Unknown configuration key: ${key}`);
    }

    this.saveConfig(config);
  }

  /**
   * List all configuration values
   */
  static list(): CliConfig {
    return this.loadConfig();
  }

  /**
   * Reset configuration to defaults
   */
  static reset(): void {
    this.saveConfig({ ...DEFAULT_CONFIG });
  }

  /**
   * Delete configuration file
   */
  static delete(): void {
    try {
      if (fs.existsSync(CONFIG_FILE)) {
        fs.unlinkSync(CONFIG_FILE);
      }
    } catch (error) {
      throw new Error(`Failed to delete configuration: ${(error as Error).message}`);
    }
  }
}

/**
 * Get configuration with environment variable overrides
 */
export function getConfig(): CliConfig {
  const config = ConfigManager.loadConfig();

  // Override with environment variables
  if (process.env.FORGE_API_URL) {
    config.apiUrl = process.env.FORGE_API_URL;
  }
  if (process.env.FORGE_AUTH_TOKEN) {
    config.authToken = process.env.FORGE_AUTH_TOKEN;
  }
  if (process.env.FORGE_DEFAULT_BUNDLE) {
    config.defaultBundle = process.env.FORGE_DEFAULT_BUNDLE as BundleType;
  }
  if (process.env.FORGE_DEFAULT_OS) {
    config.defaultOs = process.env.FORGE_DEFAULT_OS as OperatingSystem;
  }
  if (process.env.FORGE_OUTPUT_FORMAT) {
    config.outputFormat = process.env.FORGE_OUTPUT_FORMAT as 'table' | 'json';
  }
  if (process.env.DEBUG === 'true') {
    config.debug = true;
  }

  return config;
}
