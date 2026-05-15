# The Ephergent Audio Pipeline — Production Skill

Single-narrator audio generation for The Ephergent Signal using Kokoro TTS. All scripts live in `scripts/` in the grand_plan repo.

**For repo-level guidance** (sync workflow, episode structure, 13 Locked Rules), see `CLAUDE.md`.

---

## Overview

The pipeline converts episode markdown → clean TTS text → MP3 audio. Signal narrates all episodes in third person regardless of source format (prose or radio-play). No character voice separation — one blended narrator voice.

### Pipeline Stages

| Stage | Script | Output |
|-------|--------|--------|
| 1. Clean body | `preprocess_episodes.py` | `tts_text/seasonNN/SXXEXX.tts.txt` |
| 2. Extract summary | `generate_summaries.py` | `excerpts/seasonNN/SXXEXX.txt` |
| 3. Assemble final | `assemble_tts_text.py` | `tts_text/seasonNN/SXXEXX.tts.txt` (overwrite) |
| 4. Generate audio | `generate_audio.py` | `audio/seasonNN/SXXEXX.mp3` |

### Data Directory Structure

```
grand_plan/
├── episodes/seasonNN/        # Canonical episode source
├── excerpts/seasonNN/        # Signal-voice episode summaries (canonical)
│   └── SXXEXX.txt           # 2-3 sentence third-person summary
├── tts_text/seasonNN/        # Intermediate + final TTS text
│   └── SXXEXX.tts.txt       # Clean body → then final with intro/outro
└── audio/seasonNN/           # Permanent MP3 output (NOT ephemeral)
    └── SXXEXX.mp3
```

**Website copy:** `generate_audio.py` copies MP3s to `ephergent.com/public/audio/seasonNN/`. The `audio/` directory in grand_plan is the canonical store.

---

## Episode Formats and Preprocessing

### Prose Episodes (S01, S02)

Third-person narrative markdown. Preprocessing strips:
- YAML frontmatter
- `## LOCKED RULES CHECK` section and all following content
- `## COFFEE CHART` tables
- All `# ## ###` headers
- Scene markers `*[LOCATION. TIME.]*`
- Audio direction markers `*(Sound:...)*` `*(SFX:...)*`
- Square bracket annotations `[subtitled]`
- Bold/italic markdown (`**text**` → text, `*` → apostrophe)
- Featured Characters lines
- Platform markers (`!!...!!` blocks)

### Radio-Play Episodes (S03)

`**CHARACTER:**` dialogue blocks. Preprocessing transforms these to attribution form:

```
**PIXEL:**
This is dialogue from Pixel.
```

becomes:

```
Pixel says, "This is dialogue from Pixel."
```

Character aliases normalize variants: `pixel paradox`, `pixel` → Pixel; `a1`, `a1/arc`, `arc` → A1; `clive`, `clive stapler` → Clive; etc.

### How to Detect Format

`generate_summaries.py` checks for `^\*\*[A-Za-z]+:` patterns to detect radio-play format. Prose episodes use section headers and first/last paragraphs as story beats.

---

## Signal's Voice

Signal is the narrator — a warm, slightly theatrical presence reading in third-person past tense. She holds the shape of the story so the story can know itself.

### Intro (always spoken first)

```
Hello from wherever and whenever you are. I'm the Ephergent Signal, and this is The Ephergent.
```

### Excerpt Format

The 2-3 sentence summary (from `excerpts/seasonNN/SXXEXX.txt`) follows the intro:

```
In this episode: [protagonist] encounters [episode title]. [second story beat]. [third story beat].
```

Example:
```
In this episode: Pixel navigates the frequency. the signal calls from the void. and the signal continues.
```

### Outro (always spoken last)

```
Thank you for listening to this neural dimensional broadcast of The Ephergent. Until next time.
```

### Final TTS Text Layout

```
[INTRO]

In this episode: [summary from excerpts/]

[clean episode body]

[OUTRO]
```

---

## Script Reference

### Stage 1: preprocess_episodes.py

**Purpose:** Strip episode markdown to clean TTS-ready body text.

```bash
# Single episode
python scripts/preprocess_episodes.py --episode S01E01

# Full season
python scripts/preprocess_episodes.py --season 01

# All episodes
python scripts/preprocess_episodes.py --all
```

**Output:** `tts_text/seasonNN/SXXEXX.tts.txt` — clean body only, no intro/outro.

**What it strips:**
- YAML frontmatter
- `## LOCKED RULES CHECK` (header + all content to end)
- `## COFFEE CHART` tables
- All markdown headers
- Scene markers `*[...]`
- Audio direction markers `*(Sound:...)*` `*(SFX:...)*`
- Square bracket annotations
- Bold/italic markdown
- Featured Characters lines
- Platform markers (`!!...!!`)
- `V.O.` / `off-mic` annotations

