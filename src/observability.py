"""
Baby MARS Observability
========================

Structured logging, metrics, and tracing for production.
"""

import asyncio
import functools
import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Callable, Optional

# ============================================================
# STRUCTURED LOGGER
# ============================================================


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add location
        if record.levelno >= logging.WARNING:
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data)


class StructuredLogger:
    """Logger with structured output and extra fields."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._context: dict = {}

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Return logger with additional context."""
        new_logger = StructuredLogger(self.logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs):
        extra = {"extra_data": {**self._context, **kwargs}}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None,
):
    """Setup logging configuration."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    if json_format:
        console.setFormatter(StructuredFormatter())
    else:
        console.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    root.addHandler(console)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root.addHandler(file_handler)

    return root


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger."""
    return StructuredLogger(name)


# ============================================================
# METRICS
# ============================================================


@dataclass
class Metric:
    """A single metric measurement."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsCollector:
    """Collects and exports metrics."""

    def __init__(self):
        self._metrics: list[Metric] = []
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}

    def gauge(self, name: str, value: float, **tags):
        """Record a gauge metric (point-in-time value)."""
        self._metrics.append(Metric(name=name, value=value, tags=tags, metric_type="gauge"))

    def increment(self, name: str, value: float = 1.0, **tags):
        """Increment a counter."""
        key = f"{name}:{json.dumps(tags, sort_keys=True)}"
        self._counters[key] = self._counters.get(key, 0) + value
        self._metrics.append(
            Metric(name=name, value=self._counters[key], tags=tags, metric_type="counter")
        )

    def histogram(self, name: str, value: float, **tags):
        """Record a histogram value."""
        key = f"{name}:{json.dumps(tags, sort_keys=True)}"
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._metrics.append(Metric(name=name, value=value, tags=tags, metric_type="histogram"))

    @contextmanager
    def timer(self, name: str, **tags):
        """Context manager to time operations."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.histogram(f"{name}_seconds", duration, **tags)

    def get_stats(self, name: str) -> dict:
        """Get statistics for a histogram."""
        matching = []
        for key, values in self._histograms.items():
            if key.startswith(name):
                matching.extend(values)

        if not matching:
            return {}

        return {
            "count": len(matching),
            "min": min(matching),
            "max": max(matching),
            "avg": sum(matching) / len(matching),
            "p50": sorted(matching)[len(matching) // 2],
            "p99": sorted(matching)[int(len(matching) * 0.99)],
        }

    def export(self) -> list[dict]:
        """Export all metrics as dicts."""
        return [asdict(m) for m in self._metrics]

    def clear(self):
        """Clear collected metrics."""
        self._metrics.clear()


# Singleton metrics collector
_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    return _metrics


# ============================================================
# TRACING
# ============================================================


@dataclass
class Span:
    """A trace span."""

    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "ok"
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)

    @property
    def duration_ms(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000


class Tracer:
    """Simple tracing implementation."""

    def __init__(self):
        self._spans: list[Span] = []
        self._current_trace: Optional[str] = None
        self._current_span: Optional[str] = None

    def start_trace(self, name: str, **attributes) -> str:
        """Start a new trace."""
        trace_id = uuid.uuid4().hex[:16]
        self._current_trace = trace_id
        self.start_span(name, **attributes)
        return trace_id

    def start_span(self, name: str, **attributes) -> str:
        """Start a new span."""
        span_id = uuid.uuid4().hex[:8]
        span = Span(
            trace_id=self._current_trace or uuid.uuid4().hex[:16],
            span_id=span_id,
            parent_id=self._current_span,
            name=name,
            start_time=time.perf_counter(),
            attributes=attributes,
        )
        self._spans.append(span)
        self._current_span = span_id
        return span_id

    def end_span(self, status: str = "ok", **attributes):
        """End the current span."""
        for span in reversed(self._spans):
            if span.span_id == self._current_span:
                span.end_time = time.perf_counter()
                span.status = status
                span.attributes.update(attributes)
                # Pop to parent
                self._current_span = span.parent_id
                break

    def add_event(self, name: str, **attributes):
        """Add an event to the current span."""
        for span in reversed(self._spans):
            if span.span_id == self._current_span:
                span.events.append(
                    {
                        "name": name,
                        "timestamp": time.perf_counter(),
                        "attributes": attributes,
                    }
                )
                break

    @contextmanager
    def span(self, name: str, **attributes):
        """Context manager for spans."""
        self.start_span(name, **attributes)
        try:
            yield
        except Exception as e:
            self.end_span(status="error", error=str(e))
            raise
        else:
            self.end_span()

    def export(self) -> list[dict]:
        """Export all spans."""
        return [asdict(s) for s in self._spans]

    def clear(self):
        """Clear spans."""
        self._spans.clear()
        self._current_trace = None
        self._current_span = None


# Singleton tracer
_tracer = Tracer()


def get_tracer() -> Tracer:
    """Get the global tracer."""
    return _tracer


# ============================================================
# DECORATORS
# ============================================================


def traced(name: Optional[str] = None):
    """Decorator to trace a function."""

    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.span(span_name, args_count=len(args)):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.span(span_name, args_count=len(args)):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def timed(name: Optional[str] = None):
    """Decorator to time a function."""

    def decorator(func: Callable):
        metric_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.timer(metric_name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics = get_metrics()
            with metrics.timer(metric_name):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================
# COGNITIVE LOOP INSTRUMENTATION
# ============================================================


class CognitiveLoopInstrumentation:
    """Instrumentation for the cognitive loop."""

    def __init__(self):
        self.logger = get_logger("cognitive_loop")
        self.metrics = get_metrics()
        self.tracer = get_tracer()

    def on_loop_start(self, thread_id: str, org_id: str):
        """Called when cognitive loop starts."""
        self.tracer.start_trace("cognitive_loop", thread_id=thread_id, org_id=org_id)
        self.metrics.increment("cognitive_loop_started", org_id=org_id)
        self.logger.info("Cognitive loop started", thread_id=thread_id, org_id=org_id)

    def on_node_start(self, node_name: str):
        """Called when a node starts processing."""
        self.tracer.start_span(f"node.{node_name}")
        self.logger.debug(f"Node started: {node_name}", node=node_name)

    def on_node_end(self, node_name: str, updates: dict):
        """Called when a node finishes."""
        self.tracer.end_span()
        self.metrics.increment("node_processed", node=node_name)
        self.logger.debug(
            f"Node completed: {node_name}", node=node_name, update_keys=list(updates.keys())
        )

    def on_claude_call(self, node_name: str, tokens_in: int, tokens_out: int, latency_ms: float):
        """Called after a Claude API call."""
        self.metrics.histogram("claude_latency_ms", latency_ms, node=node_name)
        self.metrics.increment("claude_tokens_in", tokens_in, node=node_name)
        self.metrics.increment("claude_tokens_out", tokens_out, node=node_name)
        self.logger.debug(
            "Claude API call",
            node=node_name,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
        )

    def on_belief_update(
        self, belief_id: str, old_strength: float, new_strength: float, category: str
    ):
        """Called when a belief is updated."""
        delta = new_strength - old_strength
        self.metrics.histogram("belief_strength_delta", delta, category=category)
        self.tracer.add_event("belief_update", belief_id=belief_id, delta=delta)
        self.logger.info(
            "Belief updated",
            belief_id=belief_id,
            old_strength=old_strength,
            new_strength=new_strength,
            delta=delta,
            category=category,
        )

    def on_supervision_mode(self, mode: str, strength: float):
        """Called when supervision mode is determined."""
        self.metrics.increment("supervision_mode", mode=mode)
        self.tracer.add_event("supervision_mode", mode=mode, strength=strength)
        self.logger.info("Supervision mode determined", mode=mode, belief_strength=strength)

    def on_loop_end(self, outcome: str, duration_ms: float):
        """Called when cognitive loop completes."""
        self.tracer.end_span()
        self.metrics.histogram("cognitive_loop_duration_ms", duration_ms)
        self.metrics.increment("cognitive_loop_completed", outcome=outcome)
        self.logger.info("Cognitive loop completed", outcome=outcome, duration_ms=duration_ms)

    def on_error(self, error: Exception, node: Optional[str] = None):
        """Called on error."""
        self.metrics.increment("errors", node=node or "unknown", error_type=type(error).__name__)
        self.logger.error(
            f"Error in cognitive loop: {error}",
            node=node,
            error_type=type(error).__name__,
            error_message=str(error),
        )


# Singleton instrumentation
_instrumentation = CognitiveLoopInstrumentation()


def get_instrumentation() -> CognitiveLoopInstrumentation:
    """Get the global instrumentation."""
    return _instrumentation
