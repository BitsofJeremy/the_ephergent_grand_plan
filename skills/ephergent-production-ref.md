---
name: ephergent-production-ref
description: Use when auditing Ephergent episodes for canon compliance, before audio generation, or when running the two-repo sync workflow.
author: Jeremy (BitsofJeremy)
license: MIT
tags: [ephergent, production, audio, sync, canon, quality]
related_skills: [the-ephergent, ephergent-site-builder]
---

# Ephergent Production Reference

Operational reference for sync workflow, pre-audio audits, and canon compliance checking.

## Pre-Audio Quality Gate Checklist

**Trigger: Before launching ANY audio generation pass (manual or cron)**

### Golden Rule
> **Never generate audio for episodes that are actively changing.** Story first, audio second.

### Pre-Audio Checklist

- [ ] **REFACTOR directory reviewed** — newer version in `REFACTOR/` supersedes `phase_04_episodes/`?
- [ ] **All 30 episodes exist and finalized** — no stub files (< 2KB)
- [ ] **Canon violations resolved** — run audit:
  ```bash
  grep -iE "stapler|dimension|plane|interdimensional" \
    ~/Documents/code_repos/the_ephergent_grand_plan/phase_04_episodes/season*/S*.md
  ```
- [ ] **Locked rules tables present** — S01 and S02 episodes have `## LOCKED RULES CHECK` tables
- [ ] **Sprecher API reachable** — `curl http://sprecher.nexus.home.test/api/health` returns `{"status":"ok"}`
- [ ] **No duplicate episode files** — only one file per episode slot
- [ ] **Character bibles synced** — Phase 02 characters match ephergent.com crew/

## Agent Timeout Math

For audio generation subagents:
- **30 episodes × ~30s Kokoro = ~15 minutes**
- **Subagent hard limit: 10 minutes**
- **Solution: Split into 3 agents, 10 episodes each, running in parallel**

## Sprecher LAN Connectivity

```bash
curl --max-time 10 http://sprecher.nexus.home.test/api/health
# Expected: {"status":"ok","engines":["kokoro","qwen","whisper"]}
```
If timeout: Sprecher is down. Do NOT proceed with audio generation.

## Stub File Signatures

| Stub type | Size | Fix |
|-----------|------|-----|
| Placeholder comment | < 500 bytes | Find real episode or write new |
| Empty YAML frontmatter | < 1KB | Fill with full character bible |
| Old amalgamation | 16KB, superseded | Delete old, keep new |

Detect:
```bash
find . -name "*.md" -size -2k -exec wc -c {} \; | sort -n
```

## Two-Repo Sync Reference

| Repo | Path | Role |
|------|------|------|
| `the_ephergent_grand_plan` | `phase_04_episodes/seasonNN/` | **Canonical source** |
| `the_ephergent_grand_plan` | `phase_05_lore/` | **Canonical source** |
| `the_ephergent_grand_plan` | `phase_02_characters/crew/` | **Canonical source** |
| `ephergent.com` | `src/content/transmissions/` | **Derived** |
| `ephergent.com` | `src/content/lore/` | **Derived** |
| `ephergent.com` | `src/content/crew/` | **Derived** |

⚠️ **NEVER edit transmissions/, lore/, or crew/ directly**

## The Sync Script

```bash
cd ~/Documents/code_repos/the_ephergent_grand_plan
./scripts/sync_to_website.sh --all        # episodes + lore + crew
./scripts/sync_to_website.sh --episodes   # episodes only
./scripts/sync_to_website.sh --lore       # lore only
./scripts/sync_to_website.sh --crew       # crew only
```

Script preserves website frontmatter by extracting YAML from website file, stripping any frontmatter from source, then combining: `[website frontmatter]\n[source body]`.

## The Commit Sequence

```bash
# 1. Commit in grand_plan and push
cd ~/Documents/code_repos/the_ephergent_grand_plan
git add phase_04_episodes/ phase_05_lore/ phase_02_characters/crew/
git commit -m "description" && git push origin main

# 2. Sync to website
./scripts/sync_to_website.sh --all

# 3. Build and deploy
cd ~/Documents/code_repos/ephergent.com && npm run build && npm run deploy

# 4. Commit website
cd ~/Documents/code_repos/ephergent.com
git add -A && git commit -m "sync: [episode/lore list]" && git push origin main
```

## Frontmatter Architecture

**Source files** (`phase_04_episodes/seasonNN/SNNEnn_*.md`): NO frontmatter, begin with `# Episode Title`

**Website files** (`src/content/transmissions/SNNEnn_*.md`): REQUIRE YAML frontmatter — `title`, `author`, `date`, `season`, `episode`, `tags`