#!/usr/bin/env python3
"""
generate_summaries.py — Derive 2-3 sentence third-person Signal-voice episode summaries.

Reads episode markdown, extracts story beats from section headers and first/last paragraphs,
generates a summary in Signal's warm, slightly theatrical third-person voice.
Writes to excerpts/SXXEXX.txt.

Usage:
    python scripts/generate_summaries.py --episode S01E01
    python scripts/generate_summaries.py --season 01
    python scripts/generate_summaries.py --all
"""
import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
GRAND_PLAN = SCRIPT_DIR.parent.resolve()
EPISODES_DIR = GRAND_PLAN / "episodes"
EXCERPTS_DIR = GRAND_PLAN / "excerpts"


def extract_title(text: str) -> str:
    """Pull episode title from first # heading."""
    m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "Untitled Episode"


def _is_metadata(text: str) -> bool:
    """Return True if text is a metadata row that should be skipped in summaries."""
    t = text.strip()
    if not t:
        return True
    # LOCKED RULES table rows
    if t.startswith('|') and ('Rule' in t or '✅' in t or re.search(r'\|[-:\s]+\|', t)):
        return True
    # Featured Characters lines
    if 'featured characters' in t.lower():
        return True
    return False


def _extract_paragraphs(text: str) -> list[str]:
    """Extract clean prose paragraphs, skipping metadata."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    return [p for p in paras if not _is_metadata(p)]


def extract_beats(text: str) -> list[str]:
    """Extract story section headers from markdown, filtering out metadata."""
    headers = re.findall(r'^#+\s+(.+)$', text, re.MULTILINE)
    beats = []
    for h in headers:
        h_lower = h.lower()
        h_stripped = h.strip()
        # Skip metadata/structural headers
        if any(skip in h_lower for skip in ['coffee', 'locked', 'chart', 'featured', 'rules check']):
            continue
        # Skip table rows (contain |)
        if '|' in h:
            continue
        # Skip Roman numeral section headers (I., II., III., IV.)
        if re.match(r'^[IVXLCDM]+\.\s+', h_stripped):
            continue
        # Skip episode title header (e.g. "S01E01 — The Frequency")
        if re.match(r'^S\d+E\d+', h_stripped):
            continue
        beats.append(h_stripped)
    return beats


def generate_summary(episode_path: Path, raw: str) -> str:
    """Generate a Signal-voice summary from episode content."""
    title = extract_title(raw)
    # Remove frontmatter
    if raw.startswith('---'):
        m = re.match(r'^---\n.*?\n---\n', raw, re.DOTALL)
        if m:
            raw = raw[m.end():]

    # Check if radio-play format (has **CHARACTER:**)
    is_radio_play = bool(re.search(r'^\*\*[A-Za-z]+:', raw, re.MULTILINE))

    if is_radio_play:
        character_blocks = re.findall(
            r'^\*\*([A-Za-z][A-Za-z0-9 ]*?):\*\*\n(.*?)(?=^\*\*|\Z)',
            raw, re.MULTILINE | re.DOTALL
        )
        beats = []
        for name, dialogue in character_blocks[:3]:
            dialogue = dialogue.replace('**', '').replace('*', "'").strip()
            if len(dialogue) > 150:
                dialogue = dialogue[:150].rsplit(' ', 1)[0] + "..."
            if dialogue:
                beats.append(f"{name.strip()} {dialogue}")
    else:
        section_beats = extract_beats(raw)
        paras = _extract_paragraphs(raw)
        first_par = paras[0] if paras else ""

        beats = section_beats[:2] if section_beats else []
        if first_par and len(first_par) > 50:
            first_be = first_par[:120].rsplit(' ', 1)[0] + "..."
            if first_be:
                beats.append(first_be)

    # Build summary
    clean_title = re.sub(r'^S\d+E\d+\s*—\s*', '', title)

    # Find protagonist
    protagonists = ["Pixel Paradox", "Pixel", "A1", "Clive", "The crew", "The Ephergent"]
    protagonist = "Pixel Paradox"
    intro = raw[:500]
    for p in protagonists:
        if p.lower() in intro.lower():
            protagonist = p
            break

    summary_parts = []

    # Part 1
    if is_radio_play and beats:
        part1 = f"{protagonist} encounters {clean_title.lower()}"
    elif section_beats:
        first_section = section_beats[0].strip()
        if len(first_section) > 60:
            first_section = first_section[:60].rsplit(' ', 1)[0] + "..."
        part1 = f"{protagonist} faces {first_section.lower()}"
    else:
        part1 = f"{protagonist} navigates {clean_title.lower()}"
    summary_parts.append(part1)

    # Part 2
    if is_radio_play and len(character_blocks) > 1:
        summary_parts.append(f"{character_blocks[1][0].strip().lower()} responds")
    elif len(section_beats) > 1:
        second = section_beats[1].strip()
        if len(second) > 60:
            second = second[:60].rsplit(' ', 1)[0] + "..."
        summary_parts.append(second.lower())
    else:
        summary_parts.append("the signal calls from the void")

    # Part 3
    if is_radio_play:
        summary_parts.append("and the story continues")
    elif len(section_beats) > 2:
        last_section = section_beats[-1].strip()
        if len(last_section) > 50:
            last_section = last_section[:50].rsplit(' ', 1)[0] + "..."
        summary_parts.append(f"and {last_section.lower()}")
    elif len(paras) > 1:
        last_par = paras[-1]
        if len(last_par) > 40:
            last_be = last_par[:80].rsplit(' ', 1)[0]
            if last_be:
                summary_parts.append(f"and {last_be.lower()}")
            else:
                summary_parts.append("and the signal continues")
        else:
            summary_parts.append("and the signal continues")
    else:
        summary_parts.append("and the signal continues")

    summary = f"In this episode: {summary_parts[0]}. {summary_parts[1]}. {summary_parts[2]}."
    summary = re.sub(r'\s+', ' ', summary)
    if len(summary) > 300:
        summary = summary[:297] + "..."
    return summary


def generate_summary_for_episode(episode_path: Path) -> Path | None:
    if not episode_path.exists():
        print(f"  ERROR: {episode_path} not found")
        return None

    raw = episode_path.read_text(encoding="utf-8")
    summary = generate_summary(episode_path, raw)

    stem = episode_path.stem
    episode_num = stem.split("_")[0]
    season_num = episode_season(episode_path)

    out_dir = EXCERPTS_DIR / f"season{season_num}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{episode_num}.txt"

    out_path.write_text(summary, encoding="utf-8")
    print(f"  {episode_path.name} → {out_path}")
    print(f"    Summary: {summary[:100]}...")
    return out_path


def episode_season(episode_path: Path) -> str:
    stem = episode_path.stem
    m = re.match(r'S(\d+)E\d+', stem)
    if m:
        return m.group(1).zfill(2)
    return "01"


def glob_episode(season: str, episode: str) -> Path:
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
    parser = argparse.ArgumentParser(description="Generate Signal-voice episode summaries")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", help="Episode ID, e.g. S01E01")
    group.add_argument("--season", help="Season number, e.g. 01")
    group.add_argument("--all", action="store_true", help="Process all episodes")
    args = parser.parse_args()

    if args.episode:
        parts = args.episode.split('_', 1)
        season_ep = parts[0]
        m = re.match(r'S(\d+)E(\d+)', season_ep, re.IGNORECASE)
        if not m:
            print(f"ERROR: --episode must match SXXEXX, got {args.episode}")
            sys.exit(1)
        season, ep = m.group(1).zfill(2), m.group(2).zfill(2)
        generate_summary_for_episode(glob_episode(season, ep))

    elif args.season:
        season = args.season.zfill(2)
        paths = glob_season(season)
        print(f"Season {season}: {len(paths)} episode(s)")
        for p in paths:
            generate_summary_for_episode(p)

    elif args.all:
        total = 0
        by_season: dict[str, list[Path]] = {}
        for p in sorted(EPISODES_DIR.glob("season*/S*.md")):
            season = episode_season(p)
            by_season.setdefault(season, []).append(p)
        for season in sorted(by_season):
            print(f"Season {season}: {len(by_season[season])} episode(s)")
            for p in sorted(by_season[season]):
                generate_summary_for_episode(p)
                total += 1
        print(f"\nDone. {total} summary file(s) generated.")


if __name__ == "__main__":
    main()