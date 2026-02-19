/**
 * Retro Terminal Prompt Component
 * 
 * Requirements: 22.1
 */

'use client';

interface RetroTerminalPromptProps {
  command: string;
  children: React.ReactNode;
}

export function RetroTerminalPrompt({ command, children }: RetroTerminalPromptProps) {
  return (
    <div className="hidden retro:block font-mono text-sm">
      <div className="text-green-400 mb-2">
        <span className="text-green-600">user@robco-forge</span>
        <span className="text-green-500">:</span>
        <span className="text-blue-400">~</span>
        <span className="text-green-500">$ </span>
        <span className="text-green-300">{command}</span>
      </div>
      <div className="pl-0 text-green-500">{children}</div>
    </div>
  );
}
