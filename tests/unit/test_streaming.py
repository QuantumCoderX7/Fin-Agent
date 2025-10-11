"""
Unit tests for streaming functionality.

This module tests the Server-Sent Events (SSE) streaming capabilities,
progress tracking, and connection management.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.streaming import (
    StreamEvent,
    StreamEventType,
    StreamManager,
    ProgressTracker,
    create_sse_stream,
    create_streaming_response,
    streaming_context,
    stream_with_progress,
    get_streaming_stats
)


class TestStreamEvent:
    """Test StreamEvent functionality."""
    
    def test_stream_event_creation(self):
        """Test creating a stream event."""
        event = StreamEvent(
            event_type=StreamEventType.CONTENT,
            data={"message": "test content"}
        )
        
        assert event.event_type == StreamEventType.CONTENT
        assert event.data == {"message": "test content"}
        assert event.timestamp is not None
        assert event.correlation_id is not None
    
    def test_stream_event_sse_format(self):
        """Test SSE formatting of stream events."""
        event = StreamEvent(
            event_type=StreamEventType.PROGRESS,
            data={"progress": 50, "message": "halfway done"},
            correlation_id="test-123"
        )
        
        sse_output = event.to_sse_format()
        
        assert sse_output.startswith("data: ")
        assert sse_output.endswith("\n\n")
        
        # Parse the JSON data
        json_data = sse_output[6:-2]  # Remove "data: " and "\n\n"
        parsed = json.loads(json_data)
        
        assert parsed["type"] == "progress"
        assert parsed["data"]["progress"] == 50
        assert parsed["correlation_id"] == "test-123"
    
    def test_stream_event_types(self):
        """Test all stream event types."""
        event_types = [
            StreamEventType.STARTED,
            StreamEventType.PROGRESS,
            StreamEventType.CONTENT,
            StreamEventType.STATUS,
            StreamEventType.ERROR,
            StreamEventType.COMPLETED,
            StreamEventType.HEARTBEAT
        ]
        
        for event_type in event_types:
            event = StreamEvent(event_type=event_type, data={"test": True})
            sse_output = event.to_sse_format()
            
            json_data = sse_output[6:-2]
            parsed = json.loads(json_data)
            assert parsed["type"] == event_type.value


class TestStreamManager:
    """Test StreamManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = StreamManager()
    
    def test_register_stream(self):
        """Test registering a new stream."""
        stream_id = "test-stream-1"
        metadata = {"client": "test", "endpoint": "/test"}
        
        self.manager.register_stream(stream_id, metadata)
        
        assert stream_id in self.manager.active_streams
        assert self.manager.active_streams[stream_id]["metadata"] == metadata
        assert self.manager.active_streams[stream_id]["status"] == "active"
    
    def test_unregister_stream(self):
        """Test unregistering a stream."""
        stream_id = "test-stream-1"
        
        self.manager.register_stream(stream_id)
        assert stream_id in self.manager.active_streams
        
        self.manager.unregister_stream(stream_id)
        assert stream_id not in self.manager.active_streams
    
    def test_update_stream_activity(self):
        """Test updating stream activity."""
        stream_id = "test-stream-1"
        
        self.manager.register_stream(stream_id)
        original_time = self.manager.active_streams[stream_id]["last_activity"]
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        self.manager.update_stream_activity(stream_id)
        new_time = self.manager.active_streams[stream_id]["last_activity"]
        
        assert new_time > original_time
    
    def test_get_stream_info(self):
        """Test getting stream information."""
        stream_id = "test-stream-1"
        metadata = {"test": "data"}
        
        self.manager.register_stream(stream_id, metadata)
        info = self.manager.get_stream_info(stream_id)
        
        assert info is not None
        assert info["metadata"] == metadata
        assert "start_time" in info
        assert "last_activity" in info
    
    def test_get_active_streams_count(self):
        """Test getting active streams count."""
        assert self.manager.get_active_streams_count() == 0
        
        self.manager.register_stream("stream-1")
        assert self.manager.get_active_streams_count() == 1
        
        self.manager.register_stream("stream-2")
        assert self.manager.get_active_streams_count() == 2
        
        self.manager.unregister_stream("stream-1")
        assert self.manager.get_active_streams_count() == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_streams(self):
        """Test cleaning up stale streams."""
        # Register a stream and manually set old activity time
        stream_id = "stale-stream"
        self.manager.register_stream(stream_id)
        
        # Make it appear stale
        import time
        self.manager.active_streams[stream_id]["last_activity"] = time.time() - 400
        
        await self.manager.cleanup_stale_streams(max_age_seconds=300)
        
        assert stream_id not in self.manager.active_streams