**Radio-play transformation:** `**CHARACTER:**` blocks → `Character says, "dialogue"`.

### Stage 2: generate_summaries.py

**Purpose:** Derive 2-3 sentence third-person Signal-voice summaries.

```bash
python scripts/generate_summaries.py --episode S01E01
python scripts/generate_summaries.py --season 01
python scripts/generate_summaries.py --all
```

**Output:** `excerpts/seasonNN/SXXEXX.txt`

**Behavior:**
- Prose episodes: uses section headers and first/last paragraphs as beats
- Radio-play episodes: uses first 3 character blocks as beats
- Detects protagonist from first 500 characters (searches Pixel, A1, Clive, The crew, The Ephergent)
- Strips `SXXEXX — ` prefix from episode titles
- Truncates beats > 60 chars at word boundary
- Final output: `In this episode: [beat 1]. [beat 2]. [beat 3].`

### Stage 3: assemble_tts_text.py

**Purpose:** Build final TTS text with Signal intro, summary, body, outro.

```bash
python scripts/assemble_tts_text.py --episode S01E01
python scripts/assemble_tts_text.py --season 01
python scripts/assemble_tts_text.py --all
```

**Input:**
- `excerpts/seasonNN/SXXEXX.txt` (summary)
- `tts_text/seasonNN/SXXEXX.tts.txt` (clean body from stage 1)

**Output:** `tts_text/seasonNN/SXXEXX.tts.txt` (overwrites intermediate with final)

**Layout:**
```
Hello from wherever and whenever you are. I'm the Ephergent Signal, and this is The Ephergent. In this episode: [summary]

[clean episode body]

Thank you for listening to this neural dimensional broadcast of The Ephergent. Until next time.
```

**Missing excerpt:** If `excerpts/` file missing, uses placeholder `"a new transmission from the signal"` and prints a warning.

### Stage 4: generate_audio.py

**Purpose:** Call Kokoro TTS, concatenate chunks, output MP3.

```bash
python scripts/generate_audio.py --episode S01E01
python scripts/generate_audio.py --season 01
python scripts/generate_audio.py --all
```

**Output:**
- `audio/seasonNN/SXXEXX.mp3` (grand_plan, permanent)
- `ephergent.com/public/audio/seasonNN/SXXEXX.mp3` (website copy, via cp)

**Chunking logic:**
- Splits at paragraph boundaries
- Target ~2200 chars per chunk at sentence boundaries
- Skips chunks already on disk (> 500 bytes) for resumability
- Retries failed chunks up to 3 times with exponential backoff (2s, 4s, 8s)

**ffmpeg concat:** Uses `ffmpeg -f concat -safe 0` with a temp filelist at `/tmp/ephergent_chunks/SXXEXX_chunks.txt`. Output: libmp3lame, quality 2.

**Smoke test:** Always runs one test chunk ("Testing. One. Two. Three.") before processing episodes. Fails entire run if smoke test fails.

---

## Kokoro TTS API Reference

**Base URL:** `http://sprecher.nexus.home.test`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check — returns `{"status":"ok","engines":["kokoro","qwen","whisper"]}` |
| `/api/tts/sync` | POST | Generate TTS audio |

### Health Check

```bash
curl --max-time 10 http://sprecher.nexus.home.test/api/health
# Expected: {"status":"ok","engines":["kokoro","qwen","whisper"]}
```

**If timeout:** Sprecher is down. Do NOT proceed with audio generation.

### TTS Sync Request

```
POST /api/tts/sync
Content-Type: application/x-www-form-urlencoded

text=<text>&voice=bf_emma(0.7)+af_sarah(0.3)&engine=kokoro&audio_format=mp3
```

**Response (JSON):**
```json
{
  "audio_url": "/api/tts/download/abc123",
  "status": "success"
}
```

The script extracts `audio_url` (or `audio.url` or `url`) from the response, then downloads from `{SPRECHER}{audio_url}`.

**Voice:** `bf_emma(0.7)+af_sarah(0.3)` — single narrator "Signal" blend. Do not separate characters.

**Engine:** `kokoro`

**Audio format:** `mp3`

---

## Testing and Validation

### Pre-Audio Quality Gate Checklist

Before any audio generation pass:

- [ ] **Story is final** — never generate audio for episodes that are actively changing
- [ ] **API reachable** — `curl --max-time 10 http://sprecher.nexus.home.test/api/health` returns `{"status":"ok"}`
- [ ] **No stub files** — all episodes > 2KB:
  ```bash
  find episodes/ -name "*.md" -size -2k -exec wc -c {} \; | sort -n
  ```
- [ ] **Canon compliance** — no locked-rules violations (dimension/plane/stapler/sea/voyage):
  ```bash
  grep -iE "stapler|dimension|plane|interdimensional|sea|voyage|sailing" \
    episodes/season*/S*.md
  ```

### Pipeline Smoke Test

