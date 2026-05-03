"""
Archive API for Ephergent Season 03 Story Generator

Provides REST API endpoints for archiving stories and their media files.
"""

from flask import request, current_app, jsonify
from flask_restx import Namespace, Resource, fields
from ephergent_generator.services.archive_service import ArchiveService
from ephergent_generator.services.auth_service import require_auth_or_api_key
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator import db
import logging

logger = logging.getLogger(__name__)

# Create an archive namespace
ns = Namespace('archive', description='Story archiving operations')

# Archive Status Model
archive_status_model = ns.model('ArchiveStatus', {
    'status': fields.String(description='Archive operation status', enum=['success', 'warning', 'error', 'skipped']),
    'message': fields.String(description='Status message'),
    'archive_path': fields.String(description='Path to archived story'),
    'files_archived': fields.Integer(description='Number of files archived'),
    'archived_files': fields.List(fields.String, description='List of archived file paths')
})

# Bulk Archive Status Model
bulk_archive_status_model = ns.model('BulkArchiveStatus', {
    'total_stories': fields.Integer(description='Total stories processed'),
    'successful': fields.Integer(description='Successfully archived stories'),
    'skipped': fields.Integer(description='Skipped stories (already archived)'),
    'failed': fields.Integer(description='Failed archive operations'),
    'warnings': fields.Integer(description='Stories with warnings'),
    'details': fields.List(fields.Raw, description='Detailed results for each story')
})

# Archived Story Model
archived_story_model = ns.model('ArchivedStory', {
    'story_id': fields.String(description='Story ID'),
    'title': fields.String(description='Story title'),
    'archive_path': fields.String(description='Archive directory path'),
    'archive_date': fields.String(description='Archive date (YYYY-MM-DD)'),
    'archive_time': fields.DateTime(description='When the archive was created'),
    'metadata': fields.Raw(description='Story metadata')
})

@ns.route('/story/<int:story_id>')
class StoryArchive(Resource):
    @require_auth_or_api_key(['admin'])
    @ns.marshal_with(archive_status_model)
    def post(self, story_id):
        """Archive a specific story and its media files"""
        try:
            # Get story from database
            story = Story.query.get(story_id)
            if not story:
                ns.abort(404, message="Story not found")

            # Get force_rearchive parameter
            force_rearchive = request.args.get('force', 'false').lower() == 'true'

            # Initialize archive service
            archive_service = ArchiveService()

            # Archive the story
            result = archive_service.archive_story(story, force_rearchive)

            # Determine HTTP status code based on result
            status_code = 200
            if result['status'] == 'error':
                status_code = 500
            elif result['status'] == 'warning':
                status_code = 202  # Accepted but with warnings

            return result, status_code

        except Exception as e:
            logger.error(f"Error archiving story {story_id}: {str(e)}")
            ns.abort(500, message=f"Archive operation failed: {str(e)}")

@ns.route('/completed')
class CompletedStoriesArchive(Resource):
    @require_auth_or_api_key(['admin'])
    @ns.marshal_with(bulk_archive_status_model)
    def post(self):
        """Archive all completed stories"""
        try:
            # Get all completed stories
            completed_stories = Story.query.filter_by(current_step=WorkflowStep.COMPLETED).all()

            if not completed_stories:
                return {
                    'total_stories': 0,
                    'successful': 0,
                    'skipped': 0,
                    'failed': 0,
                    'warnings': 0,
                    'details': [],
                    'message': 'No completed stories found to archive'
                }, 200

            # Get force_rearchive parameter
            force_rearchive = request.args.get('force', 'false').lower() == 'true'

            # Initialize archive service
            archive_service = ArchiveService()

            # Archive all completed stories
            result = archive_service.archive_multiple_stories(completed_stories, force_rearchive)

            logger.info(f"Bulk archive operation completed: {result['successful']} successful, "
                       f"{result['failed']} failed, {result['skipped']} skipped")

            return result, 200

        except Exception as e:
            logger.error(f"Error in bulk archive operation: {str(e)}")
            ns.abort(500, message=f"Bulk archive operation failed: {str(e)}")

