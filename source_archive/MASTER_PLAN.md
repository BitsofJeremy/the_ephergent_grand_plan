# The Ephergent — Master Plan
*Before Greatness LLC · Strategic overview for LLMs and collaborators*

---

## Who This Is For

This document is the thousand-foot view of the entire Before Greatness LLC digital strategy as of April 2026. It is written for any LLM, agent, or human contributor picking up this work cold. Read this before touching anything else.

---

## The Pivot (April 2026)

Before Greatness LLC had been operating as a 3D-printed electronics storefront — saturated market, wrong fit. We pivoted hard. The new strategy:

**The Ephergent universe becomes the product. Games are the story. The story sells itself.**

No e-commerce. No physical products. Free forever. Immersive browser-playable games that are narrative delivery devices for a sci-fi universe.

---

## The Three Sites

### 1. beforegreatness.com
**Role:** Corporate umbrella. Minimal. Links to the other properties.  
**Status:** Live. Updated card copy to reflect games-as-story pivot.  
**Changes needed:** Almost none. Keep it clean and minimal.

### 2. jeremyschroeder.net
**Role:** Jeremy's personal devlog. Documents the build — Godot, world-building, design decisions.  
**Stack:** Astro 5 + Tailwind 3, static site, GitHub Actions → auto-deploy.  
**Status:** Live. Rewired away from 3D products. 5 live posts seeded:
- The Ephergent pivot announcement
- Universe world-building primer
- Godot 4 for storytellers (Python dev angle)
- Meatball's Big Walk design notes
- Hello World (rewritten)  

**Ongoing use:** Devlog posts as each game milestone is reached. Pipeline for this will be automated later via Hermes agents.

### 3. ephergent.com
**Role:** The story hub. Browser-playable games, crew profiles, lore atlas, transmissions (blog).  
**Stack:** Astro 5 + Tailwind 3, static site, GitHub Actions → auto-deploy.  
**Status:** Live. Full pivot complete. Storefront removed. Four content collections live:
- `games/` — 4 game entries
- `crew/` — 9 character profiles
- `lore/` — 3 lore entries (more to come)
- `transmissions/` — placeholder (Hermes agent posts will fill this)

**Content note:** `getCollection()` from `astro:content` fails in `getStaticPaths`. Use `import.meta.glob` instead everywhere. This is a known Astro 5 SSG quirk in this project.

---

## The Universe — The Ephergent

Full world bible lives in `the_ephergent_rebuild/ephergent_world/`. Five files: `WORLD_PLAYBOOK.md`, `dimensions.md`, `factions.md`, `timeline.md`, `glossary.md`.

**Elevator pitch:** Nine misfits aboard a living quantum lattice ship traversing a multiverse that exists as radio frequencies. Think *Firefly* meets *Welcome to Night Vale*, told through character-driven games and weekly blog dispatches.

### Core rules (do not violate)
- **Dimensions are frequencies** — not parallel worlds, not timelines. A cosmic dial from 1–5.
- **A1 is the ship** — an ancient quantum navigator self-compressed into an espresso machine, now reawakened as the ship itself. Use sci-fi vocabulary only: fly, dock, hangar, cockpit. **No nautical metaphors.**
- **The Drift is entropy** — not a villain, not a conspiracy. Frequencies naturally fade apart. The crew fights it by broadcasting signal.
- **Unaware Crew (Season 1)** — the crew starts not knowing other dimensions exist. Prime Material (freq 1) = our modern world. First contact with each frequency is a discovery, not a return.
- **No Corporate Corp / The Board** — these antagonists were removed in the 2026 refactor. Do not reintroduce them.

### The Nine Crew Members
| Character | Role | Voice |
|-----------|------|-------|
| Pixel Paradox | Captain/Engineer | Urgency, coffee, always figuring something out |
| A1 | The ship itself | Ancient, patient, warm; espresso reflects emotional state |
| Clive | Mechanic | Dry, practical, occasionally philosophical |
| Zephyr Glitch | Navigator | Looking for his brother Aether; emotional spine of S02 |
| Luminara Usha | Scientist | Precise, curious, slightly unsettling |
| Om-Kai | Engineer | Problem-solver; their wrench smells like answered questions |
| Baron Klaus | Diplomat/Wildcard | Theatrical, unreliable narrator |
| Nano | Tech specialist | Small, fast, thinks in systems |
| Meatball | Ship's dog | Earnest, oblique, dog-term framing; occasionally profound |