class TestProgressTracker:
    """Test ProgressTracker functionality."""
    
    def test_progress_tracker_creation(self):
        """Test creating a progress tracker."""
        tracker = ProgressTracker(total_steps=10, operation_name="Test Operation")
        
        assert tracker.total_steps == 10
        assert tracker.current_step == 0
        assert tracker.operation_name == "Test Operation"
        assert tracker.start_time is not None
    
    def test_progress_update(self):
        """Test updating progress."""
        tracker = ProgressTracker(total_steps=4)
        
        # Initial state
        progress = tracker.update("Step 1")
        assert progress["current_step"] == 1
        assert progress["progress_percent"] == 25.0
        assert progress["step_name"] == "Step 1"
        assert not progress["is_complete"]
        
        # Update with increment
        progress = tracker.update("Step 2", increment=2)
        assert progress["current_step"] == 3
        assert progress["progress_percent"] == 75.0
        
        # Complete
        progress = tracker.update("Final Step")
        assert progress["current_step"] == 4
        assert progress["progress_percent"] == 100.0
        assert progress["is_complete"]
    
    def test_progress_completion(self):
        """Test marking progress as complete."""
        tracker = ProgressTracker(total_steps=5)
        
        # Partial progress
        tracker.update("Step 1")
        tracker.update("Step 2")
        assert tracker.current_step == 2
        
        # Force completion
        progress = tracker.complete()
        assert progress["current_step"] == tracker.total_steps
        assert progress["progress_percent"] == 100.0
        assert progress["is_complete"]
    
    def test_progress_time_estimation(self):
        """Test time estimation in progress tracking."""
        tracker = ProgressTracker(total_steps=4)
        
        # First update
        progress = tracker.update("Step 1")
        assert "elapsed_time" in progress
        assert "estimated_remaining" in progress
        
        # Second update should have better estimation
        import time
        time.sleep(0.01)  # Small delay
        progress = tracker.update("Step 2")
        assert progress["estimated_remaining"] is not None


@pytest.mark.asyncio
class TestSSEStream:
    """Test SSE stream creation and formatting."""
    
    async def test_create_sse_stream_basic(self):
        """Test basic SSE stream creation."""
        async def simple_generator():
            yield "Hello"
            yield "World"
        
        stream_id = "test-stream"
        events = []
        
        async for event in create_sse_stream(simple_generator(), stream_id):
            events.append(event)
        
        # Should have: started, content, content, completed
        assert len(events) >= 4
        
        # Parse first event (started)
        first_event_data = json.loads(events[0][6:-2])
        assert first_event_data["type"] == "started"
        assert first_event_data["data"]["stream_id"] == stream_id
    
    async def test_create_sse_stream_with_dict_content(self):
        """Test SSE stream with dictionary content."""
        async def dict_generator():
            yield {"progress": 50, "message": "halfway"}
            yield {"error": "something went wrong"}
            yield {"status": "recovering"}
        
        events = []
        async for event in create_sse_stream(dict_generator()):
            events.append(event)
        
        # Parse content events
        content_events = [e for e in events if '"type": "progress"' in e or '"type": "error"' in e or '"type": "status"' in e]
        assert len(content_events) == 3
    
    async def test_create_sse_stream_error_handling(self):
        """Test SSE stream error handling."""
        async def error_generator():
            yield "Good content"
            raise ValueError("Test error")
        
        events = []
        try:
            async for event in create_sse_stream(error_generator()):
                events.append(event)
        except ValueError:
            pass  # Expected
        
        # Should have started, content, and error events
        error_events = [e for e in events if '"type": "error"' in e]
        assert len(error_events) >= 1


