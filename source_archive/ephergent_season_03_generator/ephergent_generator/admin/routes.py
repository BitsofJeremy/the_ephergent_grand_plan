"""Admin routes for character and system configuration management.

Provides comprehensive administrative interfaces with proper authentication,
form validation, and database operations for managing the story generation system.
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, desc, or_
from datetime import datetime, timedelta
import logging

from ephergent_generator.admin import admin_bp
from ephergent_generator.admin.forms import (
    CharacterForm, SystemConfigForm, AdminTaskForm, DeleteConfirmForm
)
from ephergent_generator.models import (
    Character, CharacterVersion, SystemConfig, AdminTask,
    Story, WorkflowStep, StoryFailure, db
)
from ephergent_generator.services.dlq_service import dlq_service
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.queue_service import StoryQueueService

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You must be an administrator to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# Dashboard Routes
# ============================================================================

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with system statistics and quick actions."""
    # Gather statistics
    total_characters = Character.query.count()
    active_characters = Character.query.filter_by(is_active=True).count()
    total_configs = SystemConfig.query.count()

    # Recent admin tasks
    recent_tasks = AdminTask.query.order_by(desc(AdminTask.created_at)).limit(5).all()

    # Story statistics
    total_stories = Story.query.count()
    completed_stories = Story.query.filter_by(current_step=WorkflowStep.COMPLETED).count()
    failed_stories = Story.query.filter_by(current_step=WorkflowStep.FAILED).count()

    # Active tasks
    active_tasks = AdminTask.query.filter_by(task_status='running').count()

    # Phase 1.2: DLQ statistics
    dlq_pending = StoryFailure.query.filter_by(dlq_status='pending').count()
    dlq_investigating = StoryFailure.query.filter_by(dlq_status='investigating').count()
    dlq_total = StoryFailure.query.count()

    stats = {
        'characters': {
            'total': total_characters,
            'active': active_characters,
            'inactive': total_characters - active_characters
        },
        'configs': {
            'total': total_configs
        },
        'stories': {
            'total': total_stories,
            'completed': completed_stories,
            'failed': failed_stories
        },
        'tasks': {
            'active': active_tasks,
            'recent': recent_tasks
        },
        'dlq': {
            'pending': dlq_pending,
            'investigating': dlq_investigating,
            'total': dlq_total,
            'needs_attention': dlq_pending + dlq_investigating
        }
    }

    return render_template('admin/dashboard.html', stats=stats)


# ============================================================================
# Character Management Routes
# ============================================================================

@admin_bp.route('/characters')
@admin_required
def characters():
    """List all characters with filtering options."""
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()

    # Base query
    query = Character.query

    # Apply filters
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    # Apply search
    if search_query:
        query = query.filter(
            or_(
                Character.name.ilike(f'%{search_query}%'),
                Character.character_id.ilike(f'%{search_query}%')
            )
        )

    # Order by sort_order, then by name
    characters = query.order_by(Character.sort_order, Character.name).all()

    return render_template(
        'admin/characters/list.html',
        characters=characters,
        status_filter=status_filter,
        search_query=search_query
    )


