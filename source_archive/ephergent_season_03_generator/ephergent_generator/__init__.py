from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from config import load_config
from pathlib import Path
from ephergent_generator.utils.logging_config import setup_logging
from ephergent_generator.utils.metrics import metrics_service

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name=None):
    # Configure static and template directories
    project_root = Path(__file__).parent.parent
    static_folder = project_root / 'ephergent_generator' / 'static'
    template_folder = project_root / 'ephergent_generator' / 'templates'
    
    app = Flask(__name__, 
                static_folder=str(static_folder),
                template_folder=str(template_folder))
    
    # Load configuration
    config_class = load_config(app, config_name)

    # Set up structured logging (JSON in production, human-readable in development)
    setup_logging(app)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting Season 03 Generator with {config_class.__name__}", extra={
        'config_class': config_class.__name__,
        'debug_mode': app.config.get('DEBUG', False),
        'database_engine': app.config['SQLALCHEMY_DATABASE_URI'].split(':')[0] if app.config.get('SQLALCHEMY_DATABASE_URI') else 'none'
    })
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Initialize Prometheus metrics (adds /metrics endpoint)
    metrics_service.init_app(app)
    logger.info("Prometheus metrics initialized - endpoint available at /metrics")

    # Configure login manager
    login_manager.login_view = app.config['LOGIN_VIEW']
    login_manager.login_message = app.config['LOGIN_MESSAGE']
    login_manager.login_message_category = app.config['LOGIN_MESSAGE_CATEGORY']

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from ephergent_generator.models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {str(e)}")
            return None

    # Register blueprints
    from ephergent_generator.api import api_blueprint as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register admin API blueprint
    from ephergent_generator.api.admin import admin_api_blueprint
    app.register_blueprint(admin_api_blueprint)

    from ephergent_generator.main import bp as main_bp
    app.register_blueprint(main_bp)

    from ephergent_generator.auth import auth_bp
    app.register_blueprint(auth_bp)

    from ephergent_generator.admin import admin_bp
    app.register_blueprint(admin_bp)

    # Add template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to <br> tags."""
        return text.replace('\n', '<br>\n') if text else ''
    
    # Initialize database and default data
    with app.app_context():
        from ephergent_generator.services.db_init_service import DatabaseInitService
        logger.info("Initializing database and default data")
        DatabaseInitService.initialize_database()
        logger.info("Database initialization completed")
    
    logger.info("Flask application created successfully")
    return app
