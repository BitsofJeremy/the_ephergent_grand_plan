# GRABOVOI CODES INTEGRATION PLAN
**Status:** In Progress
**Date:** 2026-05-09

---

## CONTEXT

The Ephergent Signal is a transmedia science fiction universe about interdimensional journalists hopping frequencies. A recent video on Grabovoi Codes — numerological "cheat codes" for reality — inspired a request to integrate these as a core worldbuilding mechanic. The system maps naturally onto the existing frequency-hopping architecture:

- **Brain as Radio** → Consciousness as frequency-tuning
- **Numerical sequences** → Frequency coordinate systems
- **Spaces between digits** → Dangerous temporal voids (Silence Zones)
- **Reality hacking** → Frequency manipulation

The challenge: Fold Grabovoi Codes into the existing 12 Locked Rules without contradiction, distribute them across 3 seasons coherently, and do so within the current naming conventions that use an outdated `phase_XX_` prefix.

---

## PHASE 0: REMOVE `phase_XX_` PREFIX

### What
Rename all `phase_XX_<name>/` directories to clean names:

| Old Name | New Name |
|----------|----------|
| `phase_01_world/` | `world/` |
| `phase_02_characters/` | `characters/` |
| `phase_03_seasons/` | `seasons/` |
| `phase_04_episodes/` | `episodes/` |
| `phase_05_games/` | `games/` |
| `phase_05_lore/` | `lore/` |
| `phase_06_transmissions/` | `transmissions/` |
| `phase_07_site/` | `site/` |
| `phase_08_image_production/` | `image_production/` |

### Why
- `phase_XX_` was a workflow organizer from early development — now a legacy label
- Clean names align with the professional, production-grade tone of the project
- Reduces cognitive overhead for new contributors

### Files to Update After Rename
- `CLAUDE.md` — Update all path references
- `scripts/sync_to_website.sh` — Update hardcoded paths if any reference old names
- Any frontmatter or scripts that embed directory paths

### Verification
```bash
# After rename, verify these pass:
scripts/sync_to_website.sh --episodes
scripts/sync_to_website.sh --lore
scripts/sync_to_website.sh --crew
```

---

## PHASE 1: WORLD BUILD

### 1.1 Create Core Lore Entry — `lore/grabovoi-codes.md`

Define what Grabovoi Codes ARE in-universe:

**Working Definition:**
- Grabovoi Codes are pre-Builder numerological sequences — the universe's original firmware
- The Builders discovered them embedded in the quantum static, reverse-engineered from the universe's source
- They are strings of digits that act as **localized frequency overrides** — forcing a specific area of reality back to its "original state"
- Spaces within codes represent **quantum pauses** — intentional voids where the universe processes the command
- **The 12 Core Codes** (one per Locked Rule, not coincidental)

**The 12 Core Codes:**
| Code | Purpose | Lore Origin |
|------|---------|-------------|
| 518 3142 | Frequency Stabilization | Found at oldest Builder Stations |
| 814 7215 | Probability Reset | Mapped from probability currents |
| 519 7148 | Everything Is Possible | Origin unknown — may predate Builders |
| 888 8888 | Divine Protection | Appears when frequency is collapsing |
| 520 7418 | Unexpected Money | Misread as abundance in some frequencies |
| ... | ... | ... |

*(Full list to be developed in agent work)*

**Spaces are dangerous:**
- Failed code execution creates **glitch zones** — localized frequency tears
- Incorrect spacing = fragments of two frequencies bleeding together
- Worst case: a **silence zone** forms

### 1.2 Create Lore Entry — `lore/barrys-field-notes-grabovoi.md`

Barry's methodical observations about the codes — Rule 12 compliant (methodical, precise, observational).

### 1.3 Update `world/frequency-system.md` (or create `world/the-space.md`)

Add section on Grabovoi Codes as a frequency navigation mechanic. Integrate with existing:

- Probability currents (invisible rivers of likelihood)
- Frequency Storms (Scatter, Lock, Synthesis)
- Silence Zones (absolute absence)

### 1.4 Create Lore Entry — `lore/the-silence-zones.md`

Expand Silence Zones to reflect what happens when a code fails: the spaces in the sequence become real voids.

### 1.5 Update `lore/a1-navigator.md`

A1's navigation capabilities extended:
- Can detect Grabovoi Code frequency signatures
- Coffee flavor responds to proximity to code sequences
- Codes are **ancient** — A1 recognizes their architecture as older than his own systems

