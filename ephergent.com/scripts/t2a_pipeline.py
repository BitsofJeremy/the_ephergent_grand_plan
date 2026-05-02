#!/usr/bin/env python3
"""
The Ephergent — MiniMax T2A v2 Pipeline
========================================
Converts episode markdown scripts into MP3 audio using MiniMax T2A v2 API.

Usage:
    python3 scripts/t2a_pipeline.py --episode S01E01        # single episode
    python3 scripts/t2a_pipeline.py --season 01             # full season
    python3 scripts/t2a_pipeline.py --all                     # all 30 episodes
    python3 scripts/t2a_pipeline.py --episode S01E01 --dry-run  # parse only, no API calls

Requirements:
    - MINIMAX_API_KEY in ~/.hermes/.env (Bearer JWT auth)
    - ffmpeg installed (for MP3 concatenation)
    - Python 3.8+ with standard library only

Voice Assignment:
    - Pixel Paradox:  voice clone ID (moss_audio_b81c04d0-428d-11f1-9e81-7a02684cce23)
    - A1:             voice clone ID (moss_audio_aa4e833a-45a7-11f1-bc76-fe0ee6e0e90b)
    - Clive:          voice clone ID (moss_audio_5f0c0634-45a8-11f1-ae64-b65408efbb94)
    - Narration:      English female system voice
    - Other characters: system voices (English_Radiant_Girl, English_Insightful_Speaker, etc.)
"""

import os
import re
import sys
import json

import subprocess
import argparse
import binascii
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Configuration ────────────────────────────────────────────────────────────

EPISODE_GLOB  = "S{season}E{episode}_*.md"
EPISODE_GLOB_ALL = "S*.md"
# Episodes live in the grand-plan repo, two levels up from ephergent.com/scripts/
EPISODE_DIR   = Path(__file__).parent.parent.parent / "phase_04_episodes"
AUDIO_OUT_DIR = Path(__file__).parent.parent / "public" / "audio"
MANIFEST_PATH = AUDIO_OUT_DIR / "manifest.json"

# MiniMax T2A v2
T2A_ENDPOINT = "https://api-uw.minimax.io/v1/t2a_v2"
T2A_MODEL    = "speech-2.8-hd"
MAX_CHUNK_CHARS = 9500   # safe margin under 10,000 limit

# ─── Voice ID Map ────────────────────────────────────────────────────────────

# Custom voice clones (uploaded by Jeremy to his MiniMax account)
VOICE_CLONES = {
    "pixel":    "moss_audio_b81c04d0-428d-11f1-9e81-7a02684cce23",
    "a1":       "moss_audio_aa4e833a-45a7-11f1-bc76-fe0ee6e0e90b",
    "clive":    "moss_audio_5f0c0634-45a8-11f1-ae64-b65408efbb94",
}

# System voices (fallback when no clone exists)
# MiniMax system voice IDs for English voices
SYSTEM_VOICES = {
    # female
    "narrator":      "English_Graceful_Lady",
    "pixel_paradox": "English_Radiant_Girl",
    "luminara":      "English_Graceful_Lady",
    "nano":          "English_Radiant_Girl",
    "mochi":         "English_Radiant_Girl",   # dog — no speech
    # male
    "om_kai":        "English_Insightful_Speaker",
    "barry":         "English_Persuasive_Man",
    "meatball":      "English_Insightful_Speaker",
    # neutral / robot
    "clive":         "English_Radiant_Girl",   # will use clone; fallback
    "a1":            "English_Insightful_Speaker",  # will use clone; fallback
}

# Characters who should be silent (presence only, no dialogue lines)
SILENT_CHARS = {"mochi", "moochi"}

# ─── Speaker Regex Patterns ───────────────────────────────────────────────────
# Order matters — most specific first

