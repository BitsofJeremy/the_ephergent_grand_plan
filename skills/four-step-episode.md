---
name: four-step-episode
description: Use when writing a new episode for The Ephergent Signal. Produces a fully critiqued, rewritten, and humanized episode through four sequential agents: SciFi writer (draft), Literary critic (review), SciFi rewrite (fix), Humanizer (final pass).
author: Jeremy (BitsofJeremy)
license: MIT
tags: [creative, radio-play, sci-fi, ephergent, episode-writing]
related_skills: [the-ephergent]
---

# The Ephergent Signal — Four-Step Episode Writing

Produces a production-ready episode through four sequential agent passes.

## The Four Steps

### Step 1: SciFi Writer — Draft
Launch `scifi-fantasy-writer` agent with:
- Episode premise and tone
- Character voice requirements (from the-ephergent skill)
- Key plot beats
- Grabovoi mechanic if applicable
- Target word count (700-900 words)
- File path to write to

**Output:** First draft saved to `episodes/seasonXX/SXXEXX_title.md`

### Step 2: Literary Critic — Review
Launch `literary-critic-scifi-fantasy` agent.

**Review checklist:**
- [ ] Character voice consistency (Pixel first-person, Clive noir/no contractions, Arc British formal, Mochi silent)
- [ ] Grabovoi mechanic clarity if present
- [ ] Locked Rules compliance (frequencies/Space vocabulary/A1=espresso machine/Mochi silent/Clive=sphere head+fedora)
- [ ] Sci-fi craft quality
- [ ] Comedy landing / emotional arc / experimental structure

**Output:** Issues with file:line references

### Step 3: SciFi Rewrite — Fix
Apply all critic findings. Use Edit tool directly. Prioritize:
- CRITICAL voice violations (Clive contractions, Mochi speaking)
- Locked Rules breaches (frequencies not dimensions, Space not Sea)
- Frontmatter narrator field (`narrator: "third_person"`)
- Sci-fi craft issues that undermine the story

**Output:** Rewritten episode with all issues resolved

### Step 4: Humanizer — Polish
Launch `humanizer` agent.

**Patterns to remove:**
- "It is important to note that..."
- "The truth is..." / "The reality is..."
- "Fundamentally," "Essentially," "In essence," as openers
- "This means that..." → direct statement
- "The question remains..." / "The answer lies..."
- "As previously stated..." / "As noted above..."
- Hyper-confident assertions, over-explanation, hedging

**What to preserve:**
- Character voices (Pixel caffeinated, Clive noir, A1 formal, Barry methodical)
- Comedy punch
- The 12 Core Codes table in grabovoi-codes.md

**Output:** Final humanized episode

---

## Character Voice Quick Reference

| Character | Voice | Key rules |
|-----------|-------|-----------|
| Pixel | First-person narrator, conversational, caffeinated | N/A |
| A1 | British formal, protective, dry wit | Coffee flavor every scene: bitter=worried, thin=exhausted, rich=engaged |
| Clive | Noir detective, short declarative, no contractions | Sphere pulses click-click-CLICK, fedora tilt |
| Mochi | **Never speaks** | Warmth and color pulses only |
| Barry | Methodical field notes, Rule 12 | No drama |

---

## Locked Rules (from the-ephergent skill)

1. **Frequencies, not dimensions**
2. **The Space, not the Sea**
3. **A1 IS the espresso machine**
4. **Coffee flavor in every A1 scene**
5. **Clive = knee-high robot, sphere head, fedora**
6. **Barry Kowalski = alive in the Wellspring**
7. **Mochi never speaks**
8. **The Builders are NOT villains**
9. **The Drift is entropy, not villain**
10. **The Wellspring is a state, not a place**
11. **15MB per-game hard cap**
12. **Barry's notes are methodical, precise**
13. **Episodes are written in third person** (Signal reads in third person)

---

## Frontmatter Template

```yaml
---
title: "Episode Title"
author: "The Ephergent Collective"
date: "YYYY-MM-DD"
tags: ["season-X", "episode-X"]
narrator: "third_person"
---
```

## Coffee Chart Template

```markdown
## COFFEE CHART

| Scene | Beverage | Crew Present | Notes |
|-------|----------|--------------|-------|
| Arrival | Rich/complex | Pixel, A1, Clive | A1 is engaged. |
| Crisis | Bitter | Pixel, A1 | A1 is worried. |
| Resolution | Perfect/balanced | All | A1 is content. |
```
