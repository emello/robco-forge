'use client';

import { ThemeToggle } from '@/components/theme-toggle';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold mb-4">RobCo Forge</h1>
        <p className="text-xl mb-8">Self-service cloud engineering workstation platform</p>
        
        <div className="mb-8">
          <Link 
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-block"
          >
            Get Started →
          </Link>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <div className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
            <h2 className="text-2xl font-semibold mb-2">Workspaces</h2>
            <p className="opacity-70">Provision and manage your cloud workstations</p>
          </div>
          
          <div className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
            <h2 className="text-2xl font-semibold mb-2">Cost Dashboard</h2>
            <p className="opacity-70">Track spending and optimize costs</p>
          </div>
          
          <div className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
            <h2 className="text-2xl font-semibold mb-2">Lucy AI</h2>
            <p className="opacity-70">Chat with your AI assistant</p>
          </div>
          
          <div className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
            <h2 className="text-2xl font-semibold mb-2">Blueprints</h2>
            <p className="opacity-70">Manage workspace templates</p>
          </div>
        </div>
      </div>
    </main>
  );
}