### Three Seasons
- **S01 — Emergence:** Crew unaware, escape in Form 27-B lifeboat, discover A1's true form mid-season
- **S02 — Resonance:** Expanded crew, lost frequencies, searching for Aether (Zephyr's brother)
- **S03 — The Source:** Full mythology revealed; 37 episodes written across all three seasons

---

## The Games Strategy

### Philosophy
Each game is a different genre matched to a different aspect of the story. Each has its own distinct visual style. They are not sequels — they are facets of the same universe. Players can enter from any game.

Every game page on ephergent.com links to the story and crew profiles. The games ARE the story delivery mechanism.

### Hard Constraints (locked decisions)
- **Free forever.** No paywalls, no IAP, no e-commerce.
- **Browser-playable.** Godot 4 HTML5 export, embedded in Astro pages via iframe.
- **15MB compressed hard cap** per game. (Godot baseline ~5MB, leaves ~10MB for content.)
- **Self-composed audio.** Jeremy composes all music/SFX. No licensed audio.
- **Each game has its own visual style.** No shared art direction between games.
- **Sci-fi vocabulary only.** No nautical metaphors anywhere in copy or game text.

### Tech Stack
- **Godot 4.3+** for narrative/exploration games (primary engine)
- **Phaser.js or GB Studio** for Static Run (the endless runner — lighter weight)
- **Astro 5** page embeds the HTML5 export via iframe, `canvas_resize_policy=2`
- **localStorage via JavaScriptBridge** for save state (no server-side persistence)
- **Export pipeline:** `Project → Export → Web` → measure `du -sh export/` → must be ≤15MB → copy to `ephergent.com/public/games/[slug]/`

---

## Phase 1 — The Four Games

### Game 1: Meatball's Big Walk ⬅ IN PROGRESS
**Genre:** Cozy point-and-click exploration  
**Engine:** Godot 4.3  
**Visual style:** Top-down 2D (Among Us perspective), 16-bit cozy pixel art, Stardew Valley warmth. 32×32 tiles, 24×32 character sprites. 13-color amber/brass palette.  
**Premise:** You are Meatball, the ship's dog. You walk around the engine room and sniff things. Each sniff triggers an internal monologue thought bubble. All 10 hotspots sniffed = completion.  
**Story function:** Introduces the ship, A1's espresso machine, the crew through Meatball's oblique dog-perspective. Gentle, cozy, 10-minute experience.  
**Size target:** ≤10MB compressed  

**Current state:**
- Godot project scaffold complete: `games/meatballs-big-walk/`
- All GDScript written: `Main.gd`, `StartScreen.gd`, `EngineRoom.gd`, `Meatball.gd`, `Hotspot.gd`, `ThoughtBubble.gd`, `AudioManager.gd`, `SaveManager.gd`
- Dialogue data complete: `data/hotspots.gd` (all 10 hotspots × 3 lines + completion dialogue)
- Placeholder sprites generated: `uv run gen_sprites.py` (22 PNGs, all with Flux prompts in docstrings)
- Art direction bible: `docs/MEATBALLS_BIG_WALK_ART_DIRECTION.md`
- **Blocking:** Final art assets (Jeremy → Aseprite or Flux/ComfyUI), audio loops (Jeremy self-composes), `.tscn` scene files (must be built in Godot editor)

**Meatball's voice rules:**
- Earnest and oblique; frames everything in dog terms
- Occasionally profound, never ironic
- 2–3 sentences max per thought bubble
- Example: *"This smells like: home, far away, and Tuesday."*

### Game 2: Tune-the-Dial
**Genre:** Puzzle / frequency tuner  
**Engine:** Godot 4 (or vanilla JS — TBD based on scope)  
**Visual style:** Retro oscilloscope UI, vector-green on black, CRT scan lines  
**Premise:** Player operates A1's navigation console, tuning through 5 frequencies to locate signal. Each frequency has a distinct audio signature and visual pattern. Puzzle deepens as frequencies interfere.  
**Story function:** Teaches the core universe mechanic (dimensions = frequencies). The homepage of ephergent.com has an interactive Tune-the-Dial hero section that previews this.  
**Size target:** ≤8MB  
**Status:** Concept + homepage preview only. Not started.

### Game 3: Static Run
**Genre:** Endless runner / reflex  
**Engine:** Phaser.js or GB Studio  
**Visual style:** GB-style 4-color monochrome, chunky pixels  
**Premise:** Nano sprints through The Drift — a decaying frequency corridor — dodging entropy fragments. The further you run, the more the world dissolves. High score = signal strength.  
**Story function:** Visceral introduction to The Drift as an environmental threat, not a villain. Fast, replayable, shareable.  
**Size target:** ≤5MB  
**Status:** Concept only. Not started.

### Game 4: The Laughing Funeral
**Genre:** Point-and-click adventure / mystery  
**Engine:** Godot 4  
**Visual style:** Gothic watercolor-ish — muted blues and purples, hand-drawn feel achieved in pixel art  
**Premise:** Baron Klaus investigates an impossible death aboard the ship at Nocturne Aeturnus (frequency 2, gothic twilight dimension). Classic adventure game inventory puzzles.  
**Story function:** First real encounter with another frequency; introduces Nocturne Aeturnus lore; character study of Baron Klaus as unreliable narrator.  
**Size target:** ≤12MB  
**Status:** Concept only. Not started.

---

## The Hermes Agent System

Nine character agents live in `ephergent_agents/`. Each has:
- `SOUL.md` — identity, voice, perspective (slot #1 in system prompt — primary control)
- `USER.md` — reader/user context
- `config.yaml` — Hermes Agent settings
- `AGENTS.md` — project-specific context
- `.env` — API keys, voice IDs, Telegram tokens

**Purpose:** Weekly blog dispatch posts to `ephergent.com/transmissions/` and `ephergent_blog/src/content/blog/[character]/`. Each character writes from their own perspective as if broadcasting from the ship.

**Pending infrastructure** (human tasks):
- VPS (moguera, 107.172.217.225) configured for Hermes
- Telegram bots activated per character
- Cron jobs scheduled via `ephergent_orchestrator/`
- DNS routing finalized

---

## The Comic Pipeline

Separate from games — a parallel output stream.

**Flow:**
1. Prose episodes (`ephergent_stories/`) → `prose_to_comic.py` → `.comic.yaml`
2. `.comic.yaml` → `panel_prompt_builder.py` → Flux prompts
3. Flux prompts → ComfyUI (RTX 3060, `http://comfyui.nexus.home.test/`) → PNG panels
4. PNG panels → `build_cbz.py` / `build_pdf.py` / `build_epub.py` → distributable files
5. Overnight pipeline: `uv run scripts/generate_pipeline.py`

**37 episodes written** across S01–S03. Comic conversion is a separate workstream from games.

---

## Infrastructure

| Component | Location | Status |
|-----------|----------|--------|
| beforegreatness.com | GitHub → auto-deploy | Live |
| jeremyschroeder.net | GitHub → auto-deploy | Live |
| ephergent.com | GitHub → auto-deploy | Live |
| moguera VPS | 107.172.217.225 | Earmarked for Phase 2 game hosting + Hermes |
| ComfyUI | `comfyui.nexus.home.test` (home GPU server, RTX 3060 12GB) | Live |
| Hermes Agents | 9 configs in `ephergent_agents/` | Configs ready, infra pending |
| Meatball's Big Walk | `games/meatballs-big-walk/` | Scripts + sprites done, art pending |

---

## What Needs to Happen Next

### Immediate (unblocked now)
1. Open Godot 4.3, load `games/meatballs-big-walk/project.godot`
2. Install Web export templates
3. Build `.tscn` scene files using the node tree in `games/meatballs-big-walk/README.md`
4. Run "hello cockpit" spike: empty scene → HTML5 export → measure baseline size

### Blocked on Jeremy (human tasks)
- Final pixel art for Meatball's Big Walk (Aseprite, or Flux prompts in `gen_sprites.py` docstrings → ComfyUI)
- Self-compose audio: `engine_room.ogg` (ambient loop), 4 SFX files
- Activate Telegram bots for Hermes agents
- Configure moguera VPS cron jobs

### Future (Phase 2+)
- Start Tune-the-Dial game design doc
- Start Static Run engine choice + prototype spike
- Set up Hermes agent weekly post pipeline end-to-end
- First real transmissions content on ephergent.com
- moguera as game file CDN for exports >15MB if needed

---

## Key File Index

```
the_ephergent_rebuild/
├── docs/
│   ├── MASTER_PLAN.md                    ← this file
│   ├── MEATBALLS_BIG_WALK_ART_DIRECTION.md  ← full art + game design bible
│   ├── GODOT_HTML5_PIPELINE.md           ← export pipeline reference
│   └── sprite_preview.png               ← generated placeholder sprite sheet
├── ephergent_world/
│   ├── WORLD_PLAYBOOK.md                 ← universe rules (read first)
│   ├── dimensions.md, factions.md, timeline.md, glossary.md
├── ephergent_agents/                     ← 9 Hermes agent configs
├── ephergent_stories/                    ← 37 prose episodes (S01-S03)
├── ephergent_blog/                       ← ephergent.com Astro site
├── AI_Docs/
│   └── PRD-ephergent-com-v2.md          ← full site spec
└── EPHERGENT_GAMES_BRAINSTORM.md        ← original concept doc + locked decisions

games/
└── meatballs-big-walk/
    ├── project.godot
    ├── gen_sprites.py                    ← uv run gen_sprites.py → regenerates all placeholder art
    ├── export_presets.cfg
    ├── scripts/                          ← all GDScript (complete)
    ├── data/hotspots.gd                  ← all 10 dialogue sets (complete)
    ├── assets/sprites/                   ← placeholder PNGs (replace with final art)
    └── README.md                         ← scene node tree + build instructions
```

---

## Guiding Principles

1. **The story is the product.** Games exist to deliver narrative, not as standalone entertainment products.
2. **Free forever.** Removing cost removes friction. The universe grows through reach, not revenue.
3. **Each entry point is complete.** A player who only ever plays Meatball's Big Walk should feel the universe — not like they're missing something.
4. **Meatball first.** Smallest scope, clearest voice, most novel concept. Ship this before anything else.
5. **Jeremy's voice on jeremyschroeder.net.** The devlog is personal. It documents real decisions, dead ends, and discoveries — not polished marketing.

---

*Last updated: April 2026*  
*Session: ephergent-games-pivot*
