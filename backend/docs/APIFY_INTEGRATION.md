# Apify Integration Documentation

## Overview

This document outlines the integration of Apify web scraping platform with the Goosebump Crew backend system. Apify provides ready-made solutions (actors) for web scraping and automation, which we'll leverage to enhance our data collection capabilities.

## Table of Contents

1. [Architecture](#architecture)
2. [Implementation Plan](#implementation-plan)
3. [Technical Details](#technical-details)
4. [API Reference](#api-reference)
5. [Usage Examples](#usage-examples)
6. [Best Practices](#best-practices)

## Architecture

The Apify integration follows our established 3-layer architecture:

```
┌─────────────────┐
│  Router Layer   │ FastAPI routes for scraping endpoints
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Service Layer  │ ApifyService for business logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Repository Layer │ ScrapingRepository for data persistence
└─────────────────┘
```

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│    API      │────▶│   Apify     │────▶│  Database   │
│             │◀────│   Backend   │◀────│  Platform   │◀────│             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

1. Client requests scraping via API
2. Backend initiates Apify actor
3. Apify performs scraping
4. Results stored in database
5. Client receives results or job ID

## Implementation Plan

### Phase 1: Foundation Setup

1. Create database schema for scraping jobs and results
2. Implement ApifyService for actor interaction
3. Create ScrapingRepository for data persistence
4. Add configuration settings for Apify integration

### Phase 2: API Development

1. Define data models for scraping requests/responses
2. Implement API endpoints for scraping operations
3. Create synchronous and asynchronous scraping flows
4. Add error handling and logging

### Phase 3: Integration & Testing

1. Integrate with existing services (where applicable)
2. Implement webhook handling for asynchronous notifications
3. Create comprehensive tests for all components
4. Document API usage and examples

## Technical Details

### Database Schema

```sql
-- Scraping jobs table
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

-- Scraping results table
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

### Dependencies

Add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
apify-client = "^1.1.0"
```

### Configuration

Add to `config/config.py`:

```python
# Apify settings
apify_api_token: str = ""
apify_timeout_secs: int = 300
apify_webhook_secret: str = ""
```

Add to `.env.example`:

```
# Apify settings
APIFY_API_TOKEN=your_apify_api_token
APIFY_TIMEOUT_SECS=300
APIFY_WEBHOOK_SECRET=your_webhook_secret
```

## API Reference

### Endpoints

#### Start Scraping Job

```
POST /api/v1/scraping/jobs
```

Request body:
```json
{
  "website_id": "uuid",
  "actor_id": "apify/web-scraper",
  "input_data": {
    "startUrls": [{"url": "https://example.com"}],
    "pseudoUrls": [{"purl": "https://example.com/[.*]"}],
    "linkSelector": "a",
    "pageFunction": "function pageFunction() { /* scraping logic */ }"
  },
  "wait_for_finish": false,
  "timeout_secs": 300
}
```

Response:
```json
{
  "success": true,
  "job_id": "uuid",
  "status": "running",
  "message": "Scraping job started successfully"
}
```

#### Get Scraping Job Status

```
GET /api/v1/scraping/jobs/{job_id}
```

Response:
```json
{
  "job_id": "uuid",
  "website_id": "uuid",
  "actor_id": "apify/web-scraper",
  "status": "completed",
  "created_at": "2025-09-15T07:30:00Z",
  "updated_at": "2025-09-15T07:35:00Z",
  "item_count": 42,
  "metadata": {
    "run_id": "apify_run_id",
    "duration_secs": 300
  }
}
```

#### Get Scraping Results

```
GET /api/v1/scraping/jobs/{job_id}/results
```

Response:
```json
{
  "job_id": "uuid",
  "results": [
    {
      "url": "https://example.com/page1",
      "title": "Example Page 1",
      "data": { /* scraped data */ }
    },
    {
      "url": "https://example.com/page2",
      "title": "Example Page 2",
      "data": { /* scraped data */ }
    }
  ],
  "count": 2
}
```

#### Webhook Callback (for Apify)

```
POST /api/v1/scraping/webhook
```

## Usage Examples

### Basic Scraping Example

```python
from services.apify_service import ApifyService

# Initialize service
apify_service = ApifyService()

# Configure actor input
input_data = {
    "startUrls": [{"url": "https://example.com"}],
    "pseudoUrls": [{"purl": "https://example.com/[.*]"}],
    "linkSelector": "a",
    "pageFunction": """
    async function pageFunction({ request, page }) {
        return {
            url: request.url,
            title: await page.title(),
            content: await page.$eval('body', el => el.innerText)
        };
    }
    """
}

# Run actor and get results
run = apify_service.run_actor("apify/web-scraper", input_data)
results = apify_service.get_actor_results(run["id"])

# Process results
for item in results:
    print(f"Scraped: {item['url']} - {item['title']}")
```

### E-commerce Product Scraping

```python
# E-commerce product scraping example
input_data = {
    "startUrls": [{"url": "https://example-store.com/products"}],
    "pseudoUrls": [{"purl": "https://example-store.com/products/[.*]"}],
    "linkSelector": ".product-link",
    "pageFunction": """
    async function pageFunction({ request, page }) {
        // Only extract data on product pages
        if (!request.url.includes('/products/')) {
            return;
        }
        
        return {
            url: request.url,
            name: await page.$eval('.product-name', el => el.innerText.trim()),
            price: await page.$eval('.product-price', el => el.innerText.trim()),
            description: await page.$eval('.product-description', el => el.innerText.trim()),
            imageUrl: await page.$eval('.product-image', el => el.getAttribute('src')),
            inStock: await page.$$eval('.stock-status', el => !el[0].innerText.includes('Out of stock'))
        };
    }
    """
}
```

## Best Practices

1. **Rate Limiting**: Respect website terms of service and implement proper rate limiting
2. **Error Handling**: Implement robust error handling for API failures
3. **Data Validation**: Validate scraped data before storing in database
4. **Asynchronous Processing**: Use asynchronous processing for large scraping jobs
5. **Monitoring**: Implement monitoring for scraping jobs and actor performance
6. **Caching**: Cache results when appropriate to reduce unnecessary scraping
7. **Proxy Management**: Use Apify's proxy management for sites that block scrapers
8. **Incremental Scraping**: Implement incremental scraping to only fetch new/changed data
9. **Security**: Secure API endpoints and validate all input data
10. **Documentation**: Keep documentation updated with actor-specific requirements
