"""
Evaluation Service for orchestrating RAG assessment operations.

This service provides business logic layer for the RAG Evaluator Agent,
handling request orchestration, error management, and response formatting.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from app.agents.rag_evaluator import RAGEvaluator
from app.models.requests import RAGEvaluationRequest, EvaluationCriteria
from app.models.responses import RAGEvaluationResponse, ResponseStatus, ErrorResponse
from app.utils.exceptions import (
    ValidationException,
    AgentProcessingException,
    TimeoutException,
    RateLimitException
)

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Service layer for RAG Evaluator Agent operations.
    
    This service orchestrates RAG evaluation operations, provides error handling,
    retry logic, and ensures consistent response formatting.
    """
    
    def __init__(
        self, 
        groq_api_key: str,
        model_name: str = "qwen/qwen3-32b",
        timeout_seconds: int = 180,
        max_retries: int = 2,
        **kwargs
    ):
        """
        Initialize the Evaluation Service.
        
        Args:
            groq_api_key: API key for Groq LLM service
            model_name: LLM model to use for evaluation
            timeout_seconds: Timeout for operations
            max_retries: Maximum number of retries for failed operations
            **kwargs: Additional configuration parameters
        """
        self.agent = RAGEvaluator(groq_api_key, model_name, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.service_name = "EvaluationService"
        
        logger.info(f"Initialized {self.service_name} with model {model_name}")
    
    async def execute_rag_evaluation(
        self, 
        request: RAGEvaluationRequest
    ) -> RAGEvaluationResponse:
        """
        Execute RAG response evaluation with error handling and retries.
        
        Args:
            request: RAG evaluation request
            
        Returns:
            RAGEvaluationResponse with evaluation results
            
        Raises:
            ValidationException: If request validation fails
            TimeoutException: If operation times out
            AgentProcessingException: If evaluation fails after retries
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting RAG evaluation for query: {request.query[:100]}...")
            
            # Execute evaluation with timeout and retries
            result = await self._execute_with_retry(
                self.agent.process_request,
                request.dict(),
                operation_name="rag_evaluation"
            )
            
            # Convert to response model
            response = RAGEvaluationResponse(**result)
            response.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"RAG evaluation completed successfully in {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"RAG evaluation failed after {processing_time:.2f}s: {str(e)}")
            
            # Re-raise known exceptions
            if isinstance(e, (ValidationException, TimeoutException, AgentProcessingException)):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="RAGEvaluator",
                message=f"Unexpected error during RAG evaluation: {str(e)}",
                processing_stage="service_orchestration"
            )    

    async def stream_rag_evaluation(
        self, 
        request: RAGEvaluationRequest
    ) -> AsyncGenerator[str, None]:
        """
        Stream RAG evaluation with real-time progress updates.
        
        This method provides streaming evaluation results, breaking down the evaluation
        process into steps and yielding progress updates and partial results.
        
        Args:
            request: RAG evaluation request
            
        Yields:
            String chunks containing progress updates and evaluation results
            
        Raises:
            ValidationException: If request validation fails
            AgentProcessingException: If streaming evaluation fails
        """
        try:
            logger.info(f"Starting streaming RAG evaluation for query: {request.query[:100]}...")
            
            # Yield initial status
            yield "RAG Response Evaluation Starting..."
            
            # Determine evaluation criteria
            criteria = request.evaluation_criteria or ["faithfulness", "relevance", "completeness", "coherence", "source_attribution"]
            total_criteria = len(criteria)
            
            yield f"Evaluating response across {total_criteria} criteria: {', '.join(criteria)}"
            
            # Initialize evaluation results
            evaluation_scores = []
            
            # Process each criterion with streaming updates
            for i, criterion in enumerate(criteria, 1):
                yield f"[{i}/{total_criteria}] Analyzing {criterion}..."
                
                # Simulate criterion-specific evaluation (in real implementation, this would call the agent)
                try:
                    # For now, we'll use the full evaluation and extract relevant parts
                    # In a more sophisticated implementation, we could evaluate criteria individually
                    if i == 1:  # Only do full evaluation once
                        full_result = await self._execute_with_retry(
                            self.agent.process_request,
                            request.dict(),
                            operation_name="streaming_rag_evaluation"
                        )
                        self._full_evaluation_result = full_result
                    
                    # Extract score for current criterion
                    criterion_score = None
                    for score in self._full_evaluation_result.get("scores", []):
                        if score.get("criterion") == criterion:
                            criterion_score = score
                            break
                    
                    if criterion_score:
                        evaluation_scores.append(criterion_score)
                        yield f"✓ {criterion}: {criterion_score['score']}/5 - {criterion_score['justification'][:100]}..."
                    else:
                        yield f"⚠ {criterion}: Unable to evaluate this criterion"
                    
                except Exception as e:
                    yield f"✗ {criterion}: Evaluation failed - {str(e)}"
                    logger.warning(f"Criterion {criterion} evaluation failed: {str(e)}")
            
            # Yield progress update
            yield "Generating overall assessment..."
            
            # Calculate overall score
            if evaluation_scores:
                overall_score = sum(score["score"] for score in evaluation_scores) / len(evaluation_scores)
                yield f"Overall Score: {overall_score:.1f}/5.0"
            else:
                yield "Overall Score: Unable to calculate due to evaluation errors"
            
            # Yield summary and recommendations
            yield "Generating summary and recommendations..."
            
            if hasattr(self, '_full_evaluation_result'):
                summary = self._full_evaluation_result.get("summary", "Evaluation completed")
                yield f"Summary: {summary}"
                
                recommendations = self._full_evaluation_result.get("recommendations", [])
                if recommendations:
                    yield "Recommendations:"
                    for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
                        yield f"  {i}. {rec}"
                
                # Clean up temporary result
                delattr(self, '_full_evaluation_result')
            
            yield "RAG evaluation completed successfully!"
            
            logger.info("Streaming RAG evaluation completed successfully")
            
        except Exception as e:
            logger.error(f"Streaming RAG evaluation failed: {str(e)}")
            yield f"Error during evaluation: {str(e)}"
            
            # Re-raise known exceptions
            if isinstance(e, (ValidationException, TimeoutException, AgentProcessingException)):
                raise e
            
            # Wrap unknown exceptions
            raise AgentProcessingException(
                agent_name="RAGEvaluator",
                message=f"Streaming evaluation failed: {str(e)}",
                processing_stage="streaming_service"
            )

    async def batch_evaluate_responses(
        self, 
        evaluations: List[RAGEvaluationRequest]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple RAG responses in batch.
        
        Args:
            evaluations: List of evaluation requests
            
        Returns:
            Dictionary containing batch evaluation results
            
        Raises:
            ValidationException: If batch request is invalid
            AgentProcessingException: If batch processing fails
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting batch RAG evaluation for {len(evaluations)} requests")
            
            if not evaluations:
                raise ValidationException(
                    field_name="evaluations",
                    message="At least one evaluation request is required"
                )
            
            if len(evaluations) > 20:
                raise ValidationException(
                    field_name="evaluations",
                    message="Maximum 20 evaluations allowed per batch"
                )
            
            # Execute evaluations concurrently with limited concurrency
            semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent evaluations
            
            async def evaluate_single(request: RAGEvaluationRequest) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        return await self.execute_rag_evaluation(request)
                    except Exception as e:
                        return {
                            "error": str(e),
                            "query": request.query[:100] + "...",
                            "status": "failed"
                        }
            
            # Execute all evaluations
            results = await asyncio.gather(
                *[evaluate_single(req) for req in evaluations],
                return_exceptions=True
            )
            
            # Process results
            successful_evaluations = []
            failed_evaluations = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_evaluations.append({
                        "index": i,
                        "error": str(result),
                        "query": evaluations[i].query[:100] + "..."
                    })
                elif isinstance(result, dict) and "error" in result:
                    failed_evaluations.append({
                        "index": i,
                        **result
                    })
                else:
                    successful_evaluations.append(result)
            
            # Calculate batch statistics
            total_requests = len(evaluations)
            successful_count = len(successful_evaluations)
            failed_count = len(failed_evaluations)
            
            # Calculate average scores for successful evaluations
            avg_scores = {}
            if successful_evaluations:
                for evaluation in successful_evaluations:
                    if isinstance(evaluation, RAGEvaluationResponse):
                        for score in evaluation.scores:
                            criterion = score.criterion
                            if criterion not in avg_scores:
                                avg_scores[criterion] = []
                            avg_scores[criterion].append(score.score)
                    elif isinstance(evaluation, dict) and "scores" in evaluation:
                        for score in evaluation["scores"]:
                            criterion = score["criterion"]
                            if criterion not in avg_scores:
                                avg_scores[criterion] = []
                            avg_scores[criterion].append(score["score"])
                
                # Calculate averages
                for criterion in avg_scores:
                    avg_scores[criterion] = round(sum(avg_scores[criterion]) / len(avg_scores[criterion]), 2)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            batch_result = {
                "status": "completed",
                "total_requests": total_requests,
                "successful_evaluations": successful_count,
                "failed_evaluations": failed_count,
                "success_rate": round(successful_count / total_requests * 100, 1),
                "average_scores": avg_scores,
                "processing_time": processing_time,
                "results": successful_evaluations,
                "errors": failed_evaluations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Batch evaluation completed: {successful_count}/{total_requests} successful")
            return batch_result
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Batch evaluation failed after {processing_time:.2f}s: {str(e)}")
            
            if isinstance(e, (ValidationException, AgentProcessingException)):
                raise e
            
            raise AgentProcessingException(
                agent_name="RAGEvaluator",
                message=f"Batch evaluation failed: {str(e)}",
                processing_stage="batch_service"
            )
    
    async def get_evaluation_metrics(self) -> Dict[str, Any]:
        """
        Get available evaluation criteria and their descriptions.
        
        Returns:
            Dictionary containing evaluation criteria information
        """
        try:
            criteria_info = {}
            
            for criterion in EvaluationCriteria:
                criterion_data = self.agent.evaluation_criteria.get(criterion, {})
                criteria_info[criterion.value] = {
                    "name": criterion_data.get("name", criterion.value.title()),
                    "description": criterion_data.get("description", ""),
                    "weight": criterion_data.get("weight", 0.2),
                    "scoring_range": "1-5",
                    "scoring_guidelines": self.agent.scoring_guidelines
                }
            
            return {
                "evaluation_criteria": criteria_info,
                "overall_scoring": {
                    "range": "1.0-5.0",
                    "calculation": "Weighted average of individual criterion scores",
                    "guidelines": self.agent.scoring_guidelines
                },
                "service_info": {
                    "version": "1.0.0",
                    "model": self.agent.model_name,
                    "capabilities": [
                        "Multi-criteria evaluation",
                        "Detailed scoring with justification",
                        "Improvement recommendations",
                        "Batch processing support"
                    ]
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get evaluation metrics: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def quick_evaluate(
        self, 
        query: str, 
        response: str, 
        context: List[str],
        criteria: Optional[List[EvaluationCriteria]] = None
    ) -> Dict[str, Any]:
        """
        Perform a quick evaluation with simplified input.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents
            criteria: Optional specific criteria to evaluate
            
        Returns:
            Dictionary containing quick evaluation results
        """
        try:
            # Create evaluation request
            request = RAGEvaluationRequest(
                query=query,
                response=response,
                context=context,
                evaluation_criteria=criteria,
                detailed_feedback=False
            )
            
            # Execute evaluation
            result = await self.execute_rag_evaluation(request)
            
            # Return simplified result
            return {
                "overall_score": result.overall_score,
                "scores": {score.criterion: score.score for score in result.scores},
                "summary": result.summary,
                "top_recommendations": result.recommendations[:3] if result.recommendations else [],
                "generated_at": result.generated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Quick evaluation failed: {str(e)}")
            return {
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
                
            except AgentProcessingException as e:
                logger.warning(f"{operation_name} failed on attempt {attempt + 1}: {str(e)}")
                if attempt < self.max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = min(2 ** attempt, 20)  # Cap at 20 seconds for evaluations
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
            if isinstance(last_exception, (RateLimitException, AgentProcessingException)):
                raise last_exception
            
            raise AgentProcessingException(
                agent_name="RAGEvaluator",
                message=f"{operation_name} failed after {self.max_retries + 1} attempts: {str(last_exception)}",
                processing_stage="retry_logic"
            )
        
        raise AgentProcessingException(
            agent_name="RAGEvaluator",
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
            "agent_type": "rag_evaluation",
            "version": "1.0.0",
            "description": "Service for orchestrating RAG response quality evaluation operations",
            "capabilities": [
                "Multi-criteria RAG evaluation",
                "Batch evaluation processing",
                "Quick evaluation mode",
                "Detailed scoring and feedback",
                "Improvement recommendations",
                "Error handling and retries",
                "Timeout management"
            ],
            "evaluation_criteria": list(EvaluationCriteria),
            "configuration": {
                "timeout_seconds": self.timeout_seconds,
                "max_retries": self.max_retries,
                "model_name": self.agent.model_name
            },
            "agent_info": self.agent.get_agent_info()
        }