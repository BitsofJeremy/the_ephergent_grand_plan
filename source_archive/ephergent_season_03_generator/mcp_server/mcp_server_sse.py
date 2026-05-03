#!/usr/bin/env python3
"""
MCP Server with SSE Transport for Remote VM Deployment

This version uses Server-Sent Events (SSE) instead of STDIO, making it suitable
for hosting on a remote VM. It authenticates via API keys and communicates
with the Ephergent Flask API instead of direct database access.

Usage:
    python mcp_server_sse.py --api-url http://your-server:5000 --api-key your_api_key

Environment Variables:
    EPHERGENT_API_URL: Base URL for the Ephergent API (default: http://localhost:5000)
    EPHERGENT_API_KEY: Admin API key for authentication (required)
    MCP_HOST: Host to bind the MCP server (default: 127.0.0.1)
    MCP_PORT: Port for the MCP server (default: 8765)
"""

import asyncio
import logging
import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server_sse.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class MCPConfig:
    """MCP Server configuration"""
    def __init__(self):
        self.api_url = os.getenv('EPHERGENT_API_URL', 'http://localhost:5000')
        self.api_key = os.getenv('EPHERGENT_API_KEY', '')
        self.host = os.getenv('MCP_HOST', '127.0.0.1')
        self.port = int(os.getenv('MCP_PORT', '8765'))

        if not self.api_key:
            raise ValueError("EPHERGENT_API_KEY environment variable is required")

        # Remove trailing slash from API URL
        self.api_url = self.api_url.rstrip('/')

    @property
    def headers(self):
        """HTTP headers for API requests"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

# Initialize config (will be set in main())
config: Optional[MCPConfig] = None

# Initialize MCP server
server = Server("ephergent-story-generator-remote")

# HTTP client for API calls
http_client: Optional[httpx.AsyncClient] = None


async def api_get(endpoint: str, params: dict = None) -> dict:
    """Make GET request to Ephergent API"""
    url = f"{config.api_url}/api/{endpoint}"
    try:
        response = await http_client.get(url, headers=config.headers, params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API GET error ({url}): {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"API GET error ({url}): {str(e)}")
        raise


async def api_post(endpoint: str, data: dict) -> dict:
    """Make POST request to Ephergent API"""
    url = f"{config.api_url}/api/{endpoint}"
    try:
        response = await http_client.post(url, headers=config.headers, json=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API POST error ({url}): {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"API POST error ({url}): {str(e)}")
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools for story generation."""
    return [
        Tool(
            name="create_story",
            description=(
                "Submit a new story topic for asynchronous generation. The story will be "
                "queued for processing through the complete workflow including content generation, "
                "title creation, image generation, audio synthesis, video composition, YouTube upload, "
                "and Ghost blog publishing. Returns a story ID for status tracking."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The story topic or idea to generate content about"
                    },
                    "character_id": {
                        "type": "string",
                        "description": "Optional character ID for narrator perspective (use list_characters to see options)"
                    },
                    "genre": {
                        "type": "string",
                        "description": "Optional genre (e.g., 'sci-fi', 'fantasy', 'mystery', 'comedy')"
                    },
                    "tone": {
                        "type": "string",
                        "description": "Optional tone (e.g., 'humorous', 'serious', 'philosophical', 'whimsical')"
                    },
                    "word_count": {
                        "type": "integer",
                        "description": "Optional target word count (default: 500, max: 2000)"
                    }
                },
                "required": ["topic"]
            }
        ),
        Tool(
            name="get_story_status",
            description=(
                "Check the current status of a story by its ID. Returns the current workflow step, "
                "progress information, and any errors encountered during processing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "integer",
                        "description": "The unique ID of the story to check"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="list_stories",
            description=(
                "List recent stories with their current status. Optionally filter by workflow step "
                "or limit the number of results. Useful for checking queue status and finding story IDs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of stories to return (default: 10)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_story",
            description=(
                "Get complete details for a specific story including full content, metadata, "
                "and all generated media paths (images, audio, video, YouTube URL, Ghost blog URL)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "integer",
                        "description": "The unique ID of the story to retrieve"
                    }
                },
                "required": ["story_id"]
            }
        ),
        Tool(
            name="list_characters",
            description=(
                "Get a list of available narrator characters with their attributes. Each character "
                "has a unique perspective, voice, and personality for storytelling within the "
                "Ephergent Universe."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="regenerate_story",
            description=(
                "Reset and regenerate a story from scratch. This will clear all generated content "
                "and re-queue the story for complete processing with the original parameters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "integer",
                        "description": "The unique ID of the story to regenerate"
                    }
                },
                "required": ["story_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from MCP client."""
    try:
        if name == "create_story":
            return await handle_create_story(arguments)
        elif name == "get_story_status":
            return await handle_get_story_status(arguments)
        elif name == "list_stories":
            return await handle_list_stories(arguments)
        elif name == "get_story":
            return await handle_get_story(arguments)
        elif name == "list_characters":
            return await handle_list_characters(arguments)
        elif name == "regenerate_story":
            return await handle_regenerate_story(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_create_story(arguments: dict) -> list[TextContent]:
    """Handle create_story tool call using REST API."""
    topic = arguments.get("topic")
    character_id = arguments.get("character_id")
    genre = arguments.get("genre")
    tone = arguments.get("tone")
    word_count = arguments.get("word_count", 500)

    # Validate word count
    if word_count > 2000:
        return [TextContent(
            type="text",
            text="Error: Maximum word count is 2000"
        )]

    try:
        # Prepare payload for API
        payload = {
            "topic": topic,
            "genre": genre,
            "tone": tone,
            "narrator_character_id": character_id
        }

        # Create story via API
        story = await api_post("stories", payload)

        # Build response
        response_text = f"""Story created successfully!

Story ID: {story['id']}
Topic: {topic}
Status: {story.get('current_step', 'queued')}
"""

        if character_id:
            response_text += f"Narrator: {character_id}\n"
        if genre:
            response_text += f"Genre: {genre}\n"
        if tone:
            response_text += f"Tone: {tone}\n"
        if word_count:
            response_text += f"Target Word Count: {word_count}\n"

        response_text += f"""
The story has been queued for processing. You can check its status using:
get_story_status(story_id={story['id']})

The story will progress through these workflow steps:
1. Story Generation (AI content creation)
2. Title Generation
3. Image Generation
4. Audio Generation
5. Video Generation
6. YouTube Upload
7. Ghost Blog Publishing
8. Completed
"""

        logger.info(f"Created story {story['id']} via MCP: {topic[:50]}")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error creating story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error creating story: {str(e)}"
        )]


async def handle_get_story_status(arguments: dict) -> list[TextContent]:
    """Handle get_story_status tool call using REST API."""
    story_id = arguments.get("story_id")

    try:
        # Get story from API
        story = await api_get(f"stories/{story_id}")

        # Build status response
        response_text = f"""Story Status Report
{'=' * 50}

ID: {story['id']}
Topic: {story['topic']}
Current Step: {story.get('current_step', 'unknown')}
Created: {story.get('created_at', 'N/A')}
Updated: {story.get('updated_at', 'N/A')}
"""

        if story.get('completed_at'):
            response_text += f"Completed: {story['completed_at']}\n"

        response_text += "\n"

        # Content status
        response_text += "Content Status:\n"
        response_text += f"- Title: {'✓ Generated' if story.get('title') else '✗ Not generated'}\n"
        response_text += f"- Content: {'✓ Generated' if story.get('content') else '✗ Not generated'}\n"
        response_text += f"- Images: {'✓ Generated' if story.get('image_paths') else '✗ Not generated'}\n"
        response_text += f"- Audio: {'✓ Generated' if story.get('audio_path') else '✗ Not generated'}\n"
        response_text += f"- Video: {'✓ Generated' if story.get('video_path') else '✗ Not generated'}\n"
        response_text += f"- YouTube: {'✓ Uploaded' if story.get('youtube_url') else '✗ Not uploaded'}\n"
        response_text += f"- Ghost Blog: {'✓ Published' if story.get('ghost_post_url') else '✗ Not published'}\n"

        # Error information
        if story.get('error_message'):
            response_text += f"\n⚠️ Error: {story['error_message']}\n"

        # Next steps guidance
        current_step = story.get('current_step', '')
        if current_step == 'completed':
            response_text += "\n✓ Story generation completed successfully!\n"
            response_text += f"Use get_story(story_id={story_id}) to see the full content.\n"
        elif current_step == 'failed':
            response_text += "\n✗ Story generation failed.\n"
            response_text += f"You can try regenerating it with regenerate_story(story_id={story_id})\n"
        else:
            response_text += f"\n⏳ Story is currently being processed at: {current_step}\n"
            response_text += "Check back in a moment for updates.\n"

        logger.info(f"Retrieved status for story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]
        raise
    except Exception as e:
        logger.error(f"Error getting story status: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error getting story status: {str(e)}"
        )]


async def handle_list_stories(arguments: dict) -> list[TextContent]:
    """Handle list_stories tool call using REST API."""
    limit = arguments.get("limit", 10)

    try:
        # Get stories from API
        stories_data = await api_get("stories", params={"per_page": limit, "page": 1})

        # API returns list directly
        stories = stories_data if isinstance(stories_data, list) else stories_data.get('items', [])

        if not stories:
            return [TextContent(
                type="text",
                text="No stories found."
            )]

        # Build response
        response_text = f"Recent Stories ({len(stories)} results)\n"
        response_text += "=" * 80 + "\n\n"

        for story in stories:
            current_step = story.get('current_step', 'unknown')
            status_icon = "✓" if current_step == "completed" else (
                "✗" if current_step == "failed" else "⏳"
            )

            topic = story.get('topic', 'N/A')
            response_text += f"{status_icon} ID {story['id']}: {topic[:60]}\n"
            response_text += f"   Status: {current_step}\n"
            response_text += f"   Created: {story.get('created_at', 'N/A')}\n"

            if story.get('title'):
                response_text += f"   Title: {story['title']}\n"

            if story.get('narrator_character_id'):
                response_text += f"   Narrator: {story['narrator_character_id']}\n"

            if story.get('error_message'):
                error_msg = story['error_message'][:100]
                response_text += f"   Error: {error_msg}\n"

            response_text += "\n"

        response_text += f"\nUse get_story_status(story_id=X) or get_story(story_id=X) for more details.\n"

        logger.info(f"Listed {len(stories)} stories via MCP")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error listing stories: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error listing stories: {str(e)}"
        )]


