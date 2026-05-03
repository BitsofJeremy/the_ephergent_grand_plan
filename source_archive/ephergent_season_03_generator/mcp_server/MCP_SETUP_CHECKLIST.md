# MCP Server Setup Checklist

Use this checklist to ensure your MCP server is properly configured and ready to use with Claude Desktop.

## Pre-Setup Verification

- [ ] Python 3.11+ installed (`python --version`)
- [ ] UV package manager installed (`uv --version`)
- [ ] Ephergent generator database initialized (`ls stories_dev.db` or check PostgreSQL)
- [ ] Claude Desktop application installed
- [ ] Worker process tested (`python worker.py --status`)

## Installation Steps

### Step 1: Install Dependencies

- [ ] Run `uv sync` to install all dependencies including MCP SDK
- [ ] Verify MCP SDK installed: `uv pip list | grep mcp`
- [ ] No import errors when running: `python -c "import mcp.server"`

### Step 2: Test MCP Server

- [ ] Run test suite: `python test_mcp_server.py`
- [ ] All tests pass (7/7)
- [ ] Database connection successful
- [ ] Character service working
- [ ] No errors in test output

### Step 3: Configure Environment

- [ ] `.env` file exists with required variables
- [ ] `GEMINI_API_KEY` is set
- [ ] `DATABASE_URL` is set (or using default SQLite)
- [ ] MCP variables added (MCP_SERVER_NAME, MCP_LOG_FILE, MCP_LOG_LEVEL)

### Step 4: Configure Claude Desktop

#### Option A: Automated Setup

- [ ] Run `./setup_mcp.sh`
- [ ] Script completes without errors
- [ ] Generated config file created: `claude_desktop_config_generated.json`
- [ ] Copy config to Claude Desktop:
  ```bash
  cp claude_desktop_config_generated.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
  ```

#### Option B: Manual Setup

