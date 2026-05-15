# The Ephergent Grand Plan

**Canonical source for The Ephergent Signal** — a transmedia sci-fi universe about a crew broadcasting truth into a universe trending toward silence.

> **Company**: Before Greatness LLC
> **Product**: Browser-playable games + transmissions + comics, all on ephergent.com
> **Status**: Active development — Season 3 complete, Grabovoi Codes integrated

---

## Quick Start

1. **Write episodes** → `/four-step-episode` skill
2. **Generate audio** → 4-stage pipeline in `scripts/`
3. **Deploy content** → `./scripts/sync_to_website.sh --all`
4. **Build website** → `cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy`

**For full guidance**, see `CLAUDE.md` — the authoritative reference for this repo.

---

## Two-Repo Architecture

| Repo | Role |
|------|------|
| `the_ephergent_grand_plan` | **Canonical source** — all episodes, lore, characters live here |
| `ephergent.com` | **Derived deployment** — synced from this repo, never edited directly |

**Sync workflow** (ALWAYS use this, NEVER `cp`):

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

## Episode Structure

- **Season 1**: 10 episodes — Discovery arc
- **Season 2**: 10 episodes — Integration arc
- **Season 3**: 11 episodes — Mastery arc
- **Total**: 31 canonical episodes

File naming: `SXXEXX_title.md`. Episodes written in **third person**.

---

## Audio Pipeline

4-stage pipeline converts episode markdown → clean TTS text → MP3 audio.

| Stage | Script | Output |
|-------|--------|--------|
| 1. Clean body | `preprocess_episodes.py` | `tts_text/seasonNN/SXXEXX.tts.txt` |
| 2. Extract summary | `generate_summaries.py` | `excerpts/seasonNN/SXXEXX.txt` |
| 3. Assemble final | `assemble_tts_text.py` | `tts_text/seasonNN/SXXEXX.tts.txt` |
| 4. Generate audio | `generate_audio.py` | `audio/seasonNN/SXXEXX.mp3` |

See `SKILL.md` for full pipeline documentation.

---

## Key Paths

| Path | Purpose |
|------|---------|
| `episodes/season{1,2,3}/` | Canonical episode scripts (31 episodes) |
| `lore/` | Canonical lore entries |
| `characters/crew/` | Canonical character bibles |
| `plans/` | Integration plans and episode mappings |
| `skills/` | Production skills |
| `REFACTOR/` | Authoritative planning documents |
| `scripts/` | Audio pipeline + sync scripts |

---

## Skills

Production skills in `skills/`:
- `the-ephergent.md` — core production skill with 13 Locked Rules
- `four-step-episode.md` — four-step episode writing process

Also deployed to `~/.claude/skills/` for home directory access.

---

*Broadcast truth. Pay attention. The Signal must not die.*