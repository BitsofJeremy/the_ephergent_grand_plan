#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for Ephergent Story Generator

This MCP server provides async workflow integration for Claude Desktop to interact
with the Ephergent story generation system. It exposes tools for creating stories,
checking status, listing stories, and managing characters.

Usage:
    python mcp_server.py

The server runs as a stdio-based MCP server that can be integrated with Claude Desktop.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

# Import Flask app and services
from ephergent_generator import create_app, db
from ephergent_generator.models import Story, Character, WorkflowStep
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.character_service import CharacterService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = create_app()
logger.info("Flask app initialized for MCP server")

# Initialize MCP server
server = Server("ephergent-story-generator")

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
                    },
                    "status": {
                        "type": "string",
                        "description": "Optional filter by workflow step (e.g., 'completed', 'failed', 'queued')"
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
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls from MCP client."""

    try:
        # All database operations must be done within app context
        with app.app_context():
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
    """Handle create_story tool call."""
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

    # Validate character if provided
    if character_id:
        character_service = CharacterService()
        character = character_service.get_character_by_id(character_id)
        if not character:
            return [TextContent(
                type="text",
                text=f"Error: Character '{character_id}' not found. Use list_characters to see available options."
            )]

    try:
        # Create story using workflow service
        workflow_service = StoryWorkflowService()
        story = workflow_service.create_story_from_topic(
            topic=topic,
            genre=genre,
            tone=tone,
            word_count=word_count,
            narrator_character_id=character_id,
            session_id="mcp_client"
        )

        # Build response
        response_text = f"""Story created successfully!

Story ID: {story.id}
Topic: {topic}
Status: {story.current_step.value}
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
get_story_status(story_id={story.id})

The story will progress through these workflow steps:
1. Story Generation (AI content creation)
2. Title Generation
3. Image Generation
4. Audio Generation
5. Video Generation
6. YouTube Upload
7. Ghost Blog Publishing
8. Completed

Note: You must have the worker process running for stories to be processed:
python worker.py --continuous
"""

        logger.info(f"Created story {story.id} via MCP: {topic[:50]}")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error creating story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error creating story: {str(e)}"
        )]


async def handle_get_story_status(arguments: dict) -> list[TextContent]:
    """Handle get_story_status tool call."""
    story_id = arguments.get("story_id")

    try:
        story = Story.query.get(story_id)
        if not story:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]

        # Get workflow data
        workflow_data = story.get_workflow_data()

        # Build status response
        response_text = f"""Story Status Report
{'=' * 50}

ID: {story.id}
Topic: {story.topic}
Current Step: {story.current_step.value}
Created: {story.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Updated: {story.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

        if story.completed_at:
            response_text += f"Completed: {story.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        response_text += "\n"

        # Add metadata
        if story.narrator_character_id:
            response_text += f"Narrator: {story.narrator_character_id}\n"
        if story.genre:
            response_text += f"Genre: {story.genre}\n"
        if story.tone:
            response_text += f"Tone: {story.tone}\n"
        if story.word_count:
            response_text += f"Word Count: {story.word_count}\n"

        response_text += "\n"

        # Content status
        response_text += "Content Status:\n"
        response_text += f"- Title: {'✓ Generated' if story.title else '✗ Not generated'}\n"
        response_text += f"- Content: {'✓ Generated' if story.content else '✗ Not generated'}\n"
        response_text += f"- Images: {'✓ Generated' if story.image_paths else '✗ Not generated'}\n"
        response_text += f"- Audio: {'✓ Generated' if story.audio_path else '✗ Not generated'}\n"
        response_text += f"- Video: {'✓ Generated' if story.video_path else '✗ Not generated'}\n"
        response_text += f"- YouTube: {'✓ Uploaded' if story.youtube_url else '✗ Not uploaded'}\n"
        response_text += f"- Ghost Blog: {'✓ Published' if story.ghost_post_url else '✗ Not published'}\n"

        # Error information
        if story.error_message:
            response_text += f"\n⚠️ Error: {story.error_message}\n"

        # Next steps guidance
        if story.current_step == WorkflowStep.COMPLETED:
            response_text += "\n✓ Story generation completed successfully!\n"
            response_text += f"Use get_story(story_id={story.id}) to see the full content.\n"
        elif story.current_step == WorkflowStep.FAILED:
            response_text += "\n✗ Story generation failed.\n"
            response_text += f"You can try regenerating it with regenerate_story(story_id={story.id})\n"
        else:
            response_text += f"\n⏳ Story is currently being processed at: {story.current_step.value}\n"
            response_text += "Check back in a moment for updates.\n"

        logger.info(f"Retrieved status for story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error getting story status: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error getting story status: {str(e)}"
        )]


async def handle_list_stories(arguments: dict) -> list[TextContent]:
    """Handle list_stories tool call."""
    limit = arguments.get("limit", 10)
    status_filter = arguments.get("status")

    try:
        # Build query
        query = Story.query.order_by(Story.created_at.desc())

        # Apply status filter if provided
        if status_filter:
            try:
                workflow_step = WorkflowStep(status_filter.lower())
                query = query.filter(Story.current_step == workflow_step)
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Invalid status: {status_filter}. Valid statuses are: {', '.join([s.value for s in WorkflowStep])}"
                )]

        # Limit results
        stories = query.limit(limit).all()

        if not stories:
            return [TextContent(
                type="text",
                text="No stories found."
            )]

        # Build response
        response_text = f"Recent Stories ({len(stories)} results)\n"
        response_text += "=" * 80 + "\n\n"

        for story in stories:
            status_icon = "✓" if story.current_step == WorkflowStep.COMPLETED else (
                "✗" if story.current_step == WorkflowStep.FAILED else "⏳"
            )

            response_text += f"{status_icon} ID {story.id}: {story.topic[:60]}\n"
            response_text += f"   Status: {story.current_step.value}\n"
            response_text += f"   Created: {story.created_at.strftime('%Y-%m-%d %H:%M')}\n"

            if story.title:
                response_text += f"   Title: {story.title}\n"

            if story.narrator_character_id:
                response_text += f"   Narrator: {story.narrator_character_id}\n"

            if story.error_message:
                response_text += f"   Error: {story.error_message[:100]}\n"

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
    """Handle get_story tool call - returns complete story details."""
    story_id = arguments.get("story_id")

    try:
        story = Story.query.get(story_id)
        if not story:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]

        # Build comprehensive response
        response_text = f"""Complete Story Details
{'=' * 80}

ID: {story.id}
Topic: {story.topic}
Status: {story.current_step.value}

"""

        # Metadata
        if story.title:
            response_text += f"Title: {story.title}\n\n"

        if story.narrator_character_id:
            response_text += f"Narrator: {story.narrator_character_id}\n"
        if story.genre:
            response_text += f"Genre: {story.genre}\n"
        if story.tone:
            response_text += f"Tone: {story.tone}\n"
        if story.word_count:
            response_text += f"Word Count: {story.word_count}\n"

        response_text += f"\nCreated: {story.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        response_text += f"Updated: {story.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if story.completed_at:
            response_text += f"Completed: {story.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Content
        if story.content:
            response_text += f"\n{'=' * 80}\n"
            response_text += "STORY CONTENT\n"
            response_text += f"{'=' * 80}\n\n"
            response_text += story.content
            response_text += f"\n\n{'=' * 80}\n"

        # Media and publishing URLs
        media_section = "\nGenerated Media & Publishing:\n"
        has_media = False

        image_paths = story.get_image_paths()
        if image_paths:
            has_media = True
            media_section += "\nImages:\n"
            for image_type, url in image_paths.items():
                media_section += f"  - {image_type}: {url}\n"

        if story.audio_path:
            has_media = True
            media_section += f"\nAudio: {story.audio_path}\n"

        if story.video_path:
            has_media = True
            media_section += f"\nVideo: {story.video_path}\n"

        if story.youtube_url:
            has_media = True
            media_section += f"\nYouTube: {story.youtube_url}\n"

        if story.ghost_post_url:
            has_media = True
            media_section += f"\nGhost Blog: {story.ghost_post_url}\n"
            media_section += f"  Status: {story.ghost_status}\n"

        if has_media:
            response_text += media_section

        # Error information
        if story.error_message:
            response_text += f"\n⚠️ Error: {story.error_message}\n"

        logger.info(f"Retrieved full story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error getting story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error getting story: {str(e)}"
        )]


