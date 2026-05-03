"""
Audio generation service for creating story podcasts using Text-to-Speech.
Supports both Kokoro TTS (local) and fallback to basic audio placeholder generation.
"""

import os
import json
import logging
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from flask import current_app

# Import pydub for audio processing (fallback for older Python versions)
try:
    from pydub import AudioSegment
    from pydub.generators import Sine, Sawtooth
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    Sine = None
    Sawtooth = None
    PYDUB_AVAILABLE = False

# Import OpenAI client for Kokoro TTS API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class AudioService:
    """Service for generating audio files from story content using character voices.

    This service provides Text-to-Speech (TTS) functionality for story generation,
    supporting both Kokoro TTS and fallback placeholder audio generation.

    Key Features:
    - Dynamic voice selection based on character metadata
    - Kokoro TTS integration for high-quality speech generation
    - Fallback placeholder audio generation
    - Audio post-processing with effects
    - Web URL and file path conversion utilities

    Attributes:
        kokoro_url (str): URL for the Kokoro TTS service
        enable_audio_effects (bool): Flag to enable/disable audio effects
        audio_dir (Path): Directory for storing generated audio files
        sound_effects_dir (Path): Directory containing audio effect files
        character_voices (Dict[str, str]): Mapping of character IDs to voice configurations
        kokoro_available (bool): Flag indicating Kokoro TTS service availability

    Note:
        This service requires OpenAI library and FFmpeg/pydub for full functionality.
    """
    
    def __init__(self):
        """Initialize the audio service with configuration and service dependencies.

        Configures the audio service by:
        1. Setting up Kokoro TTS URL
        2. Configuring audio effects
        3. Setting up audio and sound effects directories
        4. Loading character voice configurations
        5. Checking Kokoro TTS service availability

        Environment Variables:
            KOKORO_URL: URL for Kokoro TTS service (default: http://localhost:8880/v1)
            ENABLE_AUDIO_EFFECTS: Flag to enable audio effects (default: true)

        Attributes are set dynamically based on configuration and service state:
        - kokoro_url: URL for the TTS service
        - enable_audio_effects: Whether audio effects are enabled
        - audio_dir: Directory for storing generated audio files
        - sound_effects_dir: Directory for sound effect files
        - character_voices: Mapping of character voices
        - kokoro_available: Availability of Kokoro TTS service

        Raises:
            Various exceptions might be raised during configuration if services are misconfigured
        """
        # Configuration from environment (must be first)
        self.kokoro_url = os.environ.get('KOKORO_URL', 'http://localhost:8880/v1')
        self.enable_audio_effects = os.environ.get('ENABLE_AUDIO_EFFECTS', 'true').lower() in ('true', '1', 'yes', 't')
        
        self.audio_dir = self._get_audio_directory()
        self.sound_effects_dir = self._get_sound_effects_directory()
        self.character_voices = self._load_character_voices()
        self.kokoro_available = self._check_kokoro_available()
        
    def _get_audio_directory(self) -> Path:
        """Get or create the audio directory."""
        project_root = Path(__file__).parent.parent.parent
        audio_dir = project_root / 'ephergent_generator' / 'static' / 'generated_audio'
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir
        
    def _get_sound_effects_directory(self) -> Path:
        """Get the sound effects directory."""
        return Path(__file__).parent.parent / 'sound_effects'
        
    def _load_character_voices(self) -> Dict[str, str]:
        """Load character voice mappings from the character service."""
        try:
            from ephergent_generator.services.character_service import CharacterService
            character_service = CharacterService()
            character_voices = {}
            
            # Load all characters and their voice mappings
            for character in character_service.get_all_characters():
                char_id = character['id'].upper()
                # Use the voice field from character data if available, otherwise use default mapping
                voice = character.get('voice')
                if not voice:
                    logger.warning(f"Character {char_id} missing voice field, using fallback")
                    voice = self._get_default_voice_for_character(character['id'])
                character_voices[char_id] = voice
                logger.debug(f"Loaded voice for character {char_id}: {voice}")
            
            # Add default voice
            character_voices['DEFAULT'] = 'bf_v0isabella(1.5)+bm_v0george(1)+af_v0bella(0.5)+af_v0sarah(0.5)'
            
            logger.info(f"Loaded voices for {len(character_voices)} characters/default")
            return character_voices
            
        except Exception as e:
            logger.error(f"Error loading character voices: {str(e)}")
            return {'DEFAULT': 'bf_v0isabella(1.5)+bm_v0george(1)+af_v0bella(0.5)+af_v0sarah(0.5)'}
    
    def _get_default_voice_for_character(self, character_id: str) -> str:
        """Get default voice mapping for character based on reference data."""
        voice_mappings = {
            'pixel_paradox': 'bf_v0isabella(1.5)+bm_v0george(1)+af_v0bella(0.5)+af_v0sarah(0.5)',
            'a1_assistant': 'bm_lewis(0.8)+bm_george(1.5)+bf_alice(0.4)+am_adam(0.7)+am_onyx(0.4)',
            'clive_stapler_informant': 'am_onyx(0.5)+bm_v0george(1.3)+bm_lewis(0.7)',
            'zephyr_glitch': 'bm_lewis(0.7)+bf_lily(1)+am_onyx(0.3)+am_puck(0.3)+am_fenrir(0.3)',
            'luminara_usha': 'bf_lily(0.3)+af_nova(0.2)+hf_beta(1.5)',
            'om_kai': 'hm_omega(1.5)+am_puck(0.8)+bm_lewis(1)'
        }
        return voice_mappings.get(character_id, voice_mappings['pixel_paradox'])
    
    def _check_kokoro_available(self) -> bool:
        """Check if Kokoro TTS service is available."""
        if not OpenAI:
            logger.warning("OpenAI package not available - Kokoro TTS will not work")
            return False
            
        if not self.kokoro_url:
            logger.warning("KOKORO_URL not configured - Kokoro TTS will not work")
            return False
            
        try:
            client = OpenAI(base_url=self.kokoro_url, api_key="not-needed")
            client.models.list()
            logger.info(f"Kokoro TTS service available at {self.kokoro_url}")
            return True
        except Exception as e:
            logger.warning(f"Kokoro TTS service not available at {self.kokoro_url}: {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Kokoro TTS connection and return detailed status."""
        
        status = {
            'service': 'Kokoro TTS',
            'url': self.kokoro_url,
            'available': False,
            'error': None,
            'response_time': None,
            'models_available': []
        }
        
        if not OpenAI:
            status['error'] = 'OpenAI package not available'
            return status
            
        if not self.kokoro_url:
            status['error'] = 'KOKORO_URL not configured'
            return status
            
        try:
            start_time = time.time()
            client = OpenAI(base_url=self.kokoro_url, api_key="not-needed")
            models = client.models.list()
            response_time = time.time() - start_time
            
            status['response_time'] = round(response_time, 3)
            status['available'] = True
            status['models_available'] = [model.id for model in models.data] if hasattr(models, 'data') else []
            
            logger.info(f"Kokoro TTS connection test successful - {response_time:.3f}s response time, {len(status['models_available'])} models")
            
        except Exception as e:
            status['error'] = str(e)
            logger.warning(f"Kokoro TTS connection test failed - {e}")
            
        return status
    
    def strip_html_tags(self, text: str) -> str:
        """Remove HTML tags from text using regex."""
        return re.sub(r'<[^>]*>', '', text)
    
    def prepare_story_text_for_tts(self, story_data: Dict[str, Any]) -> str:
        """Prepare and clean story text for high-quality Text-to-Speech conversion.

        This method transforms raw story content into a TTS-friendly narrative
        by:
        1. Extracting story metadata
        2. Adding narrative context
        3. Cleaning HTML and markdown artifacts
        4. Removing platform-specific markers
        5. Formatting text for optimal TTS rendering

        Args:
            story_data (Dict[str, Any]): Dictionary containing story information with keys:
                - 'title': Story title
                - 'content': Story content
                - 'narrator_character_id': ID of the story's narrator

        Returns:
            str: Cleaned and formatted text ready for Text-to-Speech conversion

        Process:
        - Retrieve narrator information
        - Add introductory and closing narrative elements
        - Remove HTML tags
        - Strip markdown and platform-specific markers
        - Handle special formatting and character references

        Examples:
            >>> audio_service = AudioService()
            >>> story_data = {
            ...     'title': 'Quantum Horizons',
            ...     'content': '<p>A story about technological singularity...</p>',
            ...     'narrator_character_id': 'pixel_paradox'
            ... }
            >>> tts_text = audio_service.prepare_story_text_for_tts(story_data)
            >>> print(tts_text)  # Prints cleaned narrative text

        Note:
            - Narrator name is dynamically retrieved from character service
            - Handles various edge cases in story content
            - Designed to create an engaging audio narrative experience
        """
        title = story_data.get('title', 'Untitled Story')
        content = story_data.get('content', '')
        narrator_character_id = story_data.get('narrator_character_id')
        
        # Get narrator character info
        try:
            from ephergent_generator.services.character_service import CharacterService
            character_service = CharacterService()
            narrator = character_service.get_character_by_id(narrator_character_id)
            narrator_name = narrator.get('name', 'Unknown Reporter') if narrator else 'Unknown Reporter'
        except Exception as e:
            logger.error(f"Error getting narrator info: {str(e)}")
            narrator_name = 'Unknown Reporter'
        
        if not content:
            logger.warning("Story content is empty, TTS output will be minimal.")
            return f"{title}. This has been a broadcast from The Ephergent."
        
        # Build TTS-friendly text
        text = f"Hello from wherever and whenever you are. I'm {narrator_name} and this is The Ephergent. \n\n"
        text += f"In this neural dimensional broadcast: {title}. \n\n"
        text += "\n\n \n\n \n\n"  # Pause
        
        # Clean the content
        clean_content = self.strip_html_tags(content)
        
        # Remove various Ephergent-specific markers
        clean_content = re.sub(r'^\s*#+\s*.*$', '', clean_content, flags=re.MULTILINE)
        clean_content = re.sub(r'‼ Video created by The Ephergent\'s dimensionally-aware AI ‼', '', clean_content, flags=re.IGNORECASE)
        clean_content = re.sub(r'‼ Audio created by The Ephergent\'s dimensionally-aware AI \[Note: voices may look different in your dimension\.\] ‼', '', clean_content, flags=re.IGNORECASE)
        clean_content = re.sub(r'Your browser does not support the audio element\.', '', clean_content, flags=re.IGNORECASE)
        clean_content = re.sub(r'Illustration created by The Ephergent\'s dimensionally-aware AI ‼', '', clean_content, flags=re.IGNORECASE)
        clean_content = re.sub(r'‼ Moment Captured by The Ephergent\'s dimensionally-aware AI \[Note: images may sound different in your dimension\.\] ‼', '', clean_content, flags=re.IGNORECASE)
        clean_content = re.sub(r'<figure>.*?</figure>', '', clean_content, flags=re.DOTALL | re.IGNORECASE)
        clean_content = re.sub(r'(?:^|\n)\s*(?:\*\*|__|[*])?\s*Featured Characters:\s*.*', '', clean_content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Clean up formatting
        clean_content = clean_content.replace('*', "'")
        clean_content = re.sub(r'^\s*---\s*$', '', clean_content, flags=re.MULTILINE)
        clean_content = re.sub(r'\s*\n\s*', '\n', clean_content)
        clean_content = re.sub(r'[ \t]+', ' ', clean_content)

        # Look for mention of 'A1' exactly and replace with 'A 1'
        clean_content = re.sub(r'\bA1\b', 'A 1', clean_content)

        text += clean_content
        text += "\n\n Thank you for listening to this neural dimensional broadcast of The Ephergent. "
        
        return text.strip()
    
    def generate_speech_with_kokoro(self, text: str, output_path: Path, voice: str, speed: float = 1.0) -> Optional[Path]:
        """Generate speech audio using the Kokoro Text-to-Speech service.

        Converts input text to speech using the specified voice and speed settings.
        Supports streaming response and handles various edge cases.

        Args:
            text (str): Input text to be converted to speech
            output_path (Path): Destination path for the generated audio file
            voice (str): Voice configuration for speech generation
            speed (float, optional): Speech speed multiplier. Defaults to 1.0.

        Returns:
            Optional[Path]: Path to the generated audio file, or None if generation fails

        Raises:
            Various exceptions related to TTS service connectivity or file generation

        Process:
        - Checks Kokoro TTS service availability
        - Creates OpenAI client with custom base URL
        - Streams audio response to file
        - Validates generated audio file

        Examples:
            >>> audio_service = AudioService()
            >>> text = "Hello, this is a test of the Kokoro TTS service."
            >>> output_path = Path("/path/to/output.mp3")
            >>> result = audio_service.generate_speech_with_kokoro(text, output_path, "bf_v0isabella")
            >>> print(result)  # Might print: /path/to/output.mp3

        Note:
            - Requires OpenAI library and Kokoro TTS service to be configured
            - Audio generation might fail if text is empty or service is unavailable
        """
        if not self.kokoro_available or not OpenAI:
            logger.error("Kokoro TTS not available")
            return None
            
        if not text:
            logger.error("No text provided for speech generation")
            return None
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Generating speech with Kokoro TTS (Voice: {voice}, Speed: {speed})")
        logger.debug(f"Text length: {len(text)} chars. Output: {output_path}")
        
        try:
            client = OpenAI(base_url=self.kokoro_url, api_key="not-needed")
            with client.audio.speech.with_streaming_response.create(
                model="kokoro",
                voice=voice,
                speed=speed,
                input=text,
                response_format="mp3"
            ) as response:
                response.stream_to_file(output_path)
                
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully generated Kokoro audio: {output_path}")
                return output_path
            else:
                logger.error(f"Kokoro audio generation failed or empty file: {output_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating speech with Kokoro: {str(e)}")
            return None
    
    def generate_placeholder_audio(self, text: str, output_path: Path, duration: float = 30.0) -> Optional[Path]:
        """Generate a placeholder audio file when TTS is not available."""
        if not AudioSegment or not Sine:
            logger.error("pydub not available - cannot generate placeholder audio")
            return None
            
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate a cyberpunk-style placeholder tone
            # Use frequencies that match the Ephergent pink theme
            duration_ms = int(duration * 1000)
            
            # Create base tone (A4 note - 440 Hz)
            base_tone = Sine(440).to_audio_segment(duration=duration_ms)
            
            # Add harmonic (fifth - 660 Hz) 
            harmonic = Sine(660).to_audio_segment(duration=duration_ms) - 6  # 6dB quieter
            
            # Add cyberpunk glitch effect (high frequency)
            glitch = Sawtooth(1320).to_audio_segment(duration=duration_ms // 4) - 12  # Short burst
            
            # Combine tones
            combined = base_tone.overlay(harmonic)
            
            # Add glitch effects at intervals
            for i in range(0, duration_ms, duration_ms // 3):
                if i + len(glitch) <= duration_ms:
                    combined = combined.overlay(glitch, position=i)
            
            # Apply fade in/out
            combined = combined.fade_in(1000).fade_out(1000)
            
            # Reduce volume to reasonable level
            combined = combined - 20  # 20dB quieter
            
            # Export as MP3
            combined.export(output_path, format="mp3")
            logger.info(f"Generated placeholder audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating placeholder audio: {str(e)}")
            return None
    
    def add_audio_effects(self, audio_path: Path) -> Optional[Path]:
        """Add intro/outro effects to audio if available."""
        if not self.enable_audio_effects:
            logger.info("Audio effects disabled")
            return audio_path
            
        try:
            fade_in_path = self.sound_effects_dir / 'fade_in.mp3'
            fade_out_path = self.sound_effects_dir / 'fade_out.mp3'
            
            if not fade_in_path.exists() or not fade_out_path.exists():
                logger.warning(f"Audio effect files not found in {self.sound_effects_dir}")
                return audio_path
                
            logger.info("Adding intro/outro audio effects...")
            
            # Save with "_with_effects" suffix
            effects_filename = audio_path.stem + "_with_effects" + audio_path.suffix
            effects_path = audio_path.with_name(effects_filename)
            
            # Try FFmpeg first (Python 3.13+ compatible)
            if self._add_effects_with_ffmpeg(audio_path, fade_in_path, fade_out_path, effects_path):
                logger.info(f"Audio with effects saved to: {effects_path}")
                return effects_path
            # Fallback to pydub if available
            elif PYDUB_AVAILABLE and AudioSegment:
                logger.info("Falling back to pydub for audio effects...")
                return self._add_effects_with_pydub(audio_path, fade_in_path, fade_out_path, effects_path)
            else:
                logger.warning("No audio processing library available, skipping effects")
                return audio_path
            
        except Exception as e:
            logger.error(f"Error adding audio effects: {str(e)}")
            return audio_path
    
    def _add_effects_with_ffmpeg(self, main_audio: Path, fade_in: Path, fade_out: Path, output: Path) -> bool:
        """Add effects using FFmpeg (Python 3.13+ compatible)."""
        try:
            # Check if ffmpeg is available
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            if result.returncode != 0:
                logger.warning("FFmpeg not available")
                return False
                
            # Create temporary file list for ffmpeg concat
            temp_list_file = output.parent / f"temp_audio_list_{output.stem}.txt"
            
            with open(temp_list_file, 'w') as f:
                f.write(f"file '{fade_in.resolve()}'\n")
                f.write(f"file '{main_audio.resolve()}'\n")
                f.write(f"file '{fade_out.resolve()}'\n")
            
            # Run ffmpeg command
            cmd = [
                'ffmpeg', '-y',  # -y to overwrite output file
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_list_file),
                '-c', 'copy',
                str(output)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            if temp_list_file.exists():
                temp_list_file.unlink()
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"FFmpeg audio effects error: {e}")
            return False
    
    def _add_effects_with_pydub(self, main_audio: Path, fade_in: Path, fade_out: Path, output: Path) -> Optional[Path]:
        """Add effects using pydub (fallback for older Python versions)."""
        try:
            # Load audio segments
            fade_in_segment = AudioSegment.from_mp3(fade_in)
            main_audio_segment = AudioSegment.from_mp3(main_audio)  
            fade_out_segment = AudioSegment.from_mp3(fade_out)
            
            # Combine audio
            combined_audio = fade_in_segment + main_audio_segment + fade_out_segment
            
            # Export combined audio
            combined_audio.export(output, format="mp3")
            logger.info(f"Pydub audio with effects saved to: {output}")
            return output
            
        except Exception as e:
            logger.error(f"Pydub audio effects error: {e}")
            return main_audio
    
    def generate_story_audio(self, story_data: Dict[str, Any]) -> Optional[Path]:
        """Generate a complete audio file for a story with intelligent fallback.

        This method attempts to create an audio representation of a story using
        the following priority:
        1. Kokoro TTS with specified character voice
        2. Fallback placeholder audio generation
        3. Return None if audio generation fails

        Args:
            story_data (Dict[str, Any]): Dictionary containing story information with keys:
                - 'id': Unique story identifier
                - 'title': Story title
                - 'narrator_character_id': Character ID for narration
                - Other optional story metadata

        Returns:
            Optional[Path]: Path to the generated audio file, or None if generation fails

        Process:
        - Prepares text for Text-to-Speech conversion
        - Selects appropriate voice for the narrator
        - Attempts Kokoro TTS generation
        - Falls back to placeholder audio if Kokoro TTS fails
        - Adds audio effects to the generated audio

        Examples:
            >>> audio_service = AudioService()
            >>> story_data = {
            ...     'id': 'story_123',
            ...     'title': 'Quantum Echoes',
            ...     'narrator_character_id': 'pixel_paradox',
            ...     'content': 'A story about interdimensional adventures...'
            ... }
            >>> audio_path = audio_service.generate_story_audio(story_data)
            >>> print(audio_path)  # Might print: /path/to/story_123_audio.mp3

        Note:
            - Estimated audio duration is calculated based on text length
            - Audio generation may fail if TTS services are unavailable
        """
        try:
            story_id = story_data.get('id', 'unknown')
            title = story_data.get('title', 'Untitled Story')
            narrator_character_id = story_data.get('narrator_character_id', 'pixel_paradox')
            
            logger.info(f"Generating audio for story '{title}' (ID: {story_id})")
            
            # Prepare text for TTS
            tts_text = self.prepare_story_text_for_tts(story_data)
            if not tts_text:
                logger.error("No text prepared for TTS")
                return None
                
            # Get character voice
            voice = self.character_voices.get(narrator_character_id.upper(), self.character_voices.get('DEFAULT'))
            logger.info(f"Using voice for {narrator_character_id}: {voice}")
            
            # Generate unique audio filename with timestamp
            import time
            timestamp = int(time.time())
            audio_filename = f"story_{story_id}_audio_{timestamp}.mp3"
            audio_path = self.audio_dir / audio_filename
            
            # Try Kokoro TTS first
            if self.kokoro_available:
                generated_path = self.generate_speech_with_kokoro(tts_text, audio_path, voice)
                if generated_path:
                    # Add audio effects if available
                    final_path = self.add_audio_effects(generated_path)
                    logger.info(f"Successfully generated story audio: {final_path}")
                    return final_path
                else:
                    logger.warning("Kokoro TTS failed, falling back to placeholder audio")
            
            # Fallback to placeholder audio
            logger.info("Generating placeholder audio")
            # Estimate duration based on text length (average 150 words per minute)
            words = len(tts_text.split())
            estimated_duration = max(10.0, min(300.0, words / 150 * 60))  # 10s to 5min
            
            generated_path = self.generate_placeholder_audio(tts_text, audio_path, estimated_duration)
            if generated_path:
                final_path = self.add_audio_effects(generated_path)  
                logger.info(f"Successfully generated placeholder audio: {final_path}")
                return final_path
            else:
                logger.error("Failed to generate any audio")
                return None
                
        except Exception as e:
            logger.error(f"Error generating story audio: {str(e)}")
            return None
    
    def get_audio_url(self, audio_path: Path) -> str:
        """
        Get the web URL for an audio file.
        """
        try:
            # Get project root and Flask static directory
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            relative_path = audio_path.relative_to(static_dir)
            
            # Convert to web path
            web_path = str(relative_path).replace('\\', '/')
            return f'/static/{web_path}'
            
        except Exception as e:
            logger.error(f"Error getting audio URL for {audio_path}: {str(e)}")
            return ""
    
    def url_to_path(self, audio_url: str) -> Optional[Path]:
        """
        Convert a web URL back to a local file path.
        
        Args:
            audio_url: Web URL of the audio file
            
        Returns:
            Path to the local audio file
        """
        try:
            if not audio_url.startswith('/static/'):
                logger.error(f"Invalid audio URL format: {audio_url}")
                return None
            
            # Remove /static/ prefix and convert to path
            relative_path = audio_url[8:]  # Remove '/static/'
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            full_path = static_dir / relative_path
            
            return full_path
        except Exception as e:
            logger.error(f"Error converting audio URL to path {audio_url}: {e}")
            return None