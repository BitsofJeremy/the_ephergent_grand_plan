"""Admin API endpoints for asynchronous task management.

This module provides endpoints for creating, monitoring, and managing
background administrative tasks such as character migrations, bulk operations,
and other long-running processes.
"""

from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields, reqparse
from marshmallow import Schema, fields as ma_fields, ValidationError, validate
from datetime import datetime
from ephergent_generator import db
from ephergent_generator.models import AdminTask, Character
from ephergent_generator.services.auth_service import require_auth_or_api_key
import logging

logger = logging.getLogger(__name__)

# Create namespace for admin tasks
ns = Namespace('admin/tasks', description='Administrative task management')

# Request/Response Models
task_model = ns.model('AdminTask', {
    'id': fields.Integer(readonly=True, description='Task ID'),
    'task_type': fields.String(description='Type of admin task'),
    'task_status': fields.String(description='Task status: pending, running, completed, failed, cancelled'),
    'task_params': fields.Raw(description='Task parameters as JSON'),
    'result_data': fields.Raw(description='Task result data as JSON'),
    'error_message': fields.String(description='Error message if failed'),
    'progress_percent': fields.Integer(description='Progress percentage (0-100)'),
    'progress_message': fields.String(description='Progress status message'),
    'started_by': fields.Integer(description='User ID who started the task'),
    'worker_id': fields.String(description='Worker ID processing the task'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'started_at': fields.DateTime(description='Task start timestamp'),
    'completed_at': fields.DateTime(description='Task completion timestamp'),
    'duration_seconds': fields.Float(description='Task duration in seconds')
})

# Request parsers
task_list_parser = reqparse.RequestParser()
task_list_parser.add_argument('task_type', type=str, help='Filter by task type')
task_list_parser.add_argument('task_status', type=str, help='Filter by task status')
task_list_parser.add_argument('limit', type=int, default=50, help='Max number of tasks to return')

@ns.route('/')
class TaskList(Resource):
    """Admin task list endpoint."""

    @ns.expect(task_list_parser)
    @ns.marshal_list_with(task_model)
    @require_auth_or_api_key(['admin'])
    def get(self):
        """List administrative tasks with optional filters.

        Query Parameters:
            task_type (str): Filter by task type (e.g., 'character_migration')
            task_status (str): Filter by status (pending, running, completed, failed, cancelled)
            limit (int): Maximum number of tasks to return (default: 50)

        Returns:
            list[AdminTask]: List of admin tasks in reverse chronological order

        Security:
            Requires admin authentication
        """
        try:
            args = task_list_parser.parse_args()

            # Build query
            query = AdminTask.query

            if args['task_type']:
                query = query.filter_by(task_type=args['task_type'])

            if args['task_status']:
                query = query.filter_by(task_status=args['task_status'])

            # Order by creation date (newest first) and limit
            query = query.order_by(AdminTask.created_at.desc()).limit(args['limit'])

            tasks = query.all()

            result = [task.to_dict() for task in tasks]

            logger.info(f"Retrieved {len(result)} admin tasks (filters: {args})")
            return result, 200

        except Exception as e:
            logger.error(f"Error listing admin tasks: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving tasks: {str(e)}")


@ns.route('/<int:task_id>')
class TaskDetail(Resource):
    """Single admin task operations."""

    @ns.marshal_with(task_model)
    @require_auth_or_api_key(['admin'])
    def get(self, task_id):
        """Get detailed information about a specific task.

        Path Parameters:
            task_id (int): Task ID

        Returns:
            AdminTask: Full task details including progress and results

        Errors:
            404: Task not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            task = AdminTask.query.get(task_id)

            if not task:
                ns.abort(404, message=f"Task with ID {task_id} not found")

            logger.info(f"Retrieved task {task_id} status: {task.task_status}")
            return task.to_dict(), 200

        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving task: {str(e)}")

    @require_auth_or_api_key(['admin'])
    def delete(self, task_id):
        """Cancel a pending or running task.

        Path Parameters:
            task_id (int): Task ID

        Returns:
            dict: Success message

        Errors:
            404: Task not found
            400: Task cannot be cancelled (already completed/failed)
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            task = AdminTask.query.get(task_id)

            if not task:
                ns.abort(404, message=f"Task with ID {task_id} not found")

            if task.task_status not in ('pending', 'running'):
                ns.abort(400, message=f"Cannot cancel task with status '{task.task_status}'")

            task.cancel_task()
            db.session.commit()

            logger.info(f"Cancelled task {task_id}")

            return {
                'message': f'Task {task_id} successfully cancelled',
                'task_id': task.id,
                'task_type': task.task_type
            }, 200

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error cancelling task: {str(e)}")


@ns.route('/character-migration')
class CharacterMigrationTask(Resource):
    """Character migration task endpoint."""

    @require_auth_or_api_key(['admin'])
    def post(self):
        """Trigger character migration from files to database.

        Creates an async task to migrate character data from legacy JSON/Markdown
        files to the database-driven Character model.

        Request Body (optional):
            force (bool): Force re-migration even if characters already exist
            source_path (str): Custom path to character files

        Returns:
            dict: Task creation confirmation with task_id and status URL

        Security:
            Requires admin authentication

        Business Logic:
            1. Creates AdminTask with 'character_migration' type
            2. Task will be picked up by background worker
            3. Migrates personality_prompts_s3.json and character markdown files
            4. Updates existing characters or creates new ones
        """
        try:
            data = request.get_json() or {}

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create admin task
            task = AdminTask(
                task_type='character_migration',
                task_status='pending',
                started_by=user_id
            )
            task.set_params({
                'force': data.get('force', False),
                'source_path': data.get('source_path', 'ephergent_generator/prompts')
            })

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created character migration task {task.id} by user {user_id}")

            return {
                'message': 'Character migration task created',
                'task_id': task.id,
                'task_type': task.task_type,
                'status_url': f'/api/admin/tasks/{task.id}'
            }, 202

        except Exception as e:
            logger.error(f"Error creating character migration task: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating migration task: {str(e)}")


@ns.route('/bulk-image-generation')
class BulkImageGenerationTask(Resource):
    """Bulk character image generation task endpoint."""

    @require_auth_or_api_key(['admin'])
    def post(self):
        """Generate profile images for all characters.

        Creates an async task to generate profile images for all active characters
        that have stable_diffusion_prompt configured.

        Request Body (optional):
            force_regenerate (bool): Regenerate even if image already exists
            character_ids (list[int]): Specific character IDs to process (all if not provided)
            active_only (bool): Only process active characters (default: True)

        Returns:
            dict: Task creation confirmation with task_id and status URL

        Security:
            Requires admin authentication

        Business Logic:
            1. Creates AdminTask with 'bulk_image_generation' type
            2. Task will be picked up by background worker
            3. Processes characters sequentially with delay between generations
            4. Updates Character.image_last_generated and profile_image_path
        """
        try:
            data = request.get_json() or {}

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Validate character_ids if provided
            character_ids = data.get('character_ids')
            if character_ids:
                if not isinstance(character_ids, list):
                    ns.abort(400, message="character_ids must be an array")

                # Verify all characters exist
                for char_id in character_ids:
                    if not Character.query.get(char_id):
                        ns.abort(404, message=f"Character with ID {char_id} not found")

            # Create admin task
            task = AdminTask(
                task_type='bulk_image_generation',
                task_status='pending',
                started_by=user_id
            )
            task.set_params({
                'force_regenerate': data.get('force_regenerate', False),
                'character_ids': character_ids,
                'active_only': data.get('active_only', True)
            })

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created bulk image generation task {task.id} by user {user_id}")

            return {
                'message': 'Bulk image generation task created',
                'task_id': task.id,
                'task_type': task.task_type,
                'status_url': f'/api/admin/tasks/{task.id}'
            }, 202

        except Exception as e:
            logger.error(f"Error creating bulk image generation task: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating task: {str(e)}")


@ns.route('/cleanup-stale')
class StaleTaskCleanupTask(Resource):
    """Stale task cleanup endpoint."""

    @require_auth_or_api_key(['admin'])
    def post(self):
        """Clean up stale running tasks that have exceeded timeout.

        Creates an async task to identify and mark as failed any tasks that have
        been running for longer than the configured timeout period.

        Request Body (optional):
            timeout_minutes (int): Timeout threshold in minutes (default: 30)

        Returns:
            dict: Task creation confirmation with task_id and status URL

        Security:
            Requires admin authentication

        Business Logic:
            1. Creates AdminTask with 'cleanup_stale_tasks' type
            2. Identifies tasks in 'running' status older than timeout
            3. Marks them as 'failed' with timeout error message
        """
        try:
            data = request.get_json() or {}

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create admin task
            task = AdminTask(
                task_type='cleanup_stale_tasks',
                task_status='pending',
                started_by=user_id
            )
            task.set_params({
                'timeout_minutes': data.get('timeout_minutes', 30)
            })

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created stale task cleanup task {task.id} by user {user_id}")

            return {
                'message': 'Stale task cleanup task created',
                'task_id': task.id,
                'task_type': task.task_type,
                'status_url': f'/api/admin/tasks/{task.id}'
            }, 202

        except Exception as e:
            logger.error(f"Error creating cleanup task: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating cleanup task: {str(e)}")


@ns.route('/stats')
class TaskStats(Resource):
    """Task statistics endpoint."""

    @require_auth_or_api_key(['admin'])
    def get(self):
        """Get statistics about admin tasks.

        Returns:
            dict: Task statistics including counts by status and type

        Security:
            Requires admin authentication
        """
        try:
            # Get counts by status
            status_counts = db.session.query(
                AdminTask.task_status,
                db.func.count(AdminTask.id).label('count')
            ).group_by(AdminTask.task_status).all()

            # Get counts by type
            type_counts = db.session.query(
                AdminTask.task_type,
                db.func.count(AdminTask.id).label('count')
            ).group_by(AdminTask.task_type).all()

            # Get recent tasks (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_count = AdminTask.query.filter(
                AdminTask.created_at >= yesterday
            ).count()

            # Get stale running tasks
            stale_tasks = AdminTask.query.filter_by(task_status='running').all()
            stale_count = sum(1 for task in stale_tasks if task.is_stale(timeout_minutes=30))

            result = {
                'by_status': {
                    status: count for status, count in status_counts
                },
                'by_type': {
                    task_type: count for task_type, count in type_counts
                },
                'recent_24h': recent_count,
                'stale_running': stale_count,
                'total_tasks': sum(count for _, count in status_counts)
            }

            logger.info(f"Retrieved task statistics")

            return result, 200

        except Exception as e:
            logger.error(f"Error retrieving task stats: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving statistics: {str(e)}")