### 1.6 Update `lore/frequency-storms.md`

Add **Code Storms** as a fourth storm type:
- **Code Storms** form when too many codes are activated in one area
- Reality attempts to process too many overrides simultaneously
- Creates a **probability cascade** — multiple possible realities collide

---

## PHASE 2: SEASON DISTRIBUTION

### Season 1 — Introduction (Episodes 1-10)
**Theme:** Awareness — characters discover codes exist

| Episode | Integration Point |
|---------|-------------------|
| S01E01 (The Frequency) | Add a line about A1 detecting an "old signal beneath the frequency" — hint at codes |
| S01E03 (Signal Keepers) | Clive remembers a Builder station that had "numbers etched into the walls" |
| S01E07 (The Song at the Edge) | Mochi pulses blue-white when near a code (foreshadowing) |

**New Episode — S01E10:** A bureaucratic dimension vending machine bit (the 300-word absurd scene from the video prompt — standalone comedic relief)

### Season 2 — Integration (Episodes 11-20)
**Theme:** Understanding — characters learn how codes work

| Episode | Integration Point |
|---------|-------------------|
| S02E00 (The Frequency Before) | Barry encounters code sequences in his field notes |
| S02E05 | Pixel uses a code accidentally to escape a bad frequency |
| S02E08 | Full code mechanics explained via Clive's memory restoration |

**New Episode — S02E10:** The first time a code is used deliberately — "The 519 7148 Everything Is Possible episode"

### Season 3 — Mastery (Episodes 21-30)
**Theme:** Mastery and consequence — codes become both tool and threat

| Episode | Integration Point |
|---------|-------------------|
| S03E01 (Where Frequencies Have No Name) | Deep space contains "code storms" — entire regions of pure numerology |
| S03E06 | The Wellspring state is reached via a specific code sequence |
| S03E10 | An antagonist uses codes to lock frequencies permanently |
| S03E11 | Resolution involves the crew broadcasting ALL 12 core codes simultaneously |

**New Episode — S03E08x (Interstitial):** "The Machine That Grew" — an episode told entirely through code sequences

---

## PHASE 3: WRITE

### 3.1 First Pass — AI Draft
Using `scifi-fantasy-writer` and `radio-play-producer` agents to:
- Draft `lore/grabovoi-codes.md` with full code definitions
- Draft new/updated episodes with code integration
- Maintain character voice (Pixel = conversational, Arc = British formal, Clive = noir)

### 3.2 Critique Pass
Using `literary-critic-scifi-fantasy` agent:
- Verify Grabovoi codes don't contradict 12 Locked Rules
- Check character voice consistency
- Verify sci-fi tone (not pseudoscience spiritualism)
- Verify absurdity level matches series tone

---

## PHASE 4: HUMANIZE

### 4.1 Humanize Pass
Using `humanizer` agent on all generated text:
- Remove AI patterns (hyperconfident assertions, hedging, formulaic transitions)
- Add natural storytelling rhythm
- Maintain the friend-to-friend tone

### 4.2 Second Critique Pass
- Final consistency check
- Verify voice matching

---

## PHASE 5: FINAL WRITE

### 5.1 Final Draft
Incorporate all critique feedback. Produce final versions of:
- `lore/grabovoi-codes.md`
- Updated `lore/a1-navigator.md`
- Updated `lore/frequency-storms.md`
- 3 new episodes (S01E10, S02E10, S03E08x)
- Updated season episodes (S01E01, S01E03, S01E07, S02E00, S02E05, S02E08, S03E01, S03E06, S03E10, S03E11)

### 5.2 Verification
```bash
# Sync to website and verify build
./scripts/sync_to_website.sh --all
cd ~/Documents/code_repos/ephergent.com && npm run build
```

---

## CRITICAL FILES

| File | Action |
|------|--------|
| `episodes/season{1,2,3}/` | Add new episodes, update existing |
| `lore/grabovoi-codes.md` | Create new |
| `lore/barrys-field-notes-grabovoi.md` | Create new |
| `lore/a1-navigator.md` | Update |
| `lore/frequency-storms.md` | Update |
| `lore/the-silence-zones.md` | Update |
| `world/` | Directory rename from `phase_01_world/` |
| `characters/` | Directory rename from `phase_02_characters/` |
| `seasons/` | Directory rename from `phase_03_seasons/` |
| `CLAUDE.md` | Update all paths after directory rename |
| `scripts/sync_to_website.sh` | Update paths if needed |

