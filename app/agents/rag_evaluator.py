"""
RAG Evaluator Agent for assessing the quality of AI-generated responses.

This module implements the RAG Evaluator Agent that provides comprehensive quality
assessment of RAG (Retrieval-Augmented Generation) responses across multiple criteria
including faithfulness, relevance, completeness, and coherence.
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from groq import AsyncGroq

from app.agents.base_agent import BaseAgent
from app.utils.exceptions import (
    ValidationException, 
    AgentProcessingException
)
from app.models.requests import RAGEvaluationRequest, EvaluationCriteria
from app.models.responses import (
    RAGEvaluationResponse, 
    EvaluationScore,
    ResponseStatus
)


class RAGEvaluator(BaseAgent):
    """
    RAG Evaluator Agent for comprehensive response quality assessment.
    
    This agent evaluates RAG-generated responses across multiple criteria:
    - Faithfulness: How well the response adheres to the provided context
    - Relevance: How relevant the response is to the original query
    - Completeness: How thoroughly the response addresses the query
    - Coherence: How well-structured and logical the response is
    - Source Attribution: How well sources are cited and attributed
    """
    
    def __init__(self, groq_api_key: str, model_name: str = "qwen/qwen3-32b", **kwargs):
        """
        Initialize the RAG Evaluator Agent.
        
        Args:
            groq_api_key: API key for Groq LLM service
            model_name: LLM model to use for evaluation
            **kwargs: Additional configuration parameters
        """
        super().__init__(model_name, **kwargs)
        self.groq_client = AsyncGroq(api_key=groq_api_key)
        self.agent_name = "RAG Evaluator"
        self.agent_type = "rag_evaluation"
        
        # Define evaluation criteria with descriptions
        self.evaluation_criteria = {
            EvaluationCriteria.FAITHFULNESS: {
                "name": "Faithfulness",
                "description": "How accurately the response reflects the information in the provided context",
                "weight": 0.25
            },
            EvaluationCriteria.RELEVANCE: {
                "name": "Relevance", 
                "description": "How well the response addresses the original query",
                "weight": 0.25
            },
            EvaluationCriteria.COMPLETENESS: {
                "name": "Completeness",
                "description": "How thoroughly the response covers all aspects of the query",
                "weight": 0.20
            },
            EvaluationCriteria.COHERENCE: {
                "name": "Coherence",
                "description": "How well-structured, logical, and easy to understand the response is",
                "weight": 0.15
            },
            EvaluationCriteria.SOURCE_ATTRIBUTION: {
                "name": "Source Attribution",
                "description": "How well sources are cited and attributed in the response",
                "weight": 0.15
            }
        }
        
        # Scoring guidelines
        self.scoring_guidelines = {
            5: "Excellent - Exceeds expectations in all aspects",
            4: "Good - Meets expectations with minor areas for improvement", 
            3: "Satisfactory - Adequate but with notable limitations",
            2: "Poor - Significant issues that impact quality",
            1: "Very Poor - Major problems that severely impact usability"
        }
    
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        Validate RAG evaluation request.
        
        Args:
            request: Request data to validate
            
        Returns:
            True if request is valid
            
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Use Pydantic model for validation
            RAGEvaluationRequest(**request)
            return True
        except Exception as e:
            raise ValidationException(
                field_name="request",
                message=f"RAG evaluation request validation failed: {str(e)}",
                validation_errors={"error": str(e)}
            )
    
    async def evaluate_faithfulness(self, query: str, response: str, context: List[str]) -> EvaluationScore:
        """
        Evaluate how faithfully the response adheres to the provided context.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents used for generation
            
        Returns:
            EvaluationScore for faithfulness
        """
        prompt = f"""
        As an expert evaluator, assess the FAITHFULNESS of this RAG response.
        
        **Original Query:** {query}
        
        **Response to Evaluate:** {response}
        
        **Context Documents:**
        {chr(10).join([f"Context {i+1}: {doc}" for i, doc in enumerate(context)])}
        
        **Evaluation Criteria for Faithfulness (Score 1-5):**
        - 5: Response is completely faithful to context, no contradictions or unsupported claims
        - 4: Response is mostly faithful with minor unsupported details
        - 3: Response is generally faithful but contains some unsupported information
        - 2: Response contains significant information not supported by context
        - 1: Response contradicts context or contains mostly unsupported claims
        
        **Provide your evaluation in this JSON format:**
        {{
            "score": [1-5],
            "justification": "Detailed explanation of the score",
            "examples": ["Specific example 1", "Specific example 2"],
            "suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"]
        }}
        """
        
        try:
            ai_response = await self._get_ai_evaluation(prompt)
            parsed_response = self._parse_evaluation_response(ai_response)
            
            return EvaluationScore(
                criterion="faithfulness",
                score=parsed_response.get("score", 3),
                justification=parsed_response.get("justification", "Evaluation completed"),
                examples=parsed_response.get("examples", []),
                suggestions=parsed_response.get("suggestions", [])
            )
            
        except Exception as e:
            return EvaluationScore(
                criterion="faithfulness",
                score=3,
                justification=f"Evaluation failed: {str(e)}",
                examples=[],
                suggestions=["Manual review recommended due to evaluation error"]
            )
    
    async def evaluate_relevance(self, query: str, response: str, context: List[str]) -> EvaluationScore:
        """
        Evaluate how relevant the response is to the original query.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents used for generation
            
        Returns:
            EvaluationScore for relevance
        """
        prompt = f"""
        As an expert evaluator, assess the RELEVANCE of this RAG response to the original query.
        
        **Original Query:** {query}
        
        **Response to Evaluate:** {response}
        
        **Evaluation Criteria for Relevance (Score 1-5):**
        - 5: Response directly and comprehensively addresses all aspects of the query
        - 4: Response addresses most aspects of the query with minor gaps
        - 3: Response addresses the main query but misses some important aspects
        - 2: Response partially addresses the query but includes irrelevant information
        - 1: Response is largely irrelevant to the query
        
        **Provide your evaluation in this JSON format:**
        {{
            "score": [1-5],
            "justification": "Detailed explanation of the score",
            "examples": ["Specific example 1", "Specific example 2"],
            "suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"]
        }}
        """
        
        try:
            ai_response = await self._get_ai_evaluation(prompt)
            parsed_response = self._parse_evaluation_response(ai_response)
            
            return EvaluationScore(
                criterion="relevance",
                score=parsed_response.get("score", 3),
                justification=parsed_response.get("justification", "Evaluation completed"),
                examples=parsed_response.get("examples", []),
                suggestions=parsed_response.get("suggestions", [])
            )
            
        except Exception as e:
            return EvaluationScore(
                criterion="relevance",
                score=3,
                justification=f"Evaluation failed: {str(e)}",
                examples=[],
                suggestions=["Manual review recommended due to evaluation error"]
            )
    
    async def evaluate_completeness(self, query: str, response: str, context: List[str]) -> EvaluationScore:
        """
        Evaluate how completely the response addresses all aspects of the query.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents used for generation
            
        Returns:
            EvaluationScore for completeness
        """
        prompt = f"""
        As an expert evaluator, assess the COMPLETENESS of this RAG response.
        
        **Original Query:** {query}
        
        **Response to Evaluate:** {response}
        
        **Context Available:**
        {chr(10).join([f"Context {i+1}: {doc[:200]}..." for i, doc in enumerate(context)])}
        
        **Evaluation Criteria for Completeness (Score 1-5):**
        - 5: Response thoroughly addresses all aspects of the query with comprehensive detail
        - 4: Response addresses most aspects with good detail, minor gaps
        - 3: Response covers main aspects but lacks depth or misses some components
        - 2: Response addresses some aspects but significant gaps remain
        - 1: Response is incomplete and fails to address major aspects of the query
        
        **Provide your evaluation in this JSON format:**
        {{
            "score": [1-5],
            "justification": "Detailed explanation of the score",
            "examples": ["Specific example 1", "Specific example 2"],
            "suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"]
        }}
        """
        
        try:
            ai_response = await self._get_ai_evaluation(prompt)
            parsed_response = self._parse_evaluation_response(ai_response)
            
            return EvaluationScore(
                criterion="completeness",
                score=parsed_response.get("score", 3),
                justification=parsed_response.get("justification", "Evaluation completed"),
                examples=parsed_response.get("examples", []),
                suggestions=parsed_response.get("suggestions", [])
            )
            
        except Exception as e:
            return EvaluationScore(
                criterion="completeness",
                score=3,
                justification=f"Evaluation failed: {str(e)}",
                examples=[],
                suggestions=["Manual review recommended due to evaluation error"]
            )
    
    async def evaluate_coherence(self, query: str, response: str, context: List[str]) -> EvaluationScore:
        """
        Evaluate how well-structured and coherent the response is.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents used for generation
            
        Returns:
            EvaluationScore for coherence
        """
        prompt = f"""
        As an expert evaluator, assess the COHERENCE of this RAG response.
        
        **Original Query:** {query}
        
        **Response to Evaluate:** {response}
        
        **Evaluation Criteria for Coherence (Score 1-5):**
        - 5: Response is exceptionally well-structured, logical flow, clear and easy to follow
        - 4: Response is well-organized with good logical flow and minor structural issues
        - 3: Response has adequate structure but some logical gaps or unclear transitions
        - 2: Response has poor structure with confusing organization and logical issues
        - 1: Response is incoherent, poorly structured, and difficult to follow
        
        **Consider these aspects:**
        - Logical flow and organization
        - Clear transitions between ideas
        - Consistent tone and style
        - Proper use of formatting and structure
        - Overall readability and clarity
        
        **Provide your evaluation in this JSON format:**
        {{
            "score": [1-5],
            "justification": "Detailed explanation of the score",
            "examples": ["Specific example 1", "Specific example 2"],
            "suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"]
        }}
        """
        
        try:
            ai_response = await self._get_ai_evaluation(prompt)
            parsed_response = self._parse_evaluation_response(ai_response)
            
            return EvaluationScore(
                criterion="coherence",
                score=parsed_response.get("score", 3),
                justification=parsed_response.get("justification", "Evaluation completed"),
                examples=parsed_response.get("examples", []),
                suggestions=parsed_response.get("suggestions", [])
            )
            
        except Exception as e:
            return EvaluationScore(
                criterion="coherence",
                score=3,
                justification=f"Evaluation failed: {str(e)}",
                examples=[],
                suggestions=["Manual review recommended due to evaluation error"]
            )
    
    async def evaluate_source_attribution(self, query: str, response: str, context: List[str]) -> EvaluationScore:
        """
        Evaluate how well sources are cited and attributed in the response.
        
        Args:
            query: Original query
            response: RAG response to evaluate
            context: Context documents used for generation
            
        Returns:
            EvaluationScore for source attribution
        """
        prompt = f"""
        As an expert evaluator, assess the SOURCE ATTRIBUTION of this RAG response.
        
        **Original Query:** {query}
        
        **Response to Evaluate:** {response}
        
        **Available Context Sources:** {len(context)} documents provided
        
        **Evaluation Criteria for Source Attribution (Score 1-5):**
        - 5: Excellent source attribution with clear, accurate citations for all claims
        - 4: Good source attribution with most claims properly cited
        - 3: Adequate attribution but some claims lack proper source references
        - 2: Poor attribution with many unsourced claims or unclear citations
        - 1: No or very poor source attribution, claims not backed by references
        
        **Consider these aspects:**
        - Are factual claims properly attributed to sources?
        - Are citations clear and specific?
        - Is it easy to trace information back to sources?
        - Are sources used appropriately and accurately?
        
        **Provide your evaluation in this JSON format:**
        {{
            "score": [1-5],
            "justification": "Detailed explanation of the score",
            "examples": ["Specific example 1", "Specific example 2"],
            "suggestions": ["Improvement suggestion 1", "Improvement suggestion 2"]
        }}
        """
        
        try:
            ai_response = await self._get_ai_evaluation(prompt)
            parsed_response = self._parse_evaluation_response(ai_response)
            
            return EvaluationScore(
                criterion="source_attribution",
                score=parsed_response.get("score", 3),
                justification=parsed_response.get("justification", "Evaluation completed"),
                examples=parsed_response.get("examples", []),
                suggestions=parsed_response.get("suggestions", [])
            )
            
        except Exception as e:
            return EvaluationScore(
                criterion="source_attribution",
                score=3,
                justification=f"Evaluation failed: {str(e)}",
                examples=[],
                suggestions=["Manual review recommended due to evaluation error"]
            )
    
    async def _get_ai_evaluation(self, prompt: str) -> str:
        """Get evaluation from AI model."""
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert RAG response evaluator with deep expertise in assessing the quality of AI-generated responses. Provide accurate, detailed, and constructive evaluations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for more consistent evaluations
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise AgentProcessingException(
                agent_name=self.agent_name,
                message=f"AI evaluation failed: {str(e)}",
                processing_stage="ai_evaluation"
            )
    
    def _parse_evaluation_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI evaluation response into structured format."""
        try:
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Validate score is within range
                if "score" in parsed:
                    score = parsed["score"]
                    if not isinstance(score, int) or score < 1 or score > 5:
                        parsed["score"] = 3  # Default to middle score
                
                return parsed
            else:
                # Fallback parsing if JSON format is not found
                return {
                    "score": 3,
                    "justification": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response,
                    "examples": ["Detailed evaluation available in justification"],
                    "suggestions": ["Review evaluation details for improvement recommendations"]
                }
                
        except Exception:
            # Fallback if parsing fails
            return {
                "score": 3,
                "justification": "Evaluation completed but response parsing failed",
                "examples": ["Manual review recommended"],
                "suggestions": ["Check evaluation format and retry"]
            }
    
    def _calculate_context_utilization(self, response: str, context: List[str]) -> float:
        """
        Calculate how well the context was utilized in the response.
        
        Args:
            response: The RAG response
            context: Context documents
            
        Returns:
            Utilization score between 0 and 1
        """
        if not context:
            return 0.0
        
        try:
            # Simple heuristic: count overlapping words/phrases
            response_words = set(re.findall(r'\b\w+\b', response.lower()))
            
            total_overlap = 0
            total_context_words = 0
            
            for doc in context:
                doc_words = set(re.findall(r'\b\w+\b', doc.lower()))
                total_context_words += len(doc_words)
                overlap = len(response_words.intersection(doc_words))
                total_overlap += overlap
            
            if total_context_words == 0:
                return 0.0
            
            # Normalize by context size and response size
            utilization = min(1.0, total_overlap / (len(response_words) + 1))
            return round(utilization, 3)
            
        except Exception:
            return 0.5  # Default middle value if calculation fails
    
    def _assess_factual_accuracy(self, response: str, context: List[str]) -> str:
        """
        Provide a basic assessment of factual accuracy.
        
        Args:
            response: The RAG response
            context: Context documents
            
        Returns:
            Factual accuracy assessment
        """
        try:
            # Simple heuristic based on context overlap and response structure
            context_utilization = self._calculate_context_utilization(response, context)
            
            if context_utilization > 0.7:
                return "High - Response closely follows provided context"
            elif context_utilization > 0.4:
                return "Medium - Response partially based on context with some additional information"
            else:
                return "Low - Response contains significant information not found in context"
                
        except Exception:
            return "Unable to assess - Manual review recommended"
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process RAG evaluation request.
        
        Args:
            request: RAG evaluation request data
            
        Returns:
            Dictionary containing evaluation results
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate request
            self.validate_request(request)
            
            # Parse request
            req = RAGEvaluationRequest(**request)
            
            # Determine which criteria to evaluate
            criteria_to_evaluate = req.evaluation_criteria or list(EvaluationCriteria)
            
            # Run evaluations for each criterion
            evaluation_tasks = []
            
            for criterion in criteria_to_evaluate:
                if criterion == EvaluationCriteria.FAITHFULNESS:
                    task = self.evaluate_faithfulness(req.query, req.response, req.context)
                elif criterion == EvaluationCriteria.RELEVANCE:
                    task = self.evaluate_relevance(req.query, req.response, req.context)
                elif criterion == EvaluationCriteria.COMPLETENESS:
                    task = self.evaluate_completeness(req.query, req.response, req.context)
                elif criterion == EvaluationCriteria.COHERENCE:
                    task = self.evaluate_coherence(req.query, req.response, req.context)
                elif criterion == EvaluationCriteria.SOURCE_ATTRIBUTION:
                    task = self.evaluate_source_attribution(req.query, req.response, req.context)
                else:
                    continue
                
                evaluation_tasks.append(task)
            
            # Execute all evaluations concurrently
            evaluation_results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
            
            # Process results
            scores = []
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for i, result in enumerate(evaluation_results):
                if isinstance(result, Exception):
                    # Create fallback score for failed evaluations
                    criterion_name = criteria_to_evaluate[i].value
                    fallback_score = EvaluationScore(
                        criterion=criterion_name,
                        score=3,
                        justification=f"Evaluation failed: {str(result)}",
                        examples=[],
                        suggestions=["Manual review recommended due to evaluation error"]
                    )
                    scores.append(fallback_score)
                else:
                    scores.append(result)
                
                # Calculate weighted score
                criterion = criteria_to_evaluate[i] if i < len(criteria_to_evaluate) else EvaluationCriteria.RELEVANCE
                weight = self.evaluation_criteria.get(criterion, {}).get("weight", 0.2)
                score_value = scores[-1].score
                
                total_weighted_score += score_value * weight
                total_weight += weight
            
            # Calculate overall score
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 3.0
            overall_score = round(overall_score, 2)
            
            # Generate summary and recommendations
            summary = self._generate_evaluation_summary(scores, overall_score)
            strengths, weaknesses, recommendations = self._extract_insights(scores)
            
            # Calculate additional metrics
            context_utilization = self._calculate_context_utilization(req.response, req.context)
            factual_accuracy = self._assess_factual_accuracy(req.response, req.context)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create response
            response = RAGEvaluationResponse(
                status=ResponseStatus.SUCCESS,
                overall_score=overall_score,
                scores=scores,
                summary=summary,
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                query=req.query,
                response_length=len(req.response),
                context_utilization=context_utilization,
                factual_accuracy=factual_accuracy,
                processing_time=processing_time
            )
            
            return response.dict()
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(e, (ValidationException, AgentProcessingException)):
                raise e
            else:
                raise AgentProcessingException(
                    agent_name=self.agent_name,
                    message=f"Unexpected error during RAG evaluation: {str(e)}",
                    processing_stage="request_processing"
                )
    
    def _generate_evaluation_summary(self, scores: List[EvaluationScore], overall_score: float) -> str:
        """Generate executive summary of the evaluation."""
        try:
            score_summaries = []
            for score in scores:
                score_summaries.append(f"{score.criterion.title()}: {score.score}/5")
            
            performance_level = "Excellent" if overall_score >= 4.5 else \
                              "Good" if overall_score >= 3.5 else \
                              "Satisfactory" if overall_score >= 2.5 else \
                              "Poor"
            
            summary = f"""
            **Overall Performance: {performance_level} ({overall_score}/5.0)**
            
            The RAG response achieved an overall quality score of {overall_score} out of 5.0 across all evaluation criteria.
            
            **Individual Scores:**
            {chr(10).join([f"• {summary}" for summary in score_summaries])}
            
            This evaluation provides a comprehensive assessment of response quality across multiple dimensions
            to help identify strengths and areas for improvement.
            """
            
            return summary.strip()
            
        except Exception:
            return f"Evaluation completed with overall score of {overall_score}/5.0. Detailed analysis available in individual criterion scores."
    
    def _extract_insights(self, scores: List[EvaluationScore]) -> tuple:
        """Extract strengths, weaknesses, and recommendations from scores."""
        strengths = []
        weaknesses = []
        recommendations = []
        
        try:
            for score in scores:
                criterion_name = score.criterion.replace("_", " ").title()
                
                if score.score >= 4:
                    strengths.append(f"Strong {criterion_name.lower()} - {score.justification[:100]}...")
                elif score.score <= 2:
                    weaknesses.append(f"Weak {criterion_name.lower()} - {score.justification[:100]}...")
                
                # Add suggestions as recommendations
                if score.suggestions:
                    for suggestion in score.suggestions[:2]:  # Limit to 2 per criterion
                        recommendations.append(f"{criterion_name}: {suggestion}")
            
            # Ensure we have at least some content
            if not strengths:
                strengths = ["Evaluation completed successfully"]
            if not weaknesses:
                weaknesses = ["No major weaknesses identified"]
            if not recommendations:
                recommendations = ["Continue current approach", "Consider regular quality reviews"]
            
        except Exception:
            # Fallback content
            strengths = ["Evaluation completed"]
            weaknesses = ["Review individual scores for details"]
            recommendations = ["Manual review recommended for detailed insights"]
        
        return strengths, weaknesses, recommendations
    
    async def stream_response(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream RAG evaluation response in real-time.
        
        Args:
            request: RAG evaluation request data
            
        Yields:
            String chunks of the streaming response
        """
        try:
            # Validate request
            self.validate_request(request)
            req = RAGEvaluationRequest(**request)
            
            yield f"🔍 **RAG Response Evaluation Starting**\n\n"
            yield f"**Query:** {req.query[:100]}{'...' if len(req.query) > 100 else ''}\n"
            yield f"**Response Length:** {len(req.response)} characters\n"
            yield f"**Context Documents:** {len(req.context)}\n\n"
            
            # Determine criteria to evaluate
            criteria_to_evaluate = req.evaluation_criteria or list(EvaluationCriteria)
            yield f"**Evaluation Criteria:** {', '.join([c.value.replace('_', ' ').title() for c in criteria_to_evaluate])}\n\n"
            
            # Evaluate each criterion and stream results
            scores = []
            
            for criterion in criteria_to_evaluate:
                criterion_name = criterion.value.replace("_", " ").title()
                yield f"## 📊 Evaluating {criterion_name}\n\n"
                yield f"⏳ Analyzing {criterion_name.lower()}...\n"
                
                try:
                    if criterion == EvaluationCriteria.FAITHFULNESS:
                        score = await self.evaluate_faithfulness(req.query, req.response, req.context)
                    elif criterion == EvaluationCriteria.RELEVANCE:
                        score = await self.evaluate_relevance(req.query, req.response, req.context)
                    elif criterion == EvaluationCriteria.COMPLETENESS:
                        score = await self.evaluate_completeness(req.query, req.response, req.context)
                    elif criterion == EvaluationCriteria.COHERENCE:
                        score = await self.evaluate_coherence(req.query, req.response, req.context)
                    elif criterion == EvaluationCriteria.SOURCE_ATTRIBUTION:
                        score = await self.evaluate_source_attribution(req.query, req.response, req.context)
                    else:
                        continue
                    
                    scores.append(score)
                    
                    # Stream results
                    yield f"✅ **Score: {score.score}/5**\n"
                    yield f"**Assessment:** {score.justification}\n\n"
                    
                    if score.examples:
                        yield f"**Examples:**\n"
                        for example in score.examples[:2]:  # Limit examples
                            yield f"• {example}\n"
                        yield "\n"
                    
                    if score.suggestions:
                        yield f"**Suggestions:**\n"
                        for suggestion in score.suggestions[:2]:  # Limit suggestions
                            yield f"• {suggestion}\n"
                        yield "\n"
                    
                    yield f"---\n\n"
                    
                except Exception as e:
                    yield f"❌ Failed to evaluate {criterion_name}: {str(e)}\n\n"
                    # Add fallback score
                    fallback_score = EvaluationScore(
                        criterion=criterion.value,
                        score=3,
                        justification=f"Evaluation failed: {str(e)}",
                        examples=[],
                        suggestions=["Manual review recommended"]
                    )
                    scores.append(fallback_score)
            
            # Calculate and stream overall results
            if scores:
                yield f"## 📈 Overall Assessment\n\n"
                
                # Calculate overall score
                total_weighted_score = 0.0
                total_weight = 0.0
                
                for i, score in enumerate(scores):
                    criterion = criteria_to_evaluate[i] if i < len(criteria_to_evaluate) else EvaluationCriteria.RELEVANCE
                    weight = self.evaluation_criteria.get(criterion, {}).get("weight", 0.2)
                    total_weighted_score += score.score * weight
                    total_weight += weight
                
                overall_score = total_weighted_score / total_weight if total_weight > 0 else 3.0
                overall_score = round(overall_score, 2)
                
                performance_level = "Excellent" if overall_score >= 4.5 else \
                                  "Good" if overall_score >= 3.5 else \
                                  "Satisfactory" if overall_score >= 2.5 else \
                                  "Poor"
                
                yield f"**Overall Score: {overall_score}/5.0 ({performance_level})**\n\n"
                
                # Stream individual scores summary
                yield f"**Individual Scores:**\n"
                for score in scores:
                    criterion_name = score.criterion.replace("_", " ").title()
                    yield f"• {criterion_name}: {score.score}/5\n"
                yield "\n"
                
                # Additional metrics
                context_utilization = self._calculate_context_utilization(req.response, req.context)
                yield f"**Context Utilization:** {context_utilization:.1%}\n"
                
                factual_accuracy = self._assess_factual_accuracy(req.response, req.context)
                yield f"**Factual Accuracy:** {factual_accuracy}\n\n"
            
            yield f"✅ **Evaluation Complete**\n"
            yield f"**Timestamp:** {datetime.utcnow().isoformat()}\n"
            
        except Exception as e:
            yield f"❌ **Evaluation Failed:** {str(e)}\n"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent's capabilities.
        
        Returns:
            Dictionary containing agent metadata and capabilities
        """
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "version": "1.0.0",
            "description": "Professional RAG response evaluator providing comprehensive quality assessment across multiple criteria",
            "capabilities": [
                "Faithfulness evaluation",
                "Relevance assessment", 
                "Completeness analysis",
                "Coherence evaluation",
                "Source attribution assessment",
                "Overall quality scoring",
                "Detailed feedback and recommendations",
                "Real-time streaming evaluation"
            ],
            "supported_models": ["qwen/qwen3-32b", "mixtral-8x7b-32768"],
            "evaluation_criteria": [
                {
                    "name": criteria["name"],
                    "description": criteria["description"],
                    "weight": criteria["weight"]
                }
                for criteria in self.evaluation_criteria.values()
            ],
            "scoring_scale": self.scoring_guidelines,
            "output_formats": [
                "Structured evaluation reports",
                "Individual criterion scores",
                "Overall quality assessment",
                "Improvement recommendations",
                "Real-time streaming evaluation"
            ]
        }