from datetime import datetime, timedelta
from enum import Enum
from ephergent_generator import db
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class WorkflowStep(Enum):
    """Represents different steps in the story generation workflow.

    Provides an enumeration of sequential stages for content generation
    and publication process.

    Attributes:
        QUEUED: Initial state when story is first entered into system.
        STORY_GENERATION: AI generates primary story content.
        TITLE_GENERATION: Creating a suitable title for the story.
        IMAGE_GENERATION: Producing visual elements.
        AUDIO_GENERATION: Generating audio components.
        VIDEO_GENERATION: Composing video content.
        YOUTUBE_UPLOAD: Uploading to YouTube platform.
        GHOST_PUBLISHING: Publishing on Ghost blog.
        COMPLETED: Workflow successfully finished.
        FAILED: Workflow encountered unrecoverable error.
    """
    QUEUED = "queued"
    STORY_GENERATION = "story_generation"
    TITLE_GENERATION = "title_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_GENERATION = "video_generation"
    YOUTUBE_UPLOAD = "youtube_upload"
    GHOST_PUBLISHING = "ghost_publishing"
    COMPLETED = "completed"
    FAILED = "failed"

class Story(db.Model):
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Input/Topic
    topic = db.Column(db.Text, nullable=False)  # The original topic/idea
    prompt = db.Column(db.Text, nullable=True)  # Generated detailed prompt (optional)
    
    # Generated Content
    title = db.Column(db.String(200), nullable=True)  # Generated title
    content = db.Column(db.Text, nullable=True)  # Generated story content
    
    # Metadata
    genre = db.Column(db.String(50), nullable=True)
    tone = db.Column(db.String(50), nullable=True)
    word_count = db.Column(db.Integer, nullable=True)
    narrator_character_id = db.Column(db.String(100), nullable=True)  # Character who narrates the story
    dimension_location = db.Column(db.String(100), nullable=True)  # Ephergent Universe dimension
    
    # Workflow Management
    current_step = db.Column(db.Enum(WorkflowStep), default=WorkflowStep.QUEUED, nullable=False)
    workflow_data = db.Column(db.Text, nullable=True)  # JSON data for workflow state
    error_message = db.Column(db.Text, nullable=True)  # Error details if step fails

    # Phase 1.2: Retry and Error Handling
    retry_count = db.Column(db.Integer, default=0, nullable=False)  # Number of retry attempts
    max_retries = db.Column(db.Integer, default=5, nullable=False)  # Maximum retry attempts (configurable)
    last_retry_at = db.Column(db.DateTime, nullable=True)  # When last retry occurred
    next_retry_at = db.Column(db.DateTime, nullable=True)  # When next retry should occur (exponential backoff)
    error_type = db.Column(db.String(50), nullable=True)  # Error classification (TRANSIENT, RATE_LIMIT, etc.)
    failed_at_step = db.Column(db.Enum(WorkflowStep), nullable=True)  # Which workflow step failed

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Session tracking
    session_id = db.Column(db.String(100), nullable=True)
    
    # Media files (paths or URLs)
    image_paths = db.Column(db.Text, nullable=True)  # JSON array of image paths/URLs
    image_prompts = db.Column(db.Text, nullable=True)  # JSON object of image generation prompts
    audio_path = db.Column(db.String(500), nullable=True)  # Audio file path/URL
    video_path = db.Column(db.String(500), nullable=True)  # Video file path/URL
    youtube_video_id = db.Column(db.String(100), nullable=True)  # YouTube video ID
    youtube_url = db.Column(db.String(200), nullable=True)  # Full YouTube URL
    
    # Ghost blog integration
    ghost_post_id = db.Column(db.String(100), nullable=True)  # Ghost post ID
    ghost_post_url = db.Column(db.String(500), nullable=True)  # Published Ghost blog post URL
    ghost_status = db.Column(db.String(20), default='draft', nullable=True)  # Ghost post status (draft/published)
    
    def __repr__(self):
        return f'<Story {self.id}: {self.topic[:50]}...>'
    
    def get_workflow_data(self):
        """Parse workflow_data JSON field."""
        if self.workflow_data:
            try:
                return json.loads(self.workflow_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_workflow_data(self, data):
        """Set workflow_data as JSON."""
        self.workflow_data = json.dumps(data) if data else None
    
    def get_image_paths(self):
        """Parse image_paths JSON field."""
        if self.image_paths:
            try:
                return json.loads(self.image_paths)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_image_paths(self, paths):
        """Set image_paths as JSON array."""
        self.image_paths = json.dumps(paths) if paths else None
    
    def get_image_prompts(self):
        """Parse image_prompts JSON field."""
        if self.image_prompts:
            try:
                return json.loads(self.image_prompts)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_image_prompts(self, prompts):
        """Set image_prompts as JSON object."""
        self.image_prompts = json.dumps(prompts) if prompts else None
    
    def advance_workflow(self, next_step, data=None, error=None):
        """Advance to next workflow step."""
        self.current_step = next_step
        self.updated_at = datetime.utcnow()
        
        if data:
            current_data = self.get_workflow_data()
            current_data.update(data)
            self.set_workflow_data(current_data)
        
        if error:
            self.error_message = error
            self.current_step = WorkflowStep.FAILED
        
        if next_step == WorkflowStep.COMPLETED:
            self.completed_at = datetime.utcnow()
    
    def reset_for_regeneration(self):
        """Reset story to initial state for regeneration."""
        # Reset workflow state
        self.current_step = WorkflowStep.QUEUED
        self.error_message = None
        self.workflow_data = None
        self.updated_at = datetime.utcnow()
        self.completed_at = None

        # Reset retry state (Phase 1.2)
        self.retry_count = 0
        self.last_retry_at = None
        self.next_retry_at = None
        self.error_type = None
        self.failed_at_step = None

        # Clear generated content
        self.title = None
        self.content = None
        self.prompt = None

        # Clear media files
        self.image_paths = None
        self.image_prompts = None
        self.audio_path = None
        self.video_path = None

        # Clear external publishing data
        self.youtube_video_id = None
        self.youtube_url = None
        self.ghost_post_id = None
        self.ghost_post_url = None
        self.ghost_status = 'draft'
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'prompt': self.prompt,
            'title': self.title,
            'content': self.content,
            'genre': self.genre,
            'tone': self.tone,
            'word_count': self.word_count,
            'narrator_character_id': self.narrator_character_id,
            'dimension_location': self.dimension_location,
            'current_step': self.current_step.value if self.current_step else None,
            'workflow_data': self.get_workflow_data(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'session_id': self.session_id,
            'image_paths': self.get_image_paths(),
            'audio_path': self.audio_path
        }

class StoryQueue(db.Model):
    """Simple queue table for processing stories."""
    __tablename__ = 'story_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processing_started_at = db.Column(db.DateTime, nullable=True)
    worker_id = db.Column(db.String(100), nullable=True)  # ID of worker processing
    
    # Relationship
    story = db.relationship('Story', backref=db.backref('queue_entries', lazy=True))
    
    def __repr__(self):
        return f'<StoryQueue {self.id}: story_id={self.story_id}, priority={self.priority}>'


class User(UserMixin, db.Model):
    """User model for authentication and authorization.

    Provides secure user management with role-based access control.
    Currently supports admin users for managing the story generation system.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Role and status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Session management
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def update_login_info(self):
        """Update login tracking information."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.updated_at = datetime.utcnow()

    def is_authenticated(self):
        """Required by Flask-Login."""
        return True

    def is_anonymous(self):
        """Required by Flask-Login."""
        return False

    def get_id(self):
        """Required by Flask-Login."""
        return str(self.id)

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary for API responses."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'api_key_count': len(self.api_keys)
        }

        if include_sensitive:
            data['api_keys'] = [key.to_dict() for key in self.api_keys if key.is_active]

        return data