---

## 12 LOCKED RULES COMPLIANCE

The integration MUST NOT violate:
1. Frequencies, not dimensions
2. Space vocabulary only
3. A1 IS the espresso machine (codes ARE frequency coordinates — A1 is the ship navigating them)
4. Coffee flavor in every A1 scene
5. Clive = knee-high robot, sphere head, fedora
6. Barry = alive in the Wellspring
7. Mochi never speaks
8. Builders are NOT villains
9. The Drift is entropy, not villain
10. The Wellspring is a state, not a place
11. 15MB per-game hard cap
12. Barry's field notes are methodical, precise, observational

**Grabovoi Code design rule:** Codes are a **navigation/coordinate mechanic**, not magic. They work within the existing frequency physics. The "spaces" in codes are quantum pauses — mechanical, not mystical.

---

## EXAMPLE: The Bureaucracy Frequency Vending Machine Scene

*Short 300-word absurd scene as proof-of-concept for tone:*

**Location:** A frequency made entirely of bureaucracy — filing cabinets stretch to infinity, stamps echo like gunshots, form 27B is required for everything.

**Setup:** Pixel's crew is stranded. They need a lift to the next frequency. A vending machine offers "Transportation Authorization Forms" for "Emotional Processing Tokens."

**Problem:** Pixel has no tokens.

**Attempt:** Pixel whispers the Grabovoi code for unexpected money: 5-2-0-7-4-1-8.

**Mistake:** She whispers it continuously without respecting the spaces: 5207418 instead of 520 7418.

**Result:** Money appears — but it's in the form of 2,847 Emotional Processing Tokens. The machine short-circuits. A bureaucratic auditor materializes. Clive, reading the situation in noir detective mode, tips his fedora and delivers: "The machine's gonna need therapy after that."

**Why this works:** It's absurd, it's comedic, it teaches the mechanic (spaces matter), and it doesn't violate any Locked Rules.

---

## AGENTS TO BE USED

| Phase | Agent(s) |
|-------|----------|
| World Build | `scifi-fantasy-writer` — create core lore |
| Write | `scifi-fantasy-writer` + `radio-play-producer` — draft episodes |
| Critique | `literary-critic-scifi-fantasy` — review for consistency |
| Humanize | `humanizer` — remove AI patterns |
| Final Critique | `literary-critic-scifi-fantasy` — final pass |

---

## WORKFLOW SUMMARY

```
PHASE 0: Directory Rename (phase_XX_ → clean names)
    ↓
PHASE 1: World Build (create core lore, update existing)
    ↓
PHASE 2: Season Distribution (map codes across 30 episodes)
    ↓
PHASE 3: Write (AI draft with scifi-fantasy-writer)
    ↓
PHASE 4: Critique (literary-critic-scifi-fantasy)
    ↓
PHASE 5: Humanize (humanizer agent)
    ↓
PHASE 6: Final Critique + Rewrite
    ↓
PHASE 7: Final Write + Verification
```

---

## MASTER TODO

| # | Task | Status |
|---|------|--------|
| 1 | Phase 0: Rename phase_XX_ directories to clean names | Pending |
| 2 | Update CLAUDE.md paths after rename | Pending |
| 3 | Update sync script paths after rename | Pending |
| 4 | Phase 1: Create `lore/grabovoi-codes.md` | Pending |
| 5 | Phase 1: Create `lore/barrys-field-notes-grabovoi.md` | Pending |
| 6 | Phase 1: Create `lore/the-silence-zones.md` | Pending |
| 7 | Phase 1: Update `lore/a1-navigator.md` | Pending |
| 8 | Phase 1: Update `lore/frequency-storms.md` | Pending |
| 9 | Phase 2: Map code distribution across all 30 episodes | Pending |
| 10 | Phase 3: Write new episodes (S01E10, S02E10, S03E08x) | Pending |
| 11 | Phase 3: Update existing episodes with code references | Pending |
| 12 | Phase 4: Critique pass | Pending |
| 13 | Phase 5: Humanize pass | Pending |
| 14 | Phase 6: Final rewrite | Pending |
| 15 | Phase 7: Final verification + sync + build | Pending |
