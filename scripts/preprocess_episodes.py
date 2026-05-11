#!/usr/bin/env python3
"""
preprocess_episodes.py — Strip episode markdown to clean TTS-ready text.

Strips: frontmatter, COFFEE CHART tables, LOCKED RULES CHECK sections,
scene markers *[...]*, audio direction markers (Sound:...), **CHARACTER:** blocks
(radio-play format, transformed to "Character says, 'dialogue'"), markdown formatting.

Output: tts_text/SXXEXX.tts.txt (clean body only — no intro/outro, no summary)

Usage:
    python scripts/preprocess_episodes.py --episode S01E01
    python scripts/preprocess_episodes.py --season 01
    python scripts/preprocess_episodes.py --all
"""
import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
GRAND_PLAN = SCRIPT_DIR.parent.resolve()
EPISODES_DIR = GRAND_PLAN / "episodes"
TTS_TEXT_DIR = GRAND_PLAN / "tts_text"

# Matches **CHARACTER:** at start of line, capturing name and dialogue
CHARACTER_RE = re.compile(
    r'^\*\*([A-Za-z][A-Za-z0-9 ]*?):\*\*\n(.*?)(?=^\*\*|\Z)',
    re.MULTILINE | re.DOTALL,
)

CHARACTER_ALIASES = {
    'pixel paradox': 'Pixel', 'pixel': 'Pixel',
    'a1': 'A1', 'a1/arc': 'A1', 'a1 assistant': 'A1', 'arc': 'A1',
    'clive': 'Clive', 'clive stapler': 'Clive',
    'mochi': 'Mochi',
    'meatball': 'Meatball',
    'zephyr': 'Zephyr', 'zephyr glitch': 'Zephyr',
    'luminara': 'Luminara', 'luminara usha': 'Luminara',
    'om kai': 'Om Kai', 'omkai': 'Om Kai',
    'nano': 'Nano',
    'klaus': 'Klaus', 'baron klaus': 'Klaus',
    'barry': 'Barry', 'barry kowalski': 'Barry',
}


