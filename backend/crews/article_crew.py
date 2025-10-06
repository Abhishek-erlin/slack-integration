import os
import pathlib
from typing import Dict, Any, Optional
import logging
import re
import json

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, before_kickoff
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from .models import ResearchBrief

# Configure logging
logger = logging.getLogger(__name__)

@CrewBase
class ArticleCrew:
    """Crew that generates articles based on keywords and locations."""
    BASE_DIR = pathlib.Path(__file__).parent.absolute()
    agents_config = str(BASE_DIR / 'config' / 'article-agents.yaml')
    tasks_config = str(BASE_DIR / 'config' / 'article-tasks.yaml')
    
    def __init__(self, openai_api_key: Optional[str] = None, use_claude: bool = False, claude_api_key: Optional[str] = None, claude_model: Optional[str] = None):
        """Initialize the crew with optional API key override."""
        logger.info("Initializing ArticleCrew")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")

        # Research Brief always uses OpenAI to manage Claude rate limits
        # Claude is reserved for full article generation which is more content-heavy
        logger.info("ArticleCrew will always use OpenAI for research brief generation (rate limit management)")
        self.llm = LLM(
            model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),  # Use model from env or fallback to gpt-4o-mini
            api_key=self.openai_api_key,
        )
        logger.info(f"OpenAI LLM initialized for research brief generation with model: {self.llm.model}")
        
        # Initialize tools
        self.serper_tool = SerperDevTool(api_key=self.serper_api_key)
        self.scrape_tool = ScrapeWebsiteTool()
        
        # Log environment variables status (without revealing values)
        logger.info(f"OPENAI_API_KEY configured: {bool(self.openai_api_key)}")
        logger.info(f"SERPER_API_KEY configured: {bool(self.serper_api_key)}")
        
        # Validate required API keys
        if not self.openai_api_key:
            error_msg = "OPENAI_API_KEY is not configured"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not self.serper_api_key:
            error_msg = "SERPER_API_KEY is not configured"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"ArticleCrew initialized with agents config: {self.agents_config}")
        logger.info(f"ArticleCrew initialized with tasks config: {self.tasks_config}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for database lookup
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL
        """
        # Remove protocol (http://, https://)
        normalized = re.sub(r'^https?://', '', url.lower().strip())
        # Remove www. prefix
        normalized = re.sub(r'^www\.', '', normalized)
        # Remove trailing slash
        normalized = normalized.rstrip('/')
        
        return normalized
    
    @before_kickoff
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the inputs before starting the crew."""
        logger.info(f"Validating inputs: {inputs}")
        
        # Validate required fields
        required_fields = ['keyword', 'location', 'goal']
        for field in required_fields:
            if field not in inputs or not inputs[field]:
                error_msg = f"{field} is required"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Add URL to brand_name for backward compatibility if URL is provided
        if 'url' in inputs and inputs['url']:
            url = inputs['url']
            logger.info(f"URL provided: {url}")
            inputs['brand_name'] = url
        
        logger.info("Input validation successful")
        return inputs
    
    @agent
    def research_brief_agent(self) -> Agent:
        """The research brief generation agent."""
        logger.info("=== RESEARCH BRIEF AGENT CREATION ===")
        logger.info("Creating research brief agent with tools and LLM")
        
        # Validate tools before agent creation
        tools = [self.serper_tool, self.scrape_tool]
        logger.info(f"Agent tools being attached: {[tool.__class__.__name__ for tool in tools]}")
        
        # Validate SerperDevTool
        if hasattr(self.serper_tool, 'api_key') and self.serper_tool.api_key:
            logger.info("✅ SerperDevTool API key is configured")
        else:
            logger.error("❌ SerperDevTool API key is missing or empty")
            
        # Validate ScrapeWebsiteTool  
        logger.info(f"✅ ScrapeWebsiteTool initialized: {self.scrape_tool.__class__.__name__}")
        
        # Validate LLM
        if hasattr(self.llm, 'model') and self.llm.model:
            logger.info(f"✅ LLM configured with model: {self.llm.model}")
        else:
            logger.error("❌ LLM model is not properly configured")
            
        # Create agent
        agent = Agent(
            config=self.agents_config['agents']['research_brief_agent'],
            tools=tools,
            llm=self.llm,
        )
        
        logger.info(f"Research brief agent created successfully")
        logger.info(f"Agent role: {agent.role if hasattr(agent, 'role') else 'Unknown'}")
        logger.info(f"Agent tools count: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
        
        return agent
    
    def create_research_brief_task(self) -> Task:
        """Task for generating a research brief."""
        logger.info("Creating research brief task")
        task_config = self.tasks_config['tasks']['research_brief_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.research_brief_agent(),
            async_execution=task_config.get('async', False),
            output_file=task_config.get('output_file', None)
        )
    
    def crew(self, inputs: Dict[str, Any] = None) -> Crew:
        """Creates the article generation crew with the provided inputs."""
        logger.info("Creating article generation crew with research_brief_agent")
        
        # Create only the research brief agent instance
        research_brief_agent_instance = self.research_brief_agent()
        
        # Create the research brief task
        # For CrewAI 0.105.0, we need to manually format the task description with inputs
        task_config = self.tasks_config['tasks']['research_brief_task'].copy()
        
        # Format the description with the input variables
        if 'description' in task_config and inputs:
            # Create a clean copy of inputs for formatting
            clean_inputs = inputs.copy()
            
            # Handle string-formatted dictionaries - remove complex fields that might cause formatting issues
            dict_fields = [
                'brand_tone_examples', 'brand_voice_examples', 'messaging_themes_examples', 
                'personality_traits_examples'
            ]
            
            # First, modify the task description to remove references to complex dictionary fields
            for field in dict_fields:
                # Replace {field} placeholders with a simple text description
                task_config['description'] = task_config['description'].replace('{' + field + '}', 
                                                                      f"the provided {field.replace('_', ' ')}")
            
            # Now format with the remaining variables
            try:
                task_config['description'] = task_config['description'].format(**clean_inputs)
                logger.info(f"Successfully formatted task description")
            except KeyError as e:
                logger.error(f"Error formatting task description: {str(e)}")
                # If formatting fails, try to identify the problematic keys
                import re
                placeholders = re.findall(r'\{([^\}]+)\}', task_config['description'])
                missing_keys = [p for p in placeholders if p not in clean_inputs]
                logger.error(f"Missing keys in task description: {missing_keys}")
                # Try a more aggressive approach - remove all problematic placeholders
                if missing_keys:
                    logger.info(f"Attempting to remove problematic placeholders: {missing_keys}")
                    for key in missing_keys:
                        task_config['description'] = task_config['description'].replace('{' + key + '}', 
                                                                          f"the provided {key.replace('_', ' ')}")
                    # Try formatting again
                    try:
                        task_config['description'] = task_config['description'].format(**clean_inputs)
                        logger.info(f"Successfully formatted task description after removing problematic placeholders")
                    except KeyError as e2:
                        logger.error(f"Still failed to format task description: {str(e2)}")
                        raise ValueError(f"Error formatting task description: {str(e)}. Missing keys: {missing_keys}")
                else:
                    raise ValueError(f"Error formatting task description: {str(e)}. Missing keys: {missing_keys}")
        
        # Create the task instance with detailed debugging
        logger.info(f"=== TASK CREATION DEBUGGING ===" )
        task_description = task_config.get('description', '')
        task_expected_output = task_config.get('expected_output', '')
        
        logger.info(f"Task description length: {len(task_description)}")
        logger.info(f"Task description preview: {task_description[:300]}...")
        logger.info(f"Expected output length: {len(task_expected_output)}")
        logger.info(f"Expected output preview: {task_expected_output[:200]}...")
        
        # Log key requirements from task description
        if "COMPLETE research brief" in task_description:
            logger.info("✅ Task explicitly requires COMPLETE research brief")
        if "SerperDevTool" in task_description:
            logger.info("✅ Task includes SerperDevTool requirement")
        if "ScrapeWebsiteTool" in task_description:
            logger.info("✅ Task includes ScrapeWebsiteTool requirement")
        
        research_brief_task_instance = Task(
            description=task_description,
            expected_output=task_expected_output,
            agent=research_brief_agent_instance
        )
        
        logger.info(f"Task instance created successfully")
        
        # Define the task workflow with only the research brief task
        tasks = [research_brief_task_instance]
        
        logger.info(f"=== CREW CREATION DEBUGGING ===")
        logger.info(f"Creating crew with {len(tasks)} task(s)")
        logger.info(f"Agent tools available: {[tool.__class__.__name__ for tool in research_brief_agent_instance.tools] if hasattr(research_brief_agent_instance, 'tools') else 'Unknown'}")
        
        # Create a crew with sequential process
        crew = Crew(
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            inputs=inputs  # Pass the inputs to the Crew constructor
        )
        
        logger.info(f"Crew created successfully with verbose=True")
        logger.info(f"Crew process type: {crew.process}")
        return crew
    
    def run_research_brief(self, keyword: str, location: str, goal: str, url: Optional[str] = None, selected_title: Optional[str] = None) -> ResearchBrief:
        """Run the research brief generation process."""
        try:
            logger.info(f"Starting research brief generation for keyword: {keyword}, location: {location}")
            
            # Log model usage (ArticleCrew always uses OpenAI for research briefs)
            logger.info(f"🚀 CrewAI will execute research brief generation using OpenAI: {self.llm.model}")
            
            # Create basic inputs
            inputs = {
                'keyword': keyword,
                'location': location,
                'goal': goal
            }
            
            # Add selected_title to inputs if provided
            if selected_title:
                logger.info(f"Including selected_title in inputs: {selected_title}")
                inputs['selected_title'] = selected_title
                
            # Add URL to inputs if provided
            if url:
                logger.info(f"Including URL in inputs: {url}")
                inputs['url'] = url
                inputs['brand_name'] = url  # For backward compatibility
            
            logger.info(f"=== FINAL CREW INPUTS ANALYSIS ===")
            logger.info(f"Total input parameters: {len(inputs)}")
            
            # Log critical inputs
            critical_params = ['keyword', 'location', 'goal', 'selected_title', 'url']
            for param in critical_params:
                if param in inputs:
                    logger.info(f"✅ {param}: {inputs[param]}")
                else:
                    logger.warning(f"❌ Missing {param}")
                    
            logger.info(f"Complete inputs object: {inputs}")

            # Create a fresh crew instance with the inputs
            crew_instance = self.crew(inputs=inputs)
          
            # Run the crew with comprehensive debugging
            logger.info(f"=== CREW EXECUTION START ===")
            logger.info(f"Running crew with inputs: {inputs}")
            
            # Log crew configuration
            logger.info(f"Crew agents count: {len(crew_instance.agents) if hasattr(crew_instance, 'agents') else 'Unknown'}")
            logger.info(f"Crew tasks count: {len(crew_instance.tasks) if hasattr(crew_instance, 'tasks') else 'Unknown'}")
            
            # Execute crew with timing
            import time
            start_time = time.time()
            logger.info(f"Crew kickoff started at: {start_time}")
            
            result = crew_instance.kickoff()
            
            end_time = time.time()
            execution_duration = end_time - start_time
            logger.info(f"=== CREW EXECUTION COMPLETED ===")
            logger.info(f"Crew execution duration: {execution_duration:.2f} seconds")
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result string length: {len(str(result))}")
            logger.info(f"Result content preview: {str(result)[:500]}..." if len(str(result)) > 500 else str(result))
            
            # Extract token usage with enhanced debugging
            logger.info(f"=== TOKEN USAGE ANALYSIS ===")
            token_usage = None
            if hasattr(result, 'token_usage'):
                # Convert UsageMetrics to dictionary
                logger.info(f"Token usage object type: {type(result.token_usage)}")
                logger.info(f"Token usage raw value: {result.token_usage}")
                
                # Check if tokens were actually used
                if hasattr(result.token_usage, 'total_tokens'):
                    total_tokens = getattr(result.token_usage, 'total_tokens', 0)
                    logger.info(f"Total tokens used: {total_tokens}")
                    if total_tokens == 0:
                        logger.error(f"❌ CRITICAL: NO TOKENS USED - LLM was not called!")
                    else:
                        logger.info(f"✅ LLM was called successfully with {total_tokens} tokens")
                        
                if hasattr(result.token_usage, '__dict__'):
                    # Try to convert using __dict__
                    token_usage = result.token_usage.__dict__
                    logger.info(f"Token usage converted from UsageMetrics.__dict__: {token_usage}")
                elif hasattr(result.token_usage, 'model_dump'):
                    # Try Pydantic v2 model_dump method
                    token_usage = result.token_usage.model_dump()
                    logger.info(f"Token usage converted using model_dump(): {token_usage}")
                elif hasattr(result.token_usage, 'dict'):
                    # Try Pydantic v1 dict method
                    token_usage = result.token_usage.dict()
                    logger.info(f"Token usage converted using dict(): {token_usage}")
                else:
                    # Manual conversion as fallback
                    try:
                        token_usage = {
                            "total_tokens": getattr(result.token_usage, 'total_tokens', 0),
                            "prompt_tokens": getattr(result.token_usage, 'prompt_tokens', 0),
                            "completion_tokens": getattr(result.token_usage, 'completion_tokens', 0),
                            "successful_requests": getattr(result.token_usage, 'successful_requests', 0)
                        }
                        logger.info(f"Token usage manually extracted: {token_usage}")
                    except Exception as e:
                        logger.warning(f"Failed to manually extract token usage: {str(e)}")
                        # Create a simple dictionary with total_tokens
                        token_usage = {"total_tokens": str(result.token_usage)}
                        logger.info(f"Using simplified token usage: {token_usage}")
            else:
                logger.error(f"❌ CRITICAL: No token_usage attribute found in result")
            
            # Enhanced result content analysis before extraction
            logger.info(f"=== DETAILED RESULT CONTENT ANALYSIS ===")
            if hasattr(result, 'raw'):
                raw_content = getattr(result, 'raw')
                logger.info(f"Result.raw content length: {len(raw_content) if raw_content else 0}")
                logger.info(f"Result.raw preview: {raw_content[:300]}..." if raw_content and len(raw_content) > 300 else str(raw_content))
                
                # Check for common issues
                if raw_content and len(raw_content) < 500:
                    logger.warning(f"⚠️ WARNING: Raw content is suspiciously short ({len(raw_content)} chars)")
                if raw_content and "The above is" in raw_content:
                    logger.error(f"❌ CRITICAL: Raw content appears to be meta-description, not actual content")
            
            # Extract research brief from result
            research_brief_text = None
            
            # ENHANCED RESULT EXTRACTION WITH MULTIPLE ACCESS PATTERNS
            logger.info("=== ATTEMPTING RESULT EXTRACTION ===")
            
            # Method 1: Try accessing tasks_output attribute (CrewAI 0.105.0 specific)
            if hasattr(result, 'tasks_output'):
                logger.info("Method 1: Attempting tasks_output access")
                try:
                    tasks_output = getattr(result, 'tasks_output')
                    logger.info(f"tasks_output type: {type(tasks_output)}")
                    if tasks_output and len(tasks_output) > 0:
                        # Try to get the first task output
                        first_task = tasks_output[0]
                        logger.info(f"First task type: {type(first_task)}")
                        
                        # Try different ways to get the content
                        if hasattr(first_task, 'raw'):
                            research_brief_text = first_task.raw
                            logger.info(f"SUCCESS Method 1a: Extracted from tasks_output[0].raw (length: {len(research_brief_text)})")
                        elif hasattr(first_task, 'output'):
                            research_brief_text = first_task.output
                            logger.info(f"SUCCESS Method 1b: Extracted from tasks_output[0].output (length: {len(research_brief_text)})")
                        elif hasattr(first_task, '__str__'):
                            research_brief_text = str(first_task)
                            logger.info(f"SUCCESS Method 1c: Extracted from str(tasks_output[0]) (length: {len(research_brief_text)})")
                except Exception as e:
                    logger.warning(f"Method 1 failed: {str(e)}")
                    
            # Method 2: Try accessing raw attribute directly
            if not research_brief_text and hasattr(result, 'raw'):
                logger.info("Method 2: Attempting direct raw access")
                try:
                    research_brief_text = getattr(result, 'raw')
                    if research_brief_text:
                        logger.info(f"SUCCESS Method 2: Extracted from result.raw (length: {len(research_brief_text)})")
                except Exception as e:
                    logger.warning(f"Method 2 failed: {str(e)}")
            
            # Method 3: Try string conversion as fallback
            if not research_brief_text:
                logger.info("Method 3: Using string conversion fallback")
                research_brief_text = str(result)
                logger.info(f"SUCCESS Method 3: Using str(result) (length: {len(research_brief_text)})")
            
            # ENHANCED CONTENT VALIDATION - Detect meta-descriptions and placeholder responses
            is_placeholder = False
            is_meta_description = False
            content_too_short = False
            missing_sections = []
            
            if research_brief_text:
                # Check for known placeholder patterns (original)
                placeholder_indicators = [
                    "The detailed research brief provided above",
                    "is ready, fully adapted",
                    "align with the brand's tone"
                ]
                
                # Check for meta-description patterns (new - the main issue)
                meta_description_indicators = [
                    "The comprehensive research brief contains",
                    "The above is a complete research brief",
                    "contains competitive analysis, a detailed content outline",
                    "research insights with citations, and SEO strategy",
                    "tailored for the article",
                    "The research brief includes"
                ]
                
                # Check for required sections presence
                required_sections = [
                    "## COMPETITIVE ANALYSIS",
                    "## CONTENT OUTLINE", 
                    "## RESEARCH INSIGHTS",
                    "## SEO STRATEGY"
                ]
                
                # Perform all validations
                is_placeholder = any(indicator in research_brief_text for indicator in placeholder_indicators)
                is_meta_description = any(indicator in research_brief_text for indicator in meta_description_indicators)
                content_too_short = len(research_brief_text.strip()) < 1000  # Updated for ~1000 word target
                
                # Check for missing sections
                for section in required_sections:
                    if section not in research_brief_text:
                        missing_sections.append(section)
                        
                # Enhanced logging
                logger.info(f"=== ENHANCED CONTENT VALIDATION ===")
                logger.info(f"Content length: {len(research_brief_text)} characters")
                logger.info(f"Is placeholder: {is_placeholder}")
                logger.info(f"Is meta-description: {is_meta_description}")
                logger.info(f"Content too short: {content_too_short} (minimum 1000 chars for ~1000 word articles)")
                logger.info(f"Missing sections: {missing_sections if missing_sections else 'None'}")
                logger.info(f"Required sections found: {len(required_sections) - len(missing_sections)}/4")
                
                # Determine overall content quality
                content_quality_issues = []
                
                if is_placeholder:
                    content_quality_issues.append("Contains placeholder patterns")
                    logger.error(f"❌ PLACEHOLDER CONTENT DETECTED: {research_brief_text[:100]}...")
                    
                if is_meta_description:
                    content_quality_issues.append("Contains meta-description instead of actual content")
                    logger.error(f"❌ META-DESCRIPTION DETECTED: This is the exact issue we're fixing!")
                    logger.error(f"Agent provided summary instead of research brief: {research_brief_text}")
                    
                if content_too_short:
                    content_quality_issues.append(f"Content too short ({len(research_brief_text)} < 1000 chars)")
                    logger.error(f"❌ CONTENT TOO SHORT: {len(research_brief_text)} characters")
                    
                if missing_sections:
                    content_quality_issues.append(f"Missing sections: {missing_sections}")
                    logger.error(f"❌ MISSING REQUIRED SECTIONS: {missing_sections}")
                    
                # Overall validation result
                if content_quality_issues:
                    logger.error(f"=== CONTENT VALIDATION FAILED ===")
                    logger.error(f"Issues found: {content_quality_issues}")
                    # Mark as problematic content that should trigger retry
                    is_placeholder = True  # Use existing retry logic
                else:
                    logger.info("=== CONTENT VALIDATION PASSED ===")
                    logger.info("✅ Content appears to be genuine research brief with all required sections")
            
            # Since we're using a single agent with combined functionality,
            # the research brief already includes brand tone adaptation
            research_brief_with_brandtone_text = research_brief_text
            logger.info("Using research brief as final output")
            
            # COMPREHENSIVE FINAL RESULT SUMMARY
            logger.info(f"=== COMPREHENSIVE FINAL RESULT SUMMARY ===")
            logger.info(f"Execution duration: {execution_duration:.2f} seconds")
            logger.info(f"Research brief length: {len(research_brief_text) if research_brief_text else 0}")
            logger.info(f"Is placeholder content: {is_placeholder}")
            logger.info(f"Token usage summary: {token_usage}")
            
            # Create and return ResearchBrief object
            # Validate and convert token_usage using the helper method
            validated_token_usage = ResearchBrief.model_validate_token_usage(token_usage)
            
            research_brief = ResearchBrief(
                keyword=keyword,
                location=location,
                goal=goal,
                research_brief=research_brief_text,
                research_brief_with_brandtone=research_brief_with_brandtone_text,
                token_usage=validated_token_usage
            )
            
            # Final status determination
            if research_brief_text and len(research_brief_text) > 500 and not is_placeholder:
                logger.info("✅ Research brief generation completed successfully")
            else:
                logger.error(f"❌ Research brief generation failed - content issues detected")
                
            logger.info(f"=== RESEARCH BRIEF GENERATION SUMMARY ===")
            logger.info(f"Final research brief object created with content length: {len(research_brief.research_brief) if research_brief else 0}")
            
            return research_brief
            
        except Exception as e:
            logger.error(f"Error running research brief generation: {str(e)}", exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