- [ ] Locate Claude Desktop config file:
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`

- [ ] Edit config file with correct absolute paths
- [ ] Verify JSON syntax is valid
- [ ] Save config file

### Step 5: Start Services

- [ ] Start worker process: `python worker.py --continuous`
- [ ] Worker shows "Waiting for stories..." message
- [ ] No errors in worker output

### Step 6: Restart Claude Desktop

- [ ] Completely quit Claude Desktop (not just close window)
- [ ] Restart Claude Desktop application
- [ ] Wait for full startup (5-10 seconds)

### Step 7: Verify MCP Integration

- [ ] Open Claude Desktop
- [ ] Start a new conversation
- [ ] Look for hammer icon (🔨) in input area
- [ ] Click hammer icon
- [ ] See "ephergent-story-generator" in tool list
- [ ] See 6 tools listed:
  - [ ] create_story
  - [ ] get_story_status
  - [ ] list_stories
  - [ ] get_story
  - [ ] list_characters
  - [ ] regenerate_story

## First Test

### Test 1: List Characters

- [ ] In Claude Desktop, type: "List all available narrator characters"
- [ ] Claude uses `list_characters` tool
- [ ] Characters list is displayed
- [ ] Default character is marked
- [ ] No errors shown

### Test 2: Create Simple Story

- [ ] Type: "Create a story about interdimensional coffee shops"
- [ ] Claude uses `create_story` tool
- [ ] Story ID is returned
- [ ] Status shows "queued"
- [ ] No errors shown

### Test 3: Check Status

- [ ] Wait 30 seconds
- [ ] Type: "What's the status of story 1?" (use your story ID)
- [ ] Claude uses `get_story_status` tool
- [ ] Status shows progression (queued → story_generation → title_generation → etc.)
- [ ] No errors shown

### Test 4: Retrieve Completed Story

- [ ] Wait for story to complete (5-15 minutes)
- [ ] Check status shows "completed"
- [ ] Type: "Show me the full story 1" (use your story ID)
- [ ] Claude uses `get_story` tool
- [ ] Full story content is displayed
- [ ] Media URLs are shown (if generated)
- [ ] No errors shown

## Troubleshooting Checks

### If MCP Tools Don't Appear

- [ ] Check Claude Desktop config file exists
- [ ] Verify JSON syntax with: `python -m json.tool < path/to/config.json`
- [ ] Ensure absolute paths used (not relative)
- [ ] On Windows, use forward slashes or escaped backslashes
- [ ] Check Claude Desktop logs:
  - macOS: `~/Library/Logs/Claude/mcp*.log`
  - Windows: `%LOCALAPPDATA%\Claude\logs\mcp*.log`
- [ ] Restart Claude Desktop again (completely quit first)

### If Stories Don't Process

- [ ] Worker process is running: `ps aux | grep worker.py`
- [ ] Check worker output for errors
- [ ] Verify database connection: `python test_mcp_server.py`
- [ ] Check queue status: `python worker.py --status`
- [ ] Check story table: `python -c "from ephergent_generator import create_app, db; from ephergent_generator.models import Story; app = create_app(); app.app_context().push(); print('Stories:', Story.query.count())"`

### If Database Errors Occur

- [ ] Run migrations: `./MIGRATION_QUICKSTART.sh`
- [ ] Or manually: `uv run flask db upgrade`
- [ ] Check database file permissions: `ls -la stories_dev.db`
- [ ] Verify DATABASE_URL in .env
- [ ] Test database: `python test_mcp_server.py`

### If Import Errors Occur

- [ ] Install dependencies: `uv sync`
- [ ] Check virtual environment: `which python`
- [ ] Verify PYTHONPATH in config
- [ ] Test imports: `python -c "import mcp.server; from ephergent_generator import create_app"`

## Logging and Monitoring

### Check MCP Server Logs

- [ ] MCP log file exists: `ls -la mcp_server.log`
- [ ] Check for errors: `tail -50 mcp_server.log`
- [ ] Look for "MCP Server ready" message
- [ ] Monitor live: `tail -f mcp_server.log`

### Check Worker Logs

- [ ] Worker shows activity
- [ ] No Python errors in output
- [ ] Stories progressing through workflow
- [ ] Check worker log file if configured

### Check Application Logs

- [ ] Main app log: `tail -50 generator.log` or `season_03_generator.log`
- [ ] No database connection errors
- [ ] No service initialization errors

## Advanced Configuration

### Using UV (Optional)

- [ ] Update Claude Desktop config to use `uv run`
- [ ] Test with: `uv run python mcp_server.py`
- [ ] Verify worker works: `uv run python worker.py --continuous`

### Multiple Workers (Optional)

- [ ] Start 2-3 worker processes
- [ ] Monitor for conflicts: `python worker.py --status`
- [ ] Verify stories process faster

### PostgreSQL Setup (Optional)

- [ ] PostgreSQL running: `pg_isready`
- [ ] Database created
- [ ] DATABASE_URL in .env points to PostgreSQL
- [ ] Migrations applied: `uv run flask db upgrade`

## Production Checklist

### Security

- [ ] SECRET_KEY set to secure random value
- [ ] GEMINI_API_KEY protected (not in version control)
- [ ] Database credentials secure
- [ ] API keys for external services configured

### Performance

- [ ] Worker timeout configured (WORKER_TIMEOUT_MINUTES)
- [ ] Queue size limit set (MAX_QUEUE_SIZE)
- [ ] Database connection pooling configured
- [ ] Log rotation set up

### Monitoring

- [ ] Log files monitored
- [ ] Disk space checked
- [ ] Worker health monitored
- [ ] Story completion rate tracked

## Documentation Review

- [ ] Read README_MCP.md for full details
- [ ] Review MCP_QUICKSTART.md for quick reference
- [ ] Check CLAUDE.md for project context
- [ ] Bookmark MCP_IMPLEMENTATION_SUMMARY.md

## Completion

When all items are checked:

- [ ] MCP server is fully operational
- [ ] Claude Desktop shows tools
- [ ] Stories can be created
- [ ] Status can be checked
- [ ] Completed stories can be retrieved
- [ ] No errors in logs

## Next Steps

After successful setup:

1. **Explore Characters**: Try different narrator characters for varied storytelling styles
2. **Adjust Parameters**: Experiment with genre, tone, and word count
3. **Monitor Performance**: Track story generation times and success rates
4. **Customize**: Add custom tools or extend existing ones
5. **Automate**: Set up scheduled story generation
6. **Scale**: Add more workers for higher throughput

## Getting Help

If issues persist after completing this checklist:

1. Review logs in detail
2. Check documentation files
3. Run test suite again
4. Verify environment variables
5. Test database connection
6. Restart all services

## Maintenance Schedule

### Daily
- [ ] Check worker process is running
- [ ] Review logs for errors
- [ ] Monitor story completion rate

### Weekly
- [ ] Clean up old log files
- [ ] Review failed stories
- [ ] Check database size

### Monthly
- [ ] Update dependencies: `uv sync --upgrade`
- [ ] Review and optimize workflows
- [ ] Backup database

## Success Indicators

You'll know everything is working when:

- ✅ MCP tools appear in Claude Desktop
- ✅ Stories are created instantly
- ✅ Worker processes stories without errors
- ✅ Status updates show progression
- ✅ Completed stories include all content and media
- ✅ No errors in any log files
- ✅ Response times are fast (<1s for most operations)

Congratulations! Your Ephergent MCP Server is ready for production use! 🎉
