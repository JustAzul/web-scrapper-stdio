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
- Dockerfile for containerization with Playwright dependencies.
- Docker Compose setup (`docker-compose.yml`) for service and testing.
- Basic test directory structure (`tests/`).
- Basic README, PRD, requirements.txt.
- `.env.example` and `.env` files for environment configuration.
- Initial `CHANGELOG.md` file. 