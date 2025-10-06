"""
Article Repository

Database operations for article management following the 3-layer architecture pattern.
Handles all database interactions for the article generation system.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from supabase import Client

from models.article_models import ResearchBrief, ArticleRecord, TokenUsage

# Configure logging
logger = logging.getLogger(__name__)


class ArticleRepository:
    """Repository for article database operations"""
    
    def __init__(self, supabase_client: Client):
        """Initialize with Supabase client"""
        self.supabase = supabase_client
        logger.info("ArticleRepository initialized")
    
    def save_research_brief(self, research_brief: ResearchBrief) -> Dict[str, Any]:
        """
        Save a research brief to the database
        
        Args:
            research_brief: ResearchBrief object containing the brief data
            
        Returns:
            Dictionary with the save result
        """
        try:
            logger.info(f"Saving research brief for keyword: {research_brief.keyword}")
            
            # Prepare data for insertion
            insert_data = {
                "keyword": research_brief.keyword,
                "location": research_brief.location,
                "goal": research_brief.goal,
                "research_brief": research_brief.research_brief,
                "research_brief_with_brandtone": research_brief.research_brief_with_brandtone,
                "token_usage": research_brief.token_usage,
                "content": "",  # Required field, will be filled when article is generated
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add optional fields if present
            if research_brief.company_id:
                insert_data["company_id"] = str(research_brief.company_id)
            if research_brief.uid:
                insert_data["uid"] = str(research_brief.uid)
            if research_brief.url:
                insert_data["publication_url"] = research_brief.url
            if research_brief.selected_title:
                insert_data["title"] = research_brief.selected_title
            
            # Insert into database
            result = self.supabase.table("articles").insert(insert_data).execute()
            
            if result.data and len(result.data) > 0:
                article_id = result.data[0]["id"]
                logger.info(f"Research brief saved successfully with ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Research brief saved successfully",
                    "article_id": article_id,
                    "data": result.data[0]
                }
            else:
                logger.error("No data returned from insert operation")
                return {
                    "status": "error",
                    "message": "Failed to save research brief - no data returned"
                }
                
        except Exception as e:
            error_msg = f"Error saving research brief: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_research_brief_by_id(self, article_id: int) -> Dict[str, Any]:
        """
        Get a research brief by article ID
        
        Args:
            article_id: The ID of the article
            
        Returns:
            Dictionary with the research brief data or error
        """
        try:
            logger.info(f"Fetching research brief with ID: {article_id}")
            
            # Query the database
            result = self.supabase.table("articles").select("*").eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                article_data = result.data[0]
                logger.info(f"Research brief found for ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Research brief found",
                    "data": article_data
                }
            else:
                logger.warning(f"Research brief not found for ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Research brief not found"
                }
                
        except Exception as e:
            error_msg = f"Error fetching research brief: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def update_article_content(self, article_id: int, content: str, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the article content for a given article ID
        
        Args:
            article_id: The ID of the article
            content: The generated article content
            title: Optional article title
            
        Returns:
            Dictionary with the update result
        """
        try:
            logger.info(f"Updating article content for ID: {article_id}")
            
            # Prepare update data
            update_data = {
                "content": content,
                "created_at": datetime.utcnow().isoformat()  # Update timestamp
            }
            
            if title:
                update_data["title"] = title
            
            # Update the database
            result = self.supabase.table("articles").update(update_data).eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Article content updated successfully for ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Article content updated successfully",
                    "data": result.data[0]
                }
            else:
                logger.warning(f"No article found with ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Article not found for update"
                }
                
        except Exception as e:
            error_msg = f"Error updating article content: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_articles_by_user_id(self, user_id: str) -> Dict[str, Any]:
        """
        Get all articles for a specific user ID
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dictionary with the articles data or error
        """
        try:
            logger.info(f"Fetching articles for user_id: {user_id}")
            
            # Query the database
            result = self.supabase.table("articles").select("*").eq("uid", user_id).order("created_at", desc=True).execute()
            
            articles = result.data if result.data else []
            logger.info(f"Found {len(articles)} articles for user_id: {user_id}")
            
            return {
                "status": "success",
                "message": f"Found {len(articles)} articles",
                "data": articles
            }
                
        except Exception as e:
            error_msg = f"Error fetching articles by user ID: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def update_research_brief_with_brandtone(self, article_id: int, research_brief_with_brandtone: str) -> Dict[str, Any]:
        """
        Update the research_brief_with_brandtone column for a given article ID
        
        Args:
            article_id: The ID of the article
            research_brief_with_brandtone: The brand-adapted research brief
            
        Returns:
            Dictionary with the update result
        """
        try:
            logger.info(f"Updating research brief with brand tone for ID: {article_id}")
            
            # Update the database
            result = self.supabase.table("articles").update({
                "research_brief_with_brandtone": research_brief_with_brandtone
            }).eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Research brief with brand tone updated successfully for ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Research brief with brand tone updated successfully",
                    "data": result.data[0]
                }
            else:
                logger.warning(f"No article found with ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Article not found for update"
                }
                
        except Exception as e:
            error_msg = f"Error updating research brief with brand tone: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def delete_article_by_id(self, article_id: int) -> Dict[str, Any]:
        """
        Delete an article by ID
        
        Args:
            article_id: The ID of the article to delete
            
        Returns:
            Dictionary with the deletion result
        """
        try:
            logger.info(f"Deleting article with ID: {article_id}")
            
            # Delete from database
            result = self.supabase.table("articles").delete().eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Article deleted successfully with ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Article deleted successfully",
                    "data": {"id": article_id}
                }
            else:
                logger.warning(f"No article found with ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Article not found for deletion"
                }
                
        except Exception as e:
            error_msg = f"Error deleting article: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_article_by_id(self, article_id: int) -> Dict[str, Any]:
        """
        Get a complete article by ID
        
        Args:
            article_id: The ID of the article
            
        Returns:
            Dictionary with the article data or error
        """
        try:
            logger.info(f"Fetching article with ID: {article_id}")
            
            # Query the database
            result = self.supabase.table("articles").select("*").eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                article_data = result.data[0]
                logger.info(f"Article found for ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Article found",
                    "data": article_data
                }
            else:
                logger.warning(f"Article not found for ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Article not found"
                }
                
        except Exception as e:
            error_msg = f"Error fetching article: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def update_token_usage(self, article_id: int, token_usage: TokenUsage) -> Dict[str, Any]:
        """
        Update token usage information for an article
        
        Args:
            article_id: The ID of the article
            token_usage: TokenUsage object with usage information
            
        Returns:
            Dictionary with the update result
        """
        try:
            logger.info(f"Updating token usage for article ID: {article_id}")
            
            # Convert token usage to JSON string
            token_usage_json = token_usage.to_json_string()
            
            # Update the database
            result = self.supabase.table("articles").update({
                "token_usage": token_usage_json
            }).eq("id", article_id).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Token usage updated successfully for ID: {article_id}")
                return {
                    "status": "success",
                    "message": "Token usage updated successfully",
                    "data": result.data[0]
                }
            else:
                logger.warning(f"No article found with ID: {article_id}")
                return {
                    "status": "error",
                    "message": "Article not found for token usage update"
                }
                
        except Exception as e:
            error_msg = f"Error updating token usage: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def get_articles_by_company_id(self, company_id: str) -> Dict[str, Any]:
        """
        Get all articles for a specific company ID
        
        Args:
            company_id: The ID of the company
            
        Returns:
            Dictionary with the articles data or error
        """
        try:
            logger.info(f"Fetching articles for company_id: {company_id}")
            
            # Query the database
            result = self.supabase.table("articles").select("*").eq("company_id", company_id).order("created_at", desc=True).execute()
            
            articles = result.data if result.data else []
            logger.info(f"Found {len(articles)} articles for company_id: {company_id}")
            
            return {
                "status": "success",
                "message": f"Found {len(articles)} articles",
                "data": articles
            }
                
        except Exception as e:
            error_msg = f"Error fetching articles by company ID: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
    
    def search_articles(self, keyword: Optional[str] = None, location: Optional[str] = None, 
                       goal: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Search articles by keyword, location, or goal
        
        Args:
            keyword: Optional keyword to search for
            location: Optional location to search for
            goal: Optional goal to search for
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with the search results
        """
        try:
            logger.info(f"Searching articles with keyword='{keyword}', location='{location}', goal='{goal}'")
            
            # Build query
            query = self.supabase.table("articles").select("*")
            
            if keyword:
                query = query.ilike("keyword", f"%{keyword}%")
            if location:
                query = query.ilike("location", f"%{location}%")
            if goal:
                query = query.ilike("goal", f"%{goal}%")
            
            # Execute query with limit and ordering
            result = query.order("created_at", desc=True).limit(limit).execute()
            
            articles = result.data if result.data else []
            logger.info(f"Found {len(articles)} articles matching search criteria")
            
            return {
                "status": "success",
                "message": f"Found {len(articles)} articles",
                "data": articles
            }
                
        except Exception as e:
            error_msg = f"Error searching articles: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "status": "error",
                "message": error_msg
            }
