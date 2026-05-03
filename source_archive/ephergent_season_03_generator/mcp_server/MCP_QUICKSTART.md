# MCP Server Quick Start Guide

Get the Ephergent MCP Server running with Claude Desktop in 5 minutes.

## Quick Setup (macOS/Linux)

```bash
# 1. Run the setup script
./setup_mcp.sh

# 2. Copy the generated config to Claude Desktop
cp claude_desktop_config_generated.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. Restart Claude Desktop (completely quit and reopen)

# 4. Start the worker process
python worker.py --continuous
```

## Quick Setup (Manual)

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this configuration (replace path with your actual project path):

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

### 3. Restart Claude Desktop

- Completely quit Claude Desktop (not just close the window)
- Open Claude Desktop again

### 4. Start Worker Process

In a terminal:

```bash
python worker.py --continuous
```

Keep this running while using MCP tools.

## Quick Test

In Claude Desktop, try:

```
"Create a story about interdimensional coffee shops"
```

Claude should use the `create_story` tool and return a story ID.

Then check status:

```
"What's the status of story 1?"
```

## Common Commands

### List Available Characters

```
"List all available narrator characters"
```

### Create Story with Character

```
"Create a humorous sci-fi story about alien tourists using the narrator_epimetheus character"
```

### Check Story Status

```
"Check the status of story 5"
```

### Get Full Story

```
"Show me the complete story 5"
```

### List Recent Stories

```
"List the 10 most recent completed stories"
```

### Regenerate Failed Story

```
"Regenerate story 3"
```

## Troubleshooting

### MCP Tools Not Showing

1. Check config file syntax is valid JSON
2. Use absolute paths (not relative)
3. Restart Claude Desktop completely
4. Check logs: `tail -f mcp_server.log`

### Stories Not Processing

1. Make sure worker is running: `python worker.py --continuous`
2. Check worker status: `python worker.py --status`
3. Check database: `uv run flask db current`

### Database Errors

```bash
# Initialize database
./MIGRATION_QUICKSTART.sh

# Or manually
uv run flask db upgrade
```

## Next Steps

- Read the full documentation in [README_MCP.md](./README_MCP.md)
- Explore the available tools and their parameters
- Set up automated workers for continuous processing
- Customize character personalities and prompts

## Getting Help

1. Check [README_MCP.md](./README_MCP.md) for detailed documentation
2. Review [CLAUDE.md](./CLAUDE.md) for project architecture
3. Check logs in `mcp_server.log`
4. Verify environment variables in `.env`

## Advanced Usage

### Using UV (Recommended)

For better dependency isolation, use `uv run`:

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

### Environment Variables

Customize behavior in `.env`:

```bash
MCP_SERVER_NAME="ephergent-story-generator"
MCP_LOG_FILE="mcp_server.log"
MCP_LOG_LEVEL=INFO
```

### Multiple Workers

Run multiple workers for faster processing:

```bash
# Terminal 1
python worker.py --continuous

# Terminal 2
python worker.py --continuous

# Terminal 3
python worker.py --continuous
```

## Workflow Reference

Stories progress through these steps:

1. **queued** → Story created, waiting for processing
2. **story_generation** → AI generating content
3. **title_generation** → Creating title
4. **image_generation** → Generating images
5. **audio_generation** → Creating audio narration
6. **video_generation** → Composing video
7. **youtube_upload** → Uploading to YouTube
8. **ghost_publishing** → Publishing to blog
9. **completed** → All done!

## Tips

- **Be patient**: Story generation takes time (5-15 minutes per story)
- **Check status**: Use `get_story_status` to track progress
- **Use filters**: When listing stories, filter by status to find what you need
- **Character selection**: Different characters have different voices and styles
- **Word count**: Longer stories take more time to generate
- **Worker monitoring**: Keep an eye on worker logs for errors

Enjoy creating stories with the Ephergent Universe!