`generate_audio.py` runs a smoke test automatically on every invocation:

```bash
python scripts/generate_audio.py --episode S01E01
# Expected output:
# [HH:MM:SS] Smoke test...
#   API OK: <size>KB
#   Generating S01E01...
#   S01E01 assembled → audio/season01/S01E01.mp3
```

### Full Pipeline Run

```bash
# 1. Clean body text
python scripts/preprocess_episodes.py --all

# 2. Generate summaries
python scripts/generate_summaries.py --all

# 3. Assemble final TTS text
python scripts/assemble_tts_text.py --all

# 4. Generate audio
python scripts/generate_audio.py --all
```

Or run per-season in order. Stage 4 requires stage 3 output; stage 3 requires stage 2 output; stage 2 requires stage 1 output.

### Validate TTS Output

- File size: `audio/seasonNN/SXXEXX.mp3` should be > 500KB for a typical episode
- Duration: ~10-20 minutes per episode (varies with word count)
- Listen for: missing words at chunk boundaries, correct Signal voice, clean intro/outro

---

## Troubleshooting

### "TTS text not found"

```
ERROR: TTS body not found: tts_text/season01/S01E01.tts.txt
```

Fix: Run `preprocess_episodes.py` first.

### "no audio_url in response"

The Kokoro API returned an unexpected response. Check:
- API health: `curl http://sprecher.nexus.home.test/api/health`
- Text length: Kokoro fails on very long chunks (> 3000 chars). The chunker targets 2200.
- Encoding: ensure text is UTF-8

### "ffmpeg: concat: was expected"

Usually means a chunk file is empty or malformed. Fix: delete the chunk dir and retry:

```bash
rm -rf /tmp/ephergent_chunks/S01E01_*
python scripts/generate_audio.py --episode S01E01
```

### "curl exit N" on chunk generation

Network timeout or curl failure. The script retries up to 3 times with backoff. If all retries fail, the chunk is skipped (resume will catch it on next run since chunks are cached).

### Sprecher unreachable

```
curl: (7) Failed to connect to sprecher.nexus.home.test
```

- Check LAN connectivity to the server
- Verify the `sprecher` service is running on the LAN server
- Do NOT proceed with audio generation — all chunks will fail

### Duplicate episode files

If `episodes/season01/` contains multiple files matching `S01E01*`, `preprocess_episodes.py` will error:

```
ValueError: Multiple matches for S01E01: [...]
```

Resolve duplicates before generating audio.

---

## Two-Repo Sync Integration

The audio pipeline reads from and writes to **grand_plan only**. The website is updated via copy at stage 4.

### Sync sequence for episodes with audio changes

```bash
# 1. Sync episodes + lore + crew to website
cd ~/Documents/code_repos/the_ephergent_grand_plan
./scripts/sync_to_website.sh --all

# 2. Build and deploy website
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 3. Commit grand_plan changes
cd ~/Documents/code_repos/the_ephergent_grand_plan
git add episodes/ tts_text/ excerpts/ audio/
git commit -m "audio: S01E01-S01E05" && git push origin main

# 4. Commit website changes
cd ~/Documents/code_repos/ephergent.com
git add -A && git commit -m "sync: audio S01E01-S01E05" && git push origin main
```

**Never edit `ephergent.com/src/content/transmissions/` directly** — derived from grand_plan.

### Audio file ownership

- **Canonical:** `grand_plan/audio/seasonNN/SXXEXX.mp3` — permanent archive
- **Website:** `ephergent.com/public/audio/seasonNN/SXXEXX.mp3` — derived copy

Both are production files. Commit grand_plan audio files to git.

---

## Agent Timeout Math

For subagent parallelization:

- **~30 episodes × ~30s Kokoro = ~15 minutes** sequential
- **Subagent hard limit: 10 minutes**
- **Solution: Split into 3 agents, 10 episodes each, parallel**

When dispatching audio generation subagents, pass `--season` to limit scope. Each season (~10 episodes) fits within the 10-minute window when run in parallel.

---

## Quick Reference

```bash
# Full pipeline
python scripts/preprocess_episodes.py --all
python scripts/generate_summaries.py --all
python scripts/assemble_tts_text.py --all
python scripts/generate_audio.py --all

# Single episode
python scripts/preprocess_episodes.py --episode S01E01
python scripts/generate_summaries.py --episode S01E01
python scripts/assemble_tts_text.py --episode S01E01
python scripts/generate_audio.py --episode S01E01

# Per-season
python scripts/preprocess_episodes.py --season 01
python scripts/generate_summaries.py --season 01
python scripts/assemble_tts_text.py --season 01
python scripts/generate_audio.py --season 01

# Health check
curl --max-time 10 http://sprecher.nexus.home.test/api/health

# Canon audit
grep -iE "stapler|dimension|plane|interdimensional|sea|voyage|sailing" \
  episodes/season*/S*.md
```