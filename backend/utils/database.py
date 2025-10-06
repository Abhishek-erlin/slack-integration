"""
Database Service

Database connection and service management for the Slack Integration application.
Provides Supabase client initialization and connection management.
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing database connections and operations"""
    
    _instance: Optional['DatabaseService'] = None
    _supabase_client: Optional[Client] = None
    
    def __new__(cls) -> 'DatabaseService':
        """Singleton pattern to ensure single database connection"""
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize database service"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._initialize_supabase()
    
    def _initialize_supabase(self) -> None:
        """Initialize Supabase client"""
        try:
            # Get Supabase configuration from environment variables
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                error_msg = """
❌ Missing Supabase Configuration!

Required environment variables:
- SUPABASE_URL: Your Supabase project URL (e.g., https://your-project.supabase.co)
- SUPABASE_KEY: Your Supabase anonymous key

To fix this:
1. Copy .env.example to .env: cp .env.example .env
2. Edit .env file with your Supabase credentials
3. Restart the server

Current values:
- SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}
- SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}
                """
                logger.error(error_msg)
                raise ValueError("Missing Supabase configuration. Please check environment variables.")
            
            # Create Supabase client
            self._supabase_client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    @property
    def supabase(self) -> Client:
        """Get Supabase client instance"""
        if self._supabase_client is None:
            self._initialize_supabase()
        return self._supabase_client
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Simple query to test connection
            result = self.supabase.table("articles").select("id").limit(1).execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def get_health_status(self) -> dict:
        """Get database health status"""
        try:
            is_connected = self.test_connection()
            return {
                "database": "healthy" if is_connected else "unhealthy",
                "supabase_configured": bool(self._supabase_client),
                "connection_status": "connected" if is_connected else "disconnected"
            }
        except Exception as e:
            logger.error(f"Error getting database health status: {str(e)}")
            return {
                "database": "unhealthy",
                "supabase_configured": False,
                "connection_status": "error",
                "error": str(e)
            }


# Global database service instance
_db_service = None


def get_database_service() -> DatabaseService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def get_supabase_client() -> Client:
    """Get Supabase client from global database service"""
    return get_database_service().supabase
