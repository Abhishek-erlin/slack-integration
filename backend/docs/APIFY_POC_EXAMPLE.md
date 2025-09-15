# Apify Integration POC Example

This document provides a minimal proof-of-concept implementation for integrating Apify with the Goosebump Crew backend. The code examples follow the project's 3-layer architecture pattern and can be used as a starting point for the full implementation.

## Prerequisites

1. Apify account with API token
2. Python 3.8+ with FastAPI
3. Access to the project's database

## POC Implementation

### 1. Basic Configuration

Add the following to your `.env` file:

```
# Apify settings
APIFY_API_TOKEN=your_apify_api_token
APIFY_TIMEOUT_SECS=300
```

### 2. Database Migration

Create a new migration file `migrations/add_scraping_tables.sql`:

```sql
-- Simple version for POC
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id UUID PRIMARY KEY,
    website_id UUID NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    item_count INTEGER,
    error_message TEXT,
    metadata JSONB,
    FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scraping_results (
    id UUID PRIMARY KEY,
    scraping_job_id UUID NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (scraping_job_id) REFERENCES scraping_jobs(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_scraping_jobs_website_id ON scraping_jobs(website_id);
CREATE INDEX idx_scraping_results_job_id ON scraping_results(scraping_job_id);
```

### 3. Minimal Implementation Files

#### 3.1 Models

Create `models/scraping_models.py`:

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapingRequest(BaseModel):
    website_id: str
    actor_id: str
    input_data: Dict[str, Any]
    wait_for_finish: bool = False
    timeout_secs: Optional[int] = 300

class ScrapingResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: str
```

#### 3.2 Service Layer

Create `services/apify_service.py`:

```python
from apify_client import ApifyClient
from typing import Dict, Any, List, Optional
import os
import logging
from config.config import get_settings

class ApifyService:
    def __init__(self, api_token: str = None):
        settings = get_settings()
        self.api_token = api_token or settings.apify_api_token
        if not self.api_token:
            raise ValueError("Apify API token is required")
        self.client = ApifyClient(self.api_token)
        self.logger = logging.getLogger(__name__)
    
    def run_actor(self, actor_id: str, input_data: Dict[str, Any], 
                  wait_for_finish: bool = True, timeout_secs: int = 300) -> Dict[str, Any]:
        """
        Run an Apify actor and return its results
        """
        try:
            self.logger.info(f"Starting actor {actor_id}")
            
            # Start the actor run
            run = self.client.actor(actor_id).call(
                run_input=input_data,
                wait_secs=timeout_secs if wait_for_finish else 0
            )
            
            self.logger.info(f"Actor run started with ID: {run['id']}")
            return run
            
        except Exception as e:
            self.logger.error(f"Error running actor {actor_id}: {str(e)}")
            raise
    
    def get_actor_results(self, run_id: str = None, dataset_id: str = None) -> List[Dict[str, Any]]:
        """
        Get results from an actor run
        """
        try:
            if not dataset_id and run_id:
                # Get run information to find the default dataset
                run_info = self.client.run(run_id).get()
                dataset_id = run_info.get("defaultDatasetId")
                
            if not dataset_id:
                raise ValueError("Either run_id or dataset_id must be provided")
                
            # Get items from the dataset
            items = self.client.dataset(dataset_id).list_items().items
            self.logger.info(f"Retrieved {len(items)} items from dataset {dataset_id}")
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting actor results: {str(e)}")
            raise
```

#### 3.3 Repository Layer

Create `repositories/scraping_repository.py`:

```python
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from utils.database import Database
from models.scraping_models import ScrapingStatus

