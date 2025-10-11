"""
Research Service for orchestrating financial research agent operations.

This service provides business logic layer for the Financial Research Agent,
handling request orchestration, error management, and response formatting.
"""

import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from app.agents.research_agent import ResearchAgent
from app.models.requests import ResearchRequest
from app.models.responses import ResearchResponse, ResponseStatus, ErrorResponse
from app.utils.exceptions import (
    ValidationException,
    DataSourceException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)


class MockResearchAgent:
    """Mock research agent for streaming functionality testing."""
    
    def __init__(self, groq_api_key: str, model_name: str = "qwen/qwen3-32b", **kwargs):
        self.groq_api_key = groq_api_key
        self.model_name = model_name
        self.kwargs = kwargs
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock process request for testing."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "topic": request_data.get('topic', 'Financial Topic'),
            "headline": f"Analysis of {request_data.get('topic', 'Financial Topic')}",
            "executive_summary": "Mock executive summary for streaming test",
            "analysis": "Detailed mock analysis content",
            "future_outlook": "Mock future outlook section",
            "sources": [
                {
                    "url": "https://example.com/source1",
                    "title": "Mock Financial Source 1",
                    "relevance_score": 0.9,
                    "excerpt": "Key financial insights from source 1"
                },
                {
                    "url": "https://example.com/source2", 
                    "title": "Mock Financial Source 2",
                    "relevance_score": 0.8,
                    "excerpt": "Important market data from source 2"
                },
                {
                    "url": "https://example.com/source3",
                    "title": "Mock Financial Source 3", 
                    "relevance_score": 0.7,
                    "excerpt": "Additional analysis from source 3"
                }
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "processing_time": 0.1
        }
    
    async def stream_response(self, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Mock streaming response for testing."""
        topic = request_data.get('topic', 'Financial Topic')
        
        yield f"🔍 Starting research analysis for: {topic}"
        await asyncio.sleep(0.1)
        
        yield f"📊 Searching for sources on {topic}..."
        await asyncio.sleep(0.1)
        
        yield "✅ Found 5 authoritative sources"
        await asyncio.sleep(0.1)
        
        yield "📄 Processing source content..."
        await asyncio.sleep(0.1)
        
        yield "🧠 Analyzing market trends and data..."
        await asyncio.sleep(0.1)
        
        yield "📈 Generating insights and recommendations..."
        await asyncio.sleep(0.1)
        
        yield f"✅ Research analysis completed for {topic}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get mock agent information."""
        return {
            "agent_name": "Mock Research Agent",
            "agent_type": "research",
            "version": "1.0.0-mock",
            "model_name": self.model_name,
            "capabilities": ["Mock research", "Mock streaming"],
            "status": "mock_ready"
        }

logger = logging.getLogger(__name__)


class ResearchService:
    """
    Service layer for Financial Research Agent operations.
    
    This service orchestrates research agent operations, provides error handling,
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
        Initialize the Research Service.
        
        Args:
            groq_api_key: API key for Groq LLM service
            model_name: LLM model to use for analysis
            timeout_seconds: Timeout for operations
            max_retries: Maximum number of retries for failed operations
            **kwargs: Additional configuration parameters
        """
        # Create the real research agent
        self.agent = ResearchAgent(groq_api_key, model_name, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.service_name = "ResearchService"
        
        logger.info(f"Initialized {self.service_name} with model {model_name}")
    
    async def execute_research_analysis(
        self, 
        request: ResearchRequest
    ) -> ResearchResponse:
        """
        Execute financial research analysis with error handling and retries.
        
        Args:
            request: Research analysis request
            
        Returns:
            ResearchResponse with analysis results
            
        Raises:
            ValidationException: If request validation fails
            TimeoutException: If operation times out
            AgentProcessingException: If analysis fails after retries
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting research analysis for topic: {request.topic}")
            
            # Execute analysis with timeout and retries
            result = await self._execute_with_retry(
                self.agent.process_request,
                request.dict(),
                operation_name="research_analysis"
            )
            
            # Convert to response model
            response = ResearchResponse(**result)
            response.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Research analysis completed successfully in {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Research analysis failed after {processing_time:.2f}s: {str(e)}")
            
            # Re-raise known exceptions
            if isinstance(e, (ValidationException, TimeoutException, AgentProcessingException)):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="ResearchAgent",
                message=f"Unexpected error during research analysis: {str(e)}",
                processing_stage="service_orchestration"
            ) 
   
    async def stream_research_analysis(
        self, 
        request: ResearchRequest
    ) -> AsyncGenerator[str, None]:
        """
        Stream financial research analysis with enhanced progress tracking.
        
        This method provides real-time streaming of research analysis with detailed
        progress updates, source discovery notifications, and transparent processing steps.
        
        Args:
            request: Research analysis request
            
        Yields:
            String chunks of the streaming response with progress indicators
            
        Raises:
            ValidationException: If request validation fails
            AgentProcessingException: If streaming fails
        """
        try:
            logger.info(f"Starting streaming research analysis for topic: {request.topic}")
            
            # Yield initial status
            yield f"🔍 Starting research analysis for: {request.topic}"
            yield f"📊 Configuration: {request.sources_limit} sources, outlook: {request.include_outlook}"
            
            # Initialize progress tracking
            total_steps = 5  # Search, fetch, analyze, format, complete
            current_step = 0
            
            # Step 1: Search phase
            current_step += 1
            yield f"[{current_step}/{total_steps}] 🔎 Searching for authoritative sources..."
            
            # Step 2: Source processing
            current_step += 1
            yield f"[{current_step}/{total_steps}] 📰 Processing and validating sources..."
            
            # Stream the actual analysis with enhanced progress tracking
            chunk_count = 0
            async for chunk in self.agent.stream_response(request.dict()):
                chunk_count += 1
                
                # Add contextual information based on chunk content
                if "sources found" in chunk.lower():
                    yield f"✅ {chunk}"
                elif "analyzing" in chunk.lower():
                    current_step += 1
                    yield f"[{current_step}/{total_steps}] 🧠 {chunk}"
                elif "generating report" in chunk.lower():
                    current_step += 1
                    yield f"[{current_step}/{total_steps}] 📝 {chunk}"
                elif "executive summary" in chunk.lower():
                    yield f"📋 {chunk}"
                elif "future outlook" in chunk.lower():
                    yield f"🔮 {chunk}"
                else:
                    yield chunk
                
                # Periodic progress updates for long streams
                if chunk_count % 10 == 0:
                    yield f"📈 Processing... ({chunk_count} updates sent)"
            
            # Final completion
            current_step = total_steps
            yield f"[{current_step}/{total_steps}] ✅ Research analysis completed successfully!"
            yield f"📊 Total updates: {chunk_count}, Topic: {request.topic}"
            
            logger.info(f"Streaming research analysis completed successfully with {chunk_count} chunks")
            
        except ValidationException as e:
            logger.warning(f"Validation error in streaming research: {str(e)}")
            yield f"❌ Validation Error: {str(e)}"
            raise e
            
        except TimeoutException as e:
            logger.error(f"Timeout in streaming research: {str(e)}")
            yield f"⏰ Timeout Error: Research analysis timed out after {e.timeout_seconds} seconds"
            raise e
            
        except DataSourceException as e:
            logger.error(f"Data source error in streaming research: {str(e)}")
            yield f"🔌 Data Source Error: {str(e)}"
            raise e
            
        except Exception as e:
            logger.error(f"Streaming research analysis failed: {str(e)}")
            yield f"💥 Unexpected Error: {str(e)}"
            
            # Re-raise known exceptions
            if isinstance(e, AgentProcessingException):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="ResearchAgent",
                message=f"Streaming research analysis failed: {str(e)}",
                processing_stage="streaming_service"
            )
            # Send error message to stream
            yield f"❌ **Analysis Failed:** {str(e)}\n"
            
            # Re-raise for upstream handling
            if isinstance(e, (ValidationException, AgentProcessingException)):
                raise e
            
            raise AgentProcessingException(
                agent_name="ResearchAgent",
                message=f"Streaming analysis failed: {str(e)}",
                processing_stage="streaming_service"
            )
    
    async def get_research_suggestions(self, domain: str = "finance") -> Dict[str, Any]:
        """
        Get suggested research topics for a given domain.
        
        Args:
            domain: Domain for topic suggestions
            
        Returns:
            Dictionary containing suggested topics
        """
        try:
            # Define topic suggestions based on domain
            suggestions = {
                "finance": [
                    "Federal Reserve interest rate policy impact",
                    "Cryptocurrency market trends and regulation",
                    "ESG investing and sustainable finance",
                    "Inflation trends and economic indicators",
                    "Technology sector growth prospects",
                    "Real estate market outlook",
                    "Energy transition and renewable investments",
                    "Supply chain disruption effects on markets"
                ],
                "markets": [
                    "Emerging markets investment opportunities",
                    "Bond market dynamics and yield curves",
                    "Sector rotation strategies",
                    "Market volatility and risk management",
                    "International trade impact on equities"
                ],
                "economy": [
                    "Labor market trends and employment data",
                    "Consumer spending patterns",
                    "GDP growth forecasts",
                    "Central bank monetary policies",
                    "Global economic recovery trends"
                ]
            }
            
            return {
                "domain": domain,
                "suggested_topics": suggestions.get(domain, suggestions["finance"]),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get research suggestions: {str(e)}")
            return {
                "domain": domain,
                "suggested_topics": ["Market analysis", "Economic trends", "Investment opportunities"],
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
                
            except Exception as e:
                logger.error(f"{operation_name} failed with unexpected error: {str(e)}")
                last_exception = e
                break  # Don't retry unexpected errors
        
        # All retries exhausted
        if last_exception:
            if isinstance(last_exception, (RateLimitException, DataSourceException)):
                raise last_exception
            
            raise AgentProcessingException(
                agent_name="ResearchAgent",
                message=f"{operation_name} failed after {self.max_retries + 1} attempts: {str(last_exception)}",
                processing_stage="retry_logic"
            )
        
        raise AgentProcessingException(
            agent_name="ResearchAgent",
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
            "agent_type": "financial_research",
            "version": "1.0.0",
            "description": "Service for orchestrating financial research analysis operations",
            "capabilities": [
                "Financial research analysis",
                "Real-time streaming responses",
                "Research topic suggestions",
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