# Slack Integration Backend

A FastAPI-based backend service for Slack integration with the Goosebump platform.

## Features

- Slack Bot integration using Slack SDK and Bolt framework
- FastAPI REST API endpoints
- CrewAI integration for AI-powered analysis
- Supabase database integration
- Authentication and authorization
- Background task processing with Celery
- Redis for caching and message queuing

## Tech Stack

- **Framework**: FastAPI
- **AI**: CrewAI, OpenAI
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Slack**: Slack SDK, Slack Bolt
- **Authentication**: OAuth2, JWT
- **Deployment**: Docker, Google Cloud

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- Redis
- PostgreSQL (via Supabase)

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

## Environment Variables

- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_SIGNING_SECRET`: Your Slack app signing secret
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `OPENAI_API_KEY`: OpenAI API key
- `REDIS_URL`: Redis connection URL

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.

## Development

### Code Quality

- **Formatting**: Black
- **Import Sorting**: isort
- **Linting**: Flake8
- **Type Checking**: MyPy
- **Testing**: Pytest

Run all checks:
```bash
poetry run black .
poetry run isort .
poetry run flake8 .
poetry run mypy .
poetry run pytest
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
poetry run pre-commit install
```

## License

MIT License