SPEAKER_PATTERNS = [
    # Markdown bold: **PIXEL:**
    (re.compile(r"^\s*\*\*(?P<speaker>[A-Z][A-Z0-9 ]+):\*\*(?P<text>.*)", re.MULTILINE), "bold"),
    # Brackets: [PIXEL]
    (re.compile(r"^\s*\[(?P<speaker>[A-Za-z][A-Za-z0-9 ]+)\](?P<text>.*)", re.MULTILINE), "bracket"),
    # XML/HTML style: <PIXEL> or <PIXEL:
    (re.compile(r"^\s*<(?P<speaker>[A-Za-z][A-Za-z0-9 ]+?)[\s>:]*(?P<text>.*)", re.MULTILINE), "xml"),
    # Dash prefix: PIXEL -
    (re.compile(r"^\s*(?P<speaker>[A-Z][a-z]+(?:\s+[A-Za-z]+)?)\s+[-–—](?P<text>.*)", re.MULTILINE), "dash"),
]

# Regex to split long text into API-safe chunks (on sentence/phrase boundaries)
SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'])|(?<=[,;:])\s+(?=[A-Z\"'])")


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Utterance:
    speaker: str
    text: str
    voice_id: str
    is_clone: bool = False

    @property
    def cleaned_speaker(self) -> str:
        return self.speaker.strip().lower().replace(" ", "_")


@dataclass
class EpisodeResult:
    season: int
    episode: int
    slug: str
    title: str
    utterances: list[Utterance] = field(default_factory=list)
    mp3_path: Optional[Path] = None
    duration_sec: Optional[float] = None
    file_size_bytes: Optional[int] = None
    error: Optional[str] = None


# ─── API Client ───────────────────────────────────────────────────────────────

def get_api_key() -> str:
    """Load MINIMAX_API_KEY from ~/.hermes/.env"""
    env_path = Path.home() / ".hermes" / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"~/.hermes/.env not found — cannot load MINIMAX_API_KEY")

    api_key = None
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("MINIMAX_API_KEY") or line.startswith("minimax_api_key"):
                _, _, api_key = line.partition("=")
                api_key = api_key.strip().strip("\"'")
                break

    if not api_key:
        raise ValueError("MINIMAX_API_KEY not found in ~/.hermes/.env")

    return api_key


def get_api_key() -> str:
    """Load MINIMAX_API_KEY from ~/.hermes/.env"""
    env_path = Path.home() / ".hermes" / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"~/.hermes/.env not found — cannot load MINIMAX_API_KEY")

    api_key = None
    with open(env_path) as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("MINIMAX_API_KEY") or line.startswith("minimax_api_key"):
                _, _, api_key = line.partition("=")
                api_key = api_key.strip().strip("\"'")
                break

    if not api_key:
        raise ValueError("MINIMAX_API_KEY not found in ~/.hermes/.env")

    return api_key


def fetch_t2a(text: str, voice_id: str, api_key: str) -> bytes:
    """Call MiniMax T2A v2 API, return raw MP3 bytes. Uses stdlib urllib only."""
    import json, urllib.request

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": T2A_MODEL,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
        },
    }

    req = urllib.request.Request(
        T2A_ENDPOINT,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
        status = body.get("base_resp", {}).get("status_code", 0)
        if status == 0:
            # Audio hex is nested: body["data"]["audio"]
            audio_hex = body.get("data", {}).get("audio", "")
            if not audio_hex:
                return b""
            return binascii.unhexlify(audio_hex)
        else:
            msg = body.get("base_resp", {}).get("status_msg", "unknown error")
            raise RuntimeError(f"T2A API error {status}: {msg}")


def synthesize_utterances(utterances: list[Utterance], dry_run: bool = False) -> list[tuple[Utterance, bytes]]:
    """Synthesize all utterances to MP3 bytes using ThreadPoolExecutor. Returns list of (utterance, mp3_bytes)."""
    if dry_run:
        return [(u, b"DRY_RUN") for u in utterances]

    api_key = get_api_key()
    results: list[tuple[Utterance, bytes]] = []
    completed = 0

    def synth(u: Utterance) -> tuple[Utterance, bytes]:
        try:
            mp3 = fetch_t2a(u.text, u.voice_id, api_key)
            return (u, mp3)
        except Exception as exc:
            print(f"    [WARN] {u.cleaned_speaker}: {exc}", file=sys.stderr)
            return (u, b"")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(synth, u): u for u in utterances}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1

    # Preserve original order
    utterance_map = {id(u): i for i, (u, _) in enumerate(results)}
    ordered = sorted(results, key=lambda x: utterance_map.get(id(x[0]), 999))
    return ordered


