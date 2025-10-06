#!/usr/bin/env python3
"""
Test script for the simplified article generation API.
Tests the new schema with only 4 required parameters: keyword, url, company_id, user_id
"""

import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_article_generation_api():
    """Test the article generation API with simplified schema."""
    
    # API endpoint
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/articles/research-brief"
    
    # Test data using the simplified schema with proper UUIDs
    import uuid
    test_data = {
        "keyword": "sustainable energy solutions",
        "url": "https://example.com/energy-solutions",
        "company_id": str(uuid.uuid4()),  # Generate a proper UUID
        "user_id": str(uuid.uuid4())      # Generate a proper UUID
    }
    
    logger.info("Testing Article Generation API with simplified schema")
    logger.info(f"Endpoint: {endpoint}")
    logger.info(f"Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test research brief generation
            logger.info("Sending POST request to generate research brief...")
            
            async with session.post(
                endpoint,
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Research brief generation successful!")
                    logger.info(f"Article ID: {result.get('article_id')}")
                    logger.info(f"Success: {result.get('success')}")
                    logger.info(f"Processing time: {result.get('processing_time'):.2f}s")
                    logger.info(f"Scraped data quality: {result.get('scraped_data_quality')}")
                    
                    # Check brief content
                    brief = result.get('brief', {})
                    if brief:
                        logger.info(f"Research summary length: {len(brief.get('research_summary', ''))}")
                        logger.info(f"Confidence score: {brief.get('confidence_score')}")
                        logger.info("Brief content preview:")
                        logger.info(brief.get('research_summary', '')[:200] + "...")
                    
                    # Test article generation if we got an article_id
                    article_id = result.get('article_id')
                    if article_id:
                        await test_article_generation(session, base_url, article_id)
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Request failed with status {response.status}")
                    logger.error(f"Error response: {error_text}")
                    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Network error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")

async def test_article_generation(session, base_url, article_id):
    """Test full article generation from research brief."""
    
    endpoint = f"{base_url}/api/v1/articles/generate/{article_id}"
    logger.info(f"Testing article generation for article_id: {article_id}")
    
    try:
        async with session.post(endpoint) as response:
            logger.info(f"Article generation response status: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                logger.info("✅ Article generation successful!")
                logger.info(f"Status: {result.get('status')}")
                logger.info(f"Word count: {result.get('word_count')}")
                logger.info(f"Processing time: {result.get('processing_time'):.2f}s")
                
                content = result.get('content', '')
                if content:
                    logger.info("Article content preview:")
                    logger.info(content[:300] + "...")
            else:
                error_text = await response.text()
                logger.error(f"❌ Article generation failed: {error_text}")
                
    except Exception as e:
        logger.error(f"❌ Article generation error: {str(e)}")

async def test_health_check():
    """Test the health check endpoint."""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/articles/health"
    
    logger.info("Testing health check endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                logger.info(f"Health check status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    logger.info("✅ Health check successful!")
                    logger.info(f"Service status: {result.get('status')}")
                    logger.info(f"Service: {result.get('service')}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Health check failed: {error_text}")
                    
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")

async def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("ARTICLE GENERATION API TEST")
    logger.info("Testing simplified schema: keyword, url, company_id, user_id")
    logger.info("=" * 60)
    
    # Test health check first
    await test_health_check()
    
    print()  # Add spacing
    
    # Test main API
    await test_article_generation_api()
    
    logger.info("=" * 60)
    logger.info("TEST COMPLETED")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
