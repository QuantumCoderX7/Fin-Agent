# Deployment Guide

This guide covers various deployment options for the Financial AI Agents system.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required API Keys

Before deploying, ensure you have the following API keys:

- **Groq API Key**: For LLM operations
- **Phi API Key**: For additional AI services

### System Requirements

- **Minimum**: 2 CPU cores, 4GB RAM, 10GB storage
- **Recommended**: 4 CPU cores, 8GB RAM, 20GB storage
- **Production**: 8+ CPU cores, 16GB+ RAM, 50GB+ storage

## Local Development

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd financial-ai-agents
   cp .env.example .env
   ```

2. **Configure environment**:
   ```bash
   # Edit .env with your API keys
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
   ```

### Using Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Single Container

```bash
# Build the image
docker build -t financial-ai-agents .

# Run with environment variables
docker run -d \
  --name financial-ai-agents \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e PHI_API_KEY=your_key \
  financial-ai-agents
```

### Docker Compose - Development

```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.development.yml up -d

# View logs
docker-compose logs -f financial-ai-agents

# Stop services
docker-compose down
```

### Docker Compose - Production

```bash
# Start production environment with nginx
docker-compose -f docker-compose.yml -f docker-compose.production.yml --profile production up -d

# Check status
docker-compose ps

# Scale the application
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --scale financial-ai-agents=3
```

### Environment-Specific Deployment

```bash
# Development
./scripts/deploy.sh development

# Staging
./scripts/deploy.sh staging

# Production
./scripts/deploy.sh production
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Ingress controller (nginx recommended)
- cert-manager for SSL (optional)

### Basic Deployment

1. **Update configuration**:
   ```bash
   # Edit k8s-deployment.yaml
   # Update image registry, domain, and API keys
   ```

2. **Deploy to cluster**:
   ```bash
   kubectl apply -f k8s-deployment.yaml
   ```

3. **Verify deployment**:
   ```bash
   kubectl get pods -n financial-ai-agents
   kubectl get services -n financial-ai-agents
   kubectl get ingress -n financial-ai-agents
   ```

### Advanced Kubernetes Setup

#### Using Helm (Recommended)

```bash
# Create Helm chart structure
helm create financial-ai-agents-chart

# Install with custom values
helm install financial-ai-agents ./financial-ai-agents-chart \
  --set image.tag=latest \
  --set ingress.host=api.yourdomain.com \
  --set secrets.groqApiKey=your_key \
  --set secrets.phiApiKey=your_key
```

#### Secrets Management

```bash
# Create secrets from command line
kubectl create secret generic api-keys \
  --from-literal=GROQ_API_KEY=your_groq_key \
  --from-literal=PHI_API_KEY=your_phi_key \
  -n financial-ai-agents

# Or use external secrets operator
kubectl apply -f external-secrets-config.yaml
```

#### Monitoring Setup

```bash
# Deploy Prometheus and Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack

# Apply ServiceMonitor for the application
kubectl apply -f monitoring/service-monitor.yaml
```

## Production Considerations

### Security

1. **API Key Management**:
   - Use Kubernetes secrets or external secret management
   - Rotate keys regularly
   - Never commit keys to version control

2. **Network Security**:
   - Use TLS/SSL certificates
   - Configure proper firewall rules
   - Implement rate limiting

3. **Container Security**:
   - Use non-root user in containers
   - Scan images for vulnerabilities
   - Keep base images updated

### Performance

1. **Resource Allocation**:
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "1Gi"
       cpu: "500m"
   ```

2. **Horizontal Scaling**:
   ```yaml
   # HPA configuration
   minReplicas: 2
   maxReplicas: 10
   targetCPUUtilizationPercentage: 70
   ```

3. **Load Balancing**:
   - Use nginx or cloud load balancer
   - Configure health checks
   - Implement circuit breakers

### High Availability

1. **Multi-Zone Deployment**:
   ```yaml
   affinity:
     podAntiAffinity:
       preferredDuringSchedulingIgnoredDuringExecution:
       - weight: 100
         podAffinityTerm:
           labelSelector:
             matchExpressions:
             - key: app
               operator: In
               values:
               - financial-ai-agents
           topologyKey: kubernetes.io/zone
   ```

2. **Database Considerations**:
   - Use managed database services
   - Implement backup strategies
   - Configure read replicas

## Monitoring and Logging

### Health Checks

The application provides several health check endpoints:

- `GET /health` - Basic health status
- `GET /status` - Detailed system information
- `GET /streaming/stats` - Streaming connection statistics

### Logging Configuration

```yaml
# Production logging
LOG_LEVEL: INFO
LOG_FORMAT: json
LOG_FILE: /app/logs/financial-ai-agents.log

# Development logging
LOG_LEVEL: DEBUG
LOG_FORMAT: structured
```

### Metrics Collection

```python
# Custom metrics endpoint
@app.get("/metrics")
async def metrics():
    return {
        "requests_total": request_counter,
        "active_streams": len(active_streams),
        "response_time_avg": avg_response_time,
        "error_rate": error_rate
    }
```

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
- name: financial-ai-agents
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    annotations:
      summary: High error rate detected
      
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    annotations:
      summary: High memory usage
```

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   ```bash
   # Check if keys are properly set
   kubectl get secret api-keys -o yaml
   
   # Verify application can access keys
   kubectl logs -n financial-ai-agents deployment/financial-ai-agents
   ```

2. **Connection Issues**:
   ```bash
   # Test internal connectivity
   kubectl exec -it pod-name -- curl http://localhost:8000/health
   
   # Check service endpoints
   kubectl get endpoints -n financial-ai-agents
   ```

3. **Performance Issues**:
   ```bash
   # Check resource usage
   kubectl top pods -n financial-ai-agents
   
   # Review application logs
   kubectl logs -n financial-ai-agents -l app=financial-ai-agents --tail=100
   ```

### Debug Commands

```bash
# Get pod status
kubectl describe pod <pod-name> -n financial-ai-agents

# Check events
kubectl get events -n financial-ai-agents --sort-by='.lastTimestamp'

# Port forward for local testing
kubectl port-forward service/financial-ai-agents-service 8000:80 -n financial-ai-agents

# Execute commands in pod
kubectl exec -it <pod-name> -n financial-ai-agents -- /bin/bash
```

### Log Analysis

```bash
# Follow logs in real-time
kubectl logs -f deployment/financial-ai-agents -n financial-ai-agents

# Search for specific errors
kubectl logs deployment/financial-ai-agents -n financial-ai-agents | grep ERROR

# Export logs for analysis
kubectl logs deployment/financial-ai-agents -n financial-ai-agents > app-logs.txt
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup Kubernetes resources
kubectl get all -n financial-ai-agents -o yaml > backup-resources.yaml

# Backup secrets (be careful with this)
kubectl get secrets -n financial-ai-agents -o yaml > backup-secrets.yaml
```

### Disaster Recovery

1. **Application Recovery**:
   ```bash
   # Restore from backup
   kubectl apply -f backup-resources.yaml
   
   # Verify deployment
   ./scripts/health-check.sh
   ```

2. **Data Recovery**:
   - Restore from database backups
   - Verify data integrity
   - Test application functionality

## Performance Tuning

### Application Level

```python
# Optimize uvicorn settings
uvicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 1000 \
  --max-requests-jitter 100
```

### Infrastructure Level

```yaml
# Kubernetes resource optimization
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Monitoring Performance

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Load testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/research/topics
```

This deployment guide provides comprehensive instructions for deploying the Financial AI Agents system in various environments, from local development to production Kubernetes clusters.