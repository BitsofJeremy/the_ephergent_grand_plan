# CLAUDE.md — The Ephergent Grand Plan

**This repo is the CANONICAL source for The Ephergent.** All writing, editing, and creative work happens here. `ephergent.com` is a derived deployment — never edit its `transmissions/`, `lore/`, or `crew/` directories directly.

## Two-Repo Architecture (Option B)

| Repo | Path | Role |
|------|------|------|
| `the_ephergent_grand_plan` | `episodes/seasonNN/` | **Canonical source** — episodes written here |
| `the_ephergent_grand_plan` | `lore/` | **Canonical source** — lore entries written here |
| `the_ephergent_grand_plan` | `characters/crew/` | **Canonical source** — crew bibles written here |
| `ephergent.com` | `src/content/transmissions/` | **Derived** — synced from this repo |
| `ephergent.com` | `src/content/lore/` | **Derived** — synced from this repo |
| `ephergent.com` | `src/content/crew/` | **Derived** — synced from this repo |

### Sync Workflow

```bash
# 1. Write/edit in grand_plan (episodes/, lore/, characters/crew/)

# 2. Sync to website (preserves frontmatter — DO NOT use cp):
./scripts/sync_to_website.sh --all        # episodes + lore + crew
./scripts/sync_to_website.sh --episodes   # episodes only
./scripts/sync_to_website.sh --lore       # lore only
./scripts/sync_to_website.sh --crew       # crew only

# 3. Build and deploy:
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 4. Commit to grand_plan and push:
git add -A && git commit -m "description" && git push origin main
```

⚠️ **NEVER `cp` files directly to ephergent.com** — the sync script preserves Astro's required YAML frontmatter. Naive copies break the build.

---

## Current Canonical Plan: REFACTOR/

The `REFACTOR/` directory contains the current authoritative planning documents:
- `ephergent_canon_v2.md` — single source of truth universe bible (13 Locked Rules)
- `season_architecture_v2.md` — 30-episode breakdown (10 per season)
- `absurdity_guide.md` — tone/style guide
- `TIME_WAR_INTEGRATION.md` — retrocausality mechanics as physics
- `episode_map.md` — amalgamation plan (which episodes merged/split)

**Do not contradict REFACTOR/ documents.** If something in REFACTOR/ conflicts with older files, REFACTOR/ wins.

---

## Episode Structure

Episodes live in `episodes/season{1,2,3}/`. File naming: `S01E01_title.md`

