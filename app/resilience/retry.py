import asyncio
import random
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class RetryExhausted(Exception):
    pass


class RetryableError(Exception):
    pass


class RetryStrategy:
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def is_retryable(self, error: Exception) -> bool:
        # Retry on network errors, 5xx, and temporary failures
        error_str = str(error).lower()
        return any(
            keyword in error_str
            for keyword in ["connection", "timeout", "502", "503", "504", "rate limit", "temporary"]
        )

    def calculate_delay(self, attempt: int) -> float:
        delay = self.base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, self.max_delay)

    async def execute(self, func: Callable[[], T], *args: Any, **kwargs: Any) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if not self.is_retryable(e):
                    raise
                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise RetryExhausted(f"Exhausted {self.max_attempts} attempts") from e
        raise last_error
