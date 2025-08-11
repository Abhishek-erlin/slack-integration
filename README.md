# Slack Integration Platform

A comprehensive Slack integration platform built with FastAPI backend and Next.js frontend, designed to work seamlessly with the Goosebump ecosystem.

## Project Structure

```
slack-integration/
├── backend/                 # FastAPI backend service
│   ├── app/                # Application code
│   ├── tests/              # Test files
│   ├── pyproject.toml      # Python dependencies
│   └── README.md           # Backend documentation
├── frontend/               # Next.js frontend application
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── README.md           # Frontend documentation
└── README.md               # This file
```

## Features

### Backend
- **FastAPI REST API** with automatic OpenAPI documentation
- **Slack Bot Integration** using Slack SDK and Bolt framework
- **CrewAI Integration** for AI-powered analysis and automation
- **Supabase Database** with PostgreSQL and real-time subscriptions
- **Authentication & Authorization** with JWT and OAuth2
- **Background Tasks** with Celery and Redis
- **Comprehensive Testing** with Pytest
- **Code Quality Tools** (Black, isort, Flake8, MyPy)

### Frontend
- **Next.js 14** with App Router and Server Components
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** component library
- **TanStack Query** for data fetching and caching
- **Supabase Integration** for authentication and real-time data
- **Framer Motion** for animations
- **React Hook Form** with Zod validation

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **AI**: CrewAI, OpenAI
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **Slack**: Slack SDK, Slack Bolt
- **Authentication**: OAuth2, JWT
- **Testing**: Pytest
- **Code Quality**: Black, isort, Flake8, MyPy

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui, Radix UI
- **State Management**: Zustand, TanStack Query
- **Authentication**: Supabase Auth
- **Forms**: React Hook Form + Zod
- **Animation**: Framer Motion

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Poetry (for Python dependency management)
- Redis
- PostgreSQL (via Supabase)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Environment Variables

### Backend (.env)
- `SLACK_BOT_TOKEN`: Your Slack bot token
- `SLACK_SIGNING_SECRET`: Your Slack app signing secret
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `OPENAI_API_KEY`: OpenAI API key
- `REDIS_URL`: Redis connection URL

### Frontend (.env.local)
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anon key
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Development

### Code Quality (Backend)
```bash
# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run flake8 .
poetry run mypy .

# Run tests
poetry run pytest
```

### Code Quality (Frontend)
```bash
# Lint code
npm run lint

# Type check
npm run type-check

# Build
npm run build
```

## Architecture

This project follows the same architectural patterns as the Goosebump Crew project:

- **Layered Architecture** with Service-Repository pattern
- **FastAPI** with dependency injection
- **CrewAI** for multi-agent AI analysis
- **Supabase** with Row Level Security (RLS)
- **Next.js App Router** with Server Components
- **TanStack Query** for efficient data fetching and caching

## Contributing

1. Follow the established code quality standards
2. Write tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## License

MIT License
