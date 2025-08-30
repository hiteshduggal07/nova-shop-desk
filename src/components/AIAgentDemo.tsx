import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Mic, Bot, Navigation, Search, ShoppingCart, HelpCircle } from 'lucide-react';

export function AIAgentDemo() {
  const examples = [
    {
      category: 'Navigation',
      icon: <Navigation className="w-4 h-4" />,
      commands: [
        'Go to products',
        'Take me to cart',
        'Show me home',
        'Navigate to checkout'
      ]
    },
    {
      category: 'Search',
      icon: <Search className="w-4 h-4" />,
      commands: [
        'Search for shoes',
        'Find red dresses',
        'Look for electronics',
        'Show me laptops'
      ]
    },
    {
      category: 'Cart',
      icon: <ShoppingCart className="w-4 h-4" />,
      commands: [
        'View cart',
        'Clear cart',
        'Add to cart',
        'Show my basket'
      ]
    },
    {
      category: 'Help',
      icon: <HelpCircle className="w-4 h-4" />,
      commands: [
        'Help',
        'What can you do?',
        'How do I use this?',
        'Show commands'
      ]
    }
  ];

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2 text-2xl">
          <Bot className="w-6 h-6 text-primary" />
          AI Shopping Assistant Demo
        </CardTitle>
        <p className="text-muted-foreground">
          Experience hands-free shopping with voice commands and intelligent text input
        </p>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Voice Features */}
        <div className="text-center p-6 bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Mic className="w-8 h-8 text-primary" />
            <h3 className="text-xl font-semibold">Voice Commands</h3>
          </div>
          <p className="text-muted-foreground mb-4">
            Simply speak your request and the AI will understand and execute your commands
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            <Badge variant="secondary">Speech Recognition</Badge>
            <Badge variant="secondary">Text-to-Speech</Badge>
            <Badge variant="secondary">Natural Language</Badge>
            <Badge variant="secondary">Real-time Processing</Badge>
          </div>
        </div>

        {/* Command Examples */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {examples.map((category) => (
            <Card key={category.category} className="border-dashed">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  {category.icon}
                  {category.category}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {category.commands.map((command, index) => (
                    <div
                      key={index}
                      className="p-2 bg-muted rounded text-sm font-mono hover:bg-muted/80 transition-colors cursor-pointer"
                      onClick={() => navigator.clipboard.writeText(command)}
                      title="Click to copy"
                    >
                      "{command}"
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* How to Use */}
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-blue-900">How to Get Started</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                1
              </div>
              <div>
                <p className="font-medium">Click the AI Assistant button</p>
                <p className="text-sm text-muted-foreground">
                  Look for the floating bot icon in the bottom-right corner
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                2
              </div>
              <div>
                <p className="font-medium">Choose your input method</p>
                <p className="text-sm text-muted-foreground">
                  Use voice commands with the microphone button or type in the text field
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                3
              </div>
              <div>
                <p className="font-medium">Start shopping hands-free</p>
                <p className="text-sm text-muted-foreground">
                  Navigate, search, and manage your cart using natural language
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tips */}
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardHeader>
            <CardTitle className="text-green-900">Pro Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>Speak clearly and at a normal pace for better voice recognition</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>Use natural language - "show me shoes" works better than "navigate to products"</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>If a command isn't understood, try rephrasing or use the suggestions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-600">•</span>
                <span>Say "help" anytime to see what commands are available</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}
