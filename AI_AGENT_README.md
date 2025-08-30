# AI Shopping Assistant - Nova Shop

## Overview

The AI Shopping Assistant is an intelligent voice and text-based navigation system for the Nova Shop website. It allows users to navigate the store, search for products, manage their cart, and get help using natural language commands through both voice and text input.

## Features

### 🎤 Voice Commands
- **Speech Recognition**: Uses the Web Speech API for voice input
- **Text-to-Speech**: Provides audio feedback for all actions
- **Natural Language Processing**: Understands conversational commands

### ⌨️ Text Commands
- **Chat Interface**: Type commands in natural language
- **Smart Suggestions**: Gets helpful suggestions when commands aren't understood
- **Real-time Processing**: Instant command execution

### 🧭 Navigation
- **Page Navigation**: Move between different sections of the website
- **Smart Routing**: Automatically navigates to appropriate pages
- **Context Awareness**: Knows current location and provides relevant options

### 🔍 Search & Discovery
- **Product Search**: Find products using natural language
- **Category Filtering**: Browse products by category
- **Smart Suggestions**: Get help with search queries

### 🛒 Cart Management
- **View Cart**: Check current cart contents
- **Clear Cart**: Remove all items from cart
- **Add Products**: Get guidance on adding products

## How to Use

### Getting Started

1. **Open the AI Assistant**: Click the floating bot icon (🤖) in the bottom-right corner
2. **Choose Input Method**: Use either voice or text input
3. **Start Speaking/Typing**: Give commands in natural language

### Voice Commands

#### Navigation Commands
- "Go to products" → Navigate to products page
- "Take me to cart" → Navigate to shopping cart
- "Show me home" → Return to homepage
- "Navigate to checkout" → Go to checkout page

#### Search Commands
- "Search for shoes" → Search for shoes
- "Find red dresses" → Search for red dresses
- "Look for electronics" → Search for electronics

#### Category Commands
- "Show electronics category" → Filter by electronics
- "Filter by clothing" → Show clothing products

#### Cart Commands
- "View cart" → Open shopping cart
- "Clear cart" → Remove all items
- "Add to cart" → Get guidance on adding products

#### Help Commands
- "Help" → Show available commands
- "What can you do?" → Display capabilities

### Text Commands

Type any of the voice commands above in the text input field. The AI will process your request and provide appropriate responses.

### Examples

```
User: "Go to products"
AI: "Taking you to products"

User: "Search for running shoes"
AI: "Searching for running shoes"

User: "Show me the cart"
AI: "Taking you to your cart"

User: "What can you do?"
AI: "I can help you navigate, search, and manage your cart..."
```

## Technical Implementation

### Architecture

- **React Component**: `AIAgent.tsx` - Main AI assistant component
- **Command Parser**: `commandParser.ts` - Natural language processing
- **Speech API**: Web Speech API for voice recognition and synthesis
- **State Management**: Integrates with existing store context

### Key Components

1. **AIAgent**: Main component with voice/text input handling
2. **CommandParser**: Parses natural language into executable commands
3. **Speech Recognition**: Handles voice input
4. **Speech Synthesis**: Provides audio feedback
5. **Command Execution**: Routes commands to appropriate actions

### Browser Compatibility

- **Voice Recognition**: Chrome, Edge, Safari (webkit)
- **Text Input**: All modern browsers
- **Fallback**: Graceful degradation for unsupported features

## Customization

### Adding New Commands

To add new command types, modify the `CommandParser` class in `src/lib/commandParser.ts`:

```typescript
// Add new command type
private static newCommandKeywords = ['keyword1', 'keyword2'];

// Add parsing logic
private static parseNewCommand(input: string, words: string[]): Command | null {
  // Implementation
}

// Add to main parse method
const newCommand = this.parseNewCommand(lowerInput, words);
if (newCommand) {
  return { command: newCommand, originalText: input };
}
```

### Modifying Responses

Update the `executeCommand` function in `AIAgent.tsx` to handle new command types:

```typescript
case 'newCommand':
  // Handle new command type
  break;
```

### Styling

The AI agent uses Tailwind CSS classes and can be customized by modifying the className props in the component.

## Troubleshooting

### Voice Recognition Issues

- **Browser Support**: Ensure you're using a supported browser
- **Microphone Permissions**: Allow microphone access when prompted
- **Clear Speech**: Speak clearly and at a normal pace
- **Background Noise**: Minimize background noise for better recognition

### Command Not Understood

- **Use Suggestions**: Click on suggested commands when available
- **Try Alternatives**: Use different phrasing for the same command
- **Check Help**: Say "help" to see available commands
- **Be Specific**: Use clear, specific language

### Performance Issues

- **Browser Updates**: Keep your browser updated
- **Clear Cache**: Clear browser cache if experiencing issues
- **Restart**: Refresh the page if the assistant becomes unresponsive

## Future Enhancements

### Planned Features

- **Product Recommendations**: AI-powered product suggestions
- **Order Tracking**: Voice commands for order status
- **Multi-language Support**: Support for multiple languages
- **Advanced Search**: Semantic search capabilities
- **Personalization**: Learn user preferences over time

### Integration Possibilities

- **Chatbot API**: Connect to external AI services
- **Analytics**: Track user interaction patterns
- **A/B Testing**: Test different command interpretations
- **Mobile App**: Extend to mobile applications

## Support

For technical support or feature requests:

1. Check the browser console for error messages
2. Ensure all dependencies are properly installed
3. Verify browser compatibility
4. Test with different voice commands

## License

This AI Shopping Assistant is part of the Nova Shop project and follows the same licensing terms.

---

**Note**: The AI agent requires microphone permissions and works best in quiet environments with clear speech. For optimal experience, use a modern browser with Web Speech API support.
