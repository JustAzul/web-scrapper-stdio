"""
Circuit Breaker Pattern Implementation
Responsabilidade única: Implementar padrão circuit breaker para falhas
"""

import time

from src.logger import Logger

logger = Logger(__name__)


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
        """Records a failure and opens the circuit if threshold is met."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = time.time()
            self.logger.warning("Circuit breaker OPENED.")

    def record_success(self):
        """Resets the circuit breaker to a CLOSED state on success."""
        if self.state != "CLOSED":
            self.logger.info("Circuit breaker RESET to CLOSED state.")
        self.failure_count = 0
        self.state = "CLOSED"

    @property
    def is_open(self) -> bool:
        """Checks if the circuit is open, with logic for HALF_OPEN state."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker moved to HALF_OPEN state.")
                return False  # Allow one trial request
            return True
        return False

    def get_state(self) -> str:
        """Returns the current state of the circuit."""
        # Trigger property to update state if needed
        _ = self.is_open
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
