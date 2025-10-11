"""
Sample data and fixtures for testing the Financial AI Agents system.

This module provides consistent test data across all test modules.
"""

from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any

# Sample API Keys for testing
TEST_API_KEYS = {
    "groq_api_key": "test-groq-key-12345",
    "phi_api_key": "test-phi-key-67890"
}

# Sample Research Data
SAMPLE_RESEARCH_TOPICS = [
    "Federal Reserve interest rate policy impact on markets",
    "Cryptocurrency regulation and institutional adoption",
    "ESG investing trends and sustainable finance growth",
    "Inflation hedging strategies for portfolio management",
    "Central bank digital currencies (CBDC) development"
]

SAMPLE_SEARCH_RESULTS = [
    {
        "title": "Federal Reserve Announces Policy Decision on Interest Rates",
        "href": "https://example.com/fed-policy-announcement",
        "body": "The Federal Reserve announced today that it will maintain current interest rates at 5.25-5.50% while continuing to monitor inflation indicators and employment data."
    },
    {
        "title": "Market Analysis: Fed Policy Impact on Financial Sectors",
        "href": "https://example.com/market-analysis-fed-impact",
        "body": "Financial markets showed mixed reactions to the Federal Reserve's latest policy statement, with banking stocks rising while growth stocks declined."
    },
    {
        "title": "Economic Outlook: Monetary Policy and Growth Projections",
        "href": "https://example.com/economic-outlook-monetary-policy",
        "body": "Economists project that current monetary policy stance will support gradual economic growth while maintaining price stability over the medium term."
    },
    {
        "title": "Global Central Bank Coordination on Interest Rate Policies",
        "href": "https://example.com/global-central-bank-coordination",
        "body": "Major central banks are coordinating their monetary policy approaches to address global economic challenges and maintain financial stability."
    },
    {
        "title": "Investment Strategy Adjustments Following Fed Decision",
        "href": "https://example.com/investment-strategy-fed-decision",
        "body": "Investment managers are adjusting portfolio allocations in response to the Federal Reserve's policy guidance and forward-looking statements."
    }
]

SAMPLE_ARTICLE_CONTENT = {
    "title": "Federal Reserve Policy Analysis: Navigating Economic Uncertainty",
    "text": """
    The Federal Reserve's recent policy decisions reflect a careful balance between supporting economic growth and controlling inflation. 
    Key factors influencing the decision include robust employment data, persistent inflation concerns, and global economic uncertainties.
    
    The central bank's dual mandate of price stability and full employment continues to guide policy decisions. Recent data shows 
    unemployment remains near historic lows while inflation has shown signs of moderation from peak levels.
    
    Looking ahead, the Fed faces challenges from geopolitical tensions, supply chain disruptions, and evolving labor market dynamics. 
    Policy makers emphasize data-dependent decision making and gradual adjustments to monetary policy stance.
    
    Market participants are closely monitoring Fed communications for signals about future policy direction. The central bank's 
    commitment to transparency and forward guidance helps anchor market expectations and reduce volatility.
    """,
    "authors": ["Dr. Sarah Johnson", "Michael Chen"],
    "publish_date": "2024-01-15",
    "url": "https://example.com/fed-policy-analysis-detailed"
}

# Sample Stock Data
SAMPLE_STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "JNJ", "V"]

def create_sample_stock_data(symbol: str = "AAPL") -> Dict[str, Any]:
    """Create sample stock data for testing."""
    # Generate sample historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create realistic price movement
    base_price = 150.0 if symbol == "AAPL" else 100.0
    prices = []
    current_price = base_price
    
    for i in range(len(dates)):
        # Add some random walk with slight upward trend
        change = (i * 0.02) + ((-1) ** i) * (i % 5) * 0.5
        current_price = base_price + change
        prices.append(current_price)
    
    hist_data = pd.DataFrame({
        'Open': [p * 0.99 for p in prices],
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Close': prices,
        'Volume': [1000000 + i * 1000 for i in range(len(dates))]
    }, index=dates)
    
    return {
        "symbol": symbol,
        "company_name": f"{symbol} Inc." if symbol == "AAPL" else f"{symbol} Corporation",
        "current_price": prices[-1],
        "market_cap": 2800000000000 if symbol == "AAPL" else 1500000000000,
        "pe_ratio": 28.5,
        "eps": 6.34,
        "dividend_yield": 0.52,
        "beta": 1.2,
        "volume": 45000000,
        "day_change": 1.5,
        "day_change_percent": 0.85,
        "year_high": max(prices),
        "year_low": min(prices),
        "sector": "Technology",
        "industry": "Consumer Electronics" if symbol == "AAPL" else "Software",
        "historical_data": hist_data,
        "info": {
            "longName": f"{symbol} Inc." if symbol == "AAPL" else f"{symbol} Corporation",
            "sector": "Technology",
            "industry": "Consumer Electronics" if symbol == "AAPL" else "Software",
            "marketCap": 2800000000000 if symbol == "AAPL" else 1500000000000,
            "trailingPE": 28.5,
            "forwardPE": 26.8,
            "dividendYield": 0.0052,
            "beta": 1.2,
            "52WeekHigh": max(prices),
            "52WeekLow": min(prices),
            "averageVolume": 50000000,
            "regularMarketPrice": prices[-1]
        }
    }

