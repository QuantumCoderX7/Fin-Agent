"""
FastAPI application entry point for Financial AI Agents system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import get_settings
from app.config.security import get_security_config_for_environment
from app.config.logging import setup_logging
from app.api.v1 import research, stock, evaluation
from app.api.middleware import ErrorHandlingMiddleware, RateLimitMiddleware, SecurityMiddleware
from app.api.streaming import StreamingMiddleware
from app.api.exception_handlers import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    
    # Validate all security settings on startup
    settings.validate_security_settings()
    
    # Start streaming health checker
    from app.api.streaming import stream_health_checker
    await stream_health_checker.start_health_checks()
    
    yield
    
    # Shutdown
    # Stop streaming health checker
    await stream_health_checker.stop_health_checks()
    
    # Clean up any remaining streams
    from app.api.streaming import cleanup_inactive_streams
    cleanup_stats = await cleanup_inactive_streams(0)  # Clean all streams
    if cleanup_stats["cleaned_streams"] > 0:
        print(f"Cleaned up {cleanup_stats['cleaned_streams']} streams during shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Create a minimal FastAPI app for debugging
    app = FastAPI(
        title=settings.app_name,
        description="Financial AI Agents API",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan
    )
    
    # Temporarily comment out middleware for debugging
    # Configure CORS (keep this one as it's standard)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(research.router, prefix=settings.api_v1_prefix)
    app.include_router(stock.router, prefix=settings.api_v1_prefix)
    app.include_router(evaluation.router, prefix=settings.api_v1_prefix)
    
    # Root endpoint
    @app.get("/", tags=["system"], summary="API Information", 
             description="Get basic information about the Financial AI Agents API")
    async def root():
        """Root endpoint with API information."""
        settings = get_settings()
        return {
            "service": settings.app_name,
            "version": "1.0.0",
            "description": "Professional-grade financial analysis through specialized AI agents",
            "docs_url": "/docs",
            "health_check": "/health",
            "status": "/status",
            "api_base": settings.api_v1_prefix
        }
    
    # Health check endpoint
    @app.get("/health", tags=["system"], summary="Health Check",
             description="Basic health check endpoint for monitoring service availability")
    async def health_check():
        """Basic health check endpoint."""
        return {"status": "healthy", "service": "financial-ai-agents"}
    
    # Status endpoint with detailed information
    @app.get("/status", tags=["system"], summary="Detailed Status",
             description="Comprehensive status information including configuration and statistics")
    async def status_check():
        """Detailed status endpoint with system information."""
        from app.api.streaming import get_streaming_stats
        
        settings = get_settings()
        
        # Check API key availability (without exposing values)
        api_keys_status = {
            "groq_api_key": bool(settings.groq_api_key),
            "phi_api_key": bool(settings.phi_api_key)
        }
        
        # Get streaming statistics
        streaming_stats = get_streaming_stats()
        
        return {
            "status": "operational",
            "service": settings.app_name,
            "version": "1.0.0",
            "debug_mode": settings.debug,
            "api_keys_configured": api_keys_status,
            "streaming": streaming_stats,
            "available_endpoints": {
                "research": f"{settings.api_v1_prefix}/research",
                "stocks": f"{settings.api_v1_prefix}/stocks", 
                "evaluation": f"{settings.api_v1_prefix}/evaluation"
            },
            "streaming_endpoints": {
                "research_stream": f"{settings.api_v1_prefix}/research/stream",
                "stock_stream": f"{settings.api_v1_prefix}/stocks/stream",
                "evaluation_stream": f"{settings.api_v1_prefix}/evaluation/stream"
            },
            "configuration": {
                "max_sources": settings.max_sources,
                "request_timeout": settings.request_timeout,
                "default_model": settings.default_model
            }
        }
    
    # Streaming management endpoints
    @app.get("/streaming/stats", tags=["system"], summary="Streaming Statistics",
             description="Get detailed statistics about active streaming connections")
    async def get_streaming_statistics():
        """Get detailed streaming connection statistics."""
        from app.api.streaming import get_streaming_stats
        return get_streaming_stats()
    
    @app.post("/streaming/cleanup", tags=["system"], summary="Cleanup Inactive Streams",
              description="Force cleanup of inactive streaming connections")
    async def cleanup_streams(max_inactive_seconds: int = 300):
        """Clean up inactive streaming connections."""
        from app.api.streaming import cleanup_inactive_streams
        return await cleanup_inactive_streams(max_inactive_seconds)
    
    @app.delete("/streaming/{stream_id}", tags=["system"], summary="Force Close Stream",
                description="Force close a specific streaming connection")
    async def force_close_streaming_connection(stream_id: str):
        """Force close a specific streaming connection."""
        from app.api.streaming import force_close_stream
        success = await force_close_stream(stream_id)
        if success:
            return {"message": f"Stream {stream_id} closed successfully", "stream_id": stream_id}
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Stream {stream_id} not found")
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )