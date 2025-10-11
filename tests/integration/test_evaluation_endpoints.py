"""
Integration tests for RAG evaluation endpoints.

These tests verify the functionality of evaluation endpoints with mocked services.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Set up test environment BEFORE importing app modules
os.environ["GROQ_API_KEY"] = "test-groq-key"
os.environ["PHI_API_KEY"] = "test-phi-key"

from app.main import create_app
from app.models.responses import RAGEvaluationResponse, EvaluationScore
from app.models.requests import EvaluationCriteria
from app.api.deps import get_evaluation_service


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_evaluation_service():
    """Mock evaluation service for testing."""
    service = MagicMock()
    service.execute_rag_evaluation = AsyncMock()
    service.batch_evaluate_responses = AsyncMock()
    service.get_evaluation_metrics = AsyncMock()
    return service


@pytest.fixture
def sample_evaluation_response():
    """Sample evaluation response for testing."""
    return RAGEvaluationResponse(
        overall_score=4.2,
        scores=[
            EvaluationScore(
                criterion="faithfulness",
                score=4,
                justification="Response accurately reflects the provided context",
                examples=["Correctly cites financial data from sources"],
                suggestions=["Could provide more specific citations"]
            ),
            EvaluationScore(
                criterion="relevance",
                score=5,
                justification="Response directly addresses the query",
                examples=["Focuses on requested financial metrics"],
                suggestions=[]
            ),
            EvaluationScore(
                criterion="completeness",
                score=4,
                justification="Covers most aspects but could be more comprehensive",
                examples=["Addresses main points but lacks some details"],
                suggestions=["Include more historical context"]
            )
        ],
        summary="High-quality response with good accuracy and relevance",
        strengths=[
            "Accurate use of financial data",
            "Clear and well-structured response",
            "Directly addresses the query"
        ],
        weaknesses=[
            "Could provide more detailed analysis",
            "Missing some contextual information"
        ],
        recommendations=[
            "Add more specific citations",
            "Include historical context for better understanding",
            "Provide more detailed financial analysis"
        ],
        query="What is the current P/E ratio of Apple Inc?",
        response_length=245,
        context_utilization=0.85,
        factual_accuracy="High",
        processing_time=8.5
    )


@pytest.fixture
def valid_evaluation_request():
    """Valid evaluation request for testing."""
    return {
        "query": "What is the current P/E ratio of Apple Inc?",
        "response": "Apple Inc (AAPL) currently has a P/E ratio of approximately 28.5 based on the latest financial data. This indicates that investors are willing to pay $28.50 for every dollar of earnings, which is considered reasonable for a technology company of Apple's caliber.",
        "context": [
            "Apple Inc financial metrics: P/E ratio 28.5, Market Cap $2.8T",
            "Technology sector average P/E ratio: 25.3",
            "Apple's historical P/E range: 15-35 over past 5 years"
        ],
        "evaluation_criteria": ["faithfulness", "relevance", "completeness"],
        "include_recommendations": True,
        "detailed_feedback": True
    }


@pytest.fixture
def sample_metrics_response():
    """Sample metrics response for testing."""
    return {
        "evaluation_criteria": {
            "faithfulness": {
                "name": "Faithfulness",
                "description": "How well the response reflects the provided context",
                "weight": 0.25,
                "scoring_range": "1-5",
                "scoring_guidelines": {
                    "1": "Poor - Response contradicts context",
                    "2": "Below Average - Some inaccuracies",
                    "3": "Average - Generally accurate",
                    "4": "Good - Mostly accurate with minor issues",
                    "5": "Excellent - Completely accurate"
                }
            },
            "relevance": {
                "name": "Relevance",
                "description": "How well the response addresses the original query",
                "weight": 0.25,
                "scoring_range": "1-5",
                "scoring_guidelines": {
                    "1": "Poor - Off-topic response",
                    "2": "Below Average - Partially relevant",
                    "3": "Average - Generally relevant",
                    "4": "Good - Highly relevant",
                    "5": "Excellent - Perfectly addresses query"
                }
            }
        },
        "overall_scoring": {
            "range": "1.0-5.0",
            "calculation": "Weighted average of individual criterion scores",
            "guidelines": {
                "1": "Poor quality response",
                "2": "Below average quality",
                "3": "Average quality",
                "4": "Good quality",
                "5": "Excellent quality"
            }
        },
        "service_info": {
            "version": "1.0.0",
            "model": "qwen/qwen3-32b",
            "capabilities": [
                "Multi-criteria evaluation",
                "Detailed scoring with justification",
                "Improvement recommendations",
                "Batch processing support"
            ]
        },
        "generated_at": datetime.utcnow().isoformat()
    }


class TestEvaluationEndpoints:
    """Test cases for evaluation endpoints."""
    
    def test_evaluation_status(self, app, client, mock_evaluation_service):
        """Test evaluation status endpoint."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        try:
            response = client.get("/api/v1/evaluation/")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "ready"
            assert data["agent"] == "evaluation"
            assert "available_endpoints" in data
            assert len(data["available_endpoints"]) == 4
        finally:
            app.dependency_overrides.clear()
    
    def test_assess_success(self, app, client, mock_evaluation_service, sample_evaluation_response, valid_evaluation_request):
        """Test successful RAG response assessment."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        # Setup mock
        mock_evaluation_service.execute_rag_evaluation.return_value = sample_evaluation_response
        
        try:
            response = client.post("/api/v1/evaluation/assess", json=valid_evaluation_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["overall_score"] == 4.2
            assert data["query"] == "What is the current P/E ratio of Apple Inc?"
            assert data["response_length"] == 245
            assert data["context_utilization"] == 0.85
            assert len(data["scores"]) == 3
            assert len(data["strengths"]) == 3
            assert len(data["weaknesses"]) == 2
            assert len(data["recommendations"]) == 3
            
            # Check individual scores
            scores_by_criterion = {score["criterion"]: score for score in data["scores"]}
            assert scores_by_criterion["faithfulness"]["score"] == 4
            assert scores_by_criterion["relevance"]["score"] == 5
            assert scores_by_criterion["completeness"]["score"] == 4
            
            # Verify service was called
            mock_evaluation_service.execute_rag_evaluation.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_assess_invalid_request(self, app, client, mock_evaluation_service):
        """Test assessment with invalid request."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        try:
            # Request with missing required fields
            invalid_request = {"query": "test"}
            response = client.post("/api/v1/evaluation/assess", json=invalid_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_assess_empty_context(self, app, client, mock_evaluation_service):
        """Test assessment with empty context."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        try:
            # Request with empty context
            invalid_request = {
                "query": "What is the P/E ratio?",
                "response": "The P/E ratio is 25.",
                "context": []
            }
            response = client.post("/api/v1/evaluation/assess", json=invalid_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_get_metrics_success(self, app, client, mock_evaluation_service, sample_metrics_response):
        """Test successful metrics retrieval."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        # Setup mock
        mock_evaluation_service.get_evaluation_metrics.return_value = sample_metrics_response
        
        try:
            response = client.get("/api/v1/evaluation/metrics")
            assert response.status_code == 200
            
            data = response.json()
            assert "evaluation_criteria" in data
            assert "overall_scoring" in data
            assert "service_info" in data
            assert "generated_at" in data
            
            # Check criteria structure
            criteria = data["evaluation_criteria"]
            assert "faithfulness" in criteria
            assert "relevance" in criteria
            
            # Check faithfulness criteria details
            faithfulness = criteria["faithfulness"]
            assert faithfulness["name"] == "Faithfulness"
            assert faithfulness["weight"] == 0.25
            assert faithfulness["scoring_range"] == "1-5"
            assert "scoring_guidelines" in faithfulness
            
            # Verify service was called
            mock_evaluation_service.get_evaluation_metrics.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_batch_evaluate_success(self, app, client, mock_evaluation_service):
        """Test successful batch evaluation."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        # Setup mock batch response
        batch_result = {
            "status": "completed",
            "total_requests": 2,
            "successful_evaluations": 2,
            "failed_evaluations": 0,
            "success_rate": 100.0,
            "average_scores": {
                "faithfulness": 4.0,
                "relevance": 4.5,
                "completeness": 3.5
            },
            "processing_time": 15.2,
            "results": [
                {
                    "overall_score": 4.2,
                    "query": "Query 1",
                    "summary": "Good quality response"
                },
                {
                    "overall_score": 3.8,
                    "query": "Query 2", 
                    "summary": "Average quality response"
                }
            ],
            "errors": [],
            "generated_at": datetime.utcnow().isoformat()
        }
        mock_evaluation_service.batch_evaluate_responses.return_value = batch_result
        
        try:
            # Create batch request
            batch_request = {
                "requests": [
                    {
                        "query": "What is Apple's P/E ratio?",
                        "response": "Apple's P/E ratio is 28.5",
                        "context": ["Apple financial data: P/E 28.5"]
                    },
                    {
                        "query": "What is Google's market cap?",
                        "response": "Google's market cap is $1.7T",
                        "context": ["Google financial data: Market cap $1.7T"]
                    }
                ],
                "parallel_processing": True,
                "fail_fast": False
            }
            
            response = client.post("/api/v1/evaluation/batch", json=batch_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "completed"
            assert data["total_requests"] == 2
            assert data["successful_evaluations"] == 2
            assert data["failed_evaluations"] == 0
            assert data["success_rate"] == 100.0
            assert len(data["results"]) == 2
            assert len(data["errors"]) == 0
            
            # Check average scores
            avg_scores = data["average_scores"]
            assert avg_scores["faithfulness"] == 4.0
            assert avg_scores["relevance"] == 4.5
            assert avg_scores["completeness"] == 3.5
            
            # Verify service was called
            mock_evaluation_service.batch_evaluate_responses.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_batch_evaluate_invalid_request(self, app, client, mock_evaluation_service):
        """Test batch evaluation with invalid request."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        try:
            # Request with empty batch
            invalid_request = {"requests": []}
            response = client.post("/api/v1/evaluation/batch", json=invalid_request)
            assert response.status_code == 422
            
            data = response.json()
            assert "detail" in data
        finally:
            app.dependency_overrides.clear()
    
    def test_batch_evaluate_validation_error(self, app, client, mock_evaluation_service):
        """Test batch evaluation with validation errors."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        try:
            # Create batch request with invalid data
            batch_request = {
                "requests": [
                    {
                        "query": "What is Apple's P/E ratio?",
                        "response": "Apple's P/E ratio is 28.5",
                        "context": ["Apple financial data: P/E 28.5"]
                    },
                    {
                        "query": "",  # Invalid empty query
                        "response": "Some response",
                        "context": ["Some context"]
                    }
                ]
            }
            
            response = client.post("/api/v1/evaluation/batch", json=batch_request)
            assert response.status_code == 400
            
            data = response.json()
            assert data["detail"]["error_code"] == "BATCH_VALIDATION_ERROR"
            assert "Invalid evaluation request at index 1" in data["detail"]["message"]
            
            # Verify service was not called due to validation error
            mock_evaluation_service.batch_evaluate_responses.assert_not_called()
        finally:
            app.dependency_overrides.clear()
    
    def test_batch_evaluate_partial_failure(self, app, client, mock_evaluation_service):
        """Test batch evaluation with partial failures during processing."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        # Setup mock batch response with failures that occur during processing
        batch_result = {
            "status": "completed",
            "total_requests": 3,
            "successful_evaluations": 2,
            "failed_evaluations": 1,
            "success_rate": 66.7,
            "average_scores": {
                "faithfulness": 4.0,
                "relevance": 4.5
            },
            "processing_time": 18.5,
            "results": [
                {
                    "overall_score": 4.2,
                    "query": "Query 1",
                    "summary": "Good quality response"
                },
                {
                    "overall_score": 3.8,
                    "query": "Query 2",
                    "summary": "Average quality response"
                }
            ],
            "errors": [
                {
                    "index": 2,
                    "error": "Processing timeout",
                    "query": "Complex query that timed out..."
                }
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        mock_evaluation_service.batch_evaluate_responses.return_value = batch_result
        
        try:
            # Create batch request with valid data (failures happen during processing)
            batch_request = {
                "requests": [
                    {
                        "query": "What is Apple's P/E ratio?",
                        "response": "Apple's P/E ratio is 28.5",
                        "context": ["Apple financial data: P/E 28.5"]
                    },
                    {
                        "query": "What is Google's market cap?",
                        "response": "Google's market cap is $1.7T",
                        "context": ["Google financial data: Market cap $1.7T"]
                    },
                    {
                        "query": "Complex query that will timeout during processing",
                        "response": "Some complex response",
                        "context": ["Complex context that causes timeout"]
                    }
                ]
            }
            
            response = client.post("/api/v1/evaluation/batch", json=batch_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "completed"
            assert data["total_requests"] == 3
            assert data["successful_evaluations"] == 2
            assert data["failed_evaluations"] == 1
            assert data["success_rate"] == 66.7
            assert len(data["results"]) == 2
            assert len(data["errors"]) == 1
            
            # Check error details
            error = data["errors"][0]
            assert error["index"] == 2
            assert "error" in error
            
            # Verify service was called
            mock_evaluation_service.batch_evaluate_responses.assert_called_once()
        finally:
            app.dependency_overrides.clear()
    
    def test_assess_with_specific_criteria(self, app, client, mock_evaluation_service, sample_evaluation_response):
        """Test assessment with specific evaluation criteria."""
        # Override dependency
        app.dependency_overrides[get_evaluation_service] = lambda: mock_evaluation_service
        
        # Setup mock
        mock_evaluation_service.execute_rag_evaluation.return_value = sample_evaluation_response
        
        try:
            # Request with specific criteria
            request_with_criteria = {
                "query": "What is the current P/E ratio of Apple Inc?",
                "response": "Apple Inc has a P/E ratio of 28.5",
                "context": ["Apple financial data: P/E ratio 28.5"],
                "evaluation_criteria": ["faithfulness", "relevance"],
                "include_recommendations": False,
                "detailed_feedback": False
            }
            
            response = client.post("/api/v1/evaluation/assess", json=request_with_criteria)
            assert response.status_code == 200
            
            data = response.json()
            assert data["overall_score"] == 4.2
            
            # Verify service was called
            mock_evaluation_service.execute_rag_evaluation.assert_called_once()
            
            # Check that the request was properly formed
            call_args = mock_evaluation_service.execute_rag_evaluation.call_args[0][0]
            assert call_args.evaluation_criteria == ["faithfulness", "relevance"]
            assert call_args.include_recommendations == False
            assert call_args.detailed_feedback == False
        finally:
            app.dependency_overrides.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])