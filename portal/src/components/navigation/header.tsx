'use client';

/**
 * Header Component
 * 
 * Requirements: 22.1
 */

import { useAuth } from '@/contexts/auth-context';
import { useTheme } from '@/contexts/theme-context';
import { ThemeToggle } from '@/components/theme-toggle';
import { cn } from '@/lib/utils';

export function Header() {
  const { user, logout } = useAuth();
  const { theme } = useTheme();

  return (
    <header
      className={cn(
        'border-b p-4 flex justify-between items-center',
        theme === 'retro' && 'retro-border bg-retro-bg'
      )}
    >
      <div>
        <h2 className={cn('text-xl font-semibold', theme === 'retro' && 'retro-glow font-retro')}>
          Welcome back, {user?.name}
        </h2>
        <p className={cn('text-sm opacity-70', theme === 'retro' && 'text-retro-dim')}>
          {user?.email} • {user?.role}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <ThemeToggle />
        
        <button
          onClick={logout}
          className={cn(
            'px-4 py-2 rounded-lg font-medium transition-colors',
            theme === 'retro'
              ? 'retro-border text-retro-text hover:bg-retro-dim'
              : 'border hover:bg-gray-100 dark:hover:bg-gray-800'
          )}
        >
          Sign Out
        </button>
      </div>
    </header>
  );
}
