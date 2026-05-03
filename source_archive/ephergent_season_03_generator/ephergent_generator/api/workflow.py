from flask import current_app
from flask_restx import Namespace, Resource, fields
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services import workflow_service

# Create a workflow namespace
ns = Namespace('workflow', description='Story workflow management')

# Workflow Step Model
workflow_step_model = ns.model('WorkflowStep', {
    'step': fields.String(required=True, description='Current workflow step'),
    'status': fields.String(description='Status of the current step'),
    'started_at': fields.DateTime(description='Step start timestamp'),
    'completed_at': fields.DateTime(description='Step completion timestamp'),
    'details': fields.Raw(description='Additional workflow details')
})

# Workflow Status Model
workflow_status_model = ns.model('WorkflowStatus', {
    'story_id': fields.Integer(required=True, description='Story ID'),
    'current_step': fields.String(description='Current workflow step'),
    'total_steps': fields.Integer(description='Total workflow steps'),
    'progress_percentage': fields.Float(description='Workflow progress percentage'),
    'status': fields.String(description='Overall workflow status'),
    'steps': fields.List(fields.Nested(workflow_step_model), description='Detailed workflow steps')
})

@ns.route('/<int:story_id>/status')
class WorkflowStatus(Resource):
    @ns.marshal_with(workflow_status_model)
    def get(self, story_id):
        """Get detailed workflow status for a story"""
        story = Story.query.get_or_404(story_id)
        
        try:
            # Get workflow status from service
            workflow_status = workflow_service.get_workflow_status(story)
            return workflow_status, 200
        
        except Exception as e:
            current_app.logger.error(f"Workflow status error: {str(e)}")
            ns.abort(500, message="An error occurred while retrieving workflow status")

@ns.route('/<int:story_id>/steps')
class WorkflowSteps(Resource):
    @ns.marshal_with(workflow_step_model, as_list=True)
    def get(self, story_id):
        """Get all workflow steps for a story"""
        story = Story.query.get_or_404(story_id)
        
        try:
            # Retrieve workflow steps from service
            workflow_steps = workflow_service.get_workflow_steps(story)
            return workflow_steps, 200
        
        except Exception as e:
            current_app.logger.error(f"Workflow steps retrieval error: {str(e)}")
            ns.abort(500, message="An error occurred while retrieving workflow steps")

@ns.route('/<int:story_id>/retry')
class WorkflowRetry(Resource):
    def post(self, story_id):
        """Retry failed workflow step for a story"""
        story = Story.query.get_or_404(story_id)
        
        try:
            # Check if story is in a failed state
            if story.current_step != WorkflowStep.FAILED:
                ns.abort(400, message="Story is not in a failed state")
            
            # Retry workflow
            workflow_service.retry_workflow(story)
            
            return {'message': 'Workflow retry initiated successfully'}, 200
        
        except Exception as e:
            current_app.logger.error(f"Workflow retry error: {str(e)}")
            ns.abort(500, message="An error occurred while retrying the workflow")