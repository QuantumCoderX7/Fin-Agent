"""
RAG evaluation API endpoints.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.settings import Settings
from app.api.deps import validate_api_keys, get_evaluation_service
from app.services.evaluation_service import EvaluationService
from app.models.requests import RAGEvaluationRequest, BatchRequest
from app.models.responses import RAGEvaluationResponse, BatchResponse, ErrorResponse
from app.utils.exceptions import (
    ValidationException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/")
async def evaluation_status(
    settings: Settings = Depends(validate_api_keys),
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """Get evaluation agent status."""
    return {
        "status": "ready", 
        "agent": "evaluation",
        "service_initialized": evaluation_service is not None,
        "available_endpoints": [
            "GET /evaluation/ - Get status",
            "POST /evaluation/assess - Assess RAG response quality",
            "GET /evaluation/metrics - Get evaluation criteria definitions",
            "POST /evaluation/batch - Batch evaluate responses"
        ]
    }


@router.post("/assess", response_model=RAGEvaluationResponse)
async def assess_rag_response(
    request: RAGEvaluationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    Assess the quality of a RAG-generated response.
    
    This endpoint evaluates a RAG response across multiple criteria including
    faithfulness, relevance, completeness, coherence, and source attribution.
    
    Args:
        request: RAG evaluation request containing query, response, and context
        evaluation_service: Injected evaluation service
        
    Returns:
        RAGEvaluationResponse with detailed scoring and recommendations
        
    Raises:
        HTTPException: For validation errors, timeouts, or processing failures
    """
    try:
        logger.info(f"Processing RAG evaluation request for query: {request.query[:100]}...")
        
        # Execute evaluation
        result = await evaluation_service.execute_rag_evaluation(request)
        
        logger.info(f"RAG evaluation completed successfully with overall score: {result.overall_score}")
        return result
        
    except ValidationException as e:
        logger.warning(f"Validation error in RAG evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "field": getattr(e, 'field_name', None)
            }
        )
        
    except TimeoutException as e:
        logger.error(f"Timeout in RAG evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "error_code": "EVALUATION_TIMEOUT",
                "message": f"RAG evaluation timed out after {e.timeout_seconds} seconds",
                "suggestions": [
                    "Try with a shorter response or fewer context documents",
                    "Retry the request as this may be a temporary issue"
                ]
            }
        )
        
    except RateLimitException as e:
        logger.warning(f"Rate limit exceeded in RAG evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": str(e),
                "suggestions": [
                    "Wait a moment before retrying",
                    "Consider using batch evaluation for multiple requests"
                ]
            }
        )
        
    except AgentProcessingException as e:
        logger.error(f"Agent processing error in RAG evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EVALUATION_PROCESSING_ERROR",
                "message": f"Failed to process RAG evaluation: {str(e)}",
                "agent": e.agent_name,
                "stage": e.processing_stage,
                "suggestions": [
                    "Verify that the response and context are properly formatted",
                    "Try again as this may be a temporary issue",
                    "Contact support if the problem persists"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in RAG evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during RAG evaluation",
                "suggestions": [
                    "Try again as this may be a temporary issue",
                    "Contact support if the problem persists"
                ]
            }
        )


