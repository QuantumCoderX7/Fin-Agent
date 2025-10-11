#!/bin/bash

# Financial AI Agents Deployment Script
# Usage: ./scripts/deploy.sh [environment] [version]

set -e

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
APP_NAME="financial-ai-agents"
REGISTRY="your-registry.com"  # Update with your container registry

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    error "Invalid environment: $ENVIRONMENT. Must be development, staging, or production."
fi

log "Starting deployment for environment: $ENVIRONMENT, version: $VERSION"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running. Please start Docker and try again."
fi

# Load environment configuration
ENV_FILE="config/${ENVIRONMENT}.env"
if [[ ! -f "$ENV_FILE" ]]; then
    error "Environment file not found: $ENV_FILE"
fi

log "Loading environment configuration from $ENV_FILE"
set -a
source "$ENV_FILE"
set +a

# Validate required environment variables
required_vars=("GROQ_API_KEY" "PHI_API_KEY")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        error "Required environment variable $var is not set"
    fi
done

# Build Docker image
log "Building Docker image..."
docker build -t "${APP_NAME}:${VERSION}" .

# Tag for registry if not local deployment
if [[ "$ENVIRONMENT" != "development" ]]; then
    docker tag "${APP_NAME}:${VERSION}" "${REGISTRY}/${APP_NAME}:${VERSION}"
    log "Tagged image for registry: ${REGISTRY}/${APP_NAME}:${VERSION}"
fi

# Stop existing containers
log "Stopping existing containers..."
docker-compose -f docker-compose.yml -f "docker-compose.${ENVIRONMENT}.yml" down || true

# Start new deployment
log "Starting new deployment..."
if [[ "$ENVIRONMENT" == "production" ]]; then
    docker-compose -f docker-compose.yml -f docker-compose.production.yml --profile production up -d
else
    docker-compose -f docker-compose.yml -f "docker-compose.${ENVIRONMENT}.yml" up -d
fi

# Wait for health check
log "Waiting for application to be healthy..."
max_attempts=30
attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "Application is healthy!"
        break
    fi
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Application failed to become healthy after $max_attempts attempts"
    fi
    
    warn "Health check failed (attempt $attempt/$max_attempts), retrying in 10 seconds..."
    sleep 10
    ((attempt++))
done

# Run post-deployment tests
log "Running post-deployment tests..."
if [[ -f "scripts/health-check.sh" ]]; then
    ./scripts/health-check.sh
else
    warn "No health check script found, skipping post-deployment tests"
fi

log "Deployment completed successfully!"
log "Application is running at: http://localhost:8000"
log "API documentation: http://localhost:8000/docs"
log "Health status: http://localhost:8000/health"