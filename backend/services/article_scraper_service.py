"""
Article Scraper Service

This service provides functionality to scrape article/blog pages and extract structured content
including titles, headings, main article text, and metadata.

It uses static HTML fetching with fallback to dynamic rendering when needed.
"""

import asyncio
import logging
import re
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, Tag
import httpx
from httpx import HTTPError, TimeoutException, ConnectError, TooManyRedirects
import trafilatura
import extruct
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Set up logging
logger = logging.getLogger(__name__)

# Default headers for requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

# Maximum HTML size to process (5MB)
MAX_HTML_SIZE = 5 * 1024 * 1024


class ArticleScraperService:
    """Service for scraping article/blog pages and extracting structured content."""
    
    def __init__(self, use_playwright_fallback: bool = False, max_retries: int = 3, timeout: int = 30, max_html_size: int = MAX_HTML_SIZE):
        """
        Initialize the article scraper service.
        
        Args:
            use_playwright_fallback: Whether to use Playwright as a fallback for JavaScript-rendered content
            max_retries: Maximum number of retries for static HTML extraction
            timeout: Timeout in seconds for static HTML extraction
            max_html_size: Maximum HTML size in bytes to process
        """
        self.use_playwright_fallback = use_playwright_fallback
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_html_size = max_html_size
        self.headers = DEFAULT_HEADERS
        self.limits = httpx.Limits(max_keepalive_connections=10, keepalive_expiry=30)
        
    async def scrape_article(self, url: str, use_playwright_fallback: bool = None) -> Dict[str, Any]:
        """
        Scrape article content from the given URL.
        
        Args:
            url: The URL to scrape
            use_playwright_fallback: Whether to use Playwright as a fallback for JavaScript-rendered content
            
        Returns:
            Dictionary containing the extracted article data
        """
        logger.info(f"Starting article scrape for URL: {url}")
        start_time = time.time()
        
        # Use the provided parameter if not None, otherwise use the instance variable
        use_playwright = use_playwright_fallback if use_playwright_fallback is not None else self.use_playwright_fallback
        
        # Validate URL
        if not self._is_valid_url(url):
            logger.error(f"Invalid URL provided: {url}")
            raise ValueError("Invalid URL format")
        
        try:
            # Try static HTML extraction first
            result = await self._scrape_static_html(url)
            
            # If static extraction fails or is incomplete, try Playwright if enabled
            if (not result or not self._is_extraction_complete(result)) and use_playwright:
                logger.info(f"Static extraction incomplete for {url}, attempting Playwright fallback")
                playwright_result = await self._scrape_with_playwright(url, use_playwright)
                if playwright_result and self._is_extraction_complete(playwright_result):
                    result = playwright_result
            
            # If we still don't have a result, raise an exception
            if not result:
                logger.warning(f"All extraction methods failed for {url}")
                raise ValueError("Extraction failed with all methods")
            
            # Log completion time
            elapsed_time = time.time() - start_time
            logger.info(f"Article scrape completed in {elapsed_time:.2f} seconds for {url}")
            
            # Filter the response to only include the specified fields
            filtered_result = {
                'url': result.get('url'),
                'final_url': result.get('final_url'),
                'title': result.get('title'),
                'h1': result.get('h1'),
                'headings': result.get('headings', []),
                'content': result.get('content')
            }
            
            return filtered_result
            
        except Exception as e:
            logger.error(f"Unexpected error during article scrape: {str(e)}")
            raise RuntimeError(f"Unexpected error during article scrape: {str(e)}")
            
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if the provided URL has a valid format.
        
        Args:
            url: URL to validate
            
        Returns:
            Boolean indicating if URL is valid
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False

    def _is_extraction_complete(self, result: Dict[str, Any]) -> bool:
        """
        Check if the extraction result is complete enough.
        
        Args:
            result: Extraction result dictionary
            
        Returns:
            Boolean indicating if extraction is complete
        """
        if not result:
            return False
        
        # Check if we have at least title and some content
        has_title = result.get('title') and len(result.get('title', '').strip()) > 0
        has_content = result.get('content') and len(result.get('content', '').strip()) > 100
        
        return has_title and has_content

    async def _scrape_static_html(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape the article using static HTML extraction with retries and error handling.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary of extracted data or None if extraction failed
        """
        retry_count = 0
        backoff_factor = 1.5
        
        while retry_count <= self.max_retries:
            try:
                logger.info(f"Static HTML extraction attempt {retry_count + 1}/{self.max_retries + 1} for {url}")
                
                # Fetch the HTML content with timeout and size limits
                async with httpx.AsyncClient(
                    headers=self.headers, 
                    follow_redirects=True,
                    timeout=self.timeout,
                    limits=self.limits
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Check content size before processing
                    content_length = len(response.content)
                    if content_length > self.max_html_size:
                        logger.warning(f"HTML content too large: {content_length} bytes (max: {self.max_html_size})")
                        return None
                        
                    html_content = response.text
                    final_url = str(response.url)
                    
                    # Log response info
                    logger.info(f"Received {response.status_code} response from {url}, content size: {content_length} bytes")
                
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Extract data
                extracted_data = {
                    'url': url,
                    'final_url': final_url,
                    'title': self._extract_title(soup),
                    'h1': self._extract_h1(soup),
                    'headings': self._extract_headings(soup),
                    'content': self._extract_content(html_content, soup),
                }
                
                logger.info(f"Static HTML extraction successful for {url}")
                return extracted_data
                
            except TimeoutException as e:
                logger.warning(f"Timeout during static HTML extraction: {str(e)}")
            except ConnectError as e:
                logger.warning(f"Connection error during static HTML extraction: {str(e)}")
            except TooManyRedirects as e:
                logger.warning(f"Too many redirects during static HTML extraction: {str(e)}")
                # Don't retry on redirect issues
                return None
            except HTTPError as e:
                status_code = getattr(e, 'response', {}).status_code
                if status_code:
                    logger.warning(f"HTTP error {status_code} during static HTML extraction: {str(e)}")
                    # Don't retry on client errors (4xx)
                    if 400 <= status_code < 500:
                        return None
                else:
                    logger.warning(f"HTTP error during static HTML extraction: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error during static HTML extraction: {str(e)}")
            
            # Retry with exponential backoff
            retry_count += 1
            if retry_count <= self.max_retries:
                wait_time = backoff_factor ** (retry_count - 1)
                logger.info(f"Retrying in {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
            
        logger.error(f"Static HTML extraction failed after {self.max_retries + 1} attempts for {url}")
        return None

    async def _scrape_with_playwright(self, url: str, use_playwright: bool = None) -> Optional[Dict[str, Any]]:
        """
        Scrape the article using Playwright for JavaScript-rendered content.
        
        Args:
            url: The URL to scrape
            use_playwright: Whether to use Playwright for this request
            
        Returns:
            Dictionary of extracted data or None if extraction failed
        """
        # Use the provided parameter if not None, otherwise use the instance variable
        should_use_playwright = use_playwright if use_playwright is not None else self.use_playwright_fallback
        
        if not should_use_playwright:
            logger.info("Playwright fallback disabled by configuration")
            return None
            
        try:
            logger.info(f"Starting Playwright fallback for {url}")
            
            # Initialize Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent=self.headers['User-Agent']
                )
                
                # Create a new page and navigate to the URL
                page = await context.new_page()
                
                # Set timeout for navigation
                page.set_default_timeout(30000)  # 30 seconds
                
                # Add request headers
                await page.set_extra_http_headers(self.headers)
                
                # Navigate to the URL
                response = await page.goto(url, wait_until="networkidle")
                if not response:
                    logger.error(f"Failed to navigate to {url} with Playwright")
                    await browser.close()
                    return None
                    
                final_url = page.url
                
                # Wait for content to load
                await page.wait_for_load_state("networkidle")
                
                # Handle cookie banners and modals (common on article sites)
                await self._handle_cookie_banners(page)
                
                # Wait a bit more for any delayed content
                await asyncio.sleep(2)
                
                # Get the HTML content
                html_content = await page.content()
                
                # Close the browser
                await browser.close()
                
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Extract data using the same methods as static extraction
                extracted_data = {
                    'url': url,
                    'final_url': final_url,
                    'title': self._extract_title(soup),
                    'h1': self._extract_h1(soup),
                    'headings': self._extract_headings(soup),
                    'content': self._extract_content(html_content, soup),
                }
                
                logger.info(f"Successfully extracted article data with Playwright from {url}")
                return extracted_data
                
        except PlaywrightTimeoutError as e:
            logger.warning(f"Timeout during Playwright extraction: {str(e)}")
        except Exception as e:
            logger.error(f"Error during Playwright extraction: {str(e)}")
            return None
            
    async def _handle_cookie_banners(self, page) -> None:
        """
        Attempt to handle common cookie banners and modals that might block content.
        
        Args:
            page: Playwright page object
        """
        try:
            # Common cookie banner accept button selectors
            cookie_selectors = [
                "button[id*='accept' i]",
                "button[class*='accept' i]",
                "button[id*='cookie' i]",
                "button[class*='cookie' i]",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('I Agree')",
                "button:has-text('OK')",
                "button:has-text('Close')",
                ".modal-close",
                ".modal .close",
            ]
            
            for selector in cookie_selectors:
                try:
                    # Check if the selector exists
                    if await page.query_selector(selector):
                        await page.click(selector)
                        logger.info(f"Clicked on potential cookie/modal element: {selector}")
                        await asyncio.sleep(0.5)  # Small delay after clicking
                except Exception:
                    continue  # Continue to the next selector if this one fails
                    
        except Exception as e:
            logger.warning(f"Error handling cookie banners: {str(e)}")
            # Continue with extraction even if cookie handling fails

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the page title from the HTML."""
        if soup.title:
            title = soup.title.get_text().strip()
            if title:
                logger.info(f"Extracted title: {title[:50]}..." if len(title) > 50 else f"Extracted title: {title}")
                return title
        
        logger.warning("No title tag found in HTML")
        return None
    
    def _extract_h1(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the first H1 heading from the HTML."""
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text().strip()
            if h1_text:
                logger.info(f"Extracted H1: {h1_text[:50]}..." if len(h1_text) > 50 else f"Extracted H1: {h1_text}")
                return h1_text
        
        logger.warning("No H1 tag found in HTML")
        return None
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings (h1-h6) from the HTML."""
        headings = []
        for level in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{level}'):
                heading_text = heading.get_text().strip()
                if heading_text:  # Only include non-empty headings
                    headings.append({
                        "level": str(level),  # Convert integer to string to match Pydantic model
                        "text": heading_text
                    })
        
        logger.info(f"Extracted {len(headings)} headings")
        return headings
    
    def _extract_content(self, html: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main article content from the HTML."""
        # Strategy 1: Look for common article container elements
        article_containers = [
            # Common article containers
            ('article', {}),
            ('div', {'class': re.compile(r'article|post|entry|content|main-content', re.I)}),
            ('div', {'id': re.compile(r'article|post|entry|content|main-content', re.I)}),
            ('main', {}),
            ('section', {'class': re.compile(r'article|post|entry|content', re.I)}),
            # WordPress common containers
            ('div', {'class': 'entry-content'}),
            ('div', {'class': 'post-content'}),
            # Medium-style containers
            ('article', {'class': re.compile(r'post|story')}),
            # News site containers
            ('div', {'class': re.compile(r'story-body|article-body')}),
            # Generic content containers
            ('div', {'role': 'main'}),
            ('div', {'class': 'main'})
        ]
        
        # Try each container selector
        for tag_name, attrs in article_containers:
            container = soup.find(tag_name, attrs)
            if container:
                # Remove common non-content elements
                self._clean_article_container(container)
                
                # Get the text content
                content = container.get_text(separator='\n', strip=True)
                
                # If we have substantial content, return it
                if content and len(content) > 200:  # Arbitrary minimum length for a real article
                    logger.info(f"Extracted article content using container selector: {tag_name} {attrs}")
                    return content
        
        # Strategy 2: Use trafilatura as fallback
        logger.info("No suitable article container found, falling back to trafilatura")
        try:
            extracted_content = trafilatura.extract(html, include_comments=False, include_tables=True, 
                                                  include_images=False, include_links=False, 
                                                  favor_precision=True, output_format='text')
            
            if extracted_content and len(extracted_content) > 200:
                logger.info(f"Successfully extracted content using trafilatura ({len(extracted_content)} chars)")
                return extracted_content
            else:
                logger.warning("Trafilatura extraction returned insufficient content")
        except Exception as e:
            logger.warning(f"Error using trafilatura for content extraction: {str(e)}")
        
        # Strategy 3: Last resort - extract all paragraph text from the body
        logger.info("Falling back to paragraph extraction")
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()]
        
        # Filter out very short paragraphs (likely navigation/UI text)
        paragraphs = [p for p in paragraphs if len(p) > 40]
        
        if paragraphs:
            content = '\n\n'.join(paragraphs)
            logger.info(f"Extracted {len(paragraphs)} paragraphs as content ({len(content)} chars)")
            return content
        
        logger.warning("Failed to extract meaningful article content")
        return None
    
    def _clean_article_container(self, container: Tag) -> None:
        """Remove non-content elements from an article container."""
        # Elements to remove
        selectors_to_remove = [
            # Navigation
            'nav', '.nav', '.navigation', '.menu',
            # Comments
            '.comments', '.comment-section', '#comments',
            # Sidebars
            'aside', '.sidebar', '.widget',
            # Social sharing
            '.social', '.share', '.sharing',
            # Related content
            '.related', '.related-posts', '.recommended',
            # Ads
            '.ad', '.ads', '.advertisement', '.banner',
            # Author info boxes that are not part of the main content
            '.author-box', '.bio', '.about-author',
            # Footers within the article
            'footer', '.footer',
            # Newsletter signup
            '.newsletter', '.subscribe',
            # Popups
            '.popup', '.modal',
        ]
        
        # Remove unwanted elements
        for selector in selectors_to_remove:
            for element in container.select(selector):
                element.decompose()
        
        # Also remove script and style tags
        for tag in container.find_all(['script', 'style', 'noscript']):
            tag.decompose()
