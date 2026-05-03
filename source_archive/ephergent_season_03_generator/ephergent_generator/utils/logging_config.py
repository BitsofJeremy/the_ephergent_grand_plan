"""Structured logging configuration for Ephergent Story Generator.

This module provides structured JSON logging with Flask request context integration.
Logs are formatted for easy parsing by log aggregation systems and include
contextual information like request IDs, user sessions, and story metadata.

Usage:
    from ephergent_generator.utils.logging_config import setup_logging

    app = create_app()
    app = setup_logging(app)

Environment Variables:
    LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FILE: Path to log file (default: ephergent.log)
    LOG_FORMAT: Log format (json or text, default: json for production)
"""

import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None
    print("WARNING: python-json-logger not installed. Install with: pip install python-json-logger")

from flask import g, request, has_request_context


class ContextualJsonFormatter(jsonlogger.JsonFormatter if jsonlogger else logging.Formatter):
    """Custom JSON formatter that includes Flask request context.

    Adds contextual fields to log records:
    - timestamp: ISO 8601 formatted timestamp
    - request_id: Unique request identifier (from header or auto-generated)
    - method: HTTP method (GET, POST, etc.)
    - path: Request path
    - remote_addr: Client IP address
    - environment: Application environment (development, production)
    """

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        if jsonlogger:
            super().add_fields(log_record, record, message_dict)
        else:
            # Fallback for when pythonjsonlogger is not available
            log_record.update(message_dict)

        # Add timestamp in ISO 8601 format
        log_record['timestamp'] = datetime.utcfromtimestamp(record.created).isoformat() + 'Z'

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add Flask request context if available
        if has_request_context():
            try:
                # Get or create request ID
                if not hasattr(g, 'request_id'):
                    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

                log_record['request_id'] = g.request_id
                log_record['method'] = request.method
                log_record['path'] = request.path
                log_record['remote_addr'] = request.remote_addr

                # Add user session ID if available
                if hasattr(g, 'session_id'):
                    log_record['session_id'] = g.session_id

            except RuntimeError:
                # Handle edge cases where request context is partially available
                pass

        # Add environment from app config if available
        try:
            from flask import current_app
            log_record['environment'] = current_app.config.get('ENV', 'unknown')
        except (RuntimeError, AttributeError):
            # Outside app context or app not initialized
            pass


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development environments."""

    def format(self, record):
        """Format log record with colors and structure."""
        # Color codes for different log levels
        colors = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[35m',   # Magenta
        }
        reset = '\033[0m'

        # Add color to level name
        level_color = colors.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{reset}"

        # Format the message
        formatted = super().format(record)

        # Add extra context if available
        if hasattr(record, 'story_id'):
            formatted += f" [story_id={record.story_id}]"
        if hasattr(record, 'workflow_step'):
            formatted += f" [step={record.workflow_step}]"
        if hasattr(record, 'duration_ms'):
            formatted += f" [duration={record.duration_ms:.0f}ms]"

        return formatted


def setup_logging(app):
    """Configure structured logging for the Flask application.

    Args:
        app: Flask application instance

    Returns:
        Flask application with logging configured

    Example:
        app = create_app()
        app = setup_logging(app)
    """

    # Get configuration
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_file = app.config.get('LOG_FILE', 'ephergent.log')
    log_format = app.config.get('LOG_FORMAT', 'json')
    environment = app.config.get('ENV', 'development')

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Set log level
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Create file handler (always JSON for machine parsing)
    file_handler = logging.FileHandler(log_file)
    if jsonlogger:
        json_formatter = ContextualJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)
    else:
        # Fallback to standard formatter
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    file_handler.setLevel(logging.INFO)

    # Create console handler (human-readable in dev, JSON in prod)
    console_handler = logging.StreamHandler(sys.stdout)
    if environment == 'production' or log_format == 'json':
        if jsonlogger:
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
    else:
        # Human-readable format for development
        human_formatter = HumanReadableFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(human_formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure Flask app logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # Add request ID middleware
    @app.before_request
    def assign_request_id():
        """Assign a unique request ID to each request."""
        if not hasattr(g, 'request_id'):
            g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    # Add request/response logging middleware
    @app.after_request
    def log_request(response):
        """Log each request with timing information."""
        if request.path != '/health/liveness':  # Don't log health checks
            duration_ms = 0
            if hasattr(g, 'request_start_time'):
                import time
                duration_ms = (time.time() - g.request_start_time) * 1000

            app.logger.info(
                f"{request.method} {request.path} {response.status_code}",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'request_id': getattr(g, 'request_id', None)
                }
            )

        return response

    @app.before_request
    def start_timer():
        """Start request timer for duration tracking."""
        import time
        g.request_start_time = time.time()

    app.logger.info(
        f"Logging configured - level={log_level}, format={log_format}, env={environment}",
        extra={'log_file': str(log_file)}
    )

    return app


def get_logger(name):
    """Get a logger with the specified name.

    This is a convenience wrapper around logging.getLogger() that ensures
    consistent logger configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing story", extra={'story_id': 42})
    """
    return logging.getLogger(name)


# Example usage for testing
if __name__ == '__main__':
    # Create a minimal Flask app for testing
    from flask import Flask

    app = Flask(__name__)
    app.config['LOG_LEVEL'] = 'DEBUG'
    app.config['LOG_FILE'] = 'test_logging.log'
    app.config['LOG_FORMAT'] = 'json'

    app = setup_logging(app)

    # Test logging
    logger = get_logger(__name__)
    logger.debug("Debug message")
    logger.info("Info message", extra={'story_id': 42, 'workflow_step': 'story_generation'})
    logger.warning("Warning message", extra={'error_count': 3})
    logger.error("Error message", extra={'error_type': 'TimeoutError'})

    print("\nTest logs written to test_logging.log")
