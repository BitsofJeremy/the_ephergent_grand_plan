# Ephergent Story Generator - MCP Server Integration

This guide explains how to integrate the Ephergent Story Generator with Claude Desktop using the Model Context Protocol (MCP).

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The Ephergent MCP Server provides Claude Desktop with direct access to the story generation system through a set of tools. This enables an async workflow where you can:

1. Submit story topics for generation
2. Check status of stories in progress
3. Retrieve completed stories
4. Manage characters and settings

The MCP server runs as a background service that Claude Desktop communicates with using stdio transport.

## Features

- **Async Workflow**: Submit stories and check status later - no need to wait for completion
- **Full Pipeline Access**: Create stories that go through the complete workflow (content, title, images, audio, video, YouTube, Ghost blog)
- **Character Management**: List and use different narrator characters with unique voices and perspectives
- **Status Tracking**: Check progress of stories through each workflow step
- **Error Handling**: Robust error reporting and validation
- **Database Integration**: Full access to story history and metadata

## Prerequisites

Before setting up the MCP server, ensure you have:

1. **Python 3.11+** installed
2. **Ephergent Story Generator** fully set up and working
3. **Claude Desktop** installed on your machine
4. **Worker process** configured and ready to run
5. **Database** initialized with migrations applied

## Installation

### Step 1: Install MCP SDK

The MCP Python SDK is required for the server to work. Install it using:

```bash
# From the project root directory
uv sync
```

This will install all dependencies including the `mcp>=1.0.0` package specified in `pyproject.toml`.

### Step 2: Verify Database Connection

Make sure your database is set up and accessible:

```bash
# Initialize database if needed
./MIGRATION_QUICKSTART.sh

# Or manually
uv run flask db upgrade
```

### Step 3: Test MCP Server

Verify the MCP server can start:

```bash
python mcp_server.py
```

You should see log output indicating the server has started successfully:

```
INFO - Starting Ephergent MCP Server
INFO - Flask app initialized for MCP server
INFO - Database connected: X stories, Y characters
INFO - MCP Server ready for connections
```

Press `Ctrl+C` to stop the test server.

## Configuration

### Step 1: Configure Claude Desktop

Add the MCP server configuration to your Claude Desktop config file:

**macOS/Linux:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add this configuration to the file:

```json
{
  "mcpServers": {
    "ephergent-story-generator": {
      "command": "python",
      "args": [
        "/absolute/path/to/ephergent_season_03_generator/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/ephergent_season_03_generator"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/ephergent_season_03_generator` with the actual absolute path to your project directory.

Example for macOS:
```json
{
  "mcpServers": {
    "ephergent-story-generator": {
      "command": "python",
      "args": [
        "/Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/jeremy/Documents/ephergent_next/ephergent_season_03_generator"
      }
    }
  }
}
```

### Step 2: Using UV (Alternative)

If you prefer to use `uv run` for better dependency management:

```json
{
  "mcpServers": {
    "ephergent-story-generator": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/absolute/path/to/ephergent_season_03_generator/mcp_server.py"
      ],
      "cwd": "/absolute/path/to/ephergent_season_03_generator"
    }
  }
}
```

### Step 3: Restart Claude Desktop

After updating the configuration:

1. Completely quit Claude Desktop
2. Restart Claude Desktop
3. Look for the MCP tools in the tool picker (hammer icon)

## Usage

### Starting the Worker Process

The MCP server queues stories for processing, but you need the worker process running to actually generate content:

```bash
# In a separate terminal window
cd /path/to/ephergent_season_03_generator
python worker.py --continuous
```

Keep this running while using the MCP server.

### Using MCP Tools in Claude Desktop

Once configured, you can use the tools directly in Claude Desktop conversations:

1. Click the hammer icon in the input area
2. Select the tool you want to use
3. Fill in the required parameters
4. Submit and wait for the response

Or simply ask Claude to use the tools naturally in conversation:

```
"Create a story about a time-traveling robot with a philosophical tone using the narrator_epimetheus character"

"Check the status of story ID 42"

"List all completed stories from the last week"

"Show me all available narrator characters"
```

## Available Tools

### 1. create_story

Submit a new story topic for asynchronous generation.

**Parameters:**
- `topic` (required): The story topic or idea
- `character_id` (optional): Narrator character ID (use `list_characters` to see options)
- `genre` (optional): Genre like 'sci-fi', 'fantasy', 'mystery'
- `tone` (optional): Tone like 'humorous', 'serious', 'philosophical'
- `word_count` (optional): Target word count (default: 500, max: 2000)

**Returns:** Story ID and status information

**Example:**
```json
{
  "topic": "A robot learns to feel emotions for the first time",
  "character_id": "narrator_epimetheus",
  "genre": "sci-fi",
  "tone": "philosophical",
  "word_count": 800
}
```

### 2. get_story_status

Check the current status of a story by ID.

**Parameters:**
- `story_id` (required): The unique ID of the story

**Returns:** Detailed status including current workflow step, content status, and errors

**Example:**
```json
{
  "story_id": 42
}
```

### 3. list_stories

List recent stories with their current status.

**Parameters:**
- `limit` (optional): Maximum number of results (default: 10)
- `status` (optional): Filter by workflow step (e.g., 'completed', 'failed', 'queued')

**Returns:** List of stories with basic information

**Example:**
```json
{
  "limit": 20,
  "status": "completed"
}
```

### 4. get_story

Get complete details for a specific story including full content and media.

**Parameters:**
- `story_id` (required): The unique ID of the story

**Returns:** Full story content, metadata, and all generated media URLs

**Example:**
```json
{
  "story_id": 42
}
```

