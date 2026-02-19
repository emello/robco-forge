'use client';

/**
 * Sidebar Navigation
 * 
 * Requirements: 22.1
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from '@/contexts/theme-context';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Workspaces', href: '/dashboard/workspaces', icon: '💻' },
  { name: 'Blueprints', href: '/dashboard/blueprints', icon: '📋' },
  { name: 'Costs', href: '/dashboard/costs', icon: '💰' },
  { name: 'Team', href: '/dashboard/team', icon: '👥', roleRequired: 'team_lead' },
  { name: 'Lucy AI', href: '/dashboard/lucy', icon: '🤖' },
  { name: 'Settings', href: '/dashboard/settings', icon: '⚙️' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme } = useTheme();

  return (
    <aside
      className={cn(
        'w-64 border-r min-h-screen p-6',
        theme === 'retro' && 'retro-border bg-retro-bg'
      )}
    >
      <div className="mb-8">
        <h1
          className={cn(
            'text-2xl font-bold',
            theme === 'retro' && 'retro-glow font-retro'
          )}
        >
          RobCo Forge
        </h1>
        <p className={cn('text-sm opacity-70', theme === 'retro' && 'text-retro-dim')}>
          Engineering Workstations
        </p>
      </div>

      <nav className="space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? theme === 'retro'
                    ? 'retro-border bg-retro-dim text-retro-bright'
                    : 'bg-primary-100 text-primary-900 font-medium'
                  : theme === 'retro'
                  ? 'text-retro-text hover:bg-retro-dim'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
