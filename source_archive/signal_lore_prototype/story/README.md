# Story Content

This directory contains all story content for The Ephergent Signal.

## Structure

- `season_01/` - Season 1 story files
  - `episodes/` - Prose episode markdown files (12 episodes)
  - `radio_scripts/` - Radio play JSON scripts converted from episodes
  - `SEASON_BIBLE.md` - Season arc overview and episode summaries
- `generation/` - Story generation prompts and system prompts for AI-assisted writing

## Story Format

Episodes follow a five-act structure:
1. **Teaser** (250-350 words)
2. **Act One** (500-700 words)
3. **Act Two** (800-1000 words)
4. **Act Three** (500-650 words)
5. **Chronicle Entry** (100-150 words)

See `generation/EPISODE_GENERATION_PROMPT.md` for complete writing guidelines.

## Radio Scripts

Radio play scripts are JSON files that break down episodes into:
- Speaker attributions
- Timing estimates
- Audio cues (SFX, music)
- Narration vs dialogue

These scripts drive the audio production pipeline.
