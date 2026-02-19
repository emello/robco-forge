'use client';

/**
 * Dashboard Layout
 * 
 * Requirements: 22.1, 5.2
 */

import { useState } from 'react';
import { ProtectedRoute } from '@/components/protected-route';
import { Sidebar } from '@/components/navigation/sidebar';
import { Header } from '@/components/navigation/header';
import { ChatWidget } from '@/components/lucy/chat-widget';
import { ChatFab } from '@/components/lucy/chat-fab';
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts';
import { useWebSocket } from '@/hooks/use-websocket';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  // Enable keyboard shortcuts
  useKeyboardShortcuts();
  
  // TODO: Get actual user ID from auth context
  const userId = 'user-123';
  
  // Connect to WebSocket for real-time updates
  const { isConnected } = useWebSocket(userId);

  return (
    <ProtectedRoute>
      {/* Skip to main content link for keyboard navigation */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>
      
      <div className="flex">
        <Sidebar />
        <div className="flex-1">
          <Header />
          <main id="main-content" className="p-8" tabIndex={-1}>
            {children}
          </main>
        </div>
      </div>
      
      {/* Lucy Chat Widget */}
      <ChatWidget 
        userId={userId} 
        isOpen={isChatOpen} 
        onClose={() => setIsChatOpen(false)} 
      />
      
      {/* Floating Action Button */}
      {!isChatOpen && (
        <ChatFab 
          onClick={() => setIsChatOpen(true)} 
          isOpen={isChatOpen} 
        />
      )}
    </ProtectedRoute>
  );
}
