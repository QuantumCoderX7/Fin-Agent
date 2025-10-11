# Financial AI Agents - Test Suite

This directory contains the comprehensive test suite for the Financial AI Agents system. The tests are organized into multiple categories to ensure thorough coverage of all system components.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_base_agent.py     # Base agent interface tests
│   ├── test_research_agent.py # Research agent tests
│   ├── test_stock_agent.py    # Stock analysis agent tests
│   ├── test_rag_evaluator.py  # RAG evaluator tests
│   ├── test_*_service.py      # Service layer tests
│   └── test_*.py              # Other unit tests
├── integration/            # Integration tests for API endpoints
│   ├── test_research_endpoints.py
│   ├── test_stock_endpoints.py
│   ├── test_evaluation_endpoints.py
│   └── test_*.py
├── performance/            # Performance and load tests
│   ├── test_load.py           # Load testing
│   └── test_stress.py         # Stress testing
├── fixtures/               # Test data and mock objects
│   ├── sample_data.py         # Sample test data
│   └── mock_responses.py      # Mock API responses
└── README.md              # This file
```

## Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Coverage**: Agents, services, models, utilities
- **Mocking**: All external dependencies are mocked
- **Speed**: Fast execution (< 1 second per test)

### Integration Tests
- **Purpose**: Test complete API workflows
- **Coverage**: FastAPI endpoints, request/response handling
- **Mocking**: External APIs mocked, internal integration tested
- **Speed**: Medium execution (1-5 seconds per test)

### Performance Tests
- **Purpose**: Test system performance under load
- **Coverage**: Concurrent requests, throughput, resource usage
- **Mocking**: External APIs mocked to focus on system performance
- **Speed**: Slow execution (10-60 seconds per test)

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Quick Test Execution

```bash
# Run all unit tests (fastest)
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run performance tests
python run_tests.py performance

# Run complete test suite
python run_tests.py all

# Run quick development tests
python run_tests.py quick
```

### Advanced Test Execution

```bash
# Run with verbose output
python run_tests.py unit --verbose

# Run specific test file
python run_tests.py unit --test tests/unit/test_research_agent.py

# Run specific test function
python run_tests.py unit --test tests/unit/test_research_agent.py::TestResearchAgent::test_validate_request_valid

# Run tests in parallel
python run_tests.py parallel --workers 4

# Generate coverage report
python run_tests.py coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test directory
pytest tests/unit/

# Run with coverage
pytest --cov=app --cov-report=html

# Run with markers
pytest -m "not slow"

# Run in parallel
pytest -n 4
```

## Test Configuration

### pytest.ini
The `pytest.ini` file contains test configuration including:
- Test discovery patterns
- Coverage settings
- Markers for test categorization
- Output formatting
- Timeout settings

### Environment Variables
Tests use the following environment variables:
- `GROQ_API_KEY`: Mock API key for Groq client
- `PHI_API_KEY`: Mock API key for Phi client
- `ENVIRONMENT`: Set to "test"
- `LOG_LEVEL`: Set to "WARNING" to reduce noise

## Test Data and Fixtures

### Sample Data (`fixtures/sample_data.py`)
Provides consistent test data including:
- Sample research topics and search results
- Stock market data and analysis responses
- RAG evaluation queries and contexts
- Performance test request sets

### Mock Responses (`fixtures/mock_responses.py`)
Provides mock objects for external services:
- `MockGroqClient`: Mock AI client responses
- `MockDuckDuckGoSearch`: Mock search results
- `MockNewspaperArticle`: Mock article content
- `MockYFinanceTicker`: Mock stock data
- `MockHTTPXClient`: Mock HTTP requests

## Test Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.performance   # Performance test
@pytest.mark.slow          # Slow-running test
@pytest.mark.external      # Requires external services
@pytest.mark.mock          # Uses mocked dependencies
```

Run tests by marker:
```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Exclude slow tests
pytest -m "unit and not external"  # Unit tests without external deps
```

## Coverage Requirements

The test suite maintains high code coverage standards:
- **Minimum Coverage**: 80%
- **Target Coverage**: 90%+
- **Coverage Reports**: HTML, XML, and terminal output

Coverage exclusions:
- Test files themselves
- Abstract methods
- Debug code
- Error handling for unreachable code

## Performance Benchmarks

### Response Time Targets
- **Unit Tests**: < 1 second each
- **Integration Tests**: < 5 seconds each
- **API Endpoints**: < 30 seconds under normal load
- **Concurrent Requests**: 80%+ success rate with 5+ concurrent users

### Load Testing Scenarios
- **Concurrent Users**: 5-50 simultaneous requests
- **Sustained Load**: 30+ seconds of continuous requests
- **Mixed Workload**: Research, stock, and evaluation requests
- **Resource Limits**: Memory and CPU usage monitoring

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled daily runs

### Test Stages
1. **Dependency Check**: Verify all packages installed
2. **Unit Tests**: Fast component tests
3. **Integration Tests**: API endpoint tests
4. **Coverage Report**: Generate and upload coverage
5. **Performance Tests**: Load and stress tests (on main branch only)

## Debugging Tests

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set
   export PYTHONPATH=$(pwd)
   pytest tests/
   ```

2. **Mock Setup Issues**
   ```python
   # Use fixtures for consistent mock setup
   @pytest.fixture
   def mock_agent(self):
       with patch('app.agents.research_agent.AsyncGroq') as mock:
           yield mock
   ```

3. **Async Test Issues**
   ```python
   # Use pytest-asyncio for async tests
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

### Test Debugging Tools

```bash
# Run with debugging output
pytest --tb=long --capture=no

# Run single test with debugging
pytest tests/unit/test_research_agent.py::TestResearchAgent::test_specific -v -s

# Use pdb for interactive debugging
pytest --pdb tests/unit/test_research_agent.py
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_<component>.py`
- Test classes: `Test<Component>`
- Test methods: `test_<functionality>`

### Test Structure Template
```python
"""
Test module for <Component>.

Brief description of what this module tests.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.components.component import Component
from app.utils.exceptions import ComponentException


class TestComponent:
    """Test suite for Component class."""
    
    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        return Component(config="test")
    
    def test_component_initialization(self, component):
        """Test component initializes correctly."""
        assert component.config == "test"
    
    @pytest.mark.asyncio
    async def test_async_method(self, component):
        """Test async component method."""
        result = await component.async_method()
        assert result is not None
    
    def test_error_handling(self, component):
        """Test component error handling."""
        with pytest.raises(ComponentException):
            component.invalid_operation()
```

### Mock Usage Guidelines
1. Mock external dependencies (APIs, databases)
2. Use fixtures for reusable mocks
3. Verify mock calls when testing interactions
4. Reset mocks between tests

### Performance Test Guidelines
1. Use realistic data sizes
2. Test concurrent scenarios
3. Monitor resource usage
4. Set appropriate timeouts
5. Clean up resources after tests

## Maintenance

### Regular Tasks
- Update test data when APIs change
- Review and update performance benchmarks
- Maintain mock responses for accuracy
- Update documentation for new test patterns

### Test Review Checklist
- [ ] All new code has corresponding tests
- [ ] Tests cover both success and failure scenarios
- [ ] Mocks are properly configured
- [ ] Performance impact is acceptable
- [ ] Documentation is updated

## Support

For test-related questions or issues:
1. Check this documentation
2. Review existing test patterns
3. Run tests with verbose output for debugging
4. Check CI logs for detailed error information

Remember: Good tests are the foundation of reliable software. Write tests that are clear, maintainable, and provide confidence in the system's behavior.