# MCP Server Flask Integration Plan

## Executive Summary

This document outlines the plan to integrate the MCP (Model Context Protocol) server inline with the Flask application, making it accessible at `http://10.0.0.99/mcp` instead of running as a separate service on port 8765.

## Current State

**Two MCP Server Implementations:**

1. **STDIO version** (`mcp_server/mcp_server.py`)
   - Uses stdio transport for Claude Desktop local integration
   - Direct database access via SQLAlchemy
   - Runs as subprocess from Claude Desktop

2. **SSE version** (`mcp_server/mcp_server_sse.py`)
   - Standalone HTTP server using Starlette/Uvicorn on port 8765
   - Communicates with Flask API via REST calls
   - Requires API key authentication
   - Intended for remote VM deployment

**Goal:** Integrate MCP directly into Flask app at `/mcp` endpoint while maintaining STDIO version for local use.

---

## Architecture Overview

### Integration Approach

```
Flask Application (http://10.0.0.99)
├── /api/*          (Existing REST API)
├── /admin/*        (Admin portal)
├── /auth/*         (Authentication)
└── /mcp            (NEW: MCP Streamable HTTP endpoint)
    ├── POST        (Client → Server: JSON-RPC requests/notifications/responses)
    └── GET         (Server → Client: SSE stream for messages)
```

### Key Design Principles

1. **Single Endpoint Pattern**: One `/mcp` endpoint handles both POST and GET per MCP spec
2. **Reuse Existing Infrastructure**: Leverage Flask's authentication, database, and services
3. **Backward Compatibility**: Keep STDIO version working for Claude Desktop
4. **Session Management**: Implement MCP session lifecycle with unique session IDs
5. **Async Support**: Handle long-running SSE streams in Flask

---

## Implementation Plan

### Phase 1: Core MCP Blueprint (Week 1)

#### 1.1 File Structure

```
ephergent_generator/
├── mcp/
│   ├── __init__.py              # Blueprint registration
│   ├── routes.py                # /mcp POST and GET endpoints
│   ├── handlers.py              # MCP tool handlers (reuse from mcp_server.py)
│   ├── session.py               # Session management
│   └── transport.py             # SSE stream utilities
├── models.py                    # Add MCPSession model
└── __init__.py                  # Register MCP blueprint
```

#### 1.2 Database Model for Sessions

```python
# ephergent_generator/models.py

class MCPSession(db.Model):
    """MCP session tracking for Streamable HTTP transport."""
    __tablename__ = 'mcp_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=True)

    # Session metadata
    client_info = db.Column(db.JSON, nullable=True)  # User agent, IP, etc.
    protocol_version = db.Column(db.String(20), nullable=False, default='2025-06-18')

    # Lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # SSE stream state
    last_event_id = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f'<MCPSession {self.session_id}>'
```

#### 1.3 Blueprint Registration

```python
# ephergent_generator/mcp/__init__.py

from flask import Blueprint

mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')

from ephergent_generator.mcp import routes
```

```python
# ephergent_generator/__init__.py (add to create_app)

# Register MCP blueprint
from ephergent_generator.mcp import mcp_bp
app.register_blueprint(mcp_bp)
```

---

### Phase 2: MCP Routes Implementation (Week 1-2)

#### 2.1 POST Endpoint - JSON-RPC Handler

