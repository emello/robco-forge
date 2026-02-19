'use client';

/**
 * Authentication Context
 * 
 * Requirements: 8.1, 8.2
 */

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Check for existing auth token on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('forge_auth_token');
        if (token) {
          // Decode JWT to get user info (simplified - in production, validate with backend)
          const payload = JSON.parse(atob(token.split('.')[1]));
          setUser({
            user_id: payload.sub || payload.user_id,
            email: payload.email,
            name: payload.name,
            role: payload.role,
            team_id: payload.team_id,
            created_at: payload.iat ? new Date(payload.iat * 1000).toISOString() : new Date().toISOString(),
          });
        }
      } catch (error) {
        console.error('Failed to restore auth session:', error);
        localStorage.removeItem('forge_auth_token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (token: string) => {
    try {
      // Store token
      apiClient.setAuthToken(token);
      
      // Decode JWT to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({
        user_id: payload.sub || payload.user_id,
        email: payload.email,
        name: payload.name,
        role: payload.role,
        team_id: payload.team_id,
        created_at: payload.iat ? new Date(payload.iat * 1000).toISOString() : new Date().toISOString(),
      });

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    apiClient.clearAuthToken();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
