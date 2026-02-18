"""Tests for the retry and rate-limiting utilities."""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from jarkdown.retry import RetryConfig, parse_retry_after, retry_with_backoff, DEFAULT_RETRY


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_defaults(self):
        """Verify all default values match specification."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True

    def test_custom_values(self):
        """Custom values override defaults correctly."""
        config = RetryConfig(max_retries=1, base_delay=0.1)
        assert config.max_retries == 1
        assert config.base_delay == 0.1
        assert config.max_delay == 60.0  # still default

    def test_retryable_status_codes_include_429(self):
        """429 Too Many Requests must be in retryable codes."""
        assert 429 in DEFAULT_RETRY.retryable_status_codes

    def test_retryable_status_codes_include_503(self):
        """503 Service Unavailable must be in retryable codes."""
        assert 503 in DEFAULT_RETRY.retryable_status_codes


class TestParseRetryAfter:
    """Tests for parse_retry_after() helper."""

    def test_integer_seconds(self):
        """Parse plain integer seconds string."""
        assert parse_retry_after("30") == 30.0

    def test_zero_seconds(self):
        """Zero seconds returns 0.0."""
        assert parse_retry_after("0") == 0.0

    def test_large_value_capped(self):
        """Values over 300 are capped at 300.0."""
        assert parse_retry_after("999") == 300.0

    def test_negative_clamped_to_zero(self):
        """Negative values are clamped to 0.0."""
        assert parse_retry_after("-5") == 0.0

    def test_http_date_future(self):
        """HTTP-date 30 seconds in the future returns ≈30.0."""
        future = datetime.now(tz=timezone.utc) + timedelta(seconds=30)
        header = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
        result = parse_retry_after(header)
        assert 28.0 <= result <= 32.0  # 2 second tolerance

    def test_http_date_past_clamped(self):
        """HTTP-date in the past returns 0.0 (clamped)."""
        past = datetime.now(tz=timezone.utc) - timedelta(seconds=30)
        header = past.strftime("%a, %d %b %Y %H:%M:%S GMT")
        result = parse_retry_after(header)
        assert result == 0.0

    def test_unparseable_returns_default(self):
        """Unparseable header value returns default of 5.0."""
        assert parse_retry_after("invalid garbage") == 5.0


class TestRetryWithBackoff:
    """Tests for retry_with_backoff() async function."""

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_success_on_first_attempt(self, mock_sleep):
        """Successful call on first attempt is called exactly once."""
        mock_func = AsyncMock(return_value="success")
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        result = await retry_with_backoff(mock_func, config=config)

        assert result == "success"
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_retries_on_429_then_succeeds(self, mock_sleep):
        """Raises 429 twice then succeeds — called 3 times total."""
        import aiohttp

        err_429 = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=429
        )
        mock_func = AsyncMock(side_effect=[err_429, err_429, "success"])
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        result = await retry_with_backoff(mock_func, config=config)

        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2  # slept twice between 3 attempts

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_raises_after_max_retries_exhausted(self, mock_sleep):
        """Always raises 429 — raises ClientResponseError after max_retries+1 attempts."""
        import aiohttp

        err_429 = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=429
        )
        mock_func = AsyncMock(side_effect=err_429)
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        with pytest.raises(aiohttp.ClientResponseError) as exc_info:
            await retry_with_backoff(mock_func, config=config)

        assert exc_info.value.status == 429
        assert mock_func.call_count == 4  # initial + 3 retries

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_non_retryable_404_raises_immediately(self, mock_sleep):
        """404 is not retried — raises on first call."""
        import aiohttp

        err_404 = aiohttp.ClientResponseError(
            request_info=MagicMock(), history=(), status=404
        )
        mock_func = AsyncMock(side_effect=err_404)
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        with pytest.raises(aiohttp.ClientResponseError) as exc_info:
            await retry_with_backoff(mock_func, config=config)

        assert exc_info.value.status == 404
        mock_func.assert_called_once()
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_timeout_error_is_retried(self, mock_sleep):
        """asyncio.TimeoutError triggers retry — succeeds on second attempt."""
        mock_func = AsyncMock(side_effect=[asyncio.TimeoutError(), "success"])
        config = RetryConfig(max_retries=3, base_delay=0.1, jitter=False)

        result = await retry_with_backoff(mock_func, config=config)

        assert result == "success"
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1
