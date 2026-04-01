import logging
import time
import uuid
from contextlib import contextmanager
from typing import Optional

import structlog

from apps.apis.config import LOG_LEVEL


# Configure structlog to output structured JSON logs
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,          # Respect logging level
        structlog.stdlib.add_logger_name,          # Add logger name to each log entry
        structlog.stdlib.add_log_level,            # Add log level (info, error, etc.)
        structlog.stdlib.PositionalArgumentsFormatter(),  # Format positional args
        structlog.processors.TimeStamper(fmt="iso"),      # Add timestamp in ISO format
        structlog.processors.StackInfoRenderer(),         # Include stack info if requested
        structlog.processors.format_exc_info,             # Format exception info
        structlog.processors.UnicodeDecoder(),            # Ensure unicode-safe output
        structlog.processors.JSONRenderer(),              # Render logs as JSON
    ],
    wrapper_class=structlog.stdlib.BoundLogger,   # Use standard library logger wrapper
    context_class=dict,                           # Store context in a simple dict
    logger_factory=structlog.stdlib.LoggerFactory(),  # Create standard loggers
    cache_logger_on_first_use=True,               # Cache logger for performance
)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a structlog logger with the given name.
    """
    return structlog.get_logger(name)


@contextmanager
def log_api_call(symbol: str, provider: str):
    """
    Context manager that logs the lifecycle of an API call:
    - When it starts
    - When it completes successfully
    - When it fails (with error details)

    It also:
    - Generates a unique correlation_id for tracing
    - Measures latency in milliseconds
    """
    correlation_id = str(uuid.uuid4())  # Unique ID for tracing this API call
    logger = get_logger("api_call")
    start_time = time.time()            # Track start time for latency measurement

    # Log the start of the API call
    logger.info(
        "API call started",
        symbol=symbol,
        provider=provider,
        correlation_id=correlation_id,
    )

    try:
        # Yield control back to the caller's code block
        yield

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Log successful completion
        logger.info(
            "API call completed",
            symbol=symbol,
            provider=provider,
            correlation_id=correlation_id,
            latency_ms=round(latency_ms, 2),
            status="success",
        )

    except Exception as e:
        # Calculate latency even on failure
        latency_ms = (time.time() - start_time) * 1000

        # Log failure with error details
        logger.error(
            "API call failed",
            symbol=symbol,
            provider=provider,
            correlation_id=correlation_id,
            latency_ms=round(latency_ms, 2),
            status="error",
            error=str(e),
        )

        # Re-raise the exception so the caller can handle it
        raise
