#!/bin/bash
# Setup script for Ephergent MCP Server

set -e

echo "======================================"
echo "Ephergent MCP Server Setup"
echo "======================================"
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Install dependencies
echo "Step 1: Installing dependencies..."
uv sync
echo "✓ Dependencies installed"
echo ""

# Step 2: Test database connection
echo "Step 2: Testing database connection..."
if python -c "from ephergent_generator import create_app, db; app = create_app(); app.app_context().push(); print('Database OK')" 2>/dev/null; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
    echo "Run ./MIGRATION_QUICKSTART.sh to initialize the database"
    exit 1
fi
echo ""

# Step 3: Test MCP server
echo "Step 3: Testing MCP server startup..."
timeout 5 python mcp_server.py > /dev/null 2>&1 || true
if [ -f mcp_server.log ]; then
    if grep -q "MCP Server ready" mcp_server.log; then
        echo "✓ MCP server test successful"
    else
        echo "⚠ MCP server may have issues, check mcp_server.log"
    fi
else
    echo "⚠ MCP server log not found, but installation should be OK"
fi
echo ""

# Step 4: Generate Claude Desktop configuration
echo "Step 4: Generating Claude Desktop configuration..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CLAUDE_CONFIG_DIR="$APPDATA/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
else
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
    CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
fi

echo "Claude Desktop config location: $CLAUDE_CONFIG_FILE"
echo ""

# Create the configuration JSON
cat > "${PROJECT_DIR}/claude_desktop_config_generated.json" <<EOF
{
  "mcpServers": {
    "ephergent-story-generator": {
      "command": "python",
      "args": [
        "$PROJECT_DIR/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "$PROJECT_DIR"
      }
    }
  }
}
EOF

echo "✓ Configuration generated: ${PROJECT_DIR}/claude_desktop_config_generated.json"
echo ""

# Step 5: Provide installation instructions
echo "======================================"
echo "Next Steps:"
echo "======================================"
echo ""
echo "1. Copy the configuration to Claude Desktop:"
echo "   cp ${PROJECT_DIR}/claude_desktop_config_generated.json \"$CLAUDE_CONFIG_FILE\""
echo ""
echo "   Or manually add this to your existing Claude Desktop config:"
echo "   cat ${PROJECT_DIR}/claude_desktop_config_generated.json"
echo ""
echo "2. Restart Claude Desktop completely (quit and reopen)"
echo ""
echo "3. Start the worker process (required for story generation):"
echo "   python worker.py --continuous"
echo ""
echo "4. In Claude Desktop, look for the MCP tools (hammer icon)"
echo ""
echo "5. Try creating a story:"
echo "   \"Create a story about interdimensional coffee shops\""
echo ""
echo "For more information, see README_MCP.md"
echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
