import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, X, Bot, History, AlertCircle } from 'lucide-react';
import { useNavigator } from './useNavigator';
import { cn } from '@/lib/utils';

interface CommandBarProps {
  className?: string;
  apiEndpoint?: string;
}

export function CommandBar({ className, apiEndpoint }: CommandBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { 
    isProcessing, 
    history, 
    error, 
    lastAction,
    executeCommand, 
    clearHistory, 
    resetError 
  } = useNavigator(apiEndpoint);

  // Keyboard shortcut to open command bar (Ctrl/Cmd + K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Clear error when user starts typing
  useEffect(() => {
    if (error && query) {
      resetError();
    }
  }, [query, error, resetError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim() || isProcessing) return;

    await executeCommand(query);
    setQuery('');
  };

  const handleClose = () => {
    setIsOpen(false);
    setQuery('');
    resetError();
  };

  // Example commands for users
  const exampleCommands = [
    "Search for a leather wallet and add it to cart",
    "Go to the checkout page",
    "Find products under $50",
    "Add the first product to my cart",
    "Navigate to the home page"
  ];

  if (!isOpen) {
    return (
      <div className={cn("fixed bottom-6 right-6 z-50", className)}>
        <Button
          onClick={() => setIsOpen(true)}
          size="lg"
          className="rounded-full shadow-lg hover:shadow-xl transition-all duration-200 bg-primary hover:bg-primary/90"
        >
          <Bot className="w-5 h-5 mr-2" />
          AI Assistant
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-20 right-6 z-50 animate-in slide-in-from-bottom-2 slide-in-from-right-2 duration-200">
      <Card className="w-96 max-h-[500px] overflow-hidden shadow-2xl border border-border/50 bg-background">
        <CardContent className="p-0">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-muted/50">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              <h2 className="font-semibold">AI Website Navigator</h2>
              {isProcessing && (
                <Badge variant="secondary" className="ml-2">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Processing
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClose}
              disabled={isProcessing}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Command Input */}
          <div className="p-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Type a command... (e.g., 'search for leather wallet and add to cart')"
                disabled={isProcessing}
                className="flex-1"
              />
              <Button 
                type="submit" 
                disabled={isProcessing || !query.trim()}
                size="sm"
              >
                {isProcessing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </form>

            {/* Error Display */}
            {error && (
              <div className="mt-3 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Error</span>
                </div>
                <p className="text-sm text-destructive/80 mt-1">{error}</p>
              </div>
            )}

            {/* Current Action Display */}
            {lastAction && lastAction.action !== 'DONE' && isProcessing && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 text-blue-700">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-medium">
                    {lastAction.action === 'CLICK' ? 'Clicking' : 'Typing'} 
                    {lastAction.action === 'TYPE' && lastAction.text ? `: "${lastAction.text}"` : ''}
                  </span>
                </div>
              </div>
            )}

            {/* Success Message */}
            {lastAction?.action === 'DONE' && lastAction.summary && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-700">
                  <Bot className="w-4 h-4" />
                  <span className="text-sm font-medium">Completed</span>
                </div>
                <p className="text-sm text-green-700/80 mt-1">{lastAction.summary}</p>
              </div>
            )}
          </div>

          {/* Example Commands */}
          {!isProcessing && history.length === 0 && (
            <div className="px-4 pb-4">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">
                Try these commands:
              </h3>
              <div className="space-y-2">
                {exampleCommands.map((cmd, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(cmd)}
                    className="text-left text-sm text-muted-foreground hover:text-foreground transition-colors block w-full p-2 rounded hover:bg-muted/50"
                  >
                    "{cmd}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* History */}
          {history.length > 0 && (
            <div className="border-t bg-muted/30">
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <History className="w-4 h-4 text-muted-foreground" />
                    <h3 className="text-sm font-medium">Recent Actions</h3>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearHistory}
                    disabled={isProcessing}
                  >
                    Clear
                  </Button>
                </div>
                <div className="space-y-2 max-h-24 overflow-y-auto">
                  {history.slice(-5).map((action, index) => (
                    <div key={index} className="text-xs text-muted-foreground">
                      <Badge variant="outline" className="mr-2 text-xs">
                        {action.action}
                      </Badge>
                      {action.action === 'TYPE' && action.text && (
                        <span>Typed: "{action.text}"</span>
                      )}
                      {action.action === 'CLICK' && (
                        <span>Clicked element</span>
                      )}
                      {action.action === 'DONE' && action.summary && (
                        <span>{action.summary}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="px-4 py-2 bg-muted/50 border-t">
            <p className="text-xs text-muted-foreground text-center">
              Press <kbd className="px-1 py-0.5 bg-muted rounded text-xs">Ctrl+K</kbd> to open, 
              <kbd className="px-1 py-0.5 bg-muted rounded text-xs ml-1">Esc</kbd> to close
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
