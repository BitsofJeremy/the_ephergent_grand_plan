from flask import request, current_app
from flask_restx import Namespace, Resource, fields, reqparse
from marshmallow import ValidationError
from ephergent_generator import db
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services import workflow_service
from ephergent_generator.services.queue_service import StoryQueueService
from ephergent_generator.services.auth_service import require_auth_or_api_key

# Create a namespace for stories
ns = Namespace('stories', description='Story management operations')

# Story Model for Request/Response Validation
story_model = ns.model('Story', {
    'id': fields.Integer(readonly=True, description='The unique story identifier'),
    'topic': fields.String(required=True, description='The original story topic'),
    'prompt': fields.String(description='Generated detailed prompt'),
    'title': fields.String(description='Generated story title'),
    'content': fields.String(description='Generated story content'),
    'genre': fields.String(description='Story genre'),
    'tone': fields.String(description='Story tone'),
    'word_count': fields.Integer(description='Word count of the story'),
    'current_step': fields.String(description='Current workflow step'),
    'error_message': fields.String(description='Error message if generation failed'),
    'created_at': fields.DateTime(description='Story creation timestamp'),
    'updated_at': fields.DateTime(description='Story last update timestamp'),
    'completed_at': fields.DateTime(description='Story completion timestamp'),
    'image_paths': fields.List(fields.String, description='Generated image paths')
})

# Story Creation Input Model
story_input_model = ns.model('StoryInput', {
    'topic': fields.String(required=True, description='Story topic'),
    'genre': fields.String(description='Story genre'),
    'tone': fields.String(description='Story tone'),
    'narrator_character_id': fields.String(description='Narrator character ID')
})

# Pagination Parser
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, default=1, help='Page number')
pagination_parser.add_argument('per_page', type=int, default=10, help='Items per page')

@ns.route('/')
class StoryList(Resource):
    @ns.expect(pagination_parser)
    @ns.marshal_with(story_model, as_list=True)
    def get(self):
        """
        Retrieve a list of stories with pagination.

        Returns:
            list[Story]: Paginated list of stories sorted by creation date.
            dict: Headers containing total story count and total pages.

        Query Parameters:
            page (int): Page number for pagination. Defaults to 1.
            per_page (int): Number of stories per page. Defaults to 10.
        """
        args = pagination_parser.parse_args()
        
        query = Story.query.order_by(Story.created_at.desc())
        paginated_stories = query.paginate(
            page=args['page'], 
            per_page=args['per_page'], 
            error_out=False
        )
        
        return paginated_stories.items, 200, {
            'X-Total-Count': paginated_stories.total,
            'X-Total-Pages': paginated_stories.pages
        }
    
    @ns.expect(story_input_model)
    @ns.marshal_with(story_model)
    @require_auth_or_api_key(['stories:write'])
    def post(self):
        """Create a new story for generation"""
        try:
            # Parse and validate input
            data = request.get_json()
            
            # Create new Story object
            story = Story(
                topic=data['topic'],
                genre=data.get('genre'),
                tone=data.get('tone'),
                narrator_character_id=data.get('narrator_character_id')
            )
            
            # Add to database and commit
            db.session.add(story)
            db.session.commit()
            
            # Queue the story for processing
            StoryQueueService.enqueue_story(story.id)
            
            return story, 201
        
        except ValidationError as e:
            ns.abort(400, message=str(e))
        except Exception as e:
            current_app.logger.error(f"Story creation error: {str(e)}")
            db.session.rollback()
            ns.abort(500, message="An error occurred while creating the story")

@ns.route('/<int:story_id>')
class StoryResource(Resource):
    @ns.marshal_with(story_model)
    def get(self, story_id):
        """Retrieve a specific story by ID"""
        story = Story.query.get_or_404(story_id)
        return story
    
    @require_auth_or_api_key(['stories:write'])
    def delete(self, story_id):
        """Delete a story"""
        story = Story.query.get_or_404(story_id)
        
        try:
            # Remove from queue if needed
            # Note: There's no remove_from_queue method, queue entries are handled automatically
            
            # Delete the story
            db.session.delete(story)
            db.session.commit()
            
            return {'message': 'Story deleted successfully'}, 200
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Story deletion error: {str(e)}")
            ns.abort(500, message="An error occurred while deleting the story")

@ns.route('/<int:story_id>/regenerate')
class StoryRegenerate(Resource):
    @ns.marshal_with(story_model)
    @require_auth_or_api_key(['stories:write'])
    def post(self, story_id):
        """Trigger story regeneration"""
        story = Story.query.get_or_404(story_id)
        
        try:
            # Reset story for regeneration
            story.reset_for_regeneration()
            db.session.commit()
            
            # Requeue the story
            StoryQueueService.enqueue_story(story.id)
            
            return story, 200
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Story regeneration error: {str(e)}")
            ns.abort(500, message="An error occurred while regenerating the story")

@ns.route('/search')
class StorySearch(Resource):
    @ns.expect(pagination_parser)
    @ns.marshal_with(story_model, as_list=True)
    def get(self):
        """Search stories with filters"""
        args = pagination_parser.parse_args()
        
        # Create base query
        query = Story.query
        
        # Add optional filters
        topic = request.args.get('topic')
        genre = request.args.get('genre')
        tone = request.args.get('tone')
        current_step = request.args.get('current_step')
        
        if topic:
            query = query.filter(Story.topic.ilike(f'%{topic}%'))
        if genre:
            query = query.filter(Story.genre == genre)
        if tone:
            query = query.filter(Story.tone == tone)
        if current_step:
            query = query.filter(Story.current_step == current_step)
        
        # Order by most recent first
        query = query.order_by(Story.created_at.desc())
        
        # Paginate results
        paginated_stories = query.paginate(
            page=args['page'], 
            per_page=args['per_page'], 
            error_out=False
        )
        
        return paginated_stories.items, 200, {
            'X-Total-Count': paginated_stories.total,
            'X-Total-Pages': paginated_stories.pages
        }