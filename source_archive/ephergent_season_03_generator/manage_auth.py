#!/usr/bin/env python3
"""Authentication management script for Season 03 Story Generator.

This script provides command-line utilities for managing users and API keys
in the Season 03 Story Generator application.

Usage:
    python manage_auth.py create-admin <username> <email> <password>
    python manage_auth.py create-user <username> <email> <password>
    python manage_auth.py list-users
    python manage_auth.py create-api-key <username> <key_name> [--permissions <perm1,perm2>] [--expires <days>] [--rate-limit <limit>]
    python manage_auth.py list-api-keys [<username>]
    python manage_auth.py revoke-api-key <key_id>
    python manage_auth.py change-password <username> <new_password>
    python manage_auth.py deactivate-user <username>
    python manage_auth.py activate-user <username>
    python manage_auth.py make-admin <username>
    python manage_auth.py remove-admin <username>
    python manage_auth.py init-db
"""

import os
import sys
import argparse
import getpass
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ephergent_generator import create_app, db
from ephergent_generator.models import User, APIKey
from ephergent_generator.services.auth_service import AuthService


def setup_app():
    """Create and configure the Flask app."""
    app = create_app()
    return app


def create_admin_user(args):
    """Create an admin user."""
    app = setup_app()

    with app.app_context():
        try:
            user = AuthService.create_user(
                username=args.username,
                email=args.email,
                password=args.password,
                is_admin=True
            )
            print(f"✅ Admin user created successfully:")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Admin: {user.is_admin}")
            print(f"   ID: {user.id}")
        except ValueError as e:
            print(f"❌ Error creating admin user: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1

    return 0


def create_regular_user(args):
    """Create a regular user."""
    app = setup_app()

    with app.app_context():
        try:
            user = AuthService.create_user(
                username=args.username,
                email=args.email,
                password=args.password,
                is_admin=False
            )
            print(f"✅ User created successfully:")
            print(f"   Username: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Admin: {user.is_admin}")
            print(f"   ID: {user.id}")
        except ValueError as e:
            print(f"❌ Error creating user: {e}")
            return 1
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1

    return 0


def list_users(args):
    """List all users."""
    app = setup_app()

    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).all()

        if not users:
            print("📭 No users found.")
            return 0

        print(f"👥 Found {len(users)} user(s):\n")

        for user in users:
            status_icon = "✅" if user.is_active else "❌"
            admin_icon = "👑" if user.is_admin else "👤"

            print(f"{status_icon} {admin_icon} {user.username} ({user.email})")
            print(f"    ID: {user.id}")
            print(f"    Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'}")
            print(f"    Login Count: {user.login_count}")
            print(f"    API Keys: {len(user.api_keys)}")
            print()

    return 0


def create_api_key_cmd(args):
    """Create an API key for a user."""
    app = setup_app()

    with app.app_context():
        # Find user
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        # Parse permissions
        permissions = []
        if args.permissions:
            permissions = [p.strip() for p in args.permissions.split(',')]

        try:
            api_key_obj, raw_key = AuthService.create_api_key(
                user_id=user.id,
                name=args.key_name,
                permissions=permissions,
                expires_days=args.expires,
                rate_limit=args.rate_limit
            )

            print(f"✅ API key created successfully:")
            print(f"   Name: {api_key_obj.name}")
            print(f"   User: {user.username}")
            print(f"   Key: {raw_key}")
            print(f"   Permissions: {', '.join(permissions) if permissions else 'None'}")
            print(f"   Rate Limit: {api_key_obj.rate_limit}/hour")
            print(f"   Expires: {api_key_obj.expires_at.strftime('%Y-%m-%d') if api_key_obj.expires_at else 'Never'}")
            print()
            print("⚠️  IMPORTANT: This is the only time the full API key will be shown.")
            print("   Store it securely as it cannot be retrieved again.")

        except Exception as e:
            print(f"❌ Error creating API key: {e}")
            return 1

    return 0