async def handle_get_story(arguments: dict) -> list[TextContent]:
    """Handle get_story tool call using REST API."""
    story_id = arguments.get("story_id")

    try:
        # Get story from API
        story = await api_get(f"stories/{story_id}")

        # Build comprehensive response
        response_text = f"""Complete Story Details
{'=' * 80}

ID: {story['id']}
Topic: {story['topic']}
Status: {story.get('current_step', 'unknown')}

"""

        # Metadata
        if story.get('title'):
            response_text += f"Title: {story['title']}\n\n"

        if story.get('narrator_character_id'):
            response_text += f"Narrator: {story['narrator_character_id']}\n"
        if story.get('genre'):
            response_text += f"Genre: {story['genre']}\n"
        if story.get('tone'):
            response_text += f"Tone: {story['tone']}\n"
        if story.get('word_count'):
            response_text += f"Word Count: {story['word_count']}\n"

        response_text += f"\nCreated: {story.get('created_at', 'N/A')}\n"
        response_text += f"Updated: {story.get('updated_at', 'N/A')}\n"

        if story.get('completed_at'):
            response_text += f"Completed: {story['completed_at']}\n"

        # Content
        if story.get('content'):
            response_text += f"\n{'=' * 80}\n"
            response_text += "STORY CONTENT\n"
            response_text += f"{'=' * 80}\n\n"
            response_text += story['content']
            response_text += f"\n\n{'=' * 80}\n"

        # Media and publishing URLs
        media_section = "\nGenerated Media & Publishing:\n"
        has_media = False

        if story.get('image_paths'):
            has_media = True
            media_section += "\nImages:\n"
            image_paths = story['image_paths']
            if isinstance(image_paths, dict):
                for image_type, url in image_paths.items():
                    media_section += f"  - {image_type}: {url}\n"
            elif isinstance(image_paths, list):
                for i, url in enumerate(image_paths, 1):
                    media_section += f"  - Image {i}: {url}\n"

        if story.get('audio_path'):
            has_media = True
            media_section += f"\nAudio: {story['audio_path']}\n"

        if story.get('video_path'):
            has_media = True
            media_section += f"\nVideo: {story['video_path']}\n"

        if story.get('youtube_url'):
            has_media = True
            media_section += f"\nYouTube: {story['youtube_url']}\n"

        if story.get('ghost_post_url'):
            has_media = True
            media_section += f"\nGhost Blog: {story['ghost_post_url']}\n"
            media_section += f"  Status: {story.get('ghost_status', 'unknown')}\n"

        if has_media:
            response_text += media_section

        # Error information
        if story.get('error_message'):
            response_text += f"\n⚠️ Error: {story['error_message']}\n"

        logger.info(f"Retrieved full story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]
        raise
    except Exception as e:
        logger.error(f"Error getting story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error getting story: {str(e)}"
        )]


