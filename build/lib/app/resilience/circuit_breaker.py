import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class Clock:
    """Injectable clock for deterministic tests."""

    def time(self) -> float:
        return time.time()


class CircuitBreaker:
    def __init__(
        self,
        threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 3,
        clock: Clock | None = None,
    ):
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.clock = clock or Clock()

        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: float | None = None

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN
            self.last_failure_time = self.clock.time()
            self.successes = 0

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
        elif self.state == CircuitState.CLOSED:
            self.failures = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.clock.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        return True  # HALF_OPEN allows execution
