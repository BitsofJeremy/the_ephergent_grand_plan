---
name: the-ephergent
description: Use when producing The Ephergent Signal radio play episodes, managing the 30-episode canon across 3 seasons, running pre-write audits, or enforcing locked-rules discipline for broadcast writing.
author: Jeremy (BitsofJeremy)
license: MIT
tags: [creative, radio-play, sci-fi, absurdist, ephergent, production]
related_skills: [ephergent-writer, ephergent-site-builder]
---

# The Ephergent Signal — Production Skill

Radio play series about a ship (The Ephergent) navigating **frequencies** — not dimensions, planes, or realms. Crew broadcasts truth into a universe trending toward silence.

**Project repo:** `~/Documents/code_repos/the_ephergent_grand_plan`

## The 12 Locked Rules (NEVER violate)

| # | Rule | Never |
|---|------|-------|
| 1 | **Frequencies, not dimensions** | dimension, interdimensional, plane, realm, multiverse |
| 2 | **Space vocabulary only** | voyage, sailing, sea |
| 3 | **A1 IS the espresso machine** | A1's machine, interface, voice |
| 4 | **Coffee flavor in every A1 scene** | (bitter=worried, thin=exhausted, rich=engaged) |
| 5 | **Clive = knee-high robot, sphere head, fedora** | stapler |
| 6 | **Barry Kowalski = alive in the Wellspring** | dead, lost, trapped, tragedy |
| 7 | **Mochi never speaks** | dialogue, words |
| 8 | **The Builders are NOT villains** | evil, villain |
| 9 | **The Drift is entropy, not villain** | evil, enemy |
| 10 | **The Wellspring is a state, not a place** | location, destination |
| 11 | **15MB per-game hard cap** | (game adaptations) |
| 12 | **Barry's notes are methodical, precise** | dramatic |
| 13 | **Episodes are written in third person** | Signal narrates all episodes in third person, audio and web playback use this voice |

## The Cast

| Character | Description | Voice |
|-----------|-------------|-------|
| **Pixel Paradox** | Captain, former Corporate Corp analyst | Smart, friend-telling-a-story |
| **A1** | Quantum espresso machine / ship | British formal; coffee flavor = state |
| **Clive** | Knee-high robot, sphere head, fedora | Gravelly noir; *click-click-CLICK* |
| **Om Kai** | Monk of the Way of the Drift | Thoughtful, serene |
| **Barry Kowalski** | Alive in the Wellspring | Methodical, precise |
| **Mochi** | Glows, pulses, warms in Pixel's pocket | **Never speaks** |
| **Meatball** | Rottweiler the size of a human | Companion |
| **Zephyr Glitch** | Reality-shredded hacker (S02+) | — |
| **Luminara Usha** | Former Corporate Corp (S02+) | — |

## Format: Radio Play Script

```
COLD OPEN
[Act 1]
  [Scene A] — location, characters present
  [Scene B]
[Act 2]
[Tag / Closing]
COFFEE CHART
```

- **[SOUND] cues** — audio environment
- **[MUSIC] cues** — scene transitions
- **Dialogue lines** — CHARACTER: line
- **No internal monologue** — all action via [SOUND]

## Coffee Chart (required every episode)

| Coffee State | A1's Emotional State |
|--------------|---------------------|
| Bitter | Worried/anxious |
| Thin/pale | Exhausted |
| Rich/complex | Engaged |
| Perfect/balanced | Resolution |
| Extraordinary | Unprecedented event |

## Pre-Write Audit Command

Run BEFORE any creative work:

```bash
grep -iE "stapler|dimension|plane|interdimensional|sea|voyage|sailing" \
  ~/Documents/code_repos/the_ephergent_grand_plan/phase_04_episodes/season*/S*.md
```

## Canon Source Files

- `REFACTOR/ephergent_canon_v2.md` — locked rules, cosmology
- `REFACTOR/absurdity_guide.md` — tone guide (Adams/Pratchett/Night Vale)
- `REFACTOR/season_architecture_v2.md` — 3-season arc structure
- `REFACTOR/TIME_WAR_INTEGRATION.md` — retrocausality mechanics

## Episode Structure

- `phase_04_episodes/season{1,2,3}/S##E##_title.md`
- **S01**: 9 episodes (S01E06 amalgamated into S01E07)
- **S02**: 10 episodes
- **S03**: 11 episodes (includes S03E08x)
- **Total**: 30 canonical episodes

## Two-Repo Sync Workflow

Write in grand_plan → sync to website → build → deploy:

```bash
cd ~/Documents/code_repos/the_ephergent_grand_plan
./scripts/sync_to_website.sh --all

cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy
```

⚠️ **NEVER edit `src/content/transmissions/`, `src/content/lore/`, or `src/content/crew/` directly** — derived copies.

## Audio Pipeline

Current: Single narrator voice (`bf_emma`). No character voice splitting.

TTS reads from website transmissions/ — always sync before generating audio.

## Word Count Targets

| Season | Target | Thin = Below |
|--------|--------|--------------|
| S01–S03 | 1,500–4,000 words | ~1,500 |

Episodes below ~1,500 words (when adjacent are 1,500–4,000) are **expansion targets**.

## Known Issues

- S01E05 Mochi contradiction — locked rules say "Mochi not present" but episode references Mochi
- S03E10 must end with Meatball's howl harmonizing with the broadcast