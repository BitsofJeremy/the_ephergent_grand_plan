# Phase 1: Production Readiness & Stability - Technical Architecture

**Version:** 1.0
**Date:** 2025-10-08
**Status:** Design Complete - Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Component Design](#component-design)
4. [Database Schema Additions](#database-schema-additions)
5. [Technology Stack](#technology-stack)
6. [Implementation Phases](#implementation-phases)
7. [Deployment Strategy](#deployment-strategy)
8. [Success Metrics](#success-metrics)
9. [Migration Strategy](#migration-strategy)
10. [Testing Approach](#testing-approach)

---

## Executive Summary

Phase 1 transforms the Ephergent story generation system from a functional prototype into a production-ready, observable, and resilient platform. This architecture document provides a comprehensive technical design for three core pillars:

1. **System Monitoring & Observability** - Structured logging, Prometheus metrics, health checks
2. **Error Handling & Recovery** - Automatic retries, dead letter queues, story intervention tools
3. **Database Optimization** - Connection pooling, archiving, retention policies

**Key Design Principles:**
- **12-Factor App Methodology** - Environment-based config, stateless processes, disposable workers
- **Cloud-Native Observability** - Prometheus metrics, structured JSON logging, OpenMetrics compatibility
- **Graceful Degradation** - System continues operating when non-critical services fail
- **Zero-Downtime Deployment** - Rolling updates, health checks, graceful shutdowns

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                       │
│                    SSL/TLS, Rate Limiting, Caching                  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
         ┌────────────┴─────────────┬─────────────────────────────────┐
         │                          │                                 │
┌────────▼────────┐     ┌───────────▼──────────┐     ┌──────────────▼──────┐
│  Flask Web App  │     │  Background Worker   │     │   MCP Server         │
│  (Gunicorn)     │     │  (Continuous Mode)   │     │   (Story API)        │
│                 │     │                      │     │                      │
│  - Web UI       │     │  - Queue Processor   │     │  - Claude Desktop    │
│  - REST API     │     │  - Workflow Engine   │     │  - External Clients  │
│  - Health Check │     │  - Retry Logic       │     │                      │
└────────┬────────┘     └───────────┬──────────┘     └──────────────┬──────┘
         │                          │                                │
         └──────────────────────────┴────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────▼──────────┐         ┌─────────▼─────────┐
         │   PostgreSQL DB     │         │   Redis Cache     │
         │                     │         │                   │
         │  - Stories          │         │  - Metrics Cache  │
         │  - Workflow State   │         │  - Rate Limiting  │
         │  - Metrics Table    │         │  - Worker Locks   │
         │  - Retry Tracking   │         │                   │
         │  - Audit Logs       │         └───────────────────┘
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Prometheus Server  │
         │                     │
         │  - /metrics scraper │
         │  - Alert Manager    │
         │  - Time-Series DB   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Grafana UI        │
         │                     │
         │  - Dashboards       │
         │  - Alert Visualizer │
         └─────────────────────┘
```

### Data Flow: Story Processing with Observability

```
User Request → Flask API → Create Story → Queue Entry
                  │
                  ├─> Log: INFO - Story {id} created
                  ├─> Metric: stories_created_total++
                  └─> Database: Story + StoryQueue + StoryRetry records
                                │
                ┌───────────────▼────────────────┐
                │   Background Worker (Loop)      │
                │                                 │
                │  1. Poll Queue                  │
                │  2. Acquire Worker Lock (Redis) │
                │  3. Process Workflow Step       │
                │  4. Update Metrics              │
                │  5. Log Progress (JSON)         │
                │  6. Retry on Transient Failure  │
                │  7. DLQ on Permanent Failure    │
                └───────────────┬─────────────────┘
                                │
                    ┌───────────┴──────────┬────────────────┐
                    │                      │                │
            ┌───────▼───────┐    ┌────────▼──────┐  ┌─────▼──────┐
            │   Success     │    │  Retry Logic  │  │  DLQ       │
            │               │    │               │  │            │
            │ - Next Step   │    │ - Backoff     │  │ - Failed   │
            │ - Log: INFO   │    │ - Max 3 tries │  │ - Alert    │
            │ - Metric++    │    │ - Log: WARN   │  │ - Manual   │
            └───────────────┘    └───────────────┘  └────────────┘
```

---

## Component Design

### 1. Structured Logging System

**Objective:** Replace ad-hoc print statements and basic logging with structured JSON logs for easy parsing, searching, and analysis.

#### Design

**Log Format:** JSON Lines (newline-delimited JSON)

```json
{
  "timestamp": "2025-10-08T14:32:10.123456Z",
  "level": "INFO",
  "logger": "ephergent_generator.services.workflow_service",
  "message": "Processing story workflow step",
  "story_id": 42,
  "workflow_step": "image_generation",
  "worker_id": "worker_abc123",
  "request_id": "req-xyz789",
  "duration_ms": 1234,
  "context": {
    "session_id": "sess-123",
    "narrator_character_id": "ezra",
    "genre": "sci-fi"
  }
}
```

**Implementation:**

- **Library:** `python-json-logger` (structlog alternative for Flask compatibility)
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Outputs:**
  - **Development:** Console (human-readable) + File (JSON)
  - **Production:** File (JSON) + Syslog (optional for centralized logging)

**Logging Service (`ephergent_generator/utils/logging_config.py`):**

```python
import logging
import sys
from pythonjsonlogger import jsonlogger
from flask import g, request
import uuid

class ContextualJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes Flask request context."""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record['timestamp'] = record.created

        # Add Flask request context if available
        try:
            if request:
                log_record['request_id'] = getattr(g, 'request_id', None)
                log_record['method'] = request.method
                log_record['path'] = request.path
                log_record['remote_addr'] = request.remote_addr
        except RuntimeError:
            # Outside request context
            pass

        # Add environment
        log_record['environment'] = current_app.config.get('ENV', 'unknown')

def setup_logging(app):
    """Configure structured logging for the application."""

    # Create JSON formatter
    json_formatter = ContextualJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )

    # File handler (JSON logs)
    file_handler = logging.FileHandler(
        app.config.get('LOG_FILE', 'ephergent.log')
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)

    # Console handler (human-readable in dev, JSON in prod)
    console_handler = logging.StreamHandler(sys.stdout)
    if app.config.get('ENV') == 'production':
        console_handler.setFormatter(json_formatter)
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure Flask app logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Add request ID middleware
    @app.before_request
    def assign_request_id():
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    return app
```

**Usage in Services:**

```python
import logging

logger = logging.getLogger(__name__)

# Structured logging with extra context
logger.info(
    "Story generation completed",
    extra={
        'story_id': story.id,
        'workflow_step': story.current_step.value,
        'word_count': story.word_count,
        'duration_ms': elapsed_time * 1000
    }
)
```

---

### 2. Prometheus Metrics Collection

**Objective:** Expose application metrics in Prometheus format for monitoring, alerting, and performance analysis.

#### Design

**Metrics Categories:**

1. **Business Metrics** - Story generation success/failure, workflow steps completed
2. **Application Metrics** - Request latency, queue depth, worker utilization
3. **Infrastructure Metrics** - Database connections, Redis hits/misses, memory usage
4. **External Service Metrics** - Gemini API latency, ComfyUI success rate, YouTube upload time

**Prometheus Client Library:** `prometheus-client` (official Python client)

**Metrics Service (`ephergent_generator/utils/metrics.py`):**

```python
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
import time
from functools import wraps
from flask import current_app

# Custom registry for application metrics
registry = CollectorRegistry()

# Business Metrics
stories_created_total = Counter(
    'ephergent_stories_created_total',
    'Total number of stories created',
    ['narrator_character', 'genre'],
    registry=registry
)

stories_completed_total = Counter(
    'ephergent_stories_completed_total',
    'Total number of stories fully completed',
    ['narrator_character', 'genre'],
    registry=registry
)

stories_failed_total = Counter(
    'ephergent_stories_failed_total',
    'Total number of stories that failed processing',
    ['workflow_step', 'error_type'],
    registry=registry
)

workflow_step_duration_seconds = Histogram(
    'ephergent_workflow_step_duration_seconds',
    'Duration of workflow steps in seconds',
    ['workflow_step', 'status'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],  # 1s to 10min
    registry=registry
)

# Application Metrics
queue_depth = Gauge(
    'ephergent_queue_depth',
    'Number of stories waiting in queue',
    registry=registry
)

active_workers = Gauge(
    'ephergent_active_workers',
    'Number of active background workers',
    registry=registry
)

http_requests_total = Counter(
    'ephergent_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'ephergent_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
    registry=registry
)

# Infrastructure Metrics
db_connections_active = Gauge(
    'ephergent_db_connections_active',
    'Number of active database connections',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'ephergent_db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1, 2],
    registry=registry
)

# External Service Metrics
external_api_requests_total = Counter(
    'ephergent_external_api_requests_total',
    'Total external API requests',
    ['service', 'status'],
    registry=registry
)

external_api_duration_seconds = Histogram(
    'ephergent_external_api_duration_seconds',
    'External API request duration in seconds',
    ['service'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60],
    registry=registry
)

# Retry Metrics
story_retries_total = Counter(
    'ephergent_story_retries_total',
    'Total story processing retries',
    ['workflow_step', 'retry_count'],
    registry=registry
)

# Dead Letter Queue Metrics
dlq_stories_total = Gauge(
    'ephergent_dlq_stories_total',
    'Number of stories in dead letter queue',
    registry=registry
)

# System Info
app_info = Info(
    'ephergent_app',
    'Application version and environment info',
    registry=registry
)

def track_workflow_step(workflow_step):
    """Decorator to track workflow step execution time and status."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            try:
                result = func(*args, **kwargs)
                success = result  # Assuming bool return for success/failure
                return result
            finally:
                duration = time.time() - start_time
                status = 'success' if success else 'failure'
                workflow_step_duration_seconds.labels(
                    workflow_step=workflow_step,
                    status=status
                ).observe(duration)
        return wrapper
    return decorator

def track_external_api(service_name):
    """Decorator to track external API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'error'
            try:
                result = func(*args, **kwargs)
                status = 'success' if result else 'error'
                return result
            except Exception as e:
                status = 'exception'
                raise
            finally:
                duration = time.time() - start_time
                external_api_requests_total.labels(
                    service=service_name,
                    status=status
                ).inc()
                external_api_duration_seconds.labels(
                    service=service_name
                ).observe(duration)
        return wrapper
    return decorator

def update_queue_metrics(app):
    """Update queue depth metrics (called periodically)."""
    with app.app_context():
        from ephergent_generator.models import StoryQueue
        from ephergent_generator import db

        waiting = db.session.query(StoryQueue).filter(
            StoryQueue.worker_id.is_(None)
        ).count()

        processing = db.session.query(StoryQueue).filter(
            StoryQueue.worker_id.isnot(None)
        ).count()

        queue_depth.set(waiting)
        active_workers.set(processing)

def update_dlq_metrics(app):
    """Update dead letter queue metrics."""
    with app.app_context():
        from ephergent_generator.models import StoryRetry
        from ephergent_generator import db

        dlq_count = db.session.query(StoryRetry).filter(
            StoryRetry.retry_status == 'dead_letter'
        ).count()

        dlq_stories_total.set(dlq_count)

def set_app_info(version, environment):
    """Set application metadata."""
    app_info.info({
        'version': version,
        'environment': environment,
        'python_version': sys.version.split()[0]
    })
```

**Metrics Endpoint (`ephergent_generator/api/metrics.py`):**

```python
from flask import Blueprint, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from ephergent_generator.utils.metrics import registry, update_queue_metrics, update_dlq_metrics
from flask import current_app

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    # Update dynamic metrics before scraping
    update_queue_metrics(current_app)
    update_dlq_metrics(current_app)

    # Generate Prometheus metrics
    metrics_data = generate_latest(registry)

    return Response(metrics_data, mimetype=CONTENT_TYPE_LATEST)
```

**Integration in Services:**

```python
from ephergent_generator.utils.metrics import (
    stories_created_total,
    track_workflow_step,
    track_external_api
)

class StoryWorkflowService:

    @track_workflow_step('story_generation')
    def _process_story_generation(self, story):
        """Process story generation step with metrics."""
        try:
            # ... existing code ...

            # Increment success counter
            stories_created_total.labels(
                narrator_character=story.narrator_character_id or 'none',
                genre=story.genre or 'unknown'
            ).inc()

            return True
        except Exception as e:
            stories_failed_total.labels(
                workflow_step='story_generation',
                error_type=type(e).__name__
            ).inc()
            return False
```

---

### 3. Health Check System

**Objective:** Provide comprehensive health checks for the application and its dependencies for monitoring, load balancing, and deployment orchestration.

#### Design

**Health Check Levels:**

1. **Liveness** - Is the application alive? (HTTP 200 if process is running)
2. **Readiness** - Is the application ready to accept traffic? (Checks DB, Redis, etc.)
3. **Dependency** - Individual health checks for external services

**Health Check Service (`ephergent_generator/utils/health_checks.py`):**

```python
from flask import current_app
from ephergent_generator import db
import redis
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class HealthCheckResult:
    """Result of a health check."""

    def __init__(self, name, healthy, message='', latency_ms=0, metadata=None):
        self.name = name
        self.healthy = healthy
        self.message = message
        self.latency_ms = latency_ms
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            'name': self.name,
            'healthy': self.healthy,
            'message': self.message,
            'latency_ms': self.latency_ms,
            'metadata': self.metadata
        }

class HealthChecker:
    """Comprehensive health check manager."""

    @staticmethod
    def check_database():
        """Check PostgreSQL database connectivity."""
        import time
        start = time.time()

        try:
            # Simple query to test connection
            result = db.session.execute(db.text('SELECT 1')).scalar()
            latency = (time.time() - start) * 1000

            if result == 1:
                return HealthCheckResult(
                    name='database',
                    healthy=True,
                    message='Database connection successful',
                    latency_ms=latency
                )
            else:
                return HealthCheckResult(
                    name='database',
                    healthy=False,
                    message='Database query returned unexpected result',
                    latency_ms=latency
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error(f"Database health check failed: {str(e)}")
            return HealthCheckResult(
                name='database',
                healthy=False,
                message=f'Database error: {str(e)}',
                latency_ms=latency
            )

    @staticmethod
    def check_redis():
        """Check Redis connectivity (optional)."""
        import time
        start = time.time()

        redis_url = current_app.config.get('REDIS_URL')
        if not redis_url:
            return HealthCheckResult(
                name='redis',
                healthy=True,  # Optional dependency
                message='Redis not configured (optional)',
                latency_ms=0
            )

        try:
            r = redis.from_url(redis_url)
            r.ping()
            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name='redis',
                healthy=True,
                message='Redis connection successful',
                latency_ms=latency
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error(f"Redis health check failed: {str(e)}")
            return HealthCheckResult(
                name='redis',
                healthy=False,
                message=f'Redis error: {str(e)}',
                latency_ms=latency
            )

    @staticmethod
    def check_gemini_api():
        """Check Google Gemini API availability."""
        import time
        start = time.time()

        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return HealthCheckResult(
                name='gemini_api',
                healthy=False,
                message='Gemini API key not configured',
                latency_ms=0
            )

        try:
            # Simple API test (you may want a lightweight endpoint)
            # For now, just check if key is present
            latency = (time.time() - start) * 1000

            return HealthCheckResult(
                name='gemini_api',
                healthy=True,
                message='Gemini API configured',
                latency_ms=latency,
                metadata={'key_present': bool(api_key)}
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthCheckResult(
                name='gemini_api',
                healthy=False,
                message=f'Gemini API error: {str(e)}',
                latency_ms=latency
            )

    @staticmethod
    def check_comfyui():
        """Check ComfyUI service availability."""
        import time
        start = time.time()

        comfyui_url = current_app.config.get('COMFYUI_URL')
        if not comfyui_url:
            return HealthCheckResult(
                name='comfyui',
                healthy=True,  # Optional dependency
                message='ComfyUI not configured (optional)',
                latency_ms=0
            )

        try:
            # Ping ComfyUI health endpoint
            response = requests.get(f"{comfyui_url}/health", timeout=5)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                return HealthCheckResult(
                    name='comfyui',
                    healthy=True,
                    message='ComfyUI service available',
                    latency_ms=latency
                )
            else:
                return HealthCheckResult(
                    name='comfyui',
                    healthy=False,
                    message=f'ComfyUI returned status {response.status_code}',
                    latency_ms=latency
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthCheckResult(
                name='comfyui',
                healthy=False,
                message=f'ComfyUI error: {str(e)}',
                latency_ms=latency
            )

    @staticmethod
    def check_worker_health():
        """Check if background workers are active."""
        try:
            from ephergent_generator.models import StoryQueue

            # Check for workers that have processed stories in last 5 minutes
            recent_time = datetime.utcnow() - timedelta(minutes=5)

            active_workers = db.session.query(StoryQueue.worker_id).filter(
                StoryQueue.worker_id.isnot(None),
                StoryQueue.processing_started_at > recent_time
            ).distinct().count()

            return HealthCheckResult(
                name='workers',
                healthy=active_workers > 0,
                message=f'{active_workers} active workers',
                latency_ms=0,
                metadata={'active_workers': active_workers}
            )
        except Exception as e:
            return HealthCheckResult(
                name='workers',
                healthy=False,
                message=f'Worker check error: {str(e)}',
                latency_ms=0
            )

    @staticmethod
    def liveness_check():
        """Simple liveness check - is the app alive?"""
        return {
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def readiness_check():
        """Comprehensive readiness check - is the app ready to serve traffic?"""
        checks = [
            HealthChecker.check_database(),
            # Redis is optional, so don't fail on Redis errors
        ]

        all_healthy = all(check.healthy for check in checks if check.name == 'database')

        return {
            'status': 'ready' if all_healthy else 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [check.to_dict() for check in checks]
        }

    @staticmethod
    def full_health_check():
        """Full health check including all dependencies."""
        checks = [
            HealthChecker.check_database(),
            HealthChecker.check_redis(),
            HealthChecker.check_gemini_api(),
            HealthChecker.check_comfyui(),
            HealthChecker.check_worker_health()
        ]

        # Critical: database, gemini_api
        # Optional: redis, comfyui, workers
        critical_checks = [c for c in checks if c.name in ['database', 'gemini_api']]
        all_critical_healthy = all(check.healthy for check in critical_checks)

        return {
            'status': 'healthy' if all_critical_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [check.to_dict() for check in checks],
            'summary': {
                'total_checks': len(checks),
                'healthy_checks': sum(1 for c in checks if c.healthy),
                'unhealthy_checks': sum(1 for c in checks if not c.healthy)
            }
        }
```

**Health Check API (`ephergent_generator/api/health.py` - update existing):**

```python
from flask import Blueprint, jsonify
from ephergent_generator.utils.health_checks import HealthChecker

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/liveness')
def liveness():
    """Liveness probe - is the app alive?"""
    result = HealthChecker.liveness_check()
    return jsonify(result), 200

@health_bp.route('/health/readiness')
def readiness():
    """Readiness probe - is the app ready to serve traffic?"""
    result = HealthChecker.readiness_check()
    status_code = 200 if result['status'] == 'ready' else 503
    return jsonify(result), status_code

@health_bp.route('/health')
@health_bp.route('/health/full')
def full_health():
    """Full health check including all dependencies."""
    result = HealthChecker.full_health_check()
    status_code = 200 if result['status'] == 'healthy' else 503
    return jsonify(result), status_code
```

---

### 4. Error Handling & Retry Logic

**Objective:** Implement automatic retry logic with exponential backoff for transient failures, dead letter queue for permanent failures, and manual intervention tools.

#### Design

**Retry Strategy:**

- **Max Retries:** 3 attempts per workflow step
- **Backoff:** Exponential with jitter (1s, 2s, 4s)
- **Retryable Errors:** Network timeouts, rate limits, transient API errors
- **Non-Retryable Errors:** Validation errors, authentication failures, quota exceeded

**Dead Letter Queue (DLQ):**

- Stories that fail after max retries are moved to DLQ
- DLQ stories are flagged for manual intervention
- Admin can view DLQ, inspect errors, and re-queue stories

**Database Schema Addition:**

```python
class StoryRetry(db.Model):
    """Tracks retry attempts for story workflow steps."""
    __tablename__ = 'story_retries'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    workflow_step = db.Column(db.String(50), nullable=False)

    # Retry tracking
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    last_error = db.Column(db.Text, nullable=True)
    last_retry_at = db.Column(db.DateTime, nullable=True)

    # Retry status
    retry_status = db.Column(
        db.String(20),
        default='pending',
        nullable=False
    )  # pending, retrying, success, dead_letter

    # Error classification
    error_type = db.Column(db.String(50), nullable=True)  # network, timeout, api_error, validation
    is_retryable = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    dead_lettered_at = db.Column(db.DateTime, nullable=True)

    # Relationship
    story = db.relationship('Story', backref=db.backref('retries', lazy=True))

    def __repr__(self):
        return f'<StoryRetry story_id={self.story_id} step={self.workflow_step} count={self.retry_count}>'

    def should_retry(self):
        """Check if this story should be retried."""
        return (
            self.is_retryable and
            self.retry_count < self.max_retries and
            self.retry_status not in ['success', 'dead_letter']
        )

    def calculate_backoff_seconds(self):
        """Calculate exponential backoff with jitter."""
        import random
        base_delay = 2 ** self.retry_count  # 1s, 2s, 4s
        jitter = random.uniform(0, 0.5 * base_delay)
        return base_delay + jitter

    def mark_dead_letter(self, reason=None):
        """Move to dead letter queue."""
        self.retry_status = 'dead_letter'
        self.dead_lettered_at = datetime.utcnow()
        if reason:
            self.last_error = reason

    def to_dict(self):
        return {
            'id': self.id,
            'story_id': self.story_id,
            'workflow_step': self.workflow_step,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'retry_status': self.retry_status,
            'error_type': self.error_type,
            'is_retryable': self.is_retryable,
            'last_error': self.last_error,
            'last_retry_at': self.last_retry_at.isoformat() if self.last_retry_at else None,
            'dead_lettered_at': self.dead_lettered_at.isoformat() if self.dead_lettered_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

**Retry Service (`ephergent_generator/services/retry_service.py`):**

```python
import logging
from datetime import datetime
from ephergent_generator import db
from ephergent_generator.models import Story, StoryRetry, WorkflowStep
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of errors for retry logic."""
    NETWORK = 'network'
    TIMEOUT = 'timeout'
    API_ERROR = 'api_error'
    RATE_LIMIT = 'rate_limit'
    VALIDATION = 'validation'
    AUTHENTICATION = 'authentication'
    QUOTA_EXCEEDED = 'quota_exceeded'
    UNKNOWN = 'unknown'

class RetryService:
    """Service for managing story retry logic."""

    # Non-retryable error types
    NON_RETRYABLE_ERRORS = [
        ErrorType.VALIDATION,
        ErrorType.AUTHENTICATION,
        ErrorType.QUOTA_EXCEEDED
    ]

    @staticmethod
    def classify_error(exception):
        """Classify an exception to determine if it's retryable."""
        error_message = str(exception).lower()

        if isinstance(exception, (TimeoutError, ConnectionError)):
            return ErrorType.TIMEOUT
        elif 'rate limit' in error_message or '429' in error_message:
            return ErrorType.RATE_LIMIT
        elif 'network' in error_message or 'connection' in error_message:
            return ErrorType.NETWORK
        elif 'quota' in error_message or 'limit exceeded' in error_message:
            return ErrorType.QUOTA_EXCEEDED
        elif 'authentication' in error_message or '401' in error_message:
            return ErrorType.AUTHENTICATION
        elif 'validation' in error_message or 'invalid' in error_message:
            return ErrorType.VALIDATION
        else:
            return ErrorType.UNKNOWN

    @staticmethod
    def is_retryable(error_type):
        """Check if an error type is retryable."""
        return error_type not in RetryService.NON_RETRYABLE_ERRORS

    @staticmethod
    def record_failure(story, workflow_step, exception):
        """Record a failure and determine if retry is needed."""
        error_type = RetryService.classify_error(exception)
        is_retryable = RetryService.is_retryable(error_type)

        # Get or create retry record for this story and step
        retry_record = StoryRetry.query.filter_by(
            story_id=story.id,
            workflow_step=workflow_step.value
        ).first()

        if not retry_record:
            retry_record = StoryRetry(
                story_id=story.id,
                workflow_step=workflow_step.value,
                error_type=error_type.value,
                is_retryable=is_retryable
            )
            db.session.add(retry_record)

        # Update retry record
        retry_record.retry_count += 1
        retry_record.last_error = str(exception)
        retry_record.last_retry_at = datetime.utcnow()
        retry_record.error_type = error_type.value

        # Check if we should retry or move to DLQ
        if not retry_record.should_retry():
            retry_record.mark_dead_letter(
                reason=f"Max retries exceeded ({retry_record.retry_count}/{retry_record.max_retries})"
            )
            logger.error(
                f"Story {story.id} moved to DLQ after {retry_record.retry_count} retries",
                extra={
                    'story_id': story.id,
                    'workflow_step': workflow_step.value,
                    'error_type': error_type.value,
                    'retry_count': retry_record.retry_count
                }
            )
        else:
            retry_record.retry_status = 'retrying'
            backoff = retry_record.calculate_backoff_seconds()
            logger.warning(
                f"Story {story.id} will be retried in {backoff:.1f}s (attempt {retry_record.retry_count}/{retry_record.max_retries})",
                extra={
                    'story_id': story.id,
                    'workflow_step': workflow_step.value,
                    'error_type': error_type.value,
                    'retry_count': retry_record.retry_count,
                    'backoff_seconds': backoff
                }
            )

        db.session.commit()

        return retry_record

    @staticmethod
    def record_success(story, workflow_step):
        """Record a successful workflow step execution."""
        retry_record = StoryRetry.query.filter_by(
            story_id=story.id,
            workflow_step=workflow_step.value
        ).first()

        if retry_record:
            retry_record.retry_status = 'success'
            db.session.commit()

            logger.info(
                f"Story {story.id} workflow step succeeded after {retry_record.retry_count} retries",
                extra={
                    'story_id': story.id,
                    'workflow_step': workflow_step.value,
                    'retry_count': retry_record.retry_count
                }
            )

    @staticmethod
    def get_dead_letter_queue():
        """Get all stories in the dead letter queue."""
        return StoryRetry.query.filter_by(
            retry_status='dead_letter'
        ).order_by(StoryRetry.dead_lettered_at.desc()).all()

    @staticmethod
    def requeue_from_dlq(story_id, reset_retries=True):
        """Manually re-queue a story from the dead letter queue."""
        retry_records = StoryRetry.query.filter_by(
            story_id=story_id,
            retry_status='dead_letter'
        ).all()

        if not retry_records:
            logger.warning(f"No DLQ entries found for story {story_id}")
            return False

        for retry_record in retry_records:
            if reset_retries:
                retry_record.retry_count = 0
            retry_record.retry_status = 'pending'
            retry_record.dead_lettered_at = None

        # Reset story to the failed step
        story = Story.query.get(story_id)
        if story:
            # Find the earliest failed step
            earliest_step = min(
                (WorkflowStep[r.workflow_step.upper()] for r in retry_records),
                key=lambda s: list(WorkflowStep).index(s)
            )
            story.current_step = earliest_step
            story.error_message = None

        db.session.commit()

        logger.info(
            f"Story {story_id} re-queued from DLQ",
            extra={'story_id': story_id, 'reset_retries': reset_retries}
        )

        return True
```

**Integration in Workflow Service:**

```python
from ephergent_generator.services.retry_service import RetryService

class StoryWorkflowService:

    def _process_story_generation(self, story):
        """Process story generation with retry logic."""
        try:
            # ... existing story generation code ...

            # Record success
            RetryService.record_success(story, WorkflowStep.STORY_GENERATION)
            return True

        except Exception as e:
            # Record failure and determine retry
            retry_record = RetryService.record_failure(
                story,
                WorkflowStep.STORY_GENERATION,
                e
            )

            if retry_record.retry_status == 'dead_letter':
                # Move to failed state
                story.advance_workflow(WorkflowStep.FAILED, error=str(e))
            # else: Story will be retried automatically

            return False
```

---

### 5. Database Optimization

**Objective:** Optimize database performance through connection pooling, query optimization, and data archiving.

#### Connection Pooling Configuration

**Update `config.py`:**

```python
class Config:
    # ... existing config ...

    # Database Connection Pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),  # Default 10 connections
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 20)),  # Additional 20 connections
        'pool_timeout': 30,  # Timeout waiting for connection (seconds)
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Test connections before using
        'echo_pool': os.environ.get('DB_ECHO_POOL', 'False').lower() in ('true', '1'),
    }
```

#### Story Archiving System

**Database Schema:**

```python
class ArchivedStory(db.Model):
    """Archived stories for long-term storage."""
    __tablename__ = 'archived_stories'

    id = db.Column(db.Integer, primary_key=True)
    original_story_id = db.Column(db.Integer, nullable=False, index=True)

    # Snapshot of story data (JSON)
    story_data = db.Column(db.Text, nullable=False)  # JSON dump of full story

    # Archive metadata
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    archived_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    archive_reason = db.Column(db.String(100), nullable=True)

    # Original timestamps
    story_created_at = db.Column(db.DateTime, nullable=True)
    story_completed_at = db.Column(db.DateTime, nullable=True)

    # Retention
    delete_after = db.Column(db.DateTime, nullable=True)  # Auto-delete after this date

    def __repr__(self):
        return f'<ArchivedStory id={self.id} original_id={self.original_story_id}>'

    @staticmethod
    def from_story(story, reason='retention_policy'):
        """Create archived story from a Story object."""
        return ArchivedStory(
            original_story_id=story.id,
            story_data=json.dumps(story.to_dict()),
            archive_reason=reason,
            story_created_at=story.created_at,
            story_completed_at=story.completed_at
        )
```

**Archive Service (`ephergent_generator/services/archive_service.py` - update existing):**

```python
import logging
from datetime import datetime, timedelta
from ephergent_generator import db
from ephergent_generator.models import Story, ArchivedStory, WorkflowStep

logger = logging.getLogger(__name__)

class ArchiveService:
    """Service for archiving and managing old stories."""

    @staticmethod
    def archive_old_stories(days_old=90, batch_size=100):
        """Archive completed stories older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Find old completed stories
        old_stories = Story.query.filter(
            Story.current_step == WorkflowStep.COMPLETED,
            Story.completed_at < cutoff_date
        ).limit(batch_size).all()

        archived_count = 0

        for story in old_stories:
            try:
                # Create archived copy
                archived = ArchivedStory.from_story(story, reason='retention_policy')
                db.session.add(archived)

                # Delete original
                db.session.delete(story)

                archived_count += 1

                logger.info(
                    f"Archived story {story.id}",
                    extra={'story_id': story.id, 'age_days': (datetime.utcnow() - story.completed_at).days}
                )

            except Exception as e:
                logger.error(f"Failed to archive story {story.id}: {str(e)}")
                db.session.rollback()
                continue

        db.session.commit()

        logger.info(f"Archived {archived_count} old stories")
        return archived_count

    @staticmethod
    def restore_archived_story(archived_story_id):
        """Restore an archived story back to active stories."""
        archived = ArchivedStory.query.get(archived_story_id)
        if not archived:
            return None

        try:
            # Parse story data
            story_data = json.loads(archived.story_data)

            # Create new story (note: won't have same ID)
            story = Story(**story_data)
            db.session.add(story)
            db.session.commit()

            logger.info(f"Restored archived story {archived_story_id} as new story {story.id}")
            return story

        except Exception as e:
            logger.error(f"Failed to restore archived story {archived_story_id}: {str(e)}")
            db.session.rollback()
            return None
```

---

## Database Schema Additions

### Summary of New Tables

1. **`story_retries`** - Tracks retry attempts for story workflow steps
2. **`archived_stories`** - Long-term storage for old completed stories
3. **Updates to existing tables:**
   - Add indexes for common queries
   - Add retention metadata fields

### Migration Script

**Create migration:**

```bash
flask db migrate -m "Add Phase 1 observability and retry tables"
flask db upgrade
```

**Migration file (`migrations/versions/xxx_phase1_observability.py`):**

```python
"""Add Phase 1 observability and retry tables

Revision ID: xxx
Revises: yyy
Create Date: 2025-10-08
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade():
    # Create story_retries table
    op.create_table(
        'story_retries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('workflow_step', sa.String(50), nullable=False),
        sa.Column('retry_count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_retries', sa.Integer(), default=3, nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_retry_at', sa.DateTime(), nullable=True),
        sa.Column('retry_status', sa.String(20), default='pending', nullable=False),
        sa.Column('error_type', sa.String(50), nullable=True),
        sa.Column('is_retryable', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False),
        sa.Column('dead_lettered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_retry_story_step', 'story_retries', ['story_id', 'workflow_step'])
    op.create_index('idx_retry_status', 'story_retries', ['retry_status'])

    # Create archived_stories table
    op.create_table(
        'archived_stories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_story_id', sa.Integer(), nullable=False),
        sa.Column('story_data', sa.Text(), nullable=False),
        sa.Column('archived_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('archived_by', sa.Integer(), nullable=True),
        sa.Column('archive_reason', sa.String(100), nullable=True),
        sa.Column('story_created_at', sa.DateTime(), nullable=True),
        sa.Column('story_completed_at', sa.DateTime(), nullable=True),
        sa.Column('delete_after', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['archived_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_archived_original_id', 'archived_stories', ['original_story_id'])
    op.create_index('idx_archived_date', 'archived_stories', ['archived_at'])

    # Add performance indexes to existing tables
    op.create_index('idx_story_step_updated', 'stories', ['current_step', 'updated_at'])
    op.create_index('idx_story_completed', 'stories', ['completed_at'])

def downgrade():
    op.drop_index('idx_story_completed', 'stories')
    op.drop_index('idx_story_step_updated', 'stories')

    op.drop_index('idx_archived_date', 'archived_stories')
    op.drop_index('idx_archived_original_id', 'archived_stories')
    op.drop_table('archived_stories')

    op.drop_index('idx_retry_status', 'story_retries')
    op.drop_index('idx_retry_story_step', 'story_retries')
    op.drop_table('story_retries')
```

---

## Technology Stack

### Python Libraries

```toml
# Add to pyproject.toml [project.dependencies]

# Observability & Monitoring
"prometheus-client>=0.20.0",        # Prometheus metrics
"python-json-logger>=2.0.7",        # Structured JSON logging

# Redis (optional - for distributed locks and caching)
"redis>=5.0.0",                     # Redis client
"redis-py-cluster>=2.1.3",         # Redis cluster support

# Performance & Reliability
"psycopg2-binary>=2.9.9",          # Already present - PostgreSQL driver
"sqlalchemy[asyncio]>=2.0.0",      # Async SQLAlchemy support (future)
```

### Debian System Packages

```bash
# Required for Phase 1
apt-get install -y \
    prometheus \
    prometheus-node-exporter \
    grafana \
    redis-server \
    logrotate \
    postgresql-client-15 \
    python3-systemd
```

### External Services

1. **Prometheus** - Metrics collection and alerting
   - Version: 2.45+ (from Debian bookworm)
   - Port: 9090
   - Configuration: `/etc/prometheus/prometheus.yml`

2. **Grafana** - Metrics visualization
   - Version: 10.x+ (from Grafana APT repository)
   - Port: 3000
   - Configuration: `/etc/grafana/grafana.ini`

3. **Redis** (Optional - for Phase 1.2)
   - Version: 7.0+
   - Port: 6379
   - Configuration: `/etc/redis/redis.conf`

---

## Implementation Phases

### Sprint 1: Core Observability (2 weeks)

**Goal:** Establish structured logging and basic Prometheus metrics.

**Tasks:**

1. **Structured Logging** (3 days)
   - Install `python-json-logger`
   - Create `logging_config.py` utility
   - Update app factory to use structured logging
   - Update all services to use structured logging with context
   - Configure log rotation with logrotate

2. **Prometheus Metrics** (4 days)
   - Install `prometheus-client`
   - Create `metrics.py` utility
   - Implement core business metrics (stories created/completed/failed)
   - Implement application metrics (HTTP requests, queue depth)
   - Create `/metrics` API endpoint
   - Deploy Prometheus on Debian VM

3. **Health Checks** (3 days)
   - Create `health_checks.py` utility
   - Implement liveness/readiness/full health endpoints
   - Update existing `/api/health` endpoint
   - Configure NGINX health check integration

4. **Documentation & Testing** (2 days)
   - Document logging standards
   - Create Prometheus query examples
   - Write integration tests for metrics
   - Update deployment documentation

**Deliverables:**
- Structured JSON logs in `/var/log/ephergent/`
- Prometheus metrics exposed on `/metrics`
- Health check endpoints operational
- Updated `deploy_on_debian.sh` script

---

### Sprint 2: Error Handling & Retry Logic (2 weeks)

**Goal:** Implement automatic retry logic with exponential backoff and dead letter queue.

**Tasks:**

1. **Database Schema** (2 days)
   - Create `StoryRetry` model
   - Create migration script
   - Run migration on production
   - Add indexes for retry queries

2. **Retry Service** (3 days)
   - Create `retry_service.py`
   - Implement error classification
   - Implement retry decision logic
   - Implement exponential backoff calculation

3. **Workflow Integration** (3 days)
   - Update `StoryWorkflowService` to use retry logic
   - Add retry tracking to each workflow step
   - Implement DLQ movement logic
   - Add retry metrics to Prometheus

4. **Admin Tools** (3 days)
   - Create DLQ admin UI/API
   - Implement manual re-queue functionality
   - Add DLQ monitoring dashboard
   - Create alerting rules for DLQ growth

5. **Testing & Documentation** (1 day)
   - Write unit tests for retry logic
   - Test DLQ workflow
   - Document retry behavior
   - Update operations runbook

**Deliverables:**
- Automatic retry system operational
- DLQ management tools available
- Retry metrics in Grafana
- Operations documentation

---

### Sprint 3: Database Optimization & Alerting (2 weeks)

**Goal:** Optimize database performance and configure Prometheus alerting.

**Tasks:**

1. **Connection Pooling** (2 days)
   - Update `config.py` with pooling settings
   - Test connection pool under load
   - Monitor pool utilization
   - Document tuning parameters

2. **Story Archiving** (3 days)
   - Create `ArchivedStory` model
   - Update `archive_service.py`
   - Create automated archiving job
   - Test archive/restore workflow

3. **Query Optimization** (2 days)
   - Add database indexes for common queries
   - Analyze slow query log
   - Optimize N+1 query issues
   - Add query performance metrics

4. **Grafana Dashboards** (3 days)
   - Create main system dashboard
   - Create workflow performance dashboard
   - Create error tracking dashboard
   - Create queue health dashboard

5. **Prometheus Alerting** (2 days)
   - Configure AlertManager
   - Create alert rules (DLQ growth, worker down, high error rate)
   - Set up notification channels (email, Slack)
   - Test alerting workflow

6. **Documentation** (1 day)
   - Document database tuning
   - Create alert runbook
   - Update monitoring guide

**Deliverables:**
- Database connection pooling optimized
- Story archiving automated
- Grafana dashboards operational
- Alerting rules configured

---

## Deployment Strategy

### Deployment Script Updates

**Update `deploy_on_debian.sh`:**

```bash
#!/bin/bash
# ... existing script header ...

# Phase 1: Install observability dependencies
install_observability_tools() {
    echo "=== Installing Observability Tools ==="

    # Install Prometheus
    apt-get install -y prometheus prometheus-node-exporter

    # Install Grafana
    wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
    add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
    apt-get update
    apt-get install -y grafana

    # Install Redis (optional)
    apt-get install -y redis-server

    # Install logrotate
    apt-get install -y logrotate

    echo "Observability tools installed"
}

# Configure Prometheus
configure_prometheus() {
    echo "=== Configuring Prometheus ==="

    cat > /etc/prometheus/prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ephergent-web'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']  # Future: postgres_exporter
EOF

    # Restart Prometheus
    systemctl restart prometheus
    systemctl enable prometheus

    echo "Prometheus configured"
}

# Configure Grafana
configure_grafana() {
    echo "=== Configuring Grafana ==="

    # Start Grafana
    systemctl start grafana-server
    systemctl enable grafana-server

    # Wait for Grafana to start
    sleep 5

    # Add Prometheus data source (via API)
    curl -X POST http://admin:admin@localhost:3000/api/datasources \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://localhost:9090",
            "access": "proxy",
            "isDefault": true
        }'

    echo "Grafana configured - access at http://10.0.0.99:3000"
    echo "Default credentials: admin/admin"
}

# Configure log rotation
configure_logrotate() {
    echo "=== Configuring Log Rotation ==="

    cat > /etc/logrotate.d/ephergent <<'EOF'
/var/log/ephergent/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload ephergent-web
        systemctl reload ephergent-worker
    endscript
}
EOF

    echo "Log rotation configured"
}

# Main deployment
main() {
    # ... existing deployment steps ...

    # Phase 1: Observability
    install_observability_tools
    configure_prometheus
    configure_grafana
    configure_logrotate

    # ... rest of deployment ...
}

main "$@"
```

### NGINX Configuration Update

**Add metrics endpoint to NGINX config:**

```nginx
# /etc/nginx/sites-available/ephergent

server {
    listen 80;
    server_name 10.0.0.99;

    # ... existing config ...

    # Prometheus metrics (internal access only)
    location /metrics {
        allow 10.0.0.0/24;  # Allow from local network
        deny all;

        proxy_pass http://127.0.0.1:5000/metrics;
        proxy_set_header Host $host;
    }

    # Health checks
    location /health/liveness {
        proxy_pass http://127.0.0.1:5000/health/liveness;
        access_log off;  # Don't log health checks
    }

    location /health/readiness {
        proxy_pass http://127.0.0.1:5000/health/readiness;
        access_log off;
    }
}
```

### Systemd Service Updates

**Add health check to systemd services:**

```ini
# /etc/systemd/system/ephergent-web.service

[Unit]
Description=Ephergent Story Generator Web Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/ephergent
Environment="PATH=/opt/ephergent/.venv/bin"
ExecStart=/opt/ephergent/.venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/ephergent/access.log \
    --error-logfile /var/log/ephergent/error.log \
    wsgi:app

# Health check (systemd will restart if health check fails)
ExecStartPost=/bin/bash -c 'sleep 5 && curl -f http://localhost:5000/health/liveness || exit 1'

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Success Metrics

### Key Performance Indicators (KPIs)

**Reliability Metrics:**

1. **Story Success Rate**
   - Target: >95% stories complete successfully
   - Measurement: `(stories_completed_total / stories_created_total) * 100`
   - Alert: Success rate drops below 90%

2. **Mean Time to Recovery (MTTR)**
   - Target: <15 minutes for worker failures
   - Measurement: Time from alert to service recovery
   - Alert: MTTR exceeds 30 minutes

3. **System Uptime**
   - Target: 99.5% uptime (43.8 hours downtime/year)
   - Measurement: Prometheus `up` metric
   - Alert: Service down for >5 minutes

**Performance Metrics:**

1. **Story Generation Latency**
   - Target: P95 <5 minutes per workflow step
   - Measurement: `workflow_step_duration_seconds{quantile="0.95"}`
   - Alert: P95 latency exceeds 10 minutes

2. **Queue Processing Rate**
   - Target: >50 stories/hour (during peak)
   - Measurement: `rate(stories_completed_total[1h])`
   - Alert: Processing rate drops below 20 stories/hour

3. **Database Query Latency**
   - Target: P95 <100ms
   - Measurement: `db_query_duration_seconds{quantile="0.95"}`
   - Alert: P95 latency exceeds 500ms

**Error Metrics:**

1. **Dead Letter Queue Size**
   - Target: <10 stories in DLQ
   - Measurement: `dlq_stories_total`
   - Alert: DLQ size exceeds 25 stories

2. **Retry Rate**
   - Target: <10% of stories require retry
   - Measurement: `(story_retries_total / stories_created_total) * 100`
   - Alert: Retry rate exceeds 25%

3. **External Service Error Rate**
   - Target: <5% error rate for external APIs
   - Measurement: `rate(external_api_requests_total{status="error"}[5m])`
   - Alert: Error rate exceeds 10%

### Prometheus Alert Rules

**Create `/etc/prometheus/rules/ephergent_alerts.yml`:**

```yaml
groups:
  - name: ephergent_alerts
    interval: 30s
    rules:
      # Story processing alerts
      - alert: HighStoryFailureRate
        expr: (rate(ephergent_stories_failed_total[5m]) / rate(ephergent_stories_created_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High story failure rate"
          description: "{{ $value | humanizePercentage }} of stories are failing"

      - alert: DLQSizeHigh
        expr: ephergent_dlq_stories_total > 25
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Dead letter queue is growing"
          description: "{{ $value }} stories in DLQ require manual intervention"

      # Worker alerts
      - alert: NoActiveWorkers
        expr: ephergent_active_workers == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "No background workers active"
          description: "Story processing has stopped - no workers detected"

      # Queue alerts
      - alert: QueueBacklogGrowing
        expr: increase(ephergent_queue_depth[10m]) > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Queue backlog growing rapidly"
          description: "Queue depth increased by {{ $value }} stories in 10 minutes"

      # External service alerts
      - alert: HighExternalAPIErrorRate
        expr: (rate(ephergent_external_api_requests_total{status="error"}[5m]) / rate(ephergent_external_api_requests_total[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate for {{ $labels.service }}"
          description: "{{ $value | humanizePercentage }} of {{ $labels.service }} API calls failing"

      # Database alerts
      - alert: HighDatabaseLatency
        expr: histogram_quantile(0.95, rate(ephergent_db_query_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database query latency"
          description: "P95 database query latency is {{ $value }}s"

      - alert: DatabaseConnectionPoolExhausted
        expr: ephergent_db_connections_active >= 30  # Assuming pool_size + max_overflow = 30
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value }} active connections (approaching limit)"
```

---

## Migration Strategy

### Zero-Downtime Migration Plan

**Objective:** Deploy Phase 1 changes without interrupting story processing.

**Steps:**

1. **Pre-Deployment Preparation** (1 hour)
   ```bash
   # Backup database
   pg_dump ephergent_production > backup_$(date +%Y%m%d).sql

   # Stop worker (graceful)
   systemctl stop ephergent-worker

   # Wait for in-flight stories to complete (check queue status)
   curl http://localhost:5000/api/health
   ```

2. **Deploy Code Changes** (30 minutes)
   ```bash
   # Pull latest code
   cd /opt/ephergent
   git pull origin main

   # Install new dependencies
   .venv/bin/pip install -e .

   # Run database migrations
   flask db upgrade
   ```

3. **Deploy Observability Stack** (1 hour)
   ```bash
   # Install and configure Prometheus
   ./deploy_on_debian.sh --only-observability

   # Verify Prometheus is scraping metrics
   curl http://localhost:9090/api/v1/targets
   ```

4. **Rolling Restart** (15 minutes)
   ```bash
   # Restart web service (one worker at a time if using multiple Gunicorn workers)
   systemctl reload ephergent-web

   # Verify health checks pass
   curl http://localhost:5000/health/readiness

   # Restart worker
   systemctl start ephergent-worker
   ```

5. **Post-Deployment Validation** (30 minutes)
   ```bash
   # Check logs for errors
   journalctl -u ephergent-web -n 100
   journalctl -u ephergent-worker -n 100

   # Verify metrics endpoint
   curl http://localhost:5000/metrics

   # Check Grafana dashboards
   # Browser: http://10.0.0.99:3000

   # Submit test story
   curl -X POST http://localhost:5000/api/stories \
       -H "Content-Type: application/json" \
       -d '{"topic": "Test story for Phase 1 validation"}'
   ```

6. **Rollback Plan** (if needed)
   ```bash
   # Rollback database migration
   flask db downgrade

   # Restore previous code version
   git checkout <previous-commit>

   # Restart services
   systemctl restart ephergent-web ephergent-worker
   ```

### Data Migration Considerations

**Existing Stories:**

- No data migration needed for existing `stories` table
- New `story_retries` table starts empty
- New `archived_stories` table starts empty
- Archiving only applies to new completions (not retroactive)

**Backwards Compatibility:**

- All new columns have defaults or are nullable
- Existing code continues to work without retry logic
- Metrics endpoint is additive (doesn't break existing endpoints)

---

## Testing Approach

### Unit Tests

**Test Coverage Areas:**

1. **Logging Configuration**
   ```python
   # tests/test_logging.py

   def test_structured_logging_format():
       """Test that logs are properly formatted as JSON."""
       # Setup test logger
       # Log a message
       # Assert JSON format
       pass

   def test_request_context_in_logs():
       """Test that Flask request context is included in logs."""
       # Make test request
       # Assert request_id in log
       pass
   ```

2. **Metrics Collection**
   ```python
   # tests/test_metrics.py

   def test_story_creation_increments_counter():
       """Test that creating a story increments the counter."""
       # Create story
       # Assert counter incremented
       pass

   def test_workflow_step_duration_recorded():
       """Test that workflow step duration is recorded."""
       # Process workflow step
       # Assert histogram updated
       pass
   ```

3. **Retry Logic**
   ```python
   # tests/test_retry_service.py

   def test_transient_error_triggers_retry():
       """Test that transient errors trigger retry."""
       # Simulate network timeout
       # Assert retry record created
       # Assert retry_status is 'retrying'
       pass

   def test_permanent_error_moves_to_dlq():
       """Test that permanent errors move to DLQ."""
       # Simulate validation error
       # Assert moved to DLQ
       pass

   def test_max_retries_moves_to_dlq():
       """Test that exceeding max retries moves to DLQ."""
       # Fail 3 times
       # Assert moved to DLQ
       pass
   ```

4. **Health Checks**
   ```python
   # tests/test_health_checks.py

   def test_liveness_check_always_succeeds():
       """Test that liveness check returns 200."""
       # Call liveness endpoint
       # Assert 200 status
       pass

   def test_readiness_fails_with_db_down():
       """Test that readiness fails when database is down."""
       # Mock database failure
       # Call readiness endpoint
       # Assert 503 status
       pass
   ```

### Integration Tests

**Test Scenarios:**

1. **End-to-End Story Processing with Retry**
   ```python
   # tests/integration/test_story_workflow_with_retry.py

   def test_story_retries_on_transient_failure():
       """Test that a story is retried after transient failure."""
       # Create story
       # Mock Gemini API to fail once, then succeed
       # Assert story eventually completes
       # Assert retry record shows 1 retry
       pass
   ```

2. **Metrics Export**
   ```python
   # tests/integration/test_metrics_export.py

   def test_metrics_endpoint_returns_prometheus_format():
       """Test that /metrics endpoint returns Prometheus format."""
       # Call /metrics endpoint
       # Assert Content-Type is text/plain
       # Assert metrics in Prometheus format
       pass
   ```

3. **Health Check Integration**
   ```python
   # tests/integration/test_health_check_integration.py

   def test_health_check_with_real_database():
       """Test health check with real database connection."""
       # Call /health/full endpoint
       # Assert all checks pass
       # Assert database check is healthy
       pass
   ```

### Load Testing

**Test Configuration:**

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between

class EphergentLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def create_story(self):
        """Simulate story creation."""
        self.client.post("/api/stories", json={
            "topic": "Load test story",
            "genre": "sci-fi"
        })

    @task(1)
    def check_health(self):
        """Simulate health check."""
        self.client.get("/health/readiness")

    @task(1)
    def view_metrics(self):
        """Simulate metrics scraping."""
        self.client.get("/metrics")
```

**Run Load Test:**

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host http://localhost:5000

# Access Locust web UI at http://localhost:8089
# Configure: 100 users, spawn rate 10/sec, duration 5 minutes
```

### Performance Regression Tests

**Benchmark Targets:**

1. **Story Creation Latency:** <100ms (database write)
2. **Metrics Endpoint Response:** <50ms
3. **Health Check Latency:** <200ms (includes DB ping)
4. **Workflow Step Processing:** <5 minutes (per step)

**Automated Performance Tests:**

```bash
# Add to CI/CD pipeline
pytest tests/performance/ --benchmark-only
```

---

## Grafana Dashboards

### Dashboard 1: System Overview

**Panels:**

1. **Story Processing Rate** (Graph)
   - Query: `rate(ephergent_stories_created_total[5m])`
   - Description: Stories created per second

2. **Story Success Rate** (Gauge)
   - Query: `(sum(rate(ephergent_stories_completed_total[5m])) / sum(rate(ephergent_stories_created_total[5m]))) * 100`
   - Description: Percentage of stories completing successfully

3. **Queue Depth** (Graph)
   - Query: `ephergent_queue_depth`
   - Description: Number of stories waiting in queue

4. **Active Workers** (Stat)
   - Query: `ephergent_active_workers`
   - Description: Number of workers processing stories

5. **Dead Letter Queue Size** (Stat with alert)
   - Query: `ephergent_dlq_stories_total`
   - Description: Stories requiring manual intervention

### Dashboard 2: Workflow Performance

**Panels:**

1. **Workflow Step Duration (P95)** (Graph)
   - Query: `histogram_quantile(0.95, rate(ephergent_workflow_step_duration_seconds_bucket[5m]))`
   - Description: 95th percentile duration by workflow step

2. **Workflow Step Success Rate** (Heatmap)
   - Query: `rate(ephergent_workflow_step_duration_seconds_count{status="success"}[5m]) / rate(ephergent_workflow_step_duration_seconds_count[5m])`
   - Description: Success rate by workflow step over time

3. **Retry Rate by Step** (Bar chart)
   - Query: `sum by (workflow_step) (ephergent_story_retries_total)`
   - Description: Total retries per workflow step

### Dashboard 3: Error Tracking

**Panels:**

1. **Error Rate** (Graph)
   - Query: `rate(ephergent_stories_failed_total[5m])`
   - Description: Stories failing per second

2. **Error Breakdown by Type** (Pie chart)
   - Query: `sum by (error_type) (ephergent_stories_failed_total)`
   - Description: Distribution of error types

3. **External API Error Rate** (Graph)
   - Query: `rate(ephergent_external_api_requests_total{status="error"}[5m])`
   - Description: External API failures by service

4. **Recent DLQ Entries** (Table)
   - Query: Join with database to show recent DLQ stories
   - Description: Stories requiring manual intervention

---

## Appendix: Configuration Reference

### Environment Variables

```bash
# Phase 1 Configuration

# Logging
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/ephergent/app.log    # Path to JSON log file
LOG_FORMAT=json                         # json or text

# Database Connection Pooling
DB_POOL_SIZE=10                         # Number of persistent connections
DB_MAX_OVERFLOW=20                      # Additional connections under load
DB_ECHO_POOL=false                      # Log connection pool events

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0      # Redis connection string

# Metrics
METRICS_ENABLED=true                    # Enable Prometheus metrics
METRICS_PATH=/metrics                   # Metrics endpoint path

# Health Checks
HEALTH_CHECK_TIMEOUT=5                  # Timeout for dependency health checks (seconds)

# Retry Configuration
RETRY_MAX_ATTEMPTS=3                    # Max retries per workflow step
RETRY_BASE_DELAY=1                      # Base delay for exponential backoff (seconds)
RETRY_MAX_DELAY=60                      # Max delay between retries (seconds)

# Archiving
ARCHIVE_AFTER_DAYS=90                   # Archive stories older than N days
ARCHIVE_BATCH_SIZE=100                  # Stories to archive per batch
```

### Prometheus Scrape Configuration

```yaml
# /etc/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ephergent-production'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Load rules
rule_files:
  - '/etc/prometheus/rules/*.yml'

# Scrape configurations
scrape_configs:
  # Ephergent Web Application
  - job_name: 'ephergent-web'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  # PostgreSQL metrics (future)
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

---

## Next Steps

After Phase 1 completion, the system will have:

1. Comprehensive observability with structured logs and Prometheus metrics
2. Automatic error recovery with retry logic and dead letter queue
3. Optimized database performance with connection pooling and archiving
4. Grafana dashboards for monitoring and troubleshooting
5. Alerting for critical system issues

**Phase 2 Preview:** Advanced Features

- Distributed tracing with OpenTelemetry
- Automated performance testing in CI/CD
- Advanced caching strategies with Redis
- Multi-region deployment support
- A/B testing framework for story generation

---

**Document End**

**Revision History:**

- v1.0 (2025-10-08): Initial architecture design
