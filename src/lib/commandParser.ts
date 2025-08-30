export interface Command {
  type: 'navigation' | 'search' | 'cart' | 'category' | 'help' | 'product' | 'general';
  action: string;
  parameters?: any;
  confidence: number;
}

export interface ParsedCommand {
  command: Command | null;
  originalText: string;
  suggestions?: string[];
}

export class CommandParser {
  private static navigationKeywords = [
    'go to', 'navigate to', 'take me to', 'show me', 'open', 'visit', 'browse'
  ];

  private static searchKeywords = [
    'search for', 'find', 'look for', 'find me', 'search', 'look up', 'show me'
  ];

  private static categoryKeywords = [
    'show', 'filter by', 'category', 'in', 'from', 'type'
  ];

  private static cartKeywords = [
    'add to cart', 'buy', 'purchase', 'order', 'get', 'add', 'cart'
  ];

  private static helpKeywords = [
    'help', 'what can you do', 'how do i', 'how to', 'guide', 'assist'
  ];

  private static locations = {
    'home': '/',
    'main page': '/',
    'start': '/',
    'products': '/products',
    'shop': '/products',
    'store': '/products',
    'catalog': '/products',
    'cart': '/cart',
    'shopping cart': '/cart',
    'basket': '/cart',
    'checkout': '/checkout',
    'payment': '/checkout',
    'order': '/checkout'
  };

  private static categories = [
    'electronics', 'clothing', 'books', 'home', 'sports', 'beauty', 'toys', 'automotive'
  ];

  static parse(input: string): ParsedCommand {
    const lowerInput = input.toLowerCase().trim();
    const words = lowerInput.split(' ');
    
    // Check for exact matches first
    const exactMatch = this.findExactMatch(lowerInput);
    if (exactMatch) {
      return { command: exactMatch, originalText: input };
    }

    // Check for navigation commands
    const navigationCommand = this.parseNavigation(lowerInput, words);
    if (navigationCommand) {
      return { command: navigationCommand, originalText: input };
    }

    // Check for search commands
    const searchCommand = this.parseSearch(lowerInput, words);
    if (searchCommand) {
      return { command: searchCommand, originalText: input };
    }

    // Check for category commands
    const categoryCommand = this.parseCategory(lowerInput, words);
    if (categoryCommand) {
      return { command: categoryCommand, originalText: input };
    }

    // Check for cart commands
    const cartCommand = this.parseCart(lowerInput, words);
    if (cartCommand) {
      return { command: cartCommand, originalText: input };
    }

    // Check for help commands
    const helpCommand = this.parseHelp(lowerInput, words);
    if (helpCommand) {
      return { command: helpCommand, originalText: input };
    }

    // Check for product-specific commands
    const productCommand = this.parseProduct(lowerInput, words);
    if (productCommand) {
      return { command: productCommand, originalText: input };
    }

    // Generate suggestions for unrecognized commands
    const suggestions = this.generateSuggestions(lowerInput);
    
    return {
      command: null,
      originalText: input,
      suggestions
    };
  }

  private static findExactMatch(input: string): Command | null {
    const exactMatches: Record<string, Command> = {
      'help': { type: 'help', action: 'help', confidence: 1.0 },
      'what can you do': { type: 'help', action: 'help', confidence: 1.0 },
      'go home': { type: 'navigation', action: 'navigate', parameters: { path: '/' }, confidence: 1.0 },
      'show cart': { type: 'cart', action: 'view', confidence: 1.0 },
      'view cart': { type: 'cart', action: 'view', confidence: 1.0 },
      'clear cart': { type: 'cart', action: 'clear', confidence: 1.0 },
      'empty cart': { type: 'cart', action: 'clear', confidence: 1.0 }
    };

    return exactMatches[input] || null;
  }

