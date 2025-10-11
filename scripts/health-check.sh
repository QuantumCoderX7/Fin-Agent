#!/bin/bash

# Health Check Script for Financial AI Agents
# Tests all critical endpoints and functionality

set -e

# Configuration
BASE_URL=${1:-http://localhost:8000}
TIMEOUT=30

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
}

test_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local method=${3:-GET}
    
    log "Testing $method $endpoint"
    
    if [[ "$method" == "GET" ]]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json --max-time $TIMEOUT "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json --max-time $TIMEOUT -X "$method" -H "Content-Type: application/json" "$BASE_URL$endpoint")
    fi
    
    if [[ "$response" == "$expected_status" ]]; then
        log "✓ $endpoint returned $response"
        return 0
    else
        error "✗ $endpoint returned $response, expected $expected_status"
        cat /tmp/response.json 2>/dev/null || true
        return 1
    fi
}

test_json_response() {
    local endpoint=$1
    local required_field=$2
    
    log "Testing JSON response structure for $endpoint"
    
    curl -s --max-time $TIMEOUT "$BASE_URL$endpoint" > /tmp/response.json
    
    if jq -e ".$required_field" /tmp/response.json > /dev/null 2>&1; then
        log "✓ $endpoint has required field: $required_field"
        return 0
    else
        error "✗ $endpoint missing required field: $required_field"
        cat /tmp/response.json
        return 1
    fi
}

log "Starting health checks for Financial AI Agents at $BASE_URL"

# Test basic endpoints
test_endpoint "/" 200
test_endpoint "/health" 200
test_endpoint "/status" 200
test_endpoint "/docs" 200

# Test API documentation
test_endpoint "/openapi.json" 200

# Test API v1 endpoints structure
test_endpoint "/api/v1/research/topics" 200
test_endpoint "/api/v1/stocks/AAPL/info" 200 || warn "Stock info endpoint may require valid symbol"
test_endpoint "/api/v1/evaluation/metrics" 200

# Test JSON response structures
test_json_response "/health" "status"
test_json_response "/status" "service"
test_json_response "/" "service"

# Test that required fields are present in status
log "Validating status endpoint response structure"
status_response=$(curl -s --max-time $TIMEOUT "$BASE_URL/status")

required_status_fields=("status" "service" "version" "api_keys_configured" "available_endpoints")
for field in "${required_status_fields[@]}"; do
    if echo "$status_response" | jq -e ".$field" > /dev/null 2>&1; then
        log "✓ Status has required field: $field"
    else
        error "✗ Status missing required field: $field"
    fi
done

# Test API key configuration (should show boolean status without exposing keys)
log "Checking API key configuration status"
api_keys_status=$(echo "$status_response" | jq -r '.api_keys_configured')
if [[ "$api_keys_status" != "null" ]]; then
    log "✓ API keys configuration status is available"
else
    warn "API keys configuration status not available"
fi

# Test error handling
log "Testing error handling"
test_endpoint "/nonexistent" 404

# Test CORS headers (if applicable)
log "Testing CORS headers"
cors_response=$(curl -s -I --max-time $TIMEOUT -H "Origin: http://localhost:3000" "$BASE_URL/")
if echo "$cors_response" | grep -i "access-control-allow-origin" > /dev/null; then
    log "✓ CORS headers are present"
else
    warn "CORS headers not found (may be intentional)"
fi

# Performance test - basic response time
log "Testing response time"
start_time=$(date +%s%N)
curl -s --max-time $TIMEOUT "$BASE_URL/health" > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 ))

if [[ $response_time -lt 1000 ]]; then
    log "✓ Response time: ${response_time}ms (good)"
elif [[ $response_time -lt 3000 ]]; then
    warn "Response time: ${response_time}ms (acceptable)"
else
    warn "Response time: ${response_time}ms (slow)"
fi

log "All health checks completed successfully!"
log "Application appears to be running correctly at $BASE_URL"