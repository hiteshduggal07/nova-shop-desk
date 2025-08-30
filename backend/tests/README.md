# AI Website Navigator Backend - Test Suite

A comprehensive test suite for the AI Website Navigator Backend API with over 150+ test cases covering all aspects of the system.

## 📋 Test Coverage

### 🔌 API Endpoint Tests (`test_api_endpoints.py`)
- **Root Endpoint**: Service information and health
- **Health Check**: Service status and component health
- **Stats Endpoint**: Performance metrics and statistics
- **Plan Endpoint**: Main AI navigation logic
  - Success scenarios with various DOM structures
  - Input validation (empty queries, invalid DOM)
  - Malicious input sanitization
  - Different action types (CLICK, TYPE, DONE)
  - Error handling and AI engine failures
- **Feedback Endpoint**: Learning and improvement
- **Rate Limiting**: Protection against abuse
- **Caching**: Performance optimization
- **Error Handling**: Comprehensive error scenarios
- **Development Endpoints**: Cache clearing and RAG reset

### 🤖 AI Engine Tests (`test_ai_engine.py`)
- **Intent Analysis**: Natural language understanding
  - Search, add-to-cart, checkout, navigation intents
  - Multi-step complex scenarios
  - Intent confidence scoring
  - Error handling and fallbacks
- **Action Planning**: Multi-step action sequences
  - First step, middle step, completion planning
  - Alternative action consideration
  - Context-aware decision making
- **Decision Making**: Complete AI workflow
  - Integration with RAG context
  - Complex DOM structure handling
  - Website context analysis
- **OpenAI Integration**: GPT-4o-mini communication
  - Response parsing and validation
  - Error recovery and timeouts
  - JSON format handling

### 🧠 RAG System Tests (`test_rag_system.py`)
- **System Initialization**: Knowledge base setup
- **Pattern Management**: Website pattern storage and retrieval
- **Vector Search**: Similarity-based pattern matching
- **Learning Mechanisms**: Continuous improvement
  - Successful interaction learning
  - Pattern extraction and storage
  - Incremental learning from feedback
- **Context Enhancement**: Website understanding
- **Knowledge Base Operations**: CRUD operations
- **Error Handling**: Database and embedding errors

### 🔄 Integration Tests (`test_integration.py`)
- **Complete Workflows**: End-to-end scenarios
  - Simple search workflow (4 steps)
  - Add-to-cart workflow
  - Checkout process
  - Complex multi-step scenarios
- **RAG Learning Integration**: Pattern learning and usage
- **Error Recovery**: Graceful degradation
- **Feedback Loop**: Learning from user feedback
- **Multi-step State Management**: History tracking

### ⚡ Performance Tests (`test_performance.py`)
- **Response Time**: Single request performance
- **Caching Performance**: Cache hit optimization
- **Sequential Load**: Multiple request handling
- **Concurrent Load**: Parallel request processing
- **Large Data Handling**: Big DOM snapshots and histories
- **Stress Testing**: High load scenarios (50+ requests)
- **Memory Usage**: Resource consumption monitoring
- **Scalability Limits**: Breaking point identification

### 🔍 Edge Case Tests (`test_edge_cases.py`)
- **Input Validation**: Extreme input scenarios
  - Very long queries (10KB+)
  - Unicode and special characters
  - Malformed JSON requests
  - Negative and duplicate element IDs
- **AI Engine Edge Cases**: Unusual AI responses
  - Invalid element IDs
  - Malformed responses
  - Timeout scenarios
  - Extreme confidence values
- **RAG System Edge Cases**: Knowledge base issues
  - Empty knowledge base
  - Corrupted patterns
  - Database connection errors
- **Concurrency Edge Cases**: Race conditions
- **Resource Limits**: Maximum values and boundaries
- **Async Operations**: Cancellation and timeout handling

## 🚀 Running Tests

### Quick Start
```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type performance
python run_tests.py --type edge
```

### Advanced Usage
```bash
# Run with coverage report
python run_tests.py --coverage

# Run tests in parallel (faster)
python run_tests.py --parallel

# Include stress tests (slow)
python run_tests.py --stress

# Run specific test file
python run_tests.py --file test_api_endpoints.py

# Run specific test function
python run_tests.py --file test_ai_engine.py --test test_analyze_intent_success

# Verbose output
python run_tests.py --verbose
```

