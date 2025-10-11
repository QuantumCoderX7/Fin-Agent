# PowerShell script to start Financial AI Agents
# Usage: .\start.ps1 [development|production] [port]

param(
    [string]$Environment = "development",
    [int]$Port = 8000
)

Write-Host "Starting Financial AI Agents in $Environment mode on port $Port" -ForegroundColor Green

# Check if .env file exists
if (Test-Path ".env") {
    Write-Host "Loading environment from .env" -ForegroundColor Yellow
} elseif (Test-Path ".env.example") {
    Write-Host "Copying .env.example to .env" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env file with your API keys before continuing" -ForegroundColor Red
    Read-Host "Press Enter after editing .env file"
} else {
    Write-Host "No environment file found. Please create .env file with your API keys." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Start the application
Write-Host "Starting uvicorn server..." -ForegroundColor Green
if ($Environment -eq "development") {
    uvicorn app.main:app --host 0.0.0.0 --port $Port --reload --log-level debug
} else {
    uvicorn app.main:app --host 0.0.0.0 --port $Port --workers 4
}