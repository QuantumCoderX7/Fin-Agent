"""
Server-Sent Events (SSE) streaming utilities and middleware for real-time responses.

This module provides comprehensive streaming capabilities for the Financial AI Agents system,
including progress indicators, connection management, and proper SSE formatting.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import AsyncGenerator, Dict, Any, Optional, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class StreamEventType(Enum):
    """Types of streaming events."""
    STARTED = "started"
    PROGRESS = "progress"
    CONTENT = "content"
    STATUS = "status"
    ERROR = "error"
    COMPLETED = "completed"
    HEARTBEAT = "heartbeat"


@dataclass
class StreamEvent:
    """Represents a streaming event."""
    event_type: StreamEventType
    data: Any
    timestamp: float = None
    correlation_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
    
    def to_sse_format(self) -> str:
        """Convert event to Server-Sent Events format."""
        event_data = {
            "type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id
        }
        
        # Format as SSE
        sse_data = json.dumps(event_data, default=str)
        return f"data: {sse_data}\n\n"


class StreamManager:
    """Manages streaming connections and provides utilities for SSE."""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = 30  # seconds
    
    def register_stream(self, stream_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register a new streaming connection."""
        self.active_streams[stream_id] = {
            "start_time": time.time(),
            "last_activity": time.time(),
            "metadata": metadata or {},
            "status": "active"
        }
        logger.info(f"Registered stream {stream_id}")
    
    def unregister_stream(self, stream_id: str) -> None:
        """Unregister a streaming connection."""
        if stream_id in self.active_streams:
            duration = time.time() - self.active_streams[stream_id]["start_time"]
            logger.info(f"Unregistered stream {stream_id} after {duration:.2f}s")
            del self.active_streams[stream_id]
    
    def update_stream_activity(self, stream_id: str) -> None:
        """Update last activity timestamp for a stream."""
        if stream_id in self.active_streams:
            self.active_streams[stream_id]["last_activity"] = time.time()
    
    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stream."""
        return self.active_streams.get(stream_id)
    
    def get_active_streams_count(self) -> int:
        """Get count of active streams."""
        return len(self.active_streams)
    
    async def cleanup_stale_streams(self, max_age_seconds: int = 300) -> None:
        """Clean up streams that have been inactive for too long."""
        current_time = time.time()
        stale_streams = []
        
        for stream_id, info in self.active_streams.items():
            if current_time - info["last_activity"] > max_age_seconds:
                stale_streams.append(stream_id)
        
        for stream_id in stale_streams:
            logger.warning(f"Cleaning up stale stream {stream_id}")
            self.unregister_stream(stream_id)


# Global stream manager instance
stream_manager = StreamManager()


class StreamingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling streaming connections and cleanup."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Handle streaming requests with proper connection management."""
        # Check if this is a streaming endpoint
        is_streaming = (
            request.url.path.endswith("/stream") or 
            "stream" in request.url.path or
            request.headers.get("Accept") == "text/event-stream"
        )
        
        if is_streaming:
            # Generate stream ID
            stream_id = str(uuid.uuid4())
            request.state.stream_id = stream_id
            
            # Register stream
            stream_manager.register_stream(stream_id, {
                "path": request.url.path,
                "method": request.method,
                "client": str(request.client) if request.client else "unknown"
            })
            
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                logger.error(f"Streaming request failed for stream {stream_id}: {str(e)}")
                stream_manager.unregister_stream(stream_id)
                raise
            finally:
                # Cleanup will be handled by the stream generator
                pass
        else:
            return await call_next(request)