@ns.route('/retry/<int:task_id>')
class TaskRetry(Resource):
    """Task retry endpoint."""

    @require_auth_or_api_key(['admin'])
    def post(self, task_id):
        """Retry a failed task by creating a new task with same parameters.

        Path Parameters:
            task_id (int): Original task ID to retry

        Returns:
            dict: New task creation confirmation

        Errors:
            404: Original task not found
            400: Task is not in failed or cancelled status
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            original_task = AdminTask.query.get(task_id)

            if not original_task:
                ns.abort(404, message=f"Task with ID {task_id} not found")

            if original_task.task_status not in ('failed', 'cancelled'):
                ns.abort(400, message=f"Can only retry failed or cancelled tasks, task status is '{original_task.task_status}'")

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create new task with same parameters
            new_task = AdminTask(
                task_type=original_task.task_type,
                task_status='pending',
                started_by=user_id
            )
            new_task.set_params(original_task.get_params())

            db.session.add(new_task)
            db.session.commit()

            logger.info(f"Created retry task {new_task.id} for failed task {task_id}")

            return {
                'message': f'Retry task created for task {task_id}',
                'original_task_id': task_id,
                'new_task_id': new_task.id,
                'task_type': new_task.task_type,
                'status_url': f'/api/admin/tasks/{new_task.id}'
            }, 201

        except Exception as e:
            logger.error(f"Error retrying task {task_id}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error retrying task: {str(e)}")
