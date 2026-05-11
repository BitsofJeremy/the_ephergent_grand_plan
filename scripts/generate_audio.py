#!/usr/bin/env python3
"""
generate_audio.py — Generate MP3 audio for episodes via Kokoro TTS.

Reads tts_text/seasonNN/SXXEXX.tts.txt (final, with Signal intro/summary/outro),
chunks at ~2200 chars at sentence boundaries, calls Kokoro TTS API,
concatenates with ffmpeg, outputs to:
  - audio/seasonNN/SXXEXX.mp3 (grand_plan, permanent)
  - ephergent.com/public/audio/seasonNN/SXXEXX.mp3 (website copy)

Voice: bf_emma(0.7)+af_sarah(0.3) — Signal narrator
Engine: kokoro
Endpoint: http://sprecher.nexus.home.test:8880/v1

Usage:
    python scripts/generate_audio.py --episode S01E01
    python scripts/generate_audio.py --season 01
    python scripts/generate_audio.py --all
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
GRAND_PLAN = SCRIPT_DIR.parent.resolve()
TTS_TEXT_DIR = GRAND_PLAN / "tts_text"
AUDIO_DIR = GRAND_PLAN / "audio"
WEBSITE_ROOT = Path.home() / "Documents" / "code_repos" / "ephergent.com"
WEBSITE_AUDIO_DIR = WEBSITE_ROOT / "public" / "audio"

SPRECHER = "http://sprecher.nexus.home.test"
TTS_ENDPOINT = f"{SPRECHER}/api/tts/sync"
VOICE = "bf_emma(0.7)+af_sarah(0.3)"
ENGINE = "kokoro"
MAX_CHARS = 2200
CHUNK_DIR = Path("/tmp/ephergent_chunks")
CHUNK_DIR.mkdir(exist_ok=True)


def generate_chunk(text: str, out_file: Path) -> tuple[bool, str]:
    """Call Kokoro TTS for one chunk. Returns (success, error_message)."""
    form = urllib.parse.urlencode({"text": text, "voice": VOICE, "engine": ENGINE, "audio_format": "mp3"})
    with open("/tmp/tts_req.txt", "w") as f:
        f.write(form)
    r1 = subprocess.run(
        ["curl", "-s", "--max-time", "90", "-X", "POST", TTS_ENDPOINT,
         "-d", "@/tmp/tts_req.txt", "-o", "/tmp/tts_resp.json"],
        capture_output=True)
    if r1.returncode != 0:
        return False, f"curl exit {r1.returncode}"
    try:
        resp = json.loads(Path("/tmp/tts_resp.json").read_text())
        audio_url = resp.get("audio_url") or resp.get("audio", {}).get("url", "")
        if not audio_url and "url" in resp:
            audio_url = resp["url"]
    except Exception as e:
        resp_text = Path("/tmp/tts_resp.json").read_text()[:200]
        return False, f"bad JSON: {resp_text} — {e}"
    if not audio_url:
        return False, f"no audio_url in response: {resp}"
    r2 = subprocess.run(
        ["curl", "-s", "--max-time", "60", "-f", "-o", str(out_file),
         f"{SPRECHER}{audio_url}"],
        capture_output=True)
    if r2.returncode != 0:
        return False, f"download exit {r2.returncode}"
    return True, "ok"


def chunk_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Split on paragraph boundaries, ~2200 char chunks at sentence boundaries."""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 <= max_chars:
            cur += (" " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


def generate_episode(episode_num: str, season_num: str) -> tuple[bool, str]:
    """Generate MP3 for one episode. Returns (success, message)."""
    tts_txt = TTS_TEXT_DIR / f"season{season_num}" / f"{episode_num}.tts.txt"
    output_mp3 = AUDIO_DIR / f"season{season_num}" / f"{episode_num}.mp3"
    if not tts_txt.exists():
        return False, f"TTS text not found: {tts_txt}"

    tts_text = tts_txt.read_text(encoding="utf-8")
    chunks = chunk_text(tts_text)
    print(f"  [{episode_num}] {len(chunks)} chunks")

    for i, text in enumerate(chunks):
        f = CHUNK_DIR / f"{episode_num}_c{i:04d}.mp3"
        if f.exists() and f.stat().st_size > 500:
            print(f"    chunk {i} already exists, skipping")
            continue
        for attempt in range(3):
            ok, err = generate_chunk(text, f)
            if ok:
                break
            print(f"    chunk {i} attempt {attempt+1} failed: {err}")
            if attempt < 2:
                wait = 2 ** attempt * 2
                print(f"    retrying in {wait}s...")
                time.sleep(wait)
        if not ok:
            return False, f"chunk {i}: {err}"
        time.sleep(0.3)

    files = sorted(CHUNK_DIR.glob(f"{episode_num}_c*.mp3"), key=lambda p: int(p.stem.split("_c")[1]))
    if not files:
        return False, "no chunk files found"

    list_file = CHUNK_DIR / f"{episode_num}_chunks.txt"
    list_file.write_text("\n".join(f"file '{f.absolute()}'" for f in files))

    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c:a", "libmp3lame", "-q:a", "2", str(output_mp3)],
        capture_output=True)
    if r.returncode != 0:
        return False, f"ffmpeg: {r.stderr.decode()[:200]}"

    # Copy to website
    website_dest = WEBSITE_AUDIO_DIR / f"season{season_num}" / f"{episode_num}.mp3"
    website_dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", str(output_mp3), str(website_dest)], capture_output=True)

    size_mb = output_mp3.stat().st_size // 1024 // 1024
    return True, f"{size_mb}MB, {len(files)} chunks → {output_mp3.name} (copied to website)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate audio for Ephergent episodes via Kokoro TTS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode", help="Episode ID, e.g. S01E01")
    group.add_argument("--season", help="Season number, e.g. 01")
    group.add_argument("--all", action="store_true", help="Process all episodes")
    args = parser.parse_args()

    # Smoke test
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Smoke test...")
    test_file = CHUNK_DIR / "smoke.mp3"
    ok, err = generate_chunk("Testing. One. Two. Three.", test_file)
    if not ok:
        print(f"SMOKE TEST FAILED: {err}")
        sys.exit(1)
    print(f"  API OK: {test_file.stat().st_size // 1024}KB")

    def run_episode(episode_num: str, season_num: str) -> None:
        print(f"  Generating {episode_num}...", end=" ", flush=True)
        ok, msg = generate_episode(episode_num, season_num)
        print(msg)

    if args.episode:
        m = re.match(r'S(\d+)E(\d+)', args.episode, re.IGNORECASE)
        if not m:
            print(f"ERROR: --episode must match SXXEXX, got {args.episode}")
            sys.exit(1)
        season = m.group(1).zfill(2)
        ep = f"S{season}E{m.group(2).zfill(2)}"
        run_episode(ep, season)

    elif args.season:
        season = args.season.zfill(2)
        tts_dir = TTS_TEXT_DIR / f"season{season}"
        if not tts_dir.exists():
            print(f"ERROR: no TTS text found for season {season}")
            sys.exit(1)
        files = sorted(tts_dir.glob("S*.tts.txt"))
        print(f"Season {season}: {len(files)} episode(s)")
        for f in files:
            ep_num = f.stem
            run_episode(ep_num, season)

    elif args.all:
        by_season: dict[str, list[Path]] = {}
        for p in sorted(TTS_TEXT_DIR.glob("season*/*.tts.txt")):
            season = p.parent.name.replace("season", "")
            by_season.setdefault(season, []).append(p)
        for season in sorted(by_season):
            print(f"\nSeason {season}:")
            for p in sorted(by_season[season]):
                ep_num = p.stem
                run_episode(ep_num, season)


if __name__ == "__main__":
    import re
    main()