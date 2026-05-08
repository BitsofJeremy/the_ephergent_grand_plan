# Phase 1 Revisions: Format Conversion + Pixel Voice

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan step-by-step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert 3 episodes from radio play/screenplay format to prose narrative with embedded dialogue, and calibrate Pixel's voice by removing verbal fillers across the HIGH priority episodes.

**Architecture:** Prose narrative (first-person Pixel, past tense) with embedded dialogue. COFFEE CHARTS retained as formatted text blocks (italics, indented). Clive's noir cadence needs prose to land — screenplay format diminishes his voice.

**Tech Stack:** Markdown files, creative writing tools.

---

## File Structure

```
phase_04_episodes/season01/S01E01_the_frequency.md    — CONVERT screenplay → prose
phase_04_episodes/season01/S01E05_the_clockwork_unraveling.md — CONVERT radio play → prose
phase_04_episodes/season03/S03E01_where_the_frequencies_have_no_name.md — CONVERT radio play → prose
```

---

## Conversion Rules (All Three Episodes)

### Prose Format Standard

- **Voice:** First-person Pixel, past tense
- **Dialogue:** Quoted with speaker tags or attribution, or embedded without tags
- **Scene direction:** Prose paragraphs, not stage brackets
- **COFFEE CHARTS:** Keep as formatted blocks (italics, indented, distinct typography)
- **Clive's voice:** Noir cadence in prose — "I do not believe in wanting" / "The data is sufficient" — not sparse screenplay lines
- **A1's voice:** British formal, no contractions, coffee flavor descriptions in every A1 scene
- **Mochi:** Actions only, no dialogue ever

### Pixel Voice Rules (Apply to All Three)

**REMOVE all instances of:**
- "okay, so" — cut entirely
- "here's the thing" — cut entirely
- "so here's the thing" — cut entirely
- "let me tell you" — cut entirely
- "you know what I mean" — cut entirely
- "right?" (tag questions) — cut unless Pixel is actually checking understanding

**KEEP:**
- Sharp observations, not announcements
- Caffeinated rhythm — short declarative for impact, longer for texture
- Emotional honesty without melodrama
- Interiority and reflection

---

## Task 1: S01E01 — "The Frequency"

**File:** `phase_04_episodes/season01/S01E01_the_frequency.md`

### Conversion Notes

The current S01E01 is in screenplay format. It needs to become prose narrative with embedded dialogue. Key things to preserve:

1. **Pixel's choice to grab A1** — this is the real opening moment, not the world mechanics. Lead with it.
2. **A1 reveal** — the espresso machine consciousness reveal should be gradual and earned
3. **Clive's "archival unit" moment** — already fixed from "stapler" but needs prose treatment
4. **The final broadcast** ("This is the Ephergent") — should land with appropriate weight
5. **All "Interdimensional Space" → "Space"** — already done, verify

### Pixel Voice Focus

The S01E01 opening should establish Pixel as someone who notices things and tells stories. The current screenplay format front-loads exposition. The prose version should:
- Open with Pixel in the moment — not explaining the world, experiencing it
- Let her voice emerge through sharp observation rather than announcements
- Build the DRM collapse as backdrop to her choice to grab A1 and run

### COFFEE CHART

Keep the COFFEE CHART if present. Integrate as formatted block.

---

## Task 2: S01E05 — "The Clockwork Unraveling"

**File:** `phase_04_episodes/season01/S01E05_the_clockwork_unraveling.md`

### Conversion Notes

Current format is radio play. Clive's noir voice is being wasted in screenplay format. Convert to prose with embedded dialogue.

**Key content to preserve:**
1. **Om Kai scenes** — his philosophy about the gear "choosing" to come back is precisely right for the series' themes
2. **Professor Chronos introduction** — needs careful handling in prose
3. **The temporal drift crisis** — atmospheric, needs strong prose description
4. **Clive's voice in prose** — "I do not believe in wanting" cadence needs room to breathe

### Clive Voice Focus

In screenplay format, Clive gets sparse dialogue lines. In prose, Pixel can narrate his silences, his pauses, his glow patterns. This is where Clive's voice shines. The S01E03 approach (Pixel sitting with Clive's stillness and reading his silences) is the model.

---

## Task 3: S03E01 — "Where the Frequencies Have No Name"

**File:** `phase_04_episodes/season03/S03E01_where_the_frequencies_have_no_name.md`

### Conversion Notes

Current format is radio play with integrated COFFEE CHARTS. This episode is already described as "strongest S03 premiere" so the content is good — it just needs the format conversion.

