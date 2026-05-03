import os
try:
    # dotenv is optional at runtime if the environment is managed externally
    from dotenv import load_dotenv
except Exception:
    # Provide a no-op fallback so the module can be imported in minimal environments
    def load_dotenv(*args, **kwargs):
        return False

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Base configuration class."""

    # Flask Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Authentication Settings
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('SESSION_LIFETIME_HOURS', 24)) * 3600  # 24 hours in seconds
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Login Manager Settings
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = 'Please log in to access this page.'
    LOGIN_MESSAGE_CATEGORY = 'info'

    # Default Admin User Settings (created automatically if no admin users exist)
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@ephergent.local')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'ephergent123')
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Google Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # Server Configuration
    FLASK_HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes', 't')
    
    # Worker Configuration
    WORKER_SLEEP_INTERVAL = int(os.environ.get('WORKER_SLEEP_INTERVAL', 5))
    WORKER_TIMEOUT_MINUTES = int(os.environ.get('WORKER_TIMEOUT_MINUTES', 30))
    
    # Story Generation Defaults
    DEFAULT_WORD_COUNT = int(os.environ.get('DEFAULT_WORD_COUNT', 500))
    MAX_WORD_COUNT = int(os.environ.get('MAX_WORD_COUNT', 2000))
    
    # Queue Configuration
    DEFAULT_STORY_PRIORITY = int(os.environ.get('DEFAULT_STORY_PRIORITY', 0))
    MAX_QUEUE_SIZE = int(os.environ.get('MAX_QUEUE_SIZE', 1000))
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'upload_storage')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_FILE_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'mp4', 'avi'}
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'season_03_generator.log')

    # Monitoring Services
    GRAFANA_URL = os.environ.get('GRAFANA_URL', 'http://10.0.0.99:3000')

    @staticmethod
    def validate_required_config():
        """Validate that all required configuration is present."""
        errors = []
        
        if not Config.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY environment variable is required")
        
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            if not Config.FLASK_DEBUG:
                errors.append("SECRET_KEY should be set to a secure value in production")
        
        return errors

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_DEBUG = True
    TESTING = False
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///stories_dev.db'
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use a test API key if provided
    GEMINI_API_KEY = os.environ.get('TEST_GEMINI_API_KEY') or Config.GEMINI_API_KEY

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    print("***WE ARE IN PRODUCTION***")
    # Production should use PostgreSQL or similar
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Stricter configuration validation for production
    @staticmethod
    def validate_required_config():
        errors = Config.validate_required_config()
        
        if ProductionConfig.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be set to a secure value in production")
        
        # Be defensive: DATABASE_URL may be None. Validate presence and that it's not SQLite.
        db_uri = ProductionConfig.SQLALCHEMY_DATABASE_URI or ''
        if not db_uri:
            errors.append("DATABASE_URL must be set in production")
        else:
            if db_uri.startswith('sqlite:'):
                errors.append("Production should use PostgreSQL, not SQLite")

        return errors

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration class based on environment."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_map.get(config_name, config_map['default'])

# For backwards compatibility
def load_config(app, config_name=None):
    """Load configuration into Flask app."""
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Validate configuration
    validation_errors = config_class.validate_required_config()
    if validation_errors:
        for error in validation_errors:
            app.logger.warning(f"Configuration warning: {error}")
    
    return config_class
