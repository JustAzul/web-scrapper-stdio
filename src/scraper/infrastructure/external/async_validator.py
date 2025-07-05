"""
AsyncConsistencyValidator - Validates async/await consistency

This validator checks for async/await consistency violations in the codebase.
Part of T013 - Async/Await Standardization.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional

from src.logger import get_logger

logger = get_logger(__name__)


class AsyncConsistencyValidator:
    """
    Validator for async/await consistency across the codebase.

    This class helps identify violations of async/await patterns
    and ensures consistency in asynchronous code.
    """

    def __init__(self, source_directory: str = "src"):
        """Initialize async consistency validator."""
        self.source_directory = source_directory
        self.sync_io_patterns = {
            "requests.get",
            "requests.post",
            "requests.put",
            "requests.delete",
            "time.sleep",
            "urllib.request.urlopen",
            "open",
            "file.read",
            "file.write",
            "subprocess.run",
            "subprocess.call",
        }
        self.async_io_patterns = {
            "aiohttp.get",
            "aiohttp.post",
            "asyncio.sleep",
            "aiofiles.open",
            "async with",
            "await",
        }

    def find_sync_io_violations(self) -> List[Dict[str, str]]:
        """
        Find synchronous I/O operations that should be async.

        Returns:
            List of violations found
        """
        violations = []

        for python_file in self._get_python_files():
            try:
                with open(python_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                # Find async functions with sync I/O
                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        sync_calls = self._find_sync_calls_in_function(node, content)
                        if sync_calls:
                            for call in sync_calls:
                                violations.append(
                                    {
                                        "file": str(python_file),
                                        "function": node.name,
                                        "line": call["line"],
                                        "violation": (
                                            f"Sync I/O call '{call['call']}' in "
                                            "async function"
                                        ),
                                        "suggestion": "Replace with async equivalent",
                                    }
                                )

            except Exception as e:
                logger.warning(f"Error analyzing file {python_file}: {e}")

        return violations

    def find_mixed_async_sync_patterns(self) -> List[Dict[str, str]]:
        """
        Find mixed async/sync patterns in the same module.

        Returns:
            List of mixed patterns found
        """
        violations = []

        for python_file in self._get_python_files():
            try:
                with open(python_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                async_functions = []
                sync_functions = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.AsyncFunctionDef):
                        async_functions.append(node.name)
                    elif isinstance(node, ast.FunctionDef):
                        # Skip special methods and properties
                        if not node.name.startswith("_"):
                            sync_functions.append(node.name)

                # Check for mixed patterns
                if async_functions and sync_functions:
                    violations.append(
                        {
                            "file": str(python_file),
                            "violation": "Mixed async/sync functions in same module",
                            "async_functions": ", ".join(async_functions),
                            "sync_functions": ", ".join(sync_functions),
                            "suggestion": (
                                "Consider separating async and sync code"
                                " or converting to consistent pattern"
                            ),
                        }
                    )

            except Exception as e:
                logger.warning(f"Error analyzing file {python_file}: {e}")

        return violations

    def _get_python_files(self) -> List[Path]:
        """Get all Python files in the source directory."""
        python_files = []
        source_path = Path(self.source_directory)

        if source_path.exists():
            for file_path in source_path.rglob("*.py"):
                if not any(part.startswith(".") for part in file_path.parts):
                    python_files.append(file_path)

        return python_files

    def _find_sync_calls_in_function(
        self, func_node: ast.AsyncFunctionDef, content: str
    ) -> List[Dict[str, str]]:
        """Find synchronous I/O calls within an async function."""
        sync_calls = []

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_info = self._check_sync_call(node)
                if call_info:
                    sync_calls.append(call_info)

        return sync_calls

    def _check_sync_call(self, call_node: ast.Call) -> Optional[Dict[str, str]]:
        """Check if a call is a synchronous I/O call."""
        try:
            if isinstance(call_node.func, ast.Attribute):
                if isinstance(call_node.func.value, ast.Name):
                    call_str = f"{call_node.func.value.id}.{call_node.func.attr}"
                    if any(pattern in call_str for pattern in self.sync_io_patterns):
                        return {"call": call_str, "line": str(call_node.lineno)}
            elif isinstance(call_node.func, ast.Name):
                call_str = call_node.func.id
                if any(pattern in call_str for pattern in self.sync_io_patterns):
                    return {"call": call_str, "line": str(call_node.lineno)}
        except Exception as e:
            # Log the error instead of silently passing
            logger.warning(f"Failed to check sync call: {e}")
        return None

    def validate_project(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Validate the entire project for async consistency.

        Returns:
            Dictionary with validation results
        """
        return {
            "sync_io_violations": self.find_sync_io_violations(),
            "mixed_patterns": self.find_mixed_async_sync_patterns(),
        }