async def handle_list_characters(arguments: dict) -> list[TextContent]:
    """Handle list_characters tool call."""
    try:
        character_service = CharacterService()
        characters = character_service.get_all_characters()

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
                response_text += f"Topics: {', '.join(character['topics'])}\n"

            if character.get('voice'):
                response_text += f"Voice Model: {character['voice']}\n"

            if character.get('model'):
                response_text += f"AI Model: {character['model']}\n"

            response_text += "\n"

        response_text += "\nTo use a character, include their character_id when creating a story:\n"
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
    """Handle regenerate_story tool call."""
    story_id = arguments.get("story_id")

    try:
        story = Story.query.get(story_id)
        if not story:
            return [TextContent(
                type="text",
                text=f"Story {story_id} not found"
            )]

        # Store original topic for response
        original_topic = story.topic

        # Regenerate using workflow service
        workflow_service = StoryWorkflowService()
        regenerated_story = workflow_service.regenerate_story(story_id)

        if not regenerated_story:
            return [TextContent(
                type="text",
                text=f"Failed to regenerate story {story_id}"
            )]

        response_text = f"""Story regeneration initiated successfully!

Story ID: {story_id}
Topic: {original_topic}
Status: {regenerated_story.current_step.value}

The story has been reset and re-queued for complete processing.
All previous content and media have been cleared.

Use get_story_status(story_id={story_id}) to track progress.

Note: Make sure the worker process is running:
python worker.py --continuous
"""

        logger.info(f"Regenerated story {story_id} via MCP")

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error regenerating story: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error regenerating story: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting Ephergent MCP Server")

    # Verify app context is working
    with app.app_context():
        try:
            # Test database connection
            story_count = Story.query.count()
            character_count = Character.query.count()
            logger.info(f"Database connected: {story_count} stories, {character_count} characters")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            sys.exit(1)

    logger.info("MCP Server ready for connections")

    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP Server shutdown requested")
    except Exception as e:
        logger.error(f"MCP Server error: {str(e)}", exc_info=True)
        sys.exit(1)