**Key content to preserve:**
1. **The unnamed frequencies** — philosophically rich, needs strong prose to land
2. **Pixel naming "Ephergent"** — thematic peak, needs room to breathe
3. **A1 coffee refusal** (first time he hasn't wanted to make coffee) — handled with restraint, show his overwhelm
4. **"Seven hours later" time skip** — structurally elegant, keep it
5. **COFFEE CHART** — keep as formatted block, the integration works

### Pixel Voice Focus

S03E01 is already strong but Pixel voice slips in places. Remove verbal fillers during conversion.

---

## Task 4: Pixel Voice Calibration (All HIGH Priority)

Apply to: S01E01, S01E05, S03E01 (during conversion), plus S02E01 and S02E09

### S02E01 — "First Station"

Already has the right format (Pixel-narrated prose) but Pixel voice needs refinement:
- Remove "okay, so" from opening
- Remove "here's the thing" from opening
- Keep "I need you to understand" register
- The Station 3-Resonant discovery is genuinely wondrous — strengthen around that

### S02E09 — "Clive's Coordinates"

Format is already prose. Fix the confrontation structure per REVISION_PLAN.md Section 5:
- Restructure so Pixel's anger shifts from "you hid this from me" to "you thought I couldn't handle it"
- Clive must have opportunity to explain before anger peaks
- The conflict should be about Clive's protective instinct, not miscommunication

---

## Step-by-Step Execution

### Phase 1A: S01E01 Conversion

- [ ] **Step 1: Read current S01E01**

Read the full episode to understand what needs converting.

- [ ] **Step 2: Write new prose version of S01E01 opening**

Convert the screenplay opening to first-person Pixel prose. Lead with Pixel's choice to grab A1, not world mechanics. Remove verbal fillers.

- [ ] **Step 3: Convert S01E01 middle sections**

Continue through the episode — DRM collapse, lifeboat escape, A1 reveal. Each section: read screenplay format, write prose version with embedded dialogue.

- [ ] **Step 4: Convert S01E01 ending sections**

A1 awakening, ship integration, final broadcast. Preserve the emotional weight.

- [ ] **Step 5: Verify COFFEE CHART integration**

Check if COFFEE CHART exists in this episode. If so, integrate as formatted block.

- [ ] **Step 6: Verify locked rules compliance**

Check for: frequencies not dimensions, space vocabulary, Clive not stapler, A1 coffee flavor, Mochi no dialogue.

- [ ] **Step 7: Commit S01E01**

```bash
git add phase_04_episodes/season01/S01E01_the_frequency.md
git commit -m "refactor(S01E01): convert screenplay to prose, calibrate Pixel voice"
```

### Phase 1B: S01E05 Conversion

- [ ] **Step 1: Read current S01E05**

- [ ] **Step 2: Write new prose version opening**

Convert radio play opening to prose. Establish the clockwork world.

- [ ] **Step 3: Convert Om Kai scenes**

His philosophy about the gear choosing to come back — this is the episode's best material. Give it room in prose.

- [ ] **Step 4: Convert Clive scenes**

Clive's noir voice in prose — Pixel reads his silences, his glow patterns, his pauses.

- [ ] **Step 5: Verify locked rules compliance**

- [ ] **Step 6: Commit S01E05**

```bash
git add phase_04_episodes/season01/S01E05_the_clockwork_unraveling.md
git commit -m "refactor(S01E05): convert radio play to prose, Clive voice in prose"
```

### Phase 1C: S03E01 Conversion

- [ ] **Step 1: Read current S03E01**

- [ ] **Step 2: Write new prose version**

Radio play to prose. Preserve the philosophical richness.

- [ ] **Step 3: Calibrate Pixel voice**

Remove verbal fillers during conversion.

- [ ] **Step 4: Verify COFFEE CHART integration**

Keep the formatted block.

- [ ] **Step 5: Verify locked rules compliance**

- [ ] **Step 6: Commit S03E01**

```bash
git add phase_04_episodes/season03/S03E01_where_the_frequencies_have_no_name.md
git commit -m "refactor(S03E01): convert radio play to prose, calibrate Pixel voice"
```

### Phase 1D: S02E01 Pixel Voice

- [ ] **Step 1: Read current S02E01**

- [ ] **Step 2: Rewrite opening**

Remove "okay, so," "here's the thing." Keep "I need you to understand" register.

- [ ] **Step 3: Scan for remaining fillers**

Find and remove all instances.

- [ ] **Step 4: Verify locked rules compliance**

- [ ] **Step 5: Commit**

```bash
git add phase_04_episodes/season02/S02E01_first_station.md
git commit -m "refactor(S02E01): calibrate Pixel voice, remove verbal fillers"
```

### Phase 1E: S02E09 Confrontation Fix

- [ ] **Step 1: Read current S02E09**

- [ ] **Step 2: Restructure confrontation**

Per REVISION_PLAN.md Section 5: Pixel's anger shifts from "you hid this from me" to "you thought I couldn't handle it." Clive has opportunity to explain before anger peaks.

- [ ] **Step 3: Verify Clive voice in prose**

Clive's noir cadence should be undiminished.

- [ ] **Step 4: Verify locked rules compliance**

- [ ] **Step 5: Commit**

```bash
git add phase_04_episodes/season02/S02E09_clives_coordinates.md
git commit -m "refactor(S02E09): restructure confrontation, Clive protective instinct"
```

---

## Verification After Each Task

After each commit:
1. Read the episode back
2. Check Pixel voice is consistent
3. Check Clive voice is undiminished (no sparse screenplay lines)
4. Check COFFEE CHARTS integrated correctly
5. Check locked rules compliance

---

## Phase 1 Complete

After all five tasks committed:
1. Push to remote
2. Report completion
3. Await critic review before Phase 2

---

*Plan generated: 2026-05-07*
*From: REVISION_PLAN.md Phase 1*