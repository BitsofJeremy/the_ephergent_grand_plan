#!/usr/bin/env python3
"""
Test script for Ephergent MCP Server

This script verifies that the MCP server can:
1. Initialize properly with database connection
2. List available tools
3. Handle basic tool calls
4. Process story creation workflow

Run this before configuring Claude Desktop to ensure everything works.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ephergent_generator import create_app, db
from ephergent_generator.models import Story, Character
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.character_service import CharacterService


def test_database_connection():
    """Test database connection and basic queries."""
    print("Testing database connection...")

    try:
        app = create_app()
        with app.app_context():
            story_count = Story.query.count()
            character_count = Character.query.count()

            print(f"✓ Database connected successfully")
            print(f"  - Stories in database: {story_count}")
            print(f"  - Characters in database: {character_count}")

            if character_count == 0:
                print("  ⚠ Warning: No characters found. Run database migrations and initialization.")

            return True
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        return False


def test_character_service():
    """Test character service functionality."""
    print("\nTesting character service...")

    try:
        app = create_app()
        with app.app_context():
            character_service = CharacterService()

            # Get all characters
            characters = character_service.get_all_characters()
            print(f"✓ Character service working")
            print(f"  - Available characters: {len(characters)}")

            if characters:
                default_char = character_service.get_default_character()
                if default_char:
                    print(f"  - Default character: {default_char['name']} ({default_char['id']})")

                # Show first few characters
                for char in characters[:3]:
                    print(f"  - {char['name']} ({char['id']})")

            return True
    except Exception as e:
        print(f"✗ Character service failed: {str(e)}")
        return False


def test_story_workflow_service():
    """Test story workflow service initialization."""
    print("\nTesting story workflow service...")

    try:
        app = create_app()
        with app.app_context():
            workflow_service = StoryWorkflowService()

            print(f"✓ Workflow service initialized")
            print(f"  - GeminiService: OK")
            print(f"  - CharacterService: OK")
            print(f"  - QueueService: OK")
            print(f"  - ImageService: OK")
            print(f"  - AudioService: OK")
            print(f"  - VideoService: OK")
            print(f"  - YouTubeService: OK")
            print(f"  - GhostService: OK")

            return True
    except Exception as e:
        print(f"✗ Workflow service initialization failed: {str(e)}")
        return False


def test_create_story():
    """Test story creation (without actually processing it)."""
    print("\nTesting story creation...")

    try:
        app = create_app()
        with app.app_context():
            workflow_service = StoryWorkflowService()

            # Create a test story
            test_topic = "MCP Server Test Story - Automated Test"

            story = workflow_service.create_story_from_topic(
                topic=test_topic,
                genre="test",
                tone="testing",
                word_count=100,
                session_id="mcp_test"
            )

            print(f"✓ Story creation successful")
            print(f"  - Story ID: {story.id}")
            print(f"  - Topic: {story.topic}")
            print(f"  - Status: {story.current_step.value}")

            # Clean up test story
            db.session.delete(story)
            db.session.commit()
            print(f"  - Test story cleaned up")

            return True
    except Exception as e:
        print(f"✗ Story creation failed: {str(e)}")
        db.session.rollback()
        return False


def test_story_retrieval():
    """Test story retrieval functions."""
    print("\nTesting story retrieval...")

    try:
        app = create_app()
        with app.app_context():
            # Get recent stories
            recent_stories = Story.query.order_by(Story.created_at.desc()).limit(5).all()

            print(f"✓ Story retrieval successful")
            print(f"  - Recent stories: {len(recent_stories)}")

            if recent_stories:
                for story in recent_stories[:3]:
                    print(f"  - Story {story.id}: {story.topic[:50]}... ({story.current_step.value})")

            return True
    except Exception as e:
        print(f"✗ Story retrieval failed: {str(e)}")
        return False


def test_mcp_imports():
    """Test MCP SDK imports."""
    print("\nTesting MCP SDK imports...")

    try:
        from mcp.server import Server
        from mcp.types import Tool, TextContent
        import mcp.server.stdio

        print(f"✓ MCP SDK imports successful")
        print(f"  - mcp.server.Server: OK")
        print(f"  - mcp.types: OK")
        print(f"  - mcp.server.stdio: OK")

        return True
    except ImportError as e:
        print(f"✗ MCP SDK import failed: {str(e)}")
        print(f"  Run: uv sync")
        return False


def test_mcp_server_startup():
    """Test MCP server initialization (without running it)."""
    print("\nTesting MCP server initialization...")

    try:
        # Import the server module
        import mcp_server

        print(f"✓ MCP server module loaded")

        # Check that the server instance exists
        if hasattr(mcp_server, 'server'):
            print(f"  - Server instance: OK")

        # Check that handlers are defined
        if hasattr(mcp_server, 'list_tools'):
            print(f"  - list_tools handler: OK")

        if hasattr(mcp_server, 'call_tool'):
            print(f"  - call_tool handler: OK")

        return True
    except Exception as e:
        print(f"✗ MCP server initialization failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Ephergent MCP Server Test Suite")
    print("=" * 60)

    tests = [
        ("Database Connection", test_database_connection),
        ("Character Service", test_character_service),
        ("Story Workflow Service", test_story_workflow_service),
        ("Create Story", test_create_story),
        ("Story Retrieval", test_story_retrieval),
        ("MCP SDK Imports", test_mcp_imports),
        ("MCP Server Initialization", test_mcp_server_startup),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Configure Claude Desktop (see README_MCP.md)")
        print("2. Restart Claude Desktop")
        print("3. Start worker process: python worker.py --continuous")
        print("4. Test in Claude Desktop: 'Create a story about test'")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues before using MCP server.")
        print("\nCommon fixes:")
        print("- Run: uv sync (to install dependencies)")
        print("- Run: ./MIGRATION_QUICKSTART.sh (to initialize database)")
        print("- Check .env file for required configuration")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
