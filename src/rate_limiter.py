"""
Intelligent Rate Limiter — Exponential backoff with Meta API header monitoring.
Thread-safe implementation for concurrent extraction.
"""
import json
import time
import logging
import threading
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    """Track rate limit state from Meta API response headers."""
    call_count: int = 0
    total_time: int = 0
    estimated_time_to_regain: int = 0
    last_updated: float = 0.0
    is_blocked: bool = False


class MetaRateLimiter:
    """
    Intelligent rate limiter for Meta Marketing API.
    Handles app-level, account-level, and business-level rate limiting.
    """

    def __init__(
        self,
        max_calls_per_hour: int = 180,
        max_batch_size: int = 50,
        max_retries: int = 5,
        backoff_base: float = 2.0,
        enabled: bool = True,
    ):
        self.max_calls_per_hour = max_calls_per_hour
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.enabled = enabled
        self._app_limits = RateLimitState()
        self._account_limits = RateLimitState()
        self._call_timestamps: list = []
        self._lock = threading.Lock()

    def update_from_headers(self, headers: dict) -> None:
        """Parse rate limit info from Meta API response headers."""
        try:
            usage_header = headers.get("x-business-use-case-usage", "")
            if usage_header:
                usage_data = json.loads(usage_header)
                for _account_id, data in usage_data.items():
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    self._account_limits.call_count = data.get("call_count", 0)
                    self._account_limits.total_time = data.get("total_time", 0)
                    self._account_limits.estimated_time_to_regain = data.get(
                        "estimated_time_to_regain", 0
                    )
                    self._account_limits.last_updated = time.time()
                    self._account_limits.is_blocked = data.get("type", "") == "100"

            app_usage_header = headers.get("x-app-usage", "")
            if app_usage_header:
                app_data = json.loads(app_usage_header)
                self._app_limits.call_count = app_data.get("call_count", 0)
                self._app_limits.last_updated = time.time()

            ad_account_header = headers.get("x-ad-account-usage", "")
            if ad_account_header:
                ad_data = json.loads(ad_account_header)
                pct = ad_data.get("acc_id_util_pct", 0)
                if pct > 75:
                    time.sleep(2)
        except Exception as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")

    def wait_if_needed(self) -> None:
        """Proactively wait if approaching rate limits."""
        if not self.enabled:
            return

        with self._lock:
            now = time.time()
            self._call_timestamps = [
                ts for ts in self._call_timestamps if now - ts < 3600
            ]

            if len(self._call_timestamps) >= self.max_calls_per_hour * 0.8:
                sleep_time = 60
                logger.warning(
                    f"Approaching rate limit "
                    f"({len(self._call_timestamps)}/{self.max_calls_per_hour}). "
                    f"Sleeping {sleep_time}s..."
                )
                time.sleep(sleep_time)

            if self._account_limits.estimated_time_to_regain > 0:
                sleep_time = min(
                    self._account_limits.estimated_time_to_regain + 5, 300
                )
                logger.warning(
                    f"Rate limit regeneration: "
                    f"{self._account_limits.estimated_time_to_regain}s. "
                    f"Sleeping {sleep_time}s..."
                )
                time.sleep(sleep_time)
                self._account_limits.estimated_time_to_regain = 0

            self._call_timestamps.append(now)

    def get_backoff_time(self, attempt: int) -> float:
        """Calculate exponential backoff time."""
        return min(self.backoff_base ** attempt + (0.5 * attempt), 60.0)

    def retry_with_backoff(self, func: Callable, *args, **kwargs):
        """Execute a function with automatic retry on rate limit errors."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.wait_if_needed()
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if any(code in error_str for code in [
                    "rate limit", "too many calls", "throttled",
                    "user request limit", "(#17)", "(#32)", "(#613)",
                    "(#80000)", "(#80003)",
                ]):
                    wait = self.get_backoff_time(attempt)
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{self.max_retries}). "
                        f"Waiting {wait:.1f}s..."
                    )
                    time.sleep(wait)
                else:
                    raise
        raise last_error

    @property
    def status(self) -> dict:
        return {
            "calls_this_hour": len(self._call_timestamps),
            "max_calls_per_hour": self.max_calls_per_hour,
            "account_blocked": self._account_limits.is_blocked,
            "estimated_time_to_regain": self._account_limits.estimated_time_to_regain,
        }


rate_limiter = MetaRateLimiter()


def with_rate_limit(func):
    """Decorator to apply rate limiting to API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return rate_limiter.retry_with_backoff(func, *args, **kwargs)
    return wrapper
