"""
Stock analysis API endpoints.

This module implements the REST API endpoints for the Stock Market Analyst Agent,
providing comprehensive stock analysis, comparison, and streaming capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from app.config.settings import Settings
from app.api.deps import validate_api_keys, get_stock_service
from app.services.stock_service import StockService
from app.models.requests import StockAnalysisRequest
from app.models.responses import (
    StockAnalysisResponse, 
    ErrorResponse, 
    AgentInfoResponse,
    HealthResponse
)
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/", response_model=HealthResponse)
async def stock_status(
    settings: Settings = Depends(validate_api_keys),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get stock agent status and available endpoints.
    
    Returns basic health information and available endpoints for the stock analysis service.
    """
    try:
        service_info = stock_service.get_service_info()
        
        return HealthResponse(
            status="ready",
            service="Stock Market Analyst",
            version=service_info.get("version", "1.0.0"),
            dependencies={
                "groq_api": "available" if settings.groq_api_key else "missing",
                "yahoo_finance": "available",
                "stock_service": "initialized"
            }
        )
    except Exception as e:
        logger.error(f"Stock status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Stock service unavailable: {str(e)}"
        )


@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stocks(
    request: StockAnalysisRequest,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Analyze individual stocks or perform multi-stock analysis.
    
    This endpoint provides comprehensive stock analysis including:
    - Financial metrics and ratios
    - Investment recommendations
    - Risk assessment
    - Comparative analysis (when multiple stocks provided)
    - Market sentiment analysis
    
    **Requirements covered:** 2.1, 2.2, 2.3, 2.4
    """
    try:
        logger.info(f"Stock analysis request for symbols: {request.symbols}")
        
        # Execute stock analysis
        result = await stock_service.execute_stock_analysis(request)
        
        logger.info(f"Stock analysis completed successfully for {len(result.symbols)} symbols")
        return result
        
    except ValidationException as e:
        logger.warning(f"Stock analysis validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except DataSourceException as e:
        logger.error(f"Stock analysis data source error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data source error: {str(e)}"
        )
    except TimeoutException as e:
        logger.error(f"Stock analysis timeout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Analysis timeout: {str(e)}"
        )
    except RateLimitException as e:
        logger.warning(f"Stock analysis rate limited: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {str(e)}"
        )
    except AgentProcessingException as e:
        logger.error(f"Stock analysis processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in stock analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during stock analysis"
        )


@router.post("/compare")
async def compare_stocks(
    request: StockAnalysisRequest,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Compare multiple stocks and provide comparative analysis.
    
    This endpoint performs side-by-side comparison of multiple stocks including:
    - Relative valuation metrics
    - Risk-adjusted performance comparison
    - Sector positioning analysis
    - Investment recommendations for each stock
    - Portfolio allocation suggestions
    
    **Requirements covered:** 2.2, 2.3, 2.4
    """
    try:
        logger.info(f"Stock comparison request for symbols: {request.symbols}")
        
        # Validate that we have multiple stocks for comparison
        if len(request.symbols) < 2:
            raise ValidationException(
                field_name="symbols",
                message="At least 2 stocks are required for comparison"
            )
        
        # Execute stock comparison
        result = await stock_service.compare_stocks(request.symbols)
        
        logger.info(f"Stock comparison completed successfully for {len(request.symbols)} symbols")
        return result
        
    except ValidationException as e:
        logger.warning(f"Stock comparison validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except DataSourceException as e:
        logger.error(f"Stock comparison data source error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data source error: {str(e)}"
        )
    except AgentProcessingException as e:
        logger.error(f"Stock comparison processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in stock comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during stock comparison"
        )


@router.get("/{symbol}/info")
async def get_stock_info(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, GOOGL)", min_length=1, max_length=10),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get basic stock information for a single symbol.
    
    This endpoint provides essential stock information including:
    - Current price and market capitalization
    - Key financial ratios (P/E, dividend yield)
    - Trading volume and price ranges
    - Company sector and industry
    - Basic company information
    
    **Requirements covered:** 2.1, 2.2
    """
    try:
        logger.info(f"Stock info request for symbol: {symbol}")
        
        # Clean and validate symbol
        symbol = symbol.strip().upper()
        if not symbol.replace('.', '').replace('-', '').isalnum():
            raise ValidationException(
                field_name="symbol",
                message=f"Invalid stock symbol format: {symbol}"
            )
        
        # Get stock information
        result = await stock_service.get_stock_info(symbol)
        
        logger.info(f"Stock info retrieved successfully for {symbol}")
        return result
        
    except ValidationException as e:
        logger.warning(f"Stock info validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except DataSourceException as e:
        logger.error(f"Stock info data source error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock data not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting stock info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving stock information"
        )


@router.post("/stream")
async def stream_stock_analysis(
    request: StockAnalysisRequest,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Stream stock analysis in real-time.
    
    This endpoint provides real-time streaming of stock analysis results,
    allowing clients to receive progressive updates as the analysis is performed.
    
    The response is streamed as Server-Sent Events (SSE) with:
    - Progress indicators during data fetching
    - Real-time analysis results as they're generated
    - Tool usage transparency
    - Final analysis summary
    
    **Requirements covered:** 2.1, 2.2, 2.3, 2.4, 6.1, 6.4
    """
    from app.api.streaming import create_streaming_response, ProgressTracker
    
    try:
        logger.info(f"Streaming stock analysis request for symbols: {request.symbols}")
        
        async def generate_stream():
            """Generate streaming response with enhanced progress tracking."""
            try:
                # Initialize progress tracker based on number of symbols
                total_steps = len(request.symbols) * 3 + 2  # Data fetch, analysis, formatting per symbol + init + final
                progress = ProgressTracker(
                    total_steps=total_steps,
                    operation_name=f"Stock Analysis: {', '.join(request.symbols)}"
                )
                
                # Send initial progress
                yield {"progress": progress.update("Initializing stock analysis...")}
                
                # Track symbol processing
                symbols_processed = 0
                
                async for chunk in stock_service.stream_stock_analysis(request):
                    # Update progress based on content
                    if "fetching data" in chunk.lower():
                        yield {"progress": progress.update(f"Fetching data for symbol {symbols_processed + 1}...")}
                    elif "analyzing" in chunk.lower():
                        yield {"progress": progress.update(f"Analyzing symbol {symbols_processed + 1}...")}
                    elif "completed analysis" in chunk.lower():
                        symbols_processed += 1
                        yield {"progress": progress.update(f"Completed analysis for symbol {symbols_processed}")}
                    elif "generating report" in chunk.lower():
                        yield {"progress": progress.update("Generating final report...")}
                    
                    # Send content chunk
                    yield {"content": chunk}
                
                # Send completion
                yield {"progress": progress.complete()}
                
            except ValidationException as e:
                yield {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
            except DataSourceException as e:
                yield {"error": {"code": "DATA_SOURCE_ERROR", "message": str(e)}}
            except AgentProcessingException as e:
                yield {"error": {"code": "AGENT_PROCESSING_ERROR", "message": str(e)}}
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}")
                yield {"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)}}
        
        return create_streaming_response(generate_stream())
        
    except ValidationException as e:
        logger.warning(f"Streaming validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in streaming: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while setting up streaming"
        )


@router.get("/info", response_model=AgentInfoResponse)
async def get_agent_info(
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get detailed information about the Stock Market Analyst Agent.
    
    Returns comprehensive information about the agent's capabilities,
    supported models, tools, and configuration.
    """
    try:
        service_info = stock_service.get_service_info()
        agent_info = service_info.get("agent_info", {})
        
        return AgentInfoResponse(
            agent_name=agent_info.get("agent_name", "Stock Market Analyst"),
            agent_type=agent_info.get("agent_type", "stock_analysis"),
            capabilities=agent_info.get("capabilities", []),
            supported_models=agent_info.get("supported_models", []),
            version=agent_info.get("version", "1.0.0"),
            description=agent_info.get("description", "Stock market analysis agent"),
            tools=agent_info.get("tools", []),
            configuration=service_info.get("configuration", {})
        )
        
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent information"
        )


@router.get("/market/overview")
async def get_market_overview(
    sector: str = None,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    Get market overview and sector analysis.
    
    This endpoint provides a broad market overview including:
    - Major market indices performance
    - Sector-specific analysis (if sector specified)
    - Market sentiment indicators
    - Key market movers
    
    **Parameters:**
    - sector: Optional sector to focus on (e.g., 'technology', 'finance', 'healthcare')
    """
    try:
        logger.info(f"Market overview request for sector: {sector or 'general'}")
        
        # Get market overview
        result = await stock_service.get_market_overview(sector)
        
        logger.info(f"Market overview completed for sector: {sector or 'general'}")
        return result
        
    except Exception as e:
        logger.error(f"Market overview error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market overview: {str(e)}"
        )