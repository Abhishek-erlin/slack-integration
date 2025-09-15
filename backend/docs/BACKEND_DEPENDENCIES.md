# Slack Integration Backend Dependencies

This document provides a comprehensive overview of all the important dependencies required for the Slack integration backend service.

## Core Framework Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | ^0.109.0 | Main web framework for building the API endpoints with automatic OpenAPI documentation |
| **Uvicorn** | ^0.25.0 | ASGI server for running the FastAPI application |
| **Pydantic** | ^2.5.0 | Data validation and settings management using Python type annotations |
| **Pydantic-Settings** | ^2.1.0 | Settings management for Pydantic |

## Slack Integration Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **slack-sdk** | ^3.27.0 | Official Slack SDK for Python to interact with Slack APIs |
| **slack-bolt** | ^1.18.0 | Framework for building Slack apps with event handling and middleware support |
| **httpx** | ^0.27.0 | Fully featured async HTTP client for making API requests to Slack |

## Database and ORM

| Dependency | Version | Purpose |
|------------|---------|---------|
| **supabase** | ^2.3.1 | Python client for Supabase (PostgreSQL database with additional features) |
| **SQLAlchemy** | ^2.0.25 | SQL toolkit and ORM for database interactions |
| **psycopg2-binary** | ^2.9.9 | PostgreSQL adapter for Python |
| **alembic** | ^1.13.1 | Database migration tool for SQLAlchemy |
| **redis** | ^5.0.1 | In-memory data structure store for caching and session management |

## Authentication and Security

| Dependency | Version | Purpose |
|------------|---------|---------|
| **python-jose** | ^3.3.0 | JavaScript Object Signing and Encryption implementation for JWT |
| **passlib** | ^1.7.4 | Password hashing library |
| **bcrypt** | ^3.1.7 | Password hashing function |
| **cryptography** | ^43.0.1 | Cryptographic recipes and primitives |

## Task Processing

| Dependency | Version | Purpose |
|------------|---------|---------|
| **celery** | ^5.3.4 | Distributed task queue for background processing |

## AI and NLP Components

| Dependency | Version | Purpose |
|------------|---------|---------|
| **crewai** | 0.105.0 | AI agent framework for orchestrating multi-agent workflows |
| **crewai-tools** | 0.42.0 | Tools for the CrewAI framework |
| **nltk** | ^3.8.1 | Natural Language Toolkit for text processing |

## Web Scraping and Content Extraction

| Dependency | Version | Purpose |
|------------|---------|---------|
| **extruct** | 0.13.0 | Library for extracting embedded metadata from HTML pages |
| **w3lib** | ^2.1.2 | Library of web-related functions |
| **lxml** | 4.9.3 | XML and HTML processing library |
| **selenium** | ^4.17.2 | Browser automation for web scraping |
| **webdriver-manager** | ^4.0.1 | Automated driver management for Selenium |
| **playwright** | ^1.40.0 | Modern browser automation library |

## Utility Libraries

| Dependency | Version | Purpose |
|------------|---------|---------|
| **python-dotenv** | ^1.0.0 | Loading environment variables from .env files |
| **pyyaml** | ^6.0.1 | YAML parser and emitter for configuration files |
| **boto3** | ^1.34.0 | AWS SDK for Python, used for AWS services integration |
| **nest-asyncio** | ^1.6.0 | Patch for asyncio to allow nested event loops |
| **python-multipart** | ^0.0.20 | Multipart form data parser, used for file uploads |
| **email-validator** | ^2.2.0 | Email validation library |
| **aiofiles** | ^23.2.1 | File operations for asyncio |
| **requests** | ^2.31.0 | HTTP library for synchronous requests |

## Google API Integration

| Dependency | Version | Purpose |
|------------|---------|---------|
| **google-auth-oauthlib** | ^1.2.2 | Google authentication library with OAuth 2.0 support |
| **google-api-python-client** | ^2.172.0 | Google API client library |

## Development and Testing Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **pytest** | ^8.0.0 | Testing framework |
| **pytest-asyncio** | ^0.23.5 | Pytest plugin for testing asyncio code |
| **pytest-cov** | ^4.1.0 | Coverage plugin for pytest |
| **black** | ^23.7.0 | Code formatter |
| **isort** | ^5.12.0 | Import sorter |
| **flake8** | ^6.1.0 | Linter for style guide enforcement |
| **mypy** | ^1.5.1 | Static type checker |
| **pre-commit** | ^3.6.0 | Git hook scripts for code quality checks |

## Environment Setup

The application requires several environment variables to be set up properly:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_REDIRECT_URI=your_slack_redirect_uri
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Installation Instructions

The project uses Poetry for dependency management. To install all dependencies:

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# For development dependencies
poetry install --with dev
```

## Dependency Management

- **Poetry**: Used for dependency management and packaging
- **pyproject.toml**: Contains all dependency specifications
- **poetry.lock**: Ensures reproducible installations

## Key Dependency Relationships

1. **FastAPI + Uvicorn**: Core web framework and server
2. **Slack SDK + Bolt**: Primary integration with Slack APIs
3. **SQLAlchemy + Psycopg2 + Alembic**: Database stack
4. **Pydantic**: Data validation throughout the application
5. **CrewAI + NLP Tools**: AI agent orchestration for advanced features

## Version Compatibility

- Python version: >=3.11,<3.13
- All dependencies are pinned to specific versions to ensure compatibility
