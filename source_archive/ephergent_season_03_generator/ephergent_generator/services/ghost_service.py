"""Ghost Blog Publishing Service for AI-Generated Content

Provides comprehensive integration with Ghost CMS API for publishing
AI-generated stories as blog posts. Handles content formatting, image
uploads, metadata generation, and post management.

Features:
    - Dynamic content formatting
    - JWT authentication
    - Image file uploads
    - Automatic tag and excerpt generation
    - Post creation, updating, and retrieval

Requires configuration via environment variables:
    - GHOST_ADMIN_KEY
    - GHOST_API_KEY
    - GHOST_DOMAIN

Usage:
    >>> service = GhostService()
    >>> post = service.create_post(story_data)
    >>> print(post['post_url'])
"""
import os
import json
import requests
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import jwt
import markdown
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GhostService:
    """Comprehensive service for publishing AI-generated stories to Ghost blog.

    Manages the entire workflow of transforming AI-generated story data
    into publishable blog posts on Ghost CMS. Handles authentication,
    content processing, file uploads, and API interactions.

    Core Responsibilities:
        - Generate JWT tokens for Ghost Admin API
        - Upload supporting media (images)
        - Format story content for blog presentation
        - Create and update blog posts
        - Retrieve post information

    Attributes:
        admin_key (str): Ghost Admin API key
        api_key (str): Ghost API key
        domain (str): Ghost CMS domain
        admin_api_url (str): Constructed admin API endpoint

    Note:
        Requires proper configuration of environment variables
        for successful operation.
    """
    
    def __init__(self):
        """Initialize the Ghost service with API credentials from environment variables.

        Retrieves Ghost CMS configuration from environment variables and sets up
        the service for API interactions. Logs an error if any required credentials
        are missing.

        Environment Variables:
            GHOST_ADMIN_KEY (str): Admin API key for authentication
            GHOST_API_KEY (str): Regular API key for access
            GHOST_DOMAIN (str): Domain of the Ghost CMS instance

        Attributes:
            admin_key (str): Admin key retrieved from environment
            api_key (str): API key retrieved from environment
            domain (str): Ghost CMS domain
            admin_api_url (str): Constructed full admin API URL
        """
        self.admin_key = os.getenv('GHOST_ADMIN_KEY')
        self.api_key = os.getenv('GHOST_API_KEY')
        self.domain = os.getenv('GHOST_DOMAIN')
        
        if not all([self.admin_key, self.api_key, self.domain]):
            logger.error("Missing Ghost API configuration. Check GHOST_ADMIN_KEY, GHOST_API_KEY, and GHOST_DOMAIN")
            
        self.admin_api_url = f"https://{self.domain}/ghost/api/admin" if self.domain else ""
        
        logger.info(f"Ghost service initialized - Domain: {self.domain}")
    
    def is_configured(self) -> bool:
        """Check if the Ghost service is properly configured.

        Verifies that all required configuration parameters are present.

        Returns:
            bool: True if all required configuration keys are set, False otherwise

        Examples:
            >>> ghost_service = GhostService()
            >>> ghost_service.is_configured()
            True
        """
        return bool(self.admin_key and self.api_key and self.domain)
    
    def get_jwt_token(self) -> str:
        """Generate a JSON Web Token (JWT) for Ghost Admin API authentication.

        Creates a short-lived JWT for authenticating requests to the Ghost Admin API.
        The token is generated using the admin key's ID and secret, with a 5-minute
        expiration window.

        Returns:
            str: A JWT token for Ghost Admin API authentication

        Raises:
            ValueError: If no admin key is configured

        Notes:
            - Token expires 5 minutes after generation
            - Uses HS256 algorithm for token signing
            - Audience set to '/v3/admin/'
        """
        if not self.admin_key:
            raise ValueError("Ghost Admin Key not configured")
            
        # Split the key into ID and SECRET
        key_id, secret = self.admin_key.split(':')
        
        # Prepare header and payload
        iat = int(datetime.now().timestamp())
        
        header = {'alg': 'HS256', 'typ': 'JWT', 'kid': key_id}
        payload = {
            'iat': iat,
            'exp': iat + 5 * 60,  # Token expires in 5 minutes
            'aud': '/v3/admin/'
        }
        
        # Create the token
        token = jwt.encode(
            payload,
            bytes.fromhex(secret),
            algorithm='HS256',
            headers=header
        )
        return token
    
    def upload_image(self, image_path: Path) -> Optional[str]:
        """Upload an image to the Ghost CMS and return its uploaded URL.

        Handles image file upload to Ghost, with comprehensive error checking.

        Args:
            image_path (Path): Absolute path to the image file to upload

        Returns:
            Optional[str]: The URL of the uploaded image, or None if upload fails

        Raises:
            Logs detailed error messages without raising exceptions

        Notes:
            - Supports PNG, JPEG, and WebP image uploads
            - Uses JWT authentication
            - Automatically handles file opening and request generation
            - Logs upload status and any errors encountered
            - Defaults to PNG mime type for unknown extensions

        Examples:
            >>> ghost_service = GhostService()
            >>> image_url = ghost_service.upload_image(Path('/path/to/image.png'))
            >>> print(image_url)  # Prints the uploaded image URL or None
        """
        if not self.is_configured():
            logger.error("Ghost service not configured")
            return None
            
        if not image_path.exists():
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            # Determine MIME type based on file extension
            file_ext = image_path.suffix.lower()
            if file_ext == '.png':
                mime_type = 'image/png'
            elif file_ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif file_ext == '.webp':
                mime_type = 'image/webp'
            else:
                # Default to PNG for unknown types since that's our new standard
                mime_type = 'image/png'
                logger.warning(f"Unknown image extension {file_ext}, defaulting to PNG mime type")
            
            with open(image_path, 'rb') as img_file:
                files = {'file': (image_path.name, img_file, mime_type)}
                
                jwt_token = self.get_jwt_token()
                headers = {
                    "Authorization": f"Ghost {jwt_token}",
                    "Accept-Version": "v3.0"
                }
                
                upload_url = f"{self.admin_api_url}/images/upload/"
                response = requests.post(upload_url, headers=headers, files=files)
                
                if response.status_code in [200, 201]:
                    image_url = response.json()["images"][0]["url"]
                    logger.info(f"Uploaded image to Ghost: {image_url}")
                    return image_url
                else:
                    logger.error(f"Failed to upload image: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error uploading image to Ghost: {e}")
            return None
    
    
    def create_youtube_embed(self, youtube_url: str) -> str:
        """Create a YouTube embed HTML for Ghost"""
        try:
            # Extract video ID from YouTube URL
            if 'watch?v=' in youtube_url:
                video_id = youtube_url.split('watch?v=')[1].split('&')[0]
            elif 'youtu.be/' in youtube_url:
                video_id = youtube_url.split('/')[-1].split('?')[0]
            else:
                video_id = youtube_url.split('/')[-1]
            
            embed_url = f"https://www.youtube.com/embed/{video_id}"
            
            return f'''<figure class="kg-card kg-embed-card">
<iframe width="560" height="315" src="{embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
</figure>'''
            
        except Exception as e:
            logger.error(f"Error creating YouTube embed: {e}")
            return f'<p>Watch the video: <a href="{youtube_url}">{youtube_url}</a></p>'
    
    def format_story_content(self, story_data: Dict[str, Any]) -> str:
        """Format story content for Ghost blog post"""
        
        # Get story details
        title = story_data.get('title', 'Untitled Story')
        content = story_data.get('content', '')
        audio_url = story_data.get('audio_url')
        youtube_url = story_data.get('youtube_url')
        image_urls = story_data.get('image_urls', {})
        narrator_character = story_data.get('narrator_character', {})
        
        # Start building the HTML content
        html_content = []
        
        # Skip audio player - audio files are only used for video generation
        
        # Add YouTube video if available
        if youtube_url:
            youtube_embed = self.create_youtube_embed(youtube_url)
            html_content.append(youtube_embed)
            html_content.append('')
        
        # Add story introduction
        if narrator_character and isinstance(narrator_character, dict):
            character_name = narrator_character.get('name', 'Unknown Narrator')
            html_content.append(f'<p><em>Narrated by {character_name}</em></p>')
            html_content.append('')
        
        # Process story content and add images - comprehensive newline cleanup
        if content:
            # Handle escaped newlines step by step to avoid issues
            clean_content = content
            
            # First, handle double escaped newlines (\\n\\n)
            clean_content = clean_content.replace('\\\\n\\\\n', '\n\n')
            clean_content = clean_content.replace('\\n\\n', '\n\n')
            
            # Then handle single escaped newlines (\\n)
            clean_content = clean_content.replace('\\\\n', '\n')
            clean_content = clean_content.replace('\\n', '\n')
            
            # Remove excessive whitespace and empty lines, but preserve paragraph breaks
            lines = clean_content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                stripped_line = line.strip()
                if stripped_line:  # Non-empty line
                    cleaned_lines.append(stripped_line)
                elif cleaned_lines and cleaned_lines[-1]:  # Empty line after non-empty line
                    cleaned_lines.append('')  # Preserve paragraph break
            
            # Join lines back and split into paragraphs
            clean_content = '\n'.join(cleaned_lines)
            story_paragraphs = [p.strip() for p in clean_content.split('\n\n') if p.strip()]
        else:
            story_paragraphs = []
        
        # Handle images and story content dynamically
        story_sections = self._split_content_into_sections(story_paragraphs)
        
        # Skip feature image in body - it's already set as the post's featured image
        
        # Add beginning image and content
        if 'beginning' in image_urls:
            html_content.append(f'<figure class="kg-card kg-image-card">')
            html_content.append(f'<img src="{image_urls["beginning"]}" class="kg-image" alt="Story beginning" loading="lazy">')
            html_content.append(f'</figure>')
            html_content.append('')
        
        if story_sections['beginning']:
            for paragraph in story_sections['beginning']:
                html_content.append(f'<p>{paragraph}</p>')
            html_content.append('')
        
        # Add middle image and content
        if 'middle' in image_urls:
            html_content.append(f'<figure class="kg-card kg-image-card">')
            html_content.append(f'<img src="{image_urls["middle"]}" class="kg-image" alt="Story middle" loading="lazy">')
            html_content.append(f'</figure>')
            html_content.append('')
        
        if story_sections['middle']:
            for paragraph in story_sections['middle']:
                html_content.append(f'<p>{paragraph}</p>')
            html_content.append('')
        
        # Add final image and content
        if 'final' in image_urls:
            html_content.append(f'<figure class="kg-card kg-image-card">')
            html_content.append(f'<img src="{image_urls["final"]}" class="kg-image" alt="Story conclusion" loading="lazy">')
            html_content.append(f'</figure>')
            html_content.append('')
        
        if story_sections['final']:
            for paragraph in story_sections['final']:
                html_content.append(f'<p>{paragraph}</p>')
        
        # Add any additional images that don't fit the standard pattern at the end
        additional_images = {k: v for k, v in image_urls.items() 
                           if k not in ['beginning', 'middle', 'final', 'feature']}
        
        if additional_images:
            html_content.append('')
            html_content.append('<h3>Additional Images</h3>')
            for image_type, image_url in additional_images.items():
                html_content.append(f'<figure class="kg-card kg-image-card">')
                html_content.append(f'<img src="{image_url}" class="kg-image" alt="{image_type.replace("_", " ").title()}" loading="lazy">')
                html_content.append(f'<figcaption>{image_type.replace("_", " ").title()}</figcaption>')
                html_content.append(f'</figure>')
                html_content.append('')
        
        return '\\n'.join(html_content)
    
    def _split_content_into_sections(self, paragraphs: List[str]) -> Dict[str, List[str]]:
        """Split story content into beginning, middle, and final sections.

        Divides a list of paragraphs into three sections, optimizing for
        different story lengths. Useful for creating a structured narrative
        presentation across multiple images or sections.

        Args:
            paragraphs (List[str]): A list of story paragraphs to be divided

        Returns:
            Dict[str, List[str]]: A dictionary with three keys: 'beginning', 'middle',
            and 'final', each containing an appropriate subset of paragraphs

        Strategy:
            - For 1-3 paragraphs: Distributes paragraphs across sections
            - For 4+ paragraphs: Divides content into roughly equal thirds

        Examples:
            >>> gs = GhostService()
            >>> paras = ['Intro', 'Context', 'Development', 'Twist', 'Conclusion']
            >>> gs._split_content_into_sections(paras)
            {
                'beginning': ['Intro', 'Context'],
                'middle': ['Development', 'Twist'],
                'final': ['Conclusion']
            }
        """
        if not paragraphs:
            return {'beginning': [], 'middle': [], 'final': []}
        
        total_paragraphs = len(paragraphs)
        
        if total_paragraphs <= 3:
            # For short stories, put one paragraph in each section
            return {
                'beginning': paragraphs[:1] if total_paragraphs >= 1 else [],
                'middle': paragraphs[1:2] if total_paragraphs >= 2 else [],
                'final': paragraphs[2:] if total_paragraphs >= 3 else []
            }
        else:
            # For longer stories, divide roughly into thirds
            third = total_paragraphs // 3
            return {
                'beginning': paragraphs[:third],
                'middle': paragraphs[third:third*2],
                'final': paragraphs[third*2:]
            }
    
    def create_post(self, story_data: Dict[str, Any], status: str = "draft") -> Optional[Dict[str, Any]]:
        """Create a new blog post in Ghost CMS from provided story data.

        Transforms story data into a fully formatted Ghost blog post with
        comprehensive content processing, image handling, and metadata generation.

        Args:
            story_data (Dict[str, Any]): Comprehensive data describing the story
                to be published. Expected keys include:
                - 'title': Story title
                - 'content': Story text content
                - 'audio_url' (optional): Audio version of the story
                - 'youtube_url' (optional): Related YouTube video
                - 'image_urls' (optional): Dict of image URLs for different story sections
                - 'narrator_character' (optional): Information about the story's narrator
            status (str, optional): Post publication status. Defaults to "draft".

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing post creation details:
                - 'post_id': Unique identifier of the created post
                - 'post_url': Public URL of the created post
                - 'status': Publication status
                - 'full_response': Complete Ghost API response
            Returns None if post creation fails

        Publication Statuses:
            - "draft": Unpublished, private post
            - "published": Publicly visible post
            - "scheduled": Post set for future publication

        Examples:
            >>> ghost_service = GhostService()
            >>> story_data = {
            ...     'title': 'Quantum Horizons',
            ...     'content': 'In a world beyond imagination...',
            ...     'audio_url': 'https://example.com/audio.mp3',
            ...     'narrator_character': {'name': 'Dr. Aria Chen'}
            ... }
            >>> result = ghost_service.create_post(story_data)
            >>> print(result['post_url'])  # Prints the URL of the created post
        """
        if not self.is_configured():
            logger.error("Ghost service not configured")
            return None
        
        try:
            # Format the content
            html_content = self.format_story_content(story_data)
            # TODO Remove any unwanted escape characters if necessary
            html_content = html_content.replace('\\n', '')
            html_content = html_content.replace('\n', '')
            
            # Prepare post data
            post_data = {
                "posts": [{
                    "title": story_data.get('title', 'Untitled Story'),
                    "html": html_content,
                    "status": status,
                    "authors": ['ephergent+pixelparadox@gmail.com'],  # Default author
                    "tags": self._generate_tags(story_data),
                    "custom_excerpt": self._generate_excerpt(story_data),
                }]
            }
            
            # Add featured image if available
            if 'featured_image_url' in story_data:
                post_data["posts"][0]["feature_image"] = story_data['featured_image_url']
            
            # Create the post
            jwt_token = self.get_jwt_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Ghost {jwt_token}'
            }
            
            api_url = f"{self.admin_api_url}/posts/?source=html"
            response = requests.post(api_url, json=post_data, headers=headers)
            
            if response.status_code in [200, 201]:
                post_response = response.json()
                post_id = post_response['posts'][0]['id']
                post_url = post_response['posts'][0]['url']
                
                logger.info(f"Successfully created Ghost post: {story_data.get('title', 'Untitled')} (ID: {post_id})")
                
                return {
                    'post_id': post_id,
                    'post_url': post_url,
                    'status': status,
                    'full_response': post_response
                }
            else:
                logger.error(f"Failed to create Ghost post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Ghost post: {e}")
            return None
    
    def _generate_tags(self, story_data: Dict[str, Any]) -> List[str]:
        """Generate a list of appropriate tags for the story.

        Creates a dynamic set of tags based on various story attributes.
        Allows for easy categorization and discovery of content.

        Args:
            story_data (Dict[str, Any]): A dictionary containing story metadata

        Returns:
            List[str]: A list of generated tags

        Tag Generation Strategy:
            - Always includes base tags: 'ephergent', 'ai-generated', 'season-02'
            - Adds optional tags for:
                * Genre (if specified)
                * Narrator character
                * Media types (audio/video)

        Examples:
            >>> gs = GhostService()
            >>> story_data = {
            ...     'genre': 'Science Fiction',
            ...     'narrator_character': {'id': '42'},
            ...     'audio_url': 'http://example.com/audio.mp3'
            ... }
            >>> gs._generate_tags(story_data)
            ['ephergent', 'ai-generated', 'season-02', 'science fiction', 'narrator-42', 'audio-story']
        """
        tags = ["ephergent", "ai-generated", "season-02"]
        
        # Add genre if specified
        if story_data.get('genre'):
            tags.append(story_data['genre'].lower())
        
        # Add character tag
        narrator_char = story_data.get('narrator_character')
        if narrator_char and isinstance(narrator_char, dict) and narrator_char.get('id'):
            character_id = narrator_char['id']
            tags.append(f"narrator-{character_id}")
        
        # Add media type tags
        if story_data.get('youtube_url'):
            tags.append("video-story")
        
        return tags
    
    def _generate_excerpt(self, story_data: Dict[str, Any]) -> str:
        """Generate a custom, engaging excerpt for the story using Gemini AI.

        Creates a concise, intriguing summary designed to entice readers
        to click and read the full story. Employs AI-driven content generation
        with fallback mechanisms.

        Args:
            story_data (Dict[str, Any]): Dictionary containing story metadata
                and content for excerpt generation

        Returns:
            str: A compelling, truncated excerpt of maximum 200 characters

        Excerpt Generation Strategy:
            1. Attempt AI-generated excerpt via Gemini
            2. Fallback to first sentence extraction
            3. Final fallback to generic narrator description

        Notes:
            - Uses first 1000 characters of content for AI prompt
            - Ensures excerpt is truncated to 200 characters
            - Handles various failure scenarios gracefully

        Raises:
            Logs errors but does not raise exceptions

        Examples:
            >>> gs = GhostService()
            >>> story_data = {
            ...     'title': 'Quantum Dreams',
            ...     'content': 'In the year 2150, technology reshaped humanity...',
            ...     'narrator_character': {'name': 'Dr. Elena Rodriguez'}
            ... }
            >>> excerpt = gs._generate_excerpt(story_data)
            >>> len(excerpt) <= 200
            True
        """
        content = story_data.get('content', '')
        title = story_data.get('title', 'Untitled Story')
        
        if not content:
            narrator_char = story_data.get('narrator_character')
            narrator_name = 'one of our characters'
            if narrator_char and isinstance(narrator_char, dict):
                narrator_name = narrator_char.get('name', 'one of our characters')
            return f"An AI-generated story narrated by {narrator_name}."
        
        try:
            # Import Gemini service for excerpt generation
            from ephergent_generator.services.gemini_service import GeminiService
            from flask import has_app_context, current_app

            # Check if we're in an app context before using Gemini
            if has_app_context():
                gemini = GeminiService()

                # Create excerpt generation prompt
                excerpt_prompt = f"""Create an engaging excerpt for this story that will entice readers to click and read more.

Title: {title}

Story Content:
{content[:1000]}...

Requirements:
- Maximum 200 characters
- Create intrigue and interest
- Don't give away the ending
- Make it engaging and clickable
- Suitable for a blog excerpt

Please provide only the excerpt text, no quotes or additional formatting."""

                from google.genai import types

                response = gemini.client.models.generate_content(
                    model=gemini.model_name,
                    contents=excerpt_prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                )

                if response.text:
                    excerpt = response.text.strip()
                    # Ensure it's under 200 characters
                    if len(excerpt) > 200:
                        excerpt = excerpt[:197] + "..."
                    logger.info(f"Generated AI excerpt: {excerpt}")
                    return excerpt
                else:
                    logger.warning("Gemini did not generate excerpt, using fallback")
            else:
                logger.warning("No Flask app context available for Gemini excerpt generation, using fallback")

        except Exception as e:
            logger.error(f"Error generating excerpt with Gemini: {e}")
        
        # Fallback to original logic if Gemini fails
        if content:
            # Take first sentence or first 150 characters
            first_sentence = content.split('.')[0] + '.' if '.' in content else content
            return first_sentence[:200] if len(first_sentence) > 200 else first_sentence
        
        narrator_char = story_data.get('narrator_character')
        narrator_name = 'one of our characters'
        if narrator_char and isinstance(narrator_char, dict):
            narrator_name = narrator_char.get('name', 'one of our characters')
        return f"An AI-generated story narrated by {narrator_name}."
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific blog post from Ghost CMS by its unique identifier.

        Fetches comprehensive details about a single post, allowing for
        content inspection, status verification, and metadata review.

        Args:
            post_id (str): Unique identifier of the post to retrieve

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing full post details,
            or None if retrieval fails. Post details include:
                - Title
                - HTML content
                - Publication status
                - Tags
                - Publication date
                - Featured image
                - And other Ghost CMS metadata

        Raises:
            Logs errors if post retrieval fails, but does not raise exceptions

        Authentication:
            - Uses JWT token for Ghost Admin API access
            - Requires proper configuration of Ghost service

        Examples:
            >>> ghost_service = GhostService()
            >>> post = ghost_service.get_post_by_id('post_123')
            >>> if post:
            ...     print(post['title'])  # Prints the post's title
            ...     print(post['status'])  # Prints publication status
        """
        if not self.is_configured():
            logger.error("Ghost service not configured")
            return None
        
        try:
            jwt_token = self.get_jwt_token()
            headers = {
                'Authorization': f'Ghost {jwt_token}',
                'Accept-Version': 'v3.0'
            }
            
            api_url = f"{self.admin_api_url}/posts/{post_id}/"
            response = requests.get(api_url, headers=headers)
            
            if response.status_code == 200:
                post_data = response.json()
                logger.info(f"Successfully fetched Ghost post: {post_id}")
                return post_data['posts'][0] if post_data.get('posts') else None
            else:
                logger.error(f"Failed to fetch Ghost post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Ghost post: {e}")
            return None
    
    def update_post(self, post_id: str, story_data: Dict[str, Any], status: str = None) -> Optional[Dict[str, Any]]:
        """Update an existing blog post in Ghost CMS with new story data.

        Allows comprehensive updates to a previously created post, including
        content, metadata, and publication status.

        Args:
            post_id (str): Unique identifier of the post to update
            story_data (Dict[str, Any]): Updated story data. Similar structure
                to create_post method. Includes:
                - 'title': Updated story title
                - 'content': Updated story text content
                - 'audio_url' (optional): New or updated audio URL
                - 'youtube_url' (optional): Updated YouTube video link
                - 'image_urls' (optional): Updated image URLs
                - 'narrator_character' (optional): Updated narrator information
            status (str, optional): New publication status. If None, existing
                status is preserved.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing post update details:
                - 'post_id': Identifier of the updated post
                - 'post_url': Updated public URL
                - 'status': New publication status
                - 'full_response': Complete Ghost API response
            Returns None if post update fails

        Publication Statuses:
            - "draft": Unpublished, private post
            - "published": Publicly visible post
            - "scheduled": Post set for future publication

        Notes:
            - Preserves existing post metadata not explicitly updated
            - Regenerates tags and excerpt based on new content
            - Handles potential API and data processing errors

        Examples:
            >>> ghost_service = GhostService()
            >>> updated_story = {
            ...     'title': 'Quantum Horizons: Revised Edition',
            ...     'content': 'An expanded narrative exploring deeper themes...'
            ... }
            >>> result = ghost_service.update_post('post_123', updated_story, status='published')
            >>> print(result['post_url'])  # Prints the updated post's URL
        """
        if not self.is_configured():
            logger.error("Ghost service not configured")
            return None
        
        try:
            # First, get the existing post to preserve certain fields
            existing_post = self.get_post_by_id(post_id)
            if not existing_post:
                logger.error(f"Cannot update post {post_id} - post not found")
                return None
            
            # Format the content
            html_content = self.format_story_content(story_data)
            
            # Prepare update data
            update_data = {
                "posts": [{
                    "id": post_id,
                    "updated_at": existing_post.get('updated_at'),  # Required for updates
                    "title": story_data.get('title', existing_post.get('title', 'Untitled Story')),
                    "html": html_content,
                    "custom_excerpt": self._generate_excerpt(story_data),
                    "tags": self._generate_tags(story_data),
                }]
            }
            
            # Update status if provided
            if status:
                update_data["posts"][0]["status"] = status
            
            # Add featured image if available
            if 'featured_image_url' in story_data:
                update_data["posts"][0]["feature_image"] = story_data['featured_image_url']
            
            # Update the post
            jwt_token = self.get_jwt_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Ghost {jwt_token}'
            }
            
            api_url = f"{self.admin_api_url}/posts/{post_id}/?source=html"
            response = requests.put(api_url, json=update_data, headers=headers)
            
            if response.status_code in [200, 201]:
                post_response = response.json()
                post_url = post_response['posts'][0]['url']
                
                logger.info(f"Successfully updated Ghost post: {story_data.get('title', 'Untitled')} (ID: {post_id})")
                
                return {
                    'post_id': post_id,
                    'post_url': post_url,
                    'status': post_response['posts'][0].get('status', 'unknown'),
                    'full_response': post_response
                }
            else:
                logger.error(f"Failed to update Ghost post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating Ghost post: {e}")
            return None

    def get_all_posts(self, limit: int = 15, include_drafts: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Retrieve a list of blog posts from Ghost CMS, useful for content management
        and troubleshooting.

        Fetches multiple posts with optional filtering and comprehensive details.

        Args:
            limit (int, optional): Maximum number of posts to retrieve.
                Defaults to 15. Maximum recommended value is 100.
            include_drafts (bool, optional): Whether to include draft and
                scheduled posts alongside published ones. Defaults to True.

        Returns:
            Optional[List[Dict[str, Any]]]: A list of post dictionaries containing
            full post details, or None if retrieval fails. Each post includes:
                - Title
                - Publication status
                - HTML content
                - Tags
                - Authors
                - Publication dates
                - And other Ghost CMS metadata

        Raises:
            Logs errors if post retrieval fails, but does not raise exceptions

        Authentication:
            - Uses JWT token for Ghost Admin API access
            - Requires proper configuration of Ghost service

        Examples:
            >>> ghost_service = GhostService()
            >>> posts = ghost_service.get_all_posts(limit=5, include_drafts=False)
            >>> for post in posts:
            ...     print(post['title'])  # Prints titles of retrieved posts
            ...     print(post['status'])  # Prints their publication status
        """
        if not self.is_configured():
            logger.error("Ghost service not configured")
            return None
        
        try:
            jwt_token = self.get_jwt_token()
            headers = {
                'Authorization': f'Ghost {jwt_token}',
                'Accept-Version': 'v3.0'
            }
            
            # Build query parameters
            params = {
                'limit': str(limit),
                'include': 'tags,authors',
                'formats': 'html,plaintext'
            }
            
            if include_drafts:
                params['filter'] = 'status:[draft,published,scheduled]'
            
            api_url = f"{self.admin_api_url}/posts/"
            response = requests.get(api_url, headers=headers, params=params)
            
            if response.status_code == 200:
                posts_data = response.json()
                posts = posts_data.get('posts', [])
                logger.info(f"Successfully fetched {len(posts)} Ghost posts")
                return posts
            else:
                logger.error(f"Failed to fetch Ghost posts: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Ghost posts: {e}")
            return None

    def get_service_status(self) -> Dict[str, Any]:
        """Retrieve the current configuration and operational status of the Ghost service.

        Provides a comprehensive overview of the service's configuration,
        helping diagnose potential integration or authentication issues.

        Returns:
            Dict[str, Any]: A dictionary containing service diagnostic information:
                - 'service_name': Fixed value "Ghost Blog"
                - 'configured': Boolean indicating if service is properly configured
                - 'domain': Configured Ghost CMS domain
                - 'admin_api_url': Constructed admin API endpoint
                - 'has_admin_key': Whether an admin key is present
                - 'has_api_key': Whether an API key is present

        Notes:
            - Does not perform live API validation
            - Provides a quick configuration snapshot

        Examples:
            >>> ghost_service = GhostService()
            >>> status = ghost_service.get_service_status()
            >>> print(status['configured'])  # Prints whether service is configured
            >>> print(status['domain'])      # Prints configured domain
        """
        return {
            "service_name": "Ghost Blog",
            "configured": self.is_configured(),
            "domain": self.domain,
            "admin_api_url": self.admin_api_url,
            "has_admin_key": bool(self.admin_key),
            "has_api_key": bool(self.api_key)
        }