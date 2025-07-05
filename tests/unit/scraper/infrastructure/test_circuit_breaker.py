import pytest
import time
from src.scraper.infrastructure.circuit_breaker import CircuitBreakerPattern

def test_circuit_breaker_opens_and_closes():
    breaker = CircuitBreakerPattern(failure_threshold=2, recovery_timeout=1)
    assert breaker.get_state() == "CLOSED"
    breaker.record_failure()
    assert breaker.get_state() == "CLOSED"
    breaker.record_failure()
    assert breaker.get_state() == "OPEN"
    assert breaker.is_open is True
    # Simula passagem do tempo para recovery
    breaker.last_failure_time -= 2
    assert breaker.get_state() == "HALF-OPEN"
    breaker.record_success()
    assert breaker.get_state() == "CLOSED"

def test_circuit_breaker_resets():
    breaker = CircuitBreakerPattern(failure_threshold=1, recovery_timeout=1)
    breaker.record_failure()
    assert breaker.get_state() == "OPEN"
    breaker.last_failure_time -= 2
    assert breaker.get_state() == "HALF-OPEN"
    breaker.record_success()
    assert breaker.get_state() == "CLOSED"
