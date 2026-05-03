import os
import json
import uuid
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont
from flask import current_app
from ephergent_generator.services.character_service import CharacterService
from ephergent_generator.services.gemini_service import GeminiService
from ephergent_generator.services.comfyui_service import ComfyUIService

logger = logging.getLogger(__name__)

class ImageService:
    """Service for generating and managing story images."""
    
    def __init__(self):
        self.character_service = CharacterService()
        self.gemini_service = GeminiService()
        self.comfyui_service = ComfyUIService()
        self.images_dir = self._get_images_directory()
        
    def _get_images_directory(self):
        """Get or create the images directory."""
        # Get the Flask app static directory (where Flask serves static files from)
        project_root = Path(__file__).parent.parent.parent
        images_dir = project_root / 'ephergent_generator' / 'static' / 'generated_images'
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir
    
    def generate_image_prompts(self, story_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate image prompts for different types of story images.
        
        Args:
            story_data: Dictionary containing story information
            
        Returns:
            Dictionary with image prompts for feature and article images
        """
        try:
            title = story_data.get('title', 'Untitled Story')
            content = story_data.get('content', '')
            genre = story_data.get('genre', 'sci-fi')
            tone = story_data.get('tone', 'mysterious')
            narrator_id = story_data.get('narrator_character_id')
            
            # Get character information if available
            character = None
            if narrator_id:
                character = self.character_service.get_character_by_id(narrator_id)
            
            character_context = ""
            character_stable_diffusion_prompt = ""
            if character:
                character_context = f"""
The story is narrated by {character['name']}, who is known for covering {', '.join(character.get('topics', []))}.
Consider their perspective and the types of visuals that would complement their storytelling style.
"""
                character_stable_diffusion_prompt = character.get('stable_diffusion_prompt', '')
                
                # If there's a character stable diffusion prompt, add it to the context
                if character_stable_diffusion_prompt:
                    character_context += f"""

Character Visual Reference (if the character appears in the story):
{character_stable_diffusion_prompt}

Use this character description if {character['name']} appears visually in the story content.
"""
            
            # Generate feature image prompt - use replicated method if character available
            if character:
                # Use the replicated generate_featured_image_prompt from reference code
                feature_prompt = self.generate_featured_image_prompt(story_data, character)
            else:
                # Generate improved prompt using the new method with variation hint
                feature_prompt = self._generate_article_essence_image_prompt(
                    story_data, character, "Focus on creating a compelling featured image that captures the overall essence and mood of the story."
                )
                if not feature_prompt:
                    feature_prompt = self._get_fallback_feature_prompt(title, genre, tone)
            
            # Generate article images prompts using improved method
            article_prompts = self._generate_article_image_prompts(story_data, character)
            
            prompts = {
                'feature_image_prompt': feature_prompt,
                **article_prompts
            }
            
            logger.info(f"Generated {len(prompts)} image prompts for story: {title}")
            return prompts
            
        except Exception as e:
            logger.error(f"Error generating image prompts: {str(e)}")
            return {}
    
    def _generate_article_essence_image_prompt(self, story_data: Dict[str, Any], character: Optional[Dict], variation_hint: str) -> Optional[str]:
        """
        Generate a single ComfyUI prompt for an article essence image using Gemini.
        Based on the reference implementation from zzz_example_reference_code/image_generator.py
        """
        if not self.gemini_service.client:
            logger.error("Gemini client not available for prompt generation.")
            return None

        title = story_data.get('title', 'Untitled Report')
        article_content = story_data.get('content', '')
        location = story_data.get('location', 'Unknown Location')

        # Character context handling - only mention characters found in article content
        character_mention_info = ""

        # Ephergent universe elements for context
        dimension_themes = [
            "Urban Sci-Fi Prime Material", "Gothic Horror Nocturne", "Steampunk Cogsworth",
            "Ecological Sci-Fi Verdantia", "Cosmic Horror The Edge", "Absurdist Bureaucracy",
            "Political Thriller", "Reality Stabilization", "Narrative Causality"
        ]
        
        universe_elements = [
            "The Ephergent HQ", "A1 AI Assistant", "CLX Crystallized Laughter", "Those Who Wait",
            "Reality Anchors", "Narrative Engine", "Dimensional Rifts", "Temporal Paradoxes",
            "Sentient Infrastructure", "Reality Glitches", "Void Incursions", "Anti-Creation",
            "Great Thought-Root Network", "Cybernetic Dinosaurs", "Probability Storms",
            "Data Streams", "Holographic Interfaces", "Quantum Computing", "Espresso Machine",
            "Dimensional Barriers", "Forbidden Knowledge", "Cyclical Collapse", "Reality Fatigue",
            "Orange Swingline Stapler"
        ]
        
        visual_keywords = [
            "unpredictable physics", "obsidian architecture", "stained-glass observatories",
            "clockwork mechanisms", "artisanal tea", "neon-lit megacities", "telepathic plants",
            "glowing root networks", "half-formed reality", "fragmented memories",
            "shifting geometric patterns", "flowing streams of light", "ancient symbols",
            "star charts", "data constructs", "cosmic void", "glitching displays",
            "unstable energy fluctuations", "corrupted data", "fractal patterns",
            "impossible geometries", "patchwork realities", "shadowy figures",
            "metallic tang of ozone", "cascading waterfalls (up and down)",
            "high-contrast lighting", "flickering neon", "shadowy ambiance"
        ]

        prompt_instruction = f"""
    Persona Context: You are an AI Art Director assisting with 'The Ephergent' interdimensional news service.
    Article Title: {title}
    Article Location: {location}
    Full Article Content:
    --- START ARTICLE ---
    {article_content}
    --- END ARTICLE ---
    {character_mention_info}
    Variation Hint: {variation_hint}

    MISSION:
    Generate a highly descriptive scene for a Stable Diffusion image to capture the essence of the article.
    This prompt should describe the setting, action, mood, and composition.

    CRITICAL INSTRUCTIONS:
    - **DO NOT describe the characters themselves.** Their visual descriptions will be added separately.
    - Focus entirely on the environment, what is happening, the atmosphere, and the visual style.
    - Describe a compelling visual composition for a single, impactful image.
    - Specify lighting and mood appropriate to the article's tone.
    - Avoid: Do not include the main narrator unless their action is the absolute core focus of the scene. No text overlays, panel numbers, or speech bubbles.

    OUTPUT FORMAT:
    Return ONLY a single string, which is the descriptive scene prompt.
    Example: "A chaotic server farm where endless rows of hamster wheels power a central conduit. The lighting is a sickly green, casting long, eerie shadows. The mood is dystopian and absurd."
    """

        try:
            logger.info(f"Generating '{variation_hint}' article SCENE prompt via Gemini...")
            response = self.gemini_service.client.models.generate_content(
                model=self.gemini_service.model_name,
                contents=prompt_instruction,
                config=self._get_generation_config()
            )
            
            # Safely access response text
            scene_prompt = ""
            if response.text:
                scene_prompt = response.text.strip()
            else:
                logger.error("Gemini response for scene prompt missing text.")
                return None

            # Clean up the response from the LLM
            import re
            cleaned_scene_prompt = re.sub(r'^```(?:json|text)?\n', '', scene_prompt, flags=re.MULTILINE)
            cleaned_scene_prompt = re.sub(r'\n```', '', cleaned_scene_prompt, flags=re.MULTILINE).strip()

            # Add Ephergent universe style elements
            style_prefix = "ArsMJStyle, dnddarkestfantasy, Kenva, fluxlisimo, fluxlisimo_neon,"
            post_style_suffix = """A digitally illustrated drawing in stylized 3D anime manga style with painterly cel-shading and hand-drawn textures, featuring volumetric lighting with soft watercolor-like gradients, dynamic comic book halftone patterns, realistic depth of field and atmospheric perspective, soft ambient occlusion shadows, cinematic rim lighting, subsurface scattering effects, realistic material textures and fabric physics, while maintaining clean manga lineart with NPR non-photorealistic rendering and traditional anime color palettes enhanced by atmospheric haze"""
            # post_style_suffix = ""

            # Construct final prompt without character descriptions for article images
            final_prompt_parts = [style_prefix, cleaned_scene_prompt]
            
            final_prompt = ", ".join(part.strip().rstrip(',') for part in final_prompt_parts)
            final_prompt += f" {post_style_suffix}"
            
            logger.info(f"Successfully generated and assembled '{variation_hint}' article essence image prompt.")
            return final_prompt

        except Exception as e:
            logger.error(f"Error in _generate_article_essence_image_prompt: {e}", exc_info=True)
            return None
    
    def _generate_article_image_prompts(self, story_data: Dict[str, Any], character: Optional[Dict]) -> Dict[str, str]:
        """Generate prompts for article images (beginning, middle, end) using improved method."""
        
        prompts = {}
        hints = {
            "beginning": "Focus on the inciting incident or the initial state of the story.",
            "middle": "Capture the peak of action, conflict, or a major turning point.",
            "end": "Illustrate the resolution, aftermath, or the new status quo."
        }

        for key, hint in hints.items():
            prompt = self._generate_article_essence_image_prompt(story_data, character, hint)
            if prompt:
                prompts[f"{key}_image_prompt"] = prompt
            else:
                logger.error(f"Failed to generate prompt for '{key}' image.")
                # Fallback to basic prompt
                title = story_data.get('title', 'Untitled')
                prompts[f"{key}_image_prompt"] = f"A sci-fi scene representing the {key} of '{title}'"
        
        return prompts
    
    def _get_fallback_feature_prompt(self, title: str, genre: str, tone: str) -> str:
        """Get a fallback feature image prompt when AI generation fails."""
        return f"A {tone} {genre} scene inspired by '{title}'"
    
    def _get_fallback_article_prompt(self, title: str, section: str, genre: str, tone: str) -> str:
        """Get a fallback article image prompt when AI generation fails."""
        return f"A {tone} {genre} scene representing the {section} of '{title}', "
    
    def _generate_dynamic_feature_title(self, title: str, character: Optional[Dict] = None) -> str:
        """
        Generate dynamic and absurd two-word titles for feature images.
        Adapted from example_reference_code for the main app.
        
        Args:
            title (str): Original article title
            character (Dict, optional): Character object for context
            
        Returns:
            str: Dynamic two-word title in uppercase
        """
        import random
        import re
        
        # Absurd prefix words themed to the Ephergent universe
        absurd_prefixes = [
            "QUANTUM", "PARADOX", "GLITCH", "NEURAL", "COSMIC", "TEMPORAL", "PIXEL", "VOID",
            "FRACTAL", "DIGITAL", "PLASMA", "CYBER", "NANO", "META", "HYPER", "ULTRA",
            "SYNTHETIC", "HOLOGRAPHIC", "DIMENSIONAL", "CHAOTIC", "UNSTABLE", "TWISTED",
            "CORRUPTED", "PHANTOM", "SPECTRAL", "ETHEREAL", "CRYSTALLINE", "MAGNETIC",
            "RADIOACTIVE", "SENTIENT", "ROGUE", "FERAL", "MUTANT", "EVOLVED", "QUANTUM",
            "PROBABILITY", "REALITY", "NARRATIVE", "CAUSALITY", "ENTROPY", "SINGULARITY"
        ]
        
        # Absurd suffix words for maximum chaos
        absurd_suffixes = [
            "CHAOS", "PARADOX", "GLITCH", "ERROR", "FAULT", "BREACH", "STORM", "WAVE",
            "PULSE", "SURGE", "SPIKE", "ANOMALY", "CRISIS", "MELTDOWN", "COLLAPSE",
            "EXPLOSION", "IMPLOSION", "FUSION", "FRACTURE", "RUPTURE", "DISTORTION",
            "MALFUNCTION", "OVERFLOW", "CASCADE", "FEEDBACK", "RESONANCE", "VIBRATION",
            "OSCILLATION", "FLUCTUATION", "DEVIATION", "CORRUPTION", "INFECTION",
            "CONTAMINATION", "MUTATION", "EVOLUTION", "TRANSFORMATION", "MANIFESTATION",
            "PHENOMENON", "OCCURRENCE", "EVENT", "INCIDENT", "SITUATION", "CONDITION"
        ]
        
        # Try to extract key words from the original title for context
        title_words = re.findall(r'\b[A-Z][A-Z]+\b|\b[A-Z][a-z]+\b', title.upper())
        title_keywords = [word for word in title_words if len(word) > 3 and word not in ['THE', 'AND', 'FOR', 'WITH', 'FROM']]
        
        # 60% chance to use original title structure, 40% chance for pure absurdity
        if title_keywords and random.random() < 0.6:
            # Use a keyword from the title with an absurd modifier
            keyword = random.choice(title_keywords)
            
            # If the keyword is long, use it as suffix; otherwise as prefix
            if len(keyword) > 6:
                prefix = random.choice(absurd_prefixes)
                display_title = f"{prefix} {keyword}"
            else:
                suffix = random.choice(absurd_suffixes)
                display_title = f"{keyword} {suffix}"
        else:
            # Pure absurdity - random combination
            prefix = random.choice(absurd_prefixes)
            suffix = random.choice(absurd_suffixes)
            display_title = f"{prefix} {suffix}"
        
        # Add character-specific variations
        if character and character.get('id'):
            if character['id'] == 'pixel_paradox' and random.random() < 0.3:
                # Pixel loves glitch terms
                glitch_terms = ["GLITCH", "ERROR", "CRASH", "BUG", "HACK", "VIRUS", "CODE"]
                if random.random() < 0.5:
                    display_title = f"{random.choice(glitch_terms)} {random.choice(absurd_suffixes)}"
                else:
                    display_title = f"{random.choice(absurd_prefixes)} {random.choice(glitch_terms)}"
            
            elif character['id'] == 'zephyr_glitch' and random.random() < 0.3:
                # Zephyr loves chaotic, fast-paced terms
                chaos_terms = ["SURGE", "STORM", "RUSH", "FLASH", "BOLT", "SPARK", "ZEPHYR"]
                display_title = f"{random.choice(chaos_terms)} {random.choice(absurd_suffixes)}"
            
            elif character['id'] == 'luminara_usha' and random.random() < 0.3:
                # Luminara loves mystical, cosmic terms
                mystic_terms = ["COSMIC", "ETHEREAL", "MYSTIC", "LUMINOUS", "ASTRAL", "CELESTIAL"]
                display_title = f"{random.choice(mystic_terms)} {random.choice(absurd_suffixes)}"
        
        return display_title
    
    def generate_featured_image_prompt(self, story_data: Dict[str, Any], character: Optional[Dict] = None) -> Optional[str]:
        """
        Generate a ComfyUI prompt for the FEATURED image.
        Replicated from example_reference_code/image_generator.py
        """
        import random
        
        title = story_data.get('title', 'Untitled Report')
        
        # Ephergent universe themes and elements (from reference code)
        dimension_themes = [
            "Urban Sci-Fi Prime Material", "Gothic Horror Nocturne", "Steampunk Cogsworth",
            "Ecological Sci-Fi Verdantia", "Cosmic Horror The Edge", "Absurdist Bureaucracy",
            "Political Thriller", "Reality Stabilization", "Narrative Causality"
        ]
        
        universe_elements = [
            "The Ephergent HQ", "A1 AI Assistant", "CLX Crystallized Laughter", "Those Who Wait",
            "Reality Anchors", "Narrative Engine", "Dimensional Rifts", "Sentient Infrastructure",
            "Reality Glitches", "Void Incursions", "Anti-Creation", "Great Thought-Root Network",
            "Cybernetic Dinosaurs", "Probability Storms", "Data Streams", "Holographic Interfaces",
            "Quantum Computing", "Espresso Machine", "Dimensional Barriers", "Forbidden Knowledge",
            "Cyclical Collapse", "Reality Fatigue", "Orange Swingline Stapler"
        ]
        
        visual_keywords = [
            "unpredictable physics", "obsidian architecture", "stained-glass observatories",
            "clockwork mechanisms", "artisanal tea", "neon-lit megacities", "telepathic plants",
            "glowing root networks", "half-formed reality", "time loops", "fragmented memories",
            "shifting geometric patterns", "flowing streams of light", "ancient symbols",
            "star charts", "data constructs", "cosmic void", "glitching displays",
            "unstable energy fluctuations", "corrupted data", "fractal patterns",
            "impossible geometries", "patchwork realities", "shadowy figures",
            "metallic tang of ozone", "cascading waterfalls", "high-contrast lighting",
            "flickering neon", "shadowy ambiance"
        ]
        
        # Style constants from reference code
        style_prefix = "ArsMJStyle, dnddarkestfantasy, Kenva, fluxlisimo, fluxlisimo_neon,"
        
        # Select elements based on character topics or random themes
        if character and character.get('topics'):
            selected_theme = random.choice(character['topics'])
            if not isinstance(selected_theme, str):
                selected_theme = random.choice(dimension_themes)
        else:
            selected_theme = random.choice(dimension_themes)
            
        selected_elements = random.sample(universe_elements + visual_keywords, k=random.randint(1, 3))
        
        # Text positioning and styling (from reference code)
        side_of_text = random.choice(["on the right. On the left side", "on the left. On the right side"])
        font_color_combo = random.choice([
            "light blue bold text with white", "dark red bold text with white", "white bold text with blue",
            "dark blue bold text with white", "dark green bold text with white",
            "light green bold text with white", "light red bold text with white", "purple bold text with white",
            "yellow bold text with black", "orange bold text with black", "neon pink bold text with black"
        ])
        
        # Generate dynamic title using our existing method
        display_title = self._generate_dynamic_feature_title(title, character)
        
        # Get character description
        character_desc = ""
        if character and character.get('stable_diffusion_prompt'):
            character_desc = character['stable_diffusion_prompt']
        elif character:
            character_desc = f"the reporter {character['name']}, interdimensional correspondent for The Ephergent"
        else:
            character_desc = "an interdimensional correspondent for The Ephergent"
        
        # Construct the final prompt (matching reference code structure)
        prompt_text = f"""
        {style_prefix} {font_color_combo} hard drop shadow that
        reads '{display_title}' {side_of_text} of image there is {character_desc},
        incorporating elements of '{selected_theme}' and {', '.join(selected_elements)}, black background. High detail, evocative.
        """
        
        # Clean up the prompt (join lines and strip extra whitespace)
        final_prompt = " ".join([line.strip() for line in prompt_text.strip().splitlines() if line.strip()])
        
        logger.info(f"Generated featured image prompt with dynamic title: '{display_title}'")
        return final_prompt
    
    def generate_placeholder_image(self, text: str, width: int = 800, height: int = 600, filename: str = None) -> Optional[Path]:
        """
        Generate a placeholder image with text when AI generation is not available.
        
        Args:
            text: Text to display on the image
            width: Image width
            height: Image height 
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to generated image or None if failed
        """
        try:
            if not filename:
                filename = f"placeholder_{uuid.uuid4().hex[:8]}.png"
            
            # Ensure filename ends with .png
            if not filename.endswith('.png'):
                filename += '.png'
                
            image_path = self.images_dir / filename
            
            # Create image with cyberpunk aesthetic
            image = Image.new('RGB', (width, height), color='#000000')  # Black background
            draw = ImageDraw.Draw(image)
            
            # Try to load a nice font, fall back to default if not available
            try:
                # Try to find a monospace font that fits the cyberpunk aesthetic
                font_size = min(width, height) // 20
                font = ImageFont.truetype('DejaVuSansMono.ttf', font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            
            # Wrap text for better display
            words = text.split()
            lines = []
            current_line = []
            max_chars_per_line = width // 12  # Approximate character width
            
            for word in words:
                if len(' '.join(current_line + [word])) <= max_chars_per_line:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)  # Single word longer than line
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Limit to reasonable number of lines
            lines = lines[:8]
            
            # Calculate text positioning
            if font:
                line_height = font.getbbox('A')[3] + 5
            else:
                line_height = 20
                
            total_text_height = len(lines) * line_height
            start_y = (height - total_text_height) // 2
            
            # Draw each line centered
            for i, line in enumerate(lines):
                if font:
                    bbox = font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                else:
                    text_width = len(line) * 8  # Approximate
                
                x = (width - text_width) // 2
                y = start_y + i * line_height
                
                # Draw text with cyberpunk pink color
                draw.text((x, y), line, fill='#F12CA5', font=font)
            
            # Add some cyberpunk-style decorative elements
            # Corner brackets
            bracket_size = 30
            bracket_thickness = 3
            pink = '#F12CA5'
            
            # Top-left bracket
            draw.rectangle([20, 20, 20 + bracket_size, 20 + bracket_thickness], fill=pink)
            draw.rectangle([20, 20, 20 + bracket_thickness, 20 + bracket_size], fill=pink)
            
            # Top-right bracket
            draw.rectangle([width - 20 - bracket_size, 20, width - 20, 20 + bracket_thickness], fill=pink)
            draw.rectangle([width - 20 - bracket_thickness, 20, width - 20, 20 + bracket_size], fill=pink)
            
            # Bottom-left bracket
            draw.rectangle([20, height - 20 - bracket_thickness, 20 + bracket_size, height - 20], fill=pink)
            draw.rectangle([20, height - 20 - bracket_size, 20 + bracket_thickness, height - 20], fill=pink)
            
            # Bottom-right bracket
            draw.rectangle([width - 20 - bracket_size, height - 20 - bracket_thickness, width - 20, height - 20], fill=pink)
            draw.rectangle([width - 20 - bracket_thickness, height - 20 - bracket_size, width - 20, height - 20], fill=pink)
            
            # Save image
            image.save(image_path, 'PNG')
            logger.info(f"Generated placeholder image: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error generating placeholder image: {str(e)}")
            return None
    
    def save_image_prompts_to_file(self, story_id: int, prompts: Dict[str, str]) -> Optional[Path]:
        """
        Save image prompts to a JSON file for later use.
        
        Args:
            story_id: ID of the story
            prompts: Dictionary of image prompts
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            prompts_dir = self.images_dir / 'prompts'
            prompts_dir.mkdir(exist_ok=True)
            
            filename = f"story_{story_id}_prompts.json"
            prompts_path = prompts_dir / filename
            
            # Add metadata
            prompt_data = {
                'story_id': story_id,
                'generated_at': str(uuid.uuid4()),  # Using UUID as timestamp placeholder
                'prompts': prompts
            }
            
            with open(prompts_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, indent=2)
            
            logger.info(f"Saved image prompts for story {story_id} to: {prompts_path}")
            return prompts_path
            
        except Exception as e:
            logger.error(f"Error saving image prompts: {str(e)}")
            return None
    
    def load_image_prompts_from_file(self, story_id: int) -> Optional[Dict[str, str]]:
        """
        Load image prompts from a JSON file.
        
        Args:
            story_id: ID of the story
            
        Returns:
            Dictionary of image prompts or None if not found
        """
        try:
            prompts_dir = self.images_dir / 'prompts'
            filename = f"story_{story_id}_prompts.json"
            prompts_path = prompts_dir / filename
            
            if not prompts_path.exists():
                logger.warning(f"No saved prompts found at: {prompts_path}")
                return None
            
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
            
            prompts = prompt_data.get('prompts', {})
            if prompts:
                logger.info(f"Loaded {len(prompts)} saved image prompts for story {story_id}")
                return prompts
            else:
                logger.warning(f"No prompts found in file for story {story_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading image prompts for story {story_id}: {str(e)}")
            return None
    
    def generate_story_images(self, story_data: Dict[str, Any]) -> Dict[str, Optional[Path]]:
        """
        Generate all images for a story (feature + article images).
        Uses ComfyUI if available, otherwise falls back to placeholder images.
        
        Args:
            story_data: Dictionary containing story information
            
        Returns:
            Dictionary mapping image types to file paths
        """
        try:
            story_id = story_data.get('id', 'unknown')
            title = story_data.get('title', 'Untitled Story')
            
            # Generate image prompts
            prompts = self.generate_image_prompts(story_data)
            
            # Save prompts to file
            self.save_image_prompts_to_file(story_id, prompts)
            
            # Check if ComfyUI is available and enabled
            if self.comfyui_service.is_available():
                logger.info(f"Using ComfyUI for story {story_id} image generation")
                return self._generate_with_comfyui(story_data)
            else:
                logger.info(f"ComfyUI not available, using placeholder images for story {story_id}")
                return self._generate_placeholders(story_data, prompts)
            
        except Exception as e:
            logger.error(f"Error generating story images: {str(e)}")
            return {}
    
    def _generate_with_comfyui(self, story_data: Dict[str, Any]) -> Dict[str, Optional[Path]]:
        """Generate images using ComfyUI service."""
        try:
            # Load saved image prompts and add them to story_data
            story_id = story_data.get('id', 'unknown')
            saved_prompts = self.load_image_prompts_from_file(story_id)
            
            if saved_prompts:
                # Add the saved prompts to story_data for ComfyUI service to use
                story_data['image_prompts'] = saved_prompts
                logger.info(f"Added {len(saved_prompts)} saved prompts to story data for ComfyUI")
            else:
                logger.warning(f"No saved prompts found for story {story_id}, ComfyUI will generate fallback prompts")
            
            return self.comfyui_service.generate_story_images(story_data, self.images_dir)
        except Exception as e:
            logger.error(f"ComfyUI generation failed: {e}")
            # Fallback to placeholders
            prompts = self.generate_image_prompts(story_data)
            return self._generate_placeholders(story_data, prompts)
    
    def _generate_placeholders(self, story_data: Dict[str, Any], prompts: Dict[str, str]) -> Dict[str, Optional[Path]]:
        """Generate placeholder images as fallback."""
        story_id = story_data.get('id', 'unknown')
        title = story_data.get('title', 'Untitled Story')
        images = {}
        
        # Feature image
        feature_prompt = prompts.get('feature_image_prompt', title)
        feature_filename = f"story_{story_id}_feature.png"
        images['feature'] = self.generate_placeholder_image(
            f"FEATURE IMAGE\n\n{feature_prompt[:200]}...",
            width=1200, height=630, filename=feature_filename
        )
        
        # Article images
        for section in ['beginning', 'middle', 'end']:
            prompt_key = f'{section}_image_prompt'
            if prompt_key in prompts:
                article_filename = f"story_{story_id}_{section}.png"
                images[section] = self.generate_placeholder_image(
                    f"{section.upper()}\n\n{prompts[prompt_key][:200]}...",
                    width=800, height=600, filename=article_filename
                )
        
        logger.info(f"Generated {len([p for p in images.values() if p])} placeholder images for story {story_id}")
        return images
    
    def get_image_url(self, image_path: Path) -> str:
        """
        Get the web URL for an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Web URL for the image
        """
        try:
            # Get project root and Flask static directory
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            relative_path = image_path.relative_to(static_dir)
            
            # Convert to web path
            web_path = str(relative_path).replace('\\', '/')
            return f'/static/{web_path}'
            
        except Exception as e:
            logger.error(f"Error getting image URL for {image_path}: {str(e)}")
            return ""
    
    def url_to_path(self, image_url: str) -> Optional[Path]:
        """
        Convert a web URL back to a local file path.
        
        Args:
            image_url: Web URL of the image
            
        Returns:
            Path to the local image file
        """
        try:
            if not image_url.startswith('/static/'):
                logger.error(f"Invalid image URL format: {image_url}")
                return None
            
            # Remove /static/ prefix and convert to path
            relative_path = image_url[8:]  # Remove '/static/'
            project_root = Path(__file__).parent.parent.parent
            static_dir = project_root / 'ephergent_generator' / 'static'
            full_path = static_dir / relative_path
            
            return full_path
        except Exception as e:
            logger.error(f"Error converting image URL to path {image_url}: {e}")
            return None

    def _get_generation_config(self):
        """Get generation config for Gemini API."""
        try:
            from google.genai import types
            return types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        except ImportError:
            return None
