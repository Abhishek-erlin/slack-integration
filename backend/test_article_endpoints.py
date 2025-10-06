"""
Test Article API Endpoints

Simple test script to validate the article generation API endpoints
matching the exact request/response format from the screenshots.
"""

import asyncio
import json
import logging
from typing import Dict, Any
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Base URL
BASE_URL = "http://localhost:8000"

# Test data matching the screenshot format
TEST_REQUEST_DATA = {
    "keyword": "pet food",
    "location": "New York",
    "goal": "Increase awareness of premium pet food options",
    "company_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "987fcdeb-51d2-43a1-b123-456789abcdef",
    "url": "https://example.com/pet-food-guide",
    "selected_title": "Ultimate Guide to Premium Pet Food"
}


async def test_health_endpoint():
    """Test the health endpoint"""
    logger.info("🔍 Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            logger.info(f"Health Status Code: {response.status_code}")
            logger.info(f"Health Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


async def test_article_health_endpoint():
    """Test the article service health endpoint"""
    logger.info("🔍 Testing article health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/articles/health")
            logger.info(f"Article Health Status Code: {response.status_code}")
            logger.info(f"Article Health Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Article health check failed: {str(e)}")
            return False


async def test_research_brief_endpoint():
    """Test the research brief generation endpoint (Screenshot 1)"""
    logger.info("🚀 Testing research brief generation endpoint...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/articles/research-brief",
                json=TEST_REQUEST_DATA
            )
            
            logger.info(f"Research Brief Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Research Brief Generation Successful!")
                logger.info(f"Article ID: {data.get('article_id')}")
                logger.info(f"Status: {data.get('status')}")
                logger.info(f"Message: {data.get('message')}")
                logger.info(f"Research Brief Length: {len(data.get('research_brief', ''))}")
                logger.info(f"Brand Tone Brief Length: {len(data.get('research_brief_with_brandtone', ''))}")
                
                return data.get('article_id')
            else:
                logger.error(f"❌ Research Brief Generation Failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Research Brief Generation Error: {str(e)}")
            return None


async def test_article_generation_endpoint(article_id: int):
    """Test the article generation endpoint (Screenshot 2)"""
    logger.info(f"📝 Testing article generation endpoint for article_id: {article_id}...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/articles/generate/{article_id}"
            )
            
            logger.info(f"Article Generation Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Article Generation Successful!")
                logger.info(f"Article ID: {data.get('article_id')}")
                logger.info(f"Status: {data.get('status')}")
                logger.info(f"Message: {data.get('message')}")
                logger.info(f"Content Length: {len(data.get('content', ''))}")
                logger.info(f"Word Count: {data.get('word_count')}")
                logger.info(f"Processing Time: {data.get('processing_time')} seconds")
                
                return True
            else:
                logger.error(f"❌ Article Generation Failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Article Generation Error: {str(e)}")
            return False


async def test_get_research_brief(article_id: int):
    """Test getting research brief by ID"""
    logger.info(f"📖 Testing get research brief endpoint for article_id: {article_id}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/articles/brief/{article_id}"
            )
            
            logger.info(f"Get Research Brief Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Get Research Brief Successful!")
                logger.info(f"Status: {data.get('status')}")
                logger.info(f"Message: {data.get('message')}")
                
                article_data = data.get('data', {})
                logger.info(f"Article ID: {article_data.get('id')}")
                logger.info(f"Keyword: {article_data.get('keyword')}")
                logger.info(f"Location: {article_data.get('location')}")
                logger.info(f"Goal: {article_data.get('goal')}")
                
                return True
            else:
                logger.error(f"❌ Get Research Brief Failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Get Research Brief Error: {str(e)}")
            return False


async def test_scrape_endpoint():
    """Test the URL scraping endpoint"""
    logger.info("🌐 Testing URL scraping endpoint...")
    
    scrape_data = {
        "url": "https://example.com",
        "use_playwright_fallback": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/articles/scrape",
                json=scrape_data
            )
            
            logger.info(f"Scrape Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ URL Scraping Successful!")
                logger.info(f"Status: {data.get('status')}")
                logger.info(f"Processing Time: {data.get('processing_time')} seconds")
                
                scraped_data = data.get('data', {})
                logger.info(f"Title: {scraped_data.get('title')}")
                logger.info(f"Content Length: {len(scraped_data.get('content', ''))}")
                
                return True
            else:
                logger.error(f"❌ URL Scraping Failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ URL Scraping Error: {str(e)}")
            return False


async def run_comprehensive_test():
    """Run comprehensive test of all endpoints"""
    logger.info("🎯 Starting Comprehensive Article API Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Health checks
    logger.info("1️⃣ Testing Health Endpoints...")
    health_ok = await test_health_endpoint()
    article_health_ok = await test_article_health_endpoint()
    
    if not health_ok:
        logger.error("❌ Main health check failed. Is the server running?")
        return
    
    if not article_health_ok:
        logger.error("❌ Article health check failed. Check article service configuration.")
        return
    
    logger.info("✅ All health checks passed!")
    logger.info("-" * 40)
    
    # Test 2: Research Brief Generation (Screenshot 1)
    logger.info("2️⃣ Testing Research Brief Generation (Screenshot 1)...")
    article_id = await test_research_brief_endpoint()
    
    if not article_id:
        logger.error("❌ Research brief generation failed. Cannot proceed with article generation.")
        return
    
    logger.info(f"✅ Research brief generated successfully! Article ID: {article_id}")
    logger.info("-" * 40)
    
    # Test 3: Get Research Brief
    logger.info("3️⃣ Testing Get Research Brief...")
    get_brief_ok = await test_get_research_brief(article_id)
    
    if get_brief_ok:
        logger.info("✅ Get research brief successful!")
    else:
        logger.warning("⚠️ Get research brief failed, but continuing with tests...")
    
    logger.info("-" * 40)
    
    # Test 4: Article Generation (Screenshot 2)
    logger.info("4️⃣ Testing Article Generation (Screenshot 2)...")
    article_gen_ok = await test_article_generation_endpoint(article_id)
    
    if article_gen_ok:
        logger.info("✅ Article generation successful!")
    else:
        logger.error("❌ Article generation failed.")
    
    logger.info("-" * 40)
    
    # Test 5: URL Scraping
    logger.info("5️⃣ Testing URL Scraping...")
    scrape_ok = await test_scrape_endpoint()
    
    if scrape_ok:
        logger.info("✅ URL scraping successful!")
    else:
        logger.warning("⚠️ URL scraping failed, but this is optional functionality.")
    
    logger.info("=" * 60)
    logger.info("🎉 Test Suite Complete!")
    
    # Summary
    results = {
        "Health Check": "✅" if health_ok else "❌",
        "Article Health": "✅" if article_health_ok else "❌",
        "Research Brief": "✅" if article_id else "❌",
        "Get Brief": "✅" if get_brief_ok else "❌",
        "Article Generation": "✅" if article_gen_ok else "❌",
        "URL Scraping": "✅" if scrape_ok else "❌"
    }
    
    logger.info("📊 Test Results Summary:")
    for test_name, result in results.items():
        logger.info(f"   {test_name}: {result}")
    
    # Check if core functionality works (matching screenshots)
    core_working = article_id and article_gen_ok
    if core_working:
        logger.info("🎯 CORE FUNCTIONALITY: ✅ Working! Both screenshot endpoints are functional.")
    else:
        logger.error("🎯 CORE FUNCTIONALITY: ❌ Failed! Check the implementation.")


if __name__ == "__main__":
    print("🚀 Article API Test Suite")
    print("=" * 50)
    print("This script tests the article generation API endpoints")
    print("matching the exact format from the provided screenshots.")
    print("=" * 50)
    print()
    
    # Run the test suite
    asyncio.run(run_comprehensive_test())