### 5. list_characters

Get a list of available narrator characters.

**Parameters:** None

**Returns:** List of characters with their attributes, topics, and voice models

### 6. regenerate_story

Reset and regenerate a story from scratch.

**Parameters:**
- `story_id` (required): The unique ID of the story to regenerate

**Returns:** Confirmation and new status

**Example:**
```json
{
  "story_id": 42
}
```

## Examples

### Example 1: Create a Simple Story

```
You: "Create a story about interdimensional coffee shops"
```

Claude will use `create_story` and respond with:
```
Story created successfully!

Story ID: 123
Topic: interdimensional coffee shops
Status: queued

The story has been queued for processing...
```

### Example 2: Create Story with Specific Character

```
You: "List available characters"
```

Claude uses `list_characters`, then you can say:

```
You: "Create a humorous sci-fi story about alien tourists using the narrator_epimetheus character"
```

### Example 3: Check Story Progress

```
You: "What's the status of story 123?"
```

Claude uses `get_story_status` and shows:
```
Story Status Report
==================

ID: 123
Topic: interdimensional coffee shops
Current Step: audio_generation
...
```

### Example 4: Get Completed Story

```
You: "Show me the full content of story 123"
```

Claude uses `get_story` and displays the complete story with all content and media links.

### Example 5: Batch Story Creation

```
You: "Create 5 different stories about:
1. Time-traveling historians
2. Sentient clouds
3. Underground mushroom civilizations
4. Telepathic houseplants
5. Quantum mechanics for toddlers"
```

Claude can create multiple stories in sequence using the `create_story` tool.

## Workflow Steps

Stories progress through these workflow steps:

1. **queued** - Initial state, waiting for worker
2. **story_generation** - AI generating story content
3. **title_generation** - Creating story title
4. **image_generation** - Generating images via ComfyUI
5. **audio_generation** - Creating audio narration
6. **video_generation** - Composing video
7. **youtube_upload** - Uploading to YouTube
8. **ghost_publishing** - Publishing to Ghost blog
9. **completed** - All steps finished successfully
10. **failed** - Error occurred during processing

## Troubleshooting

### MCP Server Not Appearing in Claude Desktop

1. **Check configuration file path:**
   - Verify the path in `claude_desktop_config.json` is correct
   - Use absolute paths, not relative paths
   - On Windows, use forward slashes or escaped backslashes

2. **Check configuration syntax:**
   - Ensure JSON is valid (use a JSON validator)
   - Check for missing commas or brackets

3. **Restart Claude Desktop:**
   - Completely quit Claude Desktop (not just close window)
   - Restart and check for tools

4. **Check logs:**
   ```bash
   # Look at MCP server logs
   tail -f mcp_server.log

   # Look at Claude Desktop logs (macOS)
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### Stories Not Processing

1. **Check worker is running:**
   ```bash
   python worker.py --continuous
   ```

2. **Check database connection:**
   ```bash
   python -c "from ephergent_generator import create_app, db; app = create_app(); app.app_context().push(); print('Stories:', db.session.query(db.Model.metadata.tables['stories']).count())"
   ```

3. **Check queue status:**
   ```bash
   python worker.py --status
   ```

### Database Errors

1. **Run migrations:**
   ```bash
   uv run flask db upgrade
   ```

2. **Check database file permissions:**
   ```bash
   ls -la stories_dev.db
   ```

3. **Verify environment variables:**
   ```bash
   echo $DATABASE_URL
   ```

### Import Errors

1. **Ensure dependencies are installed:**
   ```bash
   uv sync
   ```

2. **Check Python path:**
   ```bash
   echo $PYTHONPATH
   ```

3. **Verify MCP SDK version:**
   ```bash
   uv pip list | grep mcp
   ```

## Advanced Configuration

### Environment Variables

You can customize MCP server behavior with environment variables in `.env`:

```bash
# MCP Server Settings
MCP_SERVER_NAME="ephergent-story-generator"
MCP_LOG_FILE="mcp_server.log"
MCP_LOG_LEVEL=INFO
```

### Running on Different Database

If using PostgreSQL instead of SQLite:

```bash
# In .env
DATABASE_URL=postgresql://user:password@localhost:5432/ephergent_db
```

### Custom Worker Configuration

Configure worker behavior:

```bash
# In .env
WORKER_SLEEP_INTERVAL=5
WORKER_TIMEOUT_MINUTES=30
DEFAULT_STORY_PRIORITY=0
```

## Security Considerations

1. **API Keys**: The MCP server uses the same API keys as the main application (GEMINI_API_KEY, etc.)
2. **Database Access**: The server has full read/write access to the database
3. **File System**: The server can read/write files in the project directory
4. **Local Only**: The MCP server only accepts local connections from Claude Desktop

## Performance Tips

1. **Use filters**: When listing stories, use the `status` filter to reduce query time
2. **Limit results**: Set reasonable `limit` values when listing stories
3. **Worker management**: Run one worker process at a time for optimal performance
4. **Database maintenance**: Periodically clean up old/failed stories to improve query speed

## Getting Help

If you encounter issues:

1. Check this README first
2. Review the logs in `mcp_server.log`
3. Check the main application documentation in `CLAUDE.md`
4. Review the worker documentation for processing issues
5. Check database migrations with `flask db current`

## Additional Resources

- [MCP Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop Documentation](https://claude.ai/desktop)
- [Ephergent Project Documentation](./CLAUDE.md)
- [Migration Guide](./MIGRATIONS.md)
- [Worker Documentation](./worker.py)

## License

Same as the main Ephergent Story Generator project.