def extract_radio_play(text: str) -> tuple[list[str], str]:
    """Extract **CHARACTER:** blocks, transform to 'Character says, \"dialogue\"'.
    Returns (dialogue_lines, remaining_text).
    """
    text = re.sub(r'\|.*?\|.*?\n', '', text)  # strip coffee chart rows
    text = re.sub(r'[-|]+\s*\n', '', text)
    text = re.sub(r'\*\[.*?\]\*', '', text, flags=re.DOTALL)  # scene markers

    lines: list[str] = []
    for m in CHARACTER_RE.finditer(text):
        raw_name = m.group(1).strip().lower()
        raw_dialogue = m.group(2)
        name = CHARACTER_ALIASES.get(raw_name) or m.group(1).strip()
        if not name:
            continue
        dialogue = raw_dialogue.replace('**', '').replace('*', "'").strip()
        if not dialogue:
            continue
        lines.append(f'{name} says, "{dialogue}"')

    remaining = CHARACTER_RE.sub('', text)
    return lines, remaining


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter."""
    if text.startswith('---'):
        m = re.match(r'^---\n.*?\n---\n', text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def strip_prose_artifacts(text: str) -> str:
    """Remove everything TTS should not read."""
    clean = text

    # HTML tags
    clean = re.sub(r'<[^>]*>', '', clean)

    # LOCKED RULES CHECK — strip the header line and ALL following content
    # to end of string (includes all table rows and trailing --- before outro)
    # Must run BEFORE horizontal-rule removal so we capture the trailing --- too
    clean = re.sub(
        r'## LOCKED RULES CHECK.*',
        '',
        clean,
        flags=re.DOTALL,
    )

    # All headers (# ## ###) — AFTER LOCKED so we don't orphan table rows
    clean = re.sub(r'^\s*#+\s.*$', '', clean, flags=re.MULTILINE)

    # Horizontal rules ---
    clean = re.sub(r'^\s*---\s*$', '', clean, flags=re.MULTILINE)

    # Bold/italic: * → apostrophe
    clean = clean.replace('*', "'")

    # Bold **text** → text
    clean = re.sub(r"\*\*(?!\")([^*]+)\*\*(?!\")", r"\1", clean)

    # Scene markers *[LOCATION. TIME.]*
    clean = re.sub(r'\*\[.*?\]\*', '', clean, flags=re.DOTALL)

    # Audio-direction stage markers
    clean = re.sub(r'\*\((?:sound|SFX|fade|cut|beat)[^)]*\)', '', clean, flags=re.IGNORECASE)

    # Horizontal rules ---
    clean = re.sub(r'^\s*---\s*$', '', clean, flags=re.MULTILINE)

    # Square bracket annotations [subtitled], [in Veranthic], etc.
    clean = re.sub(r'\[.*?\]', '', clean)

    # V.O., off-mic
    clean = re.sub(r'\bV\.O\.\b', '', clean)
    clean = re.sub(r'\boff-mic\b', '', clean, flags=re.IGNORECASE)

    # Ephergent platform markers
    clean = re.sub(r'‼.*?!!', '', clean, flags=re.DOTALL)
    clean = re.sub(r'Video created by.*?AI\s*!!', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Audio created by.*?dimension.*?\]!!', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Illustration created by.*?AI\s*!!', '', clean, flags=re.IGNORECASE)

    # Coffee chart tables
    clean = re.sub(r'\|.*?\|.*?\n', '', clean)
    clean = re.sub(r'[-|]+\s*\n', '', clean)

    # Featured Characters lines
    clean = re.sub(
        r'(?:^|\n)\s*(?:\*\*|__|[*])?\s*Featured Characters:.*',
        '', clean, flags=re.MULTILINE | re.IGNORECASE
    )

    # Normalize whitespace
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    clean = re.sub(r'[ \t]+', ' ', clean)

    return clean.strip()


def preprocess_episode(episode_path: Path) -> Path | None:
    """Convert episode markdown to clean TTS body text. Returns output path."""
    if not episode_path.exists():
        print(f"  ERROR: {episode_path} not found")
        return None

    raw = episode_path.read_text(encoding="utf-8")
    raw = strip_frontmatter(raw)

    dialogue_lines, remaining = extract_radio_play(raw)
    body = strip_prose_artifacts(remaining)

    if dialogue_lines:
        body = f"{body}\n\n" + "\n\n".join(dialogue_lines)

    stem = episode_path.stem
    episode_num = stem.split("_")[0]
    season_num = episode_season(episode_path)

    out_dir = TTS_TEXT_DIR / f"season{season_num}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{episode_num}.tts.txt"

    out_path.write_text(body, encoding="utf-8")
    print(f"  {episode_path.name} → {out_path}")
    return out_path


def episode_season(episode_path: Path) -> str:
    stem = episode_path.stem
    m = re.match(r'S(\d+)E\d+', stem)
    if m:
        return m.group(1).zfill(2)
    return "01"


def glob_episode(season: str, episode: str) -> Path:
    """Find episode S{season}E{episode} in episodes/."""
    ep_pattern = f"S{season}E{episode}"
    matches = sorted(EPISODES_DIR.glob(f"season{season}/{ep_pattern}_*.md"))
    if not matches:
        raise FileNotFoundError(f"No episode: {ep_pattern} in {EPISODES_DIR}")
    if len(matches) > 1:
        raise ValueError(f"Multiple matches for {ep_pattern}: {matches}")
    return matches[0]


def glob_season(season: str) -> list[Path]:
    return sorted(EPISODES_DIR.glob(f"season{season}/S{season}E*_*.md"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert episode markdown to clean TTS text")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", help="Episode ID, e.g. S01E01 or S01E01_the_frequency")
    group.add_argument("--season", help="Season number, e.g. 01")
    group.add_argument("--all", action="store_true", help="Process all episodes")
    args = parser.parse_args()

    if args.episode:
        parts = args.episode.split('_', 1)
        season_ep = parts[0]
        sub_id = parts[1] if len(parts) > 1 else None
        m = re.match(r'S(\d+)E(\d+)', season_ep, re.IGNORECASE)
        if not m:
            print(f"ERROR: --episode must match SXXEXX, got {args.episode}")
            sys.exit(1)
        season, ep = m.group(1).zfill(2), m.group(2).zfill(2)
        if sub_id:
            ep_pattern = f"S{season}E{ep}_{sub_id}.md"
            matches = sorted(EPISODES_DIR.glob(f"season{season}/{ep_pattern}"))
            if not matches:
                print(f"ERROR: no file matching {ep_pattern}")
                sys.exit(1)
            preprocess_episode(matches[0])
        else:
            preprocess_episode(glob_episode(season, ep))

    elif args.season:
        season = args.season.zfill(2)
        paths = glob_season(season)
        print(f"Season {season}: {len(paths)} episode(s)")
        for p in paths:
            preprocess_episode(p)

    elif args.all:
        total = 0
        by_season: dict[str, list[Path]] = {}
        for p in sorted(EPISODES_DIR.glob("season*/S*.md")):
            season = episode_season(p)
            by_season.setdefault(season, []).append(p)
        for season in sorted(by_season):
            print(f"Season {season}: {len(by_season[season])} episode(s)")
            for p in sorted(by_season[season]):
                preprocess_episode(p)
                total += 1
        print(f"\nDone. {total} .tts.txt file(s) generated.")


if __name__ == "__main__":
    main()