```python
# ephergent_generator/mcp/routes.py

from flask import request, jsonify, current_app
from ephergent_generator.mcp import mcp_bp
from ephergent_generator.mcp.session import get_or_create_session, validate_session
from ephergent_generator.mcp.handlers import MCPHandlers
import logging

logger = logging.getLogger(__name__)

@mcp_bp.route('', methods=['POST'])
def mcp_post():
    """
    Handle JSON-RPC messages from client (requests, notifications, responses).

    Per MCP Streamable HTTP spec:
    - Accept header must include application/json and text/event-stream
    - Body is a single JSON-RPC message
    - Returns either JSON response or SSE stream
    """
    try:
        # Get protocol version
        protocol_version = request.headers.get('MCP-Protocol-Version', '2025-03-26')

        # Validate Accept header
        accept = request.headers.get('Accept', '')
        if 'application/json' not in accept and 'text/event-stream' not in accept:
            return jsonify({'error': 'Accept header must include application/json or text/event-stream'}), 400

        # Parse JSON-RPC message
        message = request.get_json()
        if not message:
            return jsonify({'error': 'Invalid JSON'}), 400

        # Extract message type
        msg_id = message.get('id')
        msg_method = message.get('method')

        # Session management
        session_id = request.headers.get('Mcp-Session-Id')

        # Handle initialization (no session required)
        if msg_method == 'initialize':
            session = get_or_create_session(protocol_version)
            result = MCPHandlers.handle_initialize(message.get('params', {}))

            response = jsonify({
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': result
            })
            response.headers['Mcp-Session-Id'] = session.session_id
            return response

        # All other messages require valid session
        if not session_id:
            return jsonify({'error': 'Mcp-Session-Id header required'}), 400

        session = validate_session(session_id)
        if not session:
            return jsonify({'error': 'Invalid or expired session'}), 404

        # Handle different message types
        if msg_id and msg_method:
            # JSON-RPC REQUEST - need to respond
            return handle_request(message, session)
        elif msg_method:
            # JSON-RPC NOTIFICATION - acknowledge only
            return '', 202
        else:
            # JSON-RPC RESPONSE - acknowledge only
            return '', 202

    except Exception as e:
        logger.error(f"MCP POST error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def handle_request(message, session):
    """Handle a JSON-RPC request and return response."""
    method = message.get('method')
    params = message.get('params', {})
    msg_id = message.get('id')

    try:
        # Route to appropriate handler
        handler = MCPHandlers(session)
        result = handler.call_tool(method, params)

        # Return JSON response
        return jsonify({
            'jsonrpc': '2.0',
            'id': msg_id,
            'result': result
        })

    except Exception as e:
        logger.error(f"Handler error for {method}: {str(e)}", exc_info=True)
        return jsonify({
            'jsonrpc': '2.0',
            'id': msg_id,
            'error': {
                'code': -32603,
                'message': 'Internal error',
                'data': str(e)
            }
        }), 500
```

#### 2.2 GET Endpoint - SSE Stream

```python
# ephergent_generator/mcp/routes.py (continued)

from flask import Response, stream_with_context
from ephergent_generator.mcp.transport import SSEStream

@mcp_bp.route('', methods=['GET'])
def mcp_get():
    """
    Open SSE stream for server-to-client messages.

    Per MCP spec:
    - Accept header must include text/event-stream
    - Returns SSE stream with server-initiated messages
    - Supports resumability via Last-Event-ID header
    """
    try:
        # Validate Accept header
        accept = request.headers.get('Accept', '')
        if 'text/event-stream' not in accept:
            return jsonify({'error': 'Accept header must include text/event-stream'}), 400

        # Get session
        session_id = request.headers.get('Mcp-Session-Id')
        if not session_id:
            return jsonify({'error': 'Mcp-Session-Id header required'}), 400

        session = validate_session(session_id)
        if not session:
            return jsonify({'error': 'Invalid or expired session'}), 404

        # Check for resumption
        last_event_id = request.headers.get('Last-Event-ID')

        # Create SSE stream
        stream = SSEStream(session, last_event_id)

        return Response(
            stream_with_context(stream.generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        logger.error(f"MCP GET error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mcp_bp.route('', methods=['DELETE'])
def mcp_delete():
    """
    Terminate an MCP session.

    Client sends DELETE with Mcp-Session-Id to end session.
    """
    session_id = request.headers.get('Mcp-Session-Id')
    if not session_id:
        return jsonify({'error': 'Mcp-Session-Id header required'}), 400

    # Deactivate session
    from ephergent_generator.mcp.session import terminate_session
    success = terminate_session(session_id)

    if success:
        return '', 204
    else:
        return '', 405  # Method not allowed if sessions can't be terminated
```

---

### Phase 3: Session Management (Week 2)

