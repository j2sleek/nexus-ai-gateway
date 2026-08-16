import asyncio
import random
from collections.abc import Awaitable, Callable
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

    def calculate_delay(self, attempt: int, remaining_time: float) -> float:
        # Calculate exponential backoff with jitter
        delay = self.base_delay * (2 ** (attempt - 1))
        jitter = random.uniform(0, delay * 0.1)
        calculated_delay = delay + jitter
        # Never exceed remaining time budget or max_delay
        return min(calculated_delay, remaining_time, self.max_delay)

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        timeout: float,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        last_error: Exception | None = None
        start_time = asyncio.get_event_loop().time()

        for attempt in range(1, self.max_attempts + 1):
            remaining_time = timeout - (asyncio.get_event_loop().time() - start_time)
            if remaining_time <= 0:
                raise TimeoutError(f"Total timeout of {timeout}s exceeded")

            try:
                # Use wait_for with the remaining time budget
                return await asyncio.wait_for(func(*args, **kwargs), timeout=remaining_time)
            except TimeoutError:
                # If we timeout on an individual attempt, check if we have retries left
                if attempt < self.max_attempts:
                    # Calculate delay based on remaining time
                    delay = self.calculate_delay(attempt, remaining_time)
                    if delay > 0:
                        await asyncio.sleep(delay)
                    continue
                raise
            except Exception as e:
                last_error = e
                if not self.is_retryable(e):
                    raise
                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt, remaining_time)
                    if delay > 0:
                        await asyncio.sleep(delay)
                else:
                    raise RetryExhausted(f"Exhausted {self.max_attempts} attempts") from e
        if last_error:
            raise last_error
        raise RetryExhausted("Max attempts reached without error")
