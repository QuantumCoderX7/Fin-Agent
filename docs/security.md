# Security Features Documentation

## Overview

The Financial AI Agents system implements comprehensive security features to protect against common web application vulnerabilities and ensure secure operation in production environments.

## Implemented Security Features

### 1. API Key Validation and Management

#### Startup Validation
- **Enhanced API Key Format Validation**: Validates GROQ and PHI API keys with proper format requirements
  - GROQ keys must start with `gsk_` and be at least 50 characters long
  - PHI keys must start with `sk-` and be at least 40 characters long
- **Comprehensive Security Settings Validation**: Validates all security-related configuration on startup
- **Clear Error Messages**: Provides detailed error messages for missing or invalid API keys

#### Implementation
```python
# API key validation in app/config/settings.py
def validate_api_keys(self) -> None:
    """Validate that required API keys are configured with proper format."""
    # Validates format and provides helpful error messages
```

### 2. Advanced Rate Limiting

#### Multi-Tier Rate Limiting
- **Per-Minute Limits**: Default 60 requests per minute
- **Per-Hour Limits**: Default 1000 requests per hour  
- **Burst Protection**: Default 10 requests per 10 seconds
- **Progressive IP Blocking**: Automatic blocking for repeat offenders

#### Features
- **IP-based Tracking**: Tracks requests per client IP address
- **Proxy Support**: Handles X-Forwarded-For and X-Real-IP headers
- **Automatic Cleanup**: Removes old request records to prevent memory leaks
- **Rate Limit Headers**: Includes rate limit information in response headers

#### Implementation
```python
# Enhanced rate limiting in app/api/middleware.py
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls_per_minute=60, calls_per_hour=1000, burst_limit=10):
        # Multi-tier rate limiting with progressive blocking
```

### 3. Request Validation and Sanitization

#### Security Middleware
- **User Agent Validation**: Blocks suspicious or empty user agents
- **Content Type Validation**: Enforces allowed content types for POST/PUT requests
- **Request Size Limits**: Prevents DoS attacks through oversized requests
- **Header Validation**: Detects suspicious headers that might indicate attacks

#### Input Sanitization
- **XSS Prevention**: Removes script tags and JavaScript URLs
- **SQL Injection Protection**: Detects and blocks SQL injection patterns
- **Command Injection Protection**: Blocks command execution attempts
- **Query Parameter Sanitization**: Sanitizes URL query parameters

#### Implementation
```python
# Security middleware in app/api/middleware.py
class SecurityMiddleware(BaseHTTPMiddleware):
    def _sanitize_query_params(self, request: Request):
        # Comprehensive input sanitization
```

### 4. Enhanced Input Validation

#### Validation Utilities
- **Stock Symbol Validation**: Validates stock ticker format
- **Text Input Validation**: Length constraints and content validation
- **URL Validation**: Ensures proper URL format
- **Numeric Range Validation**: Validates numbers within specified ranges
- **List Validation**: Validates list inputs with size constraints

#### Security Features
- **Input Sanitization**: Removes dangerous patterns from user input
- **Request Size Validation**: Prevents oversized requests
- **Pattern Detection**: Identifies suspicious input patterns

### 5. Security Configuration Management

#### Environment-Based Security
- **Development Mode**: Relaxed security for development
- **Production Mode**: Strict security enforcement
- **Configurable Limits**: Adjustable security parameters

#### Security Validation
- **CORS Validation**: Prevents wildcard CORS in production
- **Timeout Limits**: Enforces maximum request timeouts
- **Source Limits**: Limits maximum data sources for performance

#### Implementation
```python
# Security configuration in app/config/security.py
class SecurityConfig:
    # Centralized security constants and validation
```

### 6. Comprehensive Security Testing

#### Unit Tests
- **API Key Validation Tests**: Tests for all API key scenarios
- **Rate Limiting Tests**: Tests for rate limit enforcement
- **Input Validation Tests**: Tests for input sanitization and validation
- **Security Settings Tests**: Tests for configuration validation

#### Integration Tests
- **End-to-End Security**: Tests security features in full application context
- **Middleware Integration**: Tests middleware interaction
- **Error Response Format**: Tests security error responses

## Security Headers

The system automatically adds security headers to all responses:

```
X-Correlation-ID: <uuid>
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 59
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 999
```

## Configuration

### Environment Variables

```bash
# Required API Keys
GROQ_API_KEY=gsk_...  # Must start with 'gsk_' and be 50+ chars
PHI_API_KEY=sk-...    # Must start with 'sk-' and be 40+ chars

# Security Settings
DEBUG=false           # Enables/disables debug mode security
CORS_ORIGINS=https://yourdomain.com  # Specific origins in production
REQUEST_TIMEOUT=300   # Max 600 seconds
MAX_SOURCES=10        # Max 20 sources
```

### Security Levels

The system automatically adjusts security based on environment:

- **Development** (`DEBUG=true`):
  - Relaxed rate limits
  - Allows all user agents
  - Permits CORS wildcards
  - Disables IP blocking

- **Production** (`DEBUG=false`):
  - Strict rate limits
  - Blocks suspicious user agents
  - Requires specific CORS origins
  - Enables IP blocking

## Error Handling

Security errors return structured responses:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "User-Agent header is required for security purposes.",
  "details": {"field_name": "user_agent"},
  "timestamp": 1640995200.0,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Monitoring and Logging

Security events are logged with appropriate severity levels:

- **Rate Limit Violations**: WARNING level with IP and violation count
- **Suspicious Requests**: WARNING level with details
- **Blocked Requests**: WARNING level with reason
- **API Key Failures**: ERROR level (without exposing keys)

## Best Practices

1. **API Key Management**:
   - Store keys in environment variables
   - Use proper key formats
   - Rotate keys regularly

2. **Rate Limiting**:
   - Monitor rate limit headers
   - Implement client-side rate limiting
   - Handle 429 responses gracefully

3. **Input Validation**:
   - Validate all user inputs
   - Sanitize data before processing
   - Use proper content types

4. **Security Configuration**:
   - Use specific CORS origins in production
   - Set appropriate timeouts
   - Monitor security logs

## Testing Security Features

Run the security test suite:

```bash
# Unit tests
python -m pytest tests/unit/test_security.py -v

# Integration tests  
python -m pytest tests/integration/test_security_integration.py -v

# Manual testing
python test_security_manual.py
```

## Security Compliance

The implemented security features help ensure compliance with:

- **OWASP Top 10**: Protection against common web vulnerabilities
- **Input Validation**: Comprehensive input sanitization and validation
- **Rate Limiting**: DoS protection and abuse prevention
- **Security Headers**: Proper security header implementation
- **Error Handling**: Secure error responses without information leakage

## Future Enhancements

Potential security improvements for future versions:

1. **Authentication**: JWT-based authentication system
2. **Authorization**: Role-based access control
3. **Audit Logging**: Comprehensive security audit trails
4. **Encryption**: End-to-end encryption for sensitive data
5. **Security Scanning**: Automated vulnerability scanning
6. **Intrusion Detection**: Advanced threat detection capabilities