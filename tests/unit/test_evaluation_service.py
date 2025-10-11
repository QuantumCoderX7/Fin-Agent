"""
Unit tests for EvaluationService.

This module tests the business logic layer for RAG evaluation operations,
including error handling, retry logic, and response formatting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.evaluation_service import EvaluationService
from app.models.requests import RAGEvaluationRequest, EvaluationCriteria
from app.models.responses import RAGEvaluationResponse, EvaluationScore, ResponseStatus
from app.utils.exceptions import (
    ValidationException,
    AgentProcessingException,
    TimeoutException
)


class TestEvaluationService:
    """Test cases for EvaluationService."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock RAG evaluator agent."""
        agent = Mock()
        agent.process_request = AsyncMock()
        agent.get_agent_info = Mock(return_value={
            "agent_name": "RAGEvaluator",
            "capabilities": ["evaluation", "scoring"]
        })
        agent.model_name = "test-model"
        agent.evaluation_criteria = {
            EvaluationCriteria.FAITHFULNESS: {
                "name": "Faithfulness",
                "description": "How accurately the response reflects the context",
                "weight": 0.25
            },
            EvaluationCriteria.RELEVANCE: {
                "name": "Relevance",
                "description": "How well the response addresses the query",
                "weight": 0.25
            }
        }
        agent.scoring_guidelines = {
            5: "Excellent",
            4: "Good",
            3: "Satisfactory",
            2: "Poor",
            1: "Very Poor"
        }
        return agent
    
    @pytest.fixture
    def service(self, mock_agent):
        """Create an EvaluationService instance with mocked agent."""
        with patch('app.services.evaluation_service.RAGEvaluator', return_value=mock_agent):
            return EvaluationService(
                groq_api_key="test-key",
                timeout_seconds=30,
                max_retries=2
            )
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample RAG evaluation request."""
        return RAGEvaluationRequest(
            query="What is the capital of France?",
            response="The capital of France is Paris, a major European city.",
            context=["France is a country in Europe. Its capital city is Paris."],
            evaluation_criteria=[EvaluationCriteria.FAITHFULNESS, EvaluationCriteria.RELEVANCE]
        )
    
    @pytest.fixture
    def sample_evaluation_scores(self):
        """Create sample evaluation scores."""
        return [
            EvaluationScore(
                criterion="faithfulness",
                score=5,
                justification="Response accurately reflects the context",
                examples=["Correctly states Paris as capital"],
                suggestions=["None needed"]
            ),
            EvaluationScore(
                criterion="relevance",
                score=5,
                justification="Response directly answers the query",
                examples=["Directly answers what was asked"],
                suggestions=["None needed"]
            )
        ]
    
    @pytest.fixture
    def sample_agent_response(self, sample_evaluation_scores):
        """Create a sample agent response."""
        return {
            "status": ResponseStatus.SUCCESS,
            "overall_score": 5.0,
            "scores": sample_evaluation_scores,
            "summary": "Excellent response quality across all criteria",
            "strengths": ["Accurate information", "Direct answer"],
            "weaknesses": [],
            "recommendations": [],
            "query": "What is the capital of France?",
            "response_length": 52,
            "context_utilization": 0.9,
            "factual_accuracy": "High"
        }
    
    @pytest.mark.asyncio
    async def test_execute_rag_evaluation_success(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test successful RAG evaluation execution."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.execute_rag_evaluation(sample_request)
        
        # Verify
        assert isinstance(result, RAGEvaluationResponse)
        assert result.overall_score == 5.0
        assert len(result.scores) == 2
        assert result.processing_time is not None
        mock_agent.process_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_rag_evaluation_with_retry(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test RAG evaluation with retry on failure."""
        # Setup - fail first, succeed second
        mock_agent.process_request.side_effect = [
            AgentProcessingException("RAGEvaluator", "Temporary failure"),
            sample_agent_response
        ]
        
        # Execute
        result = await service.execute_rag_evaluation(sample_request)
        
        # Verify
        assert isinstance(result, RAGEvaluationResponse)
        assert mock_agent.process_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_responses_success(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test successful batch evaluation."""
        # Setup
        requests = [sample_request, sample_request]  # Two identical requests
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.batch_evaluate_responses(requests)
        
        # Verify
        assert result["status"] == "completed"
        assert result["total_requests"] == 2
        assert result["successful_evaluations"] == 2
        assert result["failed_evaluations"] == 0
        assert result["success_rate"] == 100.0
        assert "average_scores" in result
        assert mock_agent.process_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_responses_partial_failure(
        self, 
        service, 
        mock_agent, 
        sample_request, 
        sample_agent_response
    ):
        """Test batch evaluation with partial failures."""
        # Setup
        requests = [sample_request, sample_request, sample_request]
        mock_agent.process_request.side_effect = [
            sample_agent_response,  # Success
            AgentProcessingException("RAGEvaluator", "Evaluation failed"),  # Failure
            sample_agent_response   # Success
        ]
        
        # Execute
        result = await service.batch_evaluate_responses(requests)
        
        # Verify
        assert result["total_requests"] == 3
        assert result["successful_evaluations"] == 2
        assert result["failed_evaluations"] == 1
        assert result["success_rate"] == 66.7
        assert len(result["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_empty_list(self, service):
        """Test batch evaluation with empty request list."""
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.batch_evaluate_responses([])
        
        assert "At least one evaluation request is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_batch_evaluate_too_many_requests(self, service, sample_request):
        """Test batch evaluation with too many requests."""
        # Setup - 21 requests (over the limit of 20)
        requests = [sample_request] * 21
        
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.batch_evaluate_responses(requests)
        
        assert "Maximum 20 evaluations allowed per batch" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_evaluation_metrics(self, service, mock_agent):
        """Test getting evaluation criteria information."""
        # Execute
        result = await service.get_evaluation_metrics()
        
        # Verify
        assert "evaluation_criteria" in result
        assert "overall_scoring" in result
        assert "service_info" in result
        assert "faithfulness" in result["evaluation_criteria"]
        assert "relevance" in result["evaluation_criteria"]
        assert result["service_info"]["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_quick_evaluate_success(
        self, 
        service, 
        mock_agent, 
        sample_agent_response
    ):
        """Test quick evaluation with simplified input."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.quick_evaluate(
            query="What is the capital of France?",
            response="The capital of France is Paris.",
            context=["France's capital is Paris."]
        )
        
        # Verify
        assert "overall_score" in result
        assert "scores" in result
        assert "summary" in result
        assert result["overall_score"] == 5.0
        assert len(result["scores"]) == 2
    
    @pytest.mark.asyncio
    async def test_quick_evaluate_with_criteria(
        self, 
        service, 
        mock_agent, 
        sample_agent_response
    ):
        """Test quick evaluation with specific criteria."""
        # Setup
        mock_agent.process_request.return_value = sample_agent_response
        
        # Execute
        result = await service.quick_evaluate(
            query="What is the capital of France?",
            response="The capital of France is Paris.",
            context=["France's capital is Paris."],
            criteria=[EvaluationCriteria.FAITHFULNESS]
        )
        
        # Verify
        assert "overall_score" in result
        mock_agent.process_request.assert_called_once()
        # Verify the request was created with specific criteria
        call_args = mock_agent.process_request.call_args[0][0]
        assert call_args["evaluation_criteria"] == [EvaluationCriteria.FAITHFULNESS]
    
    @pytest.mark.asyncio
    async def test_quick_evaluate_error_handling(self, service, mock_agent):
        """Test quick evaluation error handling."""
        # Setup
        mock_agent.process_request.side_effect = AgentProcessingException(
            "RAGEvaluator", "Evaluation failed"
        )
        
        # Execute
        result = await service.quick_evaluate(
            query="Test query",
            response="Test response",
            context=["Test context"]
        )
        
        # Verify
        assert "error" in result
        assert "generated_at" in result
    
    def test_get_service_info(self, service, mock_agent):
        """Test getting service information."""
        # Execute
        info = service.get_service_info()
        
        # Verify
        assert info["service_name"] == "EvaluationService"
        assert info["agent_type"] == "rag_evaluation"
        assert info["version"] == "1.0.0"
        assert "capabilities" in info
        assert "Multi-criteria RAG evaluation" in info["capabilities"]
        assert "Batch evaluation processing" in info["capabilities"]
        assert "evaluation_criteria" in info
        assert "configuration" in info
        assert info["configuration"]["timeout_seconds"] == 30
        assert info["configuration"]["max_retries"] == 2
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, service, mock_agent, sample_request):
        """Test timeout exception handling."""
        # Setup
        mock_agent.process_request.side_effect = asyncio.TimeoutError()
        
        # Execute & Verify
        with pytest.raises(TimeoutException):
            await service.execute_rag_evaluation(sample_request)
    
    @pytest.mark.asyncio
    async def test_validation_error_propagation(self, service, mock_agent, sample_request):
        """Test that validation errors are properly propagated."""
        # Setup
        validation_error = ValidationException(
            field_name="query",
            message="Query too short"
        )
        mock_agent.process_request.side_effect = validation_error
        
        # Execute & Verify
        with pytest.raises(ValidationException) as exc_info:
            await service.execute_rag_evaluation(sample_request)
        
        assert exc_info.value.details["field_name"] == "query"
        # Should not retry validation errors
        assert mock_agent.process_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_unexpected_error_wrapping(self, service, mock_agent, sample_request):
        """Test that unexpected errors are properly wrapped."""
        # Setup
        mock_agent.process_request.side_effect = ValueError("Unexpected error")
        
        # Execute & Verify
        with pytest.raises(AgentProcessingException) as exc_info:
            await service.execute_rag_evaluation(sample_request)
        
        assert "rag_evaluation failed after" in str(exc_info.value)
        assert exc_info.value.details["agent_name"] == "RAGEvaluator"