class APIKey(db.Model):
    """API Key model for programmatic access to the system.

    Provides secure API key management with expiration, rate limiting,
    and usage tracking capabilities.
    """
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Key identification
    name = db.Column(db.String(100), nullable=False)  # Human-readable name
    key_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = db.Column(db.String(10), nullable=False)  # First few chars for identification

    # Key status and permissions
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    permissions = db.Column(db.Text, nullable=True)  # JSON array of permissions

    # Expiration and usage
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)

    # Rate limiting (requests per hour)
    rate_limit = db.Column(db.Integer, default=1000, nullable=False)
    current_hour_usage = db.Column(db.Integer, default=0, nullable=False)
    hour_reset_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<APIKey {self.name} ({self.key_prefix}...)>'

    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        # Generate a 32-byte (256-bit) random key
        key = secrets.token_urlsafe(32)
        return f"ephg_{key}"

    @classmethod
    def create_key(cls, user_id, name, permissions=None, expires_days=None, rate_limit=1000):
        """Create a new API key for a user."""
        api_key = cls.generate_key()
        key_hash = generate_password_hash(api_key)

        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)

        api_key_obj = cls(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=api_key[:10],  # Store first 10 chars for identification
            permissions=json.dumps(permissions) if permissions else None,
            expires_at=expires_at,
            rate_limit=rate_limit
        )

        return api_key_obj, api_key  # Return both the object and the raw key

    def verify_key(self, provided_key):
        """Verify if the provided key matches this API key."""
        return check_password_hash(self.key_hash, provided_key)

    def is_expired(self):
        """Check if the API key has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def is_rate_limited(self):
        """Check if the API key has exceeded its rate limit."""
        now = datetime.utcnow()

        # Reset hourly counter if an hour has passed
        if now >= self.hour_reset_time + timedelta(hours=1):
            self.current_hour_usage = 0
            self.hour_reset_time = now.replace(minute=0, second=0, microsecond=0)

        return self.current_hour_usage >= self.rate_limit

    def record_usage(self):
        """Record usage of this API key."""
        now = datetime.utcnow()

        # Reset hourly counter if needed
        if now >= self.hour_reset_time + timedelta(hours=1):
            self.current_hour_usage = 0
            self.hour_reset_time = now.replace(minute=0, second=0, microsecond=0)

        self.usage_count += 1
        self.current_hour_usage += 1
        self.last_used = now
        self.updated_at = now

    def get_permissions(self):
        """Get permissions as a list."""
        if self.permissions:
            try:
                return json.loads(self.permissions)
            except json.JSONDecodeError:
                return []
        return []

    def set_permissions(self, permissions):
        """Set permissions as JSON."""
        self.permissions = json.dumps(permissions) if permissions else None

    def has_permission(self, permission):
        """Check if the API key has a specific permission."""
        perms = self.get_permissions()
        return permission in perms or 'admin' in perms

    def can_be_used(self):
        """Check if the API key can be used (active, not expired, not rate limited)."""
        return (
            self.is_active and
            not self.is_expired() and
            not self.is_rate_limited()
        )

    def deactivate(self):
        """Deactivate the API key."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def to_dict(self, include_sensitive=False):
        """Convert API key to dictionary for API responses."""
        data = {
            'id': self.id,
            'name': self.name,
            'key_prefix': self.key_prefix,
            'is_active': self.is_active,
            'permissions': self.get_permissions(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'rate_limit': self.rate_limit,
            'current_hour_usage': self.current_hour_usage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_sensitive:
            data['user_id'] = self.user_id

        return data


class Character(db.Model):
    """Character model for database-driven character configuration.

    Replaces the legacy JSON-based personality_prompts_s3.json and markdown files
    with a robust database-backed character management system. Each character represents
    a unique narrator/entity within the Ephergent Universe with customizable AI behavior,
    voice characteristics, and visual appearance.
    """
    __tablename__ = 'characters'

    # Primary identifiers
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)

    # AI Configuration
    personality_prompt = db.Column(db.Text, nullable=False)
    stable_diffusion_prompt = db.Column(db.Text, nullable=True)
    voice_model = db.Column(db.String(100), nullable=True)
    ai_model = db.Column(db.String(100), nullable=True, default='gemini-2.5-flash')

    # Content categorization (stored as JSON)
    topics = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)

    # Character status and ordering
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Profile image management
    profile_image_path = db.Column(db.String(500), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    image_last_generated = db.Column(db.DateTime, nullable=True)

    # Version tracking
    version = db.Column(db.Integer, default=1, nullable=False)

    # Audit fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_characters')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_characters')
    versions = db.relationship('CharacterVersion', backref='character', lazy='dynamic',
                               order_by='CharacterVersion.version.desc()',
                               cascade='all, delete-orphan')

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_character_active_order', 'is_active', 'sort_order'),
        db.Index('idx_character_default', 'is_default', 'is_active'),
    )

    def __repr__(self):
        return f'<Character {self.character_id}: {self.name}>'

    def get_topics(self):
        """Parse topics JSON field into a list."""
        if self.topics:
            try:
                return json.loads(self.topics)
            except json.JSONDecodeError:
                return []
        return []

    def set_topics(self, topics_list):
        """Set topics from a list, storing as JSON."""
        if topics_list is not None:
            self.topics = json.dumps(topics_list) if isinstance(topics_list, list) else None
        else:
            self.topics = None

    def get_tags(self):
        """Parse tags JSON field into a list."""
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []

    def set_tags(self, tags_list):
        """Set tags from a list, storing as JSON."""
        if tags_list is not None:
            self.tags = json.dumps(tags_list) if isinstance(tags_list, list) else None
        else:
            self.tags = None

    def create_version_snapshot(self, user_id, change_description=None):
        """Create a version snapshot before making changes."""
        snapshot = CharacterVersion(
            character_id=self.id,
            version=self.version,
            snapshot_data=json.dumps(self.to_dict(include_sensitive=False)),
            change_description=change_description,
            changed_by=user_id,
            changed_at=datetime.utcnow()
        )

        self.version += 1
        self.updated_at = datetime.utcnow()

        return snapshot

    def to_dict(self, include_sensitive=False):
        """Convert character to dictionary for API responses."""
        data = {
            'id': self.id,
            'character_id': self.character_id,
            'name': self.name,
            'email': self.email,
            'voice_model': self.voice_model,
            'ai_model': self.ai_model,
            'topics': self.get_topics(),
            'tags': self.get_tags(),
            'is_default': self.is_default,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'profile_image_url': self.profile_image_url,
            'image_last_generated': self.image_last_generated.isoformat() if self.image_last_generated else None,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_sensitive:
            data.update({
                'personality_prompt': self.personality_prompt,
                'stable_diffusion_prompt': self.stable_diffusion_prompt,
                'profile_image_path': self.profile_image_path,
                'created_by': self.created_by,
                'updated_by': self.updated_by,
                'version_count': self.versions.count()
            })

        return data


class CharacterVersion(db.Model):
    """Character version history for tracking prompt changes over time."""
    __tablename__ = 'character_versions'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)

    # Version snapshot
    snapshot_data = db.Column(db.Text, nullable=False)
    change_description = db.Column(db.Text, nullable=True)

    # Audit information
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    changer = db.relationship('User', backref='character_changes')

    # Composite unique constraint and index
    __table_args__ = (
        db.UniqueConstraint('character_id', 'version', name='uq_character_version'),
        db.Index('idx_character_version_lookup', 'character_id', 'version'),
    )

    def __repr__(self):
        return f'<CharacterVersion character_id={self.character_id} v{self.version}>'

    def get_snapshot(self):
        """Parse snapshot_data JSON field."""
        if self.snapshot_data:
            try:
                return json.loads(self.snapshot_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def to_dict(self):
        """Convert version to dictionary for API responses."""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'version': self.version,
            'snapshot': self.get_snapshot(),
            'change_description': self.change_description,
            'changed_by': self.changed_by,
            'changed_at': self.changed_at.isoformat()
        }


