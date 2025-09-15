# Apify Integration Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for integrating Apify web scraping capabilities into the Goosebump Crew backend system. The implementation follows our established 3-layer architecture pattern (Router → Service → Repository).

## Implementation Phases

### Phase 1: Foundation Setup (Week 1)

#### 1.1 Database Schema (Days 1-2)

1. Create migration script for scraping tables:
   - `scraping_jobs` table
   - `scraping_results` table
   - Appropriate indexes and constraints

2. Update database schema documentation

#### 1.2 Configuration (Day 2)

1. Update `config/config.py` with Apify settings
2. Add Apify environment variables to `.env.example`
3. Update configuration documentation

#### 1.3 Dependencies (Day 2)

1. Add `apify-client` to `pyproject.toml`
2. Update dependency documentation

### Phase 2: Core Components (Week 1-2)

#### 2.1 Models (Days 3-4)

1. Create `models/scraping_models.py`:
   - `ScrapingRequest`
   - `ScrapingResponse`
   - `ScrapingJobStatus`
   - `ActorType` enum
   - Other necessary models

2. Write tests for models

#### 2.2 Repository Layer (Days 4-5)

1. Create `repositories/scraping_repository.py`:
   - `save_scraping_job`
   - `update_scraping_job`
   - `get_scraping_job`
   - `save_scraping_results`
   - `get_scraping_results`

2. Write tests for repository methods

#### 2.3 Service Layer (Days 6-8)

1. Create `services/apify_service.py`:
   - Core Apify client integration
   - Actor management
   - Result handling

2. Create `services/scraping_service.py`:
   - Business logic for scraping operations
   - Integration with ApifyService and ScrapingRepository

3. Write tests for services

### Phase 3: API Layer (Week 2-3)

#### 3.1 API Routes (Days 9-10)

1. Create `api/routes/scraping_routes.py`:
   - POST `/api/v1/scraping/jobs` endpoint
   - GET `/api/v1/scraping/jobs/{job_id}` endpoint
   - GET `/api/v1/scraping/jobs/{job_id}/results` endpoint
   - POST `/api/v1/scraping/webhook` endpoint

2. Register routes in main application

3. Write tests for API endpoints

#### 3.2 Webhook Handler (Days 11-12)

1. Implement webhook handler for Apify notifications
2. Add security validation for webhooks
3. Create background task processing for webhook events

### Phase 4: Integration & Testing (Week 3)

#### 4.1 Integration Testing (Days 13-14)

1. Create integration tests for the complete flow
2. Test with various Apify actors
3. Verify data persistence and retrieval

#### 4.2 Documentation (Day 15)

1. Update API documentation
2. Create usage examples
3. Document actor-specific configurations

## Detailed Technical Implementation

### Database Migration Script

```sql
-- migrations/create_scraping_tables.sql
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
CREATE INDEX idx_scraping_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_scraping_results_job_id ON scraping_results(scraping_job_id);
```

### Models Implementation

```python
# models/scraping_models.py
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import uuid

class ScrapingStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class ActorType(str, Enum):
    WEB_SCRAPER = "apify/web-scraper"
    CHEERIO_SCRAPER = "apify/cheerio-scraper"
    PLAYWRIGHT_SCRAPER = "apify/playwright-scraper"
    INSTAGRAM_SCRAPER = "jaroslavhejlek/instagram-scraper"
    TWITTER_SCRAPER = "vdrmota/twitter-scraper"
    CUSTOM = "custom"

class ScrapingRequest(BaseModel):
    website_id: str
    actor_id: str
    input_data: Dict[str, Any]
    wait_for_finish: bool = False
    timeout_secs: Optional[int] = 300
    
    @validator('website_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('website_id must be a valid UUID')

class ScrapingResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: str

class ScrapingJob(BaseModel):
    id: str
    website_id: str
    actor_id: str
    created_at: datetime
    updated_at: datetime
    status: ScrapingStatus
    item_count: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ScrapingResult(BaseModel):
    id: str
    scraping_job_id: str
    data: Dict[str, Any]
    created_at: datetime

class WebhookRequest(BaseModel):
    eventType: str
    eventData: Dict[str, Any]
    webhook: Dict[str, Any]
```

### Repository Layer Implementation

