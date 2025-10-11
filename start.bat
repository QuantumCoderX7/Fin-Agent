@echo off
REM Windows batch script to start Financial AI Agents
REM Usage: start.bat [development|production]

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development

set PORT=%2
if "%PORT%"=="" set PORT=8000

echo Starting Financial AI Agents in %ENVIRONMENT% mode on port %PORT%

REM Check if .env file exists
if exist .env (
    echo Loading environment from .env
) else (
    if exist .env.example (
        echo Copying .env.example to .env
        copy .env.example .env
        echo Please edit .env file with your API keys before continuing
        pause
    ) else (
        echo No environment file found. Please create .env file with your API keys.
        pause
        exit /b 1
    )
)

REM Install dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start the application
echo Starting uvicorn server...
if "%ENVIRONMENT%"=="development" (
    uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload --log-level debug
) else (
    uvicorn app.main:app --host 0.0.0.0 --port %PORT% --workers 4
)