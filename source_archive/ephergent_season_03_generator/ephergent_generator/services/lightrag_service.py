"""
LightRAG Service - Client wrapper for LightRAG graph-based RAG system.

This service provides a Python interface to the LightRAG knowledge graph
and retrieval-augmented generation system. It handles story indexing,
similarity detection, and universe lore queries.

Author: A.R.C.H.I.E.
Version: 1.0.0
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class LightRAGConnectionError(Exception):
    """Raised when connection to LightRAG service fails."""
    pass


class LightRAGIndexingError(Exception):
    """Raised when document indexing fails."""
    pass


class LightRAGQueryError(Exception):
    """Raised when query execution fails."""
    pass


class LightRAGService:
    """Client wrapper for LightRAG graph-based RAG system.

    Provides methods for indexing stories, querying similar documents,
    and performing knowledge graph operations for story continuity.

    Attributes:
        base_url (str): Base URL of LightRAG service
        timeout (int): Request timeout in seconds
        session (requests.Session): Persistent HTTP session
    """

    def __init__(self, base_url: str = None, timeout: int = 30):
        """Initialize LightRAG service client.

        Args:
            base_url: LightRAG service URL (default from environment)
            timeout: Request timeout in seconds (default 30)
        """
        self.base_url = base_url or os.environ.get('LIGHTRAG_URL', 'http://lightrag:8000')
        self.timeout = timeout
        self.session = requests.Session()

        # Add default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'EphergentGenerator/1.0'
        })

        # Add API key if configured
        api_key = os.environ.get('LIGHTRAG_API_KEY')
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

        logger.info(f"LightRAG service initialized: {self.base_url}")

    def is_configured(self) -> bool:
        """Check if LightRAG service is configured and enabled.

        Returns:
            bool: True if service is configured and enabled
        """
        enabled = os.environ.get('LIGHTRAG_ENABLED', 'false').lower() in ('true', '1', 'yes')

        if not enabled:
            logger.debug("LightRAG is disabled via LIGHTRAG_ENABLED config")
            return False

        if not self.base_url:
            logger.warning("LightRAG URL not configured")
            return False

        return True

    def health_check(self) -> bool:
        """Check if LightRAG service is healthy and responding.

        Returns:
            bool: True if service is healthy

        Example:
            >>> service = LightRAGService()
            >>> if service.health_check():
            ...     print("LightRAG is ready")
        """
        if not self.is_configured():
            return False

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=5  # Short timeout for health check
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"LightRAG health check OK: {data.get('status')}")
                return data.get('status') == 'healthy'
            else:
                logger.warning(f"LightRAG health check failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"LightRAG health check error: {str(e)}")
            return False

    # ========================================================================
    # INDEXING OPERATIONS
    # ========================================================================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def index_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index a story document in LightRAG.

        Args:
            story_data: Dictionary containing story data:
                - doc_id (str): Unique document ID (e.g., "story_123")
                - title (str): Story title
                - content (str): Story content
                - metadata (dict): Additional metadata

        Returns:
            Dict with indexing results:
                - success (bool): Whether indexing succeeded
                - doc_id (str): Document ID
                - indexed_at (str): ISO timestamp
                - embedding_version (str): Embedding model version

        Raises:
            LightRAGIndexingError: If indexing fails

        Example:
            >>> service = LightRAGService()
            >>> result = service.index_story({
            ...     'doc_id': 'story_123',
            ...     'title': 'Robot Dreams',
            ...     'content': 'Once upon a time...',
            ...     'metadata': {'genre': 'sci-fi', 'character_id': 'dr_quill'}
            ... })
            >>> print(result['success'])
            True
        """
        if not self.is_configured():
            logger.warning("LightRAG not configured, skipping indexing")
            return {'success': False, 'error': 'LightRAG not configured'}

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/index/document",
                json=story_data,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Story indexed successfully: {story_data.get('doc_id')}")
            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error indexing story: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise LightRAGIndexingError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error indexing story: {str(e)}"
            logger.error(error_msg)
            raise LightRAGIndexingError(error_msg)

    def batch_index_stories(self, stories_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index multiple stories in a single batch operation.

        Args:
            stories_data: List of story data dictionaries

        Returns:
            Dict with batch indexing results:
                - success_count (int): Number of successfully indexed stories
                - failed_count (int): Number of failed stories
                - errors (list): List of error details

        Example:
            >>> stories = [
            ...     {'doc_id': 'story_1', 'title': 'Story 1', 'content': '...'},
            ...     {'doc_id': 'story_2', 'title': 'Story 2', 'content': '...'}
            ... ]
            >>> result = service.batch_index_stories(stories)
            >>> print(f"Indexed {result['success_count']} stories")
        """
        if not self.is_configured():
            return {'success_count': 0, 'failed_count': len(stories_data), 'errors': ['LightRAG not configured']}

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/index/batch",
                json={'documents': stories_data},
                timeout=self.timeout * 2  # Double timeout for batch operations
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Batch indexed {result.get('success_count', 0)} stories")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Batch indexing error: {str(e)}")
            return {
                'success_count': 0,
                'failed_count': len(stories_data),
                'errors': [str(e)]
            }

    def update_indexed_story(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Update an already indexed story with new data.

        Args:
            doc_id: Document ID (e.g., "story_123")
            updates: Dictionary of fields to update

        Returns:
            bool: True if update succeeded

        Example:
            >>> service.update_indexed_story('story_123', {
            ...     'title': 'Updated Title',
            ...     'metadata': {'status': 'published'}
            ... })
        """
        if not self.is_configured():
            return False

        try:
            response = self.session.patch(
                f"{self.base_url}/api/v1/index/document/{doc_id}",
                json=updates,
                timeout=self.timeout
            )

            response.raise_for_status()
            logger.info(f"Story updated successfully: {doc_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating story {doc_id}: {str(e)}")
            return False

    def delete_indexed_story(self, doc_id: str) -> bool:
        """Delete a story from the LightRAG index.

        Args:
            doc_id: Document ID to delete

        Returns:
            bool: True if deletion succeeded
        """
        if not self.is_configured():
            return False

        try:
            response = self.session.delete(
                f"{self.base_url}/api/v1/index/document/{doc_id}",
                timeout=self.timeout
            )

            response.raise_for_status()
            logger.info(f"Story deleted from index: {doc_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting story {doc_id}: {str(e)}")
            return False

    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================

    def find_similar_stories(
        self,
        text: str,
        threshold: float = 0.8,
        limit: int = 5,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Find stories similar to the given text using semantic search.

        Args:
            text: Text to find similar stories for
            threshold: Minimum similarity score (0.0 to 1.0)
            limit: Maximum number of results
            filters: Optional metadata filters (e.g., {'character_id': 'dr_quill'})

        Returns:
            List of similar stories with metadata:
                - doc_id (str): Document ID
                - title (str): Story title
                - similarity (float): Similarity score
                - metadata (dict): Story metadata

        Example:
            >>> similar = service.find_similar_stories(
            ...     "A robot learning about emotions",
            ...     threshold=0.75,
            ...     limit=5
            ... )
            >>> for story in similar:
            ...     print(f"{story['title']}: {story['similarity']:.2f}")
        """
        if not self.is_configured():
            logger.warning("LightRAG not configured, returning empty results")
            return []

        try:
            payload = {
                'text': text,
                'threshold': threshold,
                'limit': limit
            }

            if filters:
                payload['filters'] = filters

            response = self.session.post(
                f"{self.base_url}/api/v1/query/similar",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            similar_docs = result.get('similar_documents', [])
            logger.info(f"Found {len(similar_docs)} similar stories")

            return similar_docs

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying similar stories: {str(e)}")
            return []

    def check_topic_overlap(
        self,
        topic: str,
        character_id: str = None,
        threshold: float = 0.75
    ) -> Dict[str, Any]:
        """Check if a topic overlaps with existing stories.

        Args:
            topic: Topic to check
            character_id: Optional character ID to filter by
            threshold: Similarity threshold for overlap detection

        Returns:
            Dict with overlap information:
                - has_overlap (bool): Whether significant overlap exists
                - max_similarity (float): Highest similarity score
                - similar_stories (list): List of overlapping stories
                - recommendation (str): Action recommendation

        Example:
            >>> overlap = service.check_topic_overlap(
            ...     "A robot learns emotions",
            ...     character_id="dr_quill",
            ...     threshold=0.75
            ... )
            >>> if overlap['has_overlap']:
            ...     print(f"Warning: {len(overlap['similar_stories'])} similar stories found")
        """
        if not self.is_configured():
            return {
                'has_overlap': False,
                'max_similarity': 0.0,
                'similar_stories': [],
                'recommendation': 'lightrag_disabled'
            }

        filters = {'character_id': character_id} if character_id else None

        similar_stories = self.find_similar_stories(
            text=topic,
            threshold=threshold,
            limit=10,
            filters=filters
        )

        if not similar_stories:
            return {
                'has_overlap': False,
                'max_similarity': 0.0,
                'similar_stories': [],
                'recommendation': 'no_overlap'
            }

        max_similarity = max(story['similarity'] for story in similar_stories)

        # Determine recommendation
        if max_similarity > 0.9:
            recommendation = 'high_similarity_warning'
        elif max_similarity > threshold:
            recommendation = 'moderate_similarity_warning'
        else:
            recommendation = 'low_similarity_ok'

        return {
            'has_overlap': max_similarity > threshold,
            'max_similarity': max_similarity,
            'similar_stories': similar_stories,
            'recommendation': recommendation
        }

    def get_character_stories(
        self,
        character_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get all stories narrated by a specific character.

        Args:
            character_id: Character ID
            limit: Maximum number of stories to return

        Returns:
            List of story dictionaries

        Example:
            >>> stories = service.get_character_stories('dr_quill', limit=5)
            >>> for story in stories:
            ...     print(story['title'])
        """
        if not self.is_configured():
            return []

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/query/character/{character_id}/stories",
                params={'limit': limit},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            stories = result.get('stories', [])
            logger.info(f"Retrieved {len(stories)} stories for character {character_id}")

            return stories

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting character stories: {str(e)}")
            return []

    def get_related_stories(
        self,
        story_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get stories related to a specific story via graph relationships.

        Args:
            story_id: Story ID
            limit: Maximum number of related stories

        Returns:
            List of related story dictionaries

        Example:
            >>> related = service.get_related_stories(123, limit=3)
            >>> for story in related:
            ...     print(f"{story['title']} (relevance: {story['relevance']:.2f})")
        """
        if not self.is_configured():
            return []

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/query/story/{story_id}/related",
                params={'limit': limit},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            related = result.get('related_stories', [])
            logger.info(f"Found {len(related)} related stories for story {story_id}")

            return related

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting related stories: {str(e)}")
            return []

    def query_universe_lore(
        self,
        question: str,
        context_limit: int = 3
    ) -> Dict[str, Any]:
        """Query the universe knowledge graph with a natural language question.

        Args:
            question: Natural language question about the universe
            context_limit: Maximum number of context stories to include

        Returns:
            Dict with answer and supporting context:
                - summary (str): Answer summary
                - related_stories (list): Supporting stories
                - entities (list): Mentioned entities

        Example:
            >>> lore = service.query_universe_lore("What happened in the Crystalline Dimension?")
            >>> print(lore['summary'])
        """
        if not self.is_configured():
            return {
                'summary': 'LightRAG not configured',
                'related_stories': [],
                'entities': []
            }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/query/lore",
                json={
                    'question': question,
                    'context_limit': context_limit,
                    'include_relationships': True
                },
                timeout=self.timeout * 2  # Longer timeout for complex queries
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Universe lore query completed: {question[:50]}...")
            return result.get('answer', {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying universe lore: {str(e)}")
            return {
                'summary': f'Error: {str(e)}',
                'related_stories': [],
                'entities': []
            }

    # ========================================================================
    # CHARACTER ANALYSIS
    # ========================================================================

    def analyze_character_consistency(
        self,
        character_id: str,
        new_content: str
    ) -> Dict[str, Any]:
        """Analyze if new content is consistent with character's voice and history.

        Args:
            character_id: Character ID
            new_content: New story content to analyze

        Returns:
            Dict with consistency analysis:
                - consistency_score (float): Score from 0.0 to 1.0
                - voice_match (str): Voice consistency assessment
                - potential_issues (list): List of detected issues

        Example:
            >>> analysis = service.analyze_character_consistency(
            ...     'dr_quill',
            ...     'The new story content...'
            ... )
            >>> if analysis['consistency_score'] < 0.7:
            ...     print("Warning: Character voice inconsistency detected")
        """
        if not self.is_configured():
            return {
                'consistency_score': 1.0,
                'voice_match': 'unknown',
                'potential_issues': []
            }

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/analyze/character/{character_id}/consistency",
                json={'content': new_content},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Character consistency analyzed: {character_id}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing character consistency: {str(e)}")
            return {
                'consistency_score': 1.0,
                'voice_match': 'error',
                'potential_issues': [str(e)]
            }

    def get_character_voice_profile(self, character_id: str) -> Dict[str, Any]:
        """Get a character's voice profile based on their story history.

        Args:
            character_id: Character ID

        Returns:
            Dict with voice profile:
                - common_phrases (list): Frequently used phrases
                - tone_analysis (str): Overall tone description
                - topics (list): Common topics covered

        Example:
            >>> profile = service.get_character_voice_profile('dr_quill')
            >>> print(profile['tone_analysis'])
        """
        if not self.is_configured():
            return {
                'common_phrases': [],
                'tone_analysis': 'unknown',
                'topics': []
            }

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/analyze/character/{character_id}/voice-profile",
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Character voice profile retrieved: {character_id}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting character voice profile: {str(e)}")
            return {
                'common_phrases': [],
                'tone_analysis': 'error',
                'topics': []
            }

    # ========================================================================
    # GRAPH OPERATIONS
    # ========================================================================

    def get_story_relationships(self, story_id: int) -> Dict[str, Any]:
        """Get graph relationships for a story.

        Args:
            story_id: Story ID

        Returns:
            Dict with relationship information:
                - nodes (list): Connected nodes
                - edges (list): Relationships
                - depth (int): Graph depth explored

        Example:
            >>> graph = service.get_story_relationships(123)
            >>> print(f"Connected to {len(graph['nodes'])} other stories")
        """
        if not self.is_configured():
            return {'nodes': [], 'edges': [], 'depth': 0}

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/graph/story/{story_id}/relationships",
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Story relationships retrieved: {story_id}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting story relationships: {str(e)}")
            return {'nodes': [], 'edges': [], 'depth': 0}

    def get_topic_graph(self, topic: str, depth: int = 2) -> Dict[str, Any]:
        """Get knowledge graph for a specific topic.

        Args:
            topic: Topic to explore
            depth: Graph traversal depth

        Returns:
            Dict with topic graph:
                - nodes (list): Topic-related nodes
                - edges (list): Relationships
                - stories (list): Related stories

        Example:
            >>> graph = service.get_topic_graph('artificial intelligence', depth=2)
        """
        if not self.is_configured():
            return {'nodes': [], 'edges': [], 'stories': []}

        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/graph/topic",
                params={'topic': topic, 'depth': depth},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Topic graph retrieved: {topic}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting topic graph: {str(e)}")
            return {'nodes': [], 'edges': [], 'stories': []}

    def __del__(self):
        """Cleanup: Close HTTP session."""
        if hasattr(self, 'session'):
            self.session.close()
