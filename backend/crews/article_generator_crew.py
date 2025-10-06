import os
import pathlib
from typing import Dict, Any, Optional, List
import logging
import yaml
import json
import re

from crewai import Agent, Crew, Task, LLM, Process
from crewai.project import CrewBase, agent, crew, task, before_kickoff

# Configure logging
logger = logging.getLogger(__name__)

@CrewBase
class ArticleGeneratorCrew:
    """Crew that generates articles based on research briefs."""
    BASE_DIR = pathlib.Path(__file__).parent.absolute()
    agents_config_path = str(BASE_DIR / 'config' / 'article-agents.yaml')
    tasks_config_path = str(BASE_DIR / 'config' / 'article-tasks.yaml')
    
    def __init__(self, openai_api_key: Optional[str] = None, use_claude: bool = False, claude_api_key: Optional[str] = None, claude_model: Optional[str] = None):
        """Initialize the crew with optional API key override."""
        logger.info("Initializing ArticleGeneratorCrew")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Store config paths as instance attributes
        self.agents_config = self.agents_config_path
        self.tasks_config = self.tasks_config_path
        
        # Initialize research_brief attribute
        self.research_brief = None
        
        # LLM Provider Selection
        self.use_claude = use_claude
        self.claude_api_key = claude_api_key
        self.claude_model = claude_model or "claude-3-7-sonnet-20250219"
        
        # Initialize LLM based on provider selection
        if self.use_claude and self.claude_api_key:
            logger.info(f"Initializing Claude LLM with model: {self.claude_model}")
            self.llm = LLM(
                model=f"anthropic/{self.claude_model}",
                api_key=self.claude_api_key,
            )
            logger.info(f"Claude LLM initialized with model: anthropic/{self.claude_model}")
        else:
            logger.info("Initializing OpenAI LLM")
            self.llm = LLM(
                model=os.getenv("LLM_MODEL_4o", "openai/gpt-4o-mini"),
                api_key=self.openai_api_key,
            )
            logger.info(f"OpenAI LLM initialized with model: {self.llm.model}")
        
        # Log environment variables status (without revealing values)
        logger.info(f"OPENAI_API_KEY configured: {bool(self.openai_api_key)}")
        
        # Validate required API keys
        if not self.openai_api_key:
            error_msg = "OPENAI_API_KEY is not configured"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"ArticleGeneratorCrew initialized with agents config: {self.agents_config}")
        logger.info(f"ArticleGeneratorCrew initialized with tasks config: {self.tasks_config}")
    
    def _load_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Load agent configuration from YAML."""
        try:
            # Use hardcoded path to avoid attribute issues
            config_path = str(self.BASE_DIR / 'config' / 'article-agents.yaml')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'agents' not in config or agent_name not in config['agents']:
                raise ValueError(f"Agent '{agent_name}' not found in config")
            
            return config['agents'][agent_name]
        except Exception as e:
            logger.error(f"Error loading agent config: {str(e)}")
            raise

    def _load_task_config(self, task_name: str) -> Dict[str, Any]:
        """Load task configuration from YAML."""
        try:
            # Use hardcoded path to avoid attribute issues
            config_path = str(self.BASE_DIR / 'config' / 'article-tasks.yaml')
    
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
    
            # Check if tasks are nested under a 'tasks' key
            if 'tasks' in config and task_name in config['tasks']:
                task_config = config['tasks'][task_name]
            elif task_name in config:
                task_config = config[task_name]
            else:
                raise ValueError(f"Task '{task_name}' not found in config")
    
            return task_config
        except Exception as e:
            logger.error(f"Error loading task config: {str(e)}")
            raise

    @before_kickoff
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the crew is ready to run."""
        logger.info("Validating crew is ready to run")
        
        # Check instance attribute instead of inputs
        if not hasattr(self, 'research_brief') or not self.research_brief:
            error_msg = "research_brief attribute is required"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Validation successful")
        return inputs or {}  # Return inputs unchanged or empty dict if None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize a URL by removing protocol and www."""
        logger.debug(f"Normalizing URL: {url}")
        try:
            # Remove protocol (http://, https://, etc.)
            normalized = re.sub(r'^https?://', '', url)
            # Remove www.
            normalized = re.sub(r'^www\.', '', normalized)
            # Remove trailing slash
            normalized = normalized.rstrip('/')
            logger.debug(f"Normalized URL: {normalized}")
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing URL: {str(e)}")
            return url
            
    def _format_guidelines_list(self, items) -> str:
        """Format a list of guideline items into a simple string"""
        if not items or not isinstance(items, list):
            return ""
            
        # Convert the list to a string representation
        return str(items)
            
    @agent
    def content_generator_agent(self) -> Agent:
        """The content generation agent."""
        try:
            # Load agent configuration from YAML
            agent_config = self._load_agent_config('content_generator_agent')
            
            # Create the agent with the loaded configuration
            agent = Agent(
                role=agent_config.get('role', 'Content Generator'),
                goal=agent_config.get('goal', 'Generate high-quality content'),
                backstory=agent_config.get('backstory', 'You are an expert content creator.'),
                verbose=True,
                llm=self.llm
            )
            
            logger.info(f"Created content generator agent with role: {agent_config.get('role')}")
            return agent
            
        except Exception as e:
            logger.error(f"Error creating content generator agent: {str(e)}")
            # Return a default agent if configuration loading fails
            return Agent(
                role="Content Generator",
                goal="Generate high-quality content",
                backstory="You are an expert content creator.",
                verbose=True,
                llm=self.llm
            )
            
    def crew(self, inputs: Dict[str, Any] = None) -> Crew:
        """Creates the article generation crew with the provided inputs."""
        logger.info("Creating article generation crew")
        
        # Create agent instance
        content_generator_agent_instance = self.content_generator_agent()
        
        # Create the content generation task
        # For CrewAI 0.105.0, we need to manually format the task description with inputs
        task_config = self._load_task_config('content_generation_task').copy()
        
        # Format the description with the input variables
        if 'description' in task_config and inputs:
            try:
                task_config['description'] = task_config['description'].format(**inputs)
                logger.info("Successfully formatted task description with inputs")
            except KeyError as e:
                logger.warning(f"Missing key in inputs for task description formatting: {e}")
                # Continue with unformatted description
            except Exception as e:
                logger.error(f"Error formatting task description: {e}", exc_info=True)
                # Continue with unformatted description
        
        content_generation_task_instance = Task(
            description=task_config.get('description', ''),
            expected_output=task_config.get('expected_output', ''),
            agent=content_generator_agent_instance,
            task_id='content_generation_task'  # Match the task ID with the one in YAML
        )
        
        # Create a crew with sequential process
        return Crew(
            tasks=[content_generation_task_instance],
            process=Process.sequential,
            verbose=True,
            inputs=inputs  # Pass the inputs to the Crew constructor
        )

    def create_content_generation_task(self):
        """Task for generating article content."""
        try:
            # Load task configuration from YAML
            task_config = self._load_task_config('content_generation_task')
            
            # Create the task with the loaded configuration
            task = Task(
                description=task_config.get('description', ''),
                expected_output=task_config.get('expected_output', ''),
                agent=self.content_generator_agent()
            )
            
            logger.info("Created content generation task")
            return task
            
        except Exception as e:
            logger.error(f"Error creating content generation task: {str(e)}")
            # Return a default task if configuration loading fails
            return Task(
                description="Generate a high-quality article based on the research brief.",
                agent=self.content_generator_agent()
            )

    async def generate_article(self, research_brief: str, company_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate an article based on the research brief."""
        try:
            logger.info("Starting article generation process")
            
            # Log which model is actively being used for this generation
            if self.use_claude:
                logger.info(f"🚀 CrewAI will execute full article generation using Claude: anthropic/{self.claude_model}")
            else:
                logger.info(f"🚀 CrewAI will execute full article generation using OpenAI: {self.llm.model}")

            def research_brief_breakdown(research_brief: str) -> Dict[str, str]:
                """Splits the research brief into sections."""
                sections = {}
                section_titles = [
                    "## COMPETITIVE ANALYSIS",
                    "## CONTENT OUTLINE",
                    "## RESEARCH INSIGHTS",
                    "## SEO STRATEGY",
                ]
                for i in range(len(section_titles)):
                    title = section_titles[i]
                    start_index = research_brief.find(title)
                    if start_index != -1:
                        end_index = research_brief.find(section_titles[i+1]) if i+1 < len(section_titles) else len(research_brief)
                        sections[title.replace("## ", "").lower().replace(" ", "_")] = research_brief[start_index:end_index].strip()
                return sections
            
            # Initialize inputs dictionary to store all parameters for the task
            inputs = {}
            
            # Breakdown the research brief into sections and store it
            brief_sections = research_brief_breakdown(research_brief)
            self.research_brief = brief_sections
            
            # Add research brief sections to inputs with the exact parameter names expected by the task
            if 'competitive_analysis' in brief_sections:
                inputs['competitive_analysis'] = brief_sections['competitive_analysis']
                
            if 'content_outline' in brief_sections:
                inputs['content_outline'] = brief_sections['content_outline']
                
            if 'research_insights' in brief_sections:
                inputs['research_insights'] = brief_sections['research_insights']
                
            if 'seo_strategy' in brief_sections:
                inputs['seo_strategy'] = brief_sections['seo_strategy']
                
            logger.info(f"Added research brief sections to inputs: {', '.join(brief_sections.keys())}")
            if company_id:
                logger.info(f"Company ID: {company_id}")

            # For simplified implementation, we'll use basic brand parameters
            # In a full implementation, these would come from brand analysis services
            inputs.update({
                'brand_tone_keywords': '',
                'brand_tone_examples': '{}',
                'brand_voice_patterns': '',
                'brand_voice_examples': '{}',
                'brand_key_messages': '',
                'messaging_themes_keywords': '',
                'messaging_themes_examples': '{}',
                'personality_traits_keywords': '',
                'personality_traits_examples': '{}',
                'tonal_dos': '',
                'tonal_donts': '',
                'lexicon_replacements': '[]',
                'content_generation_guidelines_word_choice': '{}',
                'call_to_action_examples': '[]',
                'brand_memory': ''
            })
            
            # Log the final inputs for debugging
            logger.info(f"Final inputs for crew: {list(inputs.keys())}")
            
            # Create the crew using the crew() method which will handle formatting task descriptions
            crew_instance = self.crew(inputs=inputs)

            # Run the crew
            logger.info(f"Running crew with inputs: {list(inputs.keys())}")
            result = crew_instance.kickoff()

            # Extract article content from result
            article_content = str(result)

            logger.info("Article generation completed successfully")
            return {
                "status": "success",
                "message": "Article generated successfully",
                "content": article_content
            }

        except Exception as e:  
            error_msg = f"Error generating article: {str(e)}"
            logger.error(error_msg, exc_info=True)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": error_msg}
