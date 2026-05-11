#!/usr/bin/env python3
"""
assemble_tts_text.py — Build final TTS text with Signal intro, summary, body, and outro.

Reads:
  - excerpts/SXXEXX.txt (Signal-voice episode summary)
  - tts_text/SXXEXX.tts.txt (clean episode body from preprocess_episodes.py)
Output:
  - tts_text/SXXEXX.tts.txt (final — overwrites intermediate with intro+summary+pause+body+outro)

Format:
  Hello from wherever and whenever you are. I'm the Ephergent Signal, and this is The Ephergent.
  In this episode: [summary from excerpts/]

  [pause]

  [clean episode body]

  Thank you for listening to this neural dimensional broadcast of The Ephergent. Until next time.

Usage:
    python scripts/assemble_tts_text.py --episode S01E01
    python scripts/assemble_tts_text.py --season 01
    python scripts/assemble_tts_text.py --all
"""
import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
GRAND_PLAN = SCRIPT_DIR.parent.resolve()
EXCERPTS_DIR = GRAND_PLAN / "excerpts"
TTS_TEXT_DIR = GRAND_PLAN / "tts_text"


def assemble(episode_num: str, season_num: str) -> Path | None:
    """Assemble final TTS text for one episode. Returns output path."""
    excerpt_path = EXCERPTS_DIR / f"season{season_num}" / f"{episode_num}.txt"
    body_path = TTS_TEXT_DIR / f"season{season_num}" / f"{episode_num}.tts.txt"
    out_path = body_path  # overwrite intermediate with final

    if not body_path.exists():
        print(f"  ERROR: TTS body not found: {body_path}")
        print(f"  Run preprocess_episodes.py first.")
        return None

    body = body_path.read_text(encoding="utf-8")

    summary = ""
    if excerpt_path.exists():
        summary = excerpt_path.read_text(encoding="utf-8").strip()
    else:
        print(f"  WARNING: excerpt not found: {excerpt_path} — generating placeholder")
        summary = "a new transmission from the signal"

    # Signal's intro — excerpt starts with "In this episode:", so just prepend greeting
    intro = (
        "Hello from wherever and whenever you are. "
        "I'm the Ephergent Signal, and this is The Ephergent. "
        f"{summary}"
    )

    # Signal's outro
    outro = (
        "Thank you for listening to this neural dimensional broadcast of The Ephergent. "
        "Until next time."
    )

    # Assemble: intro + body + outro
    final_text = f"{intro}\n\n{body}\n\n{outro}"

    out_path.write_text(final_text, encoding="utf-8")
    print(f"  {episode_num} assembled → {out_path}")
    return out_path


def episode_season_from_num(episode_num: str) -> str:
    """Extract season from episode number like S01E01."""
    m = re.match(r'S(\d+)E\d+', episode_num)
    if m:
        return m.group(1).zfill(2)
    return "01"


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble final TTS text with Signal intro/summary/outro")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", help="Episode ID, e.g. S01E01")
    group.add_argument("--season", help="Season number, e.g. 01")
    group.add_argument("--all", action="store_true", help="Process all episodes")
    args = parser.parse_args()

    if args.episode:
        m = re.match(r'S(\d+)E(\d+)', args.episode, re.IGNORECASE)
        if not m:
            print(f"ERROR: --episode must match SXXEXX, got {args.episode}")
            sys.exit(1)
        season = m.group(1).zfill(2)
        ep = f"S{season}E{m.group(2).zfill(2)}"
        assemble(ep, season)

    elif args.season:
        season = args.season.zfill(2)
        # Find all tts_text files for this season
        tts_dir = TTS_TEXT_DIR / f"season{season}"
        if not tts_dir.exists():
            print(f"ERROR: no TTS text found for season {season}")
            sys.exit(1)
        files = sorted(tts_dir.glob("S*.tts.txt"))
        print(f"Season {season}: {len(files)} episode(s)")
        for f in files:
            ep_num = f.stem  # e.g. "S01E01"
            assemble(ep_num, season)

    elif args.all:
        total = 0
        by_season: dict[str, list[Path]] = {}
        for p in sorted(TTS_TEXT_DIR.glob("season*/*.tts.txt")):
            season = p.parent.name.replace("season", "")  # "01"
            by_season.setdefault(season, []).append(p)
        for season in sorted(by_season):
            print(f"Season {season}: {len(by_season[season])} episode(s)")
            for p in sorted(by_season[season]):
                ep_num = p.stem
                assemble(ep_num, season)
                total += 1
        print(f"\nDone. {total} final .tts.txt file(s) assembled.")


if __name__ == "__main__":
    main()