# The Ephergent Grand Plan — TODO

> Status: **ACTIVE — Post-Cleanup 2026-05-06**
> Last updated: 2026-05-06

## Directory Structure (Post-Cleanup)

```
the_ephergent_grand_plan/
├── REFACTOR/               ✅ CANONICAL — 9 planning docs
├── phase_02_characters/    ✅ ACTIVE — 11 character bibles
├── phase_04_episodes/      ✅ ACTIVE — 30 episode scripts (S01-S03)
│   ├── season01/           (S01E01–S01E10)
│   ├── season02/           (S02E01–S02E10)
│   └── season03/           (S03E01–S03E10 + S03E08x)
├── phase_05_games/        ✅ ACTIVE — 6 game design bibles
├── phase_06_transmissions/ ✅ ACTIVE — format specs
├── phase_07_site/          ✅ ACTIVE — Astro scaffold (reference)
└── CLAUDE.md               ✅ LLM guidance
```

---

## What's Done (2026-05-06)

| Item | Status |
|------|--------|
| Time War integration | ✅ 3 major + 4 minor amendments across S01-S03 |
| Clive glow fix | ✅ blue-white (was pink/magenta) |
| REFACTOR documents | ✅ 9 files, all canonical |
| Phase 0 fixes | ✅ The The Space, A1 refs, Meatball |
| CLAUDE.md | ✅ Written for both repos |
| Website content | ✅ 11 crew, 6 games, 29 lore, 24 images |

---

## Active Content Inventory

| Category | Count | Location |
|----------|-------|----------|
| Episodes | 30 (S01-S03) | `phase_04_episodes/season{1,2,3}/` |
| Characters | 11 | `phase_02_characters/` |
| Games | 6 design bibles | `phase_05_games/` |
| Planning docs | 9 | `REFACTOR/` |

---

## Pending Work — Priority Order

### 🔴 HIGH PRIORITY

**1. Episode Audio Pipeline** (biggest gap)
- Only S01E01 has audio — 29 of 30 episodes missing
- This blocks the listen-along experience
- Need: TTS + sound design + music pipeline
- Start with S01E02 as test case

**2. Complete the Lore Atlas**
- Current: 29 entries
- Target: ~50+ entries across 7 sections
- Highest-traffic pages: frequencies, ship, builders
- Each entry needs: title, type, summary paragraph, links

**3. Game Implementation**
- Design docs exist for all 6 (`phase_05_games/`)
- Live on website: only `tune-the-dial`
- In-dev: `meatballs-big-walk`
- Needed: Builder Station, The Wellspring, Static Run, The Laughing Funeral

### 🟡 MEDIUM PRIORITY

**4. Character Image Audit**
- `clive_stapler_informant.png` may still show pink/magenta glow
- Generator used old prompts before fix (2026-05-06)
- Check and regenerate if needed

**5. REFACTOR S01E01 pilot adoption**
- `REFACTOR/S01E01_the_frequency.md` supersedes `phase_04_episodes/season01/S01E01_the_day_the_dial_broke.md`
- Decide: adopt as active S01E01 or keep both

**6. Lore content depth**
- Most 29 lore entries are stubs
- Expand summaries using episode scripts
- Add links to relevant episodes

### 🟢 LOW PRIORITY

**7. S03E08x integration** — `the_dimming_hour.md` exists, not in episode flow
**8. EPUB rebuild** — `the_ephergent.epub` regenerable via `generate_epub.py`
**9. Image production** — `phase_08_image_production/` planning only, no assets yet
**10. Comic pipeline** — `the_ephergent_signal_lore/` not yet connected

---

## Reference Files

## Character Specs (Canonical — Don't Contradict)

| Character | Key Spec |
|-----------|----------|
| **Clive** | Sphere head, blue-white glow, fedora, NOT stapler |
| **Pixel** | Red hair (not aqua), captain, narrator voice |
| **A1** | Espresso machine IS the ship, British formal |
| **Mochi** | Dome artifact, color comms only, NO speech |
| **Barry** | Field notes, thermos, alive in Wellspring |

---

## Time War (Integrated — Don't Contradict)

| Beat | Concept | Episodes |
|------|---------|----------|
| TW-1 | Loop = human automation | S01E02, S01E05, S03E04 |
| TW-2 | Consciousness breaks loops | S03E04, S03E05 |
| TW-3 | Future reaches backward | S02E08, S02E10, S03E03 |
| TW-4 | Technocapital backward | S02E04, S02E06 |
| TW-5 | Broadcasting as defense | S02E01, S02E02, S03E09 |

---

## Locked Rules (Verify Before Shipping)

1. Frequencies, not dimensions
2. Space, not Sea — no nautical metaphors
3. A1 IS the espresso machine
4. Coffee flavor in every A1 scene
5. Clive = sphere head + fedora, NOT stapler
6. Barry alive in Wellspring (state, not place)
7. Mochi never speaks
8. Builders NOT villains — Dimming was a choice
9. Drift = entropy, not villain
10. Wellspring = state, not place
11. 15MB per-game hard cap
12. Barry's notes = methodical, never dramatic

---

## How to Work

1. **Read CLAUDE.md** — canonical paths, don't touch REFACTOR/ without approval
2. **Check episode_map.md** — before modifying any episode
3. **Verify Locked Rules** — before committing any content
4. **Sync website** — if content changes in grand plan, update `my_websites/ephergent.com/` too
5. **Commit clearly** — describe what changed and why

---

## Reference Files

| File | Purpose |
|------|---------|
| `REFACTOR/ephergent_canon_v2.md` | Single source of truth |
| `REFACTOR/absurdity_guide.md` | Tone/style guide |
| `REFACTOR/episode_map.md` | Episode coverage map |
| `CLAUDE.md` | LLM path guidance |