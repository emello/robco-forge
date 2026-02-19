/**
 * Authentication and JWT token management
 * 
 * Requirements: 17.1
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * JWT token information
 */
export interface TokenInfo {
  token: string;
  expiresAt: number;
  userId: string;
}

/**
 * Token storage location
 */
const TOKEN_DIR = path.join(os.homedir(), '.forge');
const TOKEN_FILE = path.join(TOKEN_DIR, 'token.json');

/**
 * Token Manager
 * 
 * Manages JWT token storage and retrieval
 */
export class TokenManager {
  /**
   * Save token to disk
   */
  static saveToken(tokenInfo: TokenInfo): void {
    try {
      // Ensure directory exists
      if (!fs.existsSync(TOKEN_DIR)) {
        fs.mkdirSync(TOKEN_DIR, { recursive: true, mode: 0o700 });
      }

      // Write token file with restricted permissions
      fs.writeFileSync(TOKEN_FILE, JSON.stringify(tokenInfo, null, 2), {
        mode: 0o600,
      });
    } catch (error) {
      throw new Error(`Failed to save token: ${(error as Error).message}`);
    }
  }

  /**
   * Load token from disk
   */
  static loadToken(): TokenInfo | null {
    try {
      if (!fs.existsSync(TOKEN_FILE)) {
        return null;
      }

      const data = fs.readFileSync(TOKEN_FILE, 'utf-8');
      const tokenInfo = JSON.parse(data) as TokenInfo;

      // Check if token is expired
      if (this.isTokenExpired(tokenInfo)) {
        this.clearToken();
        return null;
      }

      return tokenInfo;
    } catch (error) {
      // If token file is corrupted, clear it
      this.clearToken();
      return null;
    }
  }

  /**
   * Clear token from disk
   */
  static clearToken(): void {
    try {
      if (fs.existsSync(TOKEN_FILE)) {
        fs.unlinkSync(TOKEN_FILE);
      }
    } catch (error) {
      // Ignore errors when clearing token
    }
  }

  /**
   * Check if token is expired
   */
  static isTokenExpired(tokenInfo: TokenInfo): boolean {
    const now = Date.now();
    // Consider token expired if it expires within 5 minutes
    return tokenInfo.expiresAt - now < 5 * 60 * 1000;
  }

  /**
   * Decode JWT token (without verification)
   * This is for extracting user ID and expiration, not for security validation
   */
  static decodeToken(token: string): { userId: string; expiresAt: number } | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        return null;
      }

      // Decode payload (second part)
      const payload = JSON.parse(Buffer.from(parts[1]!, 'base64').toString('utf-8'));

      return {
        userId: payload.sub || payload.user_id || '',
        expiresAt: (payload.exp || 0) * 1000, // Convert to milliseconds
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Get current token if valid
   */
  static getCurrentToken(): string | null {
    const tokenInfo = this.loadToken();
    return tokenInfo ? tokenInfo.token : null;
  }

  /**
   * Get current user ID from token
   */
  static getCurrentUserId(): string | null {
    const tokenInfo = this.loadToken();
    return tokenInfo ? tokenInfo.userId : null;
  }
}

/**
 * Ensure user is authenticated
 * Throws error if no valid token exists
 */
export function requireAuth(): TokenInfo {
  const tokenInfo = TokenManager.loadToken();
  if (!tokenInfo) {
    throw new Error(
      'Not authenticated. Please run "forge login" or set FORGE_AUTH_TOKEN environment variable.'
    );
  }
  return tokenInfo;
}

/**
 * Get auth token from environment or stored token
 */
export function getAuthToken(): string | null {
  // Check environment variable first
  const envToken = process.env.FORGE_AUTH_TOKEN;
  if (envToken) {
    return envToken;
  }

  // Fall back to stored token
  return TokenManager.getCurrentToken();
}

/**
 * Get user ID from token
 */
export function getUserId(): string | null {
  // Try environment token first
  const envToken = process.env.FORGE_AUTH_TOKEN;
  if (envToken) {
    const decoded = TokenManager.decodeToken(envToken);
    return decoded ? decoded.userId : null;
  }

  // Fall back to stored token
  return TokenManager.getCurrentUserId();
}
