"""
Stock Service for orchestrating stock market analysis operations.

This service provides business logic layer for the Stock Market Analyst Agent,
handling request orchestration, error management, and response formatting.
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, List, Optional
from datetime import datetime

from app.agents.stock_agent import StockAgent
from app.models.requests import StockAnalysisRequest
from app.models.responses import StockAnalysisResponse, ResponseStatus, ErrorResponse
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)

logger = logging.getLogger(__name__)


class StockService:
    """
    Service layer for Stock Market Analyst Agent operations.
    
    This service orchestrates stock analysis operations, provides error handling,
    retry logic, and ensures consistent response formatting.
    """
    
    def __init__(
        self, 
        groq_api_key: str,
        model_name: str = "qwen/qwen3-32b",
        timeout_seconds: int = 300,
        max_retries: int = 3,
        **kwargs
    ):
        """
        Initialize the Stock Service.
        
        Args:
            groq_api_key: API key for Groq LLM service
            model_name: LLM model to use for analysis
            timeout_seconds: Timeout for operations
            max_retries: Maximum number of retries for failed operations
            **kwargs: Additional configuration parameters
        """
        self.agent = StockAgent(groq_api_key, model_name, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.service_name = "StockService"
        
        logger.info(f"Initialized {self.service_name} with model {model_name}")
    
    async def execute_stock_analysis(
        self, 
        request: StockAnalysisRequest
    ) -> StockAnalysisResponse:
        """
        Execute stock market analysis with error handling and retries.
        
        Args:
            request: Stock analysis request
            
        Returns:
            StockAnalysisResponse with analysis results
            
        Raises:
            ValidationException: If request validation fails
            TimeoutException: If operation times out
            AgentProcessingException: If analysis fails after retries
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting stock analysis for symbols: {request.symbols}")
            
            # Execute analysis with timeout and retries
            result = await self._execute_with_retry(
                self.agent.process_request,
                request.dict(),
                operation_name="stock_analysis"
            )
            
            # Convert to response model
            response = StockAnalysisResponse(**result)
            response.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Stock analysis completed successfully in {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Stock analysis failed after {processing_time:.2f}s: {str(e)}")
            
            # Re-raise known exceptions
            if isinstance(e, (ValidationException, TimeoutException, AgentProcessingException)):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="StockAgent",
                message=f"Unexpected error during stock analysis: {str(e)}",
                processing_stage="service_orchestration"
            )    

    async def stream_stock_analysis(
        self, 
        request: StockAnalysisRequest
    ) -> AsyncGenerator[str, None]:
        """
        Stream stock market analysis with enhanced progress tracking and multi-symbol support.
        
        This method provides real-time streaming of stock analysis with detailed progress
        updates for each symbol, data fetching notifications, and analysis progress.
        
        Args:
            request: Stock analysis request
            
        Yields:
            String chunks of the streaming response with progress indicators
            
        Raises:
            ValidationException: If request validation fails
            AgentProcessingException: If streaming fails
        """
        try:
            symbols = request.symbols
            logger.info(f"Starting streaming stock analysis for symbols: {symbols}")
            
            # Yield initial status
            yield f"📈 Starting stock analysis for: {', '.join(symbols)}"
            yield f"⚙️ Analysis type: {request.analysis_type}, Comparison: {request.include_comparison}"
            
            # Calculate total steps based on symbols and analysis type
            steps_per_symbol = 3  # fetch, analyze, format
            total_steps = len(symbols) * steps_per_symbol
            if request.include_comparison and len(symbols) > 1:
                total_steps += 2  # comparison analysis + summary
            
            current_step = 0
            
            # Process each symbol with detailed progress
            for i, symbol in enumerate(symbols, 1):
                # Data fetching step
                current_step += 1
                yield f"[{current_step}/{total_steps}] 📊 Fetching data for {symbol}..."
                
                # Analysis step
                current_step += 1
                yield f"[{current_step}/{total_steps}] 🧮 Analyzing {symbol} fundamentals..."
                
                # Formatting step
                current_step += 1
                yield f"[{current_step}/{total_steps}] 📝 Generating {symbol} report..."
            
            # Stream the actual analysis with enhanced progress tracking
            chunk_count = 0
            symbols_processed = 0
            
            async for chunk in self.agent.stream_response(request.dict()):
                chunk_count += 1
                
                # Add contextual information based on chunk content
                if "fetching data" in chunk.lower():
                    yield f"🔄 {chunk}"
                elif "analyzing" in chunk.lower():
                    yield f"🔍 {chunk}"
                elif "completed analysis" in chunk.lower():
                    symbols_processed += 1
                    yield f"✅ {chunk} ({symbols_processed}/{len(symbols)} symbols completed)"
                elif "comparison" in chunk.lower() and len(symbols) > 1:
                    yield f"⚖️ {chunk}"
                elif "recommendation" in chunk.lower():
                    yield f"💡 {chunk}"
                elif "risk" in chunk.lower():
                    yield f"⚠️ {chunk}"
                elif "market sentiment" in chunk.lower():
                    yield f"📊 {chunk}"
                else:
                    yield chunk
                
                # Periodic progress updates for long streams
                if chunk_count % 15 == 0:
                    yield f"📈 Processing... ({chunk_count} updates, {symbols_processed}/{len(symbols)} symbols)"
            
            # Handle comparison analysis if requested
            if request.include_comparison and len(symbols) > 1:
                current_step += 1
                yield f"[{current_step}/{total_steps}] ⚖️ Performing comparative analysis..."
                current_step += 1
                yield f"[{current_step}/{total_steps}] 📊 Generating comparison summary..."
            
            # Final completion
            yield f"✅ Stock analysis completed successfully!"
            yield f"📊 Analyzed {len(symbols)} symbols with {chunk_count} updates"
            
            logger.info(f"Streaming stock analysis completed successfully with {chunk_count} chunks for {len(symbols)} symbols")
            
        except ValidationException as e:
            logger.warning(f"Validation error in streaming stock analysis: {str(e)}")
            yield f"❌ Validation Error: {str(e)}"
            raise e
            
        except DataSourceException as e:
            logger.error(f"Data source error in streaming stock analysis: {str(e)}")
            yield f"📡 Data Source Error: {str(e)}"
            raise e
            
        except TimeoutException as e:
            logger.error(f"Timeout in streaming stock analysis: {str(e)}")
            yield f"⏰ Timeout Error: Stock analysis timed out after {e.timeout_seconds} seconds"
            raise e
            
        except Exception as e:
            logger.error(f"Streaming stock analysis failed: {str(e)}")
            yield f"💥 Unexpected Error: {str(e)}"
            
            # Re-raise known exceptions
            if isinstance(e, AgentProcessingException):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="StockAgent",
                message=f"Streaming stock analysis failed: {str(e)}",
                processing_stage="streaming_service"
            )
            # Send error message to stream
            yield f"❌ **Analysis Failed:** {str(e)}\n"
            
            # Re-raise for upstream handling
            if isinstance(e, (ValidationException, AgentProcessingException)):
                raise e
            
            raise AgentProcessingException(
                agent_name="StockAgent",
                message=f"Streaming analysis failed: {str(e)}",
                processing_stage="streaming_service"
            )
    
    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get basic stock information for a single symbol.
        
        Args:
            symbol: Stock symbol to get information for
            
        Returns:
            Dictionary containing basic stock information
            
        Raises:
            ValidationException: If symbol is invalid
            DataSourceException: If data retrieval fails
        """
        try:
            logger.info(f"Getting stock info for symbol: {symbol}")
            
            # Validate symbol format
            if not symbol or not symbol.strip():
                raise ValidationException(
                    field_name="symbol",
                    message="Stock symbol cannot be empty"
                )
            
            symbol = symbol.strip().upper()
            
            # Get stock data with retry logic
            stock_data = await self._execute_with_retry(
                self.agent.get_stock_data,
                symbol,
                operation_name=f"get_stock_info_{symbol}"
            )
            
            # Format basic info response
            info = {
                "symbol": symbol,
                "company_name": stock_data.get("company_name", symbol),
                "current_price": stock_data.get("current_price"),
                "market_cap": stock_data.get("market_cap"),
                "sector": stock_data.get("sector"),
                "industry": stock_data.get("industry"),
                "day_change": stock_data.get("day_change"),
                "volume": stock_data.get("volume"),
                "pe_ratio": stock_data.get("pe_ratio"),
                "dividend_yield": stock_data.get("dividend_yield"),
                "year_high": stock_data.get("year_high"),
                "year_low": stock_data.get("year_low"),
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Stock info retrieved successfully for {symbol}")
            return info
            
        except Exception as e:
            logger.error(f"Failed to get stock info for {symbol}: {str(e)}")
            
            if isinstance(e, (ValidationException, DataSourceException)):
                raise e
            
            raise DataSourceException(
                source_name="Yahoo Finance",
                message=f"Failed to retrieve stock info for {symbol}: {str(e)}"
            )
    
    async def compare_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Compare multiple stocks and provide comparative analysis.
        
        Args:
            symbols: List of stock symbols to compare
            
        Returns:
            Dictionary containing comparative analysis
            
        Raises:
            ValidationException: If symbols are invalid
            AgentProcessingException: If comparison fails
        """
        try:
            logger.info(f"Starting stock comparison for symbols: {symbols}")
            
            if len(symbols) < 2:
                raise ValidationException(
                    field_name="symbols",
                    message="At least 2 symbols are required for comparison"
                )
            
            # Create comparison request
            request = StockAnalysisRequest(
                symbols=symbols,
                include_comparison=True,
                analysis_type="comprehensive"
            )
            
            # Execute comparison analysis
            result = await self.execute_stock_analysis(request)
            
            # Extract comparison-specific data
            comparison_data = {
                "symbols": result.symbols,
                "comparison_summary": result.comparison_summary,
                "individual_analyses": [
                    {
                        "symbol": analysis.symbol,
                        "recommendation": analysis.recommendation,
                        "risk_level": analysis.risk_level,
                        "current_price": analysis.metrics.current_price,
                        "market_cap": analysis.metrics.market_cap,
                        "pe_ratio": analysis.metrics.pe_ratio
                    }
                    for analysis in result.analyses
                ],
                "market_sentiment": result.market_sentiment,
                "generated_at": result.generated_at.isoformat()
            }
            
            logger.info(f"Stock comparison completed successfully for {len(symbols)} symbols")
            return comparison_data
            
        except Exception as e:
            logger.error(f"Stock comparison failed: {str(e)}")
            
            if isinstance(e, (ValidationException, AgentProcessingException)):
                raise e
            
            raise AgentProcessingException(
                agent_name="StockAgent",
                message=f"Stock comparison failed: {str(e)}",
                processing_stage="comparison_service"
            )
    
    async def get_market_overview(self, sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market overview and sector analysis.
        
        Args:
            sector: Optional sector to focus on
            
        Returns:
            Dictionary containing market overview
        """
        try:
            logger.info(f"Getting market overview for sector: {sector or 'all'}")
            
            # Define major market indices and sector representatives
            market_symbols = ["SPY", "QQQ", "DIA", "IWM"]  # Major ETFs
            
            if sector:
                # Add sector-specific symbols
                sector_symbols = {
                    "technology": ["AAPL", "MSFT", "GOOGL", "NVDA"],
                    "finance": ["JPM", "BAC", "WFC", "GS"],
                    "healthcare": ["JNJ", "PFE", "UNH", "ABBV"],
                    "energy": ["XOM", "CVX", "COP", "EOG"],
                    "consumer": ["AMZN", "TSLA", "HD", "MCD"]
                }
                market_symbols.extend(sector_symbols.get(sector.lower(), []))
            
            # Get basic info for market symbols
            market_data = []
            for symbol in market_symbols[:8]:  # Limit to 8 symbols
                try:
                    info = await self.get_stock_info(symbol)
                    market_data.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {str(e)}")
                    continue
            
            # Generate market overview
            overview = {
                "sector": sector or "general_market",
                "symbols_analyzed": len(market_data),
                "market_data": market_data,
                "summary": f"Market overview for {len(market_data)} symbols",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Market overview completed for {len(market_data)} symbols")
            return overview
            
        except Exception as e:
            logger.error(f"Market overview failed: {str(e)}")
            return {
                "sector": sector or "general_market",
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _execute_with_retry(
        self,
        operation,
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> Any:
        """
        Execute an operation with retry logic and timeout.
        
        Args:
            operation: Async operation to execute
            *args: Operation arguments
            operation_name: Name for logging
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            TimeoutException: If operation times out
            RateLimitException: If rate limited
            AgentProcessingException: If operation fails after retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    operation(*args, **kwargs),
                    timeout=self.timeout_seconds
                )
                
                if attempt > 0:
                    logger.info(f"{operation_name} succeeded on attempt {attempt + 1}")
                
                return result
                
            except asyncio.TimeoutError:
                raise TimeoutException(
                    operation_name=operation_name,
                    timeout_seconds=self.timeout_seconds
                )
                
            except RateLimitException as e:
                logger.warning(f"{operation_name} rate limited on attempt {attempt + 1}")
                if attempt < self.max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = min(2 ** attempt, 60)  # Cap at 60 seconds
                    await asyncio.sleep(wait_time)
                last_exception = e
                
            except (DataSourceException, AgentProcessingException) as e:
                logger.warning(f"{operation_name} failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                    await asyncio.sleep(wait_time)
                last_exception = e
                
            except ValidationException as e:
                # Don't retry validation errors
                raise e
                
            except Exception as e:
                logger.error(f"{operation_name} failed with unexpected error: {str(e)}")
                last_exception = e
                break  # Don't retry unexpected errors
        
        # All retries exhausted
        if last_exception:
            if isinstance(last_exception, (RateLimitException, DataSourceException)):
                raise last_exception
            
            raise AgentProcessingException(
                agent_name="StockAgent",
                message=f"{operation_name} failed after {self.max_retries + 1} attempts: {str(last_exception)}",
                processing_stage="retry_logic"
            )
        
        raise AgentProcessingException(
            agent_name="StockAgent",
            message=f"{operation_name} failed after {self.max_retries + 1} attempts",
            processing_stage="retry_logic"
        )
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this service.
        
        Returns:
            Dictionary containing service metadata
        """
        return {
            "service_name": self.service_name,
            "agent_type": "stock_analysis",
            "version": "1.0.0",
            "description": "Service for orchestrating stock market analysis operations",
            "capabilities": [
                "Individual stock analysis",
                "Multi-stock comparison",
                "Real-time streaming responses",
                "Basic stock information retrieval",
                "Market overview generation",
                "Error handling and retries",
                "Timeout management"
            ],
            "configuration": {
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "model_name": self.agent.model_name
            },
            "agent_info": self.agent.get_agent_info()
        }