@ns.route('/list')
class ArchivedStoriesList(Resource):
    @require_auth_or_api_key(['admin'])
    @ns.marshal_with(archived_story_model, as_list=True)
    def get(self):
        """Get list of all archived stories"""
        try:
            # Initialize archive service
            archive_service = ArchiveService()

            # Get archived stories
            archived_stories = archive_service.get_archived_stories()

            logger.info(f"Retrieved {len(archived_stories)} archived stories")

            return archived_stories, 200

        except Exception as e:
            logger.error(f"Error retrieving archived stories list: {str(e)}")
            ns.abort(500, message=f"Failed to retrieve archived stories: {str(e)}")

@ns.route('/status')
class ArchiveStatus(Resource):
    @require_auth_or_api_key(['admin'])
    def get(self):
        """Get archive system status and statistics"""
        try:
            # Initialize archive service
            archive_service = ArchiveService()

            # Get counts from database
            total_stories = Story.query.count()
            completed_stories = Story.query.filter_by(current_step=WorkflowStep.COMPLETED).count()
            failed_stories = Story.query.filter_by(current_step=WorkflowStep.FAILED).count()

            # Get archived stories count
            archived_stories = archive_service.get_archived_stories()
            archived_count = len(archived_stories)

            # Calculate statistics
            completion_rate = (completed_stories / total_stories * 100) if total_stories > 0 else 0
            archive_rate = (archived_count / completed_stories * 100) if completed_stories > 0 else 0

            status_info = {
                'archive_base_path': str(archive_service.archive_base),
                'archive_exists': archive_service.archive_base.exists(),
                'statistics': {
                    'total_stories': total_stories,
                    'completed_stories': completed_stories,
                    'failed_stories': failed_stories,
                    'archived_stories': archived_count,
                    'completion_rate': round(completion_rate, 2),
                    'archive_rate': round(archive_rate, 2),
                    'unarchived_completed': completed_stories - archived_count
                },
                'recent_archives': archived_stories[:5] if archived_stories else []
            }

            return status_info, 200

        except Exception as e:
            logger.error(f"Error retrieving archive status: {str(e)}")
            ns.abort(500, message=f"Failed to retrieve archive status: {str(e)}")

@ns.route('/cleanup')
class ArchiveCleanup(Resource):
    @require_auth_or_api_key(['admin'])
    def post(self):
        """Clean up empty or invalid archive directories"""
        try:
            # Initialize archive service
            archive_service = ArchiveService()

            cleaned_count = 0
            errors = []

            if archive_service.archive_base.exists():
                for archive_dir in archive_service.archive_base.iterdir():
                    if archive_dir.is_dir():
                        try:
                            # Check if directory appears to be an archive but is empty or invalid
                            if archive_dir.name.startswith(('20', '19')):  # Date-based directories
                                contents = list(archive_dir.iterdir())
                                if len(contents) == 0:
                                    # Empty archive directory
                                    archive_dir.rmdir()
                                    cleaned_count += 1
                                    logger.info(f"Removed empty archive directory: {archive_dir}")
                                elif len(contents) < 2:  # Should have at least markdown + metadata
                                    # Incomplete archive
                                    import shutil
                                    shutil.rmtree(archive_dir)
                                    cleaned_count += 1
                                    logger.info(f"Removed incomplete archive directory: {archive_dir}")
                        except Exception as e:
                            error_msg = f"Error cleaning {archive_dir}: {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg)

            result = {
                'cleaned_directories': cleaned_count,
                'errors': errors,
                'message': f"Cleaned up {cleaned_count} archive directories"
            }

            if errors:
                result['message'] += f" ({len(errors)} errors occurred)"

            return result, 200

        except Exception as e:
            logger.error(f"Error in archive cleanup: {str(e)}")
            ns.abort(500, message=f"Archive cleanup failed: {str(e)}")