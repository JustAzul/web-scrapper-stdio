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
- All domains with available RSS feeds are now included in the test suite (fortune.com, techcrunch.com, wired.com, engadget.com, medium.com, dev.to, tomsguide.com, xda-developers.com, dmnews.com).
- Improved test naming: test cases now use domain URLs for clarity.
- Cloudflare challenge detection and error handling in the scraper.

### Changed
- Implemented proper error handling for various failure scenarios.
- Optimized text extraction strategies for different website types.
- Removed all API integration, endpoints, and related tests (FastAPI, API test files, and dependencies).
- Refactored docker-compose.yml: removed legacy API and redundant test services, consolidated test execution.
- Removed run_domain_tests.py script and test_domains Docker Compose service.

### Fixed
- Addressed potential memory leaks with proper Playwright context cleanup.
- Implemented URL validation to prevent SSRF attacks.
- Test suite is robust against dynamic article discovery failures and Cloudflare blocks. 