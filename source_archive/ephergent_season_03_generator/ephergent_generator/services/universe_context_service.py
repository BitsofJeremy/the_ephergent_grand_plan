"""
Universe Context Service

Loads and manages the Ephergent Universe system prompt for consistent story generation.
Now database-driven using SystemConfig model.
"""

import os
from pathlib import Path
import logging
from ephergent_generator.models import SystemConfig

logger = logging.getLogger(__name__)

class UniverseContextService:
    """Service for managing Ephergent Universe context and prompts (database-driven)."""

    def __init__(self):
        logger.info("UniverseContextService initialized (using database)")

    def get_universe_prompt(self):
        """Get the full Ephergent Universe system prompt from database."""
        try:
            config = SystemConfig.query.filter_by(
                config_key='universe.prompt.season_03'
            ).first()

            if config and config.config_value:
                logger.debug(f"Loaded Ephergent Universe prompt from database ({len(config.config_value)} characters)")
                return config.config_value
            else:
                logger.warning("Universe prompt not found in database")
                return ""

        except Exception as e:
            logger.error(f"Error loading universe prompt from database: {str(e)}")
            return ""
    
    def build_story_prompt_with_universe_context(self, topic, genre=None, tone=None, word_count=900, dimension_location=None):
        """Build a story prompt that includes full Ephergent Universe context."""
        universe_context = self.get_universe_prompt()
        
        if not universe_context:
            logger.warning("No universe context available, using basic prompt")
            return self._build_basic_story_prompt(topic, genre, tone, word_count, dimension_location)
        
        # Build the comprehensive prompt with universe context
        prompt = f"{universe_context}\n\n"
        prompt += "=" * 80 + "\n"
        prompt += "STORY GENERATION REQUEST\n"
        prompt += "=" * 80 + "\n\n"
        
        prompt += f"**Topic/Concept**: {topic}\n\n"
        
        # Add dimension-specific context if provided
        if dimension_location:
            dimension_context = self._get_dimension_context(dimension_location)
            if dimension_context:
                prompt += f"**Primary Setting**: {dimension_context}\n\n"
        
        if genre:
            prompt += f"**Genre**: {genre}\n"
        
        if tone:
            prompt += f"**Tone**: {tone}\n"
        
        if word_count:
            prompt += f"**Target Length**: approximately {word_count} words\n"
        
        prompt += "\n**STORY GENERATION INSTRUCTIONS:**\n"
        prompt += "- Write this story as if it's being reported by Pixel Paradox for The Ephergent\n"
        prompt += "- Use the established Ephergent Universe lore, characters, and world-building\n"
        prompt += "- Incorporate the dimensional framework and universal constants as appropriate\n"
        prompt += "- Follow the narrative voice and article structure guidelines above\n"
        prompt += "- Include vivid, cinematic descriptions that fit the cyberpunk aesthetic\n"
        prompt += "- Make references to CLX currency, Cybernetic Dinosaurs, Corporate Corp, etc. when relevant\n"
        prompt += "- Focus on the conversational, friend-to-friend tone that Pixel uses\n\n"
        prompt += "Generate only the story content without a title. The story should feel like authentic Ephergent reporting."
        
        return prompt
    
    def _get_dimension_context(self, dimension_location):
        """Get specific context for a dimension."""
        dimension_contexts = {
            'prime_material': 'Prime Material - Urban Sci-Fi dimension with gleaming skyscrapers, chrome/electric blue/vibrant yellow palette',
            'nocturne_aeturnus': 'Nocturne Aeturnus - Gothic twilight dimension where emotions crystallize, indigo/purple/midnight blue palette',
            'cogsworth_cogitarium': 'Cogsworth Cogitarium - Steampunk clockwork cities with brass/copper/mahogany palette',
            'verdantia': 'Verdantia - Sentient flora civilization with all greens and bioluminescent accents',
            'the_edge': 'The Edge - Reality boundary dimension with shifting impossible colors, constantly transforming'
        }
        return dimension_contexts.get(dimension_location, '')
    
    def _build_basic_story_prompt(self, topic, genre=None, tone=None, word_count=900, dimension_location=None):
        """Fallback basic story prompt if universe context is unavailable."""
        prompt = f"Create a story for The Ephergent, an interdimensional cyberpunk publication.\n\n"
        prompt += f"Topic: {topic}\n\n"
        
        if dimension_location:
            prompt += f"Setting: {self._get_dimension_context(dimension_location)}\n"
        
        if genre:
            prompt += f"Genre: {genre}\n"
        
        if tone:
            prompt += f"Tone: {tone}\n"
        
        if word_count:
            prompt += f"Target length: approximately {word_count} words\n"
        
        prompt += "\nWrite in the style of underground cyberpunk journalism with a conversational tone."
        
        return prompt