# ─── Markdown Parsing ─────────────────────────────────────────────────────────

def load_episode(season: int, episode: int) -> tuple[Path, dict, str]:
    """Load episode markdown. Returns (path, frontmatter_dict, body_text)."""
    season_str = f"{season:02d}"
    episode_str = f"{episode:02d}"

    # Find the file
    season_dir = EPISODE_DIR / f"season{season_str}"
    if not season_dir.exists():
        raise FileNotFoundError(f"Season directory not found: {season_dir}")

    pattern = f"S{season_str}E{episode_str}_*.md"
    matches = list(season_dir.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No episode found matching {pattern} in {season_dir}")
    if len(matches) > 1:
        print(f"  [WARN] Multiple matches for {pattern}, using first: {matches[0].name}", file=sys.stderr)

    path = matches[0]

    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    # Split frontmatter
    if raw.startswith("---"):
        parts = raw[3:].split("---", 1)
        if len(parts) == 2:
            fm_text, body = parts
            frontmatter = parse_frontmatter(fm_text.strip())
            return path, frontmatter, body.strip()

    return path, {}, raw


def parse_frontmatter(text: str) -> dict:
    """Parse YAML-lite frontmatter (season:, episode:, title:, etc.)."""
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            result[key] = val
    return result


def extract_utterances(body: str, season: int, episode: int) -> list[Utterance]:
    """
    Parse episode body text into a list of Utterances.
    
    Episode format: prose narrative with quoted dialogue.
    - Narration = narrator voice (from frontmatter, default "pixel")
    - "He said." / 'She replied.' patterns = dialogue in quotes
    - Section headers and stage directions = skipped
    
    Strategy:
    1. Strip markdown headers and stage directions
    2. Split on quoted speech blocks
    3. Each block: detect if it's dialogue (has attribution) or pure narration
    4. Chunk large blocks by paragraph
    """
    utterances: list[Utterance] = []

    narrator_voice, _ = resolve_voice("narrator")

    # Remove markdown headers (##, ###) and bold/italic markers
    cleaned = strip_markdown(body)

    # Split into paragraphs (double newline = paragraph boundary)
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    
    for para in paragraphs:
        if not para or len(para) < 10:
            continue

        # Skip very short paragraphs that look like stage directions
        if para.startswith("[") or para.startswith("(") or para.startswith("*"):
            continue

        # Check if this paragraph contains dialogue (has quotation marks)
        has_quotes = '"' in para or '"' in para or '"' in para

        if has_quotes:
            # Extract dialogue blocks from within the paragraph
            blocks = extract_dialogue_blocks(para)
            for block_text, speaker in blocks:
                if not block_text.strip():
                    continue
                # Skip narration-only blocks (no quotes opened)
                if speaker is None and not block_text.strip('" \''):
                    continue
                if speaker is None:
                    speaker = "Narrator"
                voice_id, is_clone = resolve_voice(speaker)
                for chunk in chunk_text(block_text, MAX_CHUNK_CHARS):
                    utterances.append(Utterance(
                        speaker=speaker, text=chunk,
                        voice_id=voice_id, is_clone=is_clone
                    ))
        else:
            # Pure narration — chunk by paragraph
            for chunk in chunk_text(para, MAX_CHUNK_CHARS):
                utterances.append(Utterance(
                    speaker="Narrator", text=chunk,
                    voice_id=narrator_voice, is_clone=False
                ))

    return utterances


def strip_markdown(text: str) -> str:
    """Remove markdown formatting from text."""
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)       # *italic*
    text = re.sub(r'__(.+?)__', r'\1', text)       # __bold__
    text = re.sub(r'_(.+?)_', r'\1', text)          # _italic_
    # Remove markdown headers (## header)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Remove scene markers like [Stage Direction]
    text = re.sub(r'^\s*\[[^\]]+\]\s*$', '', text, flags=re.MULTILINE)
    return text


