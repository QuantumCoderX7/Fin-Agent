"""
Stock Market Analyst Agent for comprehensive stock analysis and recommendations.

This module implements the Stock Market Analyst Agent that provides individual stock
analysis, multi-stock comparison, and investment recommendations using YFinance data
and AI-powered analysis.
"""

import asyncio
import json
import yfinance as yf
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
import pandas as pd
from groq import AsyncGroq

from app.agents.base_agent import BaseAgent
from app.utils.exceptions import (
    ValidationException, 
    DataSourceException, 
    AgentProcessingException
)
from app.models.requests import StockAnalysisRequest
from app.models.responses import (
    StockAnalysisResponse, 
    StockAnalysis, 
    StockMetrics,
    ResponseStatus
)


class StockAgent(BaseAgent):
    """
    Stock Market Analyst Agent for comprehensive equity analysis.
    
    This agent provides detailed stock analysis including financial metrics,
    recommendations, risk assessment, and comparative analysis between multiple stocks.
    """
    
    def __init__(self, groq_api_key: str, model_name: str = "qwen/qwen3-32b", **kwargs):
        """
        Initialize the Stock Market Analyst Agent.
        
        Args:
            groq_api_key: API key for Groq LLM service
            model_name: LLM model to use for analysis
            **kwargs: Additional configuration parameters
        """
        super().__init__(model_name, **kwargs)
        self.groq_client = AsyncGroq(api_key=groq_api_key)
        self.agent_name = "Stock Market Analyst"
        self.agent_type = "stock_analysis"
        
        # Default financial metrics to analyze
        self.default_metrics = [
            "current_price", "market_cap", "pe_ratio", "eps", "dividend_yield",
            "beta", "volume", "day_change", "year_high", "year_low"
        ]
        
        # Time period mappings for yfinance
        self.period_mapping = {
            "1d": "1d", "5d": "5d", "1m": "1mo", "3m": "3mo", 
            "6m": "6mo", "1y": "1y", "2y": "2y", "5y": "5y", "10y": "10y"
        }
    
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """
        Validate stock analysis request.
        
        Args:
            request: Request data to validate
            
        Returns:
            True if request is valid
            
        Raises:
            ValidationException: If validation fails
        """
        try:
            # Use Pydantic model for validation
            StockAnalysisRequest(**request)
            return True
        except Exception as e:
            raise ValidationException(
                field_name="request",
                message=f"Stock analysis request validation failed: {str(e)}",
                validation_errors={"error": str(e)}
            )
    
    async def get_stock_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """
        Fetch comprehensive stock data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol to fetch data for
            period: Time period for historical data
            
        Returns:
            Dictionary containing stock data and metrics
            
        Raises:
            DataSourceException: If data fetching fails
        """
        try:
            # Create yfinance ticker object
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get historical data
            yf_period = self.period_mapping.get(period, "1y")
            hist = ticker.history(period=yf_period)
            
            if hist.empty:
                raise DataSourceException(
                    source_name="Yahoo Finance",
                    message=f"No historical data available for symbol {symbol}"
                )
            
            # Calculate current metrics
            current_price = hist['Close'].iloc[-1] if not hist.empty else None
            day_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100) if len(hist) > 1 else None
            
            # Extract key metrics
            stock_data = {
                "symbol": symbol,
                "company_name": info.get("longName", symbol),
                "current_price": current_price,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "volume": hist['Volume'].iloc[-1] if not hist.empty else None,
                "avg_volume": info.get("averageVolume"),
                "day_change": day_change,
                "year_high": info.get("fiftyTwoWeekHigh"),
                "year_low": info.get("fiftyTwoWeekLow"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "recommendation": info.get("recommendationKey"),
                "target_price": info.get("targetMeanPrice"),
                "analyst_count": info.get("numberOfAnalystOpinions"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "price_to_book": info.get("priceToBook"),
                "historical_data": hist,
                "info": info
            }
            
            return stock_data
            
        except Exception as e:
            raise DataSourceException(
                source_name="Yahoo Finance",
                message=f"Failed to fetch data for symbol {symbol}: {str(e)}"
            )
    
    async def analyze_single_stock(self, symbol: str, stock_data: Dict[str, Any], analysis_type: str = "comprehensive") -> StockAnalysis:
        """
        Perform detailed analysis of a single stock.
        
        Args:
            symbol: Stock symbol
            stock_data: Stock data from Yahoo Finance
            analysis_type: Type of analysis to perform
            
        Returns:
            StockAnalysis object with detailed analysis
        """
        try:
            # Create stock metrics
            metrics = StockMetrics(
                symbol=symbol,
                current_price=stock_data.get("current_price"),
                market_cap=stock_data.get("market_cap"),
                pe_ratio=stock_data.get("pe_ratio"),
                eps=stock_data.get("eps"),
                dividend_yield=stock_data.get("dividend_yield"),
                beta=stock_data.get("beta"),
                volume=stock_data.get("volume"),
                day_change=stock_data.get("day_change"),
                year_high=stock_data.get("year_high"),
                year_low=stock_data.get("year_low")
            )
            
            # Prepare data for AI analysis
            analysis_prompt = self._create_analysis_prompt(stock_data, analysis_type)
            
            # Get AI analysis
            ai_response = await self._get_ai_analysis(analysis_prompt)
            
            # Parse AI response into structured format
            parsed_analysis = self._parse_ai_response(ai_response, stock_data)
            
            return StockAnalysis(
                symbol=symbol,
                company_name=stock_data.get("company_name", symbol),
                metrics=metrics,
                analysis_summary=parsed_analysis.get("summary", ""),
                recommendation=parsed_analysis.get("recommendation", "HOLD"),
                target_price=stock_data.get("target_price"),
                risk_level=parsed_analysis.get("risk_level", "MEDIUM"),
                strengths=parsed_analysis.get("strengths", []),
                weaknesses=parsed_analysis.get("weaknesses", []),
                catalysts=parsed_analysis.get("catalysts", [])
            )
            
        except Exception as e:
            raise AgentProcessingException(
                agent_name=self.agent_name,
                message=f"Failed to analyze stock {symbol}: {str(e)}",
                processing_stage="single_stock_analysis"
            )
    
    def _create_analysis_prompt(self, stock_data: Dict[str, Any], analysis_type: str) -> str:
        """Create analysis prompt for the AI model."""
        symbol = stock_data.get("symbol", "")
        company_name = stock_data.get("company_name", symbol)
        
        prompt = f"""
        As a professional stock market analyst, provide a comprehensive analysis of {company_name} ({symbol}).
        
        **Financial Metrics:**
        - Current Price: ${stock_data.get('current_price', 'N/A')}
        - Market Cap: ${stock_data.get('market_cap', 'N/A'):,} if stock_data.get('market_cap') else 'N/A'
        - P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
        - EPS: ${stock_data.get('eps', 'N/A')}
        - Dividend Yield: {stock_data.get('dividend_yield', 'N/A')}%
        - Beta: {stock_data.get('beta', 'N/A')}
        - 52-Week High: ${stock_data.get('year_high', 'N/A')}
        - 52-Week Low: ${stock_data.get('year_low', 'N/A')}
        - Sector: {stock_data.get('sector', 'N/A')}
        - Industry: {stock_data.get('industry', 'N/A')}
        
        **Analysis Requirements:**
        1. Provide a clear investment recommendation (BUY/HOLD/SELL)
        2. Assess risk level (LOW/MEDIUM/HIGH)
        3. Identify 3-5 key strengths
        4. Identify 3-5 key weaknesses or concerns
        5. List potential catalysts for price movement
        6. Provide a comprehensive summary
        
        **Format your response as JSON:**
        {{
            "summary": "Detailed analysis summary",
            "recommendation": "BUY/HOLD/SELL",
            "risk_level": "LOW/MEDIUM/HIGH",
            "strengths": ["strength1", "strength2", ...],
            "weaknesses": ["weakness1", "weakness2", ...],
            "catalysts": ["catalyst1", "catalyst2", ...]
        }}
        """
        
        return prompt
    
    async def _get_ai_analysis(self, prompt: str) -> str:
        """Get analysis from AI model."""
        try:
            response = await self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional stock market analyst with expertise in financial analysis and investment recommendations. Provide accurate, data-driven analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise AgentProcessingException(
                agent_name=self.agent_name,
                message=f"AI analysis failed: {str(e)}",
                processing_stage="ai_analysis"
            )
    
    def _parse_ai_response(self, ai_response: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        try:
            import json
            
            # Try to extract JSON from the response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed
            else:
                # Fallback parsing if JSON format is not found
                return {
                    "summary": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response,
                    "recommendation": "HOLD",
                    "risk_level": "MEDIUM",
                    "strengths": ["Analysis available in summary"],
                    "weaknesses": ["Detailed breakdown not available"],
                    "catalysts": ["Market conditions", "Company performance"]
                }
                
        except Exception:
            # Fallback if parsing fails
            return {
                "summary": "Analysis completed but formatting failed. Raw analysis available.",
                "recommendation": "HOLD",
                "risk_level": "MEDIUM",
                "strengths": ["Data available for review"],
                "weaknesses": ["Analysis parsing incomplete"],
                "catalysts": ["Market dynamics"]
            }
    
    async def compare_stocks(self, analyses: List[StockAnalysis]) -> str:
        """
        Generate comparative analysis between multiple stocks.
        
        Args:
            analyses: List of individual stock analyses
            
        Returns:
            Comparative analysis summary
        """
        if len(analyses) < 2:
            return "Comparative analysis requires at least 2 stocks."
        
        try:
            # Prepare comparison data
            comparison_data = []
            for analysis in analyses:
                comparison_data.append({
                    "symbol": analysis.symbol,
                    "company": analysis.company_name,
                    "recommendation": analysis.recommendation,
                    "risk_level": analysis.risk_level,
                    "current_price": analysis.metrics.current_price,
                    "pe_ratio": analysis.metrics.pe_ratio,
                    "market_cap": analysis.metrics.market_cap,
                    "strengths_count": len(analysis.strengths),
                    "weaknesses_count": len(analysis.weaknesses)
                })
            
            # Create comparison prompt
            prompt = f"""
            As a professional portfolio analyst, compare the following stocks and provide investment insights:
            
            {json.dumps(comparison_data, indent=2)}
            
            Provide a comparative analysis covering:
            1. Relative valuation comparison
            2. Risk-adjusted recommendations
            3. Portfolio allocation suggestions
            4. Sector/industry considerations
            5. Overall investment thesis for each stock
            
            Format as a professional investment report.
            """
            
            comparison_response = await self._get_ai_analysis(prompt)
            return comparison_response
            
        except Exception as e:
            return f"Comparative analysis failed: {str(e)}"
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process stock analysis request.
        
        Args:
            request: Stock analysis request data
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate request
            self.validate_request(request)
            
            # Parse request
            req = StockAnalysisRequest(**request)
            
            # Fetch stock data for all symbols
            stock_data_tasks = [
                self.get_stock_data(symbol, req.time_period) 
                for symbol in req.symbols
            ]
            stock_data_results = await asyncio.gather(*stock_data_tasks, return_exceptions=True)
            
            # Process successful data fetches
            analyses = []
            failed_symbols = []
            
            for i, result in enumerate(stock_data_results):
                if isinstance(result, Exception):
                    failed_symbols.append(req.symbols[i])
                    continue
                
                try:
                    analysis = await self.analyze_single_stock(
                        req.symbols[i], 
                        result, 
                        req.analysis_type
                    )
                    analyses.append(analysis)
                except Exception as e:
                    failed_symbols.append(req.symbols[i])
            
            if not analyses:
                raise AgentProcessingException(
                    agent_name=self.agent_name,
                    message="Failed to analyze any of the requested stocks",
                    processing_stage="stock_analysis"
                )
            
            # Generate comparative analysis if requested and multiple stocks
            comparison_summary = None
            if req.include_comparison and len(analyses) > 1:
                comparison_summary = await self.compare_stocks(analyses)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create response
            response = StockAnalysisResponse(
                status=ResponseStatus.PARTIAL_SUCCESS if failed_symbols else ResponseStatus.SUCCESS,
                symbols=[analysis.symbol for analysis in analyses],
                analyses=analyses,
                comparison_summary=comparison_summary,
                market_sentiment="Analysis completed successfully",
                processing_time=processing_time,
                data_freshness=datetime.utcnow()
            )
            
            return response.dict()
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            if isinstance(e, (ValidationException, DataSourceException, AgentProcessingException)):
                raise e
            else:
                raise AgentProcessingException(
                    agent_name=self.agent_name,
                    message=f"Unexpected error during stock analysis: {str(e)}",
                    processing_stage="request_processing"
                )
    
    async def stream_response(self, request: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream stock analysis response in real-time.
        
        Args:
            request: Stock analysis request data
            
        Yields:
            String chunks of the streaming response
        """
        try:
            # Validate request
            self.validate_request(request)
            req = StockAnalysisRequest(**request)
            
            yield f"🔍 **Stock Market Analysis Starting**\n\n"
            yield f"**Symbols to analyze:** {', '.join(req.symbols)}\n"
            yield f"**Analysis type:** {req.analysis_type}\n\n"
            
            # Process each stock individually for streaming
            analyses = []
            
            for i, symbol in enumerate(req.symbols):
                yield f"## 📊 Analyzing {symbol}\n\n"
                
                try:
                    # Fetch stock data
                    yield f"⏳ Fetching market data for {symbol}...\n"
                    stock_data = await self.get_stock_data(symbol, req.time_period)
                    
                    yield f"✅ Data retrieved for {stock_data.get('company_name', symbol)}\n"
                    yield f"**Current Price:** ${stock_data.get('current_price', 'N/A')}\n"
                    yield f"**Market Cap:** ${stock_data.get('market_cap', 'N/A'):,}\n\n" if stock_data.get('market_cap') else "**Market Cap:** N/A\n\n"
                    
                    # Perform analysis
                    yield f"🤖 Generating AI analysis...\n"
                    analysis = await self.analyze_single_stock(symbol, stock_data, req.analysis_type)
                    analyses.append(analysis)
                    
                    # Stream analysis results
                    yield f"**Recommendation:** {analysis.recommendation}\n"
                    yield f"**Risk Level:** {analysis.risk_level}\n\n"
                    yield f"**Analysis Summary:**\n{analysis.analysis_summary}\n\n"
                    
                    if analysis.strengths:
                        yield f"**Key Strengths:**\n"
                        for strength in analysis.strengths:
                            yield f"• {strength}\n"
                        yield "\n"
                    
                    if analysis.weaknesses:
                        yield f"**Key Concerns:**\n"
                        for weakness in analysis.weaknesses:
                            yield f"• {weakness}\n"
                        yield "\n"
                    
                    yield f"---\n\n"
                    
                except Exception as e:
                    yield f"❌ Failed to analyze {symbol}: {str(e)}\n\n"
            
            # Generate comparison if requested
            if req.include_comparison and len(analyses) > 1:
                yield f"## 📈 Comparative Analysis\n\n"
                yield f"⏳ Generating comparative insights...\n"
                
                try:
                    comparison = await self.compare_stocks(analyses)
                    yield f"{comparison}\n\n"
                except Exception as e:
                    yield f"❌ Comparative analysis failed: {str(e)}\n\n"
            
            yield f"✅ **Analysis Complete**\n"
            yield f"**Total stocks analyzed:** {len(analyses)}\n"
            yield f"**Timestamp:** {datetime.utcnow().isoformat()}\n"
            
        except Exception as e:
            yield f"❌ **Analysis Failed:** {str(e)}\n"
    
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
            "description": "Professional stock market analyst providing comprehensive equity analysis and investment recommendations",
            "capabilities": [
                "Individual stock analysis",
                "Multi-stock comparison",
                "Financial metrics calculation",
                "Investment recommendations",
                "Risk assessment",
                "Real-time streaming analysis",
                "Historical data analysis"
            ],
            "supported_models": ["qwen/qwen3-32b", "mixtral-8x7b-32768"],
            "tools": [
                "Yahoo Finance API",
                "Groq LLM",
                "Financial metrics calculation",
                "Comparative analysis"
            ],
            "data_sources": [
                "Yahoo Finance",
                "Real-time market data",
                "Historical price data",
                "Company fundamentals"
            ],
            "output_formats": [
                "Structured analysis reports",
                "Investment recommendations",
                "Comparative analysis",
                "Real-time streaming"
            ]
        }