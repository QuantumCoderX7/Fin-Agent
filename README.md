# Financial AI Agents

A comprehensive financial AI agent system that provides professional-grade financial analysis through specialized AI agents. The system offers three main capabilities: Financial Research Analysis, Stock Market Analysis, and RAG Response Quality Evaluation.

## 🚀 Features

- **🔍 Financial Research Agent**: Comprehensive market research with multi-source data aggregation
- **📈 Stock Market Analyst**: Individual stock analysis and multi-stock comparison
- **🎯 RAG Evaluator**: Quality assessment of AI-generated financial content
- **⚡ Real-time Streaming**: Server-Sent Events for live response streaming
- **🔐 Enterprise Security**: Rate limiting, input validation, and comprehensive error handling
- **📊 Production Ready**: Docker, Kubernetes, and monitoring configurations included

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Development](#development)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Contributing](#contributing)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- API Keys for external services:
  - Groq API Key (for LLM operations)
  - Phi API Key (for additional AI services)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd financial-ai-agents
   cp .env.example .env
   ```

2. **Configure API keys** in `.env`:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   PHI_API_KEY=your_phi_api_key_here
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**:
   ```bash
   ./scripts/start.sh development
   # or
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health
   - System Status: http://localhost:8000/status

### Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f financial-ai-agents
```

## 📚 API Documentation

### Core Endpoints

#### Research Agent
- `POST /api/v1/research/analyze` - Conduct financial research analysis
- `GET /api/v1/research/topics` - Get suggested research topics
- `POST /api/v1/research/stream` - Stream research analysis in real-time

#### Stock Analysis
- `POST /api/v1/stocks/analyze` - Analyze individual stocks
- `POST /api/v1/stocks/compare` - Compare multiple stocks
- `GET /api/v1/stocks/{symbol}/info` - Get basic stock information
- `POST /api/v1/stocks/stream` - Stream stock analysis

#### RAG Evaluation
- `POST /api/v1/evaluation/assess` - Evaluate RAG response quality
- `GET /api/v1/evaluation/metrics` - Get evaluation criteria definitions
- `POST /api/v1/evaluation/batch` - Batch evaluate multiple responses

#### System Monitoring
- `GET /health` - Basic health check
- `GET /status` - Detailed system status
- `GET /streaming/stats` - Streaming connection statistics

### Example Usage

```python
import requests

# Research Analysis
response = requests.post("http://localhost:8000/api/v1/research/analyze", json={
    "topic": "Federal Reserve interest rate policy 2024",
    "sources_limit": 5,
    "include_outlook": True
})

# Stock Analysis
response = requests.post("http://localhost:8000/api/v1/stocks/analyze", json={
    "symbols": ["AAPL", "GOOGL"],
    "analysis_type": "comprehensive",
    "include_comparison": True
})

# RAG Evaluation
response = requests.post("http://localhost:8000/api/v1/evaluation/assess", json={
    "query": "What is the current market outlook?",
    "response": "The market shows positive trends...",
    "context": ["Market data shows growth", "Analyst reports are optimistic"]
})
```

For comprehensive examples, see [API Usage Examples](docs/api-usage-examples.md).

## 🚀 Deployment

### Docker Deployment

#### Development
```bash
./scripts/deploy.sh development
```

#### Production
```bash
./scripts/deploy.sh production
```

### Kubernetes Deployment

1. **Update configuration**:
   ```bash
   # Edit k8s-deployment.yaml with your settings
   kubectl apply -f k8s-deployment.yaml
   ```

2. **Verify deployment**:
   ```bash
   kubectl get pods -n financial-ai-agents
   kubectl get services -n financial-ai-agents
   ```

### Environment-Specific Configurations

- **Development**: `config/development.env`
- **Staging**: `config/staging.env`
- **Production**: `config/production.env`

For detailed deployment instructions, see [Deployment Guide](docs/deployment-guide.md).

## 💻 Development

### Project Structure

```
financial-ai-agents/
├── app/                    # Application source code
│   ├── main.py            # FastAPI application entry point
│   ├── config/            # Configuration management
│   ├── api/               # API routes and middleware
│   ├── services/          # Business logic layer
│   ├── agents/            # AI agent implementations
│   ├── models/            # Pydantic models
│   └── utils/             # Utilities and helpers
├── config/                # Environment configurations
├── docs/                  # Documentation
├── monitoring/            # Monitoring configurations
├── scripts/               # Deployment and utility scripts
├── tests/                 # Test suite
├── docker-compose*.yml    # Docker configurations
├── k8s-deployment.yaml    # Kubernetes deployment
└── requirements.txt       # Python dependencies
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/performance/
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq LLM API key | - | ✅ |
| `PHI_API_KEY` | Phi API key | - | ✅ |
| `DEBUG` | Enable debug mode | `false` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `API_V1_PREFIX` | API version prefix | `/api/v1` | ❌ |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | ❌ |
| `DEFAULT_MODEL` | Default LLM model | `qwen/qwen3-32b` | ❌ |
| `MAX_SOURCES` | Max research sources | `10` | ❌ |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | `300` | ❌ |

### Security Configuration

The application includes comprehensive security features:

- **Rate Limiting**: Configurable per-minute and per-hour limits
- **Input Validation**: Comprehensive request validation and sanitization
- **CORS Protection**: Configurable cross-origin resource sharing
- **Error Handling**: Structured error responses with correlation IDs
- **Health Monitoring**: Multiple health check endpoints

## 📊 Monitoring

### Prometheus Metrics

The application exposes metrics at `/metrics` for Prometheus scraping:

- Request rates and response times
- Error rates by endpoint
- Active streaming connections
- Resource usage metrics

### Grafana Dashboard

A pre-configured Grafana dashboard is available at `monitoring/grafana-dashboard.json` with:

- Request rate and error rate monitoring
- Response time percentiles
- Resource usage (CPU, memory)
- Active connection tracking

### Health Checks

Multiple health check endpoints provide different levels of detail:

- `/health` - Basic health status
- `/status` - Comprehensive system information
- `/streaming/stats` - Real-time streaming statistics

### Alerting

Prometheus alerting rules are configured for:

- High error rates
- Elevated response times
- Resource usage thresholds
- Service availability

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite**: `pytest`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR
- Use meaningful commit messages

## 📖 Documentation

- [API Usage Examples](docs/api-usage-examples.md) - Comprehensive API usage examples
- [Integration Guide](docs/integration-guide.md) - Integration patterns and best practices
- [Deployment Guide](docs/deployment-guide.md) - Deployment instructions for various environments
- [Security Guide](docs/security.md) - Security considerations and best practices
- [Streaming Guide](docs/streaming.md) - Real-time streaming implementation details

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Open an issue on GitHub
- **Health Check**: Visit `/health` endpoint for service status
- **API Docs**: Visit `/docs` for interactive API documentation

## 🔄 Version History

- **v1.0.0** - Initial release with full feature set
  - Financial Research Agent
  - Stock Market Analyst
  - RAG Evaluator
  - Real-time streaming
  - Production deployment configurations