```python
# repositories/scraping_repository.py
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
from utils.database import Database
from models.scraping_models import ScrapingStatus, ScrapingJob, ScrapingResult

class ScrapingRepository:
    def __init__(self, db: Database):
        self.db = db
        
    async def save_scraping_job(self, 
                               website_id: str, 
                               actor_id: str,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new scraping job
        
        Args:
            website_id: ID of the website to scrape
            actor_id: ID of the Apify actor to use
            metadata: Additional metadata about the job
            
        Returns:
            ID of the created scraping job
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
        
    async def update_scraping_job(self,
                                 job_id: str,
                                 status: Optional[ScrapingStatus] = None,
                                 item_count: Optional[int] = None,
                                 error_message: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update a scraping job
        
        Args:
            job_id: ID of the job to update
            status: New status
            item_count: Number of items scraped
            error_message: Error message if job failed
            metadata: Updated metadata
        """
        now = datetime.utcnow()
        update_fields = {"updated_at": now}
        
        if status is not None:
            update_fields["status"] = status.value
            
        if item_count is not None:
            update_fields["item_count"] = item_count
            
        if error_message is not None:
            update_fields["error_message"] = error_message
            
        if metadata is not None:
            # Get existing metadata
            existing_job = await self.get_scraping_job(job_id)
            if existing_job:
                existing_metadata = existing_job.metadata or {}
                # Merge with new metadata
                updated_metadata = {**existing_metadata, **metadata}
                update_fields["metadata"] = updated_metadata
        
        # Build dynamic update query
        fields = [f"{key} = :{key}" for key in update_fields.keys()]
        query = f"""
            UPDATE scraping_jobs
            SET {", ".join(fields)}
            WHERE id = :job_id
        """
        
        params = {**update_fields, "job_id": job_id}
        await self.db.execute(query, params)
        
    async def get_scraping_job(self, job_id: str) -> Optional[ScrapingJob]:
        """
        Get a scraping job by ID
        
        Args:
            job_id: ID of the job
            
        Returns:
            ScrapingJob if found, None otherwise
        """
        row = await self.db.fetch_one(
            """
            SELECT * FROM scraping_jobs
            WHERE id = :job_id
            """,
            {"job_id": job_id}
        )
        
        if not row:
            return None
            
        return ScrapingJob(**row)
        
    async def save_scraping_results(self,
                                   job_id: str,
                                   results: List[Dict[str, Any]]) -> None:
        """
        Save scraping results
        
        Args:
            job_id: ID of the scraping job
            results: List of scraped items
        """
        now = datetime.utcnow()
        
        # Update job with item count
        await self.update_scraping_job(
            job_id=job_id,
            status=ScrapingStatus.COMPLETED,
            item_count=len(results)
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
            
    async def get_scraping_results(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get results for a scraping job
        
        Args:
            job_id: ID of the scraping job
            
        Returns:
            List of scraped items
        """
        rows = await self.db.fetch_all(
            """
            SELECT data FROM scraping_results
            WHERE scraping_job_id = :job_id
            ORDER BY created_at
            """,
            {"job_id": job_id}
        )
        
        return [row["data"] for row in rows]
        
    async def get_scraping_jobs_by_website(self, 
                                          website_id: str, 
                                          limit: int = 10, 
                                          offset: int = 0) -> List[ScrapingJob]:
        """
        Get scraping jobs for a website
        
        Args:
            website_id: ID of the website
            limit: Maximum number of jobs to return
            offset: Offset for pagination
            
        Returns:
            List of scraping jobs
        """
        rows = await self.db.fetch_all(
            """
            SELECT * FROM scraping_jobs
            WHERE website_id = :website_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """,
            {
                "website_id": website_id,
                "limit": limit,
                "offset": offset
            }
        )
        
        return [ScrapingJob(**row) for row in rows]
```

### Service Layer Implementation

```python
# services/apify_service.py
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
        
        Args:
            actor_id: ID of the actor (e.g., "apify/web-scraper")
            input_data: Input parameters for the actor
            wait_for_finish: Whether to wait for the actor to finish
            timeout_secs: Maximum time to wait for the actor to finish
            
        Returns:
            Dictionary containing the actor run information
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
        
        Args:
            run_id: ID of the actor run
            dataset_id: ID of the dataset (if run_id not provided)
            
        Returns:
            List of items from the dataset
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
    
    def wait_for_actor_run(self, run_id: str, timeout_secs: int = 300) -> Dict[str, Any]:
        """
        Wait for an actor run to finish
        
        Args:
            run_id: ID of the actor run
            timeout_secs: Maximum time to wait
            
        Returns:
            Run information
        """
        return self.client.run(run_id).wait_for_finish(wait_secs=timeout_secs)
        
    def get_actor_info(self, actor_id: str) -> Dict[str, Any]:
        """
        Get information about an actor
        
        Args:
            actor_id: ID of the actor
            
        Returns:
            Actor information
        """
        return self.client.actor(actor_id).get()
```

