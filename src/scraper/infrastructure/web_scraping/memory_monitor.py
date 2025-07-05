from contextlib import contextmanager

from .application.contracts.memory_monitor import MemoryMonitorInterface


class MemoryMonitor(MemoryMonitorInterface):
    # ... existing code ...
    def check_memory_limit(
        self, current_usage_mb: float, threshold: float = 0.9
    ) -> bool:
        if self.memory_limit_mb is None:
            return False
        return current_usage_mb > (self.memory_limit_mb * threshold)

    @contextmanager
    def monitor_memory_context(self):
        """A context manager to monitor memory usage during a block of code."""
        start_memory = self.get_memory_usage()
        metrics = {
            "start_memory_mb": start_memory,
            "peak_memory_mb": start_memory,
            "end_memory_mb": 0,
        }
        try:
            yield metrics
        finally:
            end_memory = self.get_memory_usage()
            metrics["end_memory_mb"] = end_memory
            # In a real scenario, you might want to track the peak inside the block
            metrics["peak_memory_mb"] = max(metrics["peak_memory_mb"], end_memory)

    def __repr__(self):
        return f"MemoryMonitor(pid={self.pid}, memory_limit_mb={self.memory_limit_mb})"
