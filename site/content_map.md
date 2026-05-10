# ephergent.com — Content Map

## The Ephergent Project | Phase 07 — Site Architecture

*Classification: Capstone Planning Document — Content Map*
*Stack: Astro 5 + Tailwind 3 (SSG only, no server runtime)*
*Deploy: GitHub Actions → static files*
*Status: Canonical reference for site build*

---

## 1. Site Architecture

### Page Tree

```
ephergent.com/
│
├── /                           # Landing page — "Tune the dial"
│
├── /games/                     # Games hub — all 6 games
│   ├── /games/meatballs-big-walk/        # Game 1 landing
│   │   ├── /games/meatballs-big-walk/play/   # Embedded game (iframe)
│   │   └── /games/meatballs-big-walk/about/  # Story context, controls, credits
│   ├── /games/tune-the-dial/             # Game 2
│   │   ├── /games/tune-the-dial/play/
│   │   └── /games/tune-the-dial/about/
│   ├── /games/static-run/                # Game 3
│   │   ├── /games/static-run/play/
│   │   └── /games/static-run/about/
│   ├── /games/the-laughing-funeral/      # Game 4
│   │   ├── /games/the-laughing-funeral/play/
│   │   └── /games/the-laughing-funeral/about/
│   ├── /games/builder-station/           # Game 5
│   │   ├── /games/builder-station/play/
│   │   └── /games/builder-station/about/
│   └── /games/the-wellspring/            # Game 6 (series finale)
│       ├── /games/the-wellspring/play/
│       └── /games/the-wellspring/about/
│
├── /crew/                      # Crew hub — 9 characters + Mochi + Barry
│   ├── /crew/pixel-paradox/
│   ├── /crew/a1/
│   ├── /crew/clive/
│   ├── /crew/zephyr-glitch/
│   ├── /crew/luminara-usha/
│   ├── /crew/om-kai/
│   ├── /crew/baron-klaus/
│   ├── /crew/nano/
│   ├── /crew/meatball/
│   ├── /crew/mochi/
│   └── /crew/barry-kowalski/
│
├── /atlas/                     # Lore Atlas hub — visual node map
│   ├── /atlas/frequencies/             # Section: The Five Frequencies
│   │   ├── /atlas/frequencies/prime-material/
│   │   ├── /atlas/frequencies/nocturne-aeturnus/
│   │   ├── /atlas/frequencies/cogsworth-cogitarium/
│   │   ├── /atlas/frequencies/verdantia/
│   │   ├── /atlas/frequencies/the-edge/
│   │   ├── /atlas/frequencies/the-space/
│   │   ├── /atlas/frequencies/silence-zones/
│   │   ├── /atlas/frequencies/the-wellspring/
│   │   └── /atlas/frequencies/the-ephergent-frequency/
│   ├── /atlas/crew/                    # Section: The Crew (mirrors /crew/ with lore framing)
│   ├── /atlas/builders/                # Section: The Builders
│   │   ├── /atlas/builders/builder-civilization/
│   │   ├── /atlas/builders/the-dimming/
│   │   ├── /atlas/builders/the-drift/
│   │   ├── /atlas/builders/keepers/
│   │   ├── /atlas/builders/companion-units/
│   │   ├── /atlas/builders/the-builder-broadcast/
│   │   └── /atlas/builders/what-remains/
│   ├── /atlas/builder-stations/        # Section: Builder Stations
│   │   ├── /atlas/builder-stations/station-11-quiescent/
│   │   ├── /atlas/builder-stations/station-3-resonant/
│   │   ├── /atlas/builder-stations/station-5-meridian/
│   │   ├── /atlas/builder-stations/station-7-ascending/
│   │   ├── /atlas/builder-stations/station-9-liminal/
│   │   ├── /atlas/builder-stations/station-14-threshold/
│   │   ├── /atlas/builder-stations/the-wellspring-station/
│   │   └── /atlas/builder-stations/network-overview/
│   ├── /atlas/ship/                    # Section: The Ship
│   │   ├── /atlas/ship/the-ephergent/
│   │   ├── /atlas/ship/a1-navigator/
│   │   ├── /atlas/ship/form-27-b/
│   │   ├── /atlas/ship/the-broadcast/
│   │   ├── /atlas/ship/broadcast-amplifier/
│   │   └── /atlas/ship/broadcast-relay/
│   ├── /atlas/artifacts/               # Section: Artifacts & Phenomena
│   │   └── (15 entries — all 🟢 Safe, always visible)
│   └── /atlas/places/                  # Section: Places & Institutions
│       └── (8 entries — all 🟢 Safe, always visible)
│
├── /transmissions/             # Transmission feed (blog-style)
│   ├── /transmissions/                 # Feed page — chronological, filterable
│   └── /transmissions/[slug]/          # Individual transmission page
│
├── /about/                     # About the project
├── /rss.xml                    # RSS feed (transmissions)
└── /sitemap.xml                # Auto-generated sitemap
```

### Navigation Structure

**Header (persistent, all pages):**
```
[Ephergent Logo]    Games    Crew    Atlas    Transmissions    [mobile menu ≡]
```

**Footer (persistent, all pages):**
```
The Ephergent © Before Greatness LLC
Games · Crew · Atlas · Transmissions · About · RSS
"Free forever. Browser-playable. Tune the dial."
```

**Mobile navigation:** Hamburger menu → full-screen overlay with same four sections. Games and Crew show sub-items. Atlas and Transmissions link directly to their hubs.

### Landing Page Content Strategy

The landing page is the dial. First-time visitors see:

1. **Hero**: Animated frequency dial visual. Tagline: *"A crew of nine. A ship that's also an espresso machine. A universe unraveling. Play for free."*
2. **What Is This?** — Three-sentence pitch from the Universe One-Pager. Link to About.
3. **Play Now** — Featured game card (latest release). One-click to play page.
4. **Meet the Crew** — Character portrait grid (9 + Meatball). Each links to crew page.
5. **Latest Transmissions** — 3 most recent transmissions, rendered as cards.
6. **Explore the Atlas** — Visual atlas map preview. "Tune in. Discover."

No login. No signup. No paywall language. Everything is one click from the front door.

---

## 2. Content Collections Schema

Four Astro content collections in `src/content/`, defined in `src/content/config.ts`.

### 2.1 `games/` Collection

**File naming:** `{slug}.md` — e.g., `meatballs-big-walk.md`, `tune-the-dial.md`

**Frontmatter schema:**

