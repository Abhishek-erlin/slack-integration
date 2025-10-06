"""
Article Routes

FastAPI routes for article generation system following the 3-layer architecture.
Handles HTTP requests and responses for the article generation workflow.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Body, Path, Query
from pydantic import BaseModel, Field

from models.article_models import (
    ArticleRequest, ArticleResponse, ArticleGenerationResponse, 
    ScrapeRequest, ScrapeResponse, ResearchBriefUpdateRequest,
    ArticleListResponse, ResearchBriefResponse, HealthResponse
)
from services.article_service import ArticleService
from repository.article_repository import ArticleRepository

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/articles",
    tags=["articles"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Dependency injection setup
def get_article_repository():
    """Dependency to get ArticleRepository instance"""
    from utils.database import get_database_service
    db_service = get_database_service()
    return ArticleRepository(db_service.supabase)

def get_article_service(repository: ArticleRepository = Depends(get_article_repository)):
    """Dependency to get ArticleService instance"""
    return ArticleService(repository)


@router.post("/research-brief", 
          summary="Generate research brief for article",
          description="Generate a research brief for an article based on keyword, location, goal, and optional parameters",
          response_description="Research brief generation result with ID and brief content",
          response_model=ArticleResponse,
          status_code=200,
          responses={
              200: {
                  "description": "Successful generation",
                  "content": {
                      "application/json": {
                          "example": {
                              "status": "success", 
                              "message": "Research brief generated successfully",
                              "article_id": 1,
                              "research_brief": "Detailed research brief content...",
                              "research_brief_with_brandtone": "Brand-adapted research brief...",
                              "token_usage": {"prompt_tokens": 1200, "completion_tokens": 800}
                          }
                      }
                  }
              },
              400: {
                  "description": "Invalid request parameters",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Invalid keyword or location provided"
                          }
                      }
                  }
              },
              500: {
                  "description": "Generation failed",
                  "content": {
                      "application/json": {
                          "example": {
                              "detail": "Failed to generate research brief"
                          }
                      }
                  }
              }
          })
async def generate_research_brief(
    request: ArticleRequest = Body(..., 
        example={
            "keyword": "pet food",
            "location": "New York", 
            "goal": "Increase awareness of premium pet food options",
            "company_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "987fcdeb-51d2-43a1-b123-456789abcdef",
            "url": "https://example.com/pet-food-guide",
            "selected_title": "Ultimate Guide to Premium Pet Food"
        }
    ), 
    service: ArticleService = Depends(get_article_service)
) -> ArticleResponse:
    """
    Generate a research brief for an article based on keyword, location, and goal.
    
    This endpoint runs the research brief agent and creates a new record in the articles table with the generated brief.
    
    Args:
        request: The request body containing the keyword, location, goal, and optional parameters
        service: Injected ArticleService instance
        
    Returns:
        ArticleResponse with the generation result
    """
    try:
        logger.info(f"Received request to generate research brief for keyword: {request.keyword}, location: {request.location}")
        
        # Call the service method to generate the research brief
        result = await service.generate_research_brief(
            keyword=request.keyword,
            location=request.location,
            goal=request.goal,
            company_id=request.company_id,
            url=request.url,
            user_id=request.user_id,
            selected_title=request.selected_title
        )
        
        # Check if generation was successful
        if result.get("status") == "error":
            logger.error(f"Error generating research brief: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully generated research brief with ID: {result.get('article_id')}")
        
        # Return structured response
        return ArticleResponse(
            status=result.get("status"),
            message=result.get("message"),
            article_id=result.get("article_id"),
            research_brief=result.get("research_brief"),
            research_brief_with_brandtone=result.get("research_brief_with_brandtone"),
            token_usage=result.get("token_usage")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating research brief: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/{article_id}",
    summary="Generate article from research brief",
    description="Generate a full article using the research brief for the given article_id.",
    response_description="Generated article content and status",
    response_model=ArticleGenerationResponse,
    status_code=200,
    responses={
        200: {
            "description": "Article generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Article generated and saved successfully",
                        "article_id": 1,
                        "content": "Full generated article content...",
                        "title": "Ultimate Guide to Premium Pet Food",
                        "word_count": 1250,
                        "processing_time": 15.3
                    }
                }
            }
        },
        404: {
            "description": "Research brief not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Research brief not found"}
                }
            }
        },
        500: {
            "description": "Failed to generate article",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to generate article"}
                }
            }
        }
    }
)
async def generate_article_from_brief(
    article_id: int = Path(..., description="The ID of the article", example=1, gt=0),
    service: ArticleService = Depends(get_article_service)
) -> ArticleGenerationResponse:
    """
    Generate a full article for a given article_id using the research brief.
    
    Args:
        article_id: The ID of the article
        service: Injected ArticleService instance
        
    Returns:
        ArticleGenerationResponse with the generated article content and status
    """
    try:
        logger.info(f"Received request to generate article for article_id: {article_id}")
        result = await service.generate_article_from_brief(article_id)
        
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                logger.error(f"Research brief not found for article_id: {article_id}")
                raise HTTPException(status_code=404, detail="Research brief not found")
            else:
                logger.error(f"Error generating article: {result.get('message')}")
                raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully generated article for article_id: {article_id}")
        
        # Return structured response
        return ArticleGenerationResponse(
            status=result.get("status"),
            message=result.get("message"),
            article_id=result.get("article_id"),
            content=result.get("content"),
            title=result.get("title"),
            word_count=result.get("word_count"),
            processing_time=result.get("processing_time")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating article: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brief/{article_id}",
         summary="Get research brief by ID",
         description="Retrieve a research brief by its ID",
         response_description="Research brief data",
         response_model=ResearchBriefResponse,
         status_code=200,
         responses={
             200: {
                 "description": "Research brief retrieved successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "status": "success",
                             "message": "Research brief fetched successfully",
                             "data": {
                                 "id": 1,
                                 "keyword": "pet food",
                                 "location": "New York",
                                 "goal": "Educate and Guide Customers",
                                 "research_brief": "Detailed research brief content...",
                                 "research_brief_with_brandtone": "Brand-adapted research brief...",
                                 "token_usage": "{\"prompt_tokens\": 1000, \"completion_tokens\": 500}",
                                 "created_at": "2025-04-14T12:00:00.000000+00:00"
                             }
                         }
                     }
                 }
             },
             404: {
                 "description": "Research brief not found",
                 "content": {
                     "application/json": {
                         "example": {
                             "detail": "Research brief not found"
                         }
                     }
                 }
             }
         })
async def get_research_brief(
    article_id: int = Path(..., description="The ID of the article", example=1, gt=0),
    service: ArticleService = Depends(get_article_service)
) -> ResearchBriefResponse:
    """
    Get a research brief by ID.
    
    Args:
        article_id: The ID of the article
        service: Injected ArticleService instance
        
    Returns:
        ResearchBriefResponse with the research brief data
    """
    try:
        logger.info(f"Received request to fetch research brief with ID: {article_id}")
        
        # Call the service method to get the research brief
        result = await service.get_research_brief(article_id)
        
        # Check if fetching was successful
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                logger.error(f"Research brief not found with ID: {article_id}")
                raise HTTPException(status_code=404, detail="Research brief not found")
            else:
                logger.error(f"Error fetching research brief: {result.get('message')}")
                raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully fetched research brief with ID: {article_id}")
        
        # Return structured response
        return ResearchBriefResponse(
            status=result.get("status"),
            message=result.get("message"),
            data=result.get("data")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Error fetching research brief: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/article/{article_id}",
         summary="Get complete article by ID",
         description="Retrieve a complete article by its ID",
         response_description="Complete article data",
         response_model=ResearchBriefResponse,
         status_code=200)
async def get_article(
    article_id: int = Path(..., description="The ID of the article", example=1, gt=0),
    service: ArticleService = Depends(get_article_service)
) -> ResearchBriefResponse:
    """
    Get a complete article by ID.
    
    Args:
        article_id: The ID of the article
        service: Injected ArticleService instance
        
    Returns:
        ResearchBriefResponse with the complete article data
    """
    try:
        logger.info(f"Received request to fetch article with ID: {article_id}")
        
        # Use the same method as research brief since it returns complete article data
        result = await service.get_research_brief(article_id)
        
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                logger.error(f"Article not found with ID: {article_id}")
                raise HTTPException(status_code=404, detail="Article not found")
            else:
                logger.error(f"Error fetching article: {result.get('message')}")
                raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully fetched article with ID: {article_id}")
        
        return ResearchBriefResponse(
            status=result.get("status"),
            message=result.get("message"),
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error fetching article: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/user/{user_id}",
         summary="Get articles by user ID",
         description="Retrieve all articles associated with a user ID",
         response_description="List of articles for the user",
         response_model=ArticleListResponse,
         status_code=200)
async def get_articles_by_user_id(
    user_id: UUID = Path(..., description="The ID of the user to fetch articles for"),
    service: ArticleService = Depends(get_article_service)
) -> ArticleListResponse:
    """
    Get all articles for a specific user ID.
    
    Args:
        user_id: The ID of the user to fetch articles for
        service: Injected ArticleService instance
        
    Returns:
        ArticleListResponse with the list of articles data
    """
    try:
        logger.info(f"Received request to fetch articles for user_id: {user_id}")
        
        # Call the service method to get articles by user ID
        result = await service.get_articles_by_user_id(str(user_id))
        
        # Check if operation was successful
        if result.get("status") == "error":
            logger.error(f"Error fetching articles: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully fetched {result.get('count', 0)} articles for user_id: {user_id}")
        
        return ArticleListResponse(
            status=result.get("status"),
            message=result.get("message"),
            data=result.get("data", []),
            count=result.get("count", 0)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching articles: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape",
          summary="Scrape content from URL",
          description="Extract content from a web page URL for article research",
          response_description="Scraped content data",
          response_model=ScrapeResponse,
          status_code=200)
async def scrape_url(
    request: ScrapeRequest = Body(..., 
        example={
            "url": "https://example.com/article",
            "use_playwright_fallback": False
        }
    ),
    service: ArticleService = Depends(get_article_service)
) -> ScrapeResponse:
    """
    Scrape content from a URL for article research purposes.
    
    Args:
        request: The scrape request containing URL and options
        service: Injected ArticleService instance
        
    Returns:
        ScrapeResponse with the scraped content
    """
    try:
        logger.info(f"Received request to scrape URL: {request.url}")
        
        # Call the service method to scrape the URL
        result = await service.scrape_url(request.url, request.use_playwright_fallback)
        
        if result.get("status") == "error":
            logger.error(f"Error scraping URL: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully scraped URL: {request.url}")
        
        return ScrapeResponse(
            status=result.get("status"),
            message=result.get("message"),
            data=result.get("data"),
            processing_time=result.get("processing_time")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error scraping URL: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/brief/{article_id}/brandtone",
          summary="Update research brief with brand tone",
          description="Update the research_brief_with_brandtone column for an article",
          response_description="Update result with success status",
          response_model=ResearchBriefResponse)
async def update_research_brief_with_brandtone(
    article_id: int = Path(..., description="The ID of the article", example=1, gt=0),
    update_data: ResearchBriefUpdateRequest = Body(...),
    service: ArticleService = Depends(get_article_service)
) -> ResearchBriefResponse:
    """
    Update the research_brief_with_brandtone column for a given article ID.
    
    Args:
        article_id: The ID of the article
        update_data: The data containing the research_brief_with_brandtone to update
        service: Injected ArticleService instance
        
    Returns:
        ResearchBriefResponse with the update result
    """
    try:
        logger.info(f"Received request to update research brief with brand tone for article_id: {article_id}")
        
        # Call the service method to update the research brief with brand tone
        result = await service.update_research_brief_with_brandtone(
            article_id=article_id,
            research_brief_with_brandtone=update_data.research_brief_with_brandtone
        )
        
        # Check if update was successful
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                logger.error(f"Article not found with ID: {article_id}")
                raise HTTPException(status_code=404, detail="Article not found")
            else:
                logger.error(f"Error updating research brief with brand tone: {result.get('message')}")
                raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully updated research brief with brand tone for article_id: {article_id}")
        
        return ResearchBriefResponse(
            status=result.get("status"),
            message=result.get("message"),
            data=result.get("data")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating research brief with brand tone: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{article_id}",
             summary="Delete article by ID",
             description="Delete an article by its ID",
             response_description="Deletion result with success status",
             status_code=200)
async def delete_article(
    article_id: int = Path(..., description="The ID of the article to delete", example=1, gt=0),
    service: ArticleService = Depends(get_article_service)
) -> Dict[str, Any]:
    """
    Delete an article by its ID.
    
    Args:
        article_id: The ID of the article to delete
        service: Injected ArticleService instance
        
    Returns:
        Dictionary with the deletion result
    """
    try:
        logger.info(f"Received request to delete article with ID: {article_id}")
        
        # Call the service method to delete the article
        result = await service.delete_article(article_id)
        
        # Check if deletion was successful
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
                logger.error(f"Article not found with ID: {article_id}")
                raise HTTPException(status_code=404, detail="Article not found")
            else:
                logger.error(f"Error deleting article: {result.get('message')}")
                raise HTTPException(status_code=500, detail=result.get("message"))
        
        logger.info(f"Successfully deleted article with ID: {article_id}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting article: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health",
         summary="Health check for article service",
         description="Check the health status of the article generation service",
         response_description="Health status",
         response_model=HealthResponse,
         status_code=200)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for the article service.
    
    Returns:
        HealthResponse with the service health status
    """
    try:
        logger.info("Article service health check requested")
        
        return HealthResponse(
            status="healthy",
            message="Article service is operational",
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service unhealthy")