class ScrapingRepository:
    def __init__(self, db: Database):
        self.db = db
        
    async def save_scraping_job(self, 
                               website_id: str, 
                               actor_id: str,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new scraping job
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        await self.db.execute(
            """
            INSERT INTO scraping_jobs (id, website_id, actor_id, created_at, 
                                      updated_at, status, metadata)
            VALUES (:id, :website_id, :actor_id, :created_at, 
                   :updated_at, :status, :metadata)
            """,
            {
                "id": job_id,
                "website_id": website_id,
                "actor_id": actor_id,
                "created_at": now,
                "updated_at": now,
                "status": ScrapingStatus.PENDING.value,
                "metadata": metadata or {}
            }
        )
        
        return job_id
        
    async def save_scraping_results(self,
                                   job_id: str,
                                   results: List[Dict[str, Any]]) -> None:
        """
        Save scraping results
        """
        now = datetime.utcnow()
        
        # Update job status
        await self.db.execute(
            """
            UPDATE scraping_jobs
            SET status = :status, item_count = :item_count, updated_at = :updated_at
            WHERE id = :job_id
            """,
            {
                "job_id": job_id,
                "status": ScrapingStatus.COMPLETED.value,
                "item_count": len(results),
                "updated_at": now
            }
        )
        
        # Insert results
        for item in results:
            item_id = str(uuid.uuid4())
            await self.db.execute(
                """
                INSERT INTO scraping_results (id, scraping_job_id, data, created_at)
                VALUES (:id, :scraping_job_id, :data, :created_at)
                """,
                {
                    "id": item_id,
                    "scraping_job_id": job_id,
                    "data": item,
                    "created_at": now
                }
            )
```

#### 3.4 API Layer

Create `api/routes/scraping_routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from models.scraping_models import ScrapingRequest, ScrapingResponse, ScrapingStatus
from services.apify_service import ApifyService
from repositories.scraping_repository import ScrapingRepository
from utils.database import get_database

router = APIRouter()

def get_apify_service():
    return ApifyService()

@router.post("/api/v1/scraping/poc", response_model=ScrapingResponse)
async def scrape_website_poc(
    request: ScrapingRequest,
    apify_service: ApifyService = Depends(get_apify_service),
    db = Depends(get_database)
):
    """
    POC endpoint for testing Apify integration
    """
    try:
        # Create repository
        scraping_repo = ScrapingRepository(db)
        
        # Create job in database
        job_id = await scraping_repo.save_scraping_job(
            website_id=request.website_id,
            actor_id=request.actor_id,
            metadata={"original_request": request.dict(exclude={"input_data"})}
        )
        
        # Run the actor
        run = apify_service.run_actor(
            actor_id=request.actor_id,
            input_data=request.input_data,
            wait_for_finish=request.wait_for_finish,
            timeout_secs=request.timeout_secs or 300
        )
        
        # If waiting for finish, get and save results
        if request.wait_for_finish:
            results = apify_service.get_actor_results(run_id=run["id"])
            await scraping_repo.save_scraping_results(job_id, results)
            
            return ScrapingResponse(
                success=True,
                job_id=job_id,
                status=ScrapingStatus.COMPLETED.value,
                message=f"Scraping completed successfully with {len(results)} items"
            )
        else:
            return ScrapingResponse(
                success=True,
                job_id=job_id,
                status=ScrapingStatus.RUNNING.value,
                message="Scraping job started successfully"
            )
            
    except Exception as e:
        return ScrapingResponse(
            success=False,
            message=f"Scraping failed: {str(e)}"
        )
```

### 4. Register the Route

Update your main application file to include the new route:

```python
# main.py or app.py
from fastapi import FastAPI
from api.routes import scraping_routes

app = FastAPI()

# Register routes
app.include_router(scraping_routes.router, tags=["scraping"])
```

### 5. Update Configuration

Update `config/config.py` to include Apify settings:

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Apify settings
    apify_api_token: str = ""
    apify_timeout_secs: int = 300
    
    class Config:
        env_file = ".env"
```

## Testing the POC

### 1. Install Dependencies

```bash
pip install apify-client
```

Or update your `pyproject.toml`:

```toml
[tool.poetry.dependencies]
apify-client = "^1.1.0"
```

### 2. Run Database Migration

Apply the migration to create the necessary tables.

### 3. Test with a Simple Actor

Use the following curl command or test via Swagger UI:

```bash
curl -X POST "http://localhost:8000/api/v1/scraping/poc" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": "123e4567-e89b-12d3-a456-426614174000",
    "actor_id": "apify/web-scraper",
    "input_data": {
      "startUrls": [{"url": "https://example.com"}],
      "pseudoUrls": [{"purl": "https://example.com/[.*]"}],
      "linkSelector": "a",
      "pageFunction": "({ window, document }) => { return { title: document.title, url: window.location.href } }"
    },
    "wait_for_finish": true,
    "timeout_secs": 60
  }'
```

## Example Actor Configurations

### Web Scraper

```json
{
  "startUrls": [{"url": "https://example.com"}],
  "pseudoUrls": [{"purl": "https://example.com/[.*]"}],
  "linkSelector": "a",
  "pageFunction": "async function pageFunction({ request, page }) { return { url: request.url, title: await page.title() }; }"
}
```

### Cheerio Scraper (Lightweight)

```json
{
  "startUrls": [{"url": "https://example.com"}],
  "pseudoUrls": [{"purl": "https://example.com/[.*]"}],
  "linkSelector": "a",
  "cheerioFunction": "({ request, $, cheerio }) => { return { url: request.url, title: $('title').text() }; }"
}
```

### Product Scraper Example

```json
{
  "startUrls": [{"url": "https://example-store.com/products"}],
  "pseudoUrls": [{"purl": "https://example-store.com/products/[.*]"}],
  "linkSelector": ".product-link",
  "pageFunction": "async function pageFunction({ request, page }) { if (!request.url.includes('/products/')) return; return { url: request.url, name: await page.$eval('.product-name', el => el.innerText.trim()), price: await page.$eval('.product-price', el => el.innerText.trim()) }; }"
}
```

## Next Steps After POC

1. Implement the full service layer with proper error handling
2. Add webhook support for asynchronous processing
3. Create comprehensive API endpoints for job management
4. Implement proper monitoring and logging
5. Add tests for all components
