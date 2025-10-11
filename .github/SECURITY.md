# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Financial AI Agents seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please DO NOT:
- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Please DO:
1. **Email**: Send details to your security contact email
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect:
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Status Updates**: Every 7 days until resolved
- **Resolution**: We aim to patch critical vulnerabilities within 30 days

## Security Best Practices

### For Users:

1. **API Keys**:
   - Never commit API keys to git
   - Use environment variables for all secrets
   - Rotate keys regularly
   - Revoke keys immediately if exposed

2. **Environment Files**:
   - Keep `.env` files out of version control
   - Use `.env.example` as a template only
   - Never share `.env` files

3. **Dependencies**:
   - Keep dependencies up to date
   - Run `pip audit` regularly
   - Review security advisories

4. **Deployment**:
   - Use HTTPS in production
   - Enable rate limiting
   - Set `DEBUG=false` in production
   - Restrict CORS origins
   - Use strong authentication

### For Contributors:

1. **Code Review**:
   - All PRs require review
   - Security-sensitive changes need extra scrutiny
   - Run security scans before submitting

2. **Testing**:
   - Write tests for security features
   - Test input validation
   - Test authentication/authorization

3. **Documentation**:
   - Document security considerations
   - Update security guides
   - Keep examples secure

## Known Security Considerations

### API Key Management
- API keys are validated on startup
- Keys must meet minimum length requirements
- Debug mode skips validation (development only)

### Rate Limiting
- Default: 60 requests/minute
- Configurable per environment
- Applies to all API endpoints

### Input Validation
- All inputs are validated using Pydantic
- SQL injection protection
- XSS prevention
- CSRF protection

### CORS Configuration
- Wildcard (`*`) allowed in development only
- Production requires specific origins
- Credentials support configurable

## Security Updates

We will notify users of security updates through:
- GitHub Security Advisories
- Release notes
- README updates

## Compliance

This project follows:
- OWASP Top 10 guidelines
- Secure coding best practices
- Principle of least privilege
- Defense in depth

## Security Checklist for Deployments

- [ ] All API keys are set via environment variables
- [ ] `.env` file is not in version control
- [ ] `DEBUG=false` in production
- [ ] CORS origins are restricted
- [ ] HTTPS is enabled
- [ ] Rate limiting is configured
- [ ] Monitoring is set up
- [ ] Logs don't contain sensitive data
- [ ] Dependencies are up to date
- [ ] Security headers are configured

## Contact

For security concerns, please contact the repository owner through GitHub.

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities (with their permission).
