#!/bin/bash

# Setup Monitoring Stack for Financial AI Agents
# Usage: ./scripts/setup-monitoring.sh [environment]

set -e

ENVIRONMENT=${1:-development}
NAMESPACE="monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    error "kubectl is not installed or not in PATH"
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    warn "helm is not installed. Some features may not be available."
fi

log "Setting up monitoring stack for environment: $ENVIRONMENT"

# Create monitoring namespace
log "Creating monitoring namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Install Prometheus Operator (if using Helm)
if command -v helm &> /dev/null; then
    log "Installing Prometheus Operator with Helm..."
    
    # Add Prometheus community Helm repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    # Install kube-prometheus-stack
    helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
        --namespace $NAMESPACE \
        --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
        --set prometheus.prometheusSpec.ruleSelectorNilUsesHelmValues=false \
        --wait
    
    log "Prometheus Operator installed successfully"
else
    warn "Helm not available. Please install Prometheus manually or install Helm."
fi

# Apply Prometheus configuration
log "Applying Prometheus configuration..."
kubectl apply -f monitoring/prometheus-config.yaml -n $NAMESPACE

# Apply ServiceMonitor for Financial AI Agents
log "Creating ServiceMonitor for Financial AI Agents..."
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: financial-ai-agents
  namespace: financial-ai-agents
  labels:
    app: financial-ai-agents
spec:
  selector:
    matchLabels:
      app: financial-ai-agents
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
EOF

# Create Grafana dashboard ConfigMap
log "Creating Grafana dashboard..."
kubectl create configmap financial-ai-agents-dashboard \
    --from-file=monitoring/grafana-dashboard.json \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Label the ConfigMap for Grafana to pick it up
kubectl label configmap financial-ai-agents-dashboard \
    grafana_dashboard=1 \
    --namespace=$NAMESPACE \
    --overwrite

# Wait for Prometheus to be ready
log "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n $NAMESPACE --timeout=300s

# Wait for Grafana to be ready
log "Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n $NAMESPACE --timeout=300s

# Get access information
log "Getting access information..."

# Prometheus
PROMETHEUS_PORT=$(kubectl get svc -n $NAMESPACE -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].spec.ports[0].port}')
echo ""
log "Prometheus is available at:"
echo "  Port-forward: kubectl port-forward -n $NAMESPACE svc/monitoring-kube-prometheus-prometheus 9090:$PROMETHEUS_PORT"
echo "  Then access: http://localhost:9090"

# Grafana
GRAFANA_PORT=$(kubectl get svc -n $NAMESPACE -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].spec.ports[0].port}')
GRAFANA_PASSWORD=$(kubectl get secret -n $NAMESPACE monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d)

echo ""
log "Grafana is available at:"
echo "  Port-forward: kubectl port-forward -n $NAMESPACE svc/monitoring-grafana $GRAFANA_PORT:$GRAFANA_PORT"
echo "  Then access: http://localhost:$GRAFANA_PORT"
echo "  Username: admin"
echo "  Password: $GRAFANA_PASSWORD"

# AlertManager
ALERTMANAGER_PORT=$(kubectl get svc -n $NAMESPACE -l app.kubernetes.io/name=alertmanager -o jsonpath='{.items[0].spec.ports[0].port}')
echo ""
log "AlertManager is available at:"
echo "  Port-forward: kubectl port-forward -n $NAMESPACE svc/monitoring-kube-prometheus-alertmanager $ALERTMANAGER_PORT:$ALERTMANAGER_PORT"
echo "  Then access: http://localhost:$ALERTMANAGER_PORT"

# Create port-forward script
log "Creating port-forward script..."
cat > scripts/port-forward-monitoring.sh << 'EOF'
#!/bin/bash

# Port-forward monitoring services
# Usage: ./scripts/port-forward-monitoring.sh

NAMESPACE="monitoring"

echo "Starting port-forwards for monitoring services..."

# Start port-forwards in background
kubectl port-forward -n $NAMESPACE svc/monitoring-kube-prometheus-prometheus 9090:9090 &
PROMETHEUS_PID=$!

kubectl port-forward -n $NAMESPACE svc/monitoring-grafana 3000:80 &
GRAFANA_PID=$!

kubectl port-forward -n $NAMESPACE svc/monitoring-kube-prometheus-alertmanager 9093:9093 &
ALERTMANAGER_PID=$!

echo "Port-forwards started:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana: http://localhost:3000"
echo "  AlertManager: http://localhost:9093"
echo ""
echo "Press Ctrl+C to stop all port-forwards"

# Function to cleanup on exit
cleanup() {
    echo "Stopping port-forwards..."
    kill $PROMETHEUS_PID $GRAFANA_PID $ALERTMANAGER_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait
EOF

chmod +x scripts/port-forward-monitoring.sh

# Test connectivity to Financial AI Agents
log "Testing connectivity to Financial AI Agents..."
if kubectl get pods -n financial-ai-agents -l app=financial-ai-agents | grep -q Running; then
    log "✓ Financial AI Agents pods are running"
else
    warn "Financial AI Agents pods are not running. Deploy the application first."
fi

# Verify ServiceMonitor is created
if kubectl get servicemonitor -n financial-ai-agents financial-ai-agents &>/dev/null; then
    log "✓ ServiceMonitor created successfully"
else
    warn "ServiceMonitor creation failed. Check the logs above."
fi

log "Monitoring stack setup completed!"
log ""
log "Next steps:"
log "1. Run './scripts/port-forward-monitoring.sh' to access monitoring services"
log "2. Import the Financial AI Agents dashboard in Grafana"
log "3. Configure alerting rules as needed"
log "4. Set up notification channels in AlertManager"

echo ""
log "Monitoring setup complete for environment: $ENVIRONMENT"