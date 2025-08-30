# AI Website Navigator Backend

A powerful FastAPI backend service that provides AI-powered website navigation capabilities using GPT-4o-mini and RAG (Retrieval-Augmented Generation) for intelligent web automation.

## Features

🤖 **AI-Powered Decision Making**: Uses GPT-4o-mini to understand user intents and plan website navigation actions

🧠 **RAG System**: Learns from website patterns and user interactions to improve decision quality

⚡ **High Performance**: Async/await architecture with caching and rate limiting

🛡️ **Production Ready**: Comprehensive error handling, logging, and monitoring

🔧 **Extensible**: Modular design for easy customization and extension

## Quick Start

### 1. Installation

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## API Endpoints

### Main Navigation Endpoint

**POST `/plan`** - Get next action for AI navigation

```json
{
  "query": "search for leather wallet and add to cart",
  "dom_snapshot": [
    {
      "id": 0,
      "tag": "input",
      "text": "Search products",
      "type": "search",
      "placeholder": "Search..."
    },
    {
      "id": 1,
      "tag": "button", 
      "text": "Add to Cart"
    }
  ],
  "history": [
    {
      "action": "CLICK",
      "elementId": 0
    }
  ]
}
```

**Response:**
```json
{
  "action": "TYPE",
  "elementId": 0,
  "text": "leather wallet",
  "reasoning": "User wants to search for leather wallet, so type the search term",
  "confidence": 0.95
}
```

### Other Endpoints

- **GET `/`** - Service information
- **GET `/health`** - Health check
- **GET `/stats`** - Service statistics
- **POST `/feedback`** - Submit interaction feedback for learning
- **POST `/clear-cache`** - Clear request cache (dev only)
- **POST `/reset-rag`** - Reset RAG knowledge base (dev only)

## Architecture

### Core Components

1. **AI Engine** (`ai_engine.py`)
   - Intent analysis using GPT-4o-mini
   - Action planning and decision making
   - Context-aware reasoning

2. **RAG System** (`rag_system.py`)
   - Website pattern learning and storage
   - Vector similarity search using ChromaDB
   - Continuous learning from interactions

3. **FastAPI Application** (`main.py`)
   - API routes and middleware
   - Error handling and validation
   - Rate limiting and caching

4. **Models** (`models.py`)
   - Pydantic models for type safety
   - Request/response schemas
   - Data validation

5. **Utilities** (`utils.py`)
   - Rate limiting and caching
   - Input validation and sanitization
   - Health checks and monitoring

### Data Flow

```
User Query → Intent Analysis → RAG Context → Action Planning → Response
     ↓                                                          ↑
DOM Snapshot → Website Context → Pattern Matching → Execution Plan
```

## Configuration

Key configuration options in `config.py`:

```python
# AI Configuration
openai_api_key: str          # OpenAI API key
openai_model: str            # Model to use (gpt-4o-mini)
temperature: float           # AI creativity (0-1)
max_tokens: int              # Response length limit

# Performance
cache_ttl_seconds: int       # Cache duration
max_requests_per_minute: int # Rate limiting

# RAG System
embedding_model: str         # Sentence transformer model
chroma_persist_directory: str # Vector DB storage path
```

## AI Decision Process

### 1. Intent Analysis
The AI analyzes user queries to understand:
- Primary intent (SEARCH, ADD_TO_CART, CHECKOUT, etc.)
- Entities mentioned (products, quantities, etc.)
- Required steps to fulfill the intent

### 2. Context Building
RAG system provides:
- Website pattern recognition
- Similar successful interactions
- Available actions on current page

### 3. Action Planning
Combines intent and context to:
- Plan multi-step sequences
- Select optimal next action
- Provide reasoning for decisions

### 4. Learning
System learns from:
- Successful interaction patterns
- User feedback
- Website structure analysis

## Supported Actions

| Action Type | Description | Parameters |
|-------------|-------------|------------|
| `CLICK` | Click on an element | `elementId` |
| `TYPE` | Type text into input | `elementId`, `text` |
| `DONE` | Mark task complete | `summary` |

## RAG Knowledge Base

The system maintains knowledge about:

### Website Patterns
- Common e-commerce UI patterns
- Search functionality patterns
- Navigation structures
- Cart and checkout flows

### Action Sequences
- Multi-step task completion
- Successful interaction chains
- Alternative approaches
- Error recovery patterns

### Learning Mechanisms
- Automatic pattern extraction
- Feedback incorporation
- Similarity-based retrieval
- Continuous improvement

## Production Deployment

### Environment Variables

Required:
```env
OPENAI_API_KEY=your_key_here
ENVIRONMENT=production
```

Optional:
```env
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourapp.com
MAX_REQUESTS_PER_MINUTE=100
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks

The service provides health checks for:
- OpenAI API connectivity
- Embedding model availability
- ChromaDB accessibility
- Overall service status

## Testing

Run the test suite:

```bash
pytest test_main.py -v
```

Test coverage includes:
- API endpoint functionality
- AI decision making
- RAG system operations
- Input validation
- Error handling
- Rate limiting

## Monitoring and Logging

### Structured Logging
- Request/response logging
- Performance metrics
- Error tracking
- AI decision reasoning

### Metrics
- Request latency
- Cache hit rates
- AI confidence scores
- Success rates

## Security Features

- Input sanitization and validation
- Rate limiting per client
- CORS configuration
- Error message sanitization
- Request timeout protection

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check API key validity
   - Verify rate limits
   - Monitor token usage

2. **ChromaDB Issues**
   - Check disk space
   - Verify write permissions
   - Consider database reset

3. **Performance Issues**
   - Monitor cache hit rates
   - Check embedding model memory
   - Optimize rate limits

### Debug Mode

Set `LOG_LEVEL=DEBUG` for detailed logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

### Development Tools

```bash
# Clear cache
curl -X POST http://localhost:8000/clear-cache

# Reset RAG knowledge
curl -X POST http://localhost:8000/reset-rag

# Get service stats
curl http://localhost:8000/stats
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting guide
- Review logs for error details
- Submit issues with reproduction steps
- Include environment details