async def handle_list_characters(arguments: dict) -> list[TextContent]:
    """Handle list_characters tool call using REST API."""
    try:
        # Get characters from API
        characters = await api_get("characters")

        if not characters:
            return [TextContent(
                type="text",
                text="No characters found."
            )]

        # Build response
        response_text = f"Available Narrator Characters ({len(characters)} total)\n"
        response_text += "=" * 80 + "\n\n"

        for character in characters:
            default_marker = " [DEFAULT]" if character.get('default', False) else ""
            response_text += f"Character ID: {character['id']}{default_marker}\n"
            response_text += f"Name: {character['name']}\n"

            if character.get('topics'):
                topics = character['topics']
                topics_str = ', '.join(topics) if isinstance(topics, list) else topics
                response_text += f"Topics: {topics_str}\n"

            if character.get('voice'):
                response_text += f"Voice Model: {character['voice']}\n"

            if character.get('model'):
                response_text += f"AI Model: {character['model']}\n"

            response_text += "\n"

        response_text += "\nTo use a character, include their character_id when creating a story:\n"
        if characters:
            response_text += f"create_story(topic='your topic', character_id='{characters[0]['id']}')\n"

        logger.info(f"Listed {len(characters)} characters via MCP")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error listing characters: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error listing characters: {str(e)}"
        )]


