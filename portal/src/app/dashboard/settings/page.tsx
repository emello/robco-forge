'use client';

/**
 * Settings Page
 * 
 * Requirements: 22.1
 */

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

type Theme = 'modern' | 'retro';
type BundleType = 'VALUE' | 'STANDARD' | 'PERFORMANCE' | 'POWER' | 'POWERPRO' | 'GRAPHICS' | 'GRAPHICSPRO';
type Region = 'us-east-1' | 'us-west-2' | 'eu-west-1' | 'ap-southeast-1';

export default function SettingsPage() {
  // Load preferences from localStorage or use defaults
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as Theme) || 'modern';
    }
    return 'modern';
  });
  
  const [defaultBundle, setDefaultBundle] = useState<BundleType>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('defaultBundle') as BundleType) || 'STANDARD';
    }
    return 'STANDARD';
  });
  
  const [defaultRegion, setDefaultRegion] = useState<Region>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('defaultRegion') as Region) || 'us-east-1';
    }
    return 'us-east-1';
  });
  
  const [emailNotifications, setEmailNotifications] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('emailNotifications') !== 'false';
    }
    return true;
  });
  
  const [slackNotifications, setSlackNotifications] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('slackNotifications') === 'true';
    }
    return false;
  });
  
  const [budgetAlerts, setBudgetAlerts] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('budgetAlerts') !== 'false';
    }
    return true;
  });

  const handleThemeChange = (newTheme: Theme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    // Apply theme to document
    if (newTheme === 'retro') {
      document.documentElement.classList.add('retro');
    } else {
      document.documentElement.classList.remove('retro');
    }
  };

  const handleDefaultBundleChange = (bundle: BundleType) => {
    setDefaultBundle(bundle);
    localStorage.setItem('defaultBundle', bundle);
  };

  const handleDefaultRegionChange = (region: Region) => {
    setDefaultRegion(region);
    localStorage.setItem('defaultRegion', region);
  };

  const handleEmailNotificationsChange = (enabled: boolean) => {
    setEmailNotifications(enabled);
    localStorage.setItem('emailNotifications', String(enabled));
  };

  const handleSlackNotificationsChange = (enabled: boolean) => {
    setSlackNotifications(enabled);
    localStorage.setItem('slackNotifications', String(enabled));
  };

  const handleBudgetAlertsChange = (enabled: boolean) => {
    setBudgetAlerts(enabled);
    localStorage.setItem('budgetAlerts', String(enabled));
  };

  return (
    <div className="retro:retro-scanline retro:retro-crt">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono retro:retro-glow">
          {'>>'} SETTINGS
        </h1>
        <p className="text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono mt-2">
          Customize your RobCo Forge experience
        </p>
      </div>

      <div className="space-y-6">
        {/* Theme Selection */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">🎨 Theme</span>
              <span className="hidden retro:inline">[THEME SELECTION]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                Choose your preferred interface theme
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => handleThemeChange('modern')}
                  className={`flex-1 p-4 border-2 rounded-lg transition-colors retro:rounded-none ${
                    theme === 'modern'
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-900/20'
                      : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 retro:border-green-700 retro:hover:border-green-600'
                  }`}
                >
                  <div className="text-lg font-semibold mb-2 retro:font-mono retro:text-green-500">Modern</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    Clean, contemporary design
                  </div>
                </button>
                <button
                  onClick={() => handleThemeChange('retro')}
                  className={`flex-1 p-4 border-2 rounded-lg transition-colors retro:rounded-none ${
                    theme === 'retro'
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 retro:border-green-500 retro:bg-green-900/20'
                      : 'border-gray-300 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-600 retro:border-green-700 retro:hover:border-green-600'
                  }`}
                >
                  <div className="text-lg font-semibold mb-2 retro:font-mono retro:text-green-500">Retro Terminal</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    Classic terminal aesthetic
                  </div>
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Default Bundle Type */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">💻 Default Bundle Type</span>
              <span className="hidden retro:inline">[DEFAULT BUNDLE TYPE]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                Pre-select your preferred workspace bundle type
              </p>
              <select
                value={defaultBundle}
                onChange={(e) => handleDefaultBundleChange(e.target.value as BundleType)}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
              >
                <option value="VALUE">VALUE - 2 vCPU, 4 GB RAM</option>
                <option value="STANDARD">STANDARD - 2 vCPU, 4 GB RAM</option>
                <option value="PERFORMANCE">PERFORMANCE - 4 vCPU, 16 GB RAM</option>
                <option value="POWER">POWER - 8 vCPU, 32 GB RAM</option>
                <option value="POWERPRO">POWERPRO - 16 vCPU, 64 GB RAM</option>
                <option value="GRAPHICS">GRAPHICS - 8 vCPU, 15 GB RAM, GPU</option>
                <option value="GRAPHICSPRO">GRAPHICSPRO - 16 vCPU, 122 GB RAM, GPU</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Default Region */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">🌍 Default Region</span>
              <span className="hidden retro:inline">[DEFAULT REGION]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                Pre-select your preferred AWS region
              </p>
              <select
                value={defaultRegion}
                onChange={(e) => handleDefaultRegionChange(e.target.value as Region)}
                className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none"
              >
                <option value="us-east-1">US East (N. Virginia)</option>
                <option value="us-west-2">US West (Oregon)</option>
                <option value="eu-west-1">EU (Ireland)</option>
                <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Notification Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="retro:hidden">🔔 Notification Preferences</span>
              <span className="hidden retro:inline">[NOTIFICATION PREFERENCES]</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b dark:border-gray-700 retro:border-green-700">
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    Email Notifications
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    Receive updates via email
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={emailNotifications}
                    onChange={(e) => handleEmailNotificationsChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 retro:peer-checked:bg-green-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between py-3 border-b dark:border-gray-700 retro:border-green-700">
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    Slack Notifications
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    Receive updates via Slack
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={slackNotifications}
                    onChange={(e) => handleSlackNotificationsChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 retro:peer-checked:bg-green-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between py-3">
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100 retro:text-green-500 retro:font-mono">
                    Budget Alerts
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-400 retro:font-mono">
                    Get notified when approaching budget limits
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={budgetAlerts}
                    onChange={(e) => handleBudgetAlertsChange(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600 retro:peer-checked:bg-green-600"></div>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save Confirmation */}
        <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded retro:bg-black retro:border-green-500 retro:rounded-none">
          <div className="flex items-center gap-2">
            <span className="text-green-600 dark:text-green-400 retro:text-green-500 retro:hidden">✓</span>
            <span className="hidden retro:inline text-green-500 font-mono">[OK]</span>
            <p className="text-sm text-green-800 dark:text-green-200 retro:text-green-500 retro:font-mono">
              <span className="retro:hidden">Settings are saved automatically</span>
              <span className="hidden retro:inline">SETTINGS AUTO-SAVED</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
