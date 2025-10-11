"""Unit tests for stock agent response parsing."""

import pytest
from app.agents.stock_agent import StockAgent

def test_parse_full_response():
    """Test parsing a full StockAnalysisResponse JSON."""
    agent = StockAgent(groq_api_key="test")
    stock_data = {"symbol": "AAPL"}
    
    # Full response JSON (like the sample)
    full_response = '''
    {
        "status": "success",
        "symbols": ["AAPL"],
        "analyses": [{
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "analysis_summary": "Strong market position",
            "recommendation": "BUY",
            "risk_level": "MEDIUM",
            "strengths": ["Brand loyalty", "Innovation"],
            "weaknesses": ["Competition", "Regulation"],
            "catalysts": ["New products", "Services growth"]
        }]
    }
    '''
    
    result = agent._parse_ai_response(full_response, stock_data)
    assert result["summary"] == "Strong market position"
    assert result["recommendation"] == "BUY"
    assert result["risk_level"] == "MEDIUM"
    assert len(result["strengths"]) == 2
    assert len(result["weaknesses"]) == 2
    assert len(result["catalysts"]) == 2

def test_parse_per_stock_json():
    """Test parsing a single stock analysis JSON."""
    agent = StockAgent(groq_api_key="test")
    stock_data = {"symbol": "GOOGL"}
    
    # Per-stock JSON format
    per_stock = '''
    {
        "summary": "Market leader in search",
        "recommendation": "HOLD",
        "risk_level": "LOW",
        "strengths": ["Search dominance"],
        "weaknesses": ["Regulatory risk"],
        "catalysts": ["AI growth"]
    }
    '''
    
    result = agent._parse_ai_response(per_stock, stock_data)
    assert result["summary"] == "Market leader in search"
    assert result["recommendation"] == "HOLD"
    assert result["risk_level"] == "LOW"
    assert len(result["strengths"]) == 1
    assert len(result["weaknesses"]) == 1
    assert len(result["catalysts"]) == 1

def test_parse_malformed_response():
    """Test parsing malformed or non-JSON responses."""
    agent = StockAgent(groq_api_key="test")
    stock_data = {"symbol": "MSFT"}
    
    # Plain text response
    text_response = "Microsoft shows strong fundamentals with consistent growth"
    result = agent._parse_ai_response(text_response, stock_data)
    assert text_response in result["summary"]
    assert result["recommendation"] == "HOLD"  # default
    assert result["risk_level"] == "MEDIUM"  # default
    assert len(result["strengths"]) > 0  # default list
    assert len(result["weaknesses"]) > 0  # default list
    assert len(result["catalysts"]) > 0  # default list

def test_parse_alternative_field_names():
    """Test parsing JSON with alternative field names."""
    agent = StockAgent(groq_api_key="test")
    stock_data = {"symbol": "TSLA"}
    
    # JSON with alternative field names
    alt_fields = '''
    {
        "analysis": "Strong growth potential",
        "strengths": ["Innovation", "Brand"],
        "risk_level": "HIGH"
    }
    '''
    
    result = agent._parse_ai_response(alt_fields, stock_data)
    assert result["summary"] == "Strong growth potential"
    assert result["recommendation"] == "HOLD"  # default when missing
    assert result["risk_level"] == "HIGH"
    assert len(result["strengths"]) == 2
    assert isinstance(result["weaknesses"], list)  # empty list when missing
    assert isinstance(result["catalysts"], list)  # empty list when missing

def test_parse_wrong_symbol_in_response():
    """Test handling when response JSON contains wrong symbol."""
    agent = StockAgent(groq_api_key="test")
    stock_data = {"symbol": "NVDA"}
    
    # Response with different symbol
    wrong_symbol = '''
    {
        "status": "success",
        "symbols": ["AMD"],
        "analyses": [{
            "symbol": "AMD",
            "analysis_summary": "Strong competitor",
            "recommendation": "BUY"
        }]
    }
    '''
    
    result = agent._parse_ai_response(wrong_symbol, stock_data)
    # Should still extract useful info even if symbol doesn't match
    assert "Strong competitor" in result["summary"]
    assert result["recommendation"] == "BUY"