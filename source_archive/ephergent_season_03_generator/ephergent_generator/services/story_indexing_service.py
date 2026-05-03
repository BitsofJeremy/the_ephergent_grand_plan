"""
Story Indexing Service - Prepares and indexes stories for LightRAG.

This service handles the extraction, formatting, and indexing of story
data for the LightRAG knowledge graph. It coordinates between the
Story model and LightRAG service.

Author: A.R.C.H.I.E.
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ephergent_generator import db
from ephergent_generator.models import Story, StoryIndex, WorkflowStep
from ephergent_generator.services.lightrag_service import LightRAGService
from ephergent_generator.services.character_service import CharacterService

logger = logging.getLogger(__name__)


class StoryIndexingService:
    """Service for preparing and indexing stories in LightRAG.

    This service bridges the gap between Story database models and the
    LightRAG knowledge graph system, handling data extraction, formatting,
    and tracking of indexing status.

    Attributes:
        lightrag_service (LightRAGService): LightRAG client
        character_service (CharacterService): Character data service
    """

    def __init__(self):
        """Initialize story indexing service."""
        self.lightrag_service = LightRAGService()
        self.character_service = CharacterService()
        logger.info("StoryIndexingService initialized")

    def prepare_story_document(self, story: Story) -> Dict[str, Any]:
        """Prepare a story for LightRAG indexing.

        Extracts all relevant data from a Story model and formats it
        for LightRAG document ingestion.

        Args:
            story: Story model instance

        Returns:
            Dict formatted for LightRAG indexing with:
                - doc_id: Unique document identifier
                - title: Story title
                - content: Story text content
                - metadata: Additional story attributes

        Example:
            >>> service = StoryIndexingService()
            >>> story = Story.query.get(123)
            >>> doc = service.prepare_story_document(story)
            >>> print(doc['doc_id'])
            'story_123'
        """
        # Extract metadata
        metadata = self.extract_story_metadata(story)

        # Build embedding text (optimized for semantic search)
        embedding_text = self.generate_story_embedding_text(story)

        # Prepare document structure
        document = {
            'doc_id': f"story_{story.id}",
            'title': story.title or f"Story: {story.topic[:50]}",
            'content': embedding_text,
            'metadata': metadata
        }

        logger.debug(f"Prepared document for story {story.id}: {len(embedding_text)} chars")
        return document

    def extract_story_metadata(self, story: Story) -> Dict[str, Any]:
        """Extract structured metadata from a story.

        Args:
            story: Story model instance

        Returns:
            Dict with story metadata including character, genre, dates, etc.

        Example:
            >>> metadata = service.extract_story_metadata(story)
            >>> print(metadata['genre'])
            'sci-fi'
        """
        # Get character information
        character_data = None
        if story.narrator_character_id:
            character = self.character_service.get_character_by_id(story.narrator_character_id)
            if character:
                character_data = {
                    'id': character.character_id,
                    'name': character.name,
                    'topics': character.get_topics(),
                    'tags': character.get_tags()
                }

        # Extract workflow data
        workflow_data = story.get_workflow_data()

        # Build metadata dictionary
        metadata = {
            'story_id': story.id,
            'topic': story.topic,
            'genre': story.genre,
            'tone': story.tone,
            'word_count': story.word_count,
            'dimension_location': story.dimension_location,

            # Character information
            'narrator_character': character_data,

            # Status
            'current_step': story.current_step.value if story.current_step else None,
            'is_completed': story.current_step == WorkflowStep.COMPLETED,

            # Dates
            'created_at': story.created_at.isoformat() if story.created_at else None,
            'completed_at': story.completed_at.isoformat() if story.completed_at else None,

            # Publishing
            'youtube_url': story.youtube_url,
            'ghost_post_url': story.ghost_post_url,

            # Workflow data (for advanced queries)
            'similarity_warning': workflow_data.get('similarity_warning') if workflow_data else None
        }

        # Add character topics as searchable tags
        if character_data and character_data.get('topics'):
            metadata['topics'] = character_data['topics']

        return metadata

    def generate_story_embedding_text(self, story: Story) -> str:
        """Generate optimized text for semantic embedding.

        Combines story content with metadata in a way that optimizes
        semantic search and similarity detection.

        Args:
            story: Story model instance

        Returns:
            str: Formatted text for embedding

        Example:
            >>> text = service.generate_story_embedding_text(story)
            >>> print(len(text))
            1500
        """
        parts = []

        # Title (weighted heavily in semantic search)
        if story.title:
            parts.append(f"Title: {story.title}")

        # Topic/theme (also weighted)
        if story.topic:
            parts.append(f"Theme: {story.topic}")

        # Genre and tone
        if story.genre:
            parts.append(f"Genre: {story.genre}")
        if story.tone:
            parts.append(f"Tone: {story.tone}")

        # Dimension context
        if story.dimension_location:
            parts.append(f"Setting: {story.dimension_location}")

        # Character narrator
        if story.narrator_character_id:
            character = self.character_service.get_character_by_id(story.narrator_character_id)
            if character:
                parts.append(f"Narrator: {character.name}")

        # Main content
        if story.content:
            # Truncate very long content for embedding efficiency
            # Keep first 1500 words (typical limit for embedding models)
            content_words = story.content.split()
            if len(content_words) > 1500:
                truncated_content = ' '.join(content_words[:1500]) + '...'
                parts.append(truncated_content)
            else:
                parts.append(story.content)

        # Combine with double newlines for clear separation
        embedding_text = '\n\n'.join(parts)

        return embedding_text

    def index_story(
        self,
        story: Story,
        stage: str = "complete"
    ) -> bool:
        """Index a story in LightRAG.

        Args:
            story: Story model instance to index
            stage: Indexing stage ('content', 'title', 'complete')

        Returns:
            bool: True if indexing succeeded

        Raises:
            Exception: If critical indexing error occurs

        Example:
            >>> service = StoryIndexingService()
            >>> story = Story.query.get(123)
            >>> success = service.index_story(story, stage='complete')
            >>> print(f"Indexed: {success}")
        """
        if not self.lightrag_service.is_configured():
            logger.debug(f"LightRAG not configured, skipping indexing for story {story.id}")
            return False

        try:
            # Prepare document
            document = self.prepare_story_document(story)

            # Add stage to metadata
            document['metadata']['indexing_stage'] = stage

            # Index via LightRAG service
            result = self.lightrag_service.index_story(document)

            if result.get('success'):
                # Update or create StoryIndex record
                self._update_index_status(
                    story_id=story.id,
                    is_indexed=True,
                    stage=stage,
                    lightrag_doc_id=document['doc_id'],
                    embedding_version=result.get('embedding_version')
                )

                logger.info(f"Story {story.id} indexed successfully at stage '{stage}'")
                return True
            else:
                error = result.get('error', 'Unknown error')
                self._update_index_status(
                    story_id=story.id,
                    is_indexed=False,
                    error=error
                )

                logger.error(f"Story {story.id} indexing failed: {error}")
                return False

        except Exception as e:
            logger.error(f"Exception indexing story {story.id}: {str(e)}")
            self._update_index_status(
                story_id=story.id,
                is_indexed=False,
                error=str(e)
            )
            return False

    def index_story_partial(
        self,
        story: Story,
        fields: List[str]
    ) -> bool:
        """Index only specific fields of a story (incremental update).

        Args:
            story: Story model instance
            fields: List of field names to index (e.g., ['title', 'content'])

        Returns:
            bool: True if partial indexing succeeded

        Example:
            >>> service.index_story_partial(story, fields=['title'])
        """
        if not self.lightrag_service.is_configured():
            return False

        try:
            # Check if story is already indexed
            index_status = StoryIndex.query.filter_by(story_id=story.id).first()

            if not index_status or not index_status.is_indexed:
                # Not indexed yet, do full indexing
                logger.info(f"Story {story.id} not yet indexed, performing full index")
                return self.index_story(story, stage="partial")

            # Prepare update data
            updates = {}

            if 'title' in fields and story.title:
                updates['title'] = story.title

            if 'content' in fields and story.content:
                updates['content'] = self.generate_story_embedding_text(story)

            if 'metadata' in fields:
                updates['metadata'] = self.extract_story_metadata(story)

            if not updates:
                logger.warning(f"No valid fields to update for story {story.id}")
                return False

            # Update via LightRAG service
            doc_id = index_status.lightrag_doc_id or f"story_{story.id}"
            success = self.lightrag_service.update_indexed_story(doc_id, updates)

            if success:
                # Update index timestamp
                index_status.last_indexed_at = datetime.utcnow()
                index_status.updated_at = datetime.utcnow()
                db.session.commit()

                logger.info(f"Story {story.id} partially indexed: {fields}")
                return True
            else:
                logger.error(f"Failed to update story {story.id} in LightRAG")
                return False

        except Exception as e:
            logger.error(f"Exception during partial indexing of story {story.id}: {str(e)}")
            return False

    def batch_index_all_stories(
        self,
        batch_size: int = 10,
        completed_only: bool = True
    ) -> Dict[str, Any]:
        """Index all stories in batches.

        Args:
            batch_size: Number of stories per batch
            completed_only: Only index completed stories

        Returns:
            Dict with batch results:
                - total_stories (int): Total stories processed
                - success_count (int): Successfully indexed
                - failed_count (int): Failed indexing
                - skipped_count (int): Already indexed

        Example:
            >>> result = service.batch_index_all_stories(batch_size=10)
            >>> print(f"Indexed {result['success_count']} stories")
        """
        if not self.lightrag_service.is_configured():
            logger.warning("LightRAG not configured, skipping batch indexing")
            return {
                'total_stories': 0,
                'success_count': 0,
                'failed_count': 0,
                'skipped_count': 0
            }

        # Build query
        query = Story.query

        if completed_only:
            query = query.filter(Story.current_step == WorkflowStep.COMPLETED)

        # Exclude already indexed stories
        query = query.outerjoin(StoryIndex).filter(
            (StoryIndex.is_indexed == False) | (StoryIndex.is_indexed == None)
        )

        total_stories = query.count()
        logger.info(f"Starting batch indexing of {total_stories} stories")

        success_count = 0
        failed_count = 0
        skipped_count = 0

        # Process in batches
        for offset in range(0, total_stories, batch_size):
            batch = query.offset(offset).limit(batch_size).all()

            for story in batch:
                try:
                    # Skip if no content
                    if not story.content:
                        logger.warning(f"Story {story.id} has no content, skipping")
                        skipped_count += 1
                        continue

                    # Index story
                    success = self.index_story(story, stage="complete")

                    if success:
                        success_count += 1
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Error indexing story {story.id}: {str(e)}")
                    failed_count += 1

            # Commit after each batch
            db.session.commit()
            logger.info(f"Batch progress: {offset + len(batch)}/{total_stories}")

        result = {
            'total_stories': total_stories,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count
        }

        logger.info(f"Batch indexing complete: {result}")
        return result

    # ========================================================================
    # STATUS TRACKING
    # ========================================================================

    def is_story_indexed(self, story_id: int) -> bool:
        """Check if a story is indexed in LightRAG.

        Args:
            story_id: Story ID

        Returns:
            bool: True if story is indexed
        """
        index_status = StoryIndex.query.filter_by(story_id=story_id).first()
        return index_status and index_status.is_indexed

    def get_indexing_status(self, story_id: int) -> Dict[str, Any]:
        """Get detailed indexing status for a story.

        Args:
            story_id: Story ID

        Returns:
            Dict with indexing status information

        Example:
            >>> status = service.get_indexing_status(123)
            >>> print(status['is_indexed'])
            True
        """
        index_status = StoryIndex.query.filter_by(story_id=story_id).first()

        if not index_status:
            return {
                'is_indexed': False,
                'status': 'not_indexed',
                'last_indexed_at': None,
                'error': None
            }

        return {
            'is_indexed': index_status.is_indexed,
            'status': 'indexed' if index_status.is_indexed else 'failed',
            'indexing_stage': index_status.indexing_stage,
            'last_indexed_at': index_status.last_indexed_at.isoformat() if index_status.last_indexed_at else None,
            'embedding_version': index_status.embedding_version,
            'error': index_status.indexing_error,
            'retry_count': index_status.retry_count
        }

    def mark_for_reindexing(self, story_id: int) -> bool:
        """Mark a story for reindexing.

        Args:
            story_id: Story ID

        Returns:
            bool: True if marked successfully

        Example:
            >>> service.mark_for_reindexing(123)
        """
        index_status = StoryIndex.query.filter_by(story_id=story_id).first()

        if index_status:
            index_status.is_indexed = False
            index_status.indexing_error = "Marked for reindexing"
            index_status.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Story {story_id} marked for reindexing")
            return True
        else:
            logger.warning(f"Story {story_id} has no index record to mark")
            return False

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _update_index_status(
        self,
        story_id: int,
        is_indexed: bool,
        stage: str = None,
        lightrag_doc_id: str = None,
        embedding_version: str = None,
        error: str = None
    ) -> None:
        """Update or create StoryIndex record.

        Args:
            story_id: Story ID
            is_indexed: Whether indexing succeeded
            stage: Indexing stage
            lightrag_doc_id: LightRAG document ID
            embedding_version: Embedding model version
            error: Error message if indexing failed
        """
        index_status = StoryIndex.query.filter_by(story_id=story_id).first()

        if not index_status:
            index_status = StoryIndex(story_id=story_id)
            db.session.add(index_status)

        # Update fields
        index_status.is_indexed = is_indexed

        if is_indexed:
            index_status.last_indexed_at = datetime.utcnow()
            index_status.indexing_error = None
            index_status.retry_count = 0  # Reset retry count on success
        else:
            index_status.indexing_error = error
            index_status.retry_count += 1

        if stage:
            index_status.indexing_stage = stage

        if lightrag_doc_id:
            index_status.lightrag_doc_id = lightrag_doc_id

        if embedding_version:
            index_status.embedding_version = embedding_version

        index_status.updated_at = datetime.utcnow()

        # Commit changes
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating index status for story {story_id}: {str(e)}")
            db.session.rollback()
