# Financial AI Agents Documentation

Welcome to the comprehensive documentation for the Financial AI Agents system. This documentation covers everything from basic usage to advanced deployment and monitoring configurations.

## 📚 Documentation Index

### Getting Started
- [Main README](../README.md) - Project overview and quick start guide
- [API Usage Examples](api-usage-examples.md) - Comprehensive API usage examples with code samples
- [Integration Guide](integration-guide.md) - Integration patterns, SDKs, and best practices

### Deployment & Operations
- [Deployment Guide](deployment-guide.md) - Complete deployment instructions for all environments
- [Security Guide](security.md) - Security considerations and best practices
- [Streaming Guide](streaming.md) - Real-time streaming implementation details

### System Architecture

#### Core Components
The Financial AI Agents system consists of three main specialized agents:

1. **Financial Research Agent**
   - Conducts comprehensive market research
   - Aggregates data from multiple authoritative sources
   - Generates structured reports with executive summaries
   - Provides future market outlook analysis

2. **Stock Market Analyst**
   - Analyzes individual stocks with key financial metrics
   - Performs multi-stock comparisons
   - Provides investment recommendations
   - Tracks market sentiment and trends

3. **RAG Evaluator Agent**
   - Assesses quality of AI-generated financial content
   - Scores responses on multiple criteria (faithfulness, relevance, completeness)
   - Provides actionable improvement recommendations
   - Supports batch evaluation workflows

#### Technical Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Web Browser   │    │   API Clients   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Load Balancer        │
                    │        (nginx)            │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     FastAPI Gateway       │
                    │   (Rate Limiting, Auth)   │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│ Research Service  │   │  Stock Service    │   │Evaluation Service │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌─────────┴─────────┐
│ Research Agent    │   │  Stock Agent      │   │ RAG Evaluator     │
└─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
          │                       │                       │
┌─────────┴─────────┐   ┌─────────┴─────────┐             │
│   DuckDuckGo      │   │   Yahoo Finance   │             │
│   Newspaper4k     │   │      API          │             │
└───────────────────┘   └───────────────────┘             │
                                                          │
                        ┌─────────────────────────────────┘
                        │
              ┌─────────┴─────────┐
              │    Groq LLM API   │
              │   (All Agents)    │
              └───────────────────┘
```

## 🚀 Quick Navigation

### For Developers
- **New to the project?** Start with the [Main README](../README.md)
- **Want to integrate?** Check the [Integration Guide](integration-guide.md)
- **Need examples?** See [API Usage Examples](api-usage-examples.md)
- **Building clients?** Review the SDK examples in [Integration Guide](integration-guide.md#sdk-and-client-libraries)

### For DevOps/SRE
- **Deploying the system?** Follow the [Deployment Guide](deployment-guide.md)
- **Setting up monitoring?** Use the configurations in `/monitoring/`
- **Security concerns?** Review the [Security Guide](security.md)
- **Performance tuning?** Check the optimization sections in [Deployment Guide](deployment-guide.md#performance-tuning)

### For API Users
- **Learning the API?** Start with [API Usage Examples](api-usage-examples.md)
- **Real-time features?** See [Streaming Guide](streaming.md)
- **Error handling?** Check error handling sections in [Integration Guide](integration-guide.md#error-handling)
- **Rate limits?** Review limits in [Integration Guide](integration-guide.md#rate-limiting)

## 🔧 Configuration Reference

### Environment Variables

| Category | Variable | Description | Default | Required |
|----------|----------|-------------|---------|----------|
| **API Keys** | `GROQ_API_KEY` | Groq LLM API key | - | ✅ |
| | `PHI_API_KEY` | Phi API key | - | ✅ |
| **Application** | `APP_NAME` | Application name | `Financial AI Agents` | ❌ |
| | `DEBUG` | Enable debug mode | `false` | ❌ |
| | `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| **API** | `API_V1_PREFIX` | API version prefix | `/api/v1` | ❌ |
| | `CORS_ORIGINS` | Allowed CORS origins | `["*"]` | ❌ |
| **AI Models** | `DEFAULT_MODEL` | Default LLM model | `qwen/qwen3-32b` | ❌ |
| | `MAX_SOURCES` | Max research sources | `10` | ❌ |
| | `REQUEST_TIMEOUT` | Request timeout (seconds) | `300` | ❌ |
| **Security** | `RATE_LIMIT_PER_MINUTE` | Rate limit per minute | `60` | ❌ |
| | `RATE_LIMIT_PER_HOUR` | Rate limit per hour | `500` | ❌ |
| | `MAX_REQUEST_SIZE_MB` | Max request size | `5` | ❌ |

