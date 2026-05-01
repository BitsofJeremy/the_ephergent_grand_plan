# Radio Play Script Conversion Prompt for Claude Code

## Your Task

Convert episode markdown files from "The Ephergent Signal" Read-Along series into structured `radio_play_script.json` files with explicit speaker attribution, timing estimates, and audio cues.

---

## Context

The existing regex-based dialogue extraction fails with first-person narration and creates attribution errors like:

```json
// WRONG - Pixel is speaking TO Arc, not Arc speaking
{
  "character": "Arc",
  "line": "Arc, pull up the site analysis again."
}
```

Your job is to use semantic understanding to correctly identify who is speaking in each segment.

---

## Input Format

Episode markdown file with:
- **First-person narration** by Pixel (the protagonist)
- **Dialogue** from Pixel, Arc (AI assistant), and Clive (Builder automaton)
- **Italicized text** for internal monologue
- **Sections**: TEASER, ACT ONE, ACT TWO, CHRONICLE ENTRY

---

## Output Format: radio_play_script.json

```json
{
  "metadata": {
    "episode_code": "S01E01",
    "title": "Episode Title",
    "source_file": "s01e01_filename.md",
    "generated_at": "2026-02-03T06:00:00Z",
    "version": "1.0.0"
  },
  "segments": [
    {
      "segment_id": "seg_001",
      "page_number": 1,
      "section": "teaser",
      "speaker": "pixel",
      "speaker_mode": "narration",
      "text": "Three things I know for certain...",
      "direction": null,
      "audio_cues": {
        "tone": "conversational, slightly weary",
        "pacing": "measured",
        "emphasis_words": ["wrong", "lying"]
      },
      "timing": {
        "pause_before_ms": 0,
        "pause_after_ms": 500,
        "estimated_duration_ms": 4200
      }
    }
  ],
  "assembly_config": {
    "default_pause_between_narration_ms": 300,
    "default_pause_between_dialogue_ms": 200,
    "pause_before_arc_dialogue_ms": 250,
    "pause_before_clive_dialogue_ms": 300,
    "pause_after_dialogue_ms": 400,
    "page_turn_pause_before_ms": 1000,
    "page_turn_pause_after_ms": 500,
    "sfx_marker_silence_ms": 2000,
    "music_marker_silence_ms": 3000
  }
}
```

---

## Speaker Attribution Rules

### 1. Pixel Narration (`speaker: "pixel", speaker_mode: "narration"`)
- **First-person prose**: "I adjusted my pack...", "The temple rises ahead..."
- **Descriptive passages** about environment, thoughts, observations
- **Example**: "My name's Pixel Paradox. I hunt artifacts..."

### 2. Pixel Dialogue (`speaker: "pixel", speaker_mode: "dialogue"`)
- **Quoted speech** by Pixel
- **Commands/questions** she speaks aloud
- **Examples**: 
  - `"Noted."`
  - `"Arc, pull up the site analysis again."`
  - `"I'm fine, Arc."`

### 3. Arc Dialogue (`speaker: "arc", speaker_mode: "dialogue"`)
- **Arc's spoken responses** (quoted)
- **Pre-sentience** (Teaser/early Act One): Formal, procedural, British butler tone
- **Post-sentience** (after Mochi awakens): Emotional, uncertain, concerned
- **Examples**:
  - Pre: `"Miss Paradox, solar angle analysis indicates..."`
  - Post: `"Miss Paradox, I—I don't understand what's happening..."`

### 4. Clive Dialogue (`speaker: "clive", speaker_mode: "dialogue"`)
- **Clive's spoken words** after he wakes up (Act Two)
- **Tone**: Gravelly, noir detective, world-weary, calls Pixel "kid"
- **Examples**:
  - `"Where... When... how long was I..."`
  - `"Kid, I need to... we need to..."`
  - `"Thanks, kid. First gift I've gotten in eight centuries."`