class SystemConfig(db.Model):
    """System-wide configuration settings with version control."""
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(200), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text, nullable=True)

    # Type information
    config_type = db.Column(db.String(20), default='string', nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True, index=True)

    # Visibility and versioning
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)

    # Audit fields
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    updater = db.relationship('User', backref='config_updates')

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_config_category_public', 'category', 'is_public'),
    )

    def __repr__(self):
        return f'<SystemConfig {self.config_key}={self.config_value[:50] if self.config_value else None}>'

    def get_value(self):
        """Parse and return the typed configuration value."""
        if self.config_value is None:
            return None

        try:
            if self.config_type == 'int':
                return int(self.config_value)
            elif self.config_type == 'float':
                return float(self.config_value)
            elif self.config_type == 'bool':
                return self.config_value.lower() in ('true', '1', 'yes', 't')
            elif self.config_type == 'json':
                return json.loads(self.config_value)
            else:
                return self.config_value
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"Cannot parse config value '{self.config_key}' as {self.config_type}: {e}")

    def set_value(self, value, config_type=None):
        """Set the configuration value with type conversion."""
        if config_type:
            self.config_type = config_type

        if value is None:
            self.config_value = None
        elif self.config_type == 'json':
            self.config_value = json.dumps(value) if not isinstance(value, str) else value
        elif self.config_type == 'bool':
            self.config_value = 'true' if value else 'false'
        else:
            self.config_value = str(value)

        self.version += 1
        self.updated_at = datetime.utcnow()

    @staticmethod
    def get_config(key, default=None):
        """Get a configuration value by key."""
        config = SystemConfig.query.filter_by(config_key=key).first()
        if config:
            try:
                return config.get_value()
            except ValueError:
                return default
        return default

    @staticmethod
    def set_config(key, value, config_type='string', description=None, category=None,
                   is_public=False, user_id=None):
        """Set a configuration value, creating or updating as needed."""
        config = SystemConfig.query.filter_by(config_key=key).first()

        if config:
            config.set_value(value, config_type)
            if description is not None:
                config.description = description
            if category is not None:
                config.category = category
            if user_id is not None:
                config.updated_by = user_id
        else:
            config = SystemConfig(
                config_key=key,
                config_type=config_type,
                description=description,
                category=category,
                is_public=is_public,
                updated_by=user_id
            )
            config.set_value(value, config_type)
            db.session.add(config)

        return config

    @staticmethod
    def get_category_configs(category, public_only=False):
        """Get all configuration values for a category."""
        query = SystemConfig.query.filter_by(category=category)
        if public_only:
            query = query.filter_by(is_public=True)

        configs = query.all()
        return {
            config.config_key: config.get_value()
            for config in configs
        }

    def to_dict(self, include_sensitive=False):
        """Convert config to dictionary for API responses."""
        data = {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.get_value(),
            'config_type': self.config_type,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'version': self.version,
            'updated_at': self.updated_at.isoformat()
        }

        if include_sensitive:
            data.update({
                'updated_by': self.updated_by,
                'created_at': self.created_at.isoformat()
            })

        return data


