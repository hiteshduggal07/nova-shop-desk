# AI Assistant Integration Guide

## Overview

The AI Assistant has been successfully integrated with your e-commerce website. It can navigate the site based on natural language prompts and perform actions like searching for products, adding items to cart, and proceeding to checkout.

## How to Use

### 1. Starting the Servers

**Backend Server:**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

**Frontend Server:**
```bash
npm run dev
```

### 2. Using the AI Assistant

1. **Open the website** at `http://localhost:8080` (or the port shown by Vite)
2. **Open the AI Assistant** by:
   - Clicking the "AI Assistant" button in the bottom-right corner
   - Using the keyboard shortcut `Ctrl+K` or `Cmd+K`

### 3. Example Commands

Try these natural language commands:

#### Shopping Commands:
- "Search for leather wallet and add it to cart"
- "Find products under $50"
- "Add the first product to my cart"
- "Go to the checkout page"
- "Navigate to the home page"

#### Navigation Commands:
- "Show me all products"
- "Go to the cart"
- "Take me to the products page"

## How It Works

### Architecture

```
Frontend (React) ←→ AI Agent ←→ Backend API ←→ OpenAI GPT-4
                     ↓
                DOM Observer
                     ↓
                Action Executor
```

### Process Flow

1. **User Input**: User types a command in natural language
2. **DOM Analysis**: The AI agent scans the current page for interactive elements
3. **AI Decision**: The backend uses GPT-4 to decide what action to take
4. **Action Execution**: The frontend executes the action (click, type, etc.)
5. **Iteration**: Process repeats until the task is complete

### Key Components

#### Frontend (`src/aiAgent/`)
- **CommandBar.tsx**: The UI component for the AI assistant
- **useNavigator.ts**: React hook managing the AI navigation logic
- **DomObserver.ts**: Scans and collects interactive DOM elements
- **Executor.ts**: Executes actions on DOM elements
- **config.ts**: Configuration settings

#### Backend (`backend/`)
- **main.py**: FastAPI server with CORS and endpoints
- **ai_engine.py**: GPT-4 integration for decision making
- **rag_system.py**: Knowledge base for website patterns
- **models.py**: Data models for API communication

## Configuration

### Environment Variables (backend/.env)
```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
ENVIRONMENT=development
API_PORT=9000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

### API Endpoints
- `GET /health` - Health check
- `POST /plan` - Main AI planning endpoint
- `POST /feedback` - Submit feedback for learning
- `GET /stats` - Service statistics

## Customization

### Adding New Commands
1. The AI is trained on e-commerce patterns and can handle most shopping-related commands
2. For specific functionality, you can enhance the RAG system in `rag_system.py`

### Styling the AI Assistant
Modify `CommandBar.tsx` to change the appearance and behavior of the AI assistant interface.

### Adjusting AI Behavior
- Modify prompts in `ai_engine.py`
- Adjust configuration in `config.ts`
- Add patterns to `rag_system.py`

## Troubleshooting

### Common Issues

1. **Backend not starting**: Check if OpenAI API key is set correctly
2. **Assistant not responding**: Verify backend is running on port 9000
3. **Actions not working**: Check browser console for DOM-related errors

### Debug Tools
- Backend logs: Check console output from uvicorn
- Frontend logs: Check browser developer tools console
- API testing: Use `/docs` endpoint for interactive API documentation

## Security Notes

- The OpenAI API key should be kept secure
- The assistant only interacts with DOM elements on your website
- All actions are executed in the user's browser context

## Performance

- The AI assistant processes commands in real-time
- Actions are executed with visual feedback (highlighting)
- Responses are cached for better performance

## Next Steps

1. **Test the integration** with various commands
2. **Customize the prompts** based on your specific use cases
3. **Add more sophisticated patterns** to the RAG system
4. **Monitor usage** and improve based on user feedback