@admin_bp.route('/characters/new', methods=['GET', 'POST'])
@admin_required
def character_new():
    """Create a new character."""
    form = CharacterForm()

    if form.validate_on_submit():
        try:
            # Check for duplicate character_id
            existing = Character.query.filter_by(
                character_id=form.character_id.data
            ).first()
            if existing:
                flash(f'Character ID "{form.character_id.data}" already exists.', 'error')
                return render_template('admin/characters/new.html', form=form)

            # If this is set as default, unset other defaults
            if form.is_default.data:
                Character.query.filter_by(is_default=True).update({'is_default': False})

            # Create character
            character = Character(
                character_id=form.character_id.data,
                name=form.name.data,
                email=form.email.data,
                personality_prompt=form.personality_prompt.data,
                stable_diffusion_prompt=form.stable_diffusion_prompt.data,
                voice_model=form.voice_model.data,
                ai_model=form.ai_model.data,
                is_default=form.is_default.data,
                is_active=form.is_active.data,
                sort_order=form.sort_order.data or 0,
                created_by=current_user.id,
                updated_by=current_user.id
            )

            # Set topics and tags
            character.set_topics(form.topics.data)
            character.set_tags(form.tags.data)

            db.session.add(character)
            db.session.commit()

            logger.info(f"Character created: {character.character_id} by user {current_user.username}")
            flash(f'Character "{character.name}" created successfully!', 'success')
            return redirect(url_for('admin.characters'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating character: {str(e)}")
            flash(f'Error creating character: {str(e)}', 'error')

    return render_template('admin/characters/new.html', form=form)


@admin_bp.route('/characters/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def character_edit(id):
    """Edit an existing character. ."""
    character = Character.query.get_or_404(id)
    form = CharacterForm(obj=character)

    if request.method == 'GET':
        # Pre-populate form with character data
        form.topics.data = character.topics
        form.tags.data = character.tags

    if form.validate_on_submit():
        try:
            # Check for duplicate character_id (excluding current character)
            existing = Character.query.filter(
                Character.character_id == form.character_id.data,
                Character.id != id
            ).first()
            if existing:
                flash(f'Character ID "{form.character_id.data}" already exists.', 'error')
                return render_template('admin/characters/edit.html', form=form, character=character)

            # Create version snapshot before changes
            snapshot = character.create_version_snapshot(
                user_id=current_user.id,
                change_description=f"Updated by {current_user.username}"
            )
            db.session.add(snapshot)

            # If this is set as default, unset other defaults
            if form.is_default.data and not character.is_default:
                Character.query.filter(
                    Character.is_default == True,
                    Character.id != id
                ).update({'is_default': False})

            # Update character
            character.character_id = form.character_id.data
            character.name = form.name.data
            character.email = form.email.data
            character.personality_prompt = form.personality_prompt.data
            character.stable_diffusion_prompt = form.stable_diffusion_prompt.data
            character.voice_model = form.voice_model.data
            character.ai_model = form.ai_model.data
            character.is_default = form.is_default.data
            character.is_active = form.is_active.data
            character.sort_order = form.sort_order.data or 0
            character.updated_by = current_user.id

            # Update topics and tags
            character.set_topics(form.topics.data)
            character.set_tags(form.tags.data)

            db.session.commit()

            logger.info(f"Character updated: {character.character_id} by user {current_user.username}")
            flash(f'Character "{character.name}" updated successfully!', 'success')
            return redirect(url_for('admin.characters'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating character: {str(e)}")
            flash(f'Error updating character: {str(e)}', 'error')

    return render_template('admin/characters/edit.html', form=form, character=character)


@admin_bp.route('/characters/<int:id>/toggle', methods=['POST'])
@admin_required
def character_toggle(id):
    """Toggle character active status (AJAX endpoint)."""
    character = Character.query.get_or_404(id)

    try:
        character.is_active = not character.is_active
        character.updated_by = current_user.id
        db.session.commit()

        logger.info(f"Character {character.character_id} status toggled to {character.is_active}")

        return jsonify({
            'success': True,
            'is_active': character.is_active,
            'message': f'Character {"activated" if character.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling character status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/characters/<int:id>/delete', methods=['POST'])
@admin_required
def character_delete(id):
    """Delete a character."""
    character = Character.query.get_or_404(id)

    try:
        character_name = character.name
        db.session.delete(character)
        db.session.commit()

        logger.info(f"Character deleted: {character.character_id} by user {current_user.username}")
        flash(f'Character "{character_name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting character: {str(e)}")
        flash(f'Error deleting character: {str(e)}', 'error')

    return redirect(url_for('admin.characters'))


@admin_bp.route('/characters/<int:id>/versions')
@admin_required
def character_versions(id):
    """View character version history."""
    character = Character.query.get_or_404(id)
    versions = character.versions.all()

    return render_template(
        'admin/characters/versions.html',
        character=character,
        versions=versions
    )


@admin_bp.route('/characters/images')
@admin_required
def character_images():
    """Character image generation management interface."""
    return render_template('admin/character_management.html')


# ============================================================================
# System Configuration Routes
# ============================================================================

@admin_bp.route('/config')
@admin_required
def config():
    """List all system configurations grouped by category."""
    category_filter = request.args.get('category', 'all')
    search_query = request.args.get('q', '').strip()

    # Base query
    query = SystemConfig.query

    # Apply filters
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)

    # Apply search
    if search_query:
        query = query.filter(
            or_(
                SystemConfig.config_key.ilike(f'%{search_query}%'),
                SystemConfig.description.ilike(f'%{search_query}%')
            )
        )

    # Order by category, then key
    configs = query.order_by(SystemConfig.category, SystemConfig.config_key).all()

    # Group by category
    configs_by_category = {}
    configs_by_category_dict = {}
    for config in configs:
        cat = config.category or 'uncategorized'
        if cat not in configs_by_category:
            configs_by_category[cat] = []
            configs_by_category_dict[cat] = []
        configs_by_category[cat].append(config)
        configs_by_category_dict[cat].append(config.to_dict(include_sensitive=True))

    return render_template(
        'admin/config/list.html',
        configs_by_category=configs_by_category,
        configs_by_category_dict=configs_by_category_dict,
        category_filter=category_filter,
        search_query=search_query
    )


@admin_bp.route('/config/new', methods=['GET', 'POST'])
@admin_required
def config_new():
    """Create a new system configuration."""
    form = SystemConfigForm()

    if form.validate_on_submit():
        try:
            # Check for duplicate key
            existing = SystemConfig.query.filter_by(
                config_key=form.config_key.data
            ).first()
            if existing:
                flash(f'Configuration key "{form.config_key.data}" already exists.', 'error')
                return render_template('admin/config/new.html', form=form)

            # Create config
            config = SystemConfig.set_config(
                key=form.config_key.data,
                value=form.config_value.data,
                config_type=form.config_type.data,
                description=form.description.data,
                category=form.category.data,
                is_public=form.is_public.data,
                user_id=current_user.id
            )

            db.session.commit()

            logger.info(f"Config created: {config.config_key} by user {current_user.username}")
            flash(f'Configuration "{config.config_key}" created successfully!', 'success')
            return redirect(url_for('admin.config'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating configuration: {str(e)}")
            flash(f'Error creating configuration: {str(e)}', 'error')

    return render_template('admin/config/new.html', form=form)


@admin_bp.route('/config/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def config_edit(id):
    """Edit an existing system configuration."""
    config = SystemConfig.query.get_or_404(id)
    form = SystemConfigForm(obj=config)

    if request.method == 'GET':
        # Pre-populate form with raw config value
        form.config_value.data = config.config_value

    if form.validate_on_submit():
        try:
            # Check for duplicate key (excluding current config)
            existing = SystemConfig.query.filter(
                SystemConfig.config_key == form.config_key.data,
                SystemConfig.id != id
            ).first()
            if existing:
                flash(f'Configuration key "{form.config_key.data}" already exists.', 'error')
                return render_template('admin/config/edit.html', form=form, config=config)

            # Update config
            config.config_key = form.config_key.data
            config.set_value(form.config_value.data, form.config_type.data)
            config.description = form.description.data
            config.category = form.category.data
            config.is_public = form.is_public.data
            config.updated_by = current_user.id

            db.session.commit()

            logger.info(f"Config updated: {config.config_key} by user {current_user.username}")
            flash(f'Configuration "{config.config_key}" updated successfully!', 'success')
            return redirect(url_for('admin.config'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating configuration: {str(e)}")
            flash(f'Error updating configuration: {str(e)}', 'error')

    return render_template('admin/config/edit.html', form=form, config=config)


@admin_bp.route('/config/<int:id>/delete', methods=['POST'])
@admin_required
def config_delete(id):
    """Delete a system configuration."""
    config = SystemConfig.query.get_or_404(id)

    try:
        config_key = config.config_key
        db.session.delete(config)
        db.session.commit()

        logger.info(f"Config deleted: {config_key} by user {current_user.username}")
        flash(f'Configuration "{config_key}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting configuration: {str(e)}")
        flash(f'Error deleting configuration: {str(e)}', 'error')

    return redirect(url_for('admin.config'))


# ============================================================================
# Admin Task Routes
# ============================================================================

@admin_bp.route('/tasks')
@admin_required
def tasks():
    """List and monitor administrative tasks."""
    status_filter = request.args.get('status', 'all')

    # Base query
    query = AdminTask.query

    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(task_status=status_filter)

    # Order by created_at descending
    tasks = query.order_by(desc(AdminTask.created_at)).limit(50).all()

    return render_template(
        'admin/tasks/list.html',
        tasks=tasks,
        status_filter=status_filter
    )


@admin_bp.route('/tasks/new', methods=['GET', 'POST'])
@admin_required
def task_new():
    """Create a new administrative task."""
    form = AdminTaskForm()

    if form.validate_on_submit():
        try:
            # Create task
            task = AdminTask(
                task_type=form.task_type.data,
                task_status='pending',
                started_by=current_user.id
            )

            # Set parameters if provided
            if form.task_params.data:
                task.set_params(form.task_params.data)

            db.session.add(task)
            db.session.commit()

            logger.info(f"Admin task created: {task.task_type} (ID: {task.id}) by user {current_user.username}")
            flash(f'Task "{task.task_type}" created successfully! Task ID: {task.id}', 'success')
            return redirect(url_for('admin.tasks'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating task: {str(e)}")
            flash(f'Error creating task: {str(e)}', 'error')

    return render_template('admin/tasks/new.html', form=form)


@admin_bp.route('/tasks/<int:id>')
@admin_required
def task_detail(id):
    """View task details and progress."""
    task = AdminTask.query.get_or_404(id)
    return render_template('admin/tasks/detail.html', task=task)


@admin_bp.route('/tasks/<int:id>/cancel', methods=['POST'])
@admin_required
def task_cancel(id):
    """Cancel a pending or running task."""
    task = AdminTask.query.get_or_404(id)

    try:
        task.cancel_task()
        db.session.commit()

        logger.info(f"Task cancelled: {task.task_type} (ID: {task.id}) by user {current_user.username}")
        flash(f'Task cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling task: {str(e)}")
        flash(f'Error cancelling task: {str(e)}', 'error')

    return redirect(url_for('admin.tasks'))


# ============================================================================
# AJAX/API Routes for Dynamic Updates
# ============================================================================

@admin_bp.route('/api/task/<int:id>/status')
@admin_required
def api_task_status(id):
    """Get task status for AJAX polling."""
    task = AdminTask.query.get_or_404(id)
    return jsonify(task.to_dict())


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """Get dashboard statistics for AJAX refresh."""
    total_characters = Character.query.count()
    active_characters = Character.query.filter_by(is_active=True).count()
    total_configs = SystemConfig.query.count()
    total_stories = Story.query.count()
    completed_stories = Story.query.filter_by(current_step=WorkflowStep.COMPLETED).count()
    active_tasks = AdminTask.query.filter_by(task_status='running').count()

    return jsonify({
        'characters': {
            'total': total_characters,
            'active': active_characters,
            'inactive': total_characters - active_characters
        },
        'configs': {
            'total': total_configs
        },
        'stories': {
            'total': total_stories,
            'completed': completed_stories
        },
        'tasks': {
            'active': active_tasks
        }
    })


# ============================================================================
# DLQ (Dead Letter Queue) Management Routes - Phase 1.2
# ============================================================================

@admin_bp.route('/dlq')
@admin_required
def dlq_list():
    """List failed stories in the Dead Letter Queue with filtering."""
    status_filter = request.args.get('status', 'pending')
    error_type_filter = request.args.get('error_type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 25

    # Base query
    query = StoryFailure.query

    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(dlq_status=status_filter)

    if error_type_filter != 'all':
        query = query.filter_by(error_type=error_type_filter)

    # Order by priority (high to low) then creation time (newest first)
    query = query.order_by(desc(StoryFailure.priority), desc(StoryFailure.created_at))

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    failures = pagination.items

    # Get unique error types for filter dropdown
    error_types = db.session.query(StoryFailure.error_type).distinct().all()
    error_types = [et[0] for et in error_types if et[0]]

    # Get counts by status
    status_counts = {
        'pending': StoryFailure.query.filter_by(dlq_status='pending').count(),
        'investigating': StoryFailure.query.filter_by(dlq_status='investigating').count(),
        'resolved': StoryFailure.query.filter_by(dlq_status='resolved').count(),
        'archived': StoryFailure.query.filter_by(dlq_status='archived').count(),
    }

    return render_template(
        'admin/dlq/list.html',
        failures=failures,
        pagination=pagination,
        status_filter=status_filter,
        error_type_filter=error_type_filter,
        error_types=error_types,
        status_counts=status_counts
    )


@admin_bp.route('/dlq/<int:id>')
@admin_required
def dlq_detail(id):
    """View detailed information about a DLQ failure."""
    failure = StoryFailure.query.get_or_404(id)
    return render_template('admin/dlq/detail.html', failure=failure)


@admin_bp.route('/dlq/<int:id>/retry', methods=['POST'])
@admin_required
def dlq_retry(id):
    """Retry a failed story from the DLQ."""
    failure = StoryFailure.query.get_or_404(id)

    try:
        if not failure.can_retry:
            flash('This failure cannot be retried automatically. Manual intervention required.', 'error')
            return redirect(url_for('admin.dlq_detail', id=id))

        # Retry the story
        story = dlq_service.retry_from_dlq(id)

        # Re-enqueue the story
        queue_service = StoryQueueService()
        queue_service.enqueue_story(story.id, priority=2)  # High priority for manual retries

        logger.info(f"Story {story.id} retried from DLQ (failure_id={id}) by user {current_user.username}")
        flash(f'Story "{story.topic[:50]}..." has been reset and re-queued for retry.', 'success')

        return redirect(url_for('admin.dlq_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error retrying story from DLQ: {str(e)}")
        flash(f'Error retrying story: {str(e)}', 'error')
        return redirect(url_for('admin.dlq_detail', id=id))


@admin_bp.route('/dlq/<int:id>/resolve', methods=['POST'])
@admin_required
def dlq_resolve(id):
    """Mark a DLQ failure as resolved."""
    failure = StoryFailure.query.get_or_404(id)
    notes = request.form.get('resolution_notes', '').strip()

    try:
        dlq_service.resolve_failure(id, current_user.id, notes)

        logger.info(f"DLQ failure {id} resolved by user {current_user.username}")
        flash('Failure marked as resolved.', 'success')

        return redirect(url_for('admin.dlq_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resolving DLQ failure: {str(e)}")
        flash(f'Error resolving failure: {str(e)}', 'error')
        return redirect(url_for('admin.dlq_detail', id=id))


@admin_bp.route('/dlq/<int:id>/investigating', methods=['POST'])
@admin_required
def dlq_investigating(id):
    """Mark a DLQ failure as under investigation."""
    failure = StoryFailure.query.get_or_404(id)

    try:
        failure.mark_investigating()
        db.session.commit()

        logger.info(f"DLQ failure {id} marked as investigating by user {current_user.username}")
        flash('Failure marked as under investigation.', 'success')

        return redirect(url_for('admin.dlq_detail', id=id))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating DLQ failure: {str(e)}")
        flash(f'Error updating failure: {str(e)}', 'error')
        return redirect(url_for('admin.dlq_detail', id=id))


@admin_bp.route('/dlq/<int:id>/archive', methods=['POST'])
@admin_required
def dlq_archive(id):
    """Archive a DLQ failure (no longer needs attention)."""
    failure = StoryFailure.query.get_or_404(id)

    try:
        failure.archive()
        db.session.commit()

        logger.info(f"DLQ failure {id} archived by user {current_user.username}")
        flash('Failure archived successfully.', 'success')

        return redirect(url_for('admin.dlq_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error archiving DLQ failure: {str(e)}")
        flash(f'Error archiving failure: {str(e)}', 'error')
        return redirect(url_for('admin.dlq_detail', id=id))


# ============================================================================
# Monitoring Routes
# ============================================================================

@admin_bp.route('/monitoring/grafana')
@admin_required
def grafana_dashboard():
    """Display Grafana monitoring dashboard."""
    grafana_url = current_app.config.get('GRAFANA_URL', 'http://localhost:3000')

    # Construct the embedded dashboard URL
    # Dashboard UID: ephergent-story-gen
    # Dashboard slug: ephergent-story-generator-production-monitoring
    dashboard_uid = 'ephergent-story-gen'
    dashboard_slug = 'ephergent-story-generator-production-monitoring'

    # Build the full embedded URL with kiosk mode for clean iframe display
    # Parameters:
    #   - orgId=1: Default organization
    #   - kiosk=tv: TV mode (removes Grafana chrome for embedding)
    #   - refresh=30s: Auto-refresh every 30 seconds
    embedded_url = f"{grafana_url}/d/{dashboard_uid}/{dashboard_slug}?orgId=1&refresh=30s&kiosk=tv"

    return render_template(
        'admin/monitoring/grafana.html',
        grafana_url=grafana_url,
        embedded_url=embedded_url
    )
