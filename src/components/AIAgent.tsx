import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useStore } from '@/contexts/StoreContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mic, MicOff, Send, X, Bot, User, Volume2, Lightbulb } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { CommandParser, type Command, type ParsedCommand } from '@/lib/commandParser';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  suggestions?: string[];
}

export function AIAgent() {
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useStore();
  const [isListening, setIsListening] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your AI shopping assistant. I can help you navigate the store, search for products, manage your cart, and more. Try saying "go to products" or "search for shoes".',
      timestamp: new Date()
    }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthesisRef = useRef<SpeechSynthesis | null>(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        handleVoiceCommand(transcript);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        toast({
          title: "Voice Recognition Error",
          description: "Please try again or use text input.",
          variant: "destructive",
        });
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    if ('speechSynthesis' in window) {
      synthesisRef.current = window.speechSynthesis;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const speak = useCallback((text: string) => {
    if (synthesisRef.current) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      synthesisRef.current.speak(utterance);
    }
  }, []);

  const addMessage = useCallback((type: 'user' | 'assistant', content: string, suggestions?: string[]) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      suggestions
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const executeCommand = useCallback(async (command: Command) => {
    setIsProcessing(true);
    
    try {
      switch (command.type) {
        case 'navigation':
          if (command.action === 'navigate' && command.parameters?.path) {
            navigate(command.parameters.path);
            addMessage('assistant', `Navigating to ${command.parameters.path === '/' ? 'home' : command.parameters.path.slice(1)}`);
            speak(`Taking you to ${command.parameters.path === '/' ? 'home' : command.parameters.path.slice(1)}`);
          }
          break;

        case 'search':
          if (command.action === 'search' && command.parameters?.query) {
            dispatch({ type: 'SET_SEARCH_QUERY', payload: command.parameters.query });
            navigate('/products');
            addMessage('assistant', `Searching for "${command.parameters.query}"`);
            speak(`Searching for ${command.parameters.query}`);
          }
          break;

        case 'category':
          if (command.action === 'filter' && command.parameters?.category) {
            dispatch({ type: 'SET_CATEGORY', payload: command.parameters.category });
            navigate('/products');
            addMessage('assistant', `Filtering by category: ${command.parameters.category}`);
            speak(`Showing products in the ${command.parameters.category} category`);
          }
          break;

        case 'cart':
          switch (command.action) {
            case 'add':
              addMessage('assistant', `I'll help you add "${command.parameters.product}" to your cart. Please navigate to the product page first.`);
              speak(`I'll help you add ${command.parameters.product} to your cart. Please navigate to the product page first.`);
              break;
            case 'clear':
              dispatch({ type: 'CLEAR_CART' });
              addMessage('assistant', 'Your cart has been cleared.');
              speak('Your cart has been cleared.');
              break;
            case 'view':
              navigate('/cart');
              addMessage('assistant', 'Taking you to your cart.');
              speak('Taking you to your cart.');
              break;
          }
          break;

        case 'product':
          if (command.action === 'info' && command.parameters?.product) {
            addMessage('assistant', `I can help you find information about "${command.parameters.product}". Let me search for it.`);
            dispatch({ type: 'SET_SEARCH_QUERY', payload: command.parameters.product });
            navigate('/products');
            speak(`I'll search for ${command.parameters.product} for you.`);
          }
          break;

        case 'help':
          const helpText = `I can help you with:
• Navigation: "go to products", "take me to cart"
• Search: "search for shoes", "find red dresses"
• Categories: "show electronics category"
• Cart: "view cart", "clear cart"
• General: "what can you do", "help"`;
          addMessage('assistant', helpText);
          speak('I can help you navigate, search, and manage your cart. Just ask!');
          break;
      }
    } catch (error) {
      console.error('Error executing command:', error);
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
      speak('Sorry, I encountered an error. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, [navigate, dispatch, addMessage, speak]);

  const handleCommand = useCallback((input: string) => {
    const parsedCommand: ParsedCommand = CommandParser.parse(input);
    
    if (parsedCommand.command) {
      executeCommand(parsedCommand.command);
    } else {
      const suggestions = parsedCommand.suggestions || [];
      addMessage('assistant', `I didn't understand "${input}". Here are some suggestions:`, suggestions);
      speak(`I didn't understand that. Try saying help to see what I can do.`);
    }
  }, [executeCommand, addMessage, speak]);

  const handleVoiceCommand = useCallback((transcript: string) => {
    addMessage('user', transcript);
    handleCommand(transcript);
  }, [addMessage, handleCommand]);

  const handleTextSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    addMessage('user', inputText);
    handleCommand(inputText);
    setInputText('');
  }, [inputText, addMessage, handleCommand]);

  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) {
      toast({
        title: "Voice Recognition Not Available",
        description: "Your browser doesn't support voice recognition. Please use text input.",
        variant: "destructive",
      });
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
      setIsListening(true);
      speak("I'm listening. What would you like me to help you with?");
    }
  }, [isListening, speak]);

  const toggleAgent = useCallback(() => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      speak("Hello! I'm your AI shopping assistant. How can I help you today?");
    }
  }, [isOpen, speak]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setInputText(suggestion);
    handleCommand(suggestion);
  }, [handleCommand]);

  return (
    <>
      {/* Floating Action Button */}
      <Button
        onClick={toggleAgent}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg z-50 bg-primary hover:bg-primary/90"
        size="icon"
      >
        <Bot className="w-6 h-6" />
      </Button>

      {/* AI Agent Panel */}
      {isOpen && (
        <Card className="fixed bottom-24 right-6 w-96 h-[600px] shadow-xl z-50 bg-background border-border">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <Bot className="w-5 h-5" />
                AI Shopping Assistant
              </CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleAgent}
                className="h-8 w-8"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                Voice & Text
              </Badge>
              <Badge variant="outline" className="text-xs">
                {location.pathname === '/' ? 'Home' : location.pathname.slice(1)}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="p-0 flex flex-col h-full">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[400px]">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                      message.type === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-foreground'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      {message.type === 'user' ? (
                        <User className="w-3 h-3" />
                      ) : (
                        <Bot className="w-3 h-3" />
                      )}
                      <span className="text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                    {message.content}
                    
                    {/* Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <div className="flex items-center gap-1 text-xs text-muted-foreground">
                          <Lightbulb className="w-3 h-3" />
                          Suggestions:
                        </div>
                        {message.suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="block w-full text-left text-xs text-primary hover:text-primary/80 hover:bg-primary/10 rounded px-2 py-1 transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isProcessing && (
                <div className="flex justify-start">
                  <div className="bg-muted text-foreground rounded-lg px-3 py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Bot className="w-3 h-3" />
                      <span className="text-xs opacity-70">Processing...</span>
                    </div>
                    <div className="flex space-x-1 mt-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-border">
              <form onSubmit={handleTextSubmit} className="flex gap-2">
                <Input
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Type your request..."
                  className="flex-1"
                  disabled={isProcessing}
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!inputText.trim() || isProcessing}
                  className="h-10 w-10"
                >
                  <Send className="w-4 h-4" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  onClick={toggleListening}
                  disabled={isProcessing}
                  variant={isListening ? "destructive" : "default"}
                  className="h-10 w-10"
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
              </form>
              
              {/* Voice Status */}
              {isListening && (
                <div className="mt-2 text-center">
                  <Badge variant="destructive" className="animate-pulse">
                    <Mic className="w-3 h-3 mr-1" />
                    Listening...
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