async def handle_regenerate_story(arguments: dict) -> list[TextContent]:
    """Handle regenerate_story tool call using REST API."""
    story_id = arguments.get("story_id")

    try:
        # Regenerate via API (assuming there's a regenerate endpoint)
        # If not, we'll need to use the workflow API
        result = await api_post(f"workflow/{story_id}/regenerate", {})

        response_text = f"""Story regeneration initiated successfully!

Story ID: {story_id}
Status: {result.get('current_step', 'queued')}

The story has been reset and re-queued for complete processing.
All previous content and media have been cleared.

Use get_story_status(story_id={story_id}) to track progress.
"""

        logger.info(f"Regenerated story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]
        raise
    except Exception as e:
        logger.error(f"Error regenerating story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error regenerating story: {str(e)}"
        )]


# SSE endpoint handlers
async def handle_sse(request):
    """Handle SSE connection for MCP protocol"""
    async with SseServerTransport("/messages") as transport:
        await server.run(
            transport.read_stream,
            transport.write_stream,
            server.create_initialization_options()
        )
    return Response()


async def handle_messages(request):
    """Handle MCP messages endpoint"""
    # This will be handled by the SSE transport
    return Response()


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
)


async def run_server(host: str, port: int):
    """Run the MCP server with SSE transport"""
    logger.info(f"Starting MCP SSE Server on {host}:{port}")
    logger.info(f"API URL: {config.api_url}")
    logger.info(f"SSE endpoint: http://{host}:{port}/sse")

    config_obj = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info"
    )
    server_instance = uvicorn.Server(config_obj)
    await server_instance.serve()


def main():
    """Main entry point"""
    global config, http_client

    parser = argparse.ArgumentParser(description='Ephergent MCP Server with SSE Transport')
    parser.add_argument('--api-url', help='Ephergent API base URL', default=os.getenv('EPHERGENT_API_URL'))
    parser.add_argument('--api-key', help='Admin API key', default=os.getenv('EPHERGENT_API_KEY'))
    parser.add_argument('--host', help='Host to bind', default=os.getenv('MCP_HOST', '127.0.0.1'))
    parser.add_argument('--port', type=int, help='Port to bind', default=int(os.getenv('MCP_PORT', '8765')))

    args = parser.parse_args()

    # Override environment with CLI args if provided
    if args.api_url:
        os.environ['EPHERGENT_API_URL'] = args.api_url
    if args.api_key:
        os.environ['EPHERGENT_API_KEY'] = args.api_key
    if args.host:
        os.environ['MCP_HOST'] = args.host
    if args.port:
        os.environ['MCP_PORT'] = str(args.port)

    try:
        # Initialize configuration
        config = MCPConfig()

        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)

        logger.info("Ephergent MCP Server (SSE) initialized")
        logger.info(f"Connecting to API: {config.api_url}")

        # Run the server
        asyncio.run(run_server(config.host, config.port))

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nError: {e}\n", file=sys.stderr)
        print("Please set EPHERGENT_API_KEY environment variable or use --api-key argument\n", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("MCP Server shutdown requested")
    except Exception as e:
        logger.error(f"MCP Server error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if http_client:
            asyncio.run(http_client.aclose())


if __name__ == "__main__":
    main()
