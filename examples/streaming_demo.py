"""
Demonstration of streaming capabilities in the Financial AI Agents system.

This script shows how to use the streaming endpoints and demonstrates
the Server-Sent Events (SSE) functionality with progress tracking.
"""

import asyncio
import json
import time
from typing import AsyncGenerator

from app.api.streaming import (
    StreamEvent,
    StreamEventType,
    ProgressTracker,
    create_sse_stream,
    streaming_context,
    stream_with_progress
)


async def demo_basic_streaming():
    """Demonstrate basic streaming functionality."""
    print("=== Basic Streaming Demo ===")
    
    async def sample_generator():
        """Sample content generator."""
        yield "Starting financial analysis..."
        await asyncio.sleep(0.5)
        yield "Fetching market data..."
        await asyncio.sleep(0.5)
        yield "Processing indicators..."
        await asyncio.sleep(0.5)
        yield "Analysis complete!"
    
    print("Streaming content:")
    async for event in create_sse_stream(sample_generator()):
        # Parse the SSE event
        if event.startswith("data: "):
            try:
                event_data = json.loads(event[6:-2])
                event_type = event_data.get("type", "unknown")
                data = event_data.get("data", {})
                
                if event_type == "started":
                    print(f"🚀 Stream started: {data.get('message', '')}")
                elif event_type == "content":
                    print(f"📄 Content: {data.get('content', '')}")
                elif event_type == "completed":
                    print(f"✅ Stream completed: {data.get('message', '')}")
                else:
                    print(f"📡 {event_type}: {data}")
            except json.JSONDecodeError:
                print(f"Raw event: {event.strip()}")


async def demo_progress_tracking():
    """Demonstrate progress tracking functionality."""
    print("\n=== Progress Tracking Demo ===")
    
    # Create a progress tracker
    tracker = ProgressTracker(total_steps=5, operation_name="Stock Analysis")
    
    print("Progress updates:")
    
    # Simulate analysis steps
    steps = [
        "Initializing analysis...",
        "Fetching stock data...",
        "Calculating indicators...",
        "Analyzing trends...",
        "Generating report..."
    ]
    
    for step in steps:
        progress = tracker.update(step)
        print(f"📊 {progress['progress_percent']:5.1f}% - {step}")
        print(f"    Step {progress['current_step']}/{progress['total_steps']} | "
              f"Elapsed: {progress['elapsed_time']:.1f}s | "
              f"ETA: {progress['estimated_remaining']:.1f}s" if progress['estimated_remaining'] else "ETA: calculating...")
        await asyncio.sleep(0.3)
    
    final_progress = tracker.complete()
    print(f"🎉 {final_progress['progress_percent']}% - Operation completed!")


async def demo_streaming_context():
    """Demonstrate streaming context manager."""
    print("\n=== Streaming Context Demo ===")
    
    async with streaming_context("Market Research", 4) as tracker:
        print("Using streaming context manager:")
        
        # Simulate research steps
        research_steps = [
            "Searching financial news...",
            "Analyzing market sentiment...",
            "Processing economic indicators...",
            "Compiling research report..."
        ]
        
        for step in research_steps:
            progress = tracker.update(step)
            print(f"🔍 {progress['progress_percent']:5.1f}% - {step}")
            await asyncio.sleep(0.4)
    
    print("✅ Context automatically completed!")


async def demo_stream_with_progress():
    """Demonstrate stream_with_progress utility."""
    print("\n=== Stream with Progress Demo ===")
    
    async def analyze_portfolio(symbols):
        """Simulate portfolio analysis."""
        await asyncio.sleep(1)
        return {
            "symbols": symbols,
            "total_value": 150000,
            "daily_change": 2.5,
            "analysis": "Portfolio showing positive momentum"
        }
    
    print("Streaming portfolio analysis:")
    
    async for item in stream_with_progress(
        analyze_portfolio,
        "Portfolio Analysis",
        3,  # total steps
        ["AAPL", "GOOGL", "MSFT"]
    ):
        if "progress" in item:
            progress = item["progress"]
            print(f"📈 {progress['progress_percent']:5.1f}% - {progress.get('step_name', 'Processing...')}")
        elif "result" in item:
            result = item["result"]
            print(f"💰 Analysis Result:")
            print(f"    Symbols: {', '.join(result['symbols'])}")
            print(f"    Total Value: ${result['total_value']:,}")
            print(f"    Daily Change: {result['daily_change']:+.1f}%")
            print(f"    Analysis: {result['analysis']}")
        elif "error" in item:
            print(f"❌ Error: {item['error']}")


async def demo_error_handling():
    """Demonstrate error handling in streaming."""
    print("\n=== Error Handling Demo ===")
    
    async def error_generator():
        """Generator that produces an error."""
        yield "Starting process..."
        await asyncio.sleep(0.2)
        yield "Processing data..."
        await asyncio.sleep(0.2)
        raise ValueError("Simulated processing error")
    
    print("Streaming with error handling:")
    
    try:
        async for event in create_sse_stream(error_generator()):
            if event.startswith("data: "):
                try:
                    event_data = json.loads(event[6:-2])
                    event_type = event_data.get("type", "unknown")
                    data = event_data.get("data", {})
                    
                    if event_type == "content":
                        print(f"📄 {data.get('content', '')}")
                    elif event_type == "error":
                        print(f"❌ Error detected: {data.get('error', '')}")
                    elif event_type == "started":
                        print(f"🚀 {data.get('message', '')}")
                except json.JSONDecodeError:
                    pass
    except ValueError as e:
        print(f"🔧 Exception handled: {e}")


async def demo_concurrent_streams():
    """Demonstrate concurrent streaming operations."""
    print("\n=== Concurrent Streaming Demo ===")
    
    async def create_analysis_stream(name, duration):
        """Create a simulated analysis stream."""
        steps = 3
        for i in range(steps):
            yield f"{name}: Step {i+1}/{steps}"
            await asyncio.sleep(duration / steps)
        yield f"{name}: Complete!"
    
    # Create multiple concurrent streams
    streams = [
        create_analysis_stream("Research Agent", 1.0),
        create_analysis_stream("Stock Agent", 1.2),
        create_analysis_stream("Evaluation Agent", 0.8)
    ]
    
    print("Running concurrent analysis streams:")
    
    # Process streams concurrently
    async def process_stream(stream, name):
        async for content in stream:
            print(f"🔄 {content}")
    
    tasks = [
        process_stream(stream, f"Stream {i+1}")
        for i, stream in enumerate(streams)
    ]
    
    await asyncio.gather(*tasks)
    print("✅ All concurrent streams completed!")


async def main():
    """Run all streaming demonstrations."""
    print("🚀 Financial AI Agents - Streaming Capabilities Demo")
    print("=" * 60)
    
    try:
        await demo_basic_streaming()
        await demo_progress_tracking()
        await demo_streaming_context()
        await demo_stream_with_progress()
        await demo_error_handling()
        await demo_concurrent_streams()
        
        print("\n" + "=" * 60)
        print("✅ All streaming demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Server-Sent Events (SSE) formatting")
        print("• Real-time progress tracking")
        print("• Automatic connection management")
        print("• Error handling and recovery")
        print("• Concurrent streaming operations")
        print("• Context managers for cleanup")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())