```python
# services/scraping_service.py
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from models.scraping_models import ScrapingStatus, ScrapingJob, ScrapingResult, ScrapingRequest, ScrapingResponse
from repositories.scraping_repository import ScrapingRepository
from services.apify_service import ApifyService

class ScrapingService:
    def __init__(self, scraping_repo: ScrapingRepository, apify_service: ApifyService):
        self.scraping_repo = scraping_repo
        self.apify_service = apify_service
        self.logger = logging.getLogger(__name__)
        
    async def start_scraping_job(self, request: ScrapingRequest) -> ScrapingResponse:
        """
        Start a new scraping job
        
        Args:
            request: Scraping request
            
        Returns:
            Scraping response
        """
        try:
            # Create job in database
            job_id = await self.scraping_repo.save_scraping_job(
                website_id=request.website_id,
                actor_id=request.actor_id,
                metadata={"original_request": request.dict(exclude={"input_data"})}
            )
            
            # Update job status to running
            await self.scraping_repo.update_scraping_job(
                job_id=job_id,
                status=ScrapingStatus.RUNNING
            )
            
            # Start actor run
            run = self.apify_service.run_actor(
                actor_id=request.actor_id,
                input_data=request.input_data,
                wait_for_finish=request.wait_for_finish,
                timeout_secs=request.timeout_secs or 300
            )
            
            # Update job with run information
            await self.scraping_repo.update_scraping_job(
                job_id=job_id,
                metadata={
                    "run_id": run["id"],
                    "start_time": datetime.utcnow().isoformat()
                }
            )
            
            # If waiting for finish, process results
            if request.wait_for_finish:
                await self._process_completed_run(job_id, run["id"])
                return ScrapingResponse(
                    success=True,
                    job_id=job_id,
                    status=ScrapingStatus.COMPLETED.value,
                    message="Scraping job completed successfully"
                )
            else:
                return ScrapingResponse(
                    success=True,
                    job_id=job_id,
                    status=ScrapingStatus.RUNNING.value,
                    message="Scraping job started successfully"
                )
                
        except Exception as e:
            self.logger.error(f"Error starting scraping job: {str(e)}")
            if 'job_id' in locals():
                await self.scraping_repo.update_scraping_job(
                    job_id=job_id,
                    status=ScrapingStatus.FAILED,
                    error_message=str(e)
                )
                return ScrapingResponse(
                    success=False,
                    job_id=job_id,
                    status=ScrapingStatus.FAILED.value,
                    message=f"Scraping job failed: {str(e)}"
                )
            else:
                return ScrapingResponse(
                    success=False,
                    message=f"Failed to start scraping job: {str(e)}"
                )
                
    async def _process_completed_run(self, job_id: str, run_id: str) -> None:
        """
        Process a completed actor run
        
        Args:
            job_id: ID of the scraping job
            run_id: ID of the actor run
        """
        try:
            # Get results from Apify
            results = self.apify_service.get_actor_results(run_id=run_id)
            
            # Save results to database
            await self.scraping_repo.save_scraping_results(
                job_id=job_id,
                results=results
            )
            
            # Update job status
            await self.scraping_repo.update_scraping_job(
                job_id=job_id,
                status=ScrapingStatus.COMPLETED,
                item_count=len(results),
                metadata={
                    "end_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing completed run: {str(e)}")
            await self.scraping_repo.update_scraping_job(
                job_id=job_id,
                status=ScrapingStatus.FAILED,
                error_message=str(e)
            )
            
    async def process_webhook_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Process a webhook event from Apify
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        if event_type != "ACTOR.RUN.SUCCEEDED":
            self.logger.info(f"Ignoring webhook event of type {event_type}")
            return
            
        try:
            # Extract run ID from event data
            run_id = event_data.get("actorRunId")
            if not run_id:
                self.logger.error("No run ID in webhook event data")
                return
                
            # Find job by run ID in metadata
            # This would require a new repository method
            # For now, we'll assume the job ID is stored in the webhook payload
            # In a real implementation, you'd query the database
            
            job_id = event_data.get("userData", {}).get("job_id")
            if not job_id:
                self.logger.error("No job ID in webhook event data")
                return
                
            # Process the completed run
            await self._process_completed_run(job_id, run_id)
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event: {str(e)}")
            
    async def get_job_status(self, job_id: str) -> Optional[ScrapingJob]:
        """
        Get the status of a scraping job
        
        Args:
            job_id: ID of the scraping job
            
        Returns:
            Scraping job if found, None otherwise
        """
        return await self.scraping_repo.get_scraping_job(job_id)
        
    async def get_job_results(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get the results of a scraping job
        
        Args:
            job_id: ID of the scraping job
            
        Returns:
            List of scraped items
        """
        job = await self.scraping_repo.get_scraping_job(job_id)
        if not job:
            raise ValueError(f"No job found with ID {job_id}")
            
        if job.status != ScrapingStatus.COMPLETED:
            raise ValueError(f"Job {job_id} is not completed (status: {job.status})")
            
        return await self.scraping_repo.get_scraping_results(job_id)
```