SAMPLE_STOCK_ANALYSIS_RESPONSE = {
    "summary": "Apple Inc. demonstrates strong fundamentals with consistent revenue growth and market leadership in consumer electronics.",
    "recommendation": "BUY",
    "risk_level": "MEDIUM",
    "strengths": [
        "Strong brand loyalty and ecosystem",
        "Consistent revenue growth and profitability",
        "Innovation pipeline and R&D investment",
        "Strong balance sheet and cash position"
    ],
    "weaknesses": [
        "High valuation multiples",
        "Dependence on iPhone revenue",
        "Regulatory scrutiny and antitrust concerns",
        "Market saturation in key segments"
    ],
    "catalysts": [
        "New product launches and innovation",
        "Services revenue expansion",
        "Emerging market penetration",
        "AI and machine learning integration"
    ]
}

# Sample RAG Evaluation Data
SAMPLE_RAG_QUERIES = [
    "What are the main benefits of renewable energy investments?",
    "How does inflation impact bond portfolio performance?",
    "What factors drive cryptocurrency price volatility?",
    "Explain the relationship between interest rates and stock valuations",
    "What are the key risks in emerging market investments?"
]

SAMPLE_RAG_RESPONSES = [
    """
    Renewable energy investments offer several key benefits including reduced carbon emissions, 
    energy independence, and long-term cost savings. Solar and wind power have become increasingly 
    cost-competitive with traditional fossil fuels, making them attractive investment opportunities.
    """,
    """
    Inflation significantly impacts bond portfolio performance through interest rate changes and 
    purchasing power erosion. When inflation rises, central banks typically increase interest rates, 
    which causes existing bond prices to decline. Additionally, fixed-rate bonds lose purchasing 
    power over time in inflationary environments.
    """,
    """
    Cryptocurrency price volatility is driven by multiple factors including regulatory developments, 
    institutional adoption, market sentiment, technological changes, and macroeconomic conditions. 
    The relatively small market size and speculative nature of crypto markets amplify price movements.
    """
]

SAMPLE_RAG_CONTEXT = [
    [
        "Renewable energy sources like solar and wind have seen dramatic cost reductions in recent years.",
        "Studies show that renewable energy can reduce carbon emissions by up to 80% compared to fossil fuels.",
        "Energy independence is a key benefit of renewable energy adoption for many countries."
    ],
    [
        "Bond prices move inversely to interest rate changes due to fixed coupon payments.",
        "Inflation erodes the purchasing power of fixed-income investments over time.",
        "Central banks use interest rate policy to control inflation and economic growth."
    ],
    [
        "Cryptocurrency markets are highly speculative and driven by sentiment.",
        "Regulatory announcements can cause significant price movements in crypto assets.",
        "Institutional adoption has increased but remains limited compared to traditional assets."
    ]
]

