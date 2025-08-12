"""
Main FastAPI application for Slack OAuth integration.
Following the 3-layer architecture pattern from Goosebump Crew.
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import sys
from logging.handlers import RotatingFileHandler
import pathlib
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Import routes
from routes.slack_routes import router as slack_router

# Import services for dependency injection
from services.slack_service import SlackService
from repository.slack_repository import SlackRepository

# Track active services that need cleanup
_services_to_cleanup = set()

# Create logs directory if it doesn't exist
logs_dir = pathlib.Path('logs')
logs_dir.mkdir(exist_ok=True)

# Configure logging with file handler
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler for all logs
file_handler = RotatingFileHandler(
    logs_dir / 'slack_integration.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)
logger.info("Starting Slack Integration API")

# Test log entry to verify file logging
logger.warning("TEST LOG ENTRY - If you can see this in the log file, logging is working correctly!")

# Define lifespan context manager for resource cleanup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Slack Integration API...")
    
    # Validate required environment variables
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SLACK_CLIENT_ID",
        "SLACK_CLIENT_SECRET",
        "SLACK_REDIRECT_URI"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("Environment variables validated successfully")
    logger.info("Slack Integration API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Slack Integration API...")
    
    # Cleanup any active services
    for service in _services_to_cleanup:
        try:
            if hasattr(service, 'cleanup'):
                await service.cleanup()
        except Exception as e:
            logger.error(f"Error during service cleanup: {e}")
    
    logger.info("Slack Integration API shutdown complete")

app = FastAPI(
    title="Slack Integration API",
    description="REST API for Slack OAuth integration with 3-layer architecture pattern",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Load environment variables
load_dotenv()

def get_cors_origins():
    """Get CORS origins from environment variables."""
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
    return [origin.strip() for origin in cors_origins.split(",")]

# Use the function to get origins
origins = get_cors_origins() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(slack_router, prefix="/api/v1/slack", tags=["slack"])

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Slack Integration API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API and database connection"""
    try:
        # Test Slack service initialization
        slack_service = SlackService()
        
        # Test repository connection
        repository = SlackRepository()
        
        return {
            "status": "healthy",
            "service": "slack-integration-api",
            "version": "1.0.0",
            "components": {
                "slack_service": "operational",
                "database": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "slack-integration-api",
            "version": "1.0.0",
            "error": str(e)
        }