async def create_sse_stream(
    generator: AsyncGenerator[Any, None],
    stream_id: str = None,
    include_heartbeat: bool = True,
    heartbeat_interval: int = 30
) -> AsyncGenerator[str, None]:
    """
    Create a Server-Sent Events stream with proper formatting and connection management.
    
    Args:
        generator: Async generator that yields content
        stream_id: Optional stream ID for tracking
        include_heartbeat: Whether to include heartbeat events
        heartbeat_interval: Interval between heartbeat events in seconds
    
    Yields:
        Formatted SSE strings
    """
    if stream_id is None:
        stream_id = str(uuid.uuid4())
    
    try:
        # Send initial event
        start_event = StreamEvent(
            event_type=StreamEventType.STARTED,
            data={"message": "Stream started", "stream_id": stream_id}
        )
        yield start_event.to_sse_format()
        
        # Set up heartbeat task if enabled
        heartbeat_task = None
        if include_heartbeat:
            heartbeat_task = asyncio.create_task(
                _heartbeat_generator(stream_id, heartbeat_interval)
            )
        
        # Process main content
        try:
            async for content in generator:
                # Update stream activity
                stream_manager.update_stream_activity(stream_id)
                
                # Determine event type based on content
                if isinstance(content, dict):
                    if "error" in content:
                        event_type = StreamEventType.ERROR
                    elif "progress" in content:
                        event_type = StreamEventType.PROGRESS
                    elif "status" in content:
                        event_type = StreamEventType.STATUS
                    else:
                        event_type = StreamEventType.CONTENT
                    data = content
                else:
                    event_type = StreamEventType.CONTENT
                    data = {"content": str(content)}
                
                # Create and yield event
                event = StreamEvent(
                    event_type=event_type,
                    data=data,
                    correlation_id=stream_id
                )
                yield event.to_sse_format()
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
        
        except Exception as e:
            # Send error event
            error_event = StreamEvent(
                event_type=StreamEventType.ERROR,
                data={"error": str(e), "stream_id": stream_id}
            )
            yield error_event.to_sse_format()
            raise
        
        finally:
            # Cancel heartbeat task
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
        
        # Send completion event
        completion_event = StreamEvent(
            event_type=StreamEventType.COMPLETED,
            data={"message": "Stream completed", "stream_id": stream_id}
        )
        yield completion_event.to_sse_format()
        
    finally:
        # Unregister stream
        stream_manager.unregister_stream(stream_id)


async def _heartbeat_generator(stream_id: str, interval: int) -> None:
    """Generate heartbeat events to keep connection alive."""
    try:
        while True:
            await asyncio.sleep(interval)
            # Heartbeat events are handled by the SSE client automatically
            # We just need to keep the connection alive
    except asyncio.CancelledError:
        logger.debug(f"Heartbeat cancelled for stream {stream_id}")


def create_streaming_response(
    generator: AsyncGenerator[Any, None],
    stream_id: str = None,
    media_type: str = "text/event-stream"
) -> StreamingResponse:
    """
    Create a FastAPI StreamingResponse with proper SSE headers.
    
    Args:
        generator: Async generator that yields content
        stream_id: Optional stream ID for tracking
        media_type: Media type for the response
    
    Returns:
        StreamingResponse configured for SSE
    """
    if stream_id is None:
        stream_id = str(uuid.uuid4())
    
    # Wrap generator with SSE formatting
    sse_generator = create_sse_stream(generator, stream_id)
    
    return StreamingResponse(
        sse_generator,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "X-Stream-ID": stream_id
        }
    )


class ProgressTracker:
    """Utility class for tracking and reporting progress during long operations."""
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.start_time = time.time()
        self.step_times = []
    
    def update(self, step_name: str = None, increment: int = 1) -> Dict[str, Any]:
        """
        Update progress and return progress information.
        
        Args:
            step_name: Optional name for the current step
            increment: Number of steps to increment
        
        Returns:
            Dictionary containing progress information
        """
        self.current_step += increment
        current_time = time.time()
        self.step_times.append(current_time)
        
        # Calculate progress percentage
        progress_percent = min((self.current_step / self.total_steps) * 100, 100)
        
        # Estimate remaining time
        elapsed_time = current_time - self.start_time
        if self.current_step > 0:
            avg_time_per_step = elapsed_time / self.current_step
            remaining_steps = max(0, self.total_steps - self.current_step)
            estimated_remaining = avg_time_per_step * remaining_steps
        else:
            estimated_remaining = None
        
        return {
            "operation": self.operation_name,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percent": round(progress_percent, 1),
            "step_name": step_name,
            "elapsed_time": round(elapsed_time, 2),
            "estimated_remaining": round(estimated_remaining, 2) if estimated_remaining else None,
            "is_complete": self.current_step >= self.total_steps
        }
    
    def complete(self) -> Dict[str, Any]:
        """Mark operation as complete and return final progress."""
        self.current_step = self.total_steps
        current_time = time.time()
        self.step_times.append(current_time)
        
        # Calculate progress percentage
        progress_percent = 100.0
        
        # Calculate elapsed time
        elapsed_time = current_time - self.start_time
        
        return {
            "operation": self.operation_name,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percent": progress_percent,
            "step_name": "Completed",
            "elapsed_time": round(elapsed_time, 2),
            "estimated_remaining": 0.0,
            "is_complete": True
        }