```python
# ephergent_generator/mcp/session.py

import secrets
from datetime import datetime, timedelta
from ephergent_generator.models import MCPSession, db
from flask import current_app

def generate_session_id():
    """Generate cryptographically secure session ID."""
    return secrets.token_urlsafe(32)

def get_or_create_session(protocol_version='2025-06-18', api_key_id=None):
    """Create a new MCP session."""
    session_id = generate_session_id()

    session = MCPSession(
        session_id=session_id,
        api_key_id=api_key_id,
        protocol_version=protocol_version,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )

    db.session.add(session)
    db.session.commit()

    return session

def validate_session(session_id):
    """Validate and return active session."""
    session = MCPSession.query.filter_by(
        session_id=session_id,
        is_active=True
    ).first()

    if not session:
        return None

    # Check expiration
    if session.expires_at and session.expires_at < datetime.utcnow():
        session.is_active = False
        db.session.commit()
        return None

    # Update last activity
    session.last_activity = datetime.utcnow()
    db.session.commit()

    return session

def terminate_session(session_id):
    """Terminate an MCP session."""
    session = MCPSession.query.filter_by(session_id=session_id).first()
    if not session:
        return False

    session.is_active = False
    db.session.commit()
    return True
```

---

### Phase 4: SSE Stream Implementation (Week 2)

```python
# ephergent_generator/mcp/transport.py

import json
import time
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

class SSEStream:
    """Server-Sent Events stream for MCP."""

    def __init__(self, session, last_event_id=None):
        self.session = session
        self.last_event_id = last_event_id
        self.message_queue = Queue()
        self.event_counter = 0

    def generate(self):
        """Generate SSE events."""
        try:
            # Send keepalive comment every 30 seconds
            last_keepalive = time.time()

            while True:
                try:
                    # Check for messages (with timeout for keepalive)
                    message = self.message_queue.get(timeout=30)

                    # Format as SSE event
                    event_id = f"{self.session.session_id}_{self.event_counter}"
                    self.event_counter += 1

                    yield f"id: {event_id}\n"
                    yield f"data: {json.dumps(message)}\n\n"

                except Empty:
                    # Send keepalive comment
                    if time.time() - last_keepalive > 30:
                        yield ": keepalive\n\n"
                        last_keepalive = time.time()

        except GeneratorExit:
            logger.info(f"SSE stream closed for session {self.session.session_id}")
        except Exception as e:
            logger.error(f"SSE stream error: {str(e)}", exc_info=True)

    def send_message(self, message):
        """Queue a message to be sent on the stream."""
        self.message_queue.put(message)
```

---

### Phase 5: MCP Handlers (Week 2-3)

```python
# ephergent_generator/mcp/handlers.py

from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.character_service import CharacterService
from ephergent_generator.models import Story, Character, WorkflowStep

class MCPHandlers:
    """MCP tool handlers - adapted from mcp_server.py."""

    def __init__(self, session):
        self.session = session
        self.workflow_service = StoryWorkflowService()
        self.character_service = CharacterService()

    @staticmethod
    def handle_initialize(params):
        """Handle MCP initialize request."""
        return {
            'protocolVersion': '2025-06-18',
            'capabilities': {
                'tools': {}
            },
            'serverInfo': {
                'name': 'ephergent-story-generator',
                'version': '3.0.0'
            }
        }

    def call_tool(self, name, arguments):
        """Route tool calls to appropriate handlers."""
        handlers = {
            'create_story': self.create_story,
            'get_story_status': self.get_story_status,
            'list_stories': self.list_stories,
            'get_story': self.get_story,
            'list_characters': self.list_characters,
            'regenerate_story': self.regenerate_story,
        }

        handler = handlers.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        return handler(arguments)

    def create_story(self, args):
        """Create a new story."""
        topic = args.get('topic')
        character_id = args.get('character_id')
        genre = args.get('genre')
        tone = args.get('tone')
        word_count = args.get('word_count', 500)

        # Validate word count
        if word_count > 2000:
            raise ValueError("Maximum word count is 2000")

        # Create story
        story = self.workflow_service.create_story_from_topic(
            topic=topic,
            genre=genre,
            tone=tone,
            word_count=word_count,
            narrator_character_id=character_id,
            session_id=f"mcp_{self.session.session_id}"
        )

        return {
            'content': [{
                'type': 'text',
                'text': f"Story created successfully! ID: {story.id}, Status: {story.current_step.value}"
            }]
        }

    # ... (implement other handlers similarly to mcp_server.py)
```

