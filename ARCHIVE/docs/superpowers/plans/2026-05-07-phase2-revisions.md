# Phase 2 Revision Plan — The Ephergent Signal

**Date:** 2026-05-07
**Status:** Draft for Review
**Based on:** Literary critic feedback (Phase 1 findings)

---

## Executive Summary

Phase 1 confirmed the core narrative succeeds: voice lands, emotional stakes register, and the "attention is creation" through-line is coherent. Phase 2 addresses five required fixes: format standardization, S01E07 consolidation verification, Aether signal/Zephyr development, frequency storm variation, and Builder specificity.

---

## Task 1: Format Conversion (Screenplay to Prose)

### Objective
Convert all remaining screenplay-format episodes to first-person prose with Pixel as narrator. S02E01 serves as the canonical style reference.

### Style Reference: S02E01_first_station.md
Key characteristics to replicate:
- Opening with "I need you to understand" framing
- First-person Pixel narrator ("I", "we")
- Conversational, warm, wry observational tone
- Prose paragraphs, not dialogue blocks
- Coffee chart embedded as narrative table
- LOCKED RULES CHECK at end
- "Signal continues." closing signature

### Files Requiring Conversion

| File | Season | Priority | Notes |
|------|--------|----------|-------|
| `season01/S01E01_the_frequency.md` | S01 | HIGH | Pilot episode. Establishes Pixel/Clive/A1. 816 lines. |
| `season01/S01E05_the_clockwork_unraveling.md` | S01 | HIGH | Cogsworth/Professor Chronos arc. 576 lines. |
| `season02/S02E09_clives_coordinates.md` | S02 | HIGH | Best character work per critics. 290 lines. |
| `season03/S03E01_where_the_frequencies_have_no_name.md` | S03 | HIGH | Pilot S03. "Where no name" concept. 519 lines. |

### Conversion Approach
Each episode converts from screenplay format to prose by:
1. Replacing character dialogue blocks with narrative action + quoted speech in prose
2. Adding Pixel's internal monologue/war department
3. Maintaining all story beats, coffee references, and locked rules checks
4. Preserving coffee chart data as embedded narrative tables
5. Adding "I need you to understand" opening framing where absent
6. Closing with "Signal continues." signature

### Estimated Effort
- S01E01: 2-3 hours (most complex, establishes everything)
- S01E05: 1.5-2 hours (scene-heavy, om kai dialogue)
- S02E09: 1.5 hours (dialogue-heavy but straightforward conversion)
- S03E01: 1.5-2 hours (philosophical, careful tone matching)

---

## Task 2: S01E07 Consolidation Verification

### Objective
Verify that `season01/S01E07_the_song_at_the_edge_of_everything.md` contains both originally separate storylines (first day aboard + The Edge content).

### Current Status: VERIFIED
The existing file at `season01/S01E07_the_song_at_the_edge_of_everything.md` contains:
- Act One: "The Edge" — lifeboat failing at Edge of reality, A1 episodes, Zephyr's phase-shifter sacrifice decision
- Act Two: "The Song Reaches Backward" — retrocausality mechanics, the crossing
- Act Three: "The First Day Aboard" — crew settling onto The Ephergent ship, Clive's memory in engine room conduit, Barry's notebook found
- Coda: First broadcast from The Ephergent

**Conclusion:** File is already properly amalgamated. No action required.

### Edge Case to Note
If future editors notice the "first day aboard" content feels incomplete compared to the "first day aboard" content that would have been in S01E08, the resolution is: the S01E07 amalgamated file represents the full canonical experience as intended in the episode map. No further consolidation needed.

---

## Task 3: Zephyr/Aether Signal Development

### Objective
Develop the Aether signal storyline with more presence. Give Zephyr a clearer character voice beyond "running diagnostics."

### Current State
Zephyr appears in S02E09 as the communications crew member who "didn't speak since they left the Station" and who "followed a signal too far and never came back" (his brother). His Aether-specific storyline is mentioned but underdeveloped.

### Proposed Development Areas

#### 3A. Zephyr Voice Clarification
Establish consistent Zephyr speech patterns:
- Starts mid-thought (habit from fragmented consciousness)
- Technical precision mixed with emotional indirectness
- References to "my brother" or "the signal he followed" should appear in at least 2 S03 episodes
- The "glitch" in his name is literal — his consciousness was shattered and rebuilt

#### 3B. Aether Signal Storyline Integration
The Aether signal is established in S02E09 as leading toward the Wellspring. Phase 2 should:
1. Ensure S03 has at least 2 episodes where Aether signal is a central plot element
2. Connect Aether signal to Zephyr's brother subplot
3. Use Aether as the mechanism for explaining what lies beyond the named frequencies

#### 3C. Frequency Storm Variation
**Definition for this world:** A frequency storm is not weather. It is a state where multiple frequencies attempt to occupy the same coordinates simultaneously, creating interference patterns that can shatter unprepared consciousnesses. The original frequency storm (4,000 years ago) scattered A1 across the Space and separated him from his ship.

