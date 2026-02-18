"""Retry and rate-limiting utilities for async API calls."""

import asyncio
import random
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Tuple

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts before raising.
        base_delay: Initial delay in seconds (doubles each attempt).
        max_delay: Cap on delay regardless of backoff calculation.
        jitter: If True, add random jitter to prevent thundering herd.
        retryable_status_codes: HTTP status codes that should trigger retry.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    retryable_status_codes: Tuple[int, ...] = (429, 503, 504)


DEFAULT_RETRY = RetryConfig()


def parse_retry_after(header_value: str) -> float:
    """Parse a Retry-After header value into seconds to wait.

    Handles both formats:
    - Integer seconds: "30" → 30.0
    - HTTP-date: "Mon, 17 Feb 2026 12:00:00 GMT" → seconds until that time

    Args:
        header_value: Raw Retry-After header string.

    Returns:
        Number of seconds to wait (minimum 0.0, maximum 300.0).
    """
    header_value = header_value.strip()

    # Try integer seconds first
    try:
        seconds = float(header_value)
        return max(0.0, min(seconds, 300.0))
    except ValueError:
        pass

    # Try HTTP-date format
    try:
        retry_time = parsedate_to_datetime(header_value)
        now = datetime.now(tz=timezone.utc)
        wait = (retry_time - now).total_seconds()
        return max(0.0, min(wait, 300.0))
    except Exception:
        # Cannot parse — return default 5 seconds
        return 5.0


async def retry_with_backoff(
    coro_func,
    *args,
    config: RetryConfig = DEFAULT_RETRY,
    retry_after_header: str = None,
    **kwargs,
):
    """Retry an async callable with exponential backoff.

    Retries on aiohttp.ClientResponseError with retryable status codes,
    asyncio.TimeoutError, and aiohttp.ServerTimeoutError.

    Args:
        coro_func: Async callable to retry.
        *args: Positional arguments to pass to coro_func.
        config: RetryConfig controlling retry behavior.
        retry_after_header: If provided, used for first retry delay.
        **kwargs: Keyword arguments to pass to coro_func.

    Returns:
        Result of coro_func on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    import aiohttp

    last_exc = None
    for attempt in range(config.max_retries + 1):
        try:
            return await coro_func(*args, **kwargs)
        except aiohttp.ClientResponseError as e:
            if e.status not in config.retryable_status_codes:
                raise  # Non-retryable HTTP error (401, 404, etc.)
            last_exc = e
            if attempt == config.max_retries:
                break
            # Use Retry-After if available (only on first attempt and if provided)
            if attempt == 0 and retry_after_header:
                delay = parse_retry_after(retry_after_header)
            else:
                delay = min(config.base_delay * (2**attempt), config.max_delay)
                if config.jitter:
                    delay += random.uniform(0, delay * 0.1)
            logger.warning(
                f"Rate limited (attempt {attempt + 1}/{config.max_retries}), "
                f"retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)
        except asyncio.TimeoutError as e:
            last_exc = e
            if attempt == config.max_retries:
                break
            delay = min(config.base_delay * (2**attempt), config.max_delay)
            if config.jitter:
                delay += random.uniform(0, delay * 0.1)
            await asyncio.sleep(delay)

    raise last_exc