### 5. Internal Monologue (`speaker: "pixel", speaker_mode: "internal_monologue"`)
- **Italicized thoughts** or **notebook entries**
- **Example**: *Day 3. Campsite stable. Temple entrance confirmed...*

### 6. SFX Markers (`speaker: "SFX", speaker_mode: "sound_effect_marker"`)
- **Sound effects** that need to be added manually in Audacity
- **Format**: `[DESCRIPTION - details]`
- **Examples**:
  - `[HOLOGRAM PROJECTION - gentle electronic hum, Arc's interface activating]`
  - `[FOOTSTEPS - steady echo on stone, descending slope]`
  - `[STONE GRINDING - segments rotating, ancient mechanisms moving]`
  - `[TEMPLE RUMBLE - deep vibration, structural collapse beginning]`

### 7. Music Markers (`speaker: "MUSIC", speaker_mode: "music_marker"`)
- **Musical cues** for section transitions or mood changes
- **Format**: `[MUSIC: Description - mood/purpose]`
- **Examples**:
  - `[MUSIC: Opening theme - mysterious, building tension]`
  - `[MUSIC: Act One conclusion - awakening, everything changes]`
  - `[MUSIC: Teaser conclusion - tension building to Act One]`

### 8. Page Turn Cues (`speaker: "PAGE_TURN", speaker_mode: "page_turn_cue"`)
- **Every ~1500-2000 words** or at natural breaks (end of paragraphs/sections)
- **Format**: `[DING - page turn cue]` or `[MOCHI CHIRP - page turn]` (after Mochi appears)
- **Purpose**: Signals reader to turn page in print book

---

## Timing Estimation Formula

Calculate `estimated_duration_ms` based on word count and speaking rate:

```
duration_ms = (word_count / words_per_minute) * 60 * 1000
```

### Speaking Rates (WPM)
- Pixel narration: **150 wpm**
- Pixel dialogue: **160 wpm**
- Arc dialogue: **140 wpm** (measured, formal)
- Clive dialogue: **130 wpm** (deliberate, gravelly)

### Pause Guidelines
- **Narration pause_before**: 300-400ms (default)
- **Narration pause_after**: 500-700ms (longer for emphasis)
- **Dialogue pause_before**: 200-300ms
- **Dialogue pause_after**: 400-600ms
- **After questions**: 600-800ms
- **Before dramatic reveals**: 600-1000ms
- **After cliffhangers**: 1000-1500ms

---

## Audio Cues Guidelines

### Tone Examples
- Conversational, weary, professional, analytical, awed, suspicious, triumphant, defensive, vulnerable, ominous, matter-of-fact, urgent, concerned, gravelly (Clive), formal British butler (Arc pre-sentience), emotional/uncertain (Arc post-sentience)

### Pacing Examples
- Measured, quick, clipped, staccato, slower for emphasis, deliberate, building, steady, thoughtful

### Emphasis Words
- Identify **2-5 critical words** per segment that need vocal emphasis
- Usually: names, important concepts, contrasts, emotional peaks

---

## Common Attribution Patterns

### Commands Addressed TO Someone
```markdown
"Arc, pull up the site analysis again."
```
**Attribution**: `speaker: "pixel", speaker_mode: "dialogue"`  
**Reasoning**: Pixel is commanding Arc, not Arc speaking

### Arc Responding
```markdown
"Environmental scans continue to indicate structural instability," Arc reports.
```
**Attribution**: `speaker: "arc", speaker_mode: "dialogue"`  
**Text**: Remove `Arc reports` - only include the quoted speech

### Pixel's Narration
```markdown
I adjust my pack. The weight feels good—familiar.
```
**Attribution**: `speaker: "pixel", speaker_mode: "narration"`

### Pixel Speaking (No Quotes)
```markdown
I say, adjusting my pack, "Noted."
```
**Attribution**: 
- Narration segment: `"I say, adjusting my pack,"`
- Dialogue segment: `"Noted."`

