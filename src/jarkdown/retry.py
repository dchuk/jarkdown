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