### Configuration Files

- **Development**: `config/development.env`
- **Staging**: `config/staging.env`
- **Production**: `config/production.env`
- **Docker**: `docker-compose*.yml`
- **Kubernetes**: `k8s-deployment.yaml`

## 📊 API Reference

### Base URLs
- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

### Authentication
Currently, no client authentication is required. The system uses API keys for external service access only.

### Response Format
All API responses follow a consistent JSON structure:

```json
{
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time": 1.23,
  "request_id": "req_123456789"
}
```

### Error Format
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Detailed error message",
  "details": { ... },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## 🔍 Monitoring & Observability

### Health Checks
- `GET /health` - Basic health status
- `GET /status` - Detailed system information
- `GET /streaming/stats` - Streaming connection statistics

### Metrics
The system exposes Prometheus metrics at `/metrics`:
- Request rates and response times
- Error rates by endpoint
- Active streaming connections
- Resource usage metrics

### Logging
Structured logging with configurable levels:
- **Development**: Human-readable format
- **Production**: JSON format for log aggregation

### Alerting
Pre-configured Prometheus alerts for:
- High error rates (>10% for 2 minutes)
- Elevated response times (>2s 95th percentile)
- Resource usage thresholds (>90% memory, >80% CPU)
- Service availability issues

## 🛠️ Development Workflow

### Local Development
1. **Setup**: Follow [Quick Start](../README.md#quick-start)
2. **Testing**: Run `pytest` for comprehensive test suite
3. **Code Quality**: Use `black`, `flake8`, and `mypy`
4. **Documentation**: Update docs for API changes

### Testing Strategy
- **Unit Tests**: Mock external APIs, test business logic
- **Integration Tests**: Test complete API workflows
- **Performance Tests**: Load testing with concurrent requests
- **Security Tests**: Validate input sanitization and rate limiting

### Deployment Pipeline
1. **Development**: Local testing and validation
2. **Staging**: Production-like environment testing
3. **Production**: Blue-green deployment with health checks

## 🔐 Security Considerations

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- CORS configuration for web clients
- Request size limits

### Infrastructure Security
- Container security with non-root users
- Network policies in Kubernetes
- Secrets management for API keys
- TLS/SSL for all external communications

### Monitoring Security
- Audit logging for all API requests
- Anomaly detection for unusual patterns
- Security alerts for potential threats

## 📈 Performance Optimization

### Application Level
- Async/await for I/O operations
- Connection pooling for external APIs
- Response caching where appropriate
- Streaming for long-running operations

### Infrastructure Level
- Horizontal pod autoscaling
- Resource limits and requests
- Load balancing across instances
- CDN for static content

### Monitoring Performance
- Response time percentiles
- Throughput metrics
- Resource utilization
- Error rate tracking

## 🤝 Contributing

### Getting Started
1. Read the [Contributing Guidelines](../CONTRIBUTING.md)
2. Set up your development environment
3. Run the test suite to ensure everything works
4. Make your changes and add tests
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Add comprehensive tests for new features
- Update documentation for API changes
- Use meaningful commit messages

### Review Process
- All changes require code review
- Tests must pass before merging
- Documentation must be updated
- Security implications must be considered

## 📞 Support

### Getting Help
- **Documentation**: Check this documentation first
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Health Check**: Visit `/health` endpoint for service status

### Troubleshooting
- Check the [Deployment Guide](deployment-guide.md#troubleshooting) for common issues
- Review application logs for error details
- Verify API key configuration
- Test connectivity to external services

### Community
- Follow our [Code of Conduct](../CODE_OF_CONDUCT.md)
- Participate in discussions and reviews
- Share your use cases and feedback
- Contribute improvements and bug fixes

---

This documentation is continuously updated. For the latest information, always refer to the main repository and check the commit history for recent changes.