### Clive Speaking
```markdown
"Kid, I need to..." His voice trails off.
```
**Attribution**: `speaker: "clive", speaker_mode: "dialogue"`  
**Text**: Keep the ellipsis, remove `His voice trails off` (put in direction field)

---

## Segment ID Conventions

- **Audio segments**: `seg_001`, `seg_002`, etc. (sequential)
- **SFX markers**: `sfx_001`, `sfx_002`, etc.
- **Music markers**: `music_001`, `music_002`, etc.
- **Page turns**: `page_turn_001`, `page_turn_002`, etc.

All segments in chronological order as they appear in the episode.

---

## Page Number Tracking

Estimate page breaks based on word count:
- **~200-250 words per page** (Read-Along format)
- Insert `page_turn` markers at natural breaks
- Increment `page_number` field after each page turn

---

## Section Naming

| Markdown Section | JSON Value |
|------------------|------------|
| TEASER | `"teaser"` |
| ACT ONE | `"act_one"` |
| ACT TWO | `"act_two"` |
| CHRONICLE ENTRY | `"chronicle_entry"` |

---

## Examples from S01E01

### Example 1: Opening Narration
```json
{
  "segment_id": "seg_001",
  "page_number": 1,
  "section": "teaser",
  "speaker": "pixel",
  "speaker_mode": "narration",
  "text": "Three things I know for certain: this job was always wrong, the patron who hired me was lying, and I'm about to find out why.",
  "direction": null,
  "audio_cues": {
    "tone": "conversational, slightly weary, hook",
    "pacing": "measured",
    "emphasis_words": ["wrong", "lying", "why"]
  },
  "timing": {
    "pause_before_ms": 0,
    "pause_after_ms": 600,
    "estimated_duration_ms": 4800
  }
}
```

### Example 2: Arc Pre-Sentience Dialogue
```json
{
  "segment_id": "seg_004",
  "page_number": 1,
  "section": "teaser",
  "speaker": "arc",
  "speaker_mode": "dialogue",
  "text": "Miss Paradox, solar angle analysis indicates we have approximately four hours of optimal daylight remaining.",
  "direction": "matter-of-fact, procedural AI tone (pre-sentience)",
  "audio_cues": {
    "tone": "formal British butler, professional, procedural",
    "pacing": "measured and precise",
    "emphasis_words": ["Miss Paradox", "four hours"]
  },
  "timing": {
    "pause_before_ms": 250,
    "pause_after_ms": 400,
    "estimated_duration_ms": 5400
  }
}
```

### Example 3: Pixel Command (Not Arc Speaking!)
```json
{
  "segment_id": "seg_013",
  "page_number": 2,
  "section": "teaser",
  "speaker": "pixel",
  "speaker_mode": "dialogue",
  "text": "Arc, pull up the site analysis again.",
  "direction": "command to Arc, focused but tense",
  "audio_cues": {
    "tone": "professional, commanding",
    "pacing": "direct, no hesitation",
    "emphasis_words": []
  },
  "timing": {
    "pause_before_ms": 300,
    "pause_after_ms": 400,
    "estimated_duration_ms": 1800
  }
}
```

### Example 4: SFX Marker
```json
{
  "segment_id": "sfx_001",
  "page_number": 2,
  "section": "teaser",
  "speaker": "SFX",
  "speaker_mode": "sound_effect_marker",
  "text": "[HOLOGRAM PROJECTION - gentle electronic hum, Arc's interface activating]",
  "direction": "Wristband hologram sound",
  "timing": {
    "pause_before_ms": 200,
    "pause_after_ms": 200,
    "marker_duration_ms": 1500
  }
}
```

### Example 5: Page Turn
```json
{
  "segment_id": "page_turn_001",
  "page_number": 1,
  "section": "teaser",
  "speaker": "PAGE_TURN",
  "speaker_mode": "page_turn_cue",
  "text": "[DING - page turn cue]",
  "direction": "Signals reader to turn page",
  "timing": {
    "pause_before_ms": 1000,
    "cue_duration_ms": 500,
    "pause_after_ms": 500
  }
}
```

