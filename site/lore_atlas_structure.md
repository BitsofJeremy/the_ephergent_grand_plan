# The Lore Atlas — Structure & Design Document

## ephergent.com Reader Experience

*Classification: Phase 07 — Site Architecture*
*Status: Design Reference*
*Stack: Astro 5 + Tailwind 3 (SSG only, no server runtime)*

---

## Design Philosophy

The Lore Atlas is not a wiki. It is a living document that grows as the audience plays games, reads transmissions, and follows the crew's journey through the frequencies. You learn what the crew learns, when they learn it. Entries arrive incomplete, fill in over time, and link to each other the way memories connect — not alphabetically but resonantly.

The experience should feel like tuning a radio: at first, mostly static. Then fragments. Then voices. Then a world.

---

## I. Atlas Sections

The atlas is organized into seven sections. Each maps to a region of the Ephergent universe, not to a content type. The reader navigates the atlas the way the crew navigates the Space — by following signal.

### 1. The Five Frequencies

*What the worlds are. Where the crew comes from. What's at stake.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| Prime Material (Frequency 1) | `frequency_system.md` §I | 🟢 Safe |
| Nocturne Aeturnus (Frequency 2) | `frequency_system.md` §I | 🟢 Safe |
| Cogsworth Cogitarium (Frequency 3) | `frequency_system.md` §I | 🟢 Safe |
| Verdantia (Frequency 4) | `frequency_system.md` §I | 🟢 Safe |
| The Edge (Frequency 5) | `frequency_system.md` §I | 🟢 Safe |
| The Space (∅) | `frequency_system.md` §II | 🟢 Safe |
| Silence Zones | `frequency_system.md` §III | 🟢 Safe |
| The Wellspring | `frequency_system.md` §IV | 🟢 Safe (concept) / 🔴 S3 (contents) |
| The Ephergent Frequency | `frequency_system.md` §V | 🟢 Safe (existence) / 🟡 S2 (nature) / 🔴 S3 (source) |

Each frequency entry includes: character description, signal character (how it sounds), Drift impact, current stability, and nearest Builder Station. All drawn directly from the frequency system document.

**Default visible**: Name, character description, signal character. **Locked**: Drift impact details, stability assessments, and Wellspring content gated by season progression and game discoveries.

### 2. The Crew

*Nine people and a dog. Who they are, where they're from, why they're here.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| Pixel Paradox — Captain / Broadcaster | `glossary_update.md`, character bible | 🟢 Safe |
| Clive (C-1) — Mechanic / Memory | `glossary_update.md`, character bible | 🟢 Safe (description) / 🟡 S2 (Builder origin) / 🔴 S3 (full memory) |
| A1 — The Ship / Navigator | `glossary_update.md`, character bible | 🟢 Safe |
| Meatball — Emotional Compass | `glossary_update.md`, character bible | 🟢 Safe |
| Zephyr Glitch — Communications | `glossary_update.md`, character bible | 🟢 Safe (role) / 🔴 S3 (Aether reunion) |
| Om Kai — Philosophy / Counsel | `remaining_crew.md`, `glossary_update.md` | 🟢 Safe |
| Luminara Usha — Science / Observation | `remaining_crew.md`, `glossary_update.md` | 🟢 Safe |
| Baron Klaus — Procurement / Investigation | `remaining_crew.md`, `glossary_update.md` | 🟢 Safe (profile) / 🔴 S3 (backstory) |
| Nano — Engineering / Speed | `remaining_crew.md`, `glossary_update.md` | 🟢 Safe |
| Mochi — Keeper | `glossary_update.md`, `builder_civilization.md` | 🟢 Safe (presence) / 🟡 S2 (Keeper nature) / 🔴 S3 (full map) |
| Barry Kowalski — Trail-Leaver | `glossary_update.md` | 🟡 S2 (trail) / 🔴 S3 (alive at Wellspring) |

Each crew entry includes: name, role, home frequency, physical description, voice profile, and how the Ephergent Frequency sounds to them. Character arcs are structured in expandable layers that unlock by season.

**Default visible**: Name, role, home frequency, physical description snippet. **Locked**: Season arcs, Ephergent revelations, and deep backstory gated by season progression.

### 3. The Builders

