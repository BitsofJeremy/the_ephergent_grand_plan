"""
Archive Service for Ephergent Season 03 Story Generator

Handles archiving of completed stories and their associated media files
(markdown, images, audio, video) to a designated archive directory.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import os

from ephergent_generator.models import Story, WorkflowStep

logger = logging.getLogger(__name__)


class ArchiveService:
    """Service for archiving completed stories and their media files."""

    def __init__(self, archive_base_path: str = None):
        """
        Initialize the Archive Service.

        Args:
            archive_base_path: Base path for archive storage. If None, uses project root/archives
        """
        if archive_base_path:
            self.archive_base = Path(archive_base_path)
        else:
            # Default to project root/archives
            project_root = Path(__file__).parent.parent.parent
            self.archive_base = project_root / 'archives'

        # Ensure archive directory exists
        self.archive_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"Archive service initialized with base path: {self.archive_base}")

    def archive_story(self, story: Story, force_rearchive: bool = False) -> Dict[str, str]:
        """
        Archive a completed story and all its media files.

        Args:
            story: The Story object to archive
            force_rearchive: If True, re-archive even if already archived

        Returns:
            Dict with archive status and paths
        """
        if not story:
            return {"status": "error", "message": "No story provided"}

        if story.current_step != WorkflowStep.COMPLETED:
            return {
                "status": "warning",
                "message": f"Story {story.id} is not completed (current step: {story.current_step.value})"
            }

        # Create story-specific archive directory
        # Format: YYYY-MM-DD_story-{id}_{safe_title}
        archive_date = (story.completed_at or story.created_at).strftime('%Y-%m-%d')
        safe_title = self._make_safe_filename(story.title or f"story-{story.id}")
        story_archive_dir = self.archive_base / f"{archive_date}_story-{story.id}_{safe_title}"

        # Check if already archived
        if story_archive_dir.exists() and not force_rearchive:
            return {
                "status": "skipped",
                "message": f"Story {story.id} already archived at {story_archive_dir}",
                "archive_path": str(story_archive_dir)
            }

        try:
            # Create archive directory
            story_archive_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Archiving story {story.id} to {story_archive_dir}")

            archived_files = []

            # 1. Archive story content as markdown
            markdown_content = self._generate_story_markdown(story)
            markdown_path = story_archive_dir / f"{safe_title}.md"
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            archived_files.append(str(markdown_path))
            logger.info(f"Archived story markdown: {markdown_path}")

            # 2. Archive story metadata as JSON
            metadata_path = story_archive_dir / "metadata.json"
            metadata = self._generate_story_metadata(story)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            archived_files.append(str(metadata_path))
            logger.info(f"Archived story metadata: {metadata_path}")

            # 3. Archive images
            image_paths = story.get_image_paths()
            if image_paths:
                images_dir = story_archive_dir / "images"
                images_dir.mkdir(exist_ok=True)

                for i, image_path in enumerate(image_paths):
                    if self._copy_media_file(image_path, images_dir, f"image_{i+1}"):
                        archived_files.append(str(images_dir / f"image_{i+1}.png"))

            # 4. Archive audio file
            if story.audio_path:
                audio_dir = story_archive_dir / "audio"
                audio_dir.mkdir(exist_ok=True)

                if self._copy_media_file(story.audio_path, audio_dir, "story_audio"):
                    archived_files.append(str(audio_dir / "story_audio.wav"))

            # 5. Archive video file
            if story.video_path:
                video_dir = story_archive_dir / "video"
                video_dir.mkdir(exist_ok=True)

                if self._copy_media_file(story.video_path, video_dir, "story_video"):
                    archived_files.append(str(video_dir / "story_video.mp4"))

            # 6. Create archive summary
            summary_path = story_archive_dir / "archive_summary.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"Archive Summary for Story {story.id}\n")
                f.write(f"================================\n\n")
                f.write(f"Title: {story.title}\n")
                f.write(f"Archived on: {datetime.utcnow().isoformat()}\n")
                f.write(f"Original creation: {story.created_at}\n")
                f.write(f"Completion date: {story.completed_at}\n")
                f.write(f"Narrator: {story.narrator_character_id}\n")
                f.write(f"Dimension: {story.dimension_location}\n")
                f.write(f"\nArchived Files:\n")
                for file_path in archived_files:
                    f.write(f"  - {file_path}\n")
                f.write(f"\nTotal files archived: {len(archived_files)}\n")

            logger.info(f"Successfully archived story {story.id} with {len(archived_files)} files")

            return {
                "status": "success",
                "message": f"Story {story.id} archived successfully",
                "archive_path": str(story_archive_dir),
                "files_archived": len(archived_files),
                "archived_files": archived_files
            }

        except Exception as e:
            logger.error(f"Error archiving story {story.id}: {str(e)}")
            # Clean up partial archive on error
            if story_archive_dir.exists():
                shutil.rmtree(story_archive_dir)

            return {
                "status": "error",
                "message": f"Failed to archive story {story.id}: {str(e)}"
            }

    def archive_multiple_stories(self, stories: List[Story], force_rearchive: bool = False) -> Dict[str, any]:
        """
        Archive multiple stories.

        Args:
            stories: List of Story objects to archive
            force_rearchive: If True, re-archive existing archives

        Returns:
            Dict with overall archive status
        """
        results = {
            "total_stories": len(stories),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
            "warnings": 0,
            "details": []
        }

        for story in stories:
            result = self.archive_story(story, force_rearchive)
            results["details"].append({
                "story_id": story.id,
                "title": story.title,
                "result": result
            })

            if result["status"] == "success":
                results["successful"] += 1
            elif result["status"] == "skipped":
                results["skipped"] += 1
            elif result["status"] == "warning":
                results["warnings"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Bulk archive complete: {results['successful']} successful, {results['skipped']} skipped, "
                   f"{results['warnings']} warnings, {results['failed']} failed")

        return results

    def get_archived_stories(self) -> List[Dict[str, str]]:
        """
        Get list of all archived stories.

        Returns:
            List of dictionaries with archive information
        """
        archived_stories = []

        if not self.archive_base.exists():
            return archived_stories

        for archive_dir in self.archive_base.iterdir():
            if archive_dir.is_dir() and archive_dir.name.startswith(('20', '19')):  # Date-based directories
                try:
                    # Parse directory name: YYYY-MM-DD_story-{id}_{title}
                    parts = archive_dir.name.split('_', 2)
                    if len(parts) >= 2 and parts[1].startswith('story-'):
                        story_id = parts[1].replace('story-', '')
                        title = parts[2] if len(parts) > 2 else f"Story {story_id}"

                        # Get archive creation time
                        archive_time = archive_dir.stat().st_ctime

                        # Check for metadata file
                        metadata_path = archive_dir / "metadata.json"
                        metadata = {}
                        if metadata_path.exists():
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                            except Exception:
                                pass

                        archived_stories.append({
                            "story_id": story_id,
                            "title": title,
                            "archive_path": str(archive_dir),
                            "archive_date": parts[0],
                            "archive_time": datetime.fromtimestamp(archive_time).isoformat(),
                            "metadata": metadata
                        })

                except Exception as e:
                    logger.warning(f"Error parsing archive directory {archive_dir.name}: {str(e)}")
                    continue

        # Sort by archive date (newest first)
        archived_stories.sort(key=lambda x: x["archive_date"], reverse=True)
        return archived_stories

    def _generate_story_markdown(self, story: Story) -> str:
        """Generate markdown content for the story."""
        content = f"# {story.title}\n\n"
        content += f"**Story ID:** {story.id}  \n"
        content += f"**Created:** {story.created_at.isoformat() if story.created_at else 'Unknown'}  \n"
        content += f"**Completed:** {story.completed_at.isoformat() if story.completed_at else 'Unknown'}  \n"
        content += f"**Narrator:** {story.narrator_character_id or 'Unknown'}  \n"
        content += f"**Dimension:** {story.dimension_location or 'Unknown'}  \n"
        content += f"**Genre:** {story.genre or 'Unknown'}  \n"
        content += f"**Tone:** {story.tone or 'Unknown'}  \n"
        content += f"**Word Count:** {story.word_count or 'Unknown'}  \n\n"

        if story.youtube_url:
            content += f"**YouTube Video:** {story.youtube_url}  \n"
        if story.ghost_post_url:
            content += f"**Blog Post:** {story.ghost_post_url}  \n"

        content += "---\n\n"

        # Original topic
        content += f"## Original Topic\n\n{story.topic}\n\n"

        # Generated prompt (if available)
        if story.prompt:
            content += f"## Generated Prompt\n\n{story.prompt}\n\n"

        # Story content
        if story.content:
            content += f"## Story Content\n\n{story.content}\n\n"

        # Image prompts (if available)
        image_prompts = story.get_image_prompts()
        if image_prompts:
            content += "## Image Generation Prompts\n\n"
            for key, prompt in image_prompts.items():
                content += f"**{key}:** {prompt}\n\n"

        return content

    def _generate_story_metadata(self, story: Story) -> Dict:
        """Generate metadata dictionary for the story."""
        return {
            "story_id": story.id,
            "title": story.title,
            "topic": story.topic,
            "prompt": story.prompt,
            "genre": story.genre,
            "tone": story.tone,
            "word_count": story.word_count,
            "narrator_character_id": story.narrator_character_id,
            "dimension_location": story.dimension_location,
            "current_step": story.current_step.value if story.current_step else None,
            "workflow_data": story.get_workflow_data(),
            "created_at": story.created_at.isoformat() if story.created_at else None,
            "updated_at": story.updated_at.isoformat() if story.updated_at else None,
            "completed_at": story.completed_at.isoformat() if story.completed_at else None,
            "session_id": story.session_id,
            "image_paths": story.get_image_paths(),
            "image_prompts": story.get_image_prompts(),
            "audio_path": story.audio_path,
            "video_path": story.video_path,
            "youtube_video_id": story.youtube_video_id,
            "youtube_url": story.youtube_url,
            "ghost_post_id": story.ghost_post_id,
            "ghost_post_url": story.ghost_post_url,
            "ghost_status": story.ghost_status,
            "archived_at": datetime.utcnow().isoformat()
        }

    def _copy_media_file(self, source_path: str, destination_dir: Path, base_filename: str) -> bool:
        """
        Copy a media file to the archive directory.

        Args:
            source_path: Path to source file
            destination_dir: Destination directory
            base_filename: Base filename (without extension)

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            source = Path(source_path)

            # Handle relative paths (assume they're relative to project root)
            if not source.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                source = project_root / source_path

            if not source.exists():
                logger.warning(f"Source file not found for archiving: {source}")
                return False

            # Determine file extension
            extension = source.suffix if source.suffix else self._guess_extension(source)
            destination = destination_dir / f"{base_filename}{extension}"

            # Copy the file
            shutil.copy2(source, destination)
            logger.info(f"Archived media file: {source} -> {destination}")
            return True

        except Exception as e:
            logger.error(f"Error copying media file {source_path}: {str(e)}")
            return False

    def _guess_extension(self, file_path: Path) -> str:
        """Guess file extension based on file content or name."""
        # Simple extension guessing based on common patterns
        path_str = str(file_path).lower()

        if 'audio' in path_str or path_str.endswith(('wav', 'mp3', 'flac', 'ogg')):
            return '.wav'
        elif 'video' in path_str or path_str.endswith(('mp4', 'avi', 'mkv', 'mov')):
            return '.mp4'
        elif 'image' in path_str or path_str.endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
            return '.png'
        else:
            return ''  # No extension

    def _make_safe_filename(self, filename: str, max_length: int = 50) -> str:
        """Convert a string to a safe filename."""
        if not filename:
            return "untitled"

        # Remove or replace unsafe characters
        safe_chars = []
        for char in filename.lower():
            if char.isalnum() or char in '-_':
                safe_chars.append(char)
            elif char.isspace():
                safe_chars.append('_')

        safe_filename = ''.join(safe_chars)

        # Remove consecutive underscores
        while '__' in safe_filename:
            safe_filename = safe_filename.replace('__', '_')

        # Trim length and remove trailing underscores
        safe_filename = safe_filename[:max_length].strip('_')

        return safe_filename or "untitled"