"""
CrewAI Models

Pydantic models for CrewAI crew operations and data structures.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


class ResearchBrief(BaseModel):
    """Research brief model for article generation"""
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

    @field_validator('token_usage')
    @classmethod
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

    @staticmethod
    def model_validate_token_usage(token_usage: Any) -> Optional[str]:
        """Validate and convert token usage to JSON string"""
        if token_usage is None:
            return None
        
        if isinstance(token_usage, dict):
            return json.dumps(token_usage)
        
        if isinstance(token_usage, str):
            try:
                json.loads(token_usage)  # Validate it's valid JSON
                return token_usage
            except json.JSONDecodeError:
                # If it's not valid JSON, wrap it in a simple structure
                return json.dumps({"raw_value": token_usage})
        
        # For any other type, convert to string and wrap
        return json.dumps({"raw_value": str(token_usage)})

    model_config = ConfigDict(
        from_attributes=True,
        # Note: json_encoders is deprecated in Pydantic v2
        # Use custom serializers if needed
    )