### Direct pytest Usage
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_endpoints.py

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m "api"       # Only API tests
pytest -m "performance"  # Only performance tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test class
pytest tests/test_ai_engine.py::TestAIDecisionEngine

# Run with custom verbosity
pytest -v tests/test_integration.py
```

## 📊 Test Metrics

### Coverage Targets
- **Overall Coverage**: >90%
- **Critical Paths**: >95%
- **API Endpoints**: 100%
- **AI Engine**: >90%
- **RAG System**: >85%

### Performance Benchmarks
- **Single Request**: <2 seconds
- **Cached Request**: <0.1 seconds
- **Concurrent Requests**: 95% success rate
- **Stress Test**: 50 requests with 90% success
- **Memory Usage**: <10MB per request

### Test Categories Distribution
- **Unit Tests**: ~60 tests
- **Integration Tests**: ~30 tests
- **Performance Tests**: ~20 tests
- **Edge Cases**: ~40 tests
- **Total**: 150+ comprehensive tests

## 🛠️ Test Architecture

### Test Structure
```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_api_endpoints.py    # API endpoint tests
├── test_ai_engine.py        # AI engine unit tests
├── test_rag_system.py       # RAG system tests
├── test_integration.py      # End-to-end workflow tests
├── test_performance.py      # Performance and stress tests
└── test_edge_cases.py       # Edge cases and error handling
```

### Fixtures and Mocking
- **Mock Dependencies**: OpenAI, ChromaDB, SentenceTransformers
- **Test Data**: Sample DOM elements, navigation requests
- **Environment Setup**: Test database, clean state
- **Rate Limiting**: Disabled for tests
- **Caching**: Isolated test cache

### Test Isolation
- Each test runs in isolation
- Mocked external dependencies
- Clean state between tests
- No shared test data
- Independent test databases

## 🔧 Configuration

### pytest.ini
- Test discovery patterns
- Marker definitions
- Warning filters
- Async test support
- Output formatting

### Environment Variables
```bash
# Test environment
ENVIRONMENT=test
OPENAI_API_KEY=test_key_12345
LOG_LEVEL=WARNING

# Disable external services
CHROMA_PERSIST_DIRECTORY=/tmp/test_chroma
```

## 📈 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r test_requirements.txt
      - run: python run_tests.py --coverage
      - uses: codecov/codecov-action@v3
```

## 🐛 Debugging Tests

### Common Issues
1. **Import Errors**: Check PYTHONPATH and module structure
2. **Mock Failures**: Verify mock patches match actual imports
3. **Async Issues**: Ensure pytest-asyncio is properly configured
4. **Database Errors**: Check test database isolation

### Debug Commands
```bash
# Run single test with full output
pytest -s -vv tests/test_api_endpoints.py::TestPlanEndpoint::test_plan_endpoint_success

# Drop into debugger on failure
pytest --pdb tests/test_ai_engine.py

# Show local variables on failure
pytest --tb=long tests/test_integration.py

# Capture and show print statements
pytest -s tests/test_performance.py
```

## 📝 Writing New Tests

### Test Naming Convention
- File: `test_<module_name>.py`
- Class: `Test<FeatureName>`
- Method: `test_<specific_behavior>`

### Test Categories
- Mark tests with appropriate markers:
  - `@pytest.mark.unit`
  - `@pytest.mark.integration`
  - `@pytest.mark.performance`
  - `@pytest.mark.slow`

### Best Practices
1. **Arrange-Act-Assert** pattern
2. **Descriptive test names** explaining what is tested
3. **Mock external dependencies** for isolation
4. **Test both happy path and error cases**
5. **Use fixtures** for common test data
6. **Clean up resources** after tests

## 🎯 Quality Gates

### Test Requirements for CI/CD
- All tests must pass
- Coverage > 90%
- No critical security issues
- Performance benchmarks met
- No flaky tests (consistent results)

### Code Quality Checks
- Type checking with mypy
- Linting with flake8/black
- Security scanning
- Dependency vulnerability checks

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Test-Driven Development Best Practices](https://testdriven.io/)