```typescript
// src/content/config.ts (games collection)
{
  slug: string;              // URL slug — matches filename
  title: string;             // Display title
  tagline: string;           // One-line pitch (used on cards)
  genre: string;             // "Point-and-Click" | "Frequency Puzzle" | "Endless Runner" | "Mystery" | "Exploration" | "Narrative Broadcast"
  engine: "godot" | "phaser" | "gb-studio";
  status: "released" | "coming-soon";
  release_order: number;     // 1–6
  season: number;            // Which season this game accompanies (1, 2, or 3)
  playable_character: string; // crew slug — "meatball", "pixel-paradox", "nano", "baron-klaus", "pixel-paradox", "barry-kowalski"
  embed_path: string;        // "/games/{slug}/index.html" — path to HTML5 export in public/
  size_mb: number;           // Measured size in MB (must be ≤ 15)
  thumbnail: string;         // Path to game card image
  crew_featured: string[];   // Crew slugs featured in this game
  atlas_unlocks: string[];   // Lore entry slugs this game can unlock
  barry_seed: string;        // Description of Barry's hidden content in this game
}
```

**Relationship fields:**
- `playable_character` → links to `crew/` collection
- `crew_featured` → links to `crew/` collection (for crew page "appears in" sections)
- `atlas_unlocks` → links to `lore/` collection (for atlas discovery credits)

**Example entry — `meatballs-big-walk.md`:**

```yaml
---
slug: "meatballs-big-walk"
title: "Meatball's Big Walk"
tagline: "A very good dog explores the ship. Sniffs everything. Judges everyone."
genre: "Point-and-Click"
engine: "godot"
status: "released"
release_order: 1
season: 1
playable_character: "meatball"
embed_path: "/games/meatballs-big-walk/index.html"
size_mb: 12.4
thumbnail: "/images/games/meatballs-big-walk-card.png"
crew_featured: ["meatball", "pixel-paradox", "a1", "clive"]
atlas_unlocks: ["barry-kowalski-presence"]
barry_seed: "Barry's coffee mug on A1's console. Sniff it: 'Smells like: looking for something. 23 years. Almost there.'"
---
```

### 2.2 `crew/` Collection

**File naming:** `{slug}.md` — e.g., `pixel-paradox.md`, `a1.md`, `clive.md`

**Frontmatter schema:**

```typescript
{
  slug: string;              // URL slug
  name: string;              // Display name — "Pixel Paradox", "A1", "Clive (C-1)"
  role: string;              // Ship role — "Captain / Broadcaster", "Ship / Navigator"
  home_frequency: string;    // "Prime Material" | "Nocturne Aeturnus" | "Cogsworth Cogitarium" | "Verdantia" | "The Edge" | "Builder-era" | "The Space"
  portrait: string;          // Path to character portrait image
  voice_summary: string;     // One-line voice description for card display
  transmission_voice: string; // Slug used in transmissions collection — matches character field
  joins_crew: string;        // Episode where they join — "E01", "E04", "E06", etc.
  first_transmission_week: number; // Week number of first transmission
  spoiler_tier: "safe" | "s2" | "s3"; // Deepest spoiler tier in their arc
  games_featured: string[];  // Game slugs where this character appears
  lore_links: string[];      // Atlas entry slugs related to this character
}
```

**Relationship fields:**
- `transmission_voice` → used to filter `transmissions/` collection
- `games_featured` → cross-links to `games/` collection
- `lore_links` → cross-links to `lore/` collection (atlas entries)

**Example entry — `clive.md`:**

```yaml
---
slug: "clive"
name: "Clive (C-1)"
role: "Mechanic / Memory"
home_frequency: "Builder-era"
portrait: "/images/crew/clive-portrait.png"
voice_summary: "Noir cadence. Two feet tall. Eight hundred years old. Won't say why."
transmission_voice: "clive"
joins_crew: "E01"
first_transmission_week: 2
spoiler_tier: "s3"
games_featured: ["meatballs-big-walk", "builder-station"]
lore_links: ["companion-units", "builder-civilization", "barry-kowalski", "station-3-resonant"]
---

A Builder-designed Companion Unit — a knee-high robot with a glowing sphere head
and a fedora. Designated C-1...
```

### 2.3 `lore/` Collection

**File naming:** `{slug}.md` — e.g., `prime-material.md`, `station-3-resonant.md`, `the-drift.md`

**Frontmatter schema:**

```typescript
{
  slug: string;
  title: string;
  section: "frequencies" | "crew" | "builders" | "builder-stations" | "ship" | "artifacts" | "places";
  spoiler_tier: "safe" | "s2" | "s3";
  first_appearance: string;  // Episode or game where this first appears — "S01E01", "Tune-the-Dial"
  icon: string;              // Atlas map node icon — "frequency", "crew", "station", "ship", "artifact", "place", "builder"
  default_visible: boolean;  // Whether title/teaser shows before unlock
  unlock_conditions: Array<{
    type: "always" | "season" | "game";
    trigger?: string;        // For season: "s02e01". For game: N/A
    game?: string;           // Game slug
    discovery?: string;      // Game-specific discovery ID
  }>;
  layers: Array<{
    tier: "safe" | "s2" | "s3";
    content_section: string; // Markdown section header to render
    unlock_conditions?: Array<{ type: string; trigger?: string; game?: string; discovery?: string }>;
  }>;
  links: {
    frequencies?: string[];
    crew?: string[];
    stations?: string[];
    concepts?: string[];
    barry_trail?: boolean;
  };
  source_documents: string[];
}
```

**Relationship fields:**
- `links.frequencies` / `links.crew` / `links.stations` / `links.concepts` → internal atlas cross-links
- `links.barry_trail` → flags entry as part of Barry's trail chain
- `unlock_conditions[].game` → cross-links to `games/` collection
- `source_documents` → maps back to Phase 1/2 source files

**Example entry — `the-drift.md`:**

```yaml
---
slug: "the-drift"
title: "The Drift"
section: "builders"
spoiler_tier: "safe"
first_appearance: "S01E01"
icon: "builder"
default_visible: true
unlock_conditions:
  - type: "always"
layers:
  - tier: "safe"
    content_section: "description"
links:
  frequencies: ["prime-material", "nocturne-aeturnus", "cogsworth-cogitarium", "verdantia", "the-edge"]
  stations: ["station-11-quiescent"]
  concepts: ["builder-civilization", "silence-zones", "the-dimming"]
  barry_trail: false
source_documents:
  - "phase_01_world/glossary_update.md"
  - "phase_01_world/frequency_system.md"
---

## Description

The ongoing consequence of Builder Stations failing. Frequencies drift apart...
```