  private static parseNavigation(input: string, words: string[]): Command | null {
    for (const keyword of this.navigationKeywords) {
      if (input.includes(keyword)) {
        const remainingText = input.replace(keyword, '').trim();
        
        for (const [location, path] of Object.entries(this.locations)) {
          if (remainingText.includes(location)) {
            return {
              type: 'navigation',
              action: 'navigate',
              parameters: { path },
              confidence: 0.9
            };
          }
        }
      }
    }
    return null;
  }

  private static parseSearch(input: string, words: string[]): Command | null {
    for (const keyword of this.searchKeywords) {
      if (input.includes(keyword)) {
        const searchTerm = input.replace(keyword, '').trim();
        if (searchTerm && searchTerm.length > 1) {
          return {
            type: 'search',
            action: 'search',
            parameters: { query: searchTerm },
            confidence: 0.9
          };
        }
      }
    }
    return null;
  }

  private static parseCategory(input: string, words: string[]): Command | null {
    for (const keyword of this.categoryKeywords) {
      if (input.includes(keyword)) {
        for (const category of this.categories) {
          if (input.includes(category)) {
            return {
              type: 'category',
              action: 'filter',
              parameters: { category },
              confidence: 0.8
            };
          }
        }
      }
    }
    return null;
  }

  private static parseCart(input: string, words: string[]): Command | null {
    for (const keyword of this.cartKeywords) {
      if (input.includes(keyword)) {
        const productName = input.replace(keyword, '').trim();
        if (productName && productName.length > 1) {
          return {
            type: 'cart',
            action: 'add',
            parameters: { product: productName },
            confidence: 0.8
          };
        }
      }
    }
    return null;
  }

  private static parseHelp(input: string, words: string[]): Command | null {
    for (const keyword of this.helpKeywords) {
      if (input.includes(keyword)) {
        return {
          type: 'help',
          action: 'help',
          confidence: 0.9
        };
      }
    }
    return null;
  }

  private static parseProduct(input: string, words: string[]): Command | null {
    // Look for product-related patterns
    const productPatterns = [
      /(?:show|display|view|see)\s+(.+)/i,
      /(?:tell me about|what is|describe)\s+(.+)/i,
      /(?:price of|cost of)\s+(.+)/i
    ];

    for (const pattern of productPatterns) {
      const match = input.match(pattern);
      if (match && match[1]) {
        const productName = match[1].trim();
        if (productName.length > 1) {
          return {
            type: 'product',
            action: 'info',
            parameters: { product: productName },
            confidence: 0.7
          };
        }
      }
    }
    return null;
  }

  private static generateSuggestions(input: string): string[] {
    const suggestions: string[] = [];
    
    if (input.length < 3) {
      suggestions.push('Try saying "help" to see what I can do');
      suggestions.push('Say "go to products" to browse the store');
      suggestions.push('Say "search for shoes" to find products');
    } else if (input.includes('go') || input.includes('navigate')) {
      suggestions.push('Try "go to products" or "go to cart"');
      suggestions.push('Say "go to checkout" to complete your order');
    } else if (input.includes('find') || input.includes('search')) {
      suggestions.push('Try "search for red shoes" or "find dresses"');
      suggestions.push('Say "search for electronics" to browse categories');
    } else if (input.includes('cart') || input.includes('buy')) {
      suggestions.push('Try "add to cart" or "view cart"');
      suggestions.push('Say "clear cart" to remove all items');
    } else {
      suggestions.push('Say "help" to see all available commands');
      suggestions.push('Try "go to products" to start shopping');
      suggestions.push('Say "search for [product name]" to find items');
    }

    return suggestions;
  }

  static getAvailableCommands(): string[] {
    return [
      'Navigation: "go to products", "take me to cart", "show me home"',
      'Search: "search for shoes", "find red dresses", "look for electronics"',
      'Categories: "show electronics category", "filter by clothing"',
      'Cart: "add to cart", "view cart", "clear cart"',
      'Help: "help", "what can you do", "how do I use this"'
    ];
  }
}