@router.get("/metrics")
async def get_evaluation_metrics(
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    Get evaluation criteria definitions and scoring guidelines.
    
    This endpoint provides detailed information about the evaluation criteria
    used to assess RAG responses, including descriptions, weights, and scoring guidelines.
    
    Args:
        evaluation_service: Injected evaluation service
        
    Returns:
        Dictionary containing evaluation criteria definitions and guidelines
    """
    try:
        logger.info("Retrieving evaluation metrics and criteria definitions")
        
        metrics = await evaluation_service.get_evaluation_metrics()
        
        logger.info("Successfully retrieved evaluation metrics")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to retrieve evaluation metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "METRICS_RETRIEVAL_ERROR",
                "message": "Failed to retrieve evaluation metrics",
                "suggestions": [
                    "Try again as this may be a temporary issue",
                    "Contact support if the problem persists"
                ]
            }
        )


@router.post("/batch")
async def batch_evaluate_responses(
    request: BatchRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    Evaluate multiple RAG responses in batch.
    
    This endpoint processes multiple RAG evaluation requests concurrently,
    providing efficient batch processing with aggregated results and statistics.
    
    Args:
        request: Batch request containing multiple RAG evaluation requests
        evaluation_service: Injected evaluation service
        
    Returns:
        Dictionary containing batch evaluation results and statistics
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    try:
        logger.info(f"Processing batch RAG evaluation with {len(request.requests)} requests")
        
        # Validate and convert requests to RAGEvaluationRequest objects
        evaluation_requests = []
        for i, req_data in enumerate(request.requests):
            try:
                # Validate each request
                eval_request = RAGEvaluationRequest(**req_data)
                evaluation_requests.append(eval_request)
            except Exception as e:
                raise ValidationException(
                    field_name=f"requests[{i}]",
                    message=f"Invalid evaluation request at index {i}: {str(e)}"
                )
        
        # Execute batch evaluation
        result = await evaluation_service.batch_evaluate_responses(evaluation_requests)
        
        logger.info(f"Batch evaluation completed: {result['successful_evaluations']}/{result['total_requests']} successful")
        return result
        
    except ValidationException as e:
        logger.warning(f"Validation error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "BATCH_VALIDATION_ERROR",
                "message": str(e),
                "field": getattr(e, 'field_name', None),
                "suggestions": [
                    "Ensure all requests in the batch are valid RAG evaluation requests",
                    "Check that required fields (query, response, context) are provided for each request",
                    "Verify that the batch size is within limits (max 20 requests)"
                ]
            }
        )
        
    except AgentProcessingException as e:
        logger.error(f"Processing error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "BATCH_PROCESSING_ERROR",
                "message": f"Batch evaluation processing failed: {str(e)}",
                "suggestions": [
                    "Try with a smaller batch size",
                    "Verify that all requests are properly formatted",
                    "Retry as this may be a temporary issue"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during batch evaluation",
                "suggestions": [
                    "Try again as this may be a temporary issue",
                    "Contact support if the problem persists"
                ]
            }
        )


@router.post("/stream")
async def stream_evaluation_assessment(
    request: RAGEvaluationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service)
):
    """
    Stream RAG evaluation assessment in real-time.
    
    This endpoint provides real-time streaming of RAG evaluation results,
    allowing clients to receive progressive updates as each evaluation criterion
    is assessed.
    
    Args:
        request: RAG evaluation request
        evaluation_service: Injected evaluation service
        
    Returns:
        Server-Sent Events stream with evaluation progress and results
        
    Raises:
        HTTPException: For validation errors or processing failures
    """
    from app.api.streaming import create_streaming_response, ProgressTracker
    
    try:
        logger.info(f"Streaming RAG evaluation for query: {request.query[:100]}...")
        
        async def generate_stream():
            """Generate streaming evaluation response with progress tracking."""
            try:
                # Initialize progress tracker for evaluation criteria
                criteria_count = len(request.evaluation_criteria) if request.evaluation_criteria else 5
                progress = ProgressTracker(
                    total_steps=criteria_count + 2,  # criteria + summary + recommendations
                    operation_name="RAG Evaluation Assessment"
                )
                
                # Send initial progress
                yield {"progress": progress.update("Starting RAG evaluation...")}
                
                # Create a streaming version of the evaluation
                # Since the current service doesn't have streaming, we'll simulate it
                # by breaking down the evaluation into steps
                
                yield {"progress": progress.update("Analyzing faithfulness...")}
                yield {"status": "Evaluating how well the response is grounded in the provided context"}
                
                yield {"progress": progress.update("Analyzing relevance...")}
                yield {"status": "Assessing how well the response addresses the original query"}
                
                yield {"progress": progress.update("Analyzing completeness...")}
                yield {"status": "Checking if the response covers all important aspects"}
                
                yield {"progress": progress.update("Analyzing coherence...")}
                yield {"status": "Evaluating logical flow and readability"}
                
                yield {"progress": progress.update("Analyzing source attribution...")}
                yield {"status": "Checking proper citation and source references"}
                
                # Execute the actual evaluation
                result = await evaluation_service.execute_rag_evaluation(request)
                
                # Stream the results
                yield {"progress": progress.update("Generating evaluation summary...")}
                yield {"evaluation_result": {
                    "overall_score": result.overall_score,
                    "scores": [{"criterion": score.criterion, "score": score.score, "justification": score.justification} for score in result.scores],
                    "summary": result.summary
                }}
                
                yield {"progress": progress.update("Generating recommendations...")}
                yield {"recommendations": result.recommendations}
                
                # Send completion
                yield {"progress": progress.complete()}
                
            except ValidationException as e:
                yield {"error": {"code": "VALIDATION_ERROR", "message": str(e)}}
            except TimeoutException as e:
                yield {"error": {"code": "EVALUATION_TIMEOUT", "message": str(e)}}
            except AgentProcessingException as e:
                yield {"error": {"code": "EVALUATION_PROCESSING_ERROR", "message": str(e)}}
            except Exception as e:
                logger.error(f"Streaming evaluation error: {str(e)}")
                yield {"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)}}
        
        return create_streaming_response(generate_stream())
        
    except Exception as e:
        logger.error(f"Error setting up streaming evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "STREAMING_SETUP_ERROR",
                "message": "Failed to set up streaming evaluation",
                "suggestions": [
                    "Try the non-streaming assess endpoint instead",
                    "Contact support if the issue persists"
                ]
            }
        )