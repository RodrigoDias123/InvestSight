import logging
from functools import wraps
from typing import Callable, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from apps.apis.config import RETRY_MAX_ATTEMPTS
from apps.apis.exceptions import ProviderUnavailable


# Standard Python logger for this module
logger = logging.getLogger(__name__)


# Generic type variable so the decorator preserves return types
T = TypeVar("T")


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that automatically retries a function when it raises ProviderUnavailable.
    Uses exponential backoff and stops after RETRY_MAX_ATTEMPTS.
    """

    @wraps(func)
    @retry(
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),   # Max retry attempts
        wait=wait_exponential(multiplier=1, min=1, max=10),  # Exponential backoff
        retry=retry_if_exception_type(ProviderUnavailable),  # Only retry on this exception
        reraise=True,  # Re-raise the final exception after retries
    )
    def wrapper(*args, **kwargs):
        # Log each attempt before calling the function
        logger.info(
            f"Attempting {func.__name__}",
            extra={"function": func.__name__}
        )

        try:
            # Execute the wrapped function
            return func(*args, **kwargs)

        except ProviderUnavailable as e:
            # Log that a retry will happen
            logger.warning(
                f"Retry needed for {func.__name__}: {e}"
            )
            raise  # Re-raise so tenacity can handle the retry

    return wrapper
