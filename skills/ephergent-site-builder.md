---
name: ephergent-site-builder
description: Use when building or deploying ephergent.com — Astro site, sync workflow, two-repo architecture, or audio pipeline.
author: Jeremy (BitsofJeremy)
license: MIT
tags: [ephergent, astro, website, devops]
related_skills: [the-ephergent]
---

# ephergent-site-builder

Build and maintain ephergent.com — the Ephergent's home at `~/Documents/code_repos/ephergent.com/`

**Stack:** Astro 5 + Tailwind 3 + TypeScript. Pure static site export.

## Two-Repo Architecture (Option B — Canonical: grand_plan)

⚠️ **This repo is the DEPLOYMENT target, not the source.** All creative work happens in `~/Documents/code_repos/the_ephergent_grand_plan/`.

**Never edit `src/content/transmissions/`, `src/content/lore/`, or `src/content/crew/` directly** — these are derived from grand_plan and will be overwritten.

## Sync Workflow (ALWAYS use sync_to_website.sh)

```bash
# 1. Edit in grand_plan:
cd ~/Documents/code_repos/the_ephergent_grand_plan

# 2. Sync to website (preserves frontmatter):
./scripts/sync_to_website.sh --all

# 3. Build and deploy:
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 4. Commit and push grand_plan:
cd ~/Documents/code_repos/the_ephergent_grand_plan
git add -A && git commit -m "description" && git push origin main
```

⚠️ **NEVER `cp` files directly** — naive copies wipe YAML frontmatter and break the Astro build.

## Content Collections

| Collection | Count | Canonical Source |
|------------|-------|------------------|
| `transmissions/` | 30 | `grand_plan/phase_04_episodes/seasonNN/` |
| `lore/` | 27 | `grand_plan/phase_05_lore/` |
| `crew/` | 12 | `grand_plan/phase_02_characters/crew/` |
| `games/` | 6 | (games only here) |

## Frontmatter (Critical)

Website files REQUIRE YAML frontmatter:
```yaml
---
title: "Episode Title"
author: "The Ephergent Station"
date: "2024-01-01"
season: "01"
episode: "01"
---
```

The sync script preserves this automatically.

## Key Paths

| Path | Purpose |
|------|---------|
| `src/pages/` | Astro page routes |
| `src/content/` | Content collections (derived) |
| `public/images/characters/` | Character portraits |
| `public/audio/` | Episode audio files |
| `src/components/` | Reusable Astro components |
| `public/terminal/` | Station terminal JS/CSS |

## Site Pages

- `/` — Landing: space station boot, crew teaser, latest transmission
- `/terminal/` — Standalone JS terminal
- `/transmissions/` — Episode archive
- `/crew/` — Crew roster
- `/atlas/` — Lore atlas with spoiler tiers
- `/games/` — Games

## Audio Pipeline

Audio is generated via Sprecher Kokoro TTS (`bf_emma` single narrator). TTS reads from `transmissions/` — always sync before generating audio.

The old MiniMax T2A voice clone approach is deprecated.

## 12 Locked Rules Compliance

When editing content, ensure all episodes follow the 12 Locked Rules from `the-ephergent` skill.