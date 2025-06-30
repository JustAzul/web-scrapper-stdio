"""
Tests for the AsyncConsistencyValidator tool.
"""

import pytest

from src.scraper.infrastructure.external.async_validator import (
    AsyncConsistencyValidator,
)


class TestAsyncConsistencyValidator:
    """Test class for verifying AsyncConsistencyValidator."""

    @pytest.fixture
    def async_validator(self):
        """Create AsyncConsistencyValidator instance for testing."""
        return AsyncConsistencyValidator(source_directory="tests/fixtures")

    def test_async_validator_initialization(self, async_validator):
        """Test that AsyncConsistencyValidator initializes properly."""
        assert async_validator.source_directory == "tests/fixtures"
        assert "requests.get" in async_validator.sync_io_patterns
        assert "time.sleep" in async_validator.sync_io_patterns
        assert "await" in async_validator.async_io_patterns

    def test_async_validator_get_python_files(self, async_validator):
        """Test that AsyncConsistencyValidator can find Python files."""
        # Mock the source directory to point to the actual src directory
        async_validator.source_directory = "src"
        python_files = async_validator._get_python_files()

        # Should find at least some Python files
        assert len(python_files) > 0
        assert all(str(f).endswith(".py") for f in python_files)

    def test_async_validator_find_violations(self, async_validator):
        """Test that AsyncConsistencyValidator can analyze code."""
        # Use the actual source directory
        async_validator.source_directory = "src"

        # Test sync I/O violations detection
        sync_violations = async_validator.find_sync_io_violations()
        assert isinstance(sync_violations, list)

        # Test mixed patterns detection
        mixed_patterns = async_validator.find_mixed_async_sync_patterns()
        assert isinstance(mixed_patterns, list)

        # Test full project validation
        results = async_validator.validate_project()
        assert "sync_io_violations" in results
        assert "mixed_patterns" in results