---

## Technical Decisions

### 1. Async Support in Flask

**Decision:** Use **Flask with gevent workers** via Gunicorn

**Rationale:**
- Flask is primarily synchronous
- SSE requires long-lived connections
- gevent provides cooperative multitasking
- Works well with existing Flask infrastructure
- No major code refactoring needed

**Implementation:**
```bash
gunicorn -k gevent -w 4 -b 0.0.0.0:5000 "main:app"
```

### 2. Session Storage

**Decision:** Use **Database (PostgreSQL)** for session storage

**Rationale:**
- Already using PostgreSQL for application data
- Simple session lifecycle management
- No additional infrastructure (Redis) needed for MVP
- Can migrate to Redis later if performance requires

**Future Enhancement:** Add Redis caching layer for high-traffic scenarios

### 3. Authentication Strategy

**Decision:** **Reuse existing API Key system** from auth blueprint

**Rationale:**
- Consistent with existing authentication patterns
- API keys already have permissions model
- Reduces code duplication
- Users already familiar with API key management

### 4. Message Queue for SSE

**Decision:** **In-memory Queue per session** (Python Queue)

**Rationale:**
- Simple implementation for MVP
- Sufficient for low-to-moderate concurrency
- Can upgrade to Redis pub/sub if needed

---

## Deployment Strategy

### Development Environment
```bash
# Run with gevent worker
gunicorn -k gevent -w 4 -b 0.0.0.0:5000 --reload "main:app"
```

### Production Environment
```bash
# Gunicorn with gevent workers
gunicorn -k gevent \
  -w 4 \
  -b 127.0.0.1:5000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info \
  "main:app"
```

### Nginx Configuration
```nginx
location /mcp {
    proxy_pass http://127.0.0.1:5000/mcp;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # SSE specific
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;  # 24 hours
}
```

---

## Security Considerations

### 1. Origin Header Validation
```python
# In routes.py
ALLOWED_ORIGINS = ['http://localhost', 'http://10.0.0.99']

def validate_origin():
    origin = request.headers.get('Origin')
    if origin and origin not in ALLOWED_ORIGINS:
        abort(403, "Invalid origin")
```

### 2. Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('Mcp-Session-Id', request.remote_addr)
)

@mcp_bp.route('', methods=['POST'])
@limiter.limit("100/hour")
def mcp_post():
    ...
```

### 3. Session Security
- Cryptographically secure session IDs (using `secrets`)
- 24-hour session expiration
- Automatic cleanup of expired sessions
- API key validation on session creation

---

## Migration Path

### Step 1: Keep STDIO Version
- No changes to `mcp_server/mcp_server.py`
- Continue supporting Claude Desktop local integration

### Step 2: Add Flask MCP Endpoint
- Implement new `/mcp` blueprint
- Run both simultaneously during testing

### Step 3: Deprecate Standalone SSE Server
- Once Flask integration is stable, deprecate `mcp_server_sse.py`
- Update documentation to point to `/mcp` endpoint

### Claude Desktop Configuration

**STDIO (Local) - Unchanged:**
```json
{
  "mcpServers": {
    "ephergent-local": {
      "command": "python",
      "args": ["mcp_server/mcp_server.py"],
      "cwd": "/path/to/ephergent_season_03_generator"
    }
  }
}
```

**HTTP (Remote) - New:**
```json
{
  "mcpServers": {
    "ephergent-remote": {
      "transport": {
        "type": "streamableHttp",
        "url": "http://10.0.0.99/mcp"
      }
    }
  }
}
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_mcp_routes.py
def test_mcp_post_initialize():
    """Test MCP initialization."""
    response = client.post('/mcp',
        json={'jsonrpc': '2.0', 'method': 'initialize', 'id': 1},
        headers={'Accept': 'application/json'})

    assert response.status_code == 200
    assert 'Mcp-Session-Id' in response.headers

def test_mcp_session_validation():
    """Test session validation."""
    # Create session
    # Test with valid session ID
    # Test with invalid session ID
    # Test with expired session
