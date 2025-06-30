# Python Web MCP Scrapper - Static Analysis and Quality Tools
.PHONY: help lint format type-check security test clean all install-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  install-dev - Install development dependencies"
	@echo "  lint        - Run all linting tools"
	@echo "  format      - Format code with black and isort"
	@echo "  type-check  - Run mypy type checking"
	@echo "  security    - Run bandit security analysis"
	@echo "  test        - Run pytest with coverage"
	@echo "  clean       - Clean cache files and build artifacts"
	@echo "  all         - Run format, lint, type-check, security, and test"

# Install development dependencies
install-dev:
	pip install --user flake8 mypy bandit black isort pytest pytest-cov pytest-asyncio

# Format code
format:
	@echo "🎨 Formatting code with black..."
	python3 -m black src tests --line-length 88
	@echo "📦 Sorting imports with isort..."
	python3 -m isort src tests --profile black

# Lint code
lint:
	@echo "🔍 Linting code with flake8..."
	python3 -m flake8 src tests

# Type checking
type-check:
	@echo "🔬 Type checking with mypy..."
	python3 -m mypy src --config-file mypy.ini

# Security analysis
security:
	@echo "🔒 Security analysis with bandit..."
	python3 -m bandit -r src -f json -o bandit-report.json || true
	python3 -m bandit -r src

# Run tests
test:
	@echo "🧪 Running tests with pytest..."
	python3 -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Clean cache and build files
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f bandit-report.json

# Run all quality checks
all: format lint type-check security test
	@echo "✅ All quality checks completed!"

# Quick check (without tests)
check: format lint type-check security
	@echo "✅ Code quality checks completed!"

# CI/CD target
ci: lint type-check security test
	@echo "✅ CI/CD pipeline completed!" 