# Contributing to Financial AI Agents

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/QuantumCoderX7/Fin-Agent/issues)
2. If not, create a new issue using the Bug Report template
3. Provide detailed information:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Error logs

### Suggesting Features

1. Check existing [Feature Requests](https://github.com/QuantumCoderX7/Fin-Agent/issues?q=is%3Aissue+label%3Aenhancement)
2. Create a new issue using the Feature Request template
3. Describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative approaches considered
   - Use cases and benefits

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Follow the coding standards
   - Add tests for new features
   - Update documentation
   - Ensure all tests pass

4. **Commit your changes**:
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes
   - `refactor:` Code refactoring
   - `test:` Test additions/changes
   - `chore:` Maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Use the PR template
   - Link related issues
   - Provide clear description
   - Request review

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Groq API key (free at console.groq.com)

### Local Setup

1. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Fin-Agent.git
   cd Fin-Agent
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Set up frontend**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run tests**:
   ```bash
   pytest tests/
   ```

6. **Start development server**:
   ```bash
   python run_server.py
   ```

## Coding Standards

### Python Code Style

- Follow PEP 8
- Use Black for formatting: `black app/ tests/`
- Use isort for imports: `isort app/ tests/`
- Maximum line length: 100 characters
- Use type hints where possible

### JavaScript/React Code Style

- Use ESLint configuration
- Use Prettier for formatting
- Follow React best practices
- Use functional components with hooks

### Documentation

- Add docstrings to all functions and classes
- Use Google-style docstrings
- Update README for significant changes
- Add inline comments for complex logic

### Testing

- Write unit tests for new features
- Maintain test coverage above 80%
- Use pytest for Python tests
- Use Jest for JavaScript tests
- Test edge cases and error conditions

## Project Structure

```
financial-ai-agents/
├── app/                    # Backend application
│   ├── agents/            # AI agent implementations
│   ├── api/               # API routes and middleware
│   ├── config/            # Configuration management
│   ├── models/            # Pydantic models
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── frontend/              # React frontend
│   ├── public/           # Static files
│   └── src/              # React components
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── performance/      # Performance tests
├── docs/                  # Documentation
├── config/                # Environment configs
└── .github/              # GitHub configuration
```

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_research_agent.py

# With coverage
pytest --cov=app --cov-report=html

# Integration tests only
pytest tests/integration/

# Performance tests
pytest tests/performance/
```

### Writing Tests

```python
import pytest
from app.agents.research_agent import ResearchAgent

def test_research_agent_initialization():
    """Test that research agent initializes correctly."""
    agent = ResearchAgent(api_key="test-key")
    assert agent is not None
    assert agent.model_name == "qwen/qwen3-32b"

@pytest.mark.asyncio
async def test_research_analysis():
    """Test research analysis functionality."""
    agent = ResearchAgent(api_key="test-key")
    result = await agent.process_request({
        "topic": "Test topic",
        "sources_limit": 3
    })
    assert result is not None
    assert "headline" in result
```

## Security Guidelines

### Critical Rules

1. **Never commit secrets**:
   - No API keys in code
   - No passwords in code
   - Use environment variables
   - Check with `git diff` before committing

2. **Validate all inputs**:
   - Use Pydantic models
   - Sanitize user input
   - Check for injection attacks

3. **Handle errors securely**:
   - Don't expose internal details
   - Log errors appropriately
   - Use structured error responses

4. **Review dependencies**:
   - Check for known vulnerabilities
   - Keep dependencies updated
   - Use `pip audit` regularly

## Review Process

### What Reviewers Look For

- Code quality and style
- Test coverage
- Documentation
- Security considerations
- Performance implications
- Breaking changes

### Review Timeline

- Initial review: Within 3 business days
- Follow-up reviews: Within 2 business days
- Approval requires: 1 maintainer approval

## Getting Help

- **Questions**: Open a Discussion on GitHub
- **Bugs**: Create an Issue
- **Security**: See SECURITY.md
- **Chat**: Join our Discord (if available)

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort! 🙏
