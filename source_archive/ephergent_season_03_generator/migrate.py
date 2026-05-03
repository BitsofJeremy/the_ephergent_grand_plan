#!/usr/bin/env python3
"""
Migration management script for Ephergent Season 03 Generator.

This script provides convenient commands for managing database migrations
using Flask-Migrate (Alembic). It's designed to work in both local development
and Docker deployment environments.

Usage:
    python migrate.py init           - Initialize migrations directory
    python migrate.py create "msg"   - Create a new migration
    python migrate.py upgrade        - Apply all pending migrations
    python migrate.py downgrade      - Rollback last migration
    python migrate.py current        - Show current migration revision
    python migrate.py history        - Show migration history
    python migrate.py stamp head     - Mark database as up-to-date without running migrations
"""

import sys
import os
from flask.cli import FlaskGroup
from ephergent_generator import create_app, db

app = create_app()
cli = FlaskGroup(create_app=lambda: app)

def print_help():
    """Print usage information."""
    print(__doc__)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_help()
        sys.exit(0)

    command = sys.argv[1]

    # Map our simple commands to flask db commands
    command_map = {
        'init': ['db', 'init'],
        'create': ['db', 'migrate'],
        'upgrade': ['db', 'upgrade'],
        'downgrade': ['db', 'downgrade'],
        'current': ['db', 'current'],
        'history': ['db', 'history'],
        'stamp': ['db', 'stamp'],
    }

    if command in command_map:
        # Replace our command with the flask db command
        sys.argv[1:] = command_map[command] + sys.argv[2:]
        cli()
    elif command in ['help', '--help', '-h']:
        print_help()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)
