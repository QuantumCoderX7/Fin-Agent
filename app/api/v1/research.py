"""
Research agent API endpoints.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict, Any

from app.config.settings import Settings
from app.api.deps import validate_api_keys, get_research_service
from app.services.research_service import ResearchService
from app.models.requests import ResearchRequest
from app.models.responses import ResearchResponse, ErrorResponse
from app.utils.exceptions import (
    ValidationException,
    AgentProcessingException,
    TimeoutException,
    DataSourceException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/")
async def research_status(
    settings: Settings = Depends(validate_api_keys),
    research_service: ResearchService = Depends(get_research_service)
):
    """Get research agent status."""
    return {
        "status": "ready", 
        "agent": "research",
        "service_initialized": research_service is not None,
        "available_endpoints": [
            "GET /research/ - Get status",
            "POST /research/analyze - Analyze financial topic",
            "GET /research/topics - Get suggested topics",
            "POST /research/stream - Stream analysis"
        ]
    }


@router.post("/analyze", response_model=ResearchResponse)
async def analyze_research_topic(
    request: ResearchRequest,
    settings: Settings = Depends(validate_api_keys),
    research_service: ResearchService = Depends(get_research_service)
):
    """
    Conduct comprehensive financial research analysis on a given topic.
    
    This endpoint performs in-depth research using multiple authoritative sources,
    providing structured analysis with executive summary, detailed findings,
    and future outlook.
    
    - **topic**: Financial research topic to analyze
    - **sources_limit**: Number of sources to search (1-10, default: 5)
    - **include_outlook**: Whether to include future outlook section
    - **focus_areas**: Specific areas to focus on in the research
    - **time_horizon**: Time horizon for analysis
    
    Returns comprehensive research report with verified data and insights.
    """
    try:
        logger.info(f"Received research analysis request for topic: {request.topic}")
        
        # Execute research analysis
        response = await research_service.execute_research_analysis(request)
        
        logger.info(f"Research analysis completed successfully for topic: {request.topic}")
        return response
        
    except ValidationException as e:
        logger.warning(f"Validation error in research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "suggestions": [
                    "Check that your research topic is valid and not empty",
                    "Ensure sources_limit is between 1 and 10",
                    "Verify that focus_areas contain valid content"
                ]
            }
        )
        
    except TimeoutException as e:
        logger.error(f"Timeout error in research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "error_code": "REQUEST_TIMEOUT",
                "message": str(e),
                "suggestions": [
                    "Try reducing the number of sources",
                    "Simplify your research topic",
                    "Retry the request"
                ]
            }
        )
        
    except DataSourceException as e:
        logger.error(f"Data source error in research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "DATA_SOURCE_ERROR",
                "message": str(e),
                "suggestions": [
                    "Check your internet connection",
                    "Try again in a few minutes",
                    "Contact support if the issue persists"
                ]
            }
        )
        
    except AgentProcessingException as e:
        logger.error(f"Agent processing error in research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "AGENT_PROCESSING_ERROR",
                "message": str(e),
                "suggestions": [
                    "Try rephrasing your research topic",
                    "Reduce the complexity of your request",
                    "Contact support if the issue persists"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during research analysis",
                "suggestions": [
                    "Try your request again",
                    "Contact support if the issue persists"
                ]
            }
        )


@router.get("/topics")
async def get_research_topics(
    domain: str = "finance",
    settings: Settings = Depends(validate_api_keys),
    research_service: ResearchService = Depends(get_research_service)
) -> Dict[str, Any]:
    """
    Get suggested research topics for financial analysis.
    
    This endpoint provides curated lists of relevant financial research topics
    based on current market trends and common analysis areas.
    
    - **domain**: Domain for topic suggestions (finance, markets, economy)
    
    Returns list of suggested topics with metadata.
    """
    try:
        logger.info(f"Received request for research topics in domain: {domain}")
        
        # Get topic suggestions
        suggestions = await research_service.get_research_suggestions(domain)
        
        logger.info(f"Successfully retrieved {len(suggestions.get('suggested_topics', []))} topic suggestions")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error retrieving research topics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "TOPIC_RETRIEVAL_ERROR",
                "message": "Failed to retrieve research topic suggestions",
                "suggestions": [
                    "Try again with a different domain",
                    "Contact support if the issue persists"
                ]
            }
        )


@router.post("/stream")
async def stream_research_analysis(
    request: ResearchRequest,
    settings: Settings = Depends(validate_api_keys),
    research_service: ResearchService = Depends(get_research_service)
):
    """
    Stream real-time financial research analysis.
    
    This endpoint provides real-time streaming of research analysis results,
    allowing clients to receive progressive updates as the analysis is conducted.
    
    - **topic**: Financial research topic to analyze
    - **sources_limit**: Number of sources to search (1-10, default: 5)
    - **include_outlook**: Whether to include future outlook section
    - **focus_areas**: Specific areas to focus on in the research
    - **time_horizon**: Time horizon for analysis
    
    Returns Server-Sent Events stream with analysis progress and results.
    """
    from app.api.streaming import create_streaming_response, ProgressTracker
    
    try:
        logger.info(f"Received streaming research analysis request for topic: {request.topic}")
        
        async def generate_stream():
            """Generate streaming response with progress tracking."""
            try:
                # Initialize progress tracker
                progress = ProgressTracker(
                    total_steps=5,  # Search, fetch, analyze, format, complete
                    operation_name=f"Research Analysis: {request.topic}"
                )
                
                # Send initial progress
                yield {"progress": progress.update("Initializing research analysis...")}
                
                # Update progress for search phase
                yield {"progress": progress.update("Searching for sources...")}
                
                # Stream analysis results with progress updates
                async for chunk in research_service.stream_research_analysis(request):
                    if "sources found" in chunk.lower():
                        yield {"progress": progress.update("Processing sources...")}
                    elif "analyzing" in chunk.lower():
                        yield {"progress": progress.update("Analyzing data...")}
                    elif "generating report" in chunk.lower():
                        yield {"progress": progress.update("Generating report...")}
                    
                    # Send content chunk
                    yield {"content": chunk}
                
                # Send completion
                yield {"progress": progress.complete()}
                
            except ValidationException as e:
                yield {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
                
            except TimeoutException as e:
                yield {"error": {"code": "REQUEST_TIMEOUT", "message": str(e)}}
                
            except DataSourceException as e:
                yield {"error": {"code": "DATA_SOURCE_ERROR", "message": str(e)}}
                
            except AgentProcessingException as e:
                yield {"error": {"code": "AGENT_PROCESSING_ERROR", "message": str(e)}}
                
            except Exception as e:
                logger.error(f"Unexpected error in streaming research analysis: {str(e)}")
                yield {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"}}
        
        return create_streaming_response(generate_stream())
        
    except Exception as e:
        logger.error(f"Error setting up streaming research analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STREAMING_SETUP_ERROR",
                "message": "Failed to set up streaming analysis",
                "suggestions": [
                    "Try the non-streaming analyze endpoint instead",
                    "Contact support if the issue persists"
                ]
            }
        )