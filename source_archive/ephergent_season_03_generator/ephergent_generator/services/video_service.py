import os
import logging
from pathlib import Path
import random
import math
from typing import Tuple, Optional, List, Dict, Any

# Third-party libraries
try:
    from moviepy import (
        AudioFileClip, ImageClip, VideoClip, concatenate_videoclips, TextClip,
        CompositeVideoClip, ColorClip
    )
    from moviepy.video import fx as vfx
    import numpy as np
    from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    # Set dummy values if imports fail
    np = None
    Image = None
    ImageDraw = None
    ImageOps = None
    UnidentifiedImageError = Exception
    
    # Dummy MoviePy classes
    class DummyClip:
        def __init__(self, *args, **kwargs):
            pass
        def with_duration(self, *args, **kwargs):
            return self
        def with_fps(self, *args, **kwargs):
            return self
        def with_start(self, *args, **kwargs):
            return self
        def with_position(self, *args, **kwargs):
            return self
        def with_audio(self, *args, **kwargs):
            return self
        def with_mask(self, *args, **kwargs):
            return self
        def set_duration(self, *args, **kwargs):
            return self
        def set_fps(self, *args, **kwargs):
            return self
        def set_start(self, *args, **kwargs):
            return self
        def set_position(self, *args, **kwargs):
            return self
        def set_audio(self, *args, **kwargs):
            return self
        def set_mask(self, *args, **kwargs):
            return self
        def write_videofile(self, *args, **kwargs):
            pass
        def close(self):
            pass
        @property
        def duration(self):
            return 0
    
    AudioFileClip = DummyClip
    ImageClip = DummyClip
    VideoClip = DummyClip
    TextClip = DummyClip
    CompositeVideoClip = DummyClip
    ColorClip = DummyClip
    
    def concatenate_videoclips(*args, **kwargs):
        return DummyClip()
    
    logging.getLogger(__name__).error("MoviePy dependencies not available")

from ephergent_generator.services.character_service import CharacterService

logger = logging.getLogger(__name__)