def list_api_keys_cmd(args):
    """List API keys."""
    app = setup_app()

    with app.app_context():
        query = APIKey.query.join(User)

        if args.username:
            query = query.filter(
                (User.username == args.username) | (User.email == args.username)
            )

        api_keys = query.order_by(APIKey.created_at.desc()).all()

        if not api_keys:
            if args.username:
                print(f"🔑 No API keys found for user: {args.username}")
            else:
                print("🔑 No API keys found.")
            return 0

        print(f"🔑 Found {len(api_keys)} API key(s):\n")

        for key in api_keys:
            status_icon = "✅" if key.is_active else "❌"
            if key.is_active and key.is_expired():
                status_icon = "⏰"
            elif key.is_active and key.is_rate_limited():
                status_icon = "🚦"

            print(f"{status_icon} {key.name} ({key.key_prefix}...)")
            print(f"    ID: {key.id}")
            print(f"    User: {key.user.username}")
            print(f"    Created: {key.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Last Used: {key.last_used.strftime('%Y-%m-%d %H:%M:%S') if key.last_used else 'Never'}")
            print(f"    Usage: {key.usage_count} total, {key.current_hour_usage}/{key.rate_limit} this hour")
            print(f"    Permissions: {', '.join(key.get_permissions()) if key.get_permissions() else 'None'}")
            print(f"    Expires: {key.expires_at.strftime('%Y-%m-%d') if key.expires_at else 'Never'}")
            print()

    return 0


def revoke_api_key_cmd(args):
    """Revoke an API key."""
    app = setup_app()

    with app.app_context():
        api_key = APIKey.query.get(args.key_id)

        if not api_key:
            print(f"❌ API key not found: {args.key_id}")
            return 1

        if not api_key.is_active:
            print(f"⚠️  API key is already inactive: {api_key.name}")
            return 0

        try:
            success = AuthService.revoke_api_key(args.key_id)
            if success:
                print(f"✅ API key revoked successfully:")
                print(f"   Name: {api_key.name}")
                print(f"   User: {api_key.user.username}")
            else:
                print(f"❌ Failed to revoke API key: {args.key_id}")
                return 1
        except Exception as e:
            print(f"❌ Error revoking API key: {e}")
            return 1

    return 0


def change_password_cmd(args):
    """Change a user's password."""
    app = setup_app()

    with app.app_context():
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        try:
            user.set_password(args.new_password)
            db.session.commit()

            print(f"✅ Password changed successfully for user: {user.username}")
        except Exception as e:
            print(f"❌ Error changing password: {e}")
            return 1

    return 0


def deactivate_user_cmd(args):
    """Deactivate a user."""
    app = setup_app()

    with app.app_context():
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        if not user.is_active:
            print(f"⚠️  User is already inactive: {user.username}")
            return 0

        try:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.session.commit()

            print(f"✅ User deactivated successfully: {user.username}")
        except Exception as e:
            print(f"❌ Error deactivating user: {e}")
            return 1

    return 0


def activate_user_cmd(args):
    """Activate a user."""
    app = setup_app()

    with app.app_context():
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        if user.is_active:
            print(f"⚠️  User is already active: {user.username}")
            return 0

        try:
            user.is_active = True
            user.updated_at = datetime.utcnow()
            db.session.commit()

            print(f"✅ User activated successfully: {user.username}")
        except Exception as e:
            print(f"❌ Error activating user: {e}")
            return 1

    return 0


def make_admin_cmd(args):
    """Make a user an admin."""
    app = setup_app()

    with app.app_context():
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        if user.is_admin:
            print(f"⚠️  User is already an admin: {user.username}")
            return 0

        try:
            user.is_admin = True
            user.updated_at = datetime.utcnow()
            db.session.commit()

            print(f"✅ User is now an admin: {user.username}")
        except Exception as e:
            print(f"❌ Error making user admin: {e}")
            return 1

    return 0


def remove_admin_cmd(args):
    """Remove admin privileges from a user."""
    app = setup_app()

    with app.app_context():
        user = User.query.filter(
            (User.username == args.username) | (User.email == args.username)
        ).first()

        if not user:
            print(f"❌ User not found: {args.username}")
            return 1

        if not user.is_admin:
            print(f"⚠️  User is not an admin: {user.username}")
            return 0

        # Check if this is the last admin
        admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
        if admin_count <= 1:
            print(f"❌ Cannot remove admin privileges: {user.username} is the last active admin.")
            print("   Create another admin user first.")
            return 1

        try:
            user.is_admin = False
            user.updated_at = datetime.utcnow()
            db.session.commit()

            print(f"✅ Admin privileges removed from user: {user.username}")
        except Exception as e:
            print(f"❌ Error removing admin privileges: {e}")
            return 1

    return 0


