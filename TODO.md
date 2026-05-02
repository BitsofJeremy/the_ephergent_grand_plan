# The Ephergent — Refactor TODO

> Status: **IN PROGRESS**
> Last updated: 2026-05-01

## Decision: Remove Paperclip
Paperclip is uninstalled. The `/api/agents` endpoint requires board-level auth that the CEO API key doesn't provide — agents cannot be created programmatically. Going forward: `delegate_task` for all subagent work.

**Uninstall command:** `npm uninstall -g @paperclip-ui/cli`

---

## Creative Brief

**What it is:** A multimedia sci-fi universe — browser games, radio transmissions, comics, a YouTube channel, an ebook — built around a crew traversing the Interdimensional Space on an ancient quantum navigator disguised as an espresso machine.

**What it isn't:** Preachy. Cynical. Corporate. Naval.

**Tone:** Firefly × One Piece × Welcome to Night Vale × Douglas Adams × Dirk Gently. Deadpan absurdity + genuine wonder + stubborn hope.

**Canon:** `REFACTOR/ephergent_canon_v2.md` — the single source of truth. All content must pass the 12 Locked Rules check before publishing.

---

## Refactor Phase 1 ✅ COMPLETE

| File | Status | Agent |
|-------|--------|-------|
| `REFACTOR/ephergent_canon_v2.md` | ✅ Done | lore-keeper |
| `REFACTOR/S01E01_the_frequency.md` | ✅ Done | episode-writer |
| `REFACTOR/absurdity_guide.md` | ✅ Done | absurdity-architect |
| `REFACTOR/season_architecture_v2.md` | ⚠️ Interrupted | plot-architect |

---

## Refactor Phase 2 — IN PROGRESS

### Season Architecture
- [ ] Fix `season_architecture_v2.md` (read Canon V2 + Absurdity Guide + existing phase_03_seasons)
- [ ] Design 3 seasons × 10 episodes with absurd sci-fi Douglas Adams energy
- [ ] Identify which existing episodes survive, which need amendments

### Character Bibles
- [ ] Rewrite all character files (phase_02_characters/) to match Canon V2
  - Clive: robot NOT stapler
  - Pixel Paradox: full backstory update
  - A1: coffee flavor system
  - Zephyr & Aether: split story
  - Luminara, Om Kai, Klaus, Nano, Meatball

### World Lore
- [ ] Update phase_01_world/ files to match Canon V2
- [ ] Remove all nautical metaphors (Space not Sea)
- [ ] Remove Corporate Corp / The Board references
- [ ] Add Time War texture section

### Episode Scripts
- [ ] Rewrite S01E01 using Canon V2 rules
- [ ] Amendment log for existing 37 episodes (classify: keep / amend / rewrite)
- [ ] Write new episodes per season_architecture_v2.md

### Games
- [ ] Tune the Dial: procedural audio game
- [ ] Static Run: Phaser.js, 15MB cap
- [ ] Meatball's Big Walk: platformer
- [ ] Builder Station: puzzle adventure

### Site (ephergent.com)
- [ ] Astro 5 + Tailwind 3 build
- [ ] Lore Atlas with spoiler tiers (🟢🟡🔴)
- [ ] Transmission archive

---

## Delegation Log

| Date | Task | Agent | Status |
|------|------|-------|--------|
| 2026-05-01 | Canon V2 | lore-keeper | ✅ Done |
| 2026-05-01 | S01E01 pilot script | episode-writer | ✅ Done |
| 2026-05-01 | Absurdity guide | absurdity-architect | ✅ Done |
| 2026-05-01 | Season architecture | plot-architect | ⚠️ Interrupted |
| 2026-05-01 | Paperclip uninstall | Rodan | 🔄 In progress |

---

## How to Run

Every creative task goes through `delegate_task`:

```
delegate_task(
  goal="<specific task>",
  context="<Canon V2 path, relevant files, constraints>",
  role="leaf",
  toolsets=["terminal", "file"]
)
```

All output goes into `REFACTOR/` until approved, then promoted to the appropriate phase folder.

---

## Locked Rules (verify before any content ships)

1. Frequencies, not dimensions
2. Space, not Sea — no nautical metaphors
3. A1 IS the espresso machine
4. A1's coffee flavor in every scene
5. Clive is a knee-high robot — glowing sphere head, fedora — NOT a stapler
6. Barry Kowalski is ALIVE in the Wellspring — not a rescue mission
7. Mochi doesn't speak — no dialogue, no complex emotions
8. The Builders are NOT villains — The Dimming was a loving choice
9. The Drift is entropy, not evil — cannot be stopped
10. The Wellspring is a state, not a place
11. 15MB per-game hard cap
12. Barry's notes are methodical — never dramatic

---

## Reference Files

| File | Purpose |
|------|---------|
| `REFACTOR/ephergent_canon_v2.md` | Single source of truth |
| `REFACTOR/absurdity_guide.md` | Douglas Adams/Dirk Gently style guide |
| `REFACTOR/S01E01_the_frequency.md` | Pilot script (example of voice) |
| `phase_03_seasons/` | Old season architecture (amend, don't replace) |
| `source_archive/` | 37 existing episode scripts (need amendments) |
| `skills/ephergent-canon/SKILL.md` | Locked rules (source of truth) |
