"""
Unit tests for the RAG Evaluator Agent.

This module contains comprehensive tests for the RAG Evaluator Agent,
covering all evaluation criteria, scoring logic, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.rag_evaluator import RAGEvaluator
from app.models.requests import RAGEvaluationRequest, EvaluationCriteria
from app.models.responses import RAGEvaluationResponse, EvaluationScore
from app.utils.exceptions import ValidationException, AgentProcessingException


class TestRAGEvaluator:
    """Test suite for RAG Evaluator Agent."""
    
    @pytest.fixture
    def mock_groq_client(self):
        """Mock Groq client for testing."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 4,
            "justification": "Good response with minor issues",
            "examples": ["Example 1", "Example 2"],
            "suggestions": ["Suggestion 1", "Suggestion 2"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client
    
    @pytest.fixture
    def rag_evaluator(self, mock_groq_client):
        """Create RAG Evaluator instance with mocked client."""
        with patch('app.agents.rag_evaluator.AsyncGroq', return_value=mock_groq_client):
            evaluator = RAGEvaluator(groq_api_key="test_key")
            evaluator.groq_client = mock_groq_client
            return evaluator
    
    @pytest.fixture
    def sample_request_data(self):
        """Sample request data for testing."""
        return {
            "query": "What are the benefits of renewable energy?",
            "response": "Renewable energy offers several benefits including reduced carbon emissions, energy independence, and long-term cost savings. Solar and wind power are becoming increasingly cost-effective alternatives to fossil fuels.",
            "context": [
                "Renewable energy sources like solar and wind have seen dramatic cost reductions in recent years.",
                "Studies show that renewable energy can reduce carbon emissions by up to 80% compared to fossil fuels.",
                "Energy independence is a key benefit of renewable energy adoption for many countries."
            ]
        }
    
    def test_initialization(self):
        """Test RAG Evaluator initialization."""
        with patch('app.agents.rag_evaluator.AsyncGroq'):
            evaluator = RAGEvaluator(groq_api_key="test_key", model_name="test_model")
            
            assert evaluator.agent_name == "RAG Evaluator"
            assert evaluator.agent_type == "rag_evaluation"
            assert evaluator.model_name == "test_model"
            assert len(evaluator.evaluation_criteria) == 5
            assert EvaluationCriteria.FAITHFULNESS in evaluator.evaluation_criteria
            assert EvaluationCriteria.RELEVANCE in evaluator.evaluation_criteria
    
    def test_validate_request_valid(self, rag_evaluator, sample_request_data):
        """Test request validation with valid data."""
        result = rag_evaluator.validate_request(sample_request_data)
        assert result is True
    
    def test_validate_request_invalid_missing_query(self, rag_evaluator):
        """Test request validation with missing query."""
        invalid_request = {
            "response": "Test response",
            "context": ["Test context"]
        }
        
        with pytest.raises(ValidationException) as exc_info:
            rag_evaluator.validate_request(invalid_request)
        
        assert "validation failed" in str(exc_info.value)
    
    def test_validate_request_invalid_empty_context(self, rag_evaluator):
        """Test request validation with empty context."""
        invalid_request = {
            "query": "Test query",
            "response": "Test response", 
            "context": []
        }
        
        with pytest.raises(ValidationException) as exc_info:
            rag_evaluator.validate_request(invalid_request)
        
        assert "validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_evaluate_faithfulness_success(self, rag_evaluator, sample_request_data):
        """Test faithfulness evaluation with successful response."""
        score = await rag_evaluator.evaluate_faithfulness(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "faithfulness"
        assert 1 <= score.score <= 5
        assert len(score.justification) > 0
        assert isinstance(score.examples, list)
        assert isinstance(score.suggestions, list)
    
    @pytest.mark.asyncio
    async def test_evaluate_relevance_success(self, rag_evaluator, sample_request_data):
        """Test relevance evaluation with successful response."""
        score = await rag_evaluator.evaluate_relevance(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "relevance"
        assert 1 <= score.score <= 5
        assert len(score.justification) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_completeness_success(self, rag_evaluator, sample_request_data):
        """Test completeness evaluation with successful response."""
        score = await rag_evaluator.evaluate_completeness(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "completeness"
        assert 1 <= score.score <= 5
        assert len(score.justification) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_coherence_success(self, rag_evaluator, sample_request_data):
        """Test coherence evaluation with successful response."""
        score = await rag_evaluator.evaluate_coherence(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "coherence"
        assert 1 <= score.score <= 5
        assert len(score.justification) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_source_attribution_success(self, rag_evaluator, sample_request_data):
        """Test source attribution evaluation with successful response."""
        score = await rag_evaluator.evaluate_source_attribution(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "source_attribution"
        assert 1 <= score.score <= 5
        assert len(score.justification) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_faithfulness_ai_failure(self, rag_evaluator, sample_request_data):
        """Test faithfulness evaluation when AI call fails."""
        # Mock AI failure
        rag_evaluator.groq_client.chat.completions.create.side_effect = Exception("API Error")
        
        score = await rag_evaluator.evaluate_faithfulness(
            sample_request_data["query"],
            sample_request_data["response"],
            sample_request_data["context"]
        )
        
        assert isinstance(score, EvaluationScore)
        assert score.criterion == "faithfulness"
        assert score.score == 3  # Default fallback score
        assert "Evaluation failed" in score.justification
    
    def test_parse_evaluation_response_valid_json(self, rag_evaluator):
        """Test parsing valid JSON evaluation response."""
        json_response = """
        Some text before
        {
            "score": 4,
            "justification": "Good response",
            "examples": ["Example 1"],
            "suggestions": ["Suggestion 1"]
        }
        Some text after
        """
        
        result = rag_evaluator._parse_evaluation_response(json_response)
        
        assert result["score"] == 4
        assert result["justification"] == "Good response"
        assert result["examples"] == ["Example 1"]
        assert result["suggestions"] == ["Suggestion 1"]
    
    def test_parse_evaluation_response_invalid_score(self, rag_evaluator):
        """Test parsing response with invalid score."""
        json_response = """
        {
            "score": 10,
            "justification": "Invalid score"
        }
        """
        
        result = rag_evaluator._parse_evaluation_response(json_response)
        
        assert result["score"] == 3  # Should default to 3 for invalid scores
        assert result["justification"] == "Invalid score"
    
    def test_parse_evaluation_response_no_json(self, rag_evaluator):
        """Test parsing response without JSON format."""
        text_response = "This is just plain text without JSON format"
        
        result = rag_evaluator._parse_evaluation_response(text_response)
        
        assert result["score"] == 3
        assert "This is just plain text" in result["justification"]
        assert isinstance(result["examples"], list)
        assert isinstance(result["suggestions"], list)
    
    def test_parse_evaluation_response_malformed_json(self, rag_evaluator):
        """Test parsing malformed JSON response."""
        malformed_response = '{"score": 4, "justification": "Missing closing brace"'
        
        result = rag_evaluator._parse_evaluation_response(malformed_response)
        
        assert result["score"] == 3
        assert "Evaluation completed but response parsing failed" in result["justification"]
    
    def test_calculate_context_utilization(self, rag_evaluator):
        """Test context utilization calculation."""
        response = "Solar energy and wind power are renewable sources that reduce emissions"
        context = [
            "Solar energy is a clean renewable source",
            "Wind power generates electricity without emissions"
        ]
        
        utilization = rag_evaluator._calculate_context_utilization(response, context)
        
        assert 0.0 <= utilization <= 1.0
        assert isinstance(utilization, float)
    
    def test_calculate_context_utilization_empty_context(self, rag_evaluator):
        """Test context utilization with empty context."""
        response = "Some response text"
        context = []
        
        utilization = rag_evaluator._calculate_context_utilization(response, context)
        
        assert utilization == 0.0
    
    def test_assess_factual_accuracy(self, rag_evaluator):
        """Test factual accuracy assessment."""
        response = "Solar energy reduces carbon emissions significantly"
        context = ["Solar energy is clean and reduces carbon footprint"]
        
        accuracy = rag_evaluator._assess_factual_accuracy(response, context)
        
        assert isinstance(accuracy, str)
        assert len(accuracy) > 0
        assert any(keyword in accuracy.lower() for keyword in ["high", "medium", "low"])
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, rag_evaluator, sample_request_data):
        """Test successful request processing."""
        result = await rag_evaluator.process_request(sample_request_data)
        
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "scores" in result
        assert "summary" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "recommendations" in result
        
        assert 1.0 <= result["overall_score"] <= 5.0
        assert isinstance(result["scores"], list)
        assert len(result["scores"]) == 5  # All criteria evaluated by default
    
    @pytest.mark.asyncio
    async def test_process_request_specific_criteria(self, rag_evaluator, sample_request_data):
        """Test request processing with specific evaluation criteria."""
        sample_request_data["evaluation_criteria"] = ["faithfulness", "relevance"]
        
        result = await rag_evaluator.process_request(sample_request_data)
        
        assert len(result["scores"]) == 2
        criteria_names = [score["criterion"] for score in result["scores"]]
        assert "faithfulness" in criteria_names
        assert "relevance" in criteria_names
    
    @pytest.mark.asyncio
    async def test_process_request_validation_error(self, rag_evaluator):
        """Test request processing with validation error."""
        invalid_request = {"query": "Test"}  # Missing required fields
        
        with pytest.raises(ValidationException):
            await rag_evaluator.process_request(invalid_request)
    
    @pytest.mark.asyncio
    async def test_process_request_partial_failure(self, rag_evaluator, sample_request_data):
        """Test request processing with some evaluation failures."""
        # Mock some evaluations to fail
        original_method = rag_evaluator.evaluate_faithfulness
        
        async def failing_evaluation(*args, **kwargs):
            raise Exception("Evaluation failed")
        
        rag_evaluator.evaluate_faithfulness = failing_evaluation
        
        result = await rag_evaluator.process_request(sample_request_data)
        
        # Should still return results with fallback scores
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert len(result["scores"]) == 5
        
        # Restore original method
        rag_evaluator.evaluate_faithfulness = original_method
    
    def test_generate_evaluation_summary(self, rag_evaluator):
        """Test evaluation summary generation."""
        scores = [
            EvaluationScore(criterion="faithfulness", score=4, justification="Good", examples=[], suggestions=[]),
            EvaluationScore(criterion="relevance", score=3, justification="Adequate", examples=[], suggestions=[]),
            EvaluationScore(criterion="completeness", score=5, justification="Excellent", examples=[], suggestions=[])
        ]
        
        summary = rag_evaluator._generate_evaluation_summary(scores, 4.0)
        
        assert isinstance(summary, str)
        assert "4.0" in summary
        assert "Faithfulness: 4/5" in summary
        assert "Relevance: 3/5" in summary
        assert "Completeness: 5/5" in summary
    
    def test_extract_insights(self, rag_evaluator):
        """Test insights extraction from scores."""
        scores = [
            EvaluationScore(
                criterion="faithfulness", 
                score=5, 
                justification="Excellent faithfulness to context", 
                examples=[], 
                suggestions=["Keep up the good work"]
            ),
            EvaluationScore(
                criterion="relevance", 
                score=2, 
                justification="Poor relevance to query", 
                examples=[], 
                suggestions=["Focus more on the query", "Remove irrelevant content"]
            ),
            EvaluationScore(
                criterion="completeness", 
                score=3, 
                justification="Adequate completeness", 
                examples=[], 
                suggestions=["Add more details"]
            )
        ]
        
        strengths, weaknesses, recommendations = rag_evaluator._extract_insights(scores)
        
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)
        assert isinstance(recommendations, list)
        
        assert len(strengths) > 0
        assert len(weaknesses) > 0
        assert len(recommendations) > 0
        
        # Check that high scores become strengths
        assert any("faithfulness" in strength.lower() for strength in strengths)
        
        # Check that low scores become weaknesses
        assert any("relevance" in weakness.lower() for weakness in weaknesses)
    
    @pytest.mark.asyncio
    async def test_stream_response_success(self, rag_evaluator, sample_request_data):
        """Test successful streaming response."""
        chunks = []
        
        async for chunk in rag_evaluator.stream_response(sample_request_data):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        
        # Check that streaming includes expected content
        full_response = "".join(chunks)
        assert "RAG Response Evaluation Starting" in full_response
        assert "Overall Assessment" in full_response
        assert "Evaluation Complete" in full_response
    
    @pytest.mark.asyncio
    async def test_stream_response_validation_error(self, rag_evaluator):
        """Test streaming response with validation error."""
        invalid_request = {"query": "Test"}  # Missing required fields
        
        chunks = []
        async for chunk in rag_evaluator.stream_response(invalid_request):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert "Evaluation Failed" in full_response
    
    def test_get_agent_info(self, rag_evaluator):
        """Test agent info retrieval."""
        info = rag_evaluator.get_agent_info()
        
        assert isinstance(info, dict)
        assert info["agent_name"] == "RAG Evaluator"
        assert info["agent_type"] == "rag_evaluation"
        assert "capabilities" in info
        assert "evaluation_criteria" in info
        assert "scoring_scale" in info
        
        assert isinstance(info["capabilities"], list)
        assert len(info["capabilities"]) > 0
        
        assert isinstance(info["evaluation_criteria"], list)
        assert len(info["evaluation_criteria"]) == 5
        
        # Check that all criteria are included
        criteria_names = [criterion["name"] for criterion in info["evaluation_criteria"]]
        assert "Faithfulness" in criteria_names
        assert "Relevance" in criteria_names
        assert "Completeness" in criteria_names
        assert "Coherence" in criteria_names
        assert "Source Attribution" in criteria_names


class TestRAGEvaluatorIntegration:
    """Integration tests for RAG Evaluator Agent."""
    
    @pytest.fixture
    def real_evaluator(self):
        """Create real RAG Evaluator instance (requires API key)."""
        # This would require a real API key for integration testing
        # For now, we'll skip these tests unless API key is available
        pytest.skip("Integration tests require real API key")
    
    @pytest.mark.asyncio
    async def test_real_evaluation_flow(self, real_evaluator):
        """Test complete evaluation flow with real API."""
        request_data = {
            "query": "What are the main benefits of solar energy?",
            "response": "Solar energy provides clean, renewable power that reduces carbon emissions and can lower electricity costs over time.",
            "context": [
                "Solar energy is a renewable energy source that harnesses sunlight to generate electricity.",
                "Studies show solar power can reduce household carbon emissions by up to 90%.",
                "While initial installation costs are high, solar panels can reduce electricity bills significantly."
            ]
        }
        
        result = await real_evaluator.process_request(request_data)
        
        assert isinstance(result, dict)
        assert 1.0 <= result["overall_score"] <= 5.0
        assert len(result["scores"]) == 5
        
        # Verify all criteria were evaluated
        criteria_evaluated = [score["criterion"] for score in result["scores"]]
        expected_criteria = ["faithfulness", "relevance", "completeness", "coherence", "source_attribution"]
        
        for criterion in expected_criteria:
            assert criterion in criteria_evaluated


class TestRAGEvaluatorEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def rag_evaluator(self):
        """Create RAG Evaluator instance for edge case testing."""
        with patch('app.agents.rag_evaluator.AsyncGroq'):
            return RAGEvaluator(groq_api_key="test_key")
    
    def test_empty_response_evaluation(self, rag_evaluator):
        """Test evaluation with empty response."""
        request_data = {
            "query": "Test query",
            "response": "",
            "context": ["Test context"]
        }
        
        with pytest.raises(ValidationException):
            rag_evaluator.validate_request(request_data)
    
    def test_very_long_response_evaluation(self, rag_evaluator):
        """Test evaluation with very long response."""
        long_response = "A" * 15000  # Exceeds max length
        
        request_data = {
            "query": "Test query",
            "response": long_response,
            "context": ["Test context"]
        }
        
        with pytest.raises(ValidationException):
            rag_evaluator.validate_request(request_data)
    
    def test_single_context_document(self, rag_evaluator):
        """Test evaluation with single context document."""
        request_data = {
            "query": "Test query",
            "response": "Test response with sufficient length for validation",
            "context": ["Single context document with enough content for testing"]
        }
        
        result = rag_evaluator.validate_request(request_data)
        assert result is True
    
    def test_maximum_context_documents(self, rag_evaluator):
        """Test evaluation with maximum number of context documents."""
        request_data = {
            "query": "Test query",
            "response": "Test response with sufficient length for validation",
            "context": [f"Context document {i} with sufficient content" for i in range(20)]
        }
        
        result = rag_evaluator.validate_request(request_data)
        assert result is True
    
    def test_context_utilization_edge_cases(self, rag_evaluator):
        """Test context utilization calculation edge cases."""
        # Test with identical response and context
        response = "Solar energy is renewable and clean"
        context = ["Solar energy is renewable and clean"]
        
        utilization = rag_evaluator._calculate_context_utilization(response, context)
        assert utilization > 0.5  # Should be high overlap
        
        # Test with completely different response and context
        response = "Machine learning algorithms process data"
        context = ["Solar energy is renewable and clean"]
        
        utilization = rag_evaluator._calculate_context_utilization(response, context)
        assert utilization < 0.5  # Should be low overlap
    
    @pytest.mark.asyncio
    async def test_concurrent_evaluations(self, rag_evaluator):
        """Test concurrent evaluation requests."""
        request_data = {
            "query": "Test query",
            "response": "Test response with sufficient length for validation",
            "context": ["Test context document with sufficient content"]
        }
        
        # Mock successful AI responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 4,
            "justification": "Good response",
            "examples": ["Example"],
            "suggestions": ["Suggestion"]
        })
        
        with patch.object(rag_evaluator, 'groq_client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            
            # Run multiple evaluations concurrently
            tasks = [
                rag_evaluator.process_request(request_data)
                for _ in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            for result in results:
                assert isinstance(result, dict)
                assert "overall_score" in result