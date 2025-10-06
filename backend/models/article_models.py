"""
Article Models

Pydantic models for article generation system following the database schema
and API requirements from the goosebump-crew implementation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator
import json


class ArticleRequest(BaseModel):
    """Request model for article research brief generation"""
    keyword: str = Field(..., description="Target keyword for the article", min_length=1, max_length=500)
    location: str = Field(..., description="Target location for the article", min_length=1, max_length=200)
    goal: str = Field(..., description="Goal of the article", min_length=1, max_length=500)
    company_id: Optional[UUID] = Field(None, description="Company ID for brand association")
    user_id: Optional[UUID] = Field(None, description="User ID to associate the article with")
    url: Optional[str] = Field(None, description="Optional URL for the agent to process", max_length=2000)
    selected_title: Optional[str] = Field(None, description="Optional selected title for the article", max_length=500)

    @validator('keyword', 'location', 'goal')
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip()

    @validator('url')
    def validate_url(cls, v):
        if v and not v.strip():
            return None
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip() if v else None


class ResearchBrief(BaseModel):
    """Research brief model containing the generated brief and metadata"""
    keyword: str = Field(..., description="Target keyword")
    location: str = Field(..., description="Target location")
    goal: str = Field(..., description="Article goal")
    research_brief: Optional[str] = Field(None, description="Generated research brief content")
    research_brief_with_brandtone: Optional[str] = Field(None, description="Research brief adapted with brand tone")
    token_usage: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Token usage information")
    company_id: Optional[UUID] = Field(None, description="Company ID")
    uid: Optional[UUID] = Field(None, description="User ID")
    url: Optional[str] = Field(None, description="URL processed")
    selected_title: Optional[str] = Field(None, description="Selected title")

    @validator('token_usage')
    def validate_token_usage(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            return json.dumps(v)
        if isinstance(v, str):
            try:
                json.loads(v)  # Validate it's valid JSON
                return v
            except json.JSONDecodeError:
                raise ValueError('token_usage must be valid JSON string or dict')
        return str(v)


class ArticleResponse(BaseModel):
    """Response model for article operations"""
    status: str = Field(..., description="Status of the operation (success/error)")
    message: str = Field(..., description="Status message")
    article_id: Optional[int] = Field(None, description="ID of the created/updated article")
    content: Optional[str] = Field(None, description="Generated content")
    research_brief: Optional[str] = Field(None, description="Research brief content")
    research_brief_with_brandtone: Optional[str] = Field(None, description="Brand-adapted research brief")
    token_usage: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Token usage information")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    word_count: Optional[int] = Field(None, description="Word count of generated content")


class ArticleRecord(BaseModel):
    """Complete article record model matching database schema"""
    id: Optional[int] = Field(None, description="Article ID")
    keyword: Optional[str] = Field(None, description="Target keyword")
    location: Optional[str] = Field(None, description="Target location")
    goal: str = Field(..., description="Article goal")
    content: str = Field(..., description="Article content")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    token_usage: Optional[str] = Field(None, description="Token usage JSON")
    uid: Optional[UUID] = Field(None, description="User ID")
    research_brief: Optional[str] = Field(None, description="Research brief content")
    company_id: Optional[UUID] = Field(None, description="Company ID")
    shopify_article_id: Optional[str] = Field(None, description="Shopify article ID")
    research_brief_with_brandtone: Optional[str] = Field(None, description="Brand-adapted research brief")
    article_type_id: Optional[int] = Field(None, description="Article type ID")
    title: Optional[str] = Field(None, description="Article title")
    product_name: Optional[str] = Field(None, description="Product name")
    product_url_1: Optional[str] = Field(None, description="Product URL 1")
    product_url_2: Optional[str] = Field(None, description="Product URL 2")
    product_url_3: Optional[str] = Field(None, description="Product URL 3")
    description: Optional[str] = Field(None, description="Article description")
    topic: Optional[str] = Field(None, description="Article topic")
    content_idea: Optional[str] = Field(None, description="Content idea")
    product_keyword: Optional[str] = Field(None, description="Product keyword")
    media_context: Optional[str] = Field(None, description="Media context")
    publication_url: Optional[str] = Field(None, description="Publication URL")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class ArticleListResponse(BaseModel):
    """Response model for listing articles"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Status message")
    data: List[ArticleRecord] = Field(..., description="List of articles")
    count: int = Field(..., description="Number of articles returned")


class ResearchBriefResponse(BaseModel):
    """Response model for research brief operations"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Status message")
    data: Optional[ArticleRecord] = Field(None, description="Article record data")


class ArticleGenerationRequest(BaseModel):
    """Request model for article generation from research brief"""
    article_id: int = Field(..., description="ID of the article with research brief", gt=0)


class ArticleGenerationResponse(BaseModel):
    """Response model for article generation"""
    status: str = Field(..., description="Status of the operation (success/error)")
    message: str = Field(..., description="Status message")
    article_id: Optional[int] = Field(None, description="ID of the article")
    content: Optional[str] = Field(None, description="Generated article content")
    title: Optional[str] = Field(None, description="Generated article title")
    word_count: Optional[int] = Field(None, description="Word count of generated content")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class ScrapedContent(BaseModel):
    """Model for scraped web content"""
    url: str = Field(..., description="Original URL")
    final_url: str = Field(..., description="Final URL after redirects")
    title: Optional[str] = Field(None, description="Page title")
    h1: Optional[str] = Field(None, description="Main heading")
    headings: List[Dict[str, str]] = Field(default_factory=list, description="All headings with levels")
    content: Optional[str] = Field(None, description="Main content")


class ScrapeRequest(BaseModel):
    """Request model for web scraping"""
    url: str = Field(..., description="URL to scrape", min_length=1)
    use_playwright_fallback: bool = Field(False, description="Whether to use Playwright fallback")

    @validator('url')
    def validate_url(cls, v):
        if not v.strip():
            raise ValueError('URL cannot be empty')
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.strip()


class ScrapeResponse(BaseModel):
    """Response model for web scraping"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Status message")
    data: Optional[ScrapedContent] = Field(None, description="Scraped content data")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


# Token usage models for better structure
class TokenUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: Optional[int] = Field(None, description="Number of prompt tokens")
    completion_tokens: Optional[int] = Field(None, description="Number of completion tokens")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens")
    model: Optional[str] = Field(None, description="Model used")
    cost: Optional[float] = Field(None, description="Estimated cost")

    def to_json_string(self) -> str:
        """Convert to JSON string for database storage"""
        return self.model_dump_json(exclude_none=True)

    @classmethod
    def from_json_string(cls, json_str: str) -> 'TokenUsage':
        """Create from JSON string"""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls()


# Update request for research brief with brand tone
class ResearchBriefUpdateRequest(BaseModel):
    """Request model for updating research brief with brand tone"""
    research_brief_with_brandtone: str = Field(..., description="Brand-adapted research brief", min_length=1)

    @validator('research_brief_with_brandtone')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Research brief with brand tone cannot be empty')
        return v.strip()


# Health check response
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field("1.0.0", description="API version")