class AdminTask(db.Model):
    """Background administrative task tracking and monitoring."""
    __tablename__ = 'admin_tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50), nullable=False, index=True)
    task_status = db.Column(db.String(20), default='pending', nullable=False, index=True)

    # Task configuration and results
    task_params = db.Column(db.Text, nullable=True)
    result_data = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # Progress tracking
    progress_percent = db.Column(db.Integer, default=0, nullable=False)
    progress_message = db.Column(db.String(500), nullable=True)

    # User and worker tracking
    started_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    worker_id = db.Column(db.String(100), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    starter = db.relationship('User', backref='started_tasks')

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_task_status_type', 'task_status', 'task_type'),
        db.Index('idx_task_started_by', 'started_by', 'task_status'),
    )

    def __repr__(self):
        return f'<AdminTask {self.id}: {self.task_type} ({self.task_status})>'

    def get_params(self):
        """Parse task_params JSON field."""
        if self.task_params:
            try:
                return json.loads(self.task_params)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_params(self, params):
        """Set task parameters as JSON."""
        self.task_params = json.dumps(params) if params else None

    def get_result(self):
        """Parse result_data JSON field."""
        if self.result_data:
            try:
                return json.loads(self.result_data)
            except json.JSONDecodeError:
                return {}
        return {}

    def set_result(self, result):
        """Set task result as JSON."""
        self.result_data = json.dumps(result) if result else None

    def start_task(self, worker_id=None):
        """Mark task as started."""
        self.task_status = 'running'
        self.started_at = datetime.utcnow()
        if worker_id:
            self.worker_id = worker_id
        self.progress_percent = 0
        self.progress_message = 'Task started'

    def update_progress(self, percent, message=None):
        """Update task progress."""
        self.progress_percent = max(0, min(100, percent))
        if message:
            self.progress_message = message

    def complete_task(self, result=None):
        """Mark task as completed successfully."""
        self.task_status = 'completed'
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100
        self.progress_message = 'Task completed successfully'
        if result:
            self.set_result(result)

    def fail_task(self, error_message):
        """Mark task as failed."""
        self.task_status = 'failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.progress_message = f'Task failed: {error_message[:200]}'

    def cancel_task(self):
        """Cancel a pending or running task."""
        if self.task_status in ('pending', 'running'):
            self.task_status = 'cancelled'
            self.completed_at = datetime.utcnow()
            self.progress_message = 'Task cancelled by user'

    def get_duration(self):
        """Calculate task duration."""
        if not self.started_at:
            return None

        end_time = self.completed_at or datetime.utcnow()
        return end_time - self.started_at

    def is_stale(self, timeout_minutes=30):
        """Check if a running task has exceeded timeout."""
        if self.task_status != 'running':
            return False

        if not self.started_at:
            return False

        timeout = timedelta(minutes=timeout_minutes)
        return datetime.utcnow() - self.started_at > timeout

    def to_dict(self):
        """Convert task to dictionary for API responses."""
        duration = self.get_duration()

        return {
            'id': self.id,
            'task_type': self.task_type,
            'task_status': self.task_status,
            'task_params': self.get_params(),
            'result_data': self.get_result() if self.task_status == 'completed' else None,
            'error_message': self.error_message,
            'progress_percent': self.progress_percent,
            'progress_message': self.progress_message,
            'started_by': self.started_by,
            'worker_id': self.worker_id,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': duration.total_seconds() if duration else None
        }


