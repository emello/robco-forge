/**
 * Keyboard Shortcuts Hook
 * 
 * Requirements: 22.1
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function useKeyboardShortcuts() {
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check if user is typing in an input field
      const target = event.target as HTMLElement;
      const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
      
      // Only handle shortcuts if not typing
      if (!isTyping && (event.metaKey || event.ctrlKey)) {
        switch (event.key.toLowerCase()) {
          case 'd':
            event.preventDefault();
            router.push('/dashboard');
            break;
          case 'w':
            event.preventDefault();
            router.push('/dashboard/workspaces');
            break;
          case 'b':
            event.preventDefault();
            router.push('/dashboard/blueprints');
            break;
          case 'c':
            event.preventDefault();
            router.push('/dashboard/costs');
            break;
          case 'l':
            event.preventDefault();
            router.push('/dashboard/lucy');
            break;
          case ',':
            event.preventDefault();
            router.push('/dashboard/settings');
            break;
          case '/':
            event.preventDefault();
            // Focus search or Lucy chat
            const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement;
            if (searchInput) {
              searchInput.focus();
            }
            break;
        }
      }
      
      // Escape key to close modals/dialogs
      if (event.key === 'Escape') {
        const closeButtons = document.querySelectorAll('[aria-label*="Close"]');
        if (closeButtons.length > 0) {
          (closeButtons[closeButtons.length - 1] as HTMLElement).click();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [router]);
}
