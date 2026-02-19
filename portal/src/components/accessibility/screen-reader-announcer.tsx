/**
 * Screen Reader Announcer Component
 * 
 * Requirements: 22.1
 */

'use client';

import { useState } from 'react';

interface AnnouncerProps {
  message: string;
  priority?: 'polite' | 'assertive';
}

export function ScreenReaderAnnouncer({ message, priority = 'polite' }: AnnouncerProps) {
  return (
    <div
      role="status"
      aria-live={priority}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}

// Hook for announcing messages to screen readers
export function useScreenReaderAnnounce() {
  const [announcement, setAnnouncement] = useState('');

  const announce = (message: string, _priority: 'polite' | 'assertive' = 'polite') => {
    setAnnouncement(''); // Clear first to ensure re-announcement
    setTimeout(() => setAnnouncement(message), 100);
  };

  return { announcement, announce };
}
