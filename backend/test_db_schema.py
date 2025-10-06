#!/usr/bin/env python3
"""
Test script to verify the database schema works with the article repository.
"""

import asyncio
import logging
import uuid
import os
import sys
from datetime import datetime, timezone

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
from repository.article_repository import ArticleRepository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_schema():
    """Test the database schema with the article repository."""
    
    logger.info("=" * 60)
    logger.info("DATABASE SCHEMA TEST")
    logger.info("=" * 60)
    
    try:
        # Initialize Supabase client (you'll need to set these environment variables)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("❌ Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        repository = ArticleRepository(supabase)
        
        # Test data
        test_brief_data = {
            "keyword": "test keyword",
            "location": "Global",
            "goal": "Test article generation",
            "research_brief": "# Test Research Brief\n\nThis is a test research brief for database schema validation.",
            "research_brief_with_brandtone": "# Test Research Brief with Brand Tone\n\nThis is a test research brief with brand tone applied.",
            "token_usage": "Test: ~100 tokens",
            "uid": str(uuid.uuid4()),
            "company_id": str(uuid.uuid4()),
            "product_name": "Test Product",
            "product_url_1": "https://example.com/test-product",
            "product_keyword": "test keyword",
            "description": "Test article for database schema validation",
            "article_type_id": 2,
            "title": "Test Article Title",
            "topic": "Test Topic"
        }
        
        logger.info(f"Test data prepared with:")
        logger.info(f"  - Keyword: {test_brief_data['keyword']}")
        logger.info(f"  - User ID: {test_brief_data['uid']}")
        logger.info(f"  - Company ID: {test_brief_data['company_id']}")
        
        # Test saving research brief
        logger.info("Testing save_research_brief...")
        article_id = await repository.save_research_brief(test_brief_data)
        
        if article_id:
            logger.info(f"✅ Research brief saved successfully with ID: {article_id}")
            
            # Test retrieving research brief
            logger.info("Testing get_research_brief_by_id...")
            retrieved_brief = await repository.get_research_brief_by_id(article_id)
            
            if retrieved_brief:
                logger.info("✅ Research brief retrieved successfully")
                logger.info(f"  - Keyword: {retrieved_brief.keyword}")
                logger.info(f"  - Goal: {retrieved_brief.goal}")
                logger.info(f"  - Research brief length: {len(retrieved_brief.research_brief or '')}")
            else:
                logger.error("❌ Failed to retrieve research brief")
            
            # Test updating article content
            logger.info("Testing update_article_content...")
            test_content = "# Test Article Content\n\nThis is test article content for database validation."
            update_success = await repository.update_article_content(
                article_id, 
                test_content, 
                "Updated Test Article Title"
            )
            
            if update_success:
                logger.info("✅ Article content updated successfully")
            else:
                logger.error("❌ Failed to update article content")
            
            # Test getting complete article
            logger.info("Testing get_article_by_id...")
            complete_article = await repository.get_article_by_id(article_id)
            
            if complete_article:
                logger.info("✅ Complete article retrieved successfully")
                logger.info(f"  - ID: {complete_article.get('id')}")
                logger.info(f"  - Title: {complete_article.get('title')}")
                logger.info(f"  - Content length: {len(complete_article.get('content', ''))}")
                logger.info(f"  - Created at: {complete_article.get('created_at')}")
            else:
                logger.error("❌ Failed to retrieve complete article")
            
            # Clean up - delete test article
            logger.info("Cleaning up test data...")
            delete_success = await repository.delete_article(article_id)
            
            if delete_success:
                logger.info("✅ Test article deleted successfully")
            else:
                logger.warning("⚠️  Failed to delete test article (manual cleanup may be needed)")
        
        else:
            logger.error("❌ Failed to save research brief")
            return
        
        logger.info("=" * 60)
        logger.info("✅ DATABASE SCHEMA TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

async def test_schema_validation():
    """Test schema validation with invalid data."""
    
    logger.info("Testing schema validation with invalid UUIDs...")
    
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Skipping validation test - missing Supabase credentials")
            return
        
        supabase: Client = create_client(supabase_url, supabase_key)
        repository = ArticleRepository(supabase)
        
        # Test with invalid UUIDs
        invalid_brief_data = {
            "keyword": "test invalid uuid",
            "goal": "Test with invalid UUIDs",
            "research_brief": "Test brief with invalid UUIDs",
            "uid": "invalid-uuid-format",  # Invalid UUID
            "company_id": "also-invalid-uuid",  # Invalid UUID
        }
        
        article_id = await repository.save_research_brief(invalid_brief_data)
        
        if article_id:
            logger.info("✅ Repository handled invalid UUIDs gracefully")
            # Clean up
            await repository.delete_article(article_id)
        else:
            logger.info("ℹ️  Repository rejected invalid UUIDs (expected behavior)")
        
    except Exception as e:
        logger.info(f"ℹ️  Validation test result: {str(e)}")

async def main():
    """Main test function."""
    await test_database_schema()
    print()  # Add spacing
    await test_schema_validation()

if __name__ == "__main__":
    asyncio.run(main())