### 2.4 `transmissions/` Collection

**File naming:** `s{season}-w{week}-{character-slug}.md` — e.g., `s1-w01-pixel-paradox.md`, `s1-w07-barry-kowalski.md`

**Frontmatter schema:**

```typescript
{
  title: string;             // Transmission title — in character voice
  character: string;         // Character slug: "pixel-paradox", "a1", "clive", etc.
  season: number;            // 1, 2, or 3
  week: number;              // Week number within the season
  date: string;              // ISO date: "2025-09-15"
  tags: string[];            // Content tags: ["frequency", "crew", "builder-station"]
  spoiler_tier: "green" | "yellow" | "red";
  episode_connection: string; // Episode(s) this transmission references — "E01", "E10-E12"
  lore_seeded: string[];     // Atlas entry slugs seeded (breadcrumbed) by this transmission
  excerpt: string;           // 1–2 sentence excerpt for cards and RSS
}
```

**Relationship fields:**
- `character` → links to `crew/` collection (for crew page transmission list)
- `lore_seeded` → links to `lore/` collection (adds "as heard in transmission" annotations)
- `episode_connection` → contextual link to season/episode structure

**Example entry — `s1-w01-pixel-paradox.md`:**

```yaml
---
title: "This Is Pixel Paradox, Broadcasting from Nowhere"
character: "pixel-paradox"
season: 1
week: 1
date: "2025-07-07"
tags: ["broadcast", "drm", "collapse", "first-contact"]
spoiler_tier: "green"
episode_connection: "E01"
lore_seeded: ["the-ephergent-frequency", "drm"]
excerpt: "First broadcast. She doesn't know who's listening or if anyone is. Raw, scared, brave anyway."
---

**[BROADCAST — EPHERGENT SIGNAL, OPEN CHANNEL]**

...
```

---

## 3. Games Section Map

### 3.1 Per-Game Page Structure

Each game has three URLs:

| URL | Purpose | Template |
|-----|---------|----------|
| `/games/{slug}/` | Landing page — pitch, screenshot, story context, play button | `GameLanding.astro` |
| `/games/{slug}/play/` | Embedded game — full-width iframe or inline canvas | `GamePlay.astro` |
| `/games/{slug}/about/` | Extended info — controls, credits, lore connections, atlas unlocks | `GameAbout.astro` |

