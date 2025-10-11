"""
Example client for consuming streaming endpoints from the Financial AI Agents API.

This script demonstrates how to connect to and consume Server-Sent Events (SSE)
from the streaming endpoints.
"""

import asyncio
import json
import httpx
from typing import AsyncGenerator


class StreamingClient:
    """Client for consuming streaming endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def stream_research_analysis(
        self, 
        topic: str, 
        sources_limit: int = 5
    ) -> AsyncGenerator[dict, None]:
        """
        Stream research analysis results.
        
        Args:
            topic: Research topic
            sources_limit: Number of sources to search
            
        Yields:
            Parsed streaming events
        """
        request_data = {
            "topic": topic,
            "sources_limit": sources_limit,
            "include_outlook": True
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/research/stream",
            json=request_data,
            headers={"Accept": "text/event-stream"}
        ) as response:
            
            if response.status_code != 200:
                raise Exception(f"Request failed: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        continue
    
    async def stream_stock_analysis(
        self, 
        symbols: list, 
        analysis_type: str = "comprehensive"
    ) -> AsyncGenerator[dict, None]:
        """
        Stream stock analysis results.
        
        Args:
            symbols: List of stock symbols
            analysis_type: Type of analysis
            
        Yields:
            Parsed streaming events
        """
        request_data = {
            "symbols": symbols,
            "analysis_type": analysis_type,
            "include_comparison": len(symbols) > 1
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/stocks/stream",
            json=request_data,
            headers={"Accept": "text/event-stream"}
        ) as response:
            
            if response.status_code != 200:
                raise Exception(f"Request failed: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        continue
    
    async def stream_evaluation_assessment(
        self, 
        query: str, 
        response: str, 
        context: list
    ) -> AsyncGenerator[dict, None]:
        """
        Stream RAG evaluation results.
        
        Args:
            query: Original query
            response: Response to evaluate
            context: Context documents
            
        Yields:
            Parsed streaming events
        """
        request_data = {
            "query": query,
            "response": response,
            "context": context
        }
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/evaluation/stream",
            json=request_data,
            headers={"Accept": "text/event-stream"}
        ) as response:
            
            if response.status_code != 200:
                raise Exception(f"Request failed: {response.status_code}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event_data = json.loads(line[6:])
                        yield event_data
                    except json.JSONDecodeError:
                        continue
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def demo_research_streaming():
    """Demonstrate research streaming."""
    print("=== Research Analysis Streaming Demo ===")
    
    client = StreamingClient()
    
    try:
        print("🔍 Starting research analysis stream...")
        
        async for event in client.stream_research_analysis(
            topic="AI impact on financial markets",
            sources_limit=3
        ):
            event_type = event.get("type", "unknown")
            data = event.get("data", {})
            
            if event_type == "started":
                print(f"🚀 {data.get('message', 'Stream started')}")
            elif event_type == "progress":
                progress = data
                print(f"📊 {progress.get('progress_percent', 0):.1f}% - {progress.get('step_name', 'Processing...')}")
            elif event_type == "content":
                content = data.get("content", "")
                if content:
                    print(f"📄 {content[:100]}{'...' if len(content) > 100 else ''}")
            elif event_type == "completed":
                print(f"✅ {data.get('message', 'Stream completed')}")
                break
            elif event_type == "error":
                print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}")
                break
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    finally:
        await client.close()


async def demo_stock_streaming():
    """Demonstrate stock analysis streaming."""
    print("\n=== Stock Analysis Streaming Demo ===")
    
    client = StreamingClient()
    
    try:
        print("📈 Starting stock analysis stream...")
        
        async for event in client.stream_stock_analysis(
            symbols=["AAPL", "GOOGL"],
            analysis_type="comprehensive"
        ):
            event_type = event.get("type", "unknown")
            data = event.get("data", {})
            
            if event_type == "started":
                print(f"🚀 {data.get('message', 'Stream started')}")
            elif event_type == "progress":
                progress = data
                print(f"📊 {progress.get('progress_percent', 0):.1f}% - {progress.get('step_name', 'Processing...')}")
            elif event_type == "content":
                content = data.get("content", "")
                if content:
                    print(f"📄 {content[:100]}{'...' if len(content) > 100 else ''}")
            elif event_type == "completed":
                print(f"✅ {data.get('message', 'Stream completed')}")
                break
            elif event_type == "error":
                print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}")
                break
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    finally:
        await client.close()


async def demo_evaluation_streaming():
    """Demonstrate evaluation streaming."""
    print("\n=== RAG Evaluation Streaming Demo ===")
    
    client = StreamingClient()
    
    try:
        print("🔍 Starting evaluation stream...")
        
        async for event in client.stream_evaluation_assessment(
            query="What is the current state of the stock market?",
            response="The stock market is currently experiencing volatility due to economic uncertainty...",
            context=["Market data shows mixed signals...", "Economic indicators suggest..."]
        ):
            event_type = event.get("type", "unknown")
            data = event.get("data", {})
            
            if event_type == "started":
                print(f"🚀 {data.get('message', 'Stream started')}")
            elif event_type == "progress":
                progress = data
                print(f"📊 {progress.get('progress_percent', 0):.1f}% - {progress.get('step_name', 'Processing...')}")
            elif event_type == "status":
                print(f"ℹ️  {data}")
            elif event_type == "content":
                if "evaluation_result" in data:
                    result = data["evaluation_result"]
                    print(f"📋 Overall Score: {result.get('overall_score', 'N/A')}")
                elif "recommendations" in data:
                    recommendations = data["recommendations"]
                    print(f"💡 Recommendations: {len(recommendations)} items")
            elif event_type == "completed":
                print(f"✅ {data.get('message', 'Stream completed')}")
                break
            elif event_type == "error":
                print(f"❌ Error: {data.get('error', {}).get('message', 'Unknown error')}")
                break
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    finally:
        await client.close()


async def demo_concurrent_streaming():
    """Demonstrate concurrent streaming requests."""
    print("\n=== Concurrent Streaming Demo ===")
    
    async def run_research_stream():
        client = StreamingClient()
        try:
            print("🔍 Research stream starting...")
            count = 0
            async for event in client.stream_research_analysis("Market trends"):
                count += 1
                if count >= 5:  # Limit output
                    break
            print("🔍 Research stream completed")
        except Exception as e:
            print(f"🔍 Research stream error: {e}")
        finally:
            await client.close()
    
    async def run_stock_stream():
        client = StreamingClient()
        try:
            print("📈 Stock stream starting...")
            count = 0
            async for event in client.stream_stock_analysis(["AAPL"]):
                count += 1
                if count >= 5:  # Limit output
                    break
            print("📈 Stock stream completed")
        except Exception as e:
            print(f"📈 Stock stream error: {e}")
        finally:
            await client.close()
    
    # Run streams concurrently
    await asyncio.gather(
        run_research_stream(),
        run_stock_stream(),
        return_exceptions=True
    )


async def main():
    """Run streaming client demonstrations."""
    print("🚀 Financial AI Agents - Streaming Client Demo")
    print("=" * 60)
    print("Note: This demo requires the API server to be running on localhost:8000")
    print("Start the server with: python -m uvicorn app.main:app --reload")
    print("=" * 60)
    
    # Note: These demos will fail if the server is not running
    # They are provided as examples of how to consume the streaming endpoints
    
    try:
        await demo_research_streaming()
        await demo_stock_streaming()
        await demo_evaluation_streaming()
        await demo_concurrent_streaming()
        
        print("\n" + "=" * 60)
        print("✅ All streaming client demos completed!")
        print("\nClient Features Demonstrated:")
        print("• Server-Sent Events consumption")
        print("• Real-time progress monitoring")
        print("• Error handling and recovery")
        print("• Concurrent streaming requests")
        print("• Proper connection cleanup")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure the API server is running on localhost:8000")


if __name__ == "__main__":
    asyncio.run(main())