@asynccontextmanager
async def streaming_context(operation_name: str, total_steps: int = None):
    """
    Context manager for streaming operations with automatic progress tracking.
    
    Args:
        operation_name: Name of the operation
        total_steps: Total number of steps (optional)
    
    Yields:
        ProgressTracker instance
    """
    if total_steps is None:
        total_steps = 1
    
    tracker = ProgressTracker(total_steps, operation_name)
    
    try:
        yield tracker
    except Exception as e:
        logger.error(f"Streaming operation '{operation_name}' failed: {str(e)}")
        raise
    finally:
        if not tracker.current_step >= tracker.total_steps:
            tracker.complete()


# Utility functions for common streaming patterns

async def stream_with_progress(
    operation: Callable,
    operation_name: str,
    total_steps: int = None,
    *args,
    **kwargs
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute an operation with progress streaming.
    
    Args:
        operation: Async function to execute
        operation_name: Name for progress tracking
        total_steps: Total steps for progress calculation
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
    
    Yields:
        Progress updates and results
    """
    async with streaming_context(operation_name, total_steps) as tracker:
        try:
            # Send initial progress
            yield {"progress": tracker.update("Starting...")}
            
            # Execute operation
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            # Send completion progress
            yield {"progress": tracker.complete()}
            
            # Send final result
            yield {"result": result}
            
        except Exception as e:
            yield {"error": str(e)}
            raise


def get_streaming_stats() -> Dict[str, Any]:
    """Get statistics about active streaming connections."""
    return {
        "active_streams": stream_manager.get_active_streams_count(),
        "stream_details": {
            stream_id: {
                "duration": time.time() - info["start_time"],
                "last_activity": time.time() - info["last_activity"],
                "metadata": info["metadata"]
            }
            for stream_id, info in stream_manager.active_streams.items()
        }
    }


async def cleanup_inactive_streams(max_inactive_seconds: int = 300) -> Dict[str, Any]:
    """
    Clean up inactive streaming connections and return cleanup statistics.
    
    Args:
        max_inactive_seconds: Maximum seconds of inactivity before cleanup
        
    Returns:
        Dictionary containing cleanup statistics
    """
    initial_count = stream_manager.get_active_streams_count()
    
    # Perform cleanup
    await stream_manager.cleanup_stale_streams(max_inactive_seconds)
    
    final_count = stream_manager.get_active_streams_count()
    cleaned_count = initial_count - final_count
    
    return {
        "initial_streams": initial_count,
        "cleaned_streams": cleaned_count,
        "remaining_streams": final_count,
        "cleanup_threshold_seconds": max_inactive_seconds,
        "cleanup_timestamp": time.time()
    }


async def force_close_stream(stream_id: str) -> bool:
    """
    Force close a specific streaming connection.
    
    Args:
        stream_id: ID of the stream to close
        
    Returns:
        True if stream was found and closed, False otherwise
    """
    if stream_id in stream_manager.active_streams:
        stream_manager.unregister_stream(stream_id)
        logger.info(f"Force closed stream {stream_id}")
        return True
    else:
        logger.warning(f"Attempted to force close non-existent stream {stream_id}")
        return False


class StreamHealthChecker:
    """Health checker for streaming connections."""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.is_running = False
        self.health_task = None
    
    async def start_health_checks(self):
        """Start periodic health checks for streaming connections."""
        if self.is_running:
            return
        
        self.is_running = True
        self.health_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started streaming health checker")
    
    async def stop_health_checks(self):
        """Stop periodic health checks."""
        self.is_running = False
        if self.health_task and not self.health_task.done():
            self.health_task.cancel()
            try:
                await self.health_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped streaming health checker")
    
    async def _health_check_loop(self):
        """Main health check loop."""
        try:
            while self.is_running:
                await asyncio.sleep(self.check_interval)
                
                if not self.is_running:
                    break
                
                # Perform health checks
                stats = await cleanup_inactive_streams(300)  # 5 minutes
                
                if stats["cleaned_streams"] > 0:
                    logger.info(f"Health check cleaned up {stats['cleaned_streams']} inactive streams")
                
                # Log health status
                active_count = stream_manager.get_active_streams_count()
                if active_count > 0:
                    logger.debug(f"Streaming health check: {active_count} active streams")
                
        except asyncio.CancelledError:
            logger.debug("Health check loop cancelled")
        except Exception as e:
            logger.error(f"Health check loop error: {str(e)}")


# Global health checker instance
stream_health_checker = StreamHealthChecker()