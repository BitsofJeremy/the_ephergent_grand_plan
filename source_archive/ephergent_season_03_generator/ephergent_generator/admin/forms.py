"""WTForms for admin blueprint.

Provides form definitions with comprehensive validation for:
- Character creation and editing
- System configuration management
- Administrative task creation
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, BooleanField,
    IntegerField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Optional, Length, NumberRange, ValidationError
)
import json


class TagListField(TextAreaField):
    """Custom field for comma-separated tags that converts to/from JSON list."""

    def _value(self):
        if self.data:
            if isinstance(self.data, str):
                try:
                    data_list = json.loads(self.data)
                    return ', '.join(data_list)
                except (json.JSONDecodeError, TypeError):
                    return self.data
            elif isinstance(self.data, list):
                return ', '.join(self.data)
        return ''

    def process_formdata(self, valuelist):
        if valuelist:
            # Split by comma and strip whitespace
            tags = [tag.strip() for tag in valuelist[0].split(',') if tag.strip()]
            self.data = json.dumps(tags) if tags else None
        else:
            self.data = None


def validate_json(form, field):
    """Validate that a field contains valid JSON."""
    if field.data:
        try:
            json.loads(field.data)
        except json.JSONDecodeError as e:
            raise ValidationError(f'Invalid JSON: {str(e)}')


class CharacterForm(FlaskForm):
    """Form for creating and editing characters."""

    character_id = StringField(
        'Character ID',
        validators=[
            DataRequired(message='Character ID is required'),
            Length(min=3, max=100, message='Character ID must be between 3 and 100 characters')
        ],
        description='Unique identifier for the character (e.g., "dr_quinn", "the_architect")'
    )

    name = StringField(
        'Display Name',
        validators=[
            DataRequired(message='Name is required'),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters')
        ],
        description='Human-readable character name'
    )

    email = StringField(
        'Email',
        validators=[Optional(), Email(message='Invalid email address')],
        description='Character email address (optional)'
    )

    personality_prompt = TextAreaField(
        'Personality Prompt',
        validators=[
            DataRequired(message='Personality prompt is required'),
            Length(min=50, message='Personality prompt should be at least 50 characters')
        ],
        description='AI personality configuration - defines how the character thinks and writes',
        render_kw={'rows': 10, 'placeholder': 'Describe the character\'s personality, voice, and narrative style...'}
    )

    stable_diffusion_prompt = TextAreaField(
        'Stable Diffusion Prompt',
        validators=[Optional()],
        description='Image generation prompt for creating character profile images',
        render_kw={'rows': 5, 'placeholder': 'Portrait of...'}
    )

    voice_model = StringField(
        'Voice Model',
        validators=[Optional(), Length(max=500)],
        description='Text-to-speech voice model for audio generation. Supports multi-voice blending: e.g., "am_onyx(0.5)+bm_v0george(1.3)+bm_lewis(0.7)"',
        render_kw={'placeholder': 'bm_george(1)+am_adam(0.6) or single voice like bm_lewis'}
    )

    ai_model = SelectField(
        'AI Model',
        choices=[
            ('gemini-2.0-flash-exp', 'Gemini 2.0 Flash (Experimental)'),
            ('gemini-2.5-flash', 'Gemini 2.5 Flash'),
            ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
            ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
        ],
        default='gemini-2.5-flash',
        validators=[DataRequired()],
        description='AI model for content generation'
    )

    topics = TagListField(
        'Topics',
        validators=[Optional()],
        description='Comma-separated list of topics this character covers',
        render_kw={'rows': 2, 'placeholder': 'quantum physics, philosophy, art, technology'}
    )

    tags = TagListField(
        'Tags',
        validators=[Optional()],
        description='Comma-separated list of metadata tags',
        render_kw={'rows': 2, 'placeholder': 'scientist, narrator, dimension-traveler'}
    )

    is_default = BooleanField(
        'Set as Default Character',
        description='Use this character as the default narrator for new stories'
    )

    is_active = BooleanField(
        'Active',
        default=True,
        description='Active characters appear in character selection'
    )

    sort_order = IntegerField(
        'Sort Order',
        validators=[Optional(), NumberRange(min=0, max=9999)],
        default=0,
        description='Display order (lower numbers appear first)'
    )

    submit = SubmitField('Save Character')


class SystemConfigForm(FlaskForm):
    """Form for creating and editing system configuration."""

    config_key = StringField(
        'Configuration Key',
        validators=[
            DataRequired(message='Configuration key is required'),
            Length(min=3, max=200, message='Key must be between 3 and 200 characters')
        ],
        description='Unique configuration key (e.g., "universe.default_dimension")',
        render_kw={'placeholder': 'category.setting_name'}
    )

    config_value = TextAreaField(
        'Configuration Value',
        validators=[Optional()],
        description='Configuration value (format depends on type)',
        render_kw={'rows': 6, 'placeholder': 'Enter configuration value...'}
    )

    config_type = SelectField(
        'Value Type',
        choices=[
            ('string', 'String (Text)'),
            ('text', 'Text (Multi-line)'),
            ('json', 'JSON (Structured Data)'),
            ('markdown', 'Markdown (Formatted Text)'),
            ('int', 'Integer (Whole Number)'),
            ('float', 'Float (Decimal Number)'),
            ('bool', 'Boolean (True/False)'),
        ],
        default='string',
        validators=[DataRequired()],
        description='Data type for value interpretation'
    )

    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=1000)],
        description='Human-readable description of this configuration',
        render_kw={'rows': 3, 'placeholder': 'Describe what this configuration controls...'}
    )

    category = SelectField(
        'Category',
        choices=[
            ('', '-- Select Category --'),
            ('universe_prompts', 'Universe Prompts'),
            ('api_settings', 'API Settings'),
            ('media_settings', 'Media Generation Settings'),
            ('workflow_settings', 'Workflow Settings'),
            ('publishing_settings', 'Publishing Settings'),
            ('system', 'System Configuration'),
        ],
        validators=[Optional()],
        description='Logical grouping for this configuration'
    )

    is_public = BooleanField(
        'Public Configuration',
        description='Allow non-admin users to read this value'
    )

    submit = SubmitField('Save Configuration')

    def validate_config_value(self, field):
        """Validate config_value based on config_type."""
        if field.data and self.config_type.data:
            if self.config_type.data == 'json':
                try:
                    json.loads(field.data)
                except json.JSONDecodeError as e:
                    raise ValidationError(f'Invalid JSON: {str(e)}')
            elif self.config_type.data == 'int':
                try:
                    int(field.data)
                except (ValueError, TypeError):
                    raise ValidationError('Value must be a valid integer')
            elif self.config_type.data == 'float':
                try:
                    float(field.data)
                except (ValueError, TypeError):
                    raise ValidationError('Value must be a valid number')
            elif self.config_type.data == 'bool':
                if field.data.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 't', 'f'):
                    raise ValidationError('Value must be a boolean (true/false)')


class AdminTaskForm(FlaskForm):
    """Form for creating administrative tasks."""

    task_type = SelectField(
        'Task Type',
        choices=[
            ('', '-- Select Task Type --'),
            ('migrate_characters', 'Migrate Characters from JSON'),
            ('regenerate_character_images', 'Regenerate Character Images'),
            ('validate_configs', 'Validate System Configurations'),
            ('cleanup_stale_workers', 'Clean Up Stale Workers'),
            ('database_maintenance', 'Database Maintenance'),
        ],
        validators=[DataRequired(message='Task type is required')],
        description='Type of administrative task to execute'
    )

    task_params = TextAreaField(
        'Task Parameters (JSON)',
        validators=[Optional(), validate_json],
        description='Optional JSON parameters for task execution',
        render_kw={
            'rows': 5,
            'placeholder': '{"param1": "value1", "param2": "value2"}'
        }
    )

    submit = SubmitField('Create Task')


class DeleteConfirmForm(FlaskForm):
    """Simple form for delete confirmation with CSRF protection."""

    submit = SubmitField('Confirm Delete')
