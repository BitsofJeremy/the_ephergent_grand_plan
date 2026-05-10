# The Ephergent Grand Plan

**Canonical source for The Ephergent Signal** — a transmedia sci-fi universe about a crew broadcasting truth into a universe trending toward silence.

> **Company**: Before Greatness LLC
> **Product**: Browser-playable games + transmissions + comics, all on ephergent.com
> **Status**: Active development — Season 3 complete, Grabovoi Codes integrated

---

## The 13 Locked Rules

These govern ALL content produced for The Ephergent:

| # | Rule | Never |
|---|------|-------|
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
| 13 | Episodes are written in third person | Signal reads all episodes in third person |

---

## What's New

### Directory Structure (Renamed from phase_XX_)
Directories use clean names now — no more `phase_04_episodes/`, `phase_05_lore/` prefix:
- `episodes/` — canonical episode scripts (31 episodes across 3 seasons)
- `lore/` — canonical lore entries
- `characters/` — canonical character bibles
- `world/` — frequency system and universe bible
- `plans/` — integration plans and episode mappings
- `skills/` — production skills including `four-step-episode.md`

### Grabovoi Codes Integrated
The universe's original firmware — pre-Builder numerological sequences that act as localized frequency overrides. Key additions:

**New Lore:**
- `lore/grabovoi-codes.md` — 12 core codes, mechanics, dangers
- `lore/barrys-field-notes-grabovoi.md` — Barry's methodical observations
- `lore/the-silence-zones.md` — what happens when codes fail
- Updated `lore/a1-navigator.md` — A1's code sensitivity
- Updated `lore/frequency-storms.md` — Code Storms as 4th storm type

**New Episodes:**
- `S01E10_bureaucracy_frequency.md` — CLX cryptocurrency + Grabovoi tutorial
- `S02E10_the_frequency_and_the_future.md` — Pixel's first deliberate code use
- `S03E08y_the_machine_that_grew.md` — experimental, told through code sequences

**Plans:**
- `plans/grabovoi-code-integration.md` — full integration plan
- `plans/grabovoi-episode-mapping.md` — code distribution across 30 episodes

---

## The Synthesis Rules
- Dimensions are **frequencies** on a cosmic dial
- **Space**, not Sea. Sci-fi vocabulary only
- **A1** = espresso machine = ship. Sacred
- **Clive** = knee-high robot, sphere head, fedora. Noir voice
- **Mochi** = dome-shaped, never speaks, communicates via warmth and color
- **The Builders** = mystery civilization, NOT villains
- **The Drift** = entropy, not a villain
- **No corporate villains**. Antagonists are philosophical, environmental, or human-scaled
- **Episodes in third person** — Signal narrates all episodes

---

## Key Paths

| Path | Purpose |
|------|---------|
| `episodes/season{1,2,3}/` | Canonical episode scripts |
| `lore/` | Canonical lore entries |
| `characters/crew/` | Canonical character bibles |
| `world/` | Frequency system and universe bible |
| `plans/` | Integration plans |
| `skills/` | Production skills |
| `REFACTOR/` | Authoritative planning documents |

---

## Episode Structure

- **Season 1**: 10 episodes — Discovery arc
- **Season 2**: 10 episodes — Integration arc
- **Season 3**: 11 episodes — Mastery arc
- **Total**: 31 canonical episodes

---

## Skills

Production skills in `skills/`:
- `the-ephergent.md` — core production skill with 13 Locked Rules
- `four-step-episode.md` — four-step episode writing process (SciFi writer → Literary critic → Rewrite → Humanizer)

Also deployed to `~/.claude/skills/` for home directory access.

---

## Sync Workflow

```bash
# 1. Write/edit in grand_plan (episodes/, lore/, characters/crew/)

# 2. Sync to website (preserves frontmatter — DO NOT use cp):
./scripts/sync_to_website.sh --all

# 3. Build and deploy:
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 4. Commit to grand_plan and push:
git add -A && git commit -m "description" && git push origin main
```

⚠️ **NEVER `cp` files directly to ephergent.com** — the sync script preserves Astro's required YAML frontmatter.

---

*Broadcast truth. Pay attention. The Signal must not die.*
