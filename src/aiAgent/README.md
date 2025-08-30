# AI Website Navigator Agent

An intelligent agent that allows users to control your e-commerce website using natural language commands. Users can type instructions like "search for a leather wallet and add it to cart" and the agent will automatically navigate the website and perform the required actions.

## Features

- 🎯 Natural language command processing
- 🤖 Automated DOM interaction (clicking, typing, navigation)
- 🎨 Beautiful floating command bar UI with keyboard shortcuts
- 🔄 Multi-step action execution with visual feedback
- 📱 Responsive design with modern UI components
- ⚡ Real-time DOM scanning and element tagging
- 🛡️ Robust error handling and timeout protection
- 📊 Action history tracking and management

## Architecture

### Core Components

1. **CommandBar** - Floating UI component for user input
2. **DomObserver** - Scans and tags interactive DOM elements
3. **Executor** - Performs actions on DOM elements
4. **useNavigator** - React hook that coordinates the entire process
5. **Types** - TypeScript interfaces for type safety
6. **Config** - Centralized configuration settings
7. **Utils** - Helper functions and utilities

### Data Flow

```
User Input → DOM Scan → API Request → AI Processing → Action Execution → Repeat Until Done
```

## Usage

### Basic Setup

The AI agent is automatically integrated into your React app. Users can:

1. **Open Command Bar**: Press `Ctrl+K` (or `Cmd+K` on Mac) or click the floating AI Assistant button
2. **Enter Command**: Type natural language instructions
3. **Execute**: Press Enter or click the Send button
4. **Watch**: The agent will automatically perform the actions

### Example Commands

- "Search for a leather wallet and add it to cart"
- "Go to the checkout page"
- "Find products under $50"
- "Add the first product to my cart"
- "Navigate to the home page"
- "Remove items from my cart"
- "Complete the checkout process"

### Keyboard Shortcuts

- `Ctrl+K` / `Cmd+K` - Open command bar
- `Escape` - Close command bar
- `Enter` - Execute command

## Backend Integration

The agent communicates with a FastAPI backend service. You need to implement the `/plan` endpoint that:

### Request Format

```json
{
  "query": "search for leather wallet and order it",
  "dom_snapshot": [
    { "id": 0, "tag": "input", "text": "Search products", "type": "search" },
    { "id": 1, "tag": "button", "text": "Add to Cart" }
  ],
  "history": [
    { "action": "CLICK", "elementId": 0 },
    { "action": "TYPE", "elementId": 0, "text": "leather wallet" }
  ]
}
```

### Response Format

```json
{
  "action": "CLICK",
  "elementId": 3
}
```

or

```json
{
  "action": "TYPE",
  "elementId": 0,
  "text": "leather wallet"
}
```

or

```json
{
  "action": "DONE",
  "summary": "Wallet added to cart and checkout started."
}
```

### Supported Actions

- `CLICK` - Click on an element
- `TYPE` - Type text into an input field
- `DONE` - Mark the command as completed

## Configuration

You can customize the agent behavior by modifying the `config.ts` file:

```typescript
export const AI_AGENT_CONFIG = {
  DEFAULT_API_ENDPOINT: 'http://localhost:8000/plan',
  MAX_STEPS: 10,
  STEP_DELAY: 500,
  HIGHLIGHT_DURATION: 1500,
  TYPING_SPEED: 50,
  REQUEST_TIMEOUT: 30000
};
```

## Safety Features

- **Step Limit**: Prevents infinite loops (max 10 steps by default)
- **Element Validation**: Ensures elements exist before interaction
- **Error Handling**: Graceful error recovery and user feedback
- **Timeouts**: Prevents hanging requests
- **Visual Feedback**: Highlights elements before interaction

## DOM Element Detection

The agent automatically detects and tags interactive elements:

- Buttons (`button`, `[role="button"]`)
- Links (`a[href]`)
- Input fields (`input`, `textarea`, `select`)
- Clickable elements (`[onclick]`, `[tabindex="0"]`)
- Custom interactive elements (`.clickable`, `[data-testid]`)

Elements are filtered to exclude:
- Hidden elements (`display: none`, `visibility: hidden`)
- Disabled elements
- Elements with zero dimensions
- Elements with `aria-hidden="true"`

## Error Handling

The agent includes comprehensive error handling:

- Network timeouts and connection errors
- Invalid backend responses
- Missing DOM elements
- User input validation
- Step limit exceeded protection

## Performance Optimizations

- **Minimal DOM Snapshots**: Only essential element data is sent
- **Debounced Commands**: Prevents duplicate API calls
- **Efficient Element Selection**: Uses optimized CSS selectors
- **Timeout Protection**: Prevents hanging requests
- **Step Delays**: Reasonable delays between actions for better UX

## Browser Support

The agent requires modern browser features:
- Fetch API
- Promises
- Modern CSS selectors
- Event listeners
- Dataset API

## Development

### File Structure

```
src/aiAgent/
├── CommandBar.tsx     # Main UI component
├── DomObserver.ts     # DOM scanning and tagging
├── Executor.ts        # Action execution
├── useNavigator.ts    # Main coordination hook
├── types.ts           # TypeScript interfaces
├── config.ts          # Configuration settings
├── utils.ts           # Helper functions
├── index.ts           # Module exports
└── README.md          # This file
```

### Adding New Action Types

To add new action types:

1. Update the `AgentAction` type in `types.ts`
2. Add execution logic in `Executor.ts`
3. Update validation in `validateAction()`
4. Update the backend to return the new action type

### Debugging

Enable debug logging by setting:

```javascript
localStorage.setItem('ai-agent-debug', 'true');
```

This will log detailed information about DOM scanning, API calls, and action execution.

## Security Considerations

- Input sanitization prevents XSS attacks
- API requests are validated and typed
- DOM interactions are sandboxed to tagged elements
- No arbitrary code execution from backend responses
- Request timeouts prevent DoS scenarios

## Troubleshooting

### Common Issues

1. **"No interactive elements found"** - The page may be loading or have no interactive elements
2. **"Element not found"** - The DOM may have changed between scanning and execution
3. **API timeout** - Check if the backend service is running and accessible
4. **Command not working** - Try simpler commands or check the backend logs

### Debug Steps

1. Check browser console for errors
2. Verify backend service is running
3. Test with simple commands first
4. Check network tab for API request/response
5. Enable debug logging for detailed information