@pytest.mark.asyncio
class TestStreamingContext:
    """Test streaming context manager."""
    
    async def test_streaming_context_basic(self):
        """Test basic streaming context usage."""
        async with streaming_context("Test Operation", 3) as tracker:
            assert tracker.operation_name == "Test Operation"
            assert tracker.total_steps == 3
            assert tracker.current_step == 0
    
    async def test_streaming_context_with_error(self):
        """Test streaming context with error handling."""
        try:
            async with streaming_context("Error Operation", 2) as tracker:
                tracker.update("Step 1")
                raise ValueError("Test error")
        except ValueError:
            pass  # Expected
        
        # Context should handle cleanup properly
        assert True  # If we get here, cleanup worked
    
    async def test_streaming_context_auto_completion(self):
        """Test automatic completion in streaming context."""
        async with streaming_context("Auto Complete", 3) as tracker:
            tracker.update("Step 1")
            # Don't complete manually
        
        # Should auto-complete
        assert tracker.current_step >= tracker.total_steps


@pytest.mark.asyncio
class TestStreamWithProgress:
    """Test stream_with_progress utility function."""
    
    async def test_stream_with_progress_sync_function(self):
        """Test streaming with synchronous function."""
        def sync_operation(x, y):
            return x + y
        
        results = []
        async for item in stream_with_progress(sync_operation, "Addition", 2, 5, 3):
            results.append(item)
        
        # Should have progress updates and final result
        progress_items = [r for r in results if "progress" in r]
        result_items = [r for r in results if "result" in r]
        
        assert len(progress_items) >= 2  # At least start and complete
        assert len(result_items) == 1
        assert result_items[0]["result"] == 8
    
    async def test_stream_with_progress_async_function(self):
        """Test streaming with asynchronous function."""
        async def async_operation(value):
            await asyncio.sleep(0.01)
            return value * 2
        
        results = []
        async for item in stream_with_progress(async_operation, "Multiplication", 2, 5):
            results.append(item)
        
        # Should have progress and result
        result_items = [r for r in results if "result" in r]
        assert len(result_items) == 1
        assert result_items[0]["result"] == 10
    
    async def test_stream_with_progress_error_handling(self):
        """Test error handling in stream_with_progress."""
        def error_operation():
            raise ValueError("Test error")
        
        results = []
        try:
            async for item in stream_with_progress(error_operation, "Error Op"):
                results.append(item)
        except ValueError:
            pass  # Expected
        
        # Should have error in results
        error_items = [r for r in results if "error" in r]
        assert len(error_items) >= 1


class TestStreamingStats:
    """Test streaming statistics functionality."""
    
    def test_get_streaming_stats_empty(self):
        """Test getting stats with no active streams."""
        # Clear any existing streams
        from app.api.streaming import stream_manager
        stream_manager.active_streams.clear()
        
        stats = get_streaming_stats()
        
        assert stats["active_streams"] == 0
        assert stats["stream_details"] == {}
    
    def test_get_streaming_stats_with_streams(self):
        """Test getting stats with active streams."""
        from app.api.streaming import stream_manager
        
        # Clear and add test streams
        stream_manager.active_streams.clear()
        stream_manager.register_stream("test-1", {"endpoint": "/test1"})
        stream_manager.register_stream("test-2", {"endpoint": "/test2"})
        
        stats = get_streaming_stats()
        
        assert stats["active_streams"] == 2
        assert "test-1" in stats["stream_details"]
        assert "test-2" in stats["stream_details"]
        assert "duration" in stats["stream_details"]["test-1"]
        assert "metadata" in stats["stream_details"]["test-1"]


@pytest.mark.asyncio
class TestStreamingResponse:
    """Test streaming response creation."""
    
    async def test_create_streaming_response(self):
        """Test creating a streaming response."""
        async def test_generator():
            yield "test content"
        
        response = create_streaming_response(test_generator())
        
        assert response.media_type == "text/event-stream"
        assert "Cache-Control" in response.headers
        assert response.headers["Cache-Control"] == "no-cache"
        assert "Connection" in response.headers
        assert response.headers["Connection"] == "keep-alive"
    
    async def test_streaming_response_with_custom_media_type(self):
        """Test streaming response with custom media type."""
        async def test_generator():
            yield {"data": "test"}
        
        response = create_streaming_response(test_generator(), media_type="application/json")
        
        assert response.media_type == "application/json"


if __name__ == "__main__":
    pytest.main([__file__])