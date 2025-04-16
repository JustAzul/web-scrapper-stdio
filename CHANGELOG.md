# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure setup.
- FastAPI application (`src/api.py`) with `/extract` endpoint.
- Core scraping logic using Playwright and BeautifulSoup (`src/scraper.py`).
- Configuration loading from environment variables (`src/config.py`).
- Entry point application (`src/main.py`) that integrates API and MCP server.
- MCP server implementation (`src/mcp_server.py`) with WEBPAGE_TEXT_EXTRACTOR tool.
- Comprehensive test suite:
  - API endpoint tests (`tests/test_api.py`)
  - MCP tool tests (`tests/test_mcp.py`) 
  - Integration tests (`tests/test_integration.py`)
- Dockerfile for containerization with Playwright dependencies.
- Docker Compose setup (`docker-compose.yml`) for service and testing.
- Project documentation:
  - README.md with setup instructions and usage guidelines
  - `.env.example` for environment configuration reference
- Initial `CHANGELOG.md` file.

### Changed
- Implemented proper error handling for various failure scenarios.
- Optimized text extraction strategies for different website types.

### Fixed
- Addressed potential memory leaks with proper Playwright context cleanup.
- Implemented URL validation to prevent SSRF attacks. 