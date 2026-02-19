'use client';

/**
 * Login Page
 * 
 * Requirements: 8.1, 8.2
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { cn } from '@/lib/utils';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const router = useRouter();

  const handleSSOLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // In production, this would redirect to Okta SSO
      // For now, we'll simulate the SSO flow
      const oktaDomain = process.env.NEXT_PUBLIC_OKTA_DOMAIN;
      const clientId = process.env.NEXT_PUBLIC_OKTA_CLIENT_ID;

      if (!oktaDomain || !clientId) {
        throw new Error('Okta SSO is not configured');
      }

      // Redirect to Okta SSO
      const redirectUri = `${window.location.origin}/auth/callback`;
      const authUrl = `https://${oktaDomain}/oauth2/v1/authorize?client_id=${clientId}&response_type=code&scope=openid%20profile%20email&redirect_uri=${encodeURIComponent(redirectUri)}&state=${Math.random().toString(36)}`;
      
      window.location.href = authUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'SSO login failed');
      setIsLoading(false);
    }
  };

  // Demo login for development
  const handleDemoLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Create a demo JWT token
      const demoPayload = {
        sub: 'demo-user-123',
        user_id: 'demo-user-123',
        email: 'demo@robco.com',
        name: 'Demo User',
        role: 'engineer',
        team_id: 'team-demo',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 86400, // 24 hours
      };

      // Create a fake JWT (header.payload.signature)
      const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
      const payload = btoa(JSON.stringify(demoPayload));
      const signature = 'demo-signature';
      const demoToken = `${header}.${payload}.${signature}`;

      await login(demoToken);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo login failed');
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">RobCo Forge</h1>
          <p className="text-lg opacity-70">Self-service cloud engineering workstations</p>
        </div>

        <div className="space-y-4 p-8 border rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold text-center mb-6">Sign In</h2>

          {error && (
            <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <button
            onClick={handleSSOLogin}
            disabled={isLoading}
            className={cn(
              'w-full py-3 px-4 rounded-lg font-medium transition-colors',
              'bg-primary-600 text-white hover:bg-primary-700',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isLoading ? 'Redirecting...' : 'Sign in with Okta SSO'}
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white dark:bg-gray-900">Or</span>
            </div>
          </div>

          <button
            onClick={handleDemoLogin}
            disabled={isLoading}
            className={cn(
              'w-full py-3 px-4 rounded-lg font-medium transition-colors',
              'border-2 hover:bg-gray-100 dark:hover:bg-gray-800',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            {isLoading ? 'Signing in...' : 'Demo Login (Development)'}
          </button>

          <p className="text-sm text-center opacity-70 mt-4">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
