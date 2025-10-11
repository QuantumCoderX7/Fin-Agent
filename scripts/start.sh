#!/bin/bash

# Start script for Financial AI Agents
# Usage: ./scripts/start.sh [environment]

set -e

ENVIRONMENT=${1:-development}
PORT=${2:-8000}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log "Starting Financial AI Agents in $ENVIRONMENT mode on port $PORT"

# Load environment configuration
ENV_FILE="config/${ENVIRONMENT}.env"
if [[ -f "$ENV_FILE" ]]; then
    log "Loading environment from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
elif [[ -f ".env" ]]; then
    log "Loading environment from .env"
    set -a
    source ".env"
    set +a
else
    warn "No environment file found. Using default settings."
fi

# Check Python virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    log "Using virtual environment: $VIRTUAL_ENV"
else
    warn "No virtual environment detected. Consider using a virtual environment."
fi

# Install dependencies if needed
if [[ ! -f "requirements.txt" ]] || [[ "requirements.txt" -nt ".requirements_installed" ]]; then
    log "Installing/updating dependencies..."
    pip install -r requirements.txt
    touch .requirements_installed
fi

# Start the application
log "Starting uvicorn server..."
if [[ "$ENVIRONMENT" == "development" ]]; then
    uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload --log-level debug
else
    uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 4
fi