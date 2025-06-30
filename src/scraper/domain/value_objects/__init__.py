"""
Domain Value Objects

This module contains value objects that replace primitive obsession
and provide type safety, validation, and encapsulation.
"""

from .value_objects import MemorySize, ScrapingConfig, TimeoutValue

__all__ = [
    "TimeoutValue",
    "MemorySize",
    "ScrapingConfig",
]