# Regex to extract quoted dialogue with speaker attribution
# Pattern: "Speech text." attribution
# Attribution patterns: he said, she replied, Pixel said, A1 muttered, Clive noted, etc.
DIALOGUE_RE = re.compile(
    r'(?P<quote>"[^"]{3,500}?"[.!?]?)'
    r'(?:\s+(?P<attr>he|she|Pixel|A1|Clive|Luminara|Om\s*Kai|Barry|Meatball|Nano|It|They|We|I)["\'\s,]+(?:said|replied|asked|muttered|noted|whispered|called|screamed|stated|added|continued|exclaimed)?)?',
    re.IGNORECASE
)


def extract_dialogue_blocks(para: str) -> list[tuple[str, Optional[str]]]:
    """
    Split a paragraph into (text, speaker_or_None) blocks.
    Returns list of (block_text, speaker) where speaker is None for narration.
    """
    blocks: list[tuple[str, Optional[str]]] = []
    narrator_voice, _ = resolve_voice("narrator")

    # Simple approach: find all quoted strings and their context
    # Split on quoted speech
    parts = DIALOGUE_RE.findall(para)
    
    if not parts:
        return [(para, None)]

    last_end = 0
    
    # Find positions of all quotes in the paragraph
    quote_positions: list[tuple[int, int, str]] = []  # (start, end, text)
    for m in re.finditer(r'"([^"]{3,500}?)"', para):
        quote_positions.append((m.start(), m.end(), m.group(1)))
    
    for start, end, quote_text in quote_positions:
        # Text before this quote = narration
        before = para[last_end:start].strip()
        if before and len(before) > 20:
            blocks.append((before, None))
        
        # The quoted dialogue
        if quote_text.strip():
            blocks.append((quote_text.strip(), "Dialogue"))
        
        last_end = end

    # Remaining text after last quote
    remaining = para[last_end:].strip()
    if remaining and len(remaining) > 20:
        blocks.append((remaining, None))

    return blocks


def normalize_speaker_labels(text: str) -> str:
    """Standardize speaker label formats across the episode."""
    # Already normalized — just return as-is since patterns handle the variations
    return text


def normalize_speaker(raw: str) -> str:
    """Normalize raw speaker string to canonical name."""
    s = raw.strip().lower()

    # Known aliases
    aliases = {
        "pixel paradox": "pixel",
        "pixel": "pixel",
        "a1": "a1",
        "clive": "clive",
        "narrator": "narrator",
        "luminara": "luminara",
        "luminarausha": "luminara",
        "om kai": "om_kai",
        "omkai": "om_kai",
        "barry": "barry",
        "barry kowalski": "barry",
        "meatball": "meatball",
        "nano": "nano",
        "mochi": "mochi",
        "moochi": "mochi",
    }

    for key, canonical in aliases.items():
        if key in s or s in key:
            return canonical.title().replace("_", " ")

    # Default: title case
    return raw.strip().title()


def resolve_voice(speaker: str) -> tuple[str, bool]:
    """Resolve speaker name to MiniMax voice_id. Returns (voice_id, is_clone)."""
    key = speaker.strip().lower().replace(" ", "_")
    short_key = key.split("_")[0]  # e.g. "pixel_paradox" -> "pixel"

    # Try clone first
    for k, clone_id in VOICE_CLONES.items():
        if k in key or key in k:
            return clone_id, True

    # Fall back to system voice
    sys_voice = SYSTEM_VOICES.get(key) or SYSTEM_VOICES.get(short_key, "English_Radiant_Girl")
    return sys_voice, False


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split text into API-safe chunks on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    # Split on sentence boundaries
    parts = SENTENCE_SPLITTER.split(text)

    current = ""
    for part in parts:
        if len(current) + len(part) + 1 <= max_chars:
            current += (" " if current else "") + part
        else:
            if current:
                chunks.append(current.strip())
            # If single sentence exceeds limit, hard-split
            if len(part) > max_chars:
                sub_parts = [part[i:i+max_chars] for i in range(0, len(part), max_chars)]
                chunks.extend(sub_parts)
                current = ""
            else:
                current = part

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c.strip()]