**Landing page content** (from `games/` collection entry + markdown body):
- Title + tagline
- Thumbnail / screenshot
- Genre badge + engine badge
- "Play Now" button → `/play/`
- Story context (1–2 paragraphs: who is the character, what's the situation)
- "What you might discover" — teaser of atlas connections (no spoilers)

**Play page content:**
- Iframe embed (Godot) or inline Phaser canvas, filling viewport
- Minimal chrome — game title, fullscreen toggle, back-to-landing link
- No ads, no interstitials, no pre-roll

**About page content:**
- Controls reference
- Character background
- "This game connects to..." — atlas entries this game can unlock (discovery credit)
- Development credits
- Size + engine info

### 3.2 Game Embedding Details

| Game | Engine | Embed Method | Notes |
|------|--------|-------------|-------|
| Meatball's Big Walk | Godot 4 | `<iframe src="/games/meatballs-big-walk/index.html">` | `canvas_resize_policy=2`, responsive width |
| Tune-the-Dial | Godot 4 | `<iframe src="/games/tune-the-dial/index.html">` | Audio-dependent — needs user interaction to start |
| Static Run | Phaser.js | `<div id="phaser-game">` + inline script | Lighter footprint, no iframe needed |
| The Laughing Funeral | Godot 4 | `<iframe src="/games/the-laughing-funeral/index.html">` | Longest playtime (45–90 min), save state via localStorage |
| Builder Station | Godot 4 | `<iframe src="/games/builder-station/index.html">` | Contemplative — no in-game atlas notifications |
| The Wellspring | Godot 4 | `<iframe src="/games/the-wellspring/index.html">` | Final game. Requires all 3 seasons. |

**Static assets:** Game HTML5 exports live in `public/games/{slug}/` and are copied as-is during build. Not processed by Astro.

**Iframe template:**

```html
<iframe
  src="{embed_path}"
  width="100%"
  height="600"
  style="border: none;"
  allowfullscreen
  loading="lazy"
></iframe>
```

### 3.3 Cross-Game Collectible Tracking

All games share a `localStorage` namespace. No server. No accounts.

**localStorage key schema:**

```
ephergent_game_{game-slug}_discovery_{discovery-id}  →  "true"
ephergent_game_{game-slug}_save_{key}                →  {value}
ephergent_atlas_unlock_{entry-slug}                  →  "true"
```

Games write both their own discovery keys AND the corresponding atlas unlock keys on collectible acquisition. The atlas reads `ephergent_atlas_unlock_*` keys on page load.

**Per-game discovery keys:**

| Game | Key Pattern | Example |
|------|-------------|---------|
| Meatball's Big Walk | `ephergent_game_meatballs-big-walk_discovery_{id}` | `..._discovery_barry-mug-sniffed` |
| Tune-the-Dial | `ephergent_game_tune-the-dial_discovery_{id}` | `..._discovery_freq-1-locked`, `..._discovery_barry-pattern-found` |
| Static Run | `ephergent_game_static-run_discovery_fragment-{n}` | `..._discovery_fragment-7` |
| The Laughing Funeral | `ephergent_game_the-laughing-funeral_discovery_{id}` | `..._discovery_form-12c-found` |
| Builder Station | `ephergent_game_builder-station_discovery_{id}` | `..._discovery_first-terminal`, `..._discovery_clive-memory-1` |
| The Wellspring | `ephergent_game_the-wellspring_discovery_{id}` | `..._discovery_broadcast-received` |

### 3.4 Game Release Order and Gating

| Order | Game | Season | Gating | Status |
|-------|------|--------|--------|--------|
| 1 | Meatball's Big Walk | S1 | None — available at launch | GDScript complete, art pending |
| 2 | Tune-the-Dial | S1 | None — available at launch | Design complete |
| 3 | Static Run | S1 | None — available at launch | Pre-production |
| 4 | The Laughing Funeral | S2 | None (S2 enhances context but game is standalone) | Pre-production |
| 5 | Builder Station | S2 | None (S2 provides context, not access) | Design bible complete |
| 6 | The Wellspring | S3 | Soft gate — all 3 seasons complete; games 1–5 shipped | Design direction only |

**Gating philosophy:** No game is locked behind another game. Every game is free and immediately playable. Season context enhances meaning but is never required. The Wellspring is the only game with a soft expectation that the player has experienced the full journey.

---

## 4. Crew Section Map

### 4.1 Per-Character Page Structure

**URL:** `/crew/{slug}/`

**Page template:** `CrewProfile.astro`

**Content blocks (top to bottom):**

1. **Portrait + Identity** — Name, role, home frequency badge, voice summary
2. **Who They Are** — 2–3 paragraph character description (always visible, from Phase 2 profiles)
3. **Their Voice** — How they sound in transmissions (links to filtered transmission feed)
4. **On the Ship** — Role aboard The Ephergent, relationships with other crew
5. **Latest Transmissions** — 3 most recent transmissions by this character (auto-populated)
6. **In the Games** — Which games feature this character (links to game pages)
7. **In the Atlas** — Related lore entries (links to atlas pages)
8. **Season Arc** — Progressive reveal: S1 arc (always visible), S2/S3 arcs (spoiler-gated by localStorage)

### 4.2 Content Sources — Phase 2 → Crew Pages

| Character | Primary Source | Supporting Sources |
|-----------|---------------|-------------------|
| Pixel Paradox | `phase_02_characters/pixel_paradox.md` | `GRAND_MASTER_PLAN.md` §Character Profiles |
| A1 | `phase_02_characters/a1.md` | `GRAND_MASTER_PLAN.md` §A1 |
| Clive (C-1) | `phase_02_characters/clive.md` | `source_archive/signal_lore/characters/prompts/clive_automaton_prompt.md` |
| Zephyr Glitch | `phase_02_characters/zephyr_and_aether.md` | `GRAND_MASTER_PLAN.md` §Zephyr |
| Luminara Usha | `phase_02_characters/remaining_crew.md` | `GRAND_MASTER_PLAN.md` §Luminara |
| Om Kai | `phase_02_characters/remaining_crew.md` | `GRAND_MASTER_PLAN.md` §Om Kai |
| Baron Klaus | `phase_02_characters/remaining_crew.md` | `GRAND_MASTER_PLAN.md` §Baron Klaus |
| Nano | `phase_02_characters/remaining_crew.md` | `GRAND_MASTER_PLAN.md` §Nano |
| Meatball | `phase_02_characters/remaining_crew.md` | `GRAND_MASTER_PLAN.md` §Meatball |
| Mochi | `phase_02_characters/mochi.md` | `source_archive/signal_lore/characters/prompts/mochi_prompt.md` |
| Barry Kowalski | `phase_02_characters/barry_kowalski.md` | `GRAND_MASTER_PLAN.md` §Barry |

### 4.3 Crew → Transmissions Cross-Link

Each crew page shows that character's transmissions, filtered by the `character` field in the transmissions collection. The query uses `import.meta.glob`:

```astro
---
const allTransmissions = import.meta.glob('../content/transmissions/*.md', { eager: true });
const characterTransmissions = Object.values(allTransmissions)
  .filter(t => t.frontmatter.character === crew.frontmatter.slug)
  .sort((a, b) => new Date(b.frontmatter.date) - new Date(a.frontmatter.date));
---
```

### 4.4 Spoiler Management — Crew Pages

| Tier | What's Visible | Crew Members Affected |
|------|---------------|----------------------|
| 🟢 Always visible | Name, role, home frequency, physical description, voice summary, S1 arc | All crew |
| 🟡 S2 gated | Builder origin, Keeper nature, investigation progress | Clive, Mochi, Barry (trail), Klaus |
| 🔴 S3 gated | Full memory, Wellspring reunion, Aether as Keeper, Klaus backstory | Clive, Barry, Zephyr, Klaus, Mochi |

**Implementation:** Same client-side `localStorage` check as the atlas. S2/S3 content blocks are rendered at build time but hidden via `display: none`. JavaScript checks season unlock flags on page load.

**Barry Kowalski's crew page** is unique: it does not exist at launch. His page appears (as a link in the crew hub) only after the reader has encountered his name in Clive's transmission (Week 7) or found his coffee mug in Meatball's Big Walk. Pre-reveal, his slot on the crew page shows as an empty silhouette: *"Signal pending..."*

---

## 5. Lore Section (Atlas)

### 5.1 Atlas Hub (`/atlas/`)

The hub page shows:

1. **Visual node map** — `AtlasMap.astro` component. Glowing nodes for visible entries, dim/pulsing nodes for locked entries. Connections drawn between linked entries. Seven section clusters.
2. **Section navigation** — Seven clickable sections with entry counts (visible / total).
3. **"New signals received"** notification when unlocks have occurred since last visit.

### 5.2 Seven Atlas Sections — Full Entry Lists

**Section 1: The Five Frequencies** (9 entries)

| Entry | Slug | Tier | Source |
|-------|------|------|--------|
| Prime Material (Freq 1) | `prime-material` | 🟢 Safe | `frequency_system.md` §I |
| Nocturne Aeturnus (Freq 2) | `nocturne-aeturnus` | 🟢 Safe | `frequency_system.md` §I |
| Cogsworth Cogitarium (Freq 3) | `cogsworth-cogitarium` | 🟢 Safe | `frequency_system.md` §I |
| Verdantia (Freq 4) | `verdantia` | 🟢 Safe | `frequency_system.md` §I |
| The Edge (Freq 5) | `the-edge` | 🟢 Safe | `frequency_system.md` §I |
| The Space (∅) | `the-space` | 🟢 Safe | `frequency_system.md` §II |
| Silence Zones | `silence-zones` | 🟢 Safe | `frequency_system.md` §III |
| The Wellspring | `the-wellspring` | 🟢/🔴 | `frequency_system.md` §IV |
| The Ephergent Frequency | `the-ephergent-frequency` | 🟢/🟡/🔴 | `frequency_system.md` §V |

**Section 2: The Crew** (11 entries)

| Entry | Slug | Tier | Source |
|-------|------|------|--------|
| Pixel Paradox | `pixel-paradox` | 🟢 Safe | Character bible, `glossary_update.md` |
| Clive (C-1) | `clive` | 🟢/🟡/🔴 | Character bible, `glossary_update.md`, `builder_civilization.md` |
| A1 | `a1` | 🟢 Safe | Character bible, `glossary_update.md` |
| Meatball | `meatball` | 🟢 Safe | Character bible, `glossary_update.md` |
| Zephyr Glitch | `zephyr-glitch` | 🟢/🔴 | Character bible, `glossary_update.md` |
| Om Kai | `om-kai` | 🟢 Safe | `remaining_crew.md`, `glossary_update.md` |
| Luminara Usha | `luminara-usha` | 🟢 Safe | `remaining_crew.md`, `glossary_update.md` |
| Baron Klaus | `baron-klaus` | 🟢/🔴 | `remaining_crew.md`, `glossary_update.md` |
| Nano | `nano` | 🟢 Safe | `remaining_crew.md`, `glossary_update.md` |
| Mochi | `mochi` | 🟢/🟡/🔴 | `glossary_update.md`, `builder_civilization.md` |
| Barry Kowalski | `barry-kowalski` | 🟡/🔴 | `glossary_update.md` |

**Section 3: The Builders** (7 entries)

| Entry | Slug | Tier | Source |
|-------|------|------|--------|
| The Builder Civilization | `builder-civilization` | 🟡 S2 | `builder_civilization.md` §I–III |
| The Dimming | `the-dimming` | 🟡 S2 | `builder_civilization.md` §V |
| The Drift | `the-drift` | 🟢 Safe | `glossary_update.md`, `frequency_system.md` §VI |
| Keepers | `keepers` | 🟡 S2 | `builder_civilization.md` §II |
| Companion Units | `companion-units` | 🟡 S2 | `builder_civilization.md` §II |
| The Builder Broadcast | `the-builder-broadcast` | 🔴 S3 | `builder_civilization.md` §VII |
| What Remains | `what-remains` | 🔴 S3 | `builder_civilization.md` §VIII |

**Section 4: Builder Stations** (8 entries)

| Entry | Slug | Tier | Source |
|-------|------|------|--------|
| Station 11-Quiescent | `station-11-quiescent` | 🟢 Safe | `builder_stations_field_guide.md` |
| Station 3-Resonant | `station-3-resonant` | 🟡 S2 | `builder_stations_field_guide.md` |
| Station 5-Meridian | `station-5-meridian` | 🟡 S2 | `builder_stations_field_guide.md` |
| Station 7-Ascending | `station-7-ascending` | 🟡 S2 | `builder_stations_field_guide.md` |
| Station 9-Liminal | `station-9-liminal` | 🟡 S2 | `builder_stations_field_guide.md` |
| Station 14-Threshold | `station-14-threshold` | 🔴 S3 | `builder_stations_field_guide.md` |
| The Wellspring (Station 0-Origin) | `the-wellspring-station` | 🔴 S3 | `builder_stations_field_guide.md` |
| Builder Station Network | `network-overview` | 🟡 S2 | `frequency_system.md` §VI |

**Section 5: The Ship** (6 entries)

| Entry | Slug | Tier | Source |
|-------|------|------|--------|
| The Ephergent (Ship) | `the-ephergent-ship` | 🟢 Safe | `glossary_update.md` |
| A1 (as Navigator) | `a1-navigator` | 🟢 Safe | `glossary_update.md`, `frequency_system.md` |
| Form 27-B (the lifeboat) | `form-27-b` | 🟢 Safe | `glossary_update.md` |
| The Broadcast | `the-broadcast` | 🟢 Safe | `glossary_update.md` |
| Broadcast Amplifier | `broadcast-amplifier` | 🟢 Safe | `glossary_update.md` |
| Broadcast Relay | `broadcast-relay` | 🟡 S2 | `glossary_update.md` |

**Section 6: Artifacts & Phenomena** (15 entries — all 🟢 Safe)

Crystallized Laughter, Cybernetic Dinosaur Banking Consortium, Echo Distortion, Echo Whale, Frequency Jellyfish, Frequency Pirate, Frequency Storm, Harmonic Anchor, Phase-Shifter, Probability Storm, Quantum Echo, Reality Ripple, Signal Anchor, Signal Barnacle, Precognitive Latte.

**Section 7: Places & Institutions** (8 entries — all 🟢 Safe)

DRM, Glitch Grub, Gloom-Glass Manor, Grand Orrery, Liminal Library, Root Council, Root Network, Aethel-Gloom.

**Total atlas entries at launch: ~64**

### 5.3 Entry Templates

Each atlas entry page (`/atlas/[section]/[slug].astro`) renders:

1. **Entry header** — Title, section breadcrumb, spoiler tier icon, first-appearance badge
2. **Content body** — Markdown rendered by tier. Safe content always visible. S2/S3 content wrapped in `<SpoilerGate>` divs checked against `localStorage`
3. **Cross-links footer** — `CrossLinks.astro` component rendering all related entries as clickable links (locked entries render as static-styled text)
4. **Discovery credit** — "Discoverable via: Tune-the-Dial (signal X) · Builder Station (terminal Y) · S02E01"
5. **"As heard in" annotations** — Links to transmissions that reference this entry

### 5.4 Progressive Revelation Implementation

**Build-time:** All content for all tiers is rendered into static HTML. Nothing is server-gated.

**Client-side on page load:**

```javascript
// SpoilerGate.astro — client script
document.querySelectorAll('[data-spoiler-tier]').forEach(el => {
  const tier = el.dataset.spoilerTier;
  const keys = (el.dataset.unlockKeys || '').split(',').filter(Boolean);

  // Check if any unlock condition is met
  const unlocked = keys.some(key => localStorage.getItem(key.trim()) === 'true');

  if (unlocked) {
    el.querySelector('.entry-locked')?.style.setProperty('display', 'none');
    el.querySelector('.entry-content')?.style.setProperty('display', 'block');
  }
});
```

**Intentional design:** A determined reader can view-source to read locked entries. This is acceptable. The lock system is a narrative experience, not DRM. The atlas trusts its readers the way the Builders trusted their successors.

### 5.5 Cross-Linking System

Five link types (from Lore Atlas Structure document):

| Link Type | Pattern | Example |
|-----------|---------|---------|
| Home Frequency | Character ↔ Frequency | Luminara → Verdantia; Verdantia → [Luminara] |
| Station Links | Station ↔ Frequency corridor | Station 3-Resonant → [Prime Material, Cogsworth] |
| Barry's Trail | Station ↔ Barry ↔ Clive | Station 3 → Barry's notebook → Clive's first memory |
| Concept Links | Term ↔ Related terms | The Drift → [Builder Stations, Silence Zones] |
| Discovery Links | Game ↔ Entry | Builder Civilization: "Discoverable via: Tune-the-Dial · Builder Station · S02E01" |

**Link behavior for locked entries:**
- Visible entry → normal navigation
- 🟡 Gated entry → title in static text: *"This signal has not been received yet."*
- 🔴 Deep locked → *"[unknown signal]"*

---

## 6. Transmissions Section

### 6.1 Feed Layout (`/transmissions/`)

The feed page shows all published transmissions in reverse chronological order. Filterable by:

- **Character** — dropdown or button row: All, Pixel, A1, Clive, Zephyr, Luminara, Om Kai, Klaus, Nano, Meatball, Barry
- **Season** — tabs: Season 1, Season 2, Season 3
- **Week** — secondary filter within a season

Each transmission renders as a card:
- Character portrait (small)
- Title (in character voice)
- Excerpt (from frontmatter `excerpt` field)
- Date + Season/Week badge
- Tags (clickable)

**Barry's transmissions** appear with a distinctive visual treatment — static-styled border, no portrait (just `?`), "Date Unknown" instead of a date. This is consistent with his field note format.

### 6.2 Per-Transmission Page (`/transmissions/[slug]/`)

**Template:** `TransmissionPage.astro`

**Content blocks:**
1. **Character header** — Portrait, name, role, link to crew page
2. **Transmission metadata** — Season, week, date, spoiler tier badge
3. **Body** — Full transmission text, rendered from markdown
4. **Lore connections** — "This transmission references:" + links to atlas entries (from `lore_seeded` field)
5. **Navigation** — Previous/next transmission (chronological), plus next from same character
6. **Character filter link** — "More from {character name}" → filtered feed

### 6.3 Calendar Integration

Season 1: 12 weeks, 50 transmissions total.

| Week | Voices | Transmission Count |
|------|--------|--------------------|
| 1 | Pixel, A1 | 2 |
| 2 | Pixel, Clive, Meatball | 3 |
| 3 | Pixel, A1, Luminara | 3 |
| 4 | Pixel, Clive, Om Kai, Meatball | 4 |
| 5 | Zephyr, Pixel, A1, Luminara | 4 |
| 6 | Pixel, Clive, Nano, Om Kai, Meatball | 5 |
| 7 | Pixel, Clive, Zephyr, **Barry** | 4 |
| 8 | Pixel, Luminara, A1, Om Kai, **Barry** | 5 |
| 9 | Meatball, Zephyr, Luminara, **Barry** | 4 |
| 10 | Pixel, Nano, Clive, A1 | 4 |
| 11 | Pixel, **Klaus**, Luminara, **Barry** | 4 |
| 12 | ALL + **Barry** | 8 |

Transmissions publish weekly. Each week's batch drops simultaneously. The site build deploys them as a batch — push to main, GitHub Actions builds, all that week's transmissions go live.

### 6.4 Hermes Agent Publication Workflow

```
Hermes Agent (per character)
  → Generates markdown + valid frontmatter
  → Validates against transmissions/ collection schema
  → PR to repo: src/content/transmissions/s{N}-w{NN}-{slug}.md
  → Review (automated schema check + human spot-check)
  → Merge to main
  → GitHub Actions: astro build → deploy
  → Transmissions live on ephergent.com
```

**Validation checklist (automated):**
- [ ] Frontmatter matches schema (all required fields present, correct types)
- [ ] `character` field matches a valid crew slug
- [ ] `spoiler_tier` is one of: `green`, `yellow`, `red`
- [ ] `date` is valid ISO date
- [ ] Word count within target range for that character
- [ ] No references to removed antagonists (Corporate Corp / The Board)
- [ ] No nautical metaphors (sail, anchor, port, starboard, helm)
- [ ] `[END TRANSMISSION]` or `[END FIELD NOTE]` present (where required by character)

**Agent output location:** `src/content/transmissions/`

**No runtime dependency:** Hermes agents feed the static build pipeline. They do not run on the site itself.

---

## 7. Progressive Revelation System

### 7.1 localStorage Key Schema

```javascript
// === GAME DISCOVERY FLAGS ===
// Written by games when player finds something
"ephergent_game_{game-slug}_discovery_{discovery-id}"  →  "true"

// === ATLAS UNLOCK FLAGS ===
// Written by games, read by atlas pages
"ephergent_atlas_unlock_{entry-slug}"  →  "true"

// === SEASON PROGRESSION FLAGS ===
// Written by site build when episode content deploys
"ephergent_season_{season-episode}"  →  "true"

// === GAME SAVE STATE ===
// Written by individual games for their own persistence
"ephergent_game_{game-slug}_save_{key}"  →  {value}
```

**Concrete examples:**

```javascript
// Tune-the-Dial: player locked onto Frequency 1
localStorage.setItem('ephergent_game_tune-the-dial_discovery_freq-1-locked', 'true');
localStorage.setItem('ephergent_atlas_unlock_prime-material-drift', 'true');

// Builder Station: player found first archive terminal
localStorage.setItem('ephergent_game_builder-station_discovery_first-terminal', 'true');
localStorage.setItem('ephergent_atlas_unlock_builder-civilization', 'true');

// Static Run: player collected fragment 7
localStorage.setItem('ephergent_game_static-run_discovery_fragment-7', 'true');

// Season 2 Episode 1 released (set during build)
localStorage.setItem('ephergent_season_s02e01', 'true');
```

### 7.2 What Unlocks What

**Games → Lore Atlas:**

| Game | Discovery | Atlas Entry Unlocked |
|------|-----------|---------------------|
| Tune-the-Dial | Lock on Frequency 1–5 signals | Frequency expanded Drift impact (×5) |
| Tune-the-Dial | Lock on any Builder Station signal | Network overview |
| Tune-the-Dial | Barry's Pattern (all 5 Station signals) | Barry trail entry + Wellspring concept |
| Tune-the-Dial | Lock on Wellspring signal (0-Origin) | Wellspring Builder-era description |
| Tune-the-Dial | Lock on any crew personal signal | That crew member's expanded profile |
| Tune-the-Dial | Lock on all 9 crew signals | Ephergent Frequency — how it sounds to each mind |
| Builder Station | Reach docking bay | Station architecture overview |
| Builder Station | Find Barry's notebook | Barry investigation methods |
| Builder Station | First archive terminal | Builder Civilization — what they built |
| Builder Station | Any Clive memory fragment | Corresponding Clive memory layer |
| Builder Station | Resonance Puzzle 1 | Resonance chambers explained |
| Builder Station | Reach Deep Archive | Pre-Dimming records |
| Builder Station | Barry's wall message | Wellspring coordinates entry |
| Builder Station | Find Clive's workshop | Companion Units — how Clive was made |
| Builder Station | Reach Resonance Chamber apex | The Dimming — the Builders' choice |
| Builder Station | Find Barry's audio log | Exclusive atlas content (audio log entry) |
| Static Run | Collect any Barry fragment | Barry trail basic |
| Static Run | Collect all 23 fragments | Wellspring coordinates + hidden lore page |
| The Laughing Funeral | Find Form 12-C | Clive DRM filing history |
| The Laughing Funeral | Find Barry's frequency chart | Barry's Nocturne signal pathway |
| The Laughing Funeral | Complete the case | Builder signal in Nocturne substrate |
| Meatball's Big Walk | Sniff Barry's coffee mug | Barry presence entry |

**Cross-game unlock chains (not announced — discovered by breadth of play):**

| Atlas Entry | Requires |
|-------------|----------|
| Barry Kowalski — Complete Trail | Static Run (any fragment) + Builder Station (notebook) + Tune-the-Dial (Barry's Pattern) |
| The Wellspring — Full Picture | Tune-the-Dial (Wellspring signal) + Static Run (all 23 fragments) + S3 release |
| Clive — Full Memory | Builder Station (all memory fragments) + The Laughing Funeral (Form 12-C) + S3 release |

**Episodes → Lore Atlas (season progression, automatic at build time):**

| Season Event | Entries Unlocked |
|--------------|-----------------|
| S01E09 | Station 11-Quiescent (full entry) |
| S02E01 | Builder Civilization (named), Station 3-Resonant, The Dimming (named), Barry trail (concept) |
| S02E05 | Station 5-Meridian, Keepers (concept), Companion Units (concept) |
| S02E07 | Station 7-Ascending, Ephergent concept (named), EPHERGENT inscription |
| S02E10 | Station 9-Liminal, Deep Builder archives |
| S03E03 | Station 14-Threshold, Clive's origin memory |
| S03E08 | The Wellspring (full), Barry alive, Aether as Keeper, Builder Broadcast |
| S03E12 | All remaining 🔴 entries |

**Transmissions → Atlas (gradual annotation):**

Transmissions do not unlock entries. When a transmission names or describes an atlas concept, the atlas entry gains an "as heard in transmission" annotation — a breadcrumb, not a full unlock.

### 7.3 Season-Gated Content Strategy

| Season | Atlas State | Crew Page State | Transmission State |
|--------|------------|-----------------|-------------------|
| S1 (Launch) | Sparse. ~30 visible entries. Frequencies, crew basics, artifacts, places. Builder Stations are mostly dark. | Full S1 arcs visible. S2/S3 hidden. Barry's page: silhouette. | S1 transmissions (50 total). Weekly publishing. |
| S2 | Growing. ~45 visible entries. Builder history, stations open, Barry trail visible. | S2 arcs visible. Builder origins, Keeper nature. Barry has a real page. | S2 transmissions. Klaus investigating. Zephyr hearing Aether. |
| S3 | Complete. All ~64 entries visible. Full web of connections. | All arcs visible. Full memory. Complete character pages. | S3 transmissions. Full ensemble. Barry at Wellspring. |

### 7.4 Spoiler Tier Implementation

**Three tiers, three visual treatments:**

| Tier | Atlas Map | Entry Page | Cross-Link |
|------|-----------|------------|------------|
| 🟢 Safe | Bright glowing node | Full content visible | Normal clickable link |
| 🟡 S2 Gated | Dim node, faint pulse | Title + one-line teaser in static text: *"Signal not yet received..."* | Static text: *"This signal has not been received yet."* |
| 🔴 S3 Deep Lock | Pulsing dot, no label | No title, no teaser. Silent presence. | *"[unknown signal]"* |

**Multi-tier entries** (e.g., Clive: 🟢/🟡/🔴) show their visible tier and locked indicators for deeper tiers. The entry grows as locks open.

---

## 8. SEO & Metadata

### 8.1 Open Graph Tags Per Content Type

**Games:**
```html
<meta property="og:type" content="website" />
<meta property="og:title" content="{game.title} — The Ephergent" />
<meta property="og:description" content="{game.tagline}" />
<meta property="og:image" content="https://ephergent.com{game.thumbnail}" />
<meta property="og:url" content="https://ephergent.com/games/{game.slug}/" />
```

**Crew:**
```html
<meta property="og:type" content="profile" />
<meta property="og:title" content="{crew.name} — The Ephergent Crew" />
<meta property="og:description" content="{crew.role}. {crew.voice_summary}" />
<meta property="og:image" content="https://ephergent.com{crew.portrait}" />
```

**Lore/Atlas entries:**
```html
<meta property="og:type" content="article" />
<meta property="og:title" content="{entry.title} — Ephergent Lore Atlas" />
<meta property="og:description" content="{first 160 chars of safe-tier content}" />
<!-- No spoiler content in OG tags — always use safe tier only -->
```

**Transmissions:**
```html
<meta property="og:type" content="article" />
<meta property="og:title" content="{transmission.title} — {character.name}" />
<meta property="og:description" content="{transmission.excerpt}" />
<meta property="og:article:author" content="{character.name}" />
<meta property="og:article:published_time" content="{transmission.date}" />
```

### 8.2 Sitemap Strategy

Auto-generated `sitemap.xml` at build time. Includes:
- All game landing pages (not `/play/` pages — those are app-like, not content pages)
- All crew pages
- All visible (🟢 Safe) atlas entries
- All published transmissions
- Static pages: `/`, `/about/`, `/games/`, `/crew/`, `/atlas/`, `/transmissions/`

**Excluded from sitemap:**
- `/play/` pages (game embeds, not crawlable content)
- 🟡/🔴 gated atlas entries (content is in HTML but semantically not "published" yet)

### 8.3 RSS Feed

**URL:** `/rss.xml`

**Scope:** Transmissions only (the blog-like, chronological content).

**Feed items include:**
- Title
- Author (character name)
- Publication date
- Excerpt
- Link to full transmission page

**Update cadence:** Weekly, matching transmission publishing schedule.

---

## 9. Content Pipeline

### 9.1 Phase → Site Mapping

| Phase | Output | Site Destination | Collection |
|-------|--------|-----------------|------------|
| Phase 1 — World | Frequency system, Builder civilization, stations field guide, glossary | `src/content/lore/*.md` | `lore/` |
| Phase 2 — Characters | Character profiles (Pixel, A1, Clive, Zephyr, Luminara, Om Kai, Klaus, Nano, Meatball, Mochi, Barry) | `src/content/crew/*.md` | `crew/` |
| Phase 3 — Seasons | Episode outlines, season arcs (16 eps/season × 3 seasons) | Crew page season arc blocks, atlas unlock schedule | Indirect — informs `crew/` and `lore/` gating |
| Phase 4 — Episodes | Full episode scripts, amendments | Not published directly — drives transmission and atlas content | Indirect |
| Phase 5 — Games | 6 game design bibles + HTML5 exports | `src/content/games/*.md` + `public/games/{slug}/` | `games/` |
| Phase 6 — Transmissions | 50 S1 transmissions (Hermes agents) + format guide | `src/content/transmissions/*.md` | `transmissions/` |
| Phase 7 — Site | This document, tech notes, atlas structure | Site architecture itself | N/A |

### 9.2 Markdown → Astro Content Collection Workflow

```
Phase document (e.g., phase_02_characters/clive.md)
  ↓
Extract content relevant to collection schema
  ↓
Create collection entry: src/content/crew/clive.md
  - Add required frontmatter (slug, name, role, etc.)
  - Structure body content by spoiler tier sections
  - Add cross-reference fields (games_featured, lore_links)
  ↓
Validate against collection schema (src/content/config.ts)
  ↓
Build: import.meta.glob picks up the entry
  ↓
Deploy: static page generated at /crew/clive/
```

**Key rules:**
- Phase documents are source-of-truth. Collection entries are derived.
- Never modify Phase documents to match the site schema — always derive forward.
- Frontmatter schemas defined in `src/content/config.ts` are the validation boundary.
- Use `import.meta.glob` with `{ eager: true }` in all `getStaticPaths()` functions. Never `getCollection()`.

### 9.3 Image/Asset Pipeline

```
src/
  content/          # Markdown content (processed by Astro)
  assets/           # Images processed by Astro (optimized, responsive)
    crew/           # Character portraits
    games/          # Game thumbnails and screenshots
    atlas/          # Atlas icons, section headers
    transmissions/  # Character avatars for transmission cards

public/
  games/            # Game HTML5 exports (copied as-is, NOT processed)
    meatballs-big-walk/
      index.html
      *.wasm
      *.pck
    tune-the-dial/
      index.html
      ...
    static-run/
      index.html    # Phaser.js — smaller footprint
      ...
  images/           # Static images that don't need Astro processing
    og/             # Open Graph images per content type
  favicon.ico
  robots.txt
```

**Game assets (Godot exports):** Must live in `public/games/{slug}/` — they are served as-is. Astro does not process them. Each game export must be ≤ 15MB total. Measure with `du -sh public/games/{slug}/` after every export.

**Character portraits and thumbnails:** Live in `src/assets/` for Astro image optimization (responsive sizes, WebP conversion).

---

## Appendix A: File Structure Summary

```
src/
  content/
    config.ts                   # Collection schemas (games, crew, lore, transmissions)
    games/
      meatballs-big-walk.md
      tune-the-dial.md
      static-run.md
      the-laughing-funeral.md
      builder-station.md
      the-wellspring.md
    crew/
      pixel-paradox.md
      a1.md
      clive.md
      zephyr-glitch.md
      luminara-usha.md
      om-kai.md
      baron-klaus.md
      nano.md
      meatball.md
      mochi.md
      barry-kowalski.md
    lore/
      # ~64 entries across 7 sections
      prime-material.md
      nocturne-aeturnus.md
      the-drift.md
      station-3-resonant.md
      clive-atlas.md            # Atlas version (separate from crew/ entry)
      barry-kowalski-atlas.md
      ...
    transmissions/
      s1-w01-pixel-paradox.md
      s1-w01-a1.md
      s1-w02-pixel-paradox.md
      s1-w02-clive.md
      s1-w02-meatball.md
      ...                       # 50 S1 transmissions total
  pages/
    index.astro                 # Landing page
    about.astro
    games/
      index.astro               # Games hub
      [slug]/
        index.astro             # Game landing (getStaticPaths via import.meta.glob)
        play.astro              # Game embed
        about.astro             # Game info
    crew/
      index.astro               # Crew hub
      [slug].astro              # Crew profile (getStaticPaths via import.meta.glob)
    atlas/
      index.astro               # Atlas hub + visual map
      [section]/
        index.astro             # Section listing
        [slug].astro            # Entry page (getStaticPaths via import.meta.glob)
    transmissions/
      index.astro               # Feed page (filterable)
      [slug].astro              # Transmission page (getStaticPaths via import.meta.glob)
    rss.xml.js                  # RSS feed generator
  components/
    layout/
      Header.astro
      Footer.astro
      MobileNav.astro
    games/
      GameCard.astro
      GameEmbed.astro           # Iframe/canvas wrapper
    crew/
      CrewCard.astro
      CrewProfile.astro
      SpoilerBlock.astro        # Season-gated content block
    atlas/
      AtlasMap.astro            # Visual node map
      EntryCard.astro           # Entry preview (handles lock states)
      SpoilerGate.astro         # Client-side localStorage check
      CrossLinks.astro          # Link web at entry footer
      UnlockNotice.astro        # "New signal received" notification
    transmissions/
      TransmissionCard.astro
      CharacterFilter.astro
      TransmissionNav.astro     # Prev/next navigation
```

## Appendix B: Astro Technical Reminders

1. **Never use `getCollection()` in `getStaticPaths()`.** Use `import.meta.glob` with `{ eager: true }`.
2. **15MB hard cap per game.** Measure with `du -sh` after every Godot export.
3. **No nautical metaphors.** Fly, dock, hangar, cockpit. Never sail, anchor, port, starboard, helm.
4. **No removed antagonists.** Corporate Corp / The Board were removed. Do not reference.
5. **Canvas resize policy.** Godot embeds must use `canvas_resize_policy=2` (adaptive).
6. **All state is localStorage.** No server. No database. No accounts.
7. **Schema validation.** Hermes agent output must match `transmissions/` schema exactly. Bad frontmatter breaks the build.

---

*This document maps every piece of content from Phases 1–7 into ephergent.com's page tree, content collections, and progressive revelation system. It is the capstone planning document for site development.*

*When in doubt, read this document, then `astro_technical_notes.md`, then `lore_atlas_structure.md`.*
