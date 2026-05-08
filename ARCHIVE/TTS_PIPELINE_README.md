# TTS Pipeline — Agent Briefing

## What Was Built

A new **single-narrator TTS pipeline** for The Ephergent, replacing the old multi-voice Kokoro+Qwen approach (Qwen was slow, voice switches were jarring).

### New Components

**1. The Ephergent Signal** (narrator character)
- File: `src/content/crew/signal.md` in the ephergent.com repo
- Role: Station Announcer AI — the calm, professional British female voice that narrates all episodes
- Voice: Kokoro TTS `bf_emma(0.7)+af_sarah(0.3)` blend
- Origin: Originally a Cogsworth broadcast relay operator, uploaded into the Signal itself when the station went dimensional. Now she IS the broadcast.

**2. Pre-processor script** (`scripts/markdown_to_tts.py` in ephergent.com repo)
- Converts episode markdown files into clean `.tts.txt` files
- Handles both prose narratives (S01 style) and radio-play scripts (S03 style)
- Strips all markdown Kokoro reads poorly: `**`, `--`, `*[`, `*(Sound:)*`, `!!` markers, coffee charts, etc.
- For radio-play episodes: transforms `**PIXEL:**` → `Pixel says, "dialogue"`
- Assembles TTS text with Signal's intro/outro

**3. Generated TTS text files** (`public/audio/season{1,2,3}/tts_text/*.tts.txt`)
- 31 files already generated across all 3 seasons
- Ready for Kokoro TTS generation

---

## How to Generate TTS Text (Step 1)

From the ephergent.com repo:

```bash
# Single episode
python scripts/markdown_to_tts.py --episode S01E01

# Full season
python scripts/markdown_to_tts.py --season 01

# All episodes
python scripts/markdown_to_tts.py --all
```

Output goes to `public/audio/seasonXX/tts_text/SXXEXX.tts.txt`

---

## How to Generate Audio from TTS Text (Step 2)

After generating the `.tts.txt` file, feed it to Kokoro TTS:

**Voice:** `bf_emma(0.7)+af_sarah(0.3)` — this is the Signal's voice, pre-blended

**Endpoint:** `http://sprecher.nexus.home.test/v1` (local Kokoro service)

**Example call:**
```python
from openai import OpenAI

client = OpenAI(base_url="http://sprecher.nexus.home.test/v1", api_key="not-needed")
with client.audio.speech.with_streaming_response.create(
    model="kokoro",
    voice="bf_emma(0.7)+af_sarah(0.3)",
    input=tts_text,
    response_format="mp3"
) as response:
    response.stream_to_file(output_path)
```

**Output path:** `public/audio/season01/S01E01.mp3` (or appropriate season)

---

## Episode File Locations

Source episodes are in the **grand_plan repo**, not ephergent.com:

```
/Users/jeremy/Documents/current_projects/the_ephergent_projects/the_ephergent_grand_plan/
  phase_04_episodes/
    season01/  # Prose narrative format (S01E01-S01E10)
    season02/  # Prose narrative format (S02E01-S02E10)
    season03/  # Radio-play format with **CHARACTER:** lines (S03E01-S03E10 + S03E08x)
```

The pre-processor reads directly from this path (configured in the script).

---

## Key Decisions Made

1. **Narrator approach, not radio drama** — All dialogue read as narration by the Signal. No more multi-voice acting.

2. **"Pixel says," attribution for radio-play episodes** — `**PIXEL:** dialogue` → `Pixel says, "dialogue"`. Keeps character context clear without voice acting.

3. **Aggressive markdown stripping** — Kokoro reads `**`, `--`, `*[`, etc. as literal text. All stripped. The TTS text should read like a clean ebook.

4. **Coffee charts and scene markers stripped before dialogue extraction** — Critical ordering: these pre-processing steps must run before the `**CHARACTER:**` regex, otherwise scene markers get absorbed into dialogue capture.

5. **A1 stays "A1"** — Not expanded to "A 1" in narration context. The `A1 → A 1` expansion from the old pipeline was for mixed human/AI dialogue; with a single narrator, "A1" reads fine.

---

## When Episodes Change

If an episode is edited, re-run the pre-processor to regenerate its `.tts.txt`:

```bash
python scripts/markdown_to_tts.py --episode S01E05  # regenerate one
python scripts/markdown_to_tts.py --season 01       # regenerate a whole season
```

Then re-generate the audio from the updated `.tts.txt`.

---

## Architecture Summary

```
Episode Markdown (grand_plan/phase_04_episodes/)
    ↓ markdown_to_tts.py
TTS Text (ephergent.com/public/audio/seasonXX/tts_text/SXXEXX.tts.txt)
    ↓ Kokoro TTS (bf_emma+af_sarah)
Audio MP3 (ephergent.com/public/audio/seasonXX/SXXEXX.mp3)
    ↓ served at
ephergent.com/audio/season01/S01E01.mp3
```
