from flask import render_template, request, redirect, url_for, flash, session, jsonify
from ephergent_generator.main import bp
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.queue_service import StoryQueueService
from ephergent_generator.services.character_service import CharacterService
from ephergent_generator.services.health_service import HealthService
from ephergent_generator.services.auth_service import AuthService, require_admin
from ephergent_generator import db
import uuid
import logging

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Homepage with recent stories."""
    # Get recent completed stories for display (limit to 6 most recent)
    recent_stories = Story.query.filter(
        Story.current_step == WorkflowStep.COMPLETED
    ).order_by(Story.completed_at.desc()).limit(6).all()
    return render_template('index.html', recent_stories=recent_stories)

@bp.route('/generate', methods=['GET', 'POST'])
def generate():
    """Story topic submission form and handler."""
    # Get character data for the form
    character_service = CharacterService()
    characters = character_service.get_characters_for_dropdown()
    
    if request.method == 'POST':
        try:
            # Get form data
            topic = request.form.get('topic', '').strip()
            genre = request.form.get('genre', '') or None
            tone = request.form.get('tone', '') or None
            word_count = request.form.get('word_count', '') or None
            narrator_character_id = request.form.get('narrator_character_id', '') or None
            dimension_location = request.form.get('dimension_location', '') or None
            
            # Validate required fields
            if not topic:
                flash('Please provide a story topic.', 'error')
                return render_template('generate.html', characters=characters)
            
            # If no character selected, use default character
            if not narrator_character_id:
                default_character = character_service.get_default_character()
                if default_character:
                    narrator_character_id = default_character['id']
            
            # Convert word_count to int if provided
            if word_count:
                try:
                    word_count = int(word_count)
                except ValueError:
                    word_count = None
            
            # Get or create session ID for tracking user stories
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            
            # Create story and add to workflow queue
            workflow_service = StoryWorkflowService()
            story = workflow_service.create_story_from_topic(
                topic=topic,
                genre=genre,
                tone=tone,
                word_count=word_count,
                narrator_character_id=narrator_character_id,
                dimension_location=dimension_location,
                session_id=session['session_id']
            )
            
            flash('Story submitted for generation! It will be processed shortly.', 'info')
            return redirect(url_for('main.view_story_status', id=story.id))
            
        except Exception as e:
            logger.error(f"Error submitting story: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('generate.html', characters=characters)
    
    return render_template('generate.html', characters=characters)

@bp.route('/story/<int:id>')
def view_story(id):
    """View a specific completed story."""
    story = Story.query.get_or_404(id)
    
    # Only show completed stories in the story view
    if story.current_step != WorkflowStep.COMPLETED:
        return redirect(url_for('main.view_story_status', id=id))
    
    return render_template('story.html', story=story)

@bp.route('/story/<int:id>/status')
def view_story_status(id):
    """View story status and processing progress."""
    story = Story.query.get_or_404(id)
    
    # If completed, redirect to full story view
    if story.current_step == WorkflowStep.COMPLETED:
        return redirect(url_for('main.view_story', id=id))
    
    return render_template('story_status.html', story=story)

@bp.route('/stories')
def stories():
    """List all stories for the current session."""
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of stories per page
    status_filter = request.args.get('status', 'all')  # all, completed, processing, failed
    
    # Get stories for current session if available, otherwise show all recent stories
    if 'session_id' in session:
        stories_query = Story.query.filter_by(session_id=session['session_id'])
    else:
        stories_query = Story.query
    
    # Apply status filter
    if status_filter == 'completed':
        stories_query = stories_query.filter(Story.current_step == WorkflowStep.COMPLETED)
    elif status_filter == 'processing':
        stories_query = stories_query.filter(
            Story.current_step.in_([
                WorkflowStep.QUEUED,
                WorkflowStep.STORY_GENERATION,
                WorkflowStep.TITLE_GENERATION,
                WorkflowStep.IMAGE_GENERATION,
                WorkflowStep.AUDIO_GENERATION
            ])
        )
    elif status_filter == 'failed':
        stories_query = stories_query.filter(Story.current_step == WorkflowStep.FAILED)
    
    stories = stories_query.order_by(Story.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return render_template('stories.html', stories=stories, status_filter=status_filter)

@bp.route('/queue/status')
@require_admin
def queue_status():
    """Show queue status and statistics."""
    queue_service = StoryQueueService()
    status = queue_service.get_queue_status()
    return render_template('queue_status.html', status=status)

@bp.route('/health')
@require_admin
def health_dashboard():
    """Service health dashboard web interface."""
    health_service = HealthService()
    status = health_service.get_all_service_status()
    return render_template('health_dashboard.html', status=status)

@bp.route('/api/health')
def health_api():
    """API endpoint for service health status."""
    health_service = HealthService()
    status = health_service.get_all_service_status()
    
    # Set appropriate HTTP status code based on overall health
    status_code = 200
    if status['overall_status'] == 'unhealthy':
        status_code = 503  # Service Unavailable
    elif status['overall_status'] == 'degraded':
        status_code = 206  # Partial Content
    elif status['overall_status'] == 'unknown':
        status_code = 202  # Accepted (checking)
    
    return jsonify(status), status_code

@bp.route('/api/health/quick')
def health_quick():
    """Quick health check API endpoint."""
    health_service = HealthService()
    status = health_service.get_quick_status()
    return jsonify(status)

@bp.route('/story/<int:id>/regenerate', methods=['POST'])
def regenerate_story(id):
    """Regenerate a story by resetting it and adding back to queue."""
    try:
        workflow_service = StoryWorkflowService()
        story = workflow_service.regenerate_story(id)
        
        if not story:
            flash('Story not found.', 'error')
            return redirect(url_for('main.stories'))
        
        flash(f'Story "{story.topic[:50]}..." has been reset and queued for regeneration!', 'success')
        return redirect(url_for('main.view_story_status', id=story.id))
        
    except Exception as e:
        logger.error(f"Error regenerating story {id}: {str(e)}")
        flash('An error occurred while regenerating the story.', 'error')
        return redirect(url_for('main.view_story', id=id))

@bp.route('/api/story/<int:id>/regenerate', methods=['POST'])
def api_regenerate_story(id):
    """API endpoint to regenerate a story."""
    try:
        workflow_service = StoryWorkflowService()
        story = workflow_service.regenerate_story(id)
        
        if not story:
            return jsonify({'error': 'Story not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Story queued for regeneration',
            'story_id': story.id,
            'status_url': url_for('main.view_story_status', id=story.id)
        })
        
    except Exception as e:
        logger.error(f"Error regenerating story {id}: {str(e)}")
        return jsonify({'error': 'Failed to regenerate story'}), 500

@bp.route('/story/<int:id>/edit', methods=['GET', 'POST'])
def edit_story(id):
    """Edit a story's metadata and content."""
    story = Story.query.get_or_404(id)
    character_service = CharacterService()
    characters = character_service.get_characters_for_dropdown()
    
    if request.method == 'POST':
        try:
            # Update story fields
            story.topic = request.form.get('topic', '').strip() or story.topic
            story.title = request.form.get('title', '').strip() or story.title
            story.content = request.form.get('content', '').strip() or story.content
            story.genre = request.form.get('genre', '') or None
            story.tone = request.form.get('tone', '') or None
            story.dimension_location = request.form.get('dimension_location', '') or None
            story.narrator_character_id = request.form.get('narrator_character_id', '') or None
            
            # Handle word count
            word_count = request.form.get('word_count', '')
            if word_count:
                try:
                    story.word_count = int(word_count)
                except ValueError:
                    pass  # Keep existing value
            
            db.session.commit()
            flash('Story updated successfully!', 'success')
            return redirect(url_for('main.view_story', id=story.id))
            
        except Exception as e:
            logger.error(f"Error updating story {id}: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating the story.', 'error')
    
    return render_template('edit_story.html', story=story, characters=characters)

@bp.route('/story/<int:id>/delete', methods=['POST'])
def delete_story(id):
    """Delete a story permanently."""
    try:
        story = Story.query.get_or_404(id)
        story_title = story.title or story.topic[:50]

        # Delete from database
        db.session.delete(story)
        db.session.commit()

        flash(f'Story "{story_title}..." has been deleted permanently.', 'success')
        return redirect(url_for('main.stories'))

    except Exception as e:
        logger.error(f"Error deleting story {id}: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the story.', 'error')
        return redirect(url_for('main.stories'))

# OLD CHARACTER MANAGEMENT ROUTES - Moved to admin blueprint
# These routes are now handled by ephergent_generator/admin/routes.py
# @bp.route('/admin/characters')
# @require_admin
# def admin_character_management():
#     """Character management admin interface."""
#     return render_template('admin/character_management.html')

# @bp.route('/admin/characters/<string:character_id>/regenerate', methods=['POST'])
# @require_admin
# def admin_regenerate_character_image(character_id):
#     """Web interface endpoint to regenerate a character image."""
#     try:
#         character_service = CharacterService()
#         character = character_service.get_character_by_id(character_id)

#         if not character:
#             flash(f'Character {character_id} not found.', 'error')
#             return redirect(url_for('main.admin_character_management'))

#         # Call the API endpoint internally
#         from flask import current_app
#         with current_app.test_client() as client:
#             response = client.post(f'/api/characters/{character_id}/regenerate-image')

#             if response.status_code == 202:
#                 flash(f'Image generation started for {character.get("name", character_id)}.', 'info')
#             elif response.status_code == 409:
#                 flash(f'Image generation already in progress for {character.get("name", character_id)}.', 'warning')
#             else:
#                 flash(f'Failed to start image generation for {character.get("name", character_id)}.', 'error')

#         return redirect(url_for('main.admin_character_management'))

#     except Exception as e:
#         logger.error(f"Error in admin regenerate endpoint for {character_id}: {str(e)}")
#         flash('An error occurred while starting image generation.', 'error')
#         return redirect(url_for('main.admin_character_management'))

# @bp.route('/admin/characters/regenerate-all', methods=['POST'])
# @require_admin
# def admin_regenerate_all_character_images():
#     """Web interface endpoint to regenerate all character images."""
#     try:
#         # Call the API endpoint internally
#         from flask import current_app
#         with current_app.test_client() as client:
#             response = client.post('/api/characters/regenerate-all')

#             if response.status_code == 202:
#                 data = response.get_json()
#                 flash(f'Bulk image generation started for {data.get("character_count", "all")} characters.', 'info')
#             elif response.status_code == 409:
#                 flash('Image generation already in progress for some characters.', 'warning')
#             elif response.status_code == 404:
#                 flash('No characters found to regenerate.', 'error')
#             else:
#                 flash('Failed to start bulk image generation.', 'error')

#         return redirect(url_for('main.admin_character_management'))

#     except Exception as e:
#         logger.error(f"Error in admin bulk regenerate endpoint: {str(e)}")
#         flash('An error occurred while starting bulk image generation.', 'error')
#         return redirect(url_for('main.admin_character_management'))

@bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return render_template('errors/500.html'), 500