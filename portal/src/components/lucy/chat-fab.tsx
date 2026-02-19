'use client';

/**
 * Lucy Chat Floating Action Button
 * 
 * Requirements: 5.2
 */

import { useState } from 'react';

interface ChatFabProps {
  onClick: () => void;
  isOpen: boolean;
}

export function ChatFab({ onClick, isOpen }: ChatFabProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="fixed bottom-4 right-4 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all z-40 flex items-center justify-center retro:bg-black retro:border-2 retro:border-green-500 retro:text-green-500 retro:rounded-none retro:hover:bg-green-900 retro:hover:border-green-400 retro:font-mono retro:retro-glow"
      aria-label="Open Lucy chat"
    >
      {isOpen ? (
        <>
          <span className="text-2xl retro:hidden">×</span>
          <span className="hidden retro:inline text-xl">[X]</span>
        </>
      ) : (
        <>
          <span className="text-2xl retro:hidden">🤖</span>
          <span className="hidden retro:inline text-sm">[AI]</span>
        </>
      )}
      {isHovered && !isOpen && (
        <div className="absolute right-16 top-1/2 -translate-y-1/2 bg-gray-900 text-white text-sm px-3 py-2 rounded whitespace-nowrap retro:bg-black retro:border retro:border-green-500 retro:text-green-500 retro:rounded-none retro:font-mono">
          <span className="retro:hidden">Chat with Lucy</span>
          <span className="hidden retro:inline">&gt; CHAT WITH LUCY</span>
        </div>
      )}
    </button>
  );
}