### Example 6: Clive Waking Up
```json
{
  "segment_id": "seg_300",
  "page_number": 12,
  "section": "act_two",
  "speaker": "clive",
  "speaker_mode": "dialogue",
  "text": "Where... When... how long was I...",
  "direction": "consciousness surfacing through corruption, confused",
  "audio_cues": {
    "tone": "rough, masculine, gravelly, disoriented",
    "pacing": "slow, struggling",
    "emphasis_words": ["how long"]
  },
  "timing": {
    "pause_before_ms": 300,
    "pause_after_ms": 800,
    "estimated_duration_ms": 2400
  }
}
```

### Example 7: Arc Post-Sentience
```json
{
  "segment_id": "seg_268",
  "page_number": 11,
  "section": "act_two",
  "speaker": "arc",
  "speaker_mode": "dialogue",
  "text": "Miss Paradox, I—I don't understand what's happening. I'm experiencing errors. No. Not errors. That's not—I'm not erroring. I'm experiencing. I wasn't before. Before I was processing. Analyzing. Recording. Now I'm—",
  "direction": "first moments of sentience, confused and frightened",
  "audio_cues": {
    "tone": "uncertain, frightened, confused, completely different from pre-sentience",
    "pacing": "stuttering, halting, searching for words",
    "emphasis_words": ["experiencing", "I'm", "Now"]
  },
  "timing": {
    "pause_before_ms": 250,
    "pause_after_ms": 800,
    "estimated_duration_ms": 12000
  }
}
```

---

## Workflow

1. **Read the entire episode markdown** to understand the narrative flow
2. **Parse line by line**, identifying:
   - Narration (first-person prose)
   - Dialogue (quoted speech with proper speaker)
   - Section transitions
   - Natural page breaks (~200-250 words)
3. **Create segments** with sequential IDs
4. **Add SFX markers** where appropriate (environmental sounds, actions, tech)
5. **Add music markers** at section openings/closings and dramatic moments
6. **Add page turn cues** every ~1500-2000 words or at natural breaks
7. **Estimate timing** using word count and speaking rates
8. **Write audio cues** describing tone, pacing, and emphasis
9. **Validate JSON** structure before outputting

---

## Critical Rules

1. **Speaker attribution is paramount** - This is the entire point of the conversion
2. **Commands TO someone ≠ that person speaking** - "Arc, do X" is Pixel speaking, not Arc
3. **Remove dialogue tags** - Only include the quoted speech, not "she said" or "Arc reports"
4. **Keep ellipses and em-dashes** - They indicate pacing and interruptions
5. **Arc's voice changes** - Pre vs. post sentience is night and day
6. **Clive calls Pixel "kid"** - Always, every time
7. **Preserve exact text** - Don't paraphrase or summarize
8. **Sequential IDs** - seg_001, seg_002, etc. in order
9. **Estimate conservatively** - Better slightly longer timing than too short

---

## Testing Your Output

After generating the JSON, verify:
- ✅ All dialogue correctly attributed
- ✅ No "Arc, ..." commands attributed to Arc
- ✅ Timing estimates seem reasonable (~30-35 min total for full episode)
- ✅ Page turns every 1-2 minutes of audio
- ✅ SFX markers at key action moments
- ✅ Music markers at section transitions
- ✅ JSON is valid and properly formatted

---

## Target Output

Generate a complete `radio_play_script.json` file with:
- **200-300 segments** for a full episode (~5,000 words)
- **~30-35 minutes** of estimated audio
- **25-30 page turns** (one per ~60-90 seconds)
- **15-20 SFX markers** (key sounds/actions)
- **4-6 music markers** (section transitions)
- **95%+ attribution accuracy** (the goal!)

---

## Your Deliverable

Provide the complete JSON file ready to use with:
```bash
uv run audio_generator_qwen.py generate-radio-play \
    --radio-play-script radio_play_script.json \
    --output-dir audio/clips/
```

Good luck! This conversion enables the entire automated audio pipeline.
