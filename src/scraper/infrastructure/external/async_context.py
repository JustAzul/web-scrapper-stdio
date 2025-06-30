"""
AsyncResourceManager - Async context manager for resource management

This provides async context management patterns for resources.
Part of T013 - Async/Await Standardization.
"""

import asyncio


class AsyncResourceManager:
    """
    Async resource manager for demonstration purposes.

    This shows proper async context manager patterns.
    """

    def __init__(self):
        """Initialize async resource manager."""
        self._active = False

    async def __aenter__(self):
        """Async context manager entry."""
        await asyncio.sleep(0.001)  # Simulate async setup
        self._active = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await asyncio.sleep(0.001)  # Simulate async cleanup
        self._active = False

    def is_active(self) -> bool:
        """Check if resource manager is active."""
        return self._active

    async def perform_async_operation(self) -> str:
        """Perform an async operation."""
        await asyncio.sleep(0.001)
        return "operation_result"
