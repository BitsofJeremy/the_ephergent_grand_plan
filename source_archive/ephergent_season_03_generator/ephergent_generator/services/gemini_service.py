from typing import Optional, Dict, Union

from google import genai
from google.genai import types
from flask import current_app
from ephergent_generator.services.universe_context_service import UniverseContextService
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """A service for generating stories and titles using Google's Gemini AI.

    This class provides methods to generate stories and titles using the Gemini API,
    with optional universe context integration. It handles API configuration, story
    generation, and title creation with various customization options.

    Attributes:
        client (genai.Client): The Gemini API client for generating content.
        model_name (str): The name of the Gemini model to use for generation.
        universe_context_service (UniverseContextService): Service for adding universe context to prompts.
    """
    def __init__(self):
        """Initialize the Gemini service.

        Sets up the Gemini client with a default model and universe context service.
        Automatically configures the API by calling _configure_api().
        """
        self.client: Optional[genai.Client] = None
        self.model_name: str = "gemini-2.5-flash"
        self.universe_context_service: UniverseContextService = UniverseContextService()
        self._configure_api()
    
    def _configure_api(self) -> None:
        """Configure the Gemini API with the API key.

        Retrieves the Gemini API key from the Flask application configuration
        and initializes the Gemini client. Raises a ValueError if no API key is found.

        Raises:
            ValueError: If the Gemini API key is not found in the configuration.
        """
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found in configuration")
            raise ValueError("Gemini API key is required")
        
        # Initialize the new genai client
        self.client = genai.Client(api_key=api_key)
    
    def generate_story_from_topic(self, topic: str, genre: Optional[str] = None, tone: Optional[str] = None, word_count: Optional[int] = 900, character_prompt: Optional[str] = None, dimension_location: Optional[str] = None) -> Dict[str, Union[str, int, bool]]:
        """Generate a story from a topic using Gemini AI with full Ephergent Universe context.

        This method leverages the Gemini AI to create a story based on the provided topic
        and optional contextual parameters. It integrates with the universe context service
        to create rich, contextually relevant story generations.

        Args:
            topic (str): The core story topic or central idea to explore.
            genre (str, optional): Preferred genre for the story (e.g., 'fantasy', 'sci-fi').
            tone (str, optional): Desired tone of the story (e.g., 'dark', 'humorous').
            word_count (int, optional): Target approximate word count for the story. Defaults to 900.
            character_prompt (str, optional): Custom character-specific prompt to override
                default universe context generation.
            dimension_location (str, optional): Specific Ephergent Universe dimension
                or setting to contextualize the story.

        Returns:
            Dict[str, Union[str, int, bool]]: A dictionary containing:
                - 'content': The generated story text
                - 'word_count': Actual number of words in the generated story
                - 'success': Boolean indicating successful generation
                - 'error' (optional): Error message if generation fails

        Raises:
            Exception: If no content is generated or an API error occurs.

        Example:
            >>> service = GeminiService()
            >>> result = service.generate_story_from_topic(
            ...     "A journey across parallel dimensions", 
            ...     genre="sci-fi", 
            ...     tone="philosophical", 
            ...     word_count=1500, 
            ...     dimension_location="Quantum Realm"
            ... )
            >>> print(result['content'])
        """
        try:
            # Use character prompt if provided, otherwise build universe-aware prompt
            if character_prompt:
                story_prompt = character_prompt
            else:
                story_prompt = self.universe_context_service.build_story_prompt_with_universe_context(
                    topic, genre, tone, word_count, dimension_location
                )
            
            # Generate content using new Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=story_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.75,  # Match Season 2's creative balance
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            
            if not response.text:
                raise Exception("No content generated from Gemini")
            
            content = response.text.strip()
            word_count_actual = len(content.split()) if content else 0
            
            return {
                'content': content,
                'word_count': word_count_actual,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error generating story from topic: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def generate_title(self, topic: str, content: str, genre: Optional[str] = None, tone: Optional[str] = None) -> Dict[str, Union[str, bool]]:
        """Generate a creative and contextually relevant title for a story.

        Uses the Gemini AI to create a title that captures the essence of the story
        based on its topic, content, genre, and tone. The method ensures the title
        is concise, intriguing, and aligned with the story's core themes.

        Args:
            topic (str): The original story topic that inspired the content.
            content (str): The full story text to derive title inspiration from.
            genre (str, optional): Genre of the story to inform title generation.
            tone (str, optional): Tone of the story to influence title style.

        Returns:
            Dict[str, Union[str, bool]]: A dictionary containing:
                - 'title': The generated story title
                - 'success': Boolean indicating successful title generation
                - 'error' (optional): Error message if title generation fails

        Raises:
            Exception: If no title is generated or an API error occurs.

        Example:
            >>> service = GeminiService()
            >>> story_content = \"A tale of exploration and discovery...\"
            >>> result = service.generate_title(
            ...     \"Scientific expedition\", 
            ...     story_content, 
            ...     genre=\"sci-fi\", 
            ...     tone=\"inspiring\"
            ... )
            >>> print(result['title'])
        """
        try:
            # Build the title generation prompt
            title_prompt = self._build_title_prompt(topic, content, genre, tone)
            
            # Generate title using new Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=title_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.75,  # Match Season 2's creative balance
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            
            if not response.text:
                raise Exception("No title generated from Gemini")
            
            # Clean up the title (remove quotes, newlines, etc.)
            title = response.text.strip().replace('"', '').replace("'", "").split('\n')[0]
            
            # Ensure reasonable length
            if len(title) > 200:
                title = title[:197] + "..."
            
            return {
                'title': title,
                'success': True
            }
        
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _build_story_prompt(self, topic: str, genre: Optional[str] = None, tone: Optional[str] = None, word_count: Optional[int] = 900) -> str:
        """Build a comprehensive story generation prompt.

        Constructs a detailed prompt for the Gemini AI to generate a story with
        specific guidelines and optional customization.

        Args:
            topic (str): The core topic or concept for the story.
            genre (str, optional): The preferred genre of the story.
            tone (str, optional): The desired tone of the story.
            word_count (int, optional): The target length of the story in words. Defaults to 900.

        Returns:
            str: A fully constructed prompt for story generation.

        Example:
            >>> service = GeminiService()
            >>> prompt = service._build_story_prompt(
            ...     "A journey through time", 
            ...     genre="sci-fi", 
            ...     tone="mysterious", 
            ...     word_count=1000
            ... )
        """
        prompt = f"Create a compelling short story based on this topic: {topic}\n\n"
        
        if genre:
            prompt += f"Genre: {genre}\n"
        
        if tone:
            prompt += f"Tone: {tone}\n"
        
        if word_count:
            prompt += f"Target length: approximately {word_count} words\n"
        
        prompt += "\nRequirements:\n"
        prompt += "- Create an engaging narrative with clear beginning, middle, and end\n"
        prompt += "- Include vivid descriptions and compelling characters\n"
        prompt += "- Focus on showing rather than telling\n"
        prompt += "- Make it suitable for a general audience\n\n"
        prompt += "Please write only the story content, without a separate title at the beginning."
        
        return prompt
    
    def _build_title_prompt(self, topic: str, content: str, genre: Optional[str] = None, tone: Optional[str] = None) -> str:
        """Build a detailed title generation prompt for the Gemini AI.

        Constructs a prompt that guides the AI in creating an engaging title
        based on the story's content, topic, genre, and tone.

        Args:
            topic (str): The original story topic.
            content (str): The full story content to derive the title from.
            genre (str, optional): The genre of the story.
            tone (str, optional): The tone of the story.

        Returns:
            str: A comprehensive prompt for title generation.

        Example:
            >>> service = GeminiService()
            >>> prompt = service._build_title_prompt(
            ...     "A scientist's discovery", 
            ...     "Full story content...", 
            ...     genre="sci-fi", 
            ...     tone="suspenseful"
            ... )
        """
        # Truncate content for prompt efficiency
        content_preview = content[:1000] + "..." if len(content) > 1000 else content
        
        prompt = f"Create a compelling, creative title for this story.\n\n"
        prompt += f"Original Topic: {topic}\n\n"
        
        if genre:
            prompt += f"Genre: {genre}\n"
        if tone:
            prompt += f"Tone: {tone}\n"
        
        prompt += f"\nStory Content Preview:\n{content_preview}\n\n"
        prompt += "Requirements:\n"
        prompt += "- Create a catchy, memorable title\n"
        prompt += "- Keep it under 100 characters\n"
        prompt += "- Make it intriguing and relevant to the story\n"
        prompt += "- Avoid clichés when possible\n\n"
        prompt += "Please provide only the title, without quotes or additional text."
        
        return prompt
    
    def generate_story(self, prompt: str, genre: Optional[str] = None, tone: Optional[str] = None, word_count: Optional[int] = 900) -> Dict[str, Union[str, int, bool]]:
        """Legacy method for generating a complete story with title (backward compatibility).

        Generates a story using generate_story_from_topic and attempts to generate
        a title using generate_title. Maintained for compatibility with older code.

        Args:
            prompt (str): The story topic or initial prompt.
            genre (str, optional): The preferred genre of the story.
            tone (str, optional): The desired tone of the story.
            word_count (int, optional): The target length of the story in words. Defaults to 900.

        Returns:
            Dict[str, Union[str, int, bool]]: A dictionary containing:
                - 'title': Generated story title
                - 'content': Generated story content
                - 'word_count': Actual number of words in the story
                - 'success': Boolean indicating successful generation

        Example:
            >>> service = GeminiService()
            >>> result = service.generate_story(
            ...     "A detective's last case", 
            ...     genre="mystery", 
            ...     tone="noir", 
            ...     word_count=1000
            ... )
            >>> print(result['title'])
            >>> print(result['content'])
        """
        story_result = self.generate_story_from_topic(prompt, genre, tone, word_count)
        
        if not story_result.get('success'):
            return story_result
        
        content = story_result['content']
        
        # Try to generate a title
        title_result = self.generate_title(prompt, content, genre, tone)
        title = title_result.get('title', 'Untitled Story') if title_result.get('success') else 'Untitled Story'
        
        return {
            'title': title,
            'content': content,
            'word_count': story_result['word_count'],
            'success': True
        }
