"""Database initialization service for the Season 03 Story Generator.

This service handles database table creation and initial data setup,
including the creation of default admin users when needed.
"""

import logging
from typing import Optional
from flask import current_app
from ephergent_generator import db
from ephergent_generator.models import User
from ephergent_generator.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class DatabaseInitService:
    """Service for database initialization and default data setup."""

    @staticmethod
    def initialize_database() -> None:
        """Initialize database tables and default data."""
        try:
            logger.info("Initializing database tables")
            db.create_all()
            logger.info("Database tables created successfully")

            # Create default admin user if none exists
            DatabaseInitService.ensure_default_admin()

        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    @staticmethod
    def ensure_default_admin() -> Optional[User]:
        """Ensure at least one admin user exists, creating a default one if needed."""
        try:
            # Check if any admin users exist
            existing_admin_count = User.query.filter_by(is_admin=True, is_active=True).count()

            if existing_admin_count > 0:
                logger.info(f"Found {existing_admin_count} existing admin user(s)")
                return None

            # No admin users exist, create the default admin
            logger.info("No admin users found, creating default admin user")

            default_admin = DatabaseInitService.create_default_admin()
            if default_admin:
                logger.info(f"✅ Default admin user created successfully:")
                logger.info(f"   Username: {default_admin.username}")
                logger.info(f"   Email: {default_admin.email}")
                logger.info(f"   ID: {default_admin.id}")
                logger.info("   ⚠️  Please change the default password after first login!")
                return default_admin
            else:
                logger.warning("Failed to create default admin user")
                return None

        except Exception as e:
            logger.error(f"Error ensuring default admin user: {str(e)}")
            return None

    @staticmethod
    def create_default_admin() -> Optional[User]:
        """Create the default admin user from configuration."""
        try:
            # Get default admin settings from configuration
            username = current_app.config.get('DEFAULT_ADMIN_USERNAME', 'admin')
            email = current_app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@ephergent.local')
            password = current_app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin123')

            # Validate required settings
            if not username or not email or not password:
                logger.error("Default admin configuration is incomplete")
                logger.error(f"Username: {username}, Email: {email}, Password: {'***' if password else 'None'}")
                return None

            # Check if user with this username or email already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                if not existing_user.is_admin:
                    # User exists but is not admin, promote them
                    logger.info(f"Promoting existing user '{username}' to admin")
                    existing_user.is_admin = True
                    existing_user.is_active = True
                    db.session.commit()
                    return existing_user
                else:
                    logger.info(f"User '{username}' already exists and is admin")
                    return existing_user

            # Create new admin user
            admin_user = AuthService.create_user(
                username=username,
                email=email,
                password=password,
                is_admin=True
            )

            return admin_user

        except ValueError as e:
            logger.error(f"Default admin creation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating default admin: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def get_database_status() -> dict:
        """Get current database status information."""
        try:
            user_count = User.query.count()
            admin_count = User.query.filter_by(is_admin=True, is_active=True).count()

            return {
                'tables_exist': True,
                'user_count': user_count,
                'admin_count': admin_count,
                'has_default_admin': admin_count > 0
            }
        except Exception as e:
            logger.error(f"Error getting database status: {str(e)}")
            return {
                'tables_exist': False,
                'error': str(e)
            }