```

### Integration Tests
- Test full story generation workflow via MCP
- Test SSE stream connectivity
- Test session resumability
- Test concurrent requests

### Performance Tests
- Load test with multiple concurrent SSE streams
- Measure memory usage with long-lived connections
- Test session cleanup performance

---

## Database Migration

```python
# migrations/versions/xxx_add_mcp_sessions.py

def upgrade():
    op.create_table(
        'mcp_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=True),
        sa.Column('client_info', sa.JSON(), nullable=True),
        sa.Column('protocol_version', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_event_id', sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('ix_mcp_sessions_session_id', 'mcp_sessions', ['session_id'])

def downgrade():
    op.drop_index('ix_mcp_sessions_session_id')
    op.drop_table('mcp_sessions')
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create `ephergent_generator/mcp/` directory structure
- [ ] Add MCPSession model to `models.py`
- [ ] Create database migration for mcp_sessions table
- [ ] Implement MCP blueprint registration
- [ ] Add gevent to dependencies (pyproject.toml)

### Phase 2: Core Routes (Week 1-2)
- [ ] Implement POST endpoint for JSON-RPC
- [ ] Implement GET endpoint for SSE stream
- [ ] Implement DELETE endpoint for session termination
- [ ] Add session management (create, validate, terminate)
- [ ] Add Origin header validation

### Phase 3: MCP Logic (Week 2)
- [ ] Port MCP handlers from mcp_server.py
- [ ] Implement SSEStream class
- [ ] Add tool routing and dispatch
- [ ] Test with real MCP client

### Phase 4: Polish (Week 3)
- [ ] Add comprehensive error handling
- [ ] Implement rate limiting
- [ ] Add logging and monitoring
- [ ] Write unit and integration tests
- [ ] Update documentation

### Phase 5: Deployment (Week 3)
- [ ] Configure Gunicorn with gevent workers
- [ ] Update Nginx configuration
- [ ] Test on production VM
- [ ] Update Claude Desktop configuration docs
- [ ] Deprecate standalone SSE server

---

## Success Criteria

1. **Functional:**
   - MCP client can connect to `/mcp` endpoint
   - All MCP tools work correctly (create_story, list_stories, etc.)
   - SSE streams remain stable for extended periods
   - Session management works correctly

2. **Performance:**
   - Handle at least 10 concurrent SSE connections
   - Response time < 500ms for tool calls
   - Memory usage remains stable over 24 hours

3. **Security:**
   - All requests authenticated via API keys
   - Origin header validation working
   - No session hijacking possible
   - Rate limiting prevents abuse

4. **Compatibility:**
   - STDIO version continues to work
   - Existing API endpoints unaffected
   - Can run both transports simultaneously

---

## Future Enhancements

1. **Redis Integration:**
   - Move session storage to Redis for better performance
   - Implement Redis pub/sub for SSE messages
   - Enable horizontal scaling across multiple workers

2. **WebSocket Support:**
   - Add WebSocket transport as alternative to SSE
   - Better bidirectional communication
   - Reduced latency for real-time updates

3. **Admin Dashboard:**
   - View active MCP sessions
   - Monitor session activity
   - Force terminate sessions
   - View MCP tool usage statistics

4. **Advanced Features:**
   - Tool result streaming (for long-running operations)
   - Progress notifications during story generation
   - Batch operations support
   - MCP resource support (prompts, data sources)

---

## Questions & Decisions Needed

1. **API Key Permissions:** Should MCP access require specific permissions, or reuse existing API key permissions?
   - **Recommendation:** Reuse existing, add `mcp:access` permission if granularity needed

2. **Session Timeout:** What should the default session timeout be?
   - **Recommendation:** 24 hours with automatic cleanup

3. **Concurrent Streams:** Should we limit SSE streams per session?
   - **Recommendation:** Start with 3 concurrent streams per session

4. **Error Reporting:** How detailed should error messages be to MCP clients?
   - **Recommendation:** Detailed for development, sanitized for production

---

## References

- [MCP Specification - Transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)
- [MCP Specification - Lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)
- [Flask SSE Documentation](https://flask.palletsprojects.com/en/latest/patterns/streaming/)
- [Gunicorn gevent Workers](https://docs.gunicorn.org/en/stable/design.html#async-workers)