def init_db_cmd(args):
    """Initialize the database with tables."""
    app = setup_app()

    with app.app_context():
        try:
            db.create_all()
            print("✅ Database initialized successfully.")

            # Check if there are any admin users
            admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
            if admin_count == 0:
                print("\n⚠️  No admin users found.")
                print("   Use 'python manage_auth.py create-admin' to create your first admin user.")

        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Authentication management for Season 03 Story Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_auth.py create-admin admin admin@example.com mypassword
  python manage_auth.py list-users
  python manage_auth.py create-api-key admin "Production API" --permissions "stories:read,stories:write"
  python manage_auth.py list-api-keys admin
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create admin user
    admin_parser = subparsers.add_parser('create-admin', help='Create an admin user')
    admin_parser.add_argument('username', help='Username for the admin user')
    admin_parser.add_argument('email', help='Email for the admin user')
    admin_parser.add_argument('password', help='Password for the admin user')

    # Create regular user
    user_parser = subparsers.add_parser('create-user', help='Create a regular user')
    user_parser.add_argument('username', help='Username for the user')
    user_parser.add_argument('email', help='Email for the user')
    user_parser.add_argument('password', help='Password for the user')

    # List users
    subparsers.add_parser('list-users', help='List all users')

    # Create API key
    api_key_parser = subparsers.add_parser('create-api-key', help='Create an API key')
    api_key_parser.add_argument('username', help='Username or email of the user')
    api_key_parser.add_argument('key_name', help='Name for the API key')
    api_key_parser.add_argument('--permissions', help='Comma-separated list of permissions')
    api_key_parser.add_argument('--expires', type=int, help='Expiration in days')
    api_key_parser.add_argument('--rate-limit', type=int, default=1000, help='Rate limit per hour (default: 1000)')

    # List API keys
    list_keys_parser = subparsers.add_parser('list-api-keys', help='List API keys')
    list_keys_parser.add_argument('username', nargs='?', help='Username to filter by (optional)')

    # Revoke API key
    revoke_parser = subparsers.add_parser('revoke-api-key', help='Revoke an API key')
    revoke_parser.add_argument('key_id', type=int, help='ID of the API key to revoke')

    # Change password
    passwd_parser = subparsers.add_parser('change-password', help='Change user password')
    passwd_parser.add_argument('username', help='Username or email of the user')
    passwd_parser.add_argument('new_password', help='New password')

    # Deactivate user
    deactivate_parser = subparsers.add_parser('deactivate-user', help='Deactivate a user')
    deactivate_parser.add_argument('username', help='Username or email of the user')

    # Activate user
    activate_parser = subparsers.add_parser('activate-user', help='Activate a user')
    activate_parser.add_argument('username', help='Username or email of the user')

    # Make admin
    make_admin_parser = subparsers.add_parser('make-admin', help='Give admin privileges to a user')
    make_admin_parser.add_argument('username', help='Username or email of the user')

    # Remove admin
    remove_admin_parser = subparsers.add_parser('remove-admin', help='Remove admin privileges from a user')
    remove_admin_parser.add_argument('username', help='Username or email of the user')

    # Initialize database
    subparsers.add_parser('init-db', help='Initialize database tables')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Command dispatch
    commands = {
        'create-admin': create_admin_user,
        'create-user': create_regular_user,
        'list-users': list_users,
        'create-api-key': create_api_key_cmd,
        'list-api-keys': list_api_keys_cmd,
        'revoke-api-key': revoke_api_key_cmd,
        'change-password': change_password_cmd,
        'deactivate-user': deactivate_user_cmd,
        'activate-user': activate_user_cmd,
        'make-admin': make_admin_cmd,
        'remove-admin': remove_admin_cmd,
        'init-db': init_db_cmd,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
