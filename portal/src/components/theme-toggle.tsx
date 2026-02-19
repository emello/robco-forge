'use client';

/**
 * Theme Toggle Component
 * 
 * Requirements: 22.1
 */

import { useTheme } from '@/contexts/theme-context';
import { cn } from '@/lib/utils';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'rounded-lg px-4 py-2 font-medium transition-colors',
        theme === 'modern'
          ? 'bg-primary-600 text-white hover:bg-primary-700'
          : 'retro-border bg-retro-bg text-retro-text hover:bg-retro-dim retro-glow'
      )}
      aria-label="Toggle theme"
    >
      {theme === 'modern' ? '🌙 Retro Mode' : '☀️ Modern Mode'}
    </button>
  );
}
