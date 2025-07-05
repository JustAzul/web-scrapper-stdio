"""
Circuit Breaker Pattern Implementation
Single Responsibility: Implement circuit breaker pattern for failures
"""

import time

from src.logger import get_logger

logger = get_logger(__name__)


class CircuitBreakerPattern:
    """Implements a Circuit Breaker pattern."""

    def __init__(self, failure_threshold: int, recovery_timeout: int):
        """
        Initializes the Circuit Breaker.

        Args:
            failure_threshold: Number of failures to open the circuit.
            recovery_timeout: Seconds to wait before moving to HALF_OPEN.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0
        self.logger = logger

    def record_failure(self):
        """Records a failure and handles state transitions."""
        if self.state == "HALF-OPEN":
            self.state = "OPEN"
            self.last_failure_time = time.time()
            self.logger.warning("Circuit breaker RE-OPENED from HALF-OPEN state.")
        else:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                if self.state == "CLOSED":
                    self.state = "OPEN"
                    self.last_failure_time = time.time()
                    self.logger.warning("Circuit breaker OPENED.")

    def record_success(self):
        """Records a success and handles state transitions."""
        if self.state == "HALF-OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.logger.info("Circuit breaker RESET to CLOSED from HALF-OPEN.")
        elif self.state == "CLOSED":
            self.failure_count = 0  # Reset on any success in closed state

    @property
    def is_open(self) -> bool:
        """
        Determines if the circuit is currently open without changing state.
        A circuit is considered open if it is in the OPEN state and the
        recovery timeout has not yet passed.
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                # The circuit is ready for a trial request (HALF-OPEN state),
                # so it's not considered strictly 'open' anymore.
                return False
            return True
        return False

    def get_state(self) -> str:
        """
        Gets the current state of the circuit breaker, handling the transition
        to HALF-OPEN if the recovery timeout has passed.
        """
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                self.logger.info("Circuit breaker moved to HALF-OPEN state.")
        return self.state

    def get_failure_count(self) -> int:
        """Returns the current number of failures."""
        return self.failure_count

    def __repr__(self) -> str:
        """String representation of the circuit breaker."""
        return (
            f"CircuitBreaker(state={self.state}, "
            f"failures={self.failure_count}/{self.failure_threshold}, "
            f"recovery_timeout={self.recovery_timeout}s)"
        )
