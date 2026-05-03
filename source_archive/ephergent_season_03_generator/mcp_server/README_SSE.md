# MCP Server - SSE Transport (Remote VM Deployment)

This is the **SSE-based MCP server** designed for remote VM deployment. Unlike the STDIO version (`mcp_server.py`), this server:

- Uses **Server-Sent Events (SSE)** transport instead of STDIO
- Communicates with the Ephergent API via **HTTP/REST** instead of direct database access
- Requires **API key authentication** for security
- Can be **hosted on a remote VM** and accessed over the network

## Architecture

```
Claude Desktop (your Mac)
    ↓
    HTTP/SSE connection
    ↓
MCP Server SSE (remote VM:8765)
    ↓
    HTTP/REST API calls
    ↓
Ephergent Flask API (remote VM:5000)
    ↓
PostgreSQL Database
```

## Requirements

- Python 3.11+
- Ephergent API running and accessible
- Valid admin API key
- Network access from Claude Desktop to the MCP server

## Installation

Install the additional dependencies:

```bash
uv sync
# or
pip install uvicorn starlette httpx
```

## Configuration

### Environment Variables

```bash
# Required
export EPHERGENT_API_KEY="ephg_your_admin_api_key_here"

# Optional (with defaults shown)
export EPHERGENT_API_URL="http://localhost:5000"  # Your Flask API URL
export MCP_HOST="127.0.0.1"                       # Bind to all interfaces: 0.0.0.0
export MCP_PORT="8765"                            # MCP server port
```

### Getting an API Key

1. Log in to the Ephergent web interface as an admin user
2. Navigate to **Profile → API Keys**
3. Click **"Create New API Key"**
4. Give it a name like "MCP Server"
5. Set permissions to include `['admin']` or at minimum `['stories:write', 'stories:read']`
6. **Copy the API key immediately** - it won't be shown again!
7. The key will look like: `ephg_abcdefghijklmnopqrstuvwxyz123456`

## Usage

### Basic Usage (Local Testing)

```bash
# With environment variables
export EPHERGENT_API_KEY="ephg_your_key_here"
python mcp_server/mcp_server_sse.py
```

### Remote VM Deployment

```bash
# On the VM, bind to all interfaces so it's accessible remotely
python mcp_server/mcp_server_sse.py \
  --api-url http://localhost:5000 \
  --api-key ephg_your_key_here \
  --host 0.0.0.0 \
  --port 8765
```

### With CLI Arguments

```bash
python mcp_server/mcp_server_sse.py \
  --api-url http://your-server.com:5000 \
  --api-key ephg_your_key_here \
  --host 127.0.0.1 \
  --port 8765
```

## Systemd Service (Production)

Create `/etc/systemd/system/ephergent-mcp.service`:

```ini
[Unit]
Description=Ephergent MCP Server (SSE)
After=network.target ephergent-web.service

[Service]
Type=simple
User=ephergent
WorkingDirectory=/opt/ephergent_season_03_generator
Environment="EPHERGENT_API_URL=http://127.0.0.1:5000"
Environment="EPHERGENT_API_KEY=ephg_your_key_here"
Environment="MCP_HOST=0.0.0.0"
Environment="MCP_PORT=8765"
ExecStart=/opt/ephergent_season_03_generator/.venv/bin/python /opt/ephergent_season_03_generator/mcp_server/mcp_server_sse.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ephergent-mcp
sudo systemctl start ephergent-mcp
sudo systemctl status ephergent-mcp
```

## Claude Desktop Configuration

Add to your Claude Desktop MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "ephergent-remote": {
      "transport": {
        "type": "sse",
        "url": "http://your-server-ip:8765/sse"
      }
    }
  }
}
```

**Security Note**: If exposing to the internet, use HTTPS and consider adding nginx reverse proxy with SSL.

## Nginx Reverse Proxy (Optional but Recommended)

For HTTPS/SSL support, add to nginx config:

```nginx
location /mcp/ {
    proxy_pass http://127.0.0.1:8765/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
    proxy_cache off;
}
```

Then use: `https://your-domain.com/mcp/sse`

## Testing

### Test API Connection

```bash
# Check if API is accessible
curl -H "Authorization: Bearer ephg_your_key_here" \
  http://localhost:5000/api/stories
```

### Test MCP Server

```bash
# Server should be running on port 8765
curl http://localhost:8765/sse

# You should see a response or connection from the SSE endpoint
```

### Test from Claude Desktop

Once configured in Claude Desktop, ask Claude:

```
Can you list the available story characters?
```

Claude should use the `list_characters` tool via the MCP server.

## Available MCP Tools

All the same tools as the STDIO version:

- `create_story` - Submit a new story for generation
- `get_story_status` - Check story processing status
- `list_stories` - List recent stories
- `get_story` - Get complete story details
- `list_characters` - List available narrator characters
- `regenerate_story` - Retry a failed story

## Differences from STDIO Version

| Feature | STDIO Version | SSE Version |
|---------|---------------|-------------|
| Transport | STDIO (stdin/stdout) | HTTP/SSE |
| Database Access | Direct SQLAlchemy | REST API calls |
| Authentication | None | API Key required |
| Deployment | Local only | Remote VM capable |
| Network | Not applicable | Requires network access |
| Security | Process isolation | API key + HTTPS |

## Troubleshooting

### "Configuration error: EPHERGENT_API_KEY environment variable is required"

Set the API key:
```bash
export EPHERGENT_API_KEY="ephg_your_key_here"
```

### "Connection refused" from Claude Desktop

- Check if the MCP server is running: `systemctl status ephergent-mcp`
- Verify the port is accessible: `curl http://localhost:8765/sse`
- Check firewall rules if accessing remotely
- Ensure the MCP_HOST is set to `0.0.0.0` for remote access

### "401 Unauthorized" API errors

- Verify your API key is correct
- Check that the API key has the necessary permissions (`admin` or `stories:write`)
- Make sure the API key hasn't expired

### "Story creation fails"

- Check that the worker process is running: `systemctl status ephergent-worker`
- Verify the Flask API is accessible: `curl http://localhost:5000/api/health`
- Check logs: `tail -f mcp_server_sse.log`

## Logs

The server logs to both console and `mcp_server_sse.log` in the current directory.

```bash
# View logs in real-time
tail -f mcp_server/mcp_server_sse.log

# View systemd service logs
journalctl -u ephergent-mcp -f
```

## Security Considerations

1. **API Key Security**: Never commit API keys to version control
2. **HTTPS**: Use HTTPS in production (via nginx reverse proxy)
3. **Firewall**: Limit access to trusted IPs if possible
4. **API Key Rotation**: Regularly rotate API keys
5. **Network Isolation**: Consider VPN or SSH tunneling for production

## Performance

- The SSE version adds minimal latency compared to STDIO (typically <100ms)
- HTTP connection pooling is enabled via `httpx.AsyncClient`
- The server can handle multiple concurrent MCP connections
- API calls are async for better performance

## Migration from STDIO Version

If you're currently using the STDIO version (`mcp_server.py`):

1. Generate an admin API key
2. Install new dependencies: `uv sync`
3. Update Claude Desktop config to use SSE transport
4. Start the SSE server: `python mcp_server_sse.py`
5. Test thoroughly before removing the STDIO version

Both versions can coexist during the transition period.