### API Layer Implementation

```python
# api/routes/scraping_routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from models.scraping_models import ScrapingRequest, ScrapingResponse, ScrapingJob, WebhookRequest
from services.scraping_service import ScrapingService
from services.apify_service import ApifyService
from repositories.scraping_repository import ScrapingRepository
from utils.database import get_database
from config.config import get_settings
import hmac
import hashlib

router = APIRouter()
settings = get_settings()

def get_scraping_service():
    db = get_database()
    scraping_repo = ScrapingRepository(db)
    apify_service = ApifyService()
    return ScrapingService(scraping_repo, apify_service)

@router.post("/api/v1/scraping/jobs", response_model=ScrapingResponse)
async def start_scraping_job(
    request: ScrapingRequest,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """
    Start a new scraping job
    """
    return await scraping_service.start_scraping_job(request)

@router.get("/api/v1/scraping/jobs/{job_id}", response_model=ScrapingJob)
async def get_scraping_job(
    job_id: str,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """
    Get the status of a scraping job
    """
    job = await scraping_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job

@router.get("/api/v1/scraping/jobs/{job_id}/results")
async def get_scraping_results(
    job_id: str,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """
    Get the results of a scraping job
    """
    try:
        results = await scraping_service.get_job_results(job_id)
        return {
            "job_id": job_id,
            "results": results,
            "count": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting results: {str(e)}")

@router.post("/api/v1/scraping/webhook")
async def webhook_handler(
    request: WebhookRequest,
    background_tasks: BackgroundTasks,
    scraping_service: ScrapingService = Depends(get_scraping_service)
):
    """
    Handle webhook events from Apify
    """
    # Verify webhook signature if configured
    if settings.apify_webhook_secret:
        # In a real implementation, you'd verify the signature
        # This is just a placeholder
        pass
        
    # Process webhook event in background
    background_tasks.add_task(
        scraping_service.process_webhook_event,
        event_type=request.eventType,
        event_data=request.eventData
    )
    
    return {"status": "accepted"}
```

### Register Routes in Main Application

```python
# main.py
from fastapi import FastAPI
from api.routes import scraping_routes

app = FastAPI()

# Register routes
app.include_router(scraping_routes.router, tags=["scraping"])
```

## POC Implementation

For a proof of concept, we'll implement the core components:

1. Database schema
2. Basic models
3. ApifyService
4. Simple API endpoint

This will allow us to test the integration with Apify and ensure it works as expected before implementing the full solution.

## Testing Strategy

1. **Unit Tests**:
   - Test models validation
   - Test repository methods with mock database
   - Test service methods with mock repository and Apify client

2. **Integration Tests**:
   - Test the complete flow with a real database
   - Test with mock Apify responses

3. **End-to-End Tests**:
   - Test with real Apify actors (using small, quick scraping jobs)
   - Verify data persistence and retrieval

## Deployment Considerations

1. **Environment Variables**:
   - Ensure Apify API token is securely stored
   - Configure appropriate timeouts

2. **Monitoring**:
   - Add logging for all Apify interactions
   - Monitor scraping job status and performance

3. **Error Handling**:
   - Implement robust error handling for API failures
   - Add retry logic for transient errors

4. **Scaling**:
   - Consider background processing for large scraping jobs
   - Implement rate limiting to avoid overloading Apify

## Conclusion

This implementation plan provides a comprehensive roadmap for integrating Apify with the Goosebump Crew backend. By following the established 3-layer architecture and implementing the components described above, we can create a robust and scalable solution for web scraping needs.