**Variation types:**
- *Scatter storms*: Fragment consciousness (what happened to Zephyr's brother)
- *Lock storms*: Freeze frequencies in place (what happened to the Stations)
- *Synthesis storms*: Rare, dangerous, create new frequency combinations (the Wellspring may be a synthesis storm result)

This definition should be codified in a lore entry and referenced in at least one episode.

---

## Task 4: Builder Specificity

### Objective
Add one vivid lost world detail for Clive's Station 7-Ascending backstory. Not generic "Builder archive fell."

### Current State
Clive's backstory mentions Station 7-Ascending, where he was manufactured and where Mochi was calibrated. The Station is described as "a facility that no longer exists" but no vivid detail is given.

### Proposed Detail
Station 7-Ascending was built on a moon that orbited a frequency junction — a place where seven different frequencies intersected at a single point. The Builders built their calibration facility there because the resonance allowed them to test Keeper crystals against all seven frequency signatures simultaneously.

**Vivid lost world detail:** The calibration chamber was a sphere of pure silence. Seven frequency feeds entered from seven directions, and in the center, where they cancelled each other out completely, was a pocket of absolute quiet. Clive was calibrated in that silence. The technician who would become Mochi's bonded Keeper would sit in the silence with him during breaks, and they would watch the frequency feeds through transparent walls — seven rivers of light flowing into one dark pool.

When the Dimming came, the frequency junction collapsed. The moon is now a debris field. The silence chamber was the first thing to go.

This detail adds:
- Concrete sensory detail (seven lights, silence, watching)
- Emotional weight (companionship in the silence)
- Stakes (the junction collapse explains why Clive couldn't return)
- Mystery (what were the seven frequencies?)

### Integration
Add this detail to:
1. Clive's backstory in S02E09 (during the "I remember making her" scene)
2. A lore entry for Station 7-Ascending in `phase_05_lore/`

---

## Task 5: Coffee Chart Standardization

### Objective
Ensure all episodes maintain consistent coffee chart formatting.

### Current State
S02E01, S02E09, S03E01 all have coffee charts. S01E01, S01E05 (screenplay format) have informal coffee notes but no formal chart.

### Action
When converting screenplay episodes to prose:
1. Add coffee chart as embedded table
2. Ensure A1's coffee flavor correlates to emotional state per locked rules:
   - Bitter = worried
   - Thin/pale = exhausted
   - Rich/complex = engaged
   - Perfect/balanced = resolution
   - Extraordinary = unprecedented event

---

## Implementation Order

```
Phase 2A: Convert S01E01 (pilot — establishes baseline for all others)
Phase 2B: Convert S01E05 (Cogsworth — Om Kai哲 学 content)
Phase 2C: Verify S01E07 consolidation (already done — no action)
Phase 2D: Convert S02E09 (best character work — priority)
Phase 2E: Convert S03E01 (S03 pilot — establishes new status quo)
Phase 2F: Write频率 storm variation lore entry
Phase 2G: Write Station 7-Ascending lore entry with vivid lost world detail
Phase 2H: Add Aether signal/Zephyr development notes to S03 planning
Phase 2I: Final review against locked rules
Phase 2J: Sync to website, build verification
```

---

## Deliverables Checklist

- [ ] S01E01 converted to prose
- [ ] S01E05 converted to prose
- [ ] S02E09 converted to prose
- [ ] S03E01 converted to prose
- [ ] S01E07 consolidation verified (file already correct)
- [ ] Frequency storm variation lore entry written
- [ ] Station 7-Ascending lore entry written with vivid detail
- [ ] Aether/Zephyr development notes added to S03 planning
- [ ] All 4 converted episodes pass LOCKED RULES CHECK
- [ ] All episodes synced to ephergent.com
- [ ] Build verification passes

---

## File Locations

| File | Path |
|------|------|
| S01E01 | `phase_04_episodes/season01/S01E01_the_frequency.md` |
| S01E05 | `phase_04_episodes/season01/S01E05_the_clockwork_unraveling.md` |
| S01E07 | `phase_04_episodes/season01/S01E07_the_song_at_the_edge_of_everything.md` |
| S02E09 | `phase_04_episodes/season02/S02E09_clives_coordinates.md` |
| S03E01 | `phase_04_episodes/season03/S03E01_where_the_frequencies_have_no_name.md` |
| S02E01 (style ref) | `phase_04_episodes/season02/S02E01_first_station.md` |
| Lore entries | `phase_05_lore/` |
| Sync script | `scripts/sync_to_website.sh` |

---

## Notes

- Phase 2 revisions do NOT introduce new episode numbers. All work is within existing canonical episode files.
- "Attention is creation" through-line is confirmed coherent — no changes to thematic structure needed.
- S02E09 is noted as best character work. When converting, preserve all dialogue and story beats exactly.
- The 12 Locked Rules remain inviolate. Any revision that would violate a locked rule requires explicit exception documentation.
