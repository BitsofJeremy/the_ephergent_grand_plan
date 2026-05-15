# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Canonical Source

This repo is **THE CANONICAL SOURCE** for The Ephergent. All writing, editing, and creative work happens here. `ephergent.com` is a derived deployment — never edit its `transmissions/`, `lore/`, or `crew/` directories directly.

## Two-Repo Architecture

| Repo | Role |
|------|------|
| `the_ephergent_grand_plan` | Canonical source for episodes, lore, characters |
| `ephergent.com` | Derived deployment — synced from this repo |

**Sync workflow** (ALWAYS use this, NEVER `cp`):

```bash
# 1. Write/edit in grand_plan
./scripts/sync_to_website.sh --all

# 2. Build and deploy:
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 3. Commit to grand_plan and push
git add -A && git commit -m "description" && git push origin main
```

The sync script preserves Astro's required YAML frontmatter. Naive copies break the build.

## Authoritative References

`REFACTOR/` contains current authoritative documents. When in doubt, these win:

- `ephergent_canon_v2.md` — universe bible, 13 Locked Rules
- `season_architecture_v2.md` — 30-episode breakdown (10 per season)
- `absurdity_guide.md` — tone/style guide
- `TIME_WAR_INTEGRATION.md` — retrocausality mechanics
- `episode_map.md` — amalgamation plan

## Episode Structure

- `episodes/season01/` — 10 episodes (S01E06 slot = S01E10_bureaucracy_frequency.md as free episode)
- `episodes/season02/` — 12 episodes
- `episodes/season03/` — 13 episodes

File naming: `SXXEXX_title.md`. Episodes written in **third person**.

## 13 Locked Rules (Enforced Always)

| # | Rule | Never say |
|---|------|-----------|
| 1 | Frequencies, not dimensions | dimension, interdimensional, plane, realm |
| 2 | The Space, not the Sea | voyage, sailing, sea |
| 3 | A1 IS the espresso machine | A1's machine, interface |
| 4 | Coffee flavor in every A1 scene | (bitter=worried, thin=exhausted, rich=engaged) |
| 5 | Clive = knee-high robot, sphere head, fedora | stapler |
| 6 | Barry Kowalski = alive in the Wellspring | dead, lost, trapped |
| 7 | Mochi never speaks | dialogue, words |
| 8 | The Builders are NOT villains | evil, villain |
| 9 | The Drift is entropy, not villain | evil, enemy |
| 10 | The Wellspring is a state, not a place | location, destination |
| 11 | 15MB per-game hard cap | (game adaptations) |
| 12 | Barry's notes are methodical, precise | dramatic |
| 13 | Episodes written in third person | Signal reads in third person |

Full character specs in `REFACTOR/ephergent_canon_v2.md`.

## Common Tasks

### Write an episode

Use the `four-step-episode` skill via `/four-step-episode`. This runs: SciFi writer → Literary critic → Rewrite → Humanizer.

### Run audio pipeline

```bash
python scripts/preprocess_episodes.py --episode S01E01
python scripts/generate_summaries.py --episode S01E01
python scripts/assemble_tts_text.py --episode S01E01
python scripts/generate_audio.py --episode S01E01
```

Use `--all` for full batch. TTS endpoint: `http://sprecher.nexus.home.test/api/tts/sync`.

### Sync content to website

```bash
./scripts/sync_to_website.sh --all        # episodes + lore + crew
./scripts/sync_to_website.sh --episodes   # episodes only
./scripts/sync_to_website.sh --lore       # lore only
./scripts/sync_to_website.sh --crew       # crew only
```

## Key Paths

| Path | Purpose |
|------|---------|
| `episodes/season{1,2,3}/` | Canonical episode scripts |
| `lore/` | Canonical lore entries (world/ merged here) |
| `characters/crew/` | Canonical character bibles |
| `REFACTOR/` | Authoritative planning documents |
| `scripts/sync_to_website.sh` | Sync to ephergent.com |
| `scripts/` | Audio pipeline scripts |

## Style Rules

- Frequencies, not dimensions, planes, realms
- The Space, not the Sea — space vocabulary only (fly, dock, navigate)
- A1 IS the espresso machine — coffee flavor in every scene
- Clive = sphere head + fedora, blue-white glow, noir detective voice
- Mochi never speaks — glows, pulses, warms
- Episodes in third person