- **season01/**: 10 episodes (S01E06 replaced by S01E10_bureaucracy_frequency.md as the free episode)
- **season02/**: 10 episodes (includes S02E10_the_frequency_and_the_future.md — Pixel's first deliberate Grabovoi code use)
- **season03/**: 11 episodes (includes S03E08y_the_machine_that_grew.md — experimental episode told through Grabovoi code sequences)
- **Total**: 31 canonical episodes

**Canonical S01E01**: `S01E01_the_frequency.md` (pilot)
**Canonical S01E07**: `S01E07_the_song_at_the_edge_of_everything.md` (amalgamated from former S01E06 and S01E07)
**Free Episode (S01E06 slot)**: `S01E10_bureaucracy_frequency.md` — The Crystallized Laughter (CLX + Grabovoi codes tutorial)

---

## Character Specs (Current Canon — 13 Locked Rules)

| Rule | Description |
|------|-------------|
| 1 | Frequencies, not dimensions |
| 2 | Space vocabulary only (fly, dock, navigate — not voyage/sailing) |
| 3 | A1 IS the espresso machine — the machine IS the ship IS A1 |
| 4 | Coffee flavor in every A1 scene (bitter=worried, thin=exhausted, rich=engaged) |
| 5 | Clive = knee-high robot, sphere head, fedora — NOT a stapler |
| 6 | Barry Kowalski = alive in the Wellspring (state, not place) |
| 7 | Mochi never speaks — glows, pulses, warms |
| 8 | The Builders are NOT villains |
| 9 | The Drift is entropy, not a villain |
| 10 | The Wellspring is a state, not a place |
| 11 | 15MB per-game hard cap (game adaptations) |
| 12 | Barry's field notes are methodical, precise, observational — never dramatic |
| 13 | Episodes are written in third person. Signal reads all episodes in third person. |

### Clive
- **Form:** Builder Companion Unit, knee-high (2 feet), barrel-chested, ancient bronze-verdigris patina
- **Head:** Single glowing sphere, **blue-white** glow (NOT pink/magenta)
- **Fedora:** Worn brown-grey, tilted, Barry's gift — essential, never optional
- **Chest:** Blue-white glowing core
- **Voice:** Hard-boiled noir detective — short declarative sentences, world-weary, dry humor
- Sphere pulses: *click-click-CLICK* (emphasis), *click-CLICK* (agreement)
- Fedora angle indicates mood; tips toward people he's greeting

### Pixel Paradox
- Hair: **fiery red**, not aqua blue
- Role: Primary narrator, captain, lead correspondent
- Voice: Conversational, caffeinated, "friend catching you up"

### A1/Arc
- Form: Espresso machine — the machine IS the ship IS A1
- British formal, protective, opinions on everything
- **A1 did not choose the espresso machine form.** He was compressed into it by damage + last coherent thought was coffee. The meaning came later, from crew's attention.
- Coffee: bitter=worried, thin/pale=exhausted, rich/complex=engaged, perfect/balanced=resolution, extraordinary=unprecedented event

### Mochi
- Builder Companion Device, dome-shaped
- **Never speaks** — communicates through color changes and warmth
- Warm in Pixel's pocket = normal; dims = grief-adjacent; intensifies = near Wellspring

---

## Time War (Integrated)

Time War retrocausality is canon and integrated into the episodes:
- The loop is not cosmic fate — it is human automation
- Only unpredictable consciousness breaks the loop
- The future reaches backward (retrocausality)
- The crew's attention/broadcasting is active defense against entropy
- TW-1 through TW-5 beats distributed across S01-S03

**Do not write episodes that contradict Time War mechanics.**

---

## Style Rules

- Frequencies, not dimensions, planes, realms, multiverse
- The Space, not the Sea
- A1 IS the espresso machine — coffee in every A1 scene
- Clive = sphere head + fedora, NOT stapler
- Barry is alive in the Wellspring (state, not place)
- Mochi never speaks
- The Builders are not villains
- The Drift is entropy, not a villain
- Episodes are written in third person (Signal reads in third person)

---

## Grabovoi Codes (Integrated)

Grabovoi Codes are pre-Builder numerological sequences — the universe's original firmware. They act as localized frequency overrides, forcing reality back to its "original state." Spaces are critical: they represent quantum pauses where the universe processes the command.

**12 Core Codes** map to the 12 original Locked Rules. An additional 13th code (519 714 8 — "Everything Is Possible") was used by Pixel for her first deliberate code activation.

Key lore: `lore/grabovoi-codes.md` | `lore/barrys-field-notes-grabovoi.md`

Key episodes: `S01E10_bureaucracy_frequency.md` (tutorial), `S02E10_the_frequency_and_the_future.md` (first deliberate use), `S03E08y_the_machine_that_grew.md` (told through code sequences)

Full plan: `plans/grabovoi-code-integration.md` | `plans/grabovoi-episode-mapping.md`

---

## Key Paths

| Path | Purpose |
|------|---------|
| `episodes/seasonNN/` | Canonical episode scripts |
| `lore/` | Canonical lore entries |
| `characters/crew/` | Canonical character bibles |
| `REFACTOR/` | Authoritative planning documents |
| `scripts/sync_to_website.sh` | Sync script — syncs episodes/lore/crew to ephergent.com |
| `source_archive/signal_lore_prototype/` | Old design docs — reference only |

---

## Audio Pipeline

Audio generation reads from `ephergent.com/src/content/transmissions/` (TTS text source).
Voice: single narrator `bf_emma+af_sarah` blend — no character voice separation.

When episode content changes: re-sync to website, then regenerate TTS text, then generate audio.