# Sample AI Response Templates
SAMPLE_AI_RESPONSES = {
    "research_analysis": """
    # Federal Reserve Policy Analysis: Navigating Economic Uncertainty
    
    ## Executive Summary
    The Federal Reserve maintains a cautious approach to monetary policy amid mixed economic signals. 
    Current interest rates remain at 5.25-5.50% as policymakers balance growth support with inflation control.
    
    ## Analysis
    Recent economic data presents a complex picture with robust employment figures contrasting with 
    persistent inflation concerns. The Fed's data-dependent approach reflects uncertainty about 
    economic trajectory and optimal policy stance.
    
    Key factors influencing policy decisions include:
    - Employment data showing continued strength
    - Inflation metrics indicating gradual moderation
    - Global economic uncertainties and geopolitical risks
    - Financial market stability considerations
    
    ## Future Outlook
    Looking ahead, the Federal Reserve is likely to maintain current policy stance while closely 
    monitoring economic indicators. Gradual policy adjustments may be warranted based on data evolution 
    and achievement of dual mandate objectives.
    """,
    
    "stock_analysis": """
    {
        "summary": "Apple Inc. shows strong fundamentals with solid revenue growth and market position in consumer electronics.",
        "recommendation": "BUY",
        "risk_level": "MEDIUM",
        "strengths": [
            "Strong brand loyalty and ecosystem integration",
            "Consistent financial performance and profitability",
            "Innovation pipeline and R&D capabilities",
            "Strong balance sheet and cash generation"
        ],
        "weaknesses": [
            "High valuation multiples relative to peers",
            "Dependence on iPhone for majority of revenue",
            "Regulatory scrutiny and potential antitrust issues",
            "Market saturation in developed countries"
        ],
        "catalysts": [
            "New product launches and technological innovation",
            "Services business expansion and growth",
            "Emerging market penetration opportunities",
            "AI and machine learning integration across products"
        ]
    }
    """,
    
    "rag_evaluation": """
    {
        "score": 4,
        "justification": "The response demonstrates good faithfulness to the provided context with accurate information and relevant details. Minor improvements could be made in completeness and source attribution.",
        "examples": [
            "Correctly cites cost reductions in renewable energy",
            "Accurately mentions carbon emission reduction statistics",
            "Properly references energy independence benefits"
        ],
        "suggestions": [
            "Include more specific data points and statistics",
            "Add explicit source attribution for claims",
            "Expand on economic implications and investment considerations"
        ]
    }
    """
}

# Test Configuration
TEST_CONFIG = {
    "api_timeout": 30,
    "max_retries": 3,
    "batch_size": 10,
    "concurrent_requests": 5,
    "test_data_size": 100
}

# Performance Test Data
PERFORMANCE_TEST_REQUESTS = {
    "research_requests": [
        {"topic": f"Market analysis topic {i}", "sources_limit": 5}
        for i in range(50)
    ],
    "stock_requests": [
        {"symbols": [symbol], "analysis_type": "comprehensive"}
        for symbol in SAMPLE_STOCK_SYMBOLS * 5
    ],
    "evaluation_requests": [
        {
            "query": query,
            "response": response,
            "context": context
        }
        for query, response, context in zip(
            SAMPLE_RAG_QUERIES * 10,
            SAMPLE_RAG_RESPONSES * 17,  # Slightly different multiplier for variety
            SAMPLE_RAG_CONTEXT * 17
        )
    ]
}

def get_sample_data(data_type: str, count: int = 1) -> Any:
    """Get sample data of specified type and count."""
    if data_type == "research_topics":
        return SAMPLE_RESEARCH_TOPICS[:count]
    elif data_type == "stock_symbols":
        return SAMPLE_STOCK_SYMBOLS[:count]
    elif data_type == "rag_queries":
        return SAMPLE_RAG_QUERIES[:count]
    elif data_type == "search_results":
        return SAMPLE_SEARCH_RESULTS[:count]
    else:
        raise ValueError(f"Unknown data type: {data_type}")

def create_test_environment():
    """Create a complete test environment with all necessary data."""
    return {
        "api_keys": TEST_API_KEYS,
        "research_data": {
            "topics": SAMPLE_RESEARCH_TOPICS,
            "search_results": SAMPLE_SEARCH_RESULTS,
            "article_content": SAMPLE_ARTICLE_CONTENT
        },
        "stock_data": {
            "symbols": SAMPLE_STOCK_SYMBOLS,
            "sample_data": create_sample_stock_data(),
            "analysis_response": SAMPLE_STOCK_ANALYSIS_RESPONSE
        },
        "rag_data": {
            "queries": SAMPLE_RAG_QUERIES,
            "responses": SAMPLE_RAG_RESPONSES,
            "context": SAMPLE_RAG_CONTEXT
        },
        "ai_responses": SAMPLE_AI_RESPONSES,
        "config": TEST_CONFIG
    }