class StoryIndex(db.Model):
    """Tracks LightRAG indexing status for stories.

    This model maintains the indexing state for each story in the LightRAG
    knowledge graph system, tracking whether stories are indexed, when they
    were last indexed, and any errors that occurred during indexing.
    """
    __tablename__ = 'story_index'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, unique=True)

    # Indexing status
    is_indexed = db.Column(db.Boolean, default=False, nullable=False)
    last_indexed_at = db.Column(db.DateTime, nullable=True)
    indexing_stage = db.Column(db.String(50), nullable=True)  # partial, content, title, complete

    # LightRAG metadata
    lightrag_doc_id = db.Column(db.String(100), nullable=True)  # External doc ID in LightRAG
    embedding_version = db.Column(db.String(20), nullable=True)  # Track embedding model version

    # Error tracking
    indexing_error = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    story = db.relationship('Story', backref=db.backref('index_status', uselist=False))

    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_story_index_indexed', 'is_indexed'),
        db.Index('idx_story_index_stage', 'indexing_stage'),
    )

    def __repr__(self):
        return f'<StoryIndex story_id={self.story_id} indexed={self.is_indexed}>'

    def to_dict(self):
        """Convert index status to dictionary for API responses."""
        return {
            'id': self.id,
            'story_id': self.story_id,
            'is_indexed': self.is_indexed,
            'last_indexed_at': self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            'indexing_stage': self.indexing_stage,
            'lightrag_doc_id': self.lightrag_doc_id,
            'embedding_version': self.embedding_version,
            'indexing_error': self.indexing_error,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class StoryFailure(db.Model):
    """Dead Letter Queue for permanently failed stories (Phase 1.2).

    Tracks stories that have exhausted all retry attempts or encountered
    unrecoverable errors. Provides manual review and retry capabilities
    through the admin portal.
    """
    __tablename__ = 'story_failures'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, unique=True)

    # Failure context
    failed_at_step = db.Column(db.Enum(WorkflowStep), nullable=False)  # Which step failed
    error_type = db.Column(db.String(50), nullable=False)  # TRANSIENT, RATE_LIMIT, CONFIGURATION, etc.
    error_message = db.Column(db.Text, nullable=False)  # Detailed error message
    stack_trace = db.Column(db.Text, nullable=True)  # Full stack trace for debugging
    retry_count = db.Column(db.Integer, default=0, nullable=False)  # Retries before failure

    # Classification and triage
    failure_reason = db.Column(db.Text, nullable=True)  # User-friendly explanation
    can_retry = db.Column(db.Boolean, default=True, nullable=False)  # Whether manual retry is possible
    requires_intervention = db.Column(db.Boolean, default=True, nullable=False)  # Needs manual action

    # Status tracking
    dlq_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, investigating, resolved, archived
    priority = db.Column(db.Integer, default=0, nullable=False)  # Higher = more urgent

    # Resolution tracking
    resolved_at = db.Column(db.DateTime, nullable=True)  # When manually fixed
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # User who resolved
    resolution_notes = db.Column(db.Text, nullable=True)  # What was done to fix

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    story = db.relationship('Story', backref=db.backref('failure', uselist=False))
    resolver = db.relationship('User', backref='resolved_failures')

    # Indexes for admin portal queries
    __table_args__ = (
        db.Index('idx_story_failure_status', 'dlq_status'),
        db.Index('idx_story_failure_error_type', 'error_type'),
        db.Index('idx_story_failure_step', 'failed_at_step'),
        db.Index('idx_story_failure_priority', 'priority', 'created_at'),
    )

    def __repr__(self):
        return f'<StoryFailure story_id={self.story_id} step={self.failed_at_step.value if self.failed_at_step else None} error_type={self.error_type}>'

    def mark_resolved(self, user_id, notes=None):
        """Mark this failure as resolved."""
        self.dlq_status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        if notes:
            self.resolution_notes = notes
        self.updated_at = datetime.utcnow()

    def mark_investigating(self):
        """Mark this failure as under investigation."""
        self.dlq_status = 'investigating'
        self.updated_at = datetime.utcnow()

    def archive(self):
        """Archive this failure (no longer needs attention)."""
        self.dlq_status = 'archived'
        self.updated_at = datetime.utcnow()

    def get_friendly_error(self):
        """Get user-friendly error explanation based on error type."""
        error_messages = {
            'TRANSIENT': 'Temporary network or API issue - safe to retry',
            'RATE_LIMIT': 'API rate limit exceeded - retry later',
            'CONFIGURATION': 'System configuration error - check API keys and settings',
            'VALIDATION': 'Invalid data or missing required fields',
            'RESOURCE': 'System resource issue (disk space, memory)',
            'PERMANENT': 'Unrecoverable error - manual review required'
        }
        return self.failure_reason or error_messages.get(self.error_type, 'Unknown error occurred')

    def to_dict(self, include_story=False):
        """Convert failure to dictionary for API responses."""
        data = {
            'id': self.id,
            'story_id': self.story_id,
            'failed_at_step': self.failed_at_step.value if self.failed_at_step else None,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'failure_reason': self.get_friendly_error(),
            'can_retry': self.can_retry,
            'requires_intervention': self.requires_intervention,
            'dlq_status': self.dlq_status,
            'priority': self.priority,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_story and self.story:
            data['story'] = {
                'topic': self.story.topic,
                'title': self.story.title,
                'genre': self.story.genre,
                'narrator_character_id': self.story.narrator_character_id
            }

        return data