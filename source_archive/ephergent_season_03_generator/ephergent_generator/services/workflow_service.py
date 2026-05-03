from ephergent_generator import db
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services.gemini_service import GeminiService
from ephergent_generator.services.queue_service import StoryQueueService
from ephergent_generator.services.character_service import CharacterService
from ephergent_generator.services.image_service import ImageService
from ephergent_generator.services.audio_service import AudioService
from ephergent_generator.services.video_service import VideoService
from ephergent_generator.services.youtube_service import YouTubeService
from ephergent_generator.services.ghost_service import GhostService
# Phase 1.2: Error handling and retry services
from ephergent_generator.services.retry_service import retry_service
from ephergent_generator.services.dlq_service import dlq_service
from ephergent_generator.utils.metrics import metrics_service
import logging
import uuid
import traceback
from typing import Optional, Dict, Any
from sqlalchemy.orm.exc import NoResultFound

from ephergent_generator.models import Story, WorkflowStep

logger = logging.getLogger(__name__)

class StoryWorkflowService:
    """Orchestrates the end-to-end story generation workflow.

    This service manages the complete lifecycle of story generation, from initial
    topic creation to final publishing on Ghost and YouTube. It coordinates
    multiple services like Gemini (content generation), Image, Audio, Video,
    YouTube, and Ghost to process stories through various workflow steps.

    Attributes:
        gemini_service (GeminiService): Service for AI-powered content generation.
        queue_service (StoryQueueService): Service for managing story processing queue.
        character_service (CharacterService): Service for character-related operations.
        image_service (ImageService): Service for image generation and management.
        audio_service (AudioService): Service for audio generation.
        video_service (VideoService): Service for video generation.
        youtube_service (YouTubeService): Service for YouTube video upload.
        ghost_service (GhostService): Service for Ghost blog publishing.
    """
    
    def __init__(self):
        """Initialize workflow services for story generation pipeline.

        Instantiates services required for different stages of story generation
        workflow, including content generation, media creation, and publishing.
        """
        self.gemini_service = GeminiService()
        self.queue_service = StoryQueueService()
        self.character_service = CharacterService()
        self.image_service = ImageService()
        self.audio_service = AudioService()
        self.video_service = VideoService()
        self.youtube_service = YouTubeService()
        self.ghost_service = GhostService()
    
    def create_story_from_topic(self, topic: str, genre: str = None, tone: str = None, word_count: int = 900, narrator_character_id: str = None, dimension_location: str = None, session_id: str = None) -> Story:
        """Create a new story and enqueue it for processing.

        Generates a Story record with the provided parameters and adds it to the
        processing queue for subsequent workflow steps.

        Args:
            topic (str): The main topic or theme of the story.
            genre (str, optional): Story genre (e.g., 'sci-fi', 'fantasy').
            tone (str, optional): Narrative tone (e.g., 'humorous', 'serious').
            word_count (int, optional): Desired story length in words.
            narrator_character_id (str, optional): ID of the narrator character.
            dimension_location (str, optional): Specific dimensional setting.
            session_id (str, optional): Unique identifier for the creation session.

        Returns:
            Story: The newly created and queued Story object.

        Raises:
            Exception: If story creation or database transaction fails.

        Example:
            >>> workflow_service = StoryWorkflowService()
            >>> story = workflow_service.create_story_from_topic(
            ...     topic='A robot learns to love', 
            ...     genre='sci-fi', 
            ...     tone='philosophical', 
            ...     word_count=1000
            ... )
        """
        try:
            # Create story record
            story = Story(
                topic=topic,
                genre=genre,
                tone=tone,
                narrator_character_id=narrator_character_id,
                dimension_location=dimension_location,
                current_step=WorkflowStep.QUEUED,
                session_id=session_id
            )
            
            # Store requested word count in workflow data
            if word_count:
                story.set_workflow_data({'requested_word_count': word_count})
            
            db.session.add(story)
            db.session.commit()
            
            # Add to queue
            self.queue_service.enqueue_story(story.id, priority=0)
            
            logger.info(f"Created story {story.id} with topic: {topic[:50]}...")
            return story
            
        except Exception as e:
            logger.error(f"Error creating story from topic: {str(e)}")
            db.session.rollback()
            raise
    
    def process_next_story(self, worker_id: str = None) -> Optional[Story]:
        """Process the next story in the workflow queue.

        Retrieves the next story from the queue and advances it through its current
        workflow step. Handles different processing stages based on the story's
        current workflow state.

        Args:
            worker_id (str, optional): Unique identifier for the processing worker.
                If not provided, a random worker ID will be generated.

        Returns:
            Optional[Story]: The processed story object, or None if no story is in the queue.

        Raises:
            Exception: If any critical error occurs during story processing.

        Note:
            This method is designed to be idempotent and can handle stories at
            various stages of the generation workflow, including:
            - Story generation
            - Title generation
            - Image generation
            - Audio generation
            - Video generation
            - YouTube upload
            - Ghost blog publishing
        """
        if not worker_id:
            worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        
        try:
            # Get next story from queue
            story = self.queue_service.get_next_story(worker_id)
            if not story:
                # Lower verbosity here so default INFO logging is not flooded by frequent empty-queue checks
                logger.debug(f"No stories in queue for worker {worker_id}")
                return None
            
            logger.info(f"Worker {worker_id} processing story {story.id}, current step: {story.current_step.value}")
            
            # Log story state before processing
            logger.debug(f"Story {story.id} before processing - Topic: '{story.topic[:50]}...', Title: {'SET' if story.title else 'NONE'}, Content: {'SET' if story.content else 'NONE'}")
            
            # Process based on current step
            if story.current_step == WorkflowStep.QUEUED:
                logger.info(f"Starting story generation for story {story.id}")
                success = self._process_story_generation(story)
            elif story.current_step == WorkflowStep.STORY_GENERATION:
                logger.info(f"Starting title generation for story {story.id}")
                success = self._process_title_generation(story)
            elif story.current_step == WorkflowStep.TITLE_GENERATION:
                logger.info(f"Starting title generation for story {story.id}")
                success = self._process_title_generation(story)
            elif story.current_step == WorkflowStep.IMAGE_GENERATION:
                logger.info(f"Starting image generation for story {story.id}")
                success = self._process_image_generation(story)
            elif story.current_step == WorkflowStep.AUDIO_GENERATION:
                logger.info(f"Starting audio generation for story {story.id}")
                success = self._process_audio_generation(story)
            elif story.current_step == WorkflowStep.VIDEO_GENERATION:
                logger.info(f"Starting video generation for story {story.id}")
                success = self._process_video_generation(story)
            elif story.current_step == WorkflowStep.YOUTUBE_UPLOAD:
                logger.info(f"Starting YouTube upload for story {story.id}")
                success = self._process_youtube_upload(story)
            elif story.current_step == WorkflowStep.GHOST_PUBLISHING:
                logger.info(f"Starting Ghost blog publishing for story {story.id}")
                success = self._process_ghost_publishing(story)
            elif story.current_step == WorkflowStep.COMPLETED:
                logger.info(f"Story {story.id} is already completed")
                success = True  # Story is already done
            else:
                logger.warning(f"Story {story.id} is in unexpected step: {story.current_step}")
                success = False
            
            # Log result of processing step
            logger.info(f"Story {story.id} processing step result: {'SUCCESS' if success else 'FAILED'}, new step: {story.current_step.value}")
            
            if success:
                # Phase 1.2: Reset retry state on successful step
                if story.retry_count > 0:
                    logger.info(f"Story {story.id} step succeeded after {story.retry_count} retries - resetting retry state")
                    metrics_service.record_retry_success(story.current_step.value)
                retry_service.reset_retry_state(story)

                # Commit changes
                logger.debug(f"Committing successful changes for story {story.id}")
                db.session.commit()

                # If completed, remove from queue
                if story.current_step == WorkflowStep.COMPLETED:
                    logger.info(f"Story {story.id} completed workflow, removing from queue")
                    self.queue_service.complete_story(story.id, worker_id)
                    logger.info(f"Story {story.id} completed workflow successfully")
                else:
                    # Release back to queue for next step
                    logger.info(f"Story {story.id} ready for next step ({story.current_step.value}), releasing back to queue")
                    self.queue_service.release_story(story.id, worker_id)
            else:
                # Phase 1.2: Processing failed - check if it's retrying or in DLQ
                logger.error(f"Story {story.id} processing failed")
                logger.error(f"Story {story.id} error details: {story.error_message}")

                # Commit the retry state changes
                db.session.commit()

                # Check if story is in FAILED state (moved to DLQ) or just retrying
                if story.current_step == WorkflowStep.FAILED:
                    # Story exhausted retries and is in DLQ - remove from queue
                    self.queue_service.complete_story(story.id, worker_id)
                    logger.error(f"Story {story.id} permanently failed - removed from queue and in DLQ")
                else:
                    # Story is scheduled for retry - release back to queue
                    self.queue_service.release_story(story.id, worker_id)
                    logger.info(
                        f"Story {story.id} will retry at {story.next_retry_at.isoformat() if story.next_retry_at else 'next opportunity'} "
                        f"(attempt {story.retry_count}/{story.max_retries})"
                    )
            
            return story
            
        except Exception as e:
            logger.error(f"Error processing story: {str(e)}")
            db.session.rollback()
            # Release story back to queue on error
            if 'story' in locals():
                self.queue_service.release_story(story.id, worker_id)
            raise
    
    def _process_story_generation(self, story):
        """Process the story generation step."""
        try:
            logger.info(f"Generating story content for story {story.id}")
            story.advance_workflow(WorkflowStep.STORY_GENERATION)
            
            # Get parameters
            workflow_data = story.get_workflow_data()
            requested_word_count = workflow_data.get('requested_word_count')
            
            # Build character-aware prompt with full universe context if narrator character is specified
            if story.narrator_character_id:
                # Use character service to build comprehensive prompt with universe context
                character_prompt = self.character_service.build_character_story_prompt(
                    character_id=story.narrator_character_id,
                    topic=story.topic,
                    genre=story.genre,
                    tone=story.tone,
                    word_count=requested_word_count,
                    dimension_location=story.dimension_location
                )
            else:
                character_prompt = None
            
            # Generate story content with universe context
            result = self.gemini_service.generate_story_from_topic(
                topic=story.topic,
                genre=story.genre,
                tone=story.tone,
                word_count=requested_word_count,
                character_prompt=character_prompt,
                dimension_location=story.dimension_location
            )
            
            if result.get('success'):
                # Update story with generated content
                story.content = result['content']
                story.word_count = result['word_count']
                
                # Move to next step
                story.advance_workflow(WorkflowStep.TITLE_GENERATION)
                
                logger.info(f"Story content generated for story {story.id}, {result['word_count']} words")
                return True
            else:
                error_msg = result.get('error', 'Unknown error in story generation')
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Story generation failed for story {story.id}: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Exception in story generation: {str(e)}"
            logger.error(f"Story generation exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                # Record retry attempt with exponential backoff
                retry_service.record_retry_attempt(story, e, error_msg)

                # Record metrics
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(
                    story.current_step.value,
                    error_type.value,
                    delay
                )

                logger.info(
                    f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries} "
                    f"at {story.next_retry_at.isoformat() if story.next_retry_at else 'immediately'}"
                )
                # Story stays in current step, will be retried later
                return False
            else:
                # Retry exhausted or permanent error - send to DLQ
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())

                # Record metrics
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)

                logger.error(
                    f"Story {story.id} moved to DLQ (failure_id={failure.id}): "
                    f"error_type={error_type.value}, can_retry={failure.can_retry}"
                )
                return False
    
    def _process_title_generation(self, story):
        """Process the title generation step."""
        try:
            logger.info(f"Generating title for story {story.id}")
            # Don't advance workflow step yet - only advance after successful generation
            
            # Generate title
            result = self.gemini_service.generate_title(
                topic=story.topic,
                content=story.content,
                genre=story.genre,
                tone=story.tone
            )
            
            if result.get('success'):
                # Update story with generated title
                story.title = result['title']
                
                # Advance to image generation step
                story.advance_workflow(WorkflowStep.IMAGE_GENERATION)
                
                logger.info(f"Title generated for story {story.id}: {result['title']}")
                return True
            else:
                error_msg = result.get('error', 'Unknown error in title generation')
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Title generation failed for story {story.id}: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Exception in title generation: {str(e)}"
            logger.error(f"Title generation exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _process_image_generation(self, story):
        """Process the image generation step."""
        try:
            logger.info(f"Generating images for story {story.id}")
            
            # Prepare story data for image generation
            story_data = {
                'id': story.id,
                'title': story.title,
                'content': story.content,
                'topic': story.topic,
                'genre': story.genre,
                'tone': story.tone,
                'narrator_character_id': story.narrator_character_id
            }
            
            # Generate image prompts
            image_prompts = self.image_service.generate_image_prompts(story_data)
            if not image_prompts:
                error_msg = "Failed to generate image prompts"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Image prompt generation failed for story {story.id}")
                return False
            
            # Save prompts to story
            story.set_image_prompts(image_prompts)
            
            # Generate images (currently placeholder images)
            generated_images = self.image_service.generate_story_images(story_data)
            if not generated_images:
                error_msg = "Failed to generate images"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Image generation failed for story {story.id}")
                return False
            
            # Convert image paths to web URLs and store
            image_urls = {}
            for image_type, image_path in generated_images.items():
                if image_path:
                    image_urls[image_type] = self.image_service.get_image_url(image_path)
            
            story.set_image_paths(image_urls)
            
            # Advance to audio generation
            story.advance_workflow(WorkflowStep.AUDIO_GENERATION)
            
            logger.info(f"Images generated for story {story.id}: {len(generated_images)} images")
            return True
            
        except Exception as e:
            error_msg = f"Exception in image generation: {str(e)}"
            logger.error(f"Image generation exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _process_audio_generation(self, story):
        """Process the audio generation step."""
        try:
            logger.info(f"Generating audio for story {story.id}")
            
            # Prepare story data for audio generation
            story_data = {
                'id': story.id,
                'title': story.title,
                'content': story.content,
                'topic': story.topic,
                'genre': story.genre,
                'tone': story.tone,
                'narrator_character_id': story.narrator_character_id
            }
            
            # Generate audio file
            audio_path = self.audio_service.generate_story_audio(story_data)
            if not audio_path:
                error_msg = "Failed to generate audio file"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Audio generation failed for story {story.id}")
                return False
            
            # Get web URL for audio file and store
            audio_url = self.audio_service.get_audio_url(audio_path)
            story.audio_path = audio_url
            
            # Advance to video generation
            story.advance_workflow(WorkflowStep.VIDEO_GENERATION)
            
            logger.info(f"Audio generated for story {story.id}: {audio_path}")
            return True
            
        except Exception as e:
            error_msg = f"Exception in audio generation: {str(e)}"
            logger.error(f"Audio generation exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _process_completion(self, story):
        """Process the completion step."""
        try:
            logger.info(f"Completing story {story.id}")
            
            # Debug: Log current story state
            logger.debug(f"Story {story.id} state - Title: {'YES' if story.title else 'NO'} ({len(story.title) if story.title else 0} chars), Content: {'YES' if story.content else 'NO'} ({len(story.content) if story.content else 0} chars)")
            
            # Final validation with detailed logging
            validation_errors = []
            if not story.content:
                validation_errors.append("missing content")
            if not story.title:
                validation_errors.append("missing title")
            
            if validation_errors:
                error_msg = f"Story incomplete - {', '.join(validation_errors)}"
                logger.error(f"Story {story.id} validation failed: {error_msg}")
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                return False
            
            # Mark as completed
            logger.info(f"Story {story.id} validation passed - Title: '{story.title[:50]}...', Content: {len(story.content)} chars")
            story.advance_workflow(WorkflowStep.COMPLETED)
            logger.info(f"Story {story.id} workflow completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Exception in story completion: {str(e)}"
            logger.error(f"Story completion exception for story {story.id}: {str(e)}")
            logger.exception(f"Full traceback for story {story.id} completion error:")
            story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
            return False
    
    def _process_video_generation(self, story):
        """Process the video generation step."""
        try:
            logger.info(f"Generating video for story {story.id}")
            
            # Convert web URLs to file system paths
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            
            # Convert audio path using audio service
            audio_file_path = None
            if story.audio_path:
                local_audio_path = self.audio_service.url_to_path(story.audio_path)
                if local_audio_path and local_audio_path.exists():
                    audio_file_path = str(local_audio_path)
                else:
                    logger.error(f"Audio file not found at resolved path: {local_audio_path}")
                    error_msg = "Audio file not found for video generation"
                    story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                    logger.error(f"Video generation failed for story {story.id} - audio missing")
                    return False
            
            # Convert image paths using image service
            image_paths = story.get_image_paths()
            converted_image_paths = {}
            if image_paths:
                for key, url in image_paths.items():
                    if url:
                        local_image_path = self.image_service.url_to_path(url)
                        if local_image_path and local_image_path.exists():
                            converted_image_paths[key] = str(local_image_path)
                        else:
                            logger.warning(f"Image file not found for {key}: {local_image_path}")
                            # Don't fail for missing images, just skip them
            
            # Prepare story data for video generation
            story_data = {
                'id': story.id,
                'title': story.title,
                'content': story.content,
                'topic': story.topic,
                'genre': story.genre,
                'tone': story.tone,
                'narrator_character_id': story.narrator_character_id,
                'audio_path': audio_file_path,
                'image_paths': converted_image_paths
            }
            
            # Generate video file
            video_path = self.video_service.generate_video(story_data)
            if not video_path:
                error_msg = "Failed to generate video file"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Video generation failed for story {story.id}")
                return False
            
            # Get web URL for video file and store
            video_url = self.video_service.get_video_url(video_path)
            story.video_path = video_url
            
            # Advance to YouTube upload
            story.advance_workflow(WorkflowStep.YOUTUBE_UPLOAD)
            
            logger.info(f"Video generated for story {story.id}: {video_path}")
            return True
            
        except Exception as e:
            error_msg = f"Exception in video generation: {str(e)}"
            logger.error(f"Video generation exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _process_youtube_upload(self, story):
        """Process the YouTube upload step."""
        try:
            logger.info(f"Uploading to YouTube for story {story.id}")
            
            # Verify we have required files
            if not story.video_path:
                error_msg = "No video file available for YouTube upload"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"YouTube upload failed for story {story.id}: {error_msg}")
                return False
            
            # Convert video URL back to local path for upload
            video_path = self.video_service.url_to_path(story.video_path)
            if not video_path or not video_path.exists():
                error_msg = f"Video file not found at path: {video_path}"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"YouTube upload failed for story {story.id}: {error_msg}")
                return False
            
            # Get feature image for thumbnail if available
            thumbnail_path = None
            image_paths = story.get_image_paths()
            if image_paths and 'feature' in image_paths:
                thumbnail_url = image_paths['feature']
                thumbnail_path = self.image_service.url_to_path(thumbnail_url)
                if not thumbnail_path or not thumbnail_path.exists():
                    logger.warning(f"Thumbnail file not found at path: {thumbnail_path}, uploading without thumbnail")
                    thumbnail_path = None
            
            # Prepare video metadata
            title = story.title or f"Ephergent Story: {story.topic[:50]}"
            
            # Create description using excerpt from ghost service
            story_data = {
                'title': title,
                'content': story.content,
                'narrator_character': {
                    'name': story.narrator_character_id or 'Ephergent Narrator'
                }
            }
            
            # Get excerpt from ghost service
            excerpt = self.ghost_service._generate_excerpt(story_data) if hasattr(self, 'ghost_service') and self.ghost_service else (
                story.content[:200] + "..." if story.content and len(story.content) > 200 else story.content
            )
            
            description_parts = [
                excerpt,
                "",
                "---------",
                "Website: https://ephergent.com",
                "Bluesky: https://bsky.app/profile/ephergent.com",
                "---------", 
                "THE EPHERGENT™",
                "Reality Optional, Truth Inevitable",
                "Est. All Timelines",
                "Approved by Telepathic Houseplants",
                "Pay with Crystallized Laughter",
                "---------",
            ]
            description = "\n".join(description_parts)
            
            # Prepare tags
            tags = ["ephergent", "ai-generated", "storytelling"]
            if story.genre:
                tags.append(story.genre.lower())
            if story.narrator_character_id:
                tags.append(f"narrator-{story.narrator_character_id.lower()}")
            
            # Upload to YouTube
            logger.info(f"Uploading video to YouTube: {video_path.name}")
            video_id = self.youtube_service.upload_to_youtube(
                video_file_path=video_path,
                title=title,
                description=description,
                tags=tags,
                thumbnail_path=thumbnail_path,
                category_id="24",  # Entertainment
                privacy_status="private"  # Default to private for now
            )
            
            if video_id:
                # Store YouTube information
                story.youtube_video_id = video_id
                story.youtube_url = self.youtube_service.get_video_url(video_id)
                
                # Advance to Ghost publishing
                story.advance_workflow(WorkflowStep.GHOST_PUBLISHING)
                
                logger.info(f"YouTube upload successful for story {story.id}: {story.youtube_url}")
                return True
            else:
                error_msg = "YouTube upload failed - no video ID returned"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"YouTube upload failed for story {story.id}: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Exception in YouTube upload: {str(e)}"
            logger.error(f"YouTube upload exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _process_ghost_publishing(self, story):
        """Process the Ghost blog publishing step."""
        try:
            logger.info(f"Publishing to Ghost blog for story {story.id}")
            
            # Check if Ghost service is configured
            if not self.ghost_service.is_configured():
                logger.warning(f"Ghost service not configured, skipping blog publishing for story {story.id}")
                # Advance to completion anyway since this is not a critical failure
                story.advance_workflow(WorkflowStep.COMPLETED)
                return True
            
            # Prepare story data for Ghost publishing
            story_data = self._prepare_story_data_for_ghost(story)
            
            # Create Ghost post (as draft for production safety)
            ghost_result = self.ghost_service.create_post(story_data, status="draft")
            
            if ghost_result:
                # Store Ghost post information
                story.ghost_post_id = ghost_result['post_id']
                story.ghost_post_url = ghost_result['post_url']
                story.ghost_status = ghost_result['status']
                
                # Advance to completion
                story.advance_workflow(WorkflowStep.COMPLETED)
                
                logger.info(f"Ghost publishing successful for story {story.id}: {story.ghost_post_url}")
                return True
            else:
                error_msg = "Ghost publishing failed - no post created"
                story.advance_workflow(WorkflowStep.FAILED, error=error_msg)
                logger.error(f"Ghost publishing failed for story {story.id}: {error_msg}")
                return False
                
        except Exception as e:
            error_msg = f"Exception in Ghost publishing: {str(e)}"
            logger.error(f"Ghost publishing exception for story {story.id}: {str(e)}")

            # Phase 1.2: Retry logic
            if retry_service.should_retry_story(story, e, error_msg):
                retry_service.record_retry_attempt(story, e, error_msg)
                from ephergent_generator.utils.error_classifier import error_classifier
                from datetime import datetime
                error_type, _ = error_classifier.classify_error(e, error_msg)
                delay = (story.next_retry_at - datetime.utcnow()).total_seconds() if story.next_retry_at else 0
                metrics_service.record_retry_attempt(story.current_step.value, error_type.value, delay)
                logger.info(f"Story {story.id} scheduled for retry attempt {story.retry_count}/{story.max_retries}")
                return False
            else:
                failure = dlq_service.add_to_dlq(story, e, error_msg, traceback.format_exc())
                from ephergent_generator.utils.error_classifier import error_classifier
                error_type, _ = error_classifier.classify_error(e, error_msg)
                if story.retry_count >= story.max_retries:
                    metrics_service.record_retry_exhausted(story.current_step.value, error_type.value)
                metrics_service.record_dlq_entry(error_type.value)
                logger.error(f"Story {story.id} moved to DLQ (failure_id={failure.id})")
                return False
    
    def _prepare_story_data_for_ghost(self, story):
        """Prepare story data for Ghost blog publishing"""
        
        # Get character information
        character = None
        if story.narrator_character_id:
            character = self.character_service.get_character_by_id(story.narrator_character_id)
        
        # Get image URLs from story
        image_paths = story.get_image_paths() or {}
        image_urls = {}

        # Upload images to Ghost and get URLs - include all image types
        if image_paths and isinstance(image_paths, dict):
            for image_type, local_path in image_paths.items():
                if local_path:
                    # Convert URL back to local path
                    local_file_path = self.image_service.url_to_path(local_path)
                    if local_file_path and local_file_path.exists():
                        ghost_url = self.ghost_service.upload_image(local_file_path)
                        if ghost_url:
                            image_urls[image_type] = ghost_url
                            logger.info(f"Uploaded {image_type} image to Ghost: {ghost_url}")
                        else:
                            logger.error(f"Failed to upload {image_type} image to Ghost: {local_file_path}")
                    else:
                        logger.error(f"Image file not found for {image_type}: {local_file_path}")
        
        # Upload audio to Ghost if available - with enhanced error handling
        audio_url = None
        if story.audio_path:
            logger.info(f"Story {story.id} has audio_path: {story.audio_path}")
            
            try:
                local_audio_path = self.audio_service.url_to_path(story.audio_path)
                if not local_audio_path:
                    logger.error(f"Failed to convert audio URL to path: {story.audio_path}")
                elif not local_audio_path.exists():
                    logger.error(f"Audio file not found at resolved path: {local_audio_path}")
                else:
                    logger.info(f"Uploading audio file to Ghost: {local_audio_path}")
                    audio_url = self.ghost_service.upload_audio(local_audio_path)
                    if audio_url:
                        logger.info(f"Successfully uploaded audio to Ghost: {audio_url}")
                    else:
                        logger.error(f"Ghost API failed to upload audio file: {local_audio_path}")
            except Exception as e:
                logger.error(f"Exception during audio path resolution for story {story.id}: {str(e)}")
        else:
            logger.warning(f"Story {story.id} has no audio_path set - skipping audio upload")
        
        # Prepare story data dictionary
        return {
            'title': story.title or f"Ephergent Story: {story.topic[:50]}",
            'content': story.content or '',
            'topic': story.topic,
            'genre': story.genre,
            'narrator_character': character,
            'image_urls': image_urls,
            'featured_image_url': image_urls.get('feature'),
            'audio_url': audio_url,
            'youtube_url': story.youtube_url,
            'word_count': story.word_count
        }
    
    def regenerate_story(self, story_id: int) -> Optional[Story]:
        """Reset a story's workflow and re-enqueue it for complete regeneration.

        Finds an existing story by ID, resets its state to the initial workflow
        step, and adds it back to the processing queue with higher priority.

        Args:
            story_id (int): The unique identifier of the story to regenerate.

        Returns:
            Optional[Story]: The reset story object, or None if no story was found.

        Raises:
            NoResultFound: If no story exists with the given ID.

        Example:
            >>> workflow_service = StoryWorkflowService()
            >>> regenerated_story = workflow_service.regenerate_story(42)
            >>> print(regenerated_story.current_step)  # Should be QUEUED

        Note:
            - Resets all generated content and metadata
            - Adds story back to queue with higher priority
            - Useful for stories with generation issues or manual intervention
        """
        story = Story.query.get(story_id)
        if not story:
            logger.error(f"Story {story_id} not found for regeneration")
            return None
        
        logger.info(f"Regenerating story {story_id}: {story.topic}")
        
        # Reset the story to initial state
        story.reset_for_regeneration()
        
        # Add back to queue for processing
        self.queue_service.enqueue_story(story.id, priority=1)  # Higher priority for regenerations
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"Story {story_id} reset and added back to queue for regeneration")
        return story
    
    def get_story_status(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve comprehensive status information for a specific story.

        Fetches a story by its ID and returns a detailed status dictionary
        containing workflow progress, content metadata, and temporal information.

        Args:
            story_id (int): The unique identifier of the story.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing story status details,
            or None if the story is not found. The dictionary includes:
            - 'id': Story's unique identifier
            - 'topic': Story's topic
            - 'current_step': Current workflow step
            - 'has_content': Boolean indicating if story content exists
            - 'has_title': Boolean indicating if story title exists
            - 'word_count': Total word count of the story
            - 'error_message': Any error encountered during processing
            - 'created_at': Timestamp of story creation
            - 'updated_at': Timestamp of last update
            - 'completed_at': Timestamp of workflow completion (if applicable)

        Example:
            >>> workflow_service = StoryWorkflowService()
            >>> status = workflow_service.get_story_status(42)
            >>> print(status['current_step'])  # E.g., 'IMAGE_GENERATION'
        """
        story = Story.query.get(story_id)
        if not story:
            return None
        
        return {
            'id': story.id,
            'topic': story.topic,
            'current_step': story.current_step.value,
            'has_content': bool(story.content),
            'has_title': bool(story.title),
            'word_count': story.word_count,
            'error_message': story.error_message,
            'created_at': story.created_at.isoformat(),
            'updated_at': story.updated_at.isoformat(),
            'completed_at': story.completed_at.isoformat() if story.completed_at else None
        }