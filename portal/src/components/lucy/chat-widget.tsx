'use client';

/**
 * Lucy Chat Widget (Modern Theme)
 * 
 * Requirements: 5.2, 6.6
 */

import { useState, useRef, useEffect } from 'react';
import { useChatWithLucy } from '@/hooks/use-lucy';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LucyMessage } from '@/types';

interface ChatWidgetProps {
  userId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ChatWidget({ userId, isOpen, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<LucyMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [pendingConfirmation, setPendingConfirmation] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { mutate: sendMessage, isPending } = useChatWithLucy();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim() || isPending) return;

    const userMessage: LucyMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageToSend = inputValue;
    setInputValue('');

    sendMessage(
      { message: messageToSend, userId },
      {
        onSuccess: (response) => {
          // Check if confirmation is required
          if (response.requires_confirmation) {
            setPendingConfirmation(messageToSend);
            const confirmMessage: LucyMessage = {
              role: 'assistant',
              content: `${response.response}\n\nPlease confirm by typing "yes" or cancel by typing "no".`,
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, confirmMessage]);
            return;
          }
          
          // Build assistant message with tool execution feedback
          let content = response.response;
          
          // Add tool execution feedback if available
          if (response.tool_executed) {
            content += `\n\n✓ Tool executed: ${response.tool_executed}`;
          }
          
          // Add intent information if available
          if (response.intent) {
            console.log(`Lucy detected intent: ${response.intent}`);
          }
          
          const assistantMessage: LucyMessage = {
            role: 'assistant',
            content,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          
          // Show cost warning if response contains cost-related keywords
          if (response.response.toLowerCase().includes('budget') || 
              response.response.toLowerCase().includes('cost') ||
              response.response.toLowerCase().includes('expensive')) {
            const warningMessage: LucyMessage = {
              role: 'assistant',
              content: '💰 Tip: You can check your current budget status in the Cost Dashboard to avoid surprises!',
              timestamp: new Date().toISOString(),
            };
            setTimeout(() => {
              setMessages((prev) => [...prev, warningMessage]);
            }, 1000);
          }
        },
        onError: (error) => {
          const errorMessage: LucyMessage = {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error.message}`,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, errorMessage]);
        },
      }
    );
  };

  const handleConfirmation = (confirmed: boolean) => {
    if (!pendingConfirmation) return;

    if (confirmed) {
      // Send confirmation message
      const confirmMessage: LucyMessage = {
        role: 'user',
        content: 'yes',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, confirmMessage]);

      sendMessage(
        { message: `confirm: ${pendingConfirmation}`, userId },
        {
          onSuccess: (response) => {
            const assistantMessage: LucyMessage = {
              role: 'assistant',
              content: response.response,
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setPendingConfirmation(null);
          },
        }
      );
    } else {
      // Send cancellation message
      const cancelMessage: LucyMessage = {
        role: 'user',
        content: 'no',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, cancelMessage]);

      const assistantMessage: LucyMessage = {
        role: 'assistant',
        content: 'Action cancelled.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setPendingConfirmation(null);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-4 right-4 w-96 h-[600px] z-50 shadow-2xl retro:retro-scanline retro:retro-crt">
      <Card className="h-full flex flex-col retro:bg-black retro:border-2 retro:border-green-500">
        <CardHeader className="flex-shrink-0 border-b retro:border-green-700">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 retro:text-green-500 retro:font-mono retro:retro-glow">
              <span className="text-2xl retro:hidden">🤖</span>
              <span className="hidden retro:inline">[LUCY]</span>
              <span className="retro:hidden">Lucy AI Assistant</span>
              <span className="hidden retro:inline">AI ASSISTANT v1.0</span>
            </CardTitle>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 text-xl retro:text-green-500 retro:hover:text-green-300 retro:font-mono"
              aria-label="Close chat"
            >
              <span className="retro:hidden">×</span>
              <span className="hidden retro:inline">[X]</span>
            </button>
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col overflow-hidden p-0 retro:bg-black">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8 retro:text-green-400 retro:font-mono">
                <div className="text-4xl mb-2 retro:hidden">👋</div>
                <div className="hidden retro:block text-green-500 text-2xl mb-2">&gt;&gt; SYSTEM READY</div>
                <p className="text-sm">
                  <span className="retro:hidden">Hi! I'm Lucy, your AI assistant.</span>
                  <span className="hidden retro:inline">&gt; LUCY AI ASSISTANT ONLINE</span>
                </p>
                <p className="text-sm mt-1">
                  <span className="retro:hidden">Ask me about workspaces, costs, or anything else!</span>
                  <span className="hidden retro:inline">&gt; AWAITING INPUT...</span>
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 retro:rounded-none retro:font-mono ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white retro:bg-transparent retro:border retro:border-green-600 retro:text-green-300'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 retro:bg-transparent retro:border retro:border-green-700 retro:text-green-500'
                    }`}
                  >
                    <div className="hidden retro:block text-xs text-green-600 mb-1">
                      {msg.role === 'user' ? '&gt; USER:' : '&gt; LUCY:'}
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs mt-1 opacity-70 retro:text-green-600">
                      <span className="retro:hidden">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                      <span className="hidden retro:inline">[{new Date(msg.timestamp).toLocaleTimeString()}]</span>
                    </p>
                  </div>
                </div>
              ))
            )}
            {isPending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2 retro:bg-transparent retro:border retro:border-green-700 retro:rounded-none">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1 retro:hidden">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm text-gray-600 dark:text-gray-400 retro:text-green-500 retro:font-mono">
                      <span className="retro:hidden">Lucy is typing...</span>
                      <span className="hidden retro:inline">&gt; PROCESSING<span className="animate-pulse">_</span></span>
                    </span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div className="flex-shrink-0 border-t p-4 retro:border-green-700">
            {pendingConfirmation ? (
              <div className="flex gap-2">
                <button
                  onClick={() => handleConfirmation(true)}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors retro:bg-transparent retro:border-2 retro:border-green-500 retro:text-green-500 retro:rounded-none retro:hover:bg-green-900 retro:font-mono"
                >
                  <span className="retro:hidden">✓ Confirm</span>
                  <span className="hidden retro:inline">[YES - CONFIRM]</span>
                </button>
                <button
                  onClick={() => handleConfirmation(false)}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors retro:bg-transparent retro:border-2 retro:border-red-500 retro:text-red-500 retro:rounded-none retro:hover:bg-red-900 retro:font-mono"
                >
                  <span className="retro:hidden">✗ Cancel</span>
                  <span className="hidden retro:inline">[NO - CANCEL]</span>
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <span className="hidden retro:inline absolute left-3 top-1/2 -translate-y-1/2 text-green-500 font-mono pointer-events-none">
                    &gt;
                  </span>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask Lucy anything..."
                    disabled={isPending}
                    className="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 retro:bg-black retro:border-green-500 retro:text-green-500 retro:font-mono retro:rounded-none retro:pl-8 retro:placeholder-green-700 retro:focus:ring-green-500"
                  />
                </div>
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors retro:bg-transparent retro:border-2 retro:border-green-500 retro:text-green-500 retro:rounded-none retro:hover:bg-green-900 retro:hover:border-green-400 retro:font-mono"
                >
                  <span className="retro:hidden">Send</span>
                  <span className="hidden retro:inline">[SEND]</span>
                </button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
