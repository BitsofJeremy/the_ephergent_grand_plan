"""Error classification system for Phase 1.2 retry logic.

Classifies exceptions into categories to determine retry strategy:
- TRANSIENT: Temporary issues (network, API timeouts) - auto-retry
- RATE_LIMIT: API rate limiting - retry with longer backoff
- CONFIGURATION: Missing/invalid config (API keys) - no retry, needs fix
- VALIDATION: Invalid data/missing fields - no retry, needs correction
- RESOURCE: System resources (disk, memory) - retry once
- PERMANENT: Unrecoverable errors - no retry, manual review
"""

import logging
import re
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Error classification categories for retry logic."""
    TRANSIENT = 'TRANSIENT'
    RATE_LIMIT = 'RATE_LIMIT'
    CONFIGURATION = 'CONFIGURATION'
    VALIDATION = 'VALIDATION'
    RESOURCE = 'RESOURCE'
    PERMANENT = 'PERMANENT'


class ErrorClassifier:
    """Classifies exceptions to determine appropriate retry strategy."""

    # Transient error patterns (network, temporary API issues)
    TRANSIENT_PATTERNS = [
        r'connection.*(?:refused|reset|timeout|timed out)',
        r'temporary failure',
        r'service unavailable',
        r'502 bad gateway',
        r'503 service unavailable',
        r'504 gateway timeout',
        r'network.*unreachable',
        r'socket.*timeout',
        r'read timeout',
        r'connect timeout',
        r'deadline exceeded',
        r'temporarily unavailable',
    ]

    # Rate limit patterns
    RATE_LIMIT_PATTERNS = [
        r'rate limit',
        r'too many requests',
        r'429',
        r'quota.*exceeded',
        r'throttl',
        r'resource.*exhausted',
    ]

    # Configuration error patterns
    CONFIGURATION_PATTERNS = [
        r'api.*key.*(?:invalid|missing|not found)',
        r'authentication.*failed',
        r'unauthorized',
        r'401',
        r'403.*forbidden',
        r'credentials.*(?:invalid|missing)',
        r'permission denied',
        r'access.*denied',
    ]

    # Validation error patterns
    VALIDATION_PATTERNS = [
        r'validation.*(?:error|failed)',
        r'invalid.*(?:input|data|parameter)',
        r'required.*(?:field|parameter).*missing',
        r'400 bad request',
        r'malformed',
        r'schema.*violation',
    ]

    # Resource error patterns
    RESOURCE_PATTERNS = [
        r'out of memory',
        r'disk.*full',
        r'no space left',
        r'resource.*(?:unavailable|exhausted)',
        r'insufficient.*(?:memory|disk)',
    ]

    @classmethod
    def classify_error(cls, exception: Exception, error_message: str = None) -> Tuple[ErrorType, str]:
        """Classify an exception into an error type.

        Args:
            exception: The exception to classify
            error_message: Optional custom error message (uses str(exception) if None)

        Returns:
            Tuple of (ErrorType, user-friendly explanation)
        """
        # Use provided message or convert exception to string
        msg = (error_message or str(exception)).lower()
        exc_type = type(exception).__name__

        logger.debug(f"Classifying error: {exc_type} - {msg[:100]}")

        # Check patterns in order of specificity
        
        # 1. Rate limiting (most specific, check first)
        if cls._matches_patterns(msg, cls.RATE_LIMIT_PATTERNS):
            return ErrorType.RATE_LIMIT, "API rate limit exceeded - will retry with longer delay"

        # 2. Configuration errors (auth, API keys)
        if cls._matches_patterns(msg, cls.CONFIGURATION_PATTERNS):
            return ErrorType.CONFIGURATION, "Configuration error - check API keys and settings"

        # 3. Validation errors (bad data)
        if cls._matches_patterns(msg, cls.VALIDATION_PATTERNS):
            return ErrorType.VALIDATION, "Invalid data or missing required fields"

        # 4. Resource errors (disk, memory)
        if cls._matches_patterns(msg, cls.RESOURCE_PATTERNS):
            return ErrorType.RESOURCE, "System resource issue (disk space or memory)"

        # 5. Transient errors (network, timeouts)
        if cls._matches_patterns(msg, cls.TRANSIENT_PATTERNS):
            return ErrorType.TRANSIENT, "Temporary network or API issue - safe to retry"

        # 6. Check common exception types
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return ErrorType.TRANSIENT, "Connection or timeout error - safe to retry"

        if exc_type in ('HTTPError', 'RequestException', 'URLError'):
            # Further classify HTTP errors by status code if available
            if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
                status = exception.response.status_code
                if status == 429:
                    return ErrorType.RATE_LIMIT, "API rate limit (HTTP 429)"
                elif status in (500, 502, 503, 504):
                    return ErrorType.TRANSIENT, f"Server error (HTTP {status}) - temporary issue"
                elif status in (401, 403):
                    return ErrorType.CONFIGURATION, f"Authentication error (HTTP {status})"
                elif status == 400:
                    return ErrorType.VALIDATION, "Invalid request (HTTP 400)"

        # Default to PERMANENT for unknown errors (requires manual review)
        logger.warning(f"Unclassified error type: {exc_type} - defaulting to PERMANENT")
        return ErrorType.PERMANENT, "Unrecoverable error - manual review required"

    @staticmethod
    def _matches_patterns(text: str, patterns: list) -> bool:
        """Check if text matches any pattern in the list."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def should_retry(cls, error_type: ErrorType) -> bool:
        """Determine if an error type should be automatically retried.

        Args:
            error_type: The classified error type

        Returns:
            True if automatic retry is appropriate
        """
        return error_type in (ErrorType.TRANSIENT, ErrorType.RATE_LIMIT, ErrorType.RESOURCE)

    @classmethod
    def get_retry_delay_multiplier(cls, error_type: ErrorType) -> float:
        """Get backoff multiplier for error type.

        Args:
            error_type: The classified error type

        Returns:
            Multiplier for exponential backoff (1.0 = normal, 2.0 = double delay)
        """
        if error_type == ErrorType.RATE_LIMIT:
            return 3.0  # Triple the normal delay for rate limits
        elif error_type == ErrorType.RESOURCE:
            return 2.0  # Double delay for resource issues
        else:
            return 1.0  # Normal delay for transient errors


# Singleton instance for easy access
error_classifier = ErrorClassifier()