# ─── Audio Processing ─────────────────────────────────────────────────────────

def concatenate_mp3(mp3_paths: list[Path], output_path: Path) -> Optional[float]:
    """Concatenate multiple MP3 files using ffmpeg. Returns duration in seconds."""
    if not mp3_paths:
        return None

    # Write concat list
    concat_list = AUDIO_OUT_DIR / "concat_list.txt"
    with open(concat_list, "w") as fh:
        for p in mp3_paths:
            fh.write(f"file '{p.resolve()}'\n")

    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            print(f"  [WARN] ffmpeg concat failed: {result.stderr[:300]}", file=sys.stderr)
            return None
    except FileNotFoundError:
        print("  [WARN] ffmpeg not found — cannot concatenate. Using first chunk only.", file=sys.stderr)
        if mp3_paths:
            import shutil
            shutil.copy(mp3_paths[0], output_path)
    except subprocess.TimeoutExpired:
        print("  [WARN] ffmpeg timed out", file=sys.stderr)
        return None

    # Get duration with ffprobe
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
            capture_output=True, text=True, timeout=30,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            return float(probe.stdout.strip())
    except Exception:
        pass

    return None


def get_mp3_duration(mp3_path: Path) -> Optional[float]:
    """Get MP3 duration in seconds via ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


# ─── Episode Processing ───────────────────────────────────────────────────────

def process_episode(
    season: int,
    episode: int,
    dry_run: bool = False,
) -> EpisodeResult:
    """Process a single episode end-to-end."""
    season_str = f"{season:02d}"
    episode_str = f"{episode:02d}"

    try:
        path, frontmatter, body = load_episode(season, episode)
    except FileNotFoundError as exc:
        return EpisodeResult(
            season=season, episode=episode,
            slug=f"S{season_str}E{episode_str}",
            title=f"Episode {episode_str}",
            error=str(exc),
        )

    title = frontmatter.get("title", path.stem)
    slug = f"S{season_str}E{episode_str}"

    print(f"\n[{slug}] {title}")
    print(f"  File: {path.name}")

    # Parse utterances
    utterances = extract_utterances(body, season, episode)
    print(f"  Utterances: {len(utterances)}")

    if not utterances:
        return EpisodeResult(
            season=season, episode=episode,
            slug=slug, title=title,
            error="No utterances extracted from episode",
        )

    # Show utterance breakdown
    speaker_counts: dict[str, int] = {}
    for u in utterances:
        speaker_counts[u.cleaned_speaker] = speaker_counts.get(u.cleaned_speaker, 0) + 1
    for spk, cnt in sorted(speaker_counts.items()):
        print(f"    {spk}: {cnt} block(s)")

    if dry_run:
        print(f"  [DRY RUN] Skipping synthesis")
        return EpisodeResult(
            season=season, episode=episode,
            slug=slug, title=title,
            utterances=utterances,
        )

    # Synthesize
    print(f"  Synthesizing via MiniMax T2A v2 ({T2A_MODEL})...")
    synthesized = synthesize_utterances(utterances, dry_run=dry_run)

    # Save individual MP3 chunks to temp dir
    temp_dir = AUDIO_OUT_DIR / f".tmp_{slug}"
    temp_dir.mkdir(exist_ok=True)

    mp3_paths: list[Path] = []
    for i, (u, mp3_bytes) in enumerate(synthesized):
        if mp3_bytes and mp3_bytes != b"DRY_RUN":
            chunk_path = temp_dir / f"chunk_{i:04d}.mp3"
            with open(chunk_path, "wb") as fh:
                fh.write(mp3_bytes)
            mp3_paths.append(chunk_path)

    # Concatenate
    audio_dir = AUDIO_OUT_DIR / f"season{season_str}"
    audio_dir.mkdir(parents=True, exist_ok=True)
    output_path = audio_dir / f"S{season_str}E{episode_str}.mp3"

    if mp3_paths:
        print(f"  Concatenating {len(mp3_paths)} chunks...")
        duration = concatenate_mp3(mp3_paths, output_path)

        # Cleanup temp
        for p in mp3_paths:
            p.unlink(missing_ok=True)
        temp_dir.rmdir()

        file_size = output_path.stat().st_size if output_path.exists() else None
        print(f"  Output: {output_path.name} ({file_size:,} bytes, {duration:.1f}s)")

        return EpisodeResult(
            season=season, episode=episode,
            slug=slug, title=title,
            utterances=utterances,
            mp3_path=output_path,
            duration_sec=duration,
            file_size_bytes=file_size,
        )
    else:
        return EpisodeResult(
            season=season, episode=episode,
            slug=slug, title=title,
            utterances=utterances,
            error="No MP3 chunks produced",
        )


def process_season(season: int, dry_run: bool = False) -> list[EpisodeResult]:
    """Process all episodes in a season."""
    results: list[EpisodeResult] = []
    for ep in range(1, 11):
        result = process_episode(season, ep, dry_run=dry_run)
        results.append(result)
    return results


# ─── Manifest ─────────────────────────────────────────────────────────────────

def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as fh:
            return json.load(fh)
    return {"version": "1.0", "episodes": []}


def save_manifest(manifest: dict):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"\nManifest: {MANIFEST_PATH}")


def update_manifest(results: list[EpisodeResult]):
    manifest = load_manifest()
    for r in results:
        entry = {
            "id": r.slug,
            "season": r.season,
            "episode": r.episode,
            "title": r.title,
            "file": str(r.mp3_path.relative_to(AUDIO_OUT_DIR.parent)) if r.mp3_path else None,
            "duration_sec": r.duration_sec,
            "file_size_bytes": r.file_size_bytes,
            "speaker_count": len(set(u.cleaned_speaker for u in r.utterances)),
        }
        # Replace or append
        for i, e in enumerate(manifest.get("episodes", [])):
            if e["id"] == r.slug:
                manifest["episodes"][i] = entry
                break
        else:
            manifest.setdefault("episodes", []).append(entry)

    manifest["generated_at"] = subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()
    save_manifest(manifest)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="The Ephergent T2A Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", metavar="S01E01", help="Single episode code (e.g. S01E01)")
    group.add_argument("--season", metavar="01", help="Season number (01, 02, 03)")
    group.add_argument("--all", action="store_true", help="Process all 30 episodes")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, skip API calls")
    parser.add_argument("--force", action="store_true", help="Overwrite existing MP3 files")
    return parser.parse_args()


def parse_episode_code(code: str) -> tuple[int, int]:
    m = re.match(r"^S(\d+)E(\d+)$", code.strip().upper())
    if not m:
        raise ValueError(f"Invalid episode code: {code} (expected S01E01)")
    return int(m.group(1)), int(m.group(2))


def main():
    args = parse_args()

    if args.all:
        print("Processing ALL seasons (S01–S03)...")
        all_results: list[EpisodeResult] = []
        for season in [1, 2, 3]:
            all_results.extend(process_season(season, dry_run=args.dry_run))
        update_manifest(all_results)

    elif args.season:
        season = int(args.season)
        if season not in [1, 2, 3]:
            raise ValueError(f"Season must be 01, 02, or 03, got {args.season}")
        print(f"Processing Season {season:02d}...")
        results = process_season(season, dry_run=args.dry_run)
        update_manifest(results)

    elif args.episode:
        season, episode = parse_episode_code(args.episode)
        print(f"Processing {args.episode}...")
        result = process_episode(season, episode, dry_run=args.dry_run)
        update_manifest([result])

    print("\nDone.")


if __name__ == "__main__":
    main()