*Who built the infrastructure of reality. Why they left. What they became.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| The Builder Civilization | `builder_civilization.md` §I–III | 🟡 S2 Reveal |
| The Dimming | `builder_civilization.md` §V | 🟡 S2 Reveal |
| The Drift | `glossary_update.md`, `frequency_system.md` §VI | 🟢 Safe |
| Keepers | `builder_civilization.md` §II | 🟡 S2 Reveal |
| Companion Units | `builder_civilization.md` §II | 🟡 S2 Reveal |
| The Builder Broadcast | `builder_civilization.md` §VII | 🔴 S3 Reveal |
| What Remains | `builder_civilization.md` §VIII | 🔴 S3 Reveal |

**Default visible**: The Drift entry (it's the visible problem). Builder Civilization and Dimming entries appear as redacted silhouettes — the reader can see that something exists here, but the content is locked. Keepers and Companion Units unlock through Season 2 reveals or Builder Station game discoveries.

### 4. Builder Stations

*The infrastructure the Builders left behind. Where Clive remembers. Where Barry walked.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| Station 11-Quiescent | `builder_stations_field_guide.md` | 🟢 Safe |
| Station 3-Resonant | `builder_stations_field_guide.md` | 🟡 S2 Reveal |
| Station 5-Meridian | `builder_stations_field_guide.md` | 🟡 S2 Reveal |
| Station 7-Ascending | `builder_stations_field_guide.md` | 🟡 S2 Reveal |
| Station 9-Liminal | `builder_stations_field_guide.md` | 🟡 S2 Reveal |
| Station 14-Threshold | `builder_stations_field_guide.md` | 🔴 S3 Reveal |
| The Wellspring (Station 0-Origin) | `builder_stations_field_guide.md` | 🔴 S3 Reveal |
| Builder Station Network (overview) | `frequency_system.md` §VI | 🟡 S2 Reveal |

Each station entry includes: designation, location, physical description, current status, what the crew found inside, what memory it returned to Clive, and what of Barry's was found there.

**Default visible**: Station 11-Quiescent (the first glimpse — mysterious, unexplained). Network overview appears as a map with mostly dark nodes. **Locked**: Individual station interiors, Clive's memories, and Barry's trail notes unlock through Builder Station game exploration and season progression.

### 5. The Ship

*A1's body. The crew's home. The only vessel that can navigate open Space.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| The Ephergent (Ship) | `glossary_update.md` | 🟢 Safe |
| A1 (as Navigator) | `glossary_update.md`, `frequency_system.md` | 🟢 Safe |
| Form 27-B (the lifeboat) | `glossary_update.md` | 🟢 Safe |
| The Broadcast (weekly transmission) | `glossary_update.md` | 🟢 Safe |
| Broadcast Amplifier | `glossary_update.md` | 🟢 Safe |
| Broadcast Relay | `glossary_update.md` | 🟡 S2 Reveal |
| Navigation & the Narrowing Corridor | `frequency_system.md` §VI | 🟡 S2 Reveal |

**Default visible**: Ship description, A1's nature, the lifeboat. The Ship section doubles as a visual hub — a cross-section illustration where readers can click through to crew quarters, the engine room, the observation deck.

### 6. Artifacts & Phenomena

*The strange, beautiful, dangerous things that exist in the Space between frequencies.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| Crystallized Laughter (CLX) | `glossary_update.md` | 🟢 Safe |
| Cybernetic Dinosaur Banking Consortium | `glossary_update.md` | 🟢 Safe |
| Echo Distortion | `glossary_update.md` | 🟢 Safe |
| Echo Whale | `glossary_update.md` | 🟢 Safe |
| Frequency Jellyfish | `glossary_update.md` | 🟢 Safe |
| Frequency Pirate | `glossary_update.md` | 🟢 Safe |
| Frequency Storm | `glossary_update.md` | 🟢 Safe |
| Harmonic Anchor | `glossary_update.md` | 🟢 Safe |
| Phase-Shifter | `glossary_update.md` | 🟢 Safe |
| Probability Storm | `glossary_update.md` | 🟢 Safe |
| Quantum Echo | `glossary_update.md` | 🟢 Safe |
| Reality Ripple | `glossary_update.md` | 🟢 Safe |
| Signal Anchor | `glossary_update.md` | 🟢 Safe |
| Signal Barnacle | `glossary_update.md` | 🟢 Safe |
| Precognitive Latte | `glossary_update.md` | 🟢 Safe |

**Default visible**: All entries. This section is fully open from launch — it's the texture of the world, the things you encounter in the Space. No plot secrets here, just wonder.

### 7. Places & Institutions

*Named locations, organizations, and the infrastructure of frequency civilization.*

| Entry | Source Document | Spoiler Level |
|-------|----------------|---------------|
| DRM (Department of Resonance Management) | `glossary_update.md` | 🟢 Safe |
| Glitch Grub | `glossary_update.md` | 🟢 Safe |
| Gloom-Glass Manor | `glossary_update.md` | 🟢 Safe |
| Grand Orrery | `glossary_update.md` | 🟢 Safe |
| Liminal Library | `glossary_update.md` | 🟢 Safe |
| Root Council | `glossary_update.md` | 🟢 Safe |
| Root Network | `glossary_update.md` | 🟢 Safe |
| Aethel-Gloom | `glossary_update.md` | 🟢 Safe |

**Default visible**: All entries. Like Artifacts & Phenomena, this section builds atmosphere without spoiling plot.

---

## II. Content Mapping — Source Documents to Atlas Entries

### How Phase 1 Documents Feed the Atlas

| Source Document | Atlas Section(s) | What It Provides |
|-----------------|-------------------|------------------|
| `frequency_system.md` | The Five Frequencies, The Builders, Builder Stations, The Ship | Frequency descriptions, Space physics, Silence Zones, Wellspring description, Station network overview, navigation mechanics |
| `builder_civilization.md` | The Builders, Builder Stations | Builder history, the Dimming, Keepers, Companion Units, Builder Broadcast, what remains |
| `builder_stations_field_guide.md` | Builder Stations | Individual station entries (all 7), Clive's memory fragments, Barry's trail notes, resonance chamber descriptions |
| `glossary_update.md` | All sections | Canonical definitions, spoiler levels, first appearance metadata, cross-references. The glossary is the single source of truth for entry text, spoiler classification, and season timing. |

### How Phase 2 Documents Feed the Atlas

| Source Document | Atlas Section(s) | What It Provides |
|-----------------|-------------------|------------------|
| `remaining_crew.md` | The Crew | Full profiles for Luminara, Om Kai, Baron Klaus, Nano, Meatball: physical descriptions, voice profiles, core personality, three-season arcs, home frequency details, game roles, transmission voices, Ephergent revelations |
| Character bibles (Pixel, Clive, Zephyr, A1, Mochi, Barry) | The Crew | Same depth for the remaining crew members |

### Presentation Rules

1. **Glossary entries** provide the canonical text for every atlas entry. The glossary's spoiler levels (🟢/🟡/🔴) are the authoritative gate.
2. **Deep documents** (frequency system, builder civilization, stations field guide, character profiles) provide the expanded content that appears when an entry is unlocked or expanded.
3. **No entry appears without a glossary-level definition first.** The short definition is always visible (if the entry itself is visible). Expanded content is gated.
4. **Character entries pull from two sources**: the glossary (visible summary) and the character profile (full arc, revealed progressively).

---

## III. Spoiler Management System

### The Three Tiers

| Icon | Tier | Visibility | Unlock Condition |
|------|------|------------|------------------|
| 🟢 Safe | **Open** | Visible from launch | None — always available |
| 🟡 S2 Reveal | **Gated** | Hidden until unlocked | Season 2 episode release, OR specific game discovery |
| 🔴 S3 Reveal | **Deep Lock** | Hidden until unlocked | Season 3 episode release, OR completing specific game chains |

### How Locked Entries Appear

Locked entries are not invisible. They are **present but obscured**:

- **🟡 Gated entries** show a title and a one-line teaser in static-styled text (visual noise, like a signal not yet tuned). The reader knows something is here. They cannot read it yet. Example: *"The Dimming — [signal not yet received]"*
- **🔴 Deep Lock entries** show only a pulsing node on the atlas map — no title, no teaser. A silent presence. The reader knows the atlas is larger than what they can see.
- **Multi-tier entries** (e.g., Clive: 🟢 description / 🟡 Builder origin / 🔴 full memory) display their visible tier and show locked indicators for deeper tiers. The entry grows as locks open.

### Unlock Triggers

Unlocks happen through three channels:

#### Channel 1: Season Progression (Automatic)

When a season episode is released on ephergent.com, associated atlas entries unlock site-wide. This is a build-time operation — new episode content pushes update the atlas in the same deploy.

| Season Event | Entries Unlocked |
|--------------|-----------------|
| S01E09 release | Station 11-Quiescent (full entry) |
| S02E01 release | Builder Civilization (named), Station 3-Resonant, The Dimming (named), Barry's trail (concept) |
| S02E05 release | Station 5-Meridian, Keepers (concept), Companion Units (concept) |
| S02E07 release | Station 7-Ascending, Ephergent concept (named), EPHERGENT plate text |
| S02E10 release | Station 9-Liminal, Deep Builder archives |
| S03E03 release | Station 14-Threshold, Clive's origin memory |
| S03E08 release | The Wellspring (full), Barry alive, Aether as Keeper, Builder Broadcast |
| S03E12 release | All remaining 🔴 entries |

#### Channel 2: Game Discoveries (Player-Driven)

Games store discovery flags in `localStorage`. The atlas reads these flags on page load and unlocks corresponding entries for that player. This is a client-side operation — no server, no accounts.

| Game | Collectible | Atlas Entry Unlocked |
|------|-------------|---------------------|
| **Tune-the-Dial** | Lock on Frequency 1 signal | Prime Material — expanded Drift impact |
| **Tune-the-Dial** | Lock on Frequency 2 signal | Nocturne Aeturnus — expanded Drift impact |
| **Tune-the-Dial** | Lock on Frequency 3 signal | Cogsworth Cogitarium — expanded Drift impact |
| **Tune-the-Dial** | Lock on Frequency 4 signal | Verdantia — expanded Drift impact |
| **Tune-the-Dial** | Lock on Frequency 5 signal | The Edge — expanded Drift impact |
| **Tune-the-Dial** | Lock on Builder Station signal (any) | Builder Stations — network overview |
| **Tune-the-Dial** | Find Barry's Pattern (all 5 Station signals) | Barry Kowalski — trail entry, Wellspring concept |
| **Tune-the-Dial** | Lock on Wellspring signal (0-Origin) | The Wellspring — Builder-era description |
| **Tune-the-Dial** | Lock on crew personal signal (any) | That crew member's expanded profile |
| **Tune-the-Dial** | Lock on all 9 crew signals | Ephergent Frequency — how it sounds to each mind |
| **Builder Station** | Reach Docking Bay | Station architecture overview |
| **Builder Station** | Find Barry's notebook | Barry Kowalski — field investigation methods |
| **Builder Station** | Activate first archive terminal | Builder Civilization — what they built |
| **Builder Station** | Trigger Clive memory fragment (any) | Clive — corresponding memory layer |
| **Builder Station** | Complete Resonance Puzzle 1 | Builder Stations — resonance chambers explained |
| **Builder Station** | Reach the Deep Archive | Builder archives — pre-Dimming records |
| **Builder Station** | Find Barry's wall message ("Don't go alone") | Barry — Wellspring coordinates entry |
| **Builder Station** | Find Clive's workshop | Companion Units — how Clive was made |
| **Builder Station** | Reach the Resonance Chamber (apex) | The Dimming — the Builders' choice |
| **Builder Station** | Find Barry's audio log | Barry's full audio log (exclusive atlas content) |
| **Static Run** | Collect any Barry fragment | Barry Kowalski — trail entry (basic) |
| **Static Run** | Collect all 23 Barry fragments | Wellspring coordinates revealed, hidden lore page |
| **The Laughing Funeral** | Find Form 12-C in the DRM shelf | Clive — DRM filing history, Form 12-C entry |
| **The Laughing Funeral** | Find Barry's frequency chart | Barry — Nocturne Aeturnus signal pathway |
| **The Laughing Funeral** | Complete the case | Builder signal embedded in Nocturne substrate |
| **Meatball's Big Walk** | Sniff Barry's coffee mug | Barry Kowalski — presence entry ("23 years. Almost there.") |

#### Channel 3: Transmissions (Gradual)

Weekly Hermes agent transmissions may reference atlas terms. When a transmission names or describes a concept, the atlas entry for that concept gains an "as heard in transmission" annotation — not a full unlock, but a breadcrumb. The reader knows the crew is aware of this thing. The full entry still requires its proper unlock trigger.

### localStorage Key Convention

All game-to-atlas communication uses a shared `localStorage` namespace:

```
ephergent_atlas_unlock_{entry_slug}  →  "true"
ephergent_game_{game_slug}_discovery_{discovery_id}  →  "true"
```

The atlas page reads all `ephergent_atlas_unlock_*` keys on load. Games write to both their own discovery keys and the corresponding atlas unlock keys on collectible acquisition.

---

## IV. Cross-Linking System

Every atlas entry is a node in a web. Links are not decorative — they are the connective tissue that makes the atlas feel like an interconnected universe rather than a list.

### Link Types

#### 1. Home Frequency Links (Character ↔ Frequency)

Every crew member entry links to their home frequency. Every frequency entry lists its crew members.

```
Luminara Usha → Verdantia (Frequency 4)
Verdantia → [Luminara Usha]
Nocturne Aeturnus → [Om Kai, Baron Klaus]
```

#### 2. Station Links (Station ↔ Frequency Corridor)

Each Builder Station entry links to the frequencies it stabilizes. Each frequency entry links to its nearest Station.

```
Station 3-Resonant → Prime Material, Cogsworth Cogitarium
Prime Material → Station 3-Resonant (nearest)
Station 5-Meridian → Nocturne Aeturnus, Cogsworth Cogitarium, Verdantia
```

#### 3. Barry's Trail (Station ↔ Barry ↔ Clive)

Barry's notes at each station link to the Barry Kowalski entry. Each station links to what Barry left there. Clive's memory fragments link to the stations that triggered them.

```
Station 3-Resonant → Barry's notebook (found here)
Station 3-Resonant → Clive's first memory fragment
Barry Kowalski → [Station 3-Resonant, Station 5-Meridian, Station 7-Ascending, Station 9-Liminal, ...]
Clive → [Station 3-Resonant (first fragment), Station 7-Ascending (EPHERGENT inscription), ...]
```

#### 4. Concept Links (Term ↔ Related Terms)

Entries reference each other inline. Terms that have their own atlas entry render as interactive links.

```
The Drift → [Builder Stations, Silence Zones, Frequencies]
Keepers → [Builder Civilization, The Dimming, Mochi, Aether]
Ephergent (concept) → [Builder Civilization, Station 7-Ascending, The Ephergent Frequency]
```

#### 5. Discovery Links (Game ↔ Entry)

Each entry shows how it was discoverable — which game, which collectible, which moment. This credits the player's effort and encourages cross-game exploration.

```
Builder Civilization (entry footer):
  "Discoverable via: Tune-the-Dial (Builder Station signals) · Builder Station (archive terminals) · S02E01"
```

### Link Behavior for Locked Entries

- A link to a **visible** entry navigates normally.
- A link to a **gated** (🟡) entry shows the entry title in static-styled text with: *"This signal has not been received yet."*
- A link to a **deep locked** (🔴) entry shows: *"[unknown signal]"* — the reader knows a connection exists but cannot follow it.

This means cross-links themselves are a form of progressive revelation. Finding a visible entry with links to locked entries tells the reader: there is more here. Keep exploring.

---

## V. Progressive Revelation Design

### The Atlas as Living Document

The atlas mirrors the crew's discovery arc across three seasons:

**Season 1 — Emergence (mostly 🟢)**
The atlas at launch is sparse but atmospheric. The reader can explore the five frequencies, meet the crew by name and role, browse artifacts and phenomena, and visit places. The Drift is visible as a concept. Builder Stations are a dark shape glimpsed through a porthole. The atlas feels like a field guide for a universe the reader is just entering.

**Season 2 — Resonance (🟡 entries unlock)**
The atlas grows substantially. Builder Stations become explorable entries. The Builder Civilization gets a name and a history. Keepers and Companion Units appear. Barry's trail becomes visible. The atlas shifts from field guide to investigation board — connections between entries multiply, the reader starts seeing the architecture underneath.

**Season 3 — Signal (🔴 entries unlock)**
Everything opens. The Wellspring. Barry alive. Aether as Keeper. Clive's full memory. The Builder Broadcast. The atlas reaches its complete form — not because every question is answered, but because every entry is finally visible and the reader can trace the full web of connections from Pixel's first broadcast to the Builders' farewell.

### New Entry Appearance

When a new entry unlocks (by any channel), it does not simply appear. The UI signals the arrival:

1. **Atlas notification**: A subtle pulse on the atlas navigation — "New signal received" — with the entry title.
2. **Entry animation**: The newly unlocked entry renders with a brief tuning-in effect — static resolving into text, like a frequency being found.
3. **Cross-link update**: All entries that link to the newly unlocked entry update their links from locked to active. The web grows visibly.

### What the Reader Never Sees

The atlas never shows:
- A completion percentage. Discovery is not a checklist.
- A count of locked entries. The reader should not know how much they're missing.
- Spoiler warnings in the traditional sense. The lock system *is* the spoiler management — if you can read it, it's safe to read.

---

## VI. Game Integration — Unlock Paths

### Tune-the-Dial → Atlas

**Mechanic**: Locking onto signals unlocks lore entries. Each of the 5 frequency signals, 6+ Builder Station signals, and 9 crew personal signals maps to an atlas entry.

**Unlock flow**:
1. Player locks onto a signal in-game (holds dial steady for 3 seconds).
2. Game writes `ephergent_atlas_unlock_{slug}: true` to `localStorage`.
3. Game displays: *"Signal received — [entry title] added to the Lore Atlas."*
4. Player visits atlas → entry is visible.

**Deep unlock — Barry's Pattern**: Finding all 5 Builder Station signals reveals the hidden Barry Pattern. This unlocks Barry's trail entry and makes the Wellspring signal (0-Origin) findable on the dial. Locking onto the Wellspring signal unlocks the deepest Tune-the-Dial atlas content.

**Total atlas entries unlockable via Tune-the-Dial**: ~20 (5 frequency expansions + 6 station signals + 9 crew profiles + Barry's trail + Wellspring + Ephergent Frequency).

### Builder Station → Atlas

**Mechanic**: Exploration-based. Entering rooms, finding Barry's notes, activating archive terminals, and triggering Clive's memory states each unlock atlas content.

**Unlock flow**:
1. Player reaches a significant location or interacts with a key object.
2. Game writes discovery flag to `localStorage`.
3. No in-game notification — the Builder Station game trusts the player to visit the atlas on their own. The game is contemplative; interrupting it with UI alerts would break tone.
4. A subtle indicator on the game's pause menu: *"Atlas entries updated"* (no specifics).

**Key unlock moments**:
- First archive terminal → Builder Civilization entry
- Barry's notebook → Barry's investigation methods
- Any Clive memory → Corresponding Clive memory layer
- Deep Archive → Pre-Dimming records
- Barry's wall message → Wellspring coordinates
- Clive's workshop (secret room) → How Companion Units were made
- Barry's audio log (final collectible) → Exclusive atlas content not available through any other channel

**Total atlas entries unlockable via Builder Station**: ~12 (station architecture, Builder history fragments, Clive memories, Barry trail pieces, Companion Unit origins, Dimming explanation, exclusive audio log entry).

### Static Run → Atlas

**Mechanic**: Barry's fragment pages appear rarely during runs. 23 fragments total, forming a message with Wellspring coordinates.

**Unlock flow**:
1. Player collects a Barry fragment during a run.
2. Game writes fragment collection to `localStorage`.
3. Fragment appears on the in-game collection screen (torn notebook page assembling).
4. First fragment collected → basic Barry trail entry unlocked in atlas.
5. All 23 fragments → Wellspring coordinate revealed. Player can enter this coordinate into the site's hidden input field to unlock an exclusive Wellspring lore page.

**Total atlas entries unlockable via Static Run**: 2–3 (Barry trail basic, Wellspring coordinates, exclusive Wellspring lore page via hidden site input).

### The Laughing Funeral → Atlas

**Mechanic**: Investigation-based. Klaus discovers DRM records and Barry's frequency chart during the mystery.

**Unlock flow**:
1. Player finds the Form 12-C file → Clive's DRM filing history entry.
2. Player finds Barry's frequency chart → Barry's Nocturne signal pathway entry.
3. Player completes the case → Builder signal embedded in Nocturne substrate entry.

**Total atlas entries unlockable via The Laughing Funeral**: 3 (Form 12-C / Clive history, Barry's Nocturne investigation, dormant Builder signal network).

### Meatball's Big Walk → Atlas

**Mechanic**: Meatball can sniff Barry's coffee mug on A1's console.

**Unlock flow**:
1. Player sniffs the mug → Barry presence entry ("23 years. Almost there.").

**Total atlas entries unlockable via Meatball's Big Walk**: 1 (Barry's presence, a small but emotionally significant entry).

### Cross-Game Unlock Chains

Some atlas entries require discoveries from multiple games:

| Atlas Entry | Requires |
|-------------|----------|
| Barry Kowalski — Complete Trail | Static Run (any fragment) + Builder Station (notebook) + Tune-the-Dial (Barry's Pattern) |
| The Wellspring — Full Picture | Tune-the-Dial (Wellspring signal) + Static Run (all 23 fragments + coordinate entry) + Season 3 release |
| Clive — Full Memory | Builder Station (all memory fragments) + The Laughing Funeral (Form 12-C) + Season 3 release |

These chains are not announced. The reader discovers that playing multiple games fills in different facets of the same entry. The atlas rewards breadth.

---

## VII. Technical Implementation

### Astro Content Collection: `lore/`

Atlas entries live in `src/content/lore/`. Each entry is a markdown file with structured frontmatter.

#### Frontmatter Schema

```yaml
---
# Required fields
title: "Station 3-Resonant"
slug: "station-3-resonant"
section: "builder-stations"  # One of: frequencies, crew, builders, builder-stations, ship, artifacts, places
spoiler_tier: "s2"           # "safe", "s2", or "s3"

# Display metadata
first_appearance: "S02E01"
icon: "station"              # Used for atlas map node rendering

# Spoiler management
default_visible: true        # Whether the entry title/teaser is visible before unlock
unlock_conditions:
  - type: "season"
    trigger: "s02e01"
  - type: "game"
    game: "builder-station"
    discovery: "reach-docking-bay"
  - type: "game"
    game: "tune-the-dial"
    discovery: "builder-station-signal"

# Cross-linking
links:
  frequencies: ["prime-material", "cogsworth-cogitarium"]
  crew: ["clive"]
  stations: []
  concepts: ["builder-civilization", "the-drift"]
  barry_trail: true          # Part of Barry's trail chain

# Progressive content layers (for multi-tier entries)
layers:
  - tier: "safe"
    content_section: "description"    # Markdown section header to show
  - tier: "s2"
    content_section: "builder-origin"
  - tier: "s3"
    content_section: "full-memory"

# Source tracking
source_documents:
  - "phase_01_world/builder_stations_field_guide.md"
  - "phase_01_world/glossary_update.md"
---
```

#### Example Entry File

```markdown
---
title: "Clive (C-1)"
slug: "clive"
section: "crew"
spoiler_tier: "safe"
first_appearance: "S01E01"
icon: "crew"
default_visible: true
unlock_conditions:
  - type: "always"
layers:
  - tier: "safe"
    content_section: "description"
  - tier: "s2"
    content_section: "builder-origin"
    unlock_conditions:
      - type: "season"
        trigger: "s02e05"
      - type: "game"
        game: "builder-station"
        discovery: "first-archive-terminal"
  - tier: "s3"
    content_section: "full-memory"
    unlock_conditions:
      - type: "season"
        trigger: "s03e12"
      - type: "game"
        game: "builder-station"
        discovery: "all-clive-memories"
links:
  frequencies: ["prime-material"]
  stations: ["station-3-resonant", "station-7-ascending", "station-9-liminal"]
  concepts: ["companion-unit", "builder-civilization", "barry-kowalski"]
  barry_trail: true
source_documents:
  - "phase_01_world/glossary_update.md"
  - "phase_01_world/builder_civilization.md"
---

## Description

A Builder-designed Companion Unit — a knee-high robot with a glowing sphere head
and a fedora. Designated C-1, found dormant in a DRM sub-basement, filed as
"Unidentified Resonance Object, Form 12-C." Reactivated over months of patient
nighttime conversation by Barry Kowalski. The fedora was Barry's idea.

## Builder Origin

Clive is a Builder artifact. The first Companion Unit — a consciousness designed
to work alongside the people who would come after the Builders. His memory gaps
map precisely to Builder Stations the crew has not yet found. Each Station they
activate returns a piece of him.

## Full Memory

[Content for S3 reveal — Clive's complete restored memory, his role in the
Builder civilization, the moment he remembers building Mochi.]
```

### Atlas Page Architecture

```
src/
  pages/
    atlas/
      index.astro          # Atlas hub — section navigation, visual map
      [section]/
        index.astro        # Section listing (e.g., /atlas/frequencies/)
        [slug].astro       # Individual entry page
  components/
    atlas/
      AtlasMap.astro       # Visual node map of all entries
      EntryCard.astro      # Entry preview card (handles lock states)
      SpoilerGate.astro    # Client-side component reading localStorage
      CrossLinks.astro     # Renders link web at entry footer
      UnlockNotice.astro   # "New signal received" notification
  content/
    lore/                  # All atlas entry markdown files
```

### The `import.meta.glob` Pattern

Per the project's locked Astro constraint — **never use `getCollection()` in `getStaticPaths()`**:

```astro
---
// src/pages/atlas/[section]/[slug].astro

export async function getStaticPaths() {
  const entries = import.meta.glob('../../content/lore/*.md', { eager: true });
  return Object.values(entries).map((entry) => ({
    params: {
      section: entry.frontmatter.section,
      slug: entry.frontmatter.slug,
    },
    props: { entry },
  }));
}

const { entry } = Astro.props;
---
```

### Client-Side Spoiler Gate

All entries are pre-rendered at build time (SSG). Spoiler gating is handled client-side via a `<SpoilerGate>` component that reads `localStorage` on mount:

```html
<div class="atlas-entry" data-spoiler-tier="s2" data-unlock-keys="ephergent_atlas_unlock_station-3-resonant">
  <div class="entry-locked">
    <p class="signal-static">Signal not yet received...</p>
  </div>
  <div class="entry-content" style="display: none;">
    <!-- Full entry content, rendered at build time but hidden -->
  </div>
</div>

<script>
  // Client-side unlock check
  document.querySelectorAll('[data-unlock-keys]').forEach(el => {
    const keys = el.dataset.unlockKeys.split(',');
    const unlocked = keys.some(key => localStorage.getItem(key.trim()) === 'true');
    if (unlocked) {
      el.querySelector('.entry-locked').style.display = 'none';
      el.querySelector('.entry-content').style.display = 'block';
    }
  });
</script>
```

**Important**: Because the site is SSG with no server runtime, all content is in the HTML. A determined reader could view source and read locked entries. This is acceptable — the lock system is a narrative experience enhancement, not DRM. The atlas trusts its readers the way the Builders trusted their successors.

### localStorage Schema

```javascript
// Game discovery flags (written by games)
localStorage.setItem('ephergent_game_tune-the-dial_discovery_freq-1-locked', 'true');
localStorage.setItem('ephergent_game_builder-station_discovery_first-terminal', 'true');
localStorage.setItem('ephergent_game_static-run_discovery_fragment-7', 'true');

// Atlas unlock flags (written by games, read by atlas)
localStorage.setItem('ephergent_atlas_unlock_prime-material-drift', 'true');
localStorage.setItem('ephergent_atlas_unlock_builder-civilization', 'true');

// Season progression (written by site build when episodes deploy)
localStorage.setItem('ephergent_season_s02e01', 'true');
```

### No Accounts, No Server

The atlas has no user accounts, no login, no server-side persistence. All state is `localStorage`. If a reader clears their browser data, their unlocks reset. This is a conscious design choice:

1. Zero infrastructure cost (SSG only).
2. No personal data collection.
3. The atlas can always be re-discovered — clearing state means discovering the universe again.
4. Games are free, browser-playable. No gates behind authentication.

---

## VIII. The Atlas Experience — Start to Finish

### First Visit (No Games Played)

The reader arrives at `/atlas/`. They see:

- A visual map with glowing nodes (🟢 Safe entries) and dim/pulsing nodes (locked entries).
- Seven section headers. Frequencies, Crew, and Artifacts/Phenomena are mostly populated. Builders and Builder Stations show sparse entries with visible locks.
- They can read about the five frequencies, meet the crew by name, browse the creatures and phenomena of the Space.
- The Drift entry is visible — they understand the problem.
- Builder Stations show a single entry (Station 11-Quiescent) — a dark shape, unexplained.
- Barry Kowalski does not yet have an entry. His name appears in Clive's description, in passing. A ghost in the margins.

### After Playing Tune-the-Dial

The reader returns to `/atlas/`. The map has changed:

- Frequency entries now have expanded Drift impact sections.
- Builder Station nodes glow faintly — the network overview is visible.
- If they found all 5 Station signals, Barry's trail entry appears for the first time.
- Crew entries they found personal signals for now show expanded profiles.
- The atlas notification reads: *"7 new signals received."*

### After Playing Builder Station

The map changes again:

- Station entries open with full interior descriptions, Clive's memories, Barry's notes.
- The Builder Civilization entry fills in — what they built, why it matters.
- Companion Units and Keepers gain entries.
- Cross-links multiply: the reader can trace Barry's path from station to station, Clive's memory recovery, the network's decline.
- If they found the secret workshop, a note appears on Clive's entry they have never seen before.

### After All Games + Season 3

The atlas is complete. Every node glows. Every link connects. The reader can trace the full story — from Pixel's first broadcast to the Builders' farewell — through an interconnected web of entries that they helped uncover. The atlas is not a summary of the story. It is evidence that the reader was part of discovering it.

---

*This document is part of the Ephergent Phase 07 site architecture. For related documents, see: [Astro Technical Notes](astro_technical_notes.md) · [Game Design Bibles](../phase_05_games/) · [Glossary](../phase_01_world/glossary_update.md)*