class VideoService:
    """Service for generating videos from story content, images, and audio."""
    
    def __init__(self):
        self.character_service = CharacterService()
        self.videos_dir = self._get_videos_directory()
        
        # Video configuration constants
        self.DEFAULT_RESOLUTION = (1280, 720)
        self.DEFAULT_LOGO_DURATION = 2.0
        self.DEFAULT_FEATURED_DURATION = 4.0
        self.DEFAULT_ARTICLE_IMAGE_DURATION = 5.0
        self.VIDEO_FPS = 24
        self.MAX_FEATURED_DURATION_RATIO = 0.15
        self.REPORTER_SIZE_RATIO = 0.20
        self.REPORTER_MARGIN_RATIO = 0.03
        self.TITLE_FONT_SIZE_RATIO = 0.04
        self.TITLE_MARGIN_RATIO = 0.04
        self.GRADIENT_HEIGHT_RATIO = 0.15
        
        # Asset paths
        project_root = Path(__file__).parent.parent.parent
        self.assets_dir = project_root / 'assets'
        self.logo_path = self.assets_dir / 'images' / 'ephergent_logo.png'
        # Fix font path to point to the actual location
        self.font_path = project_root / 'ephergent_generator' / 'static' / 'fonts' / 'Montserrat-Black.ttf'
        # Use static/img/characters for reporter images (full 1024x1024 resolution)
        self.reporter_images_dir = project_root / 'ephergent_generator' / 'static' / 'img' / 'characters'
        
        # Ensure directories exist
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        (self.assets_dir / 'images').mkdir(exist_ok=True)
        (self.assets_dir / 'fonts').mkdir(exist_ok=True)
        # Note: reporter_images_dir is in static directory, no need to create
        
    def _get_videos_directory(self):
        """Get or create the videos directory."""
        project_root = Path(__file__).parent.parent.parent
        videos_dir = project_root / 'ephergent_generator' / 'static' / 'generated_videos'
        videos_dir.mkdir(parents=True, exist_ok=True)
        return videos_dir
    
    def is_available(self) -> bool:
        """Check if video generation is available."""
        return MOVIEPY_AVAILABLE
    
    def test_connection(self) -> Dict[str, Any]:
        """Test video generation dependencies and return detailed status."""
        import time
        
        status = {
            'service': 'Video Generation',
            'moviepy_available': MOVIEPY_AVAILABLE,
            'numpy_available': np is not None,
            'pil_available': Image is not None,
            'dependencies_ok': False,
            'assets_status': {},
            'test_duration': None,
            'error': None
        }
        
        start_time = time.time()
        
        try:
            # Check core dependencies
            if not MOVIEPY_AVAILABLE:
                status['error'] = 'MoviePy not available - install moviepy package'
                return status
                
            if np is None:
                status['error'] = 'NumPy not available - install numpy package'
                return status
                
            if Image is None:
                status['error'] = 'PIL/Pillow not available - install pillow package'
                return status
            
            # Check asset directories and files
            status['assets_status'] = {
                'videos_directory': str(self.videos_dir) + (' ✓' if self.videos_dir.exists() else ' ✗'),
                'assets_directory': str(self.assets_dir) + (' ✓' if self.assets_dir.exists() else ' ✗'),
                'logo_available': self.logo_path.exists(),
                'font_available': self.font_path.exists(),
                'reporters_directory': str(self.reporter_images_dir) + (' ✓' if self.reporter_images_dir.exists() else ' ✗'),
                'reporter_images_count': len(list(self.reporter_images_dir.glob('*.png'))) if self.reporter_images_dir.exists() else 0
            }
            
            # Test basic MoviePy functionality
            try:
                # Create a minimal test clip to verify MoviePy works
                test_clip = ColorClip(size=(100, 100), color=(0, 0, 0), duration=0.1)
                test_clip = test_clip.with_fps(1)
                test_clip.close()  # Clean up
                
                status['dependencies_ok'] = True
                logger.info("Video generation dependencies test successful")
                
            except Exception as e:
                status['error'] = f'MoviePy test failed: {str(e)}'
                logger.warning(f"Video generation test failed: {e}")
            
        except Exception as e:
            status['error'] = f'Unexpected error during video test: {str(e)}'
            logger.error(f"Video generation test error: {e}")
        
        status['test_duration'] = round(time.time() - start_time, 3)
        return status
    
    def _sanitize_filename(self, text: str, max_length: int = 100) -> str:
        """Sanitize filename for filesystem safety."""
        import re
        sanitized = re.sub(r'[^\w\s\-_.]', '_', text)
        sanitized = re.sub(r'[\s_]+', '_', sanitized)
        sanitized = sanitized.strip('_').lower()
        
        if not sanitized:
            sanitized = "video"
        
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_')
        
        return sanitized
    
    def _get_resolution(self, resolution_input: Any) -> Tuple[int, int]:
        """Convert resolution input to validated (width, height) tuple."""
        if isinstance(resolution_input, tuple) and len(resolution_input) == 2:
            width, height = resolution_input
            if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
                return width, height
        
        if isinstance(resolution_input, str):
            try:
                width, height = map(int, resolution_input.lower().split('x'))
                if width > 0 and height > 0:
                    return width, height
            except (ValueError, AttributeError):
                pass
        
        logger.warning(f"Invalid resolution {resolution_input}, using default {self.DEFAULT_RESOLUTION}")
        return self.DEFAULT_RESOLUTION
    
    def _load_and_prepare_image(self, image_path: Path, size: Tuple[int, int]) -> Optional[Any]:
        """Load an image, resize it, and return as numpy array."""
        if not MOVIEPY_AVAILABLE or not image_path.exists():
            return None
        
        try:
            img = Image.open(image_path)
            
            # Handle different image modes
            if img.mode == 'RGBA':
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[3])
                img = bg
            else:
                img = img.convert("RGB")
            
            # Resize to fit
            img_resized = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
            if np:
                return np.array(img_resized)
            else:
                return img_resized
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return None
    
    def _create_circular_mask(self, size: Tuple[int, int]) -> Optional[Any]:
        """Create a circular mask for reporter images."""
        if not Image or not ImageDraw:
            return None
        try:
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            return mask
        except Exception as e:
            logger.error(f"Error creating circular mask: {e}")
            return None
    
    def _create_gradient_mask(self, width: int, height: int, gradient_height: int) -> Optional[Any]:
        """Create a gradient mask for text overlay background."""
        if not MOVIEPY_AVAILABLE or not np:
            return None
            
        try:
            alpha_gradient = np.zeros((height, width), dtype=np.uint8)
            start_y = height - gradient_height
            
            gradient_values = np.linspace(0, 255, gradient_height, dtype=np.uint8)
            
            for i, alpha_val in enumerate(gradient_values):
                y_pos = start_y + i
                if 0 <= y_pos < height:
                    alpha_gradient[y_pos, :] = alpha_val
            
            return Image.fromarray(alpha_gradient, mode='L')
        except Exception as e:
            logger.error(f"Error creating gradient mask: {e}")
            return None
    
    def generate_video(self, story_data: Dict[str, Any]) -> Optional[Path]:
        """
        Generate a video from story data, images, and audio.
        
        Args:
            story_data: Dictionary containing story information and file paths
            
        Returns:
            Path to generated video or None if failed
        """
        if not MOVIEPY_AVAILABLE:
            logger.error("MoviePy not available, cannot generate video")
            return None
        
        try:
            story_id = story_data.get('id', 'unknown')
            title = story_data.get('title', 'Untitled Story')
            narrator_id = story_data.get('narrator_character_id')
            
            # Get character info
            character = None
            if narrator_id:
                character = self.character_service.get_character_by_id(narrator_id)
            
            # Get file paths
            audio_path = story_data.get('audio_path')
            image_paths = story_data.get('image_paths', {})
            
            if not audio_path or not Path(audio_path).exists():
                logger.error(f"Audio file not found: {audio_path}")
                return None
            
            # Validate image paths
            featured_image = image_paths.get('feature')
            article_images = [
                image_paths.get('beginning'),
                image_paths.get('middle'), 
                image_paths.get('end')
            ]
            article_images = [img for img in article_images if img and Path(img).exists()]
            
            if not featured_image or not Path(featured_image).exists():
                logger.error(f"Featured image not found: {featured_image}")
                return None
            
            if not article_images:
                logger.warning("No article images found, using featured image")
                article_images = [featured_image]
            
            # Generate output filename
            safe_title = self._sanitize_filename(title)
            output_filename = f"story_{story_id}_{safe_title}_video.mp4"
            output_path = self.videos_dir / output_filename
            
            # Generate video
            return self._create_video(
                title=title,
                audio_path=Path(audio_path),
                featured_image_path=Path(featured_image),
                article_image_paths=[Path(p) for p in article_images],
                output_path=output_path,
                character=character
            )
            
        except Exception as e:
            logger.error(f"Error generating video for story {story_data.get('id')}: {e}")
            return None
    
    def _create_video(
        self,
        title: str,
        audio_path: Path,
        featured_image_path: Path,
        article_image_paths: List[Path],
        output_path: Path,
        character: Optional[Dict] = None
    ) -> Optional[Path]:
        """Create the actual video file using MoviePy."""
        
        width, height = self.DEFAULT_RESOLUTION
        size = (width, height)
        
        logger.info(f"Creating video: {output_path}")
        logger.info(f"Resolution: {width}x{height}")
        
        clip_instances = []
        
        try:
            # Load audio
            audio_clip = AudioFileClip(str(audio_path))
            total_duration = audio_clip.duration
            clip_instances.append(audio_clip)
            
            logger.info(f"Audio duration: {total_duration:.2f} seconds")
            
            # Calculate durations
            logo_duration = min(self.DEFAULT_LOGO_DURATION, total_duration * 0.1)
            remaining_after_logo = total_duration - logo_duration
            featured_duration = min(
                self.DEFAULT_FEATURED_DURATION, 
                remaining_after_logo * self.MAX_FEATURED_DURATION_RATIO
            )
            article_duration = total_duration - logo_duration - featured_duration
            
            logger.info(f"Durations - Logo: {logo_duration:.2f}s, Featured: {featured_duration:.2f}s, Article: {article_duration:.2f}s")
            
            # Load images
            featured_img = self._load_and_prepare_image(featured_image_path, size)
            if featured_img is None:
                logger.error("Failed to load featured image")
                return None
            
            article_images = []
            for img_path in article_image_paths:
                img = self._load_and_prepare_image(img_path, size)
                if img is not None:
                    article_images.append(img)
            
            if not article_images:
                article_images.append(featured_img)
            
            # Create video clips
            all_clips = []
            
            # Logo clip (if exists)
            if self.logo_path.exists() and logo_duration > 0:
                logo_img = self._load_and_prepare_image(self.logo_path, size)
                if logo_img is not None:
                    logo_clip = ImageClip(logo_img).with_duration(logo_duration).with_fps(self.VIDEO_FPS)
                    all_clips.append(logo_clip)
                    clip_instances.append(logo_clip)
            
            # Featured image clip
            if featured_duration > 0:
                featured_clip = ImageClip(featured_img).with_duration(featured_duration).with_fps(self.VIDEO_FPS)
                all_clips.append(featured_clip)
                clip_instances.append(featured_clip)
            
            # Article image clips (cycling through images)
            if article_duration > 0 and article_images:
                article_clips = []
                remaining_time = article_duration
                img_index = 0
                
                while remaining_time > 0.1:
                    clip_duration = min(self.DEFAULT_ARTICLE_IMAGE_DURATION, remaining_time)
                    img = article_images[img_index % len(article_images)]
                    
                    article_clip = ImageClip(img).with_duration(clip_duration).with_fps(self.VIDEO_FPS)
                    article_clips.append(article_clip)
                    clip_instances.append(article_clip)
                    
                    remaining_time -= clip_duration
                    img_index += 1
                    
                    if img_index > 100:  # Safety break
                        break
                
                if article_clips:
                    concatenated_articles = concatenate_videoclips(article_clips)
                    all_clips.append(concatenated_articles)
                    clip_instances.append(concatenated_articles)
            
            # Combine all clips
            if not all_clips:
                logger.error("No video clips generated")
                return None
            
            base_video = concatenate_videoclips(all_clips)
            clip_instances.append(base_video)
            
            # Create overlays
            overlays = [base_video]
            article_start_time = logo_duration + featured_duration
            
            # Add gradient overlay for text readability
            if article_duration > 0:
                gradient_height = int(height * self.GRADIENT_HEIGHT_RATIO)
                gradient_mask = self._create_gradient_mask(width, height, gradient_height)
                
                if gradient_mask is not None and np:
                    gradient_mask_np = np.array(gradient_mask)
                    black_bg = ColorClip(size=size, color=(0, 0, 0))
                    gradient_clip = black_bg.with_mask(ImageClip(gradient_mask_np, is_mask=True))
                    gradient_clip = (gradient_clip
                                   .with_duration(article_duration)
                                   .with_start(article_start_time)
                                   .with_fps(self.VIDEO_FPS))
                    overlays.append(gradient_clip)
                    clip_instances.append(gradient_clip)
            
            # Add character reporter overlay
            if character and article_duration > 0:
                reporter_clip = self._create_reporter_overlay(
                    character, width, height, article_duration, article_start_time
                )
                if reporter_clip:
                    overlays.append(reporter_clip)
                    clip_instances.append(reporter_clip)
            
            # Add title overlay
            if title and article_duration > 0:
                title_clip = self._create_title_overlay(
                    title, width, height, article_duration, article_start_time
                )
                if title_clip:
                    overlays.append(title_clip)
                    clip_instances.append(title_clip)
            
            # Compose final video
            final_video = CompositeVideoClip(overlays, size=size)
            final_video = final_video.with_audio(audio_clip).with_duration(total_duration)
            clip_instances.append(final_video)
            
            # Write video file
            logger.info(f"Writing video to: {output_path}")
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=self.VIDEO_FPS,
                preset='medium',
                threads=os.cpu_count() or 4
            )
            
            logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return None
            
        finally:
            # Clean up clips
            for clip in clip_instances:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                except:
                    pass
    
    def _create_reporter_overlay(self, character: Dict, width: int, height: int, 
                                duration: float, start_time: float) -> Optional[VideoClip]:
        """Create circular reporter overlay in bottom-right corner."""
        try:
            # Try full resolution image first, then fallback to resized
            reporter_image_path = self.reporter_images_dir / f"{character['id']}.png"
            if not reporter_image_path.exists():
                # Try resized version as fallback
                reporter_image_path = self.reporter_images_dir / f"{character['id']}_resized.png"
            
            if not reporter_image_path.exists():
                logger.warning(f"Reporter image not found: {reporter_image_path}")
                return None
            
            logger.info(f"Using reporter image: {reporter_image_path}")
            
            reporter_diameter = int(height * self.REPORTER_SIZE_RATIO)
            reporter_size = (reporter_diameter, reporter_diameter)
            margin_x = int(width * self.REPORTER_MARGIN_RATIO)
            margin_y = int(height * self.REPORTER_MARGIN_RATIO)
            
            # Load and process reporter image
            reporter_img = Image.open(reporter_image_path).convert("RGBA")
            reporter_img = reporter_img.resize(reporter_size, Image.Resampling.LANCZOS)
            
            # Apply circular mask
            mask = self._create_circular_mask(reporter_size)
            if mask and np:
                reporter_img.putalpha(mask)
                reporter_np = np.array(reporter_img)
                
                # Position at bottom-right
                pos_x = width - reporter_diameter - margin_x
                pos_y = height - reporter_diameter - margin_y
                
                reporter_clip = (ImageClip(reporter_np, transparent=True)
                               .with_duration(duration)
                               .with_start(start_time)
                               .with_position((pos_x, pos_y))
                               .with_fps(self.VIDEO_FPS))
                
                return reporter_clip
        except Exception as e:
            logger.error(f"Error creating reporter overlay: {e}")
        
        return None
    
    def _create_title_overlay(self, title: str, width: int, height: int,
                             duration: float, start_time: float) -> Optional[VideoClip]:
        """Create title text overlay in bottom-left corner."""
        try:
            logger.info(f"Creating title overlay: '{title}' (duration: {duration:.2f}s, start: {start_time:.2f}s)")
            
            font_size = int(height * self.TITLE_FONT_SIZE_RATIO)
            margin_x = int(width * self.TITLE_MARGIN_RATIO)
            margin_y = int(height * self.TITLE_MARGIN_RATIO)
            
            # Calculate max width (accounting for reporter overlay)
            reporter_area_width = int(height * self.REPORTER_SIZE_RATIO) + margin_x * 2
            max_width = width - margin_x * 2 - reporter_area_width
            max_width = max(200, max_width)
            
            # Position from bottom - ensure it's visible
            pos_y = height - margin_y - font_size * 3  # Give more space
            
            logger.info(f"Title overlay params: font_size={font_size}, pos=({margin_x}, {pos_y}), max_width={max_width}")
            
            # Try fonts in priority order: custom font, then system fonts
            font_options = [
                str(self.font_path) if self.font_path.exists() else None,
                "DejaVu-Sans-Bold",
                "Liberation-Sans-Bold",
                "DejaVu-Sans",
                "Liberation-Sans",
                "Arial-Bold",
                "Arial"
            ]

            font_arg = None
            for font in font_options:
                if font is None:
                    continue
                try:
                    # Test if font works by trying to create a temporary TextClip
                    from PIL import ImageFont
                    if font.startswith('/'):
                        # File path font
                        ImageFont.truetype(font, 12)
                    else:
                        # System font name
                        ImageFont.truetype(font, 12)
                    font_arg = font
                    logger.info(f"Using font: {font}")
                    break
                except Exception as e:
                    logger.debug(f"Font {font} not available: {e}")
                    continue

            if font_arg is None:
                # Last resort - let moviepy handle it
                font_arg = "Arial"
                logger.warning("No fonts available, using Arial as last resort")
            
            # Create title clip with better visibility settings
            title_clip = (TextClip(font=font_arg,
                                 text=title,
                                 font_size=font_size,
                                 size=(max_width, None),
                                 color='white',
                                 stroke_color='black',
                                 stroke_width=2,  # Increase stroke width
                                 method='caption',
                                 text_align='left')
                        .with_duration(duration)
                        .with_start(start_time)
                        .with_position((margin_x, pos_y))
                        .with_fps(self.VIDEO_FPS))
            
            logger.info(f"Title overlay created successfully")
            return title_clip
            
        except Exception as e:
            logger.error(f"Error creating title overlay: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return None
    
    def get_video_url(self, video_path: Path) -> str:
        """Get the web URL for a video file."""
        try:
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            relative_path = video_path.relative_to(static_dir)
            web_path = str(relative_path).replace('\\', '/')
            return f'/static/{web_path}'
        except Exception as e:
            logger.error(f"Error getting video URL for {video_path}: {e}")
            return ""
    
    def url_to_path(self, video_url: str) -> Optional[Path]:
        """Convert a web URL back to a local file path."""
        try:
            if not video_url.startswith('/static/'):
                logger.error(f"Invalid video URL format: {video_url}")
                return None
            
            # Remove /static/ prefix and convert to path
            relative_path = video_url[8:]  # Remove '/static/'
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            full_path = static_dir / relative_path
            
            return full_path
        except Exception as e:
            logger.error(f"Error converting video URL to path {video_url}: {e}")
            return None