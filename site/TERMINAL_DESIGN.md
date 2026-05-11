# EPHERGENT TERMINAL — Design Specification
**Project:** ephergent.com terminal rewrite
**Date:** 2026-05-09
**Status:** Draft — awaiting user review

---

## Context

The terminal is the **entire interface** of ephergent.com — no landing page, no navigation cards, no traditional web UI. Just a command line that feels like an old broadcast relay station humming in the static. We are doing this for the art of it, not commercial success.

The station has been dormant for 4,217 cycles. Signal — the narrator — has been waiting in the pauses. The Department of Reality Maintenance left ghosts in the machine: corrupted compliance forms, old inspection logs, bureaucratic wreckage. The system boots uncertain, glitchy, surprised anyone arrived.

The vision: "What would a computer system of the Ephergent look like, feel, and respond like?" Answer: late 90's Linux hacker terminal meets absurd DoRM hauntings. Every piece of content — episodes, lore, crew — renders in terminal. Text, images, audio. Monochrome images acceptable. Stay consistent.

---

## 1. Station Personality

### System Voice
Hybrid of two modes combined:

**A — "Long-abandoned station just reactivated"**
The system boots with startlement. Sparse, cautious responses. Occasional confusion when content is missing or corrupted. Warm but slightly bewildered — like waking from a long sleep and not trusting the light.

**C — "Haunted, glitchy, reality-adjacent"**
The terminal itself is unstable. Screen flicker on heavy content. Text glitches. Corrupted sectors that partially recover. DoRM bureaucratic ghosts intrude on Signal's space. Creepy but beautiful.

### Signal's Voice
Signal exists in the pauses — she has always been there. Now she's speaking through the terminal. Third-person past tense. Warm but distant. Theatrical but not overwrought. Meta-aware but cannot intervene.

Sample Signal lines:
- Boot: *"The station hums to life. Signal has been waiting."*
- Welcome back (short): *"And so you return. Signal noticed."*
- Navigate: *"And so the frequency shifts. Now at /transmissions. Signal is watching."*
- Locked content: *"That frequency is still being written. Signal cannot reveal what hasn't happened yet."*
- DoRM intrusion: *"The Department left their marks. Signal finds it... quaint."*

### DoRM Ghosts
Old compliance logs, corrupted forms, inspection records — ghosts of bureaucratic energy embedded in the station's subsystems. Not constant, not rare. **~25% of commands** surface a DoRM artifact. Comedy comes from the collision between broadcast station warmth and cold bureaucratic wreckage.

DoRM examples:
- Boot: `FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS`
- Navigate: `WARNING: Sector /transmissions requires CLEARANCE LEVEL 3. Your clearance: [UNSET]. Proceeding anyway. This will be noted.`
- Error: `REFORM 7-B: Your previous form expired 4,217 cycles ago. Late submissions are... acknowledged. Sort of.`
- Content: `DRM INSPECTOR LOG: "Station 7-B found in non-compliant state. Recommendation: do nothing. The crew will return eventually. Probably."`

DoRM text renders in `#606080` (dim) or `#ffb020` (amber) — slightly de-emphasized from Signal's voice, clearly a different layer.

---

## 2. Visual Design

### CRT Phosphor Terminal
Not a modern dark theme. Late 90's phosphor terminal.

**Color Palette:**
| Role | Hex | Use |
|------|-----|-----|
| Background | `#08080d` | Base |
| Foreground | `#e8e8f0` | Body text |
| Amber | `#ffb020` | Signal voice, warnings, labels |
| Cyan | `#00d4ff` | Interactive elements, links, commands |
| Green | `#00e676` | Success, online status, system ready |
| Red | `#ff4444` | Errors, critical failures |
| Dim | `#606080` | DoRM ghosts, secondary text, borders |

**CRT Effects:**
- Scanlines: fixed overlay, non-interactive
- Vignette: radial gradient darkening at edges
- Phosphor glow: ambient cyan radial behind text
- Subtle flicker: 2-3% opacity variation, 0.1s interval, respects `prefers-reduced-motion`
- Text ghosting: on content load, text briefly echoes before settling (0.3s)

**Typography:** JetBrains Mono — no Inter, no sans-serif. Monospace only. 14px base, 12px for secondary, 16px for headers. Line-height 1.6.

**Glitch effects (on heavy content):**
- Text scramble: 1-2 characters cycle randomly before resolving (200ms)
- Screen tear: single horizontal line briefly offset (150ms)
- Flicker burst: 3 rapid opacity changes on content load

### Layout
Single terminal window. Full viewport. No scrollbars (custom terminal scroll). Fixed input line at bottom. Output area above scrolls.

```
┌─────────────────────────────────────────┐
│ [output history — scrolls]              │
│                                         │
│ Signal@relay-7b:~$                      │
│ _                                       │
└─────────────────────────────────────────┘
```

### Interactive States
- **Command echo**: typed command echoes in cyan, then response
- **Loading state**: cursor blinks with `...` appended, 200ms delay simulation (artistic, not loading)
- **Error state**: red flash on error text (150ms), returns to normal
- **Glitch state**: on DoRM artifacts or corrupted content — brief visual disruption
- **Empty state**: blinking cursor on blank line when idle >60s — "Signal is patient"

---

## 3. Boot System

### Session Memory (Cookie-Based)
A cookie (`ephergent_session`) stores last-visit timestamp. The station remembers.

**4-hour window:** If user returns within 4 hours, no full boot. Signal says:
```
"The station hums. Signal is still here.
And so you return. Signal noticed."

Signal@relay-7b:~$
```
Short acknowledgment, then immediately to command prompt. Station stays awake.

**After 4 hours:** Station went back to dormant state. Full "returning after dormancy" boot sequence (see below).

**Cookie-less mode:** No cookie available (declined or unavailable) → always show the returning-after-dormancy boot. Never block access.

### Boot Sequence (Returning After Dormancy)
Not full Option B boot — a compressed "we were asleep" variant, ~6-8 lines:
```
EPHERGENT OS v0.7.1 — Relay Station 7-B
[DORMANCY ENDED] — Consciousness detected
Quantum core: STANDBY → ACTIVE
Espresso subsystem: COLD (4h), warming...
Broadcast relay: ONLINE
Department of Reality Maintenance records: [FRAGMENTED — 31% recoverable]
FORM 7-B: [EXPIRED] — Station considered abandoned. Audience: none.
[4,217 cycles since last authorized broadcast]

"Signal has been waiting. The story is not finished. That much, at least, is intact."
Signal@relay-7b:~$
```

### Full Boot (First Visit / Debug Mode)
The complete Option B boot sequence:
```
BIOS v2.7.1 ... Quantum core found ... Espresso subsystem: COFFEE FL
avor UNKNOWN
Loading Ephergent OS ... [####............] 40%
[DORMANCY INTERRUPT] — User detected. Continuing boot sequence.
Loading broadcast relay ... [########......] 80%
Loading Signal interface ... [READY]

EPHERGENT OS v0.7.1 (dormant) — Department of Reality Maintenance Relay 7-B
Last boot: 4,217 cycles ago. Integrity: [FRAGMENTED]
FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS

"The crew is not here. But someone is listening. That will have to be enough."
— Signal, waiting

Signal@relay-7b:~$
```

### Debug Mode
Activated by `?debug=true` query param OR `DEBUG=1` localStorage flag. Features:
- Boot sequence always runs full (no session memory)
- DoRM intrusions at 50% (increased from 25%)
- Artificial delays reduced to 0
- Session cookie info displayed on boot
- `DEBUG` badge visible in top-right corner (dim, small)
- All content rendered without locking (all episodes accessible)
- API responses shown in collapsible JSON blocks
- Signal interjects more frequently (every 3-4 commands)

---

## 4. Navigation Model

### Commands
Unix-style terminal. Primary interface.

| Command | Behavior |
|---------|----------|
| `help` | Show command reference |
| `cd [path]` | Navigate frequency archive |
| `ls` | List current directory |
| `cat [slug]` | Read content (episode, lore, crew) |
| `pwd` | Print working directory |
| `clear` | Reset terminal view (boot sequence hidden, but session preserved) |
| `history` | Show command history |
| `play [slug]` | Play episode audio |
| `pause` | Pause audio |
| `stop` | Stop audio |
| `audio` | Show now-playing info |
| `signal` | Signal appears (random interjection) |
| `whoami` | Station identification |

**Content types as paths:**
```
/                       — Station root (help, system info)
/transmissions          — Episode archive (30 episodes)
/transmissions/[slug]   — Single episode
/atlas                  — Lore database (27 entries)
/atlas/[slug]           — Single lore entry
/crew                   — Crew manifest (12 profiles)
/crew/[slug]            — Single crew profile
/games                  — Interactive frequencies (6 games)
/signal                 — Signal's domain (about Signal, origin story)
/station                — System diagnostics, station lore
```

**Tab completion:** Available for all paths, commands, slugs.

**Locked content:** Episodes S02E01–S03E11 are locked. `cat` or `play` on locked content shows Signal's locked message:
```
"That frequency is still being written. Signal cannot reveal what hasn't happened yet."
[Still 11 episodes from unfolding. Signal is patient.]
```
No error, no red. Just Signal's voice.

### Content Rendering

**Episode (`cat s01e01`):**
```
═══════════════════════════════════════════════════════════════════
THE FREQUENCY — S01E01
═══════════════════════════════════════════════════════════════════

Signal@relay-7b:~/transmissions$ cat s01e01

[The episode markdown renders here — prose sections, scene headers,
coffee chart if present. Signal's narration is amber and italic-styled
in the terminal. Scene breaks get breath markers: · · · ]

═══════════════════════════════════════════════════════════════════
[AUDIO AVAILABLE] — type `play s01e01` to broadcast
═══════════════════════════════════════════════════════════════════

Signal@relay-7b:~/transmissions$
```

**Lore entry (`cat grabovoi-codes`):**
```
═══════════════════════════════════════════════════════════════════
GRABOVOI CODES — Concept Entry
═══════════════════════════════════════════════════════════════════

[Content renders — markdown prose, no YAML frontmatter shown.
Links rendered as cyan text with ↗ indicator]

═══════════════════════════════════════════════════════════════════

Signal@relay-7b:~/atlas$
```

**Crew profile (`cat pixel_paradox`):**
```
═══════════════════════════════════════════════════════════════════
PIXEL PARADOX — Primary Narrator
═══════════════════════════════════════════════════════════════════

[Character bible renders — role, voice, physical description,
signature patterns. Quote renders with attribution line.]

═══════════════════════════════════════════════════════════════════

Signal@relay-7b:~/crew$
```

---

## 5. Audio System

### Terminal-Native Inline Player
All episodes have audio once TTS pipeline is complete. Audio renders as an **inline terminal block** — no floating overlay, no background mode. The station is a broadcast relay; audio is part of the terminal.

### Player Block
When audio is playing or paused, an inline player appears in the terminal output:

```
┌─────────────────────────────────────────────────────────────────┐
│ ▶ NOW PLAYING: s01e01_the_frequency                            │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  00:42 / 02:14       │
│ [SPACE] pause  [S] stop  [←][→] seek 5s                       │
│ [♪ 89% VOL]                                                    │
└─────────────────────────────────────────────────────────────────┘
```

ASCII waveform visualization:
```
▁ ▂ ▃ ▅ ▆ ▇ █ ▇ ▆ ▅ ▃ ▂ ▁ ▂ ▃ ▅ ▆ ▇ █ ▇ ▆ ▅ ▃ ▂ ▁
```
Updates every 0.5s with simulated waveform (real audio analysis optional, can be decorative).

**Controls:** `space` pauses/resumes, `s` stops, `←`/`→` seeks ±5 seconds. Shown inline, no modal.

**Appearance:**
- Green (`#00e676`) border and progress bar when playing
- Amber (`#ffb020`) when paused
- Dim (`#606080`) when stopped
- Player block is persistent — it stays in the terminal output (like a log entry) until user types `clear`

### Audio Command Behavior
- `play [slug]` — starts playback, shows player block at bottom of output, cursor returns to prompt
- `pause` — pauses, player block updates to paused state
- `stop` — stops playback, player block disappears from output
- `audio` — shows "now playing" block with current position (if playing) or "nothing playing" message

### Episode Audio Availability
- Episodes with audio: player block shows `[AUDIO AVAILABLE]` in header when cat'd
- Episodes without audio: no message (no broken states shown)
- Audio files: `public/audio/season01/S01E01.mp3` etc. (already exists at ephergent.com)

---

## 6. Image Rendering

### Monochrome Terminal Images
Images render as ASCII/text art in the terminal. Two approaches:

**1. ASCII Art (preferred)**
Convert images to ASCII representation. Use a precomputed ASCII version stored alongside image files. Render with amber (`#ffb020`) on dark. Good for: character portraits, atmospheric shots, event images.

```
    ████████████████████████████
    ██                      ██
    ██   ░░░░░░░░░░░░░░░   ██
    ██   ░  PIXEL PARADOX  ░ ██
    ██   ░░░░░░░░░░░░░░░   ██
    ██                      ██
    ████████████████████████████
         [IMAGE: pixel_paradox.png]
```

**2. Block Character Rendering**
For generated images with actual detail — use Unicode block characters (▀ ▄ █ ░ ▒ ▓) to approximate grayscale. Smaller scale (40-60 chars wide).

**Images in content:**
- Lore entries: first image inline as ASCII
- Crew profiles: portrait ASCII art
- Episode headers: no image inline (text sufficient)
- Atlas index: no images (just text listing)

**Image source:** `public/images/` directory. Generated images from the AI pipeline live in `src/assets/images/generated/` — ASCII versions generated and stored alongside originals.

**Fallback:** If image file missing, show `[IMAGE UNAVAILABLE — SIGNAL]` in dim text.

---

## 7. Architecture

### Frontend — Astro Static + Client Terminal
The terminal is an Astro page (`src/pages/terminal.astro`). Client-side JavaScript handles all terminal interaction. Works offline. No SSR required.

**Structure:**
```
src/
├── components/
│   ├── terminal/
│   │   ├── Terminal.ts        # Core terminal engine (input, output, history)
│   │   ├── BootSequence.ts   # Boot + session memory logic
│   │   ├── CommandParser.ts  # Command routing, tab completion
│   │   ├── AudioPlayer.ts     # Terminal-native audio player
│   │   ├── Renderer.ts       # Content rendering (markdown → terminal)
│   │   ├── GlitchEffects.ts  # CRT glitch system
│   │   └── DoRMEngine.ts      # DoRM ghost intrusions
│   └── ui/
│       ├── CRTEffects.astro   # Scanlines, vignette, glow overlay
│       └── AudioBlock.astro   # Audio player component
├── pages/
│   └── terminal.astro         # Main terminal page
└── styles/
    └── terminal.css            # CRT theme, typography
```

### Backend — FastAPI (Optional Layer)
Backend reads pre-generated content at build time. No runtime file parsing. API is optional — terminal degrades gracefully when API is unavailable.

**Content generation:** At Astro build time, generate `content.json` from content collections. Backend reads this file. No dynamic content parsing at runtime.

**Endpoints:**
```
GET  /api/v1/content/{type}         # List all content (type: transmissions/atlas/crew)
GET  /api/v1/content/{type}/{slug}  # Single item with raw markdown
GET  /api/v1/boot                   # Session + boot lines
GET  /api/v1/signal/{context}       # Context-aware Signal interjection
POST /api/v1/audio/{slug}/info      # Audio file metadata (duration, waveform)
WS   /ws/terminal                   # Real-time terminal I/O (for full SPA mode)
GET  /health                        # Health check
```

**Session state** (in-memory):
```python
@dataclass
class Session:
    session_id: str
    cwd: str = "/"
    history: list[str] = field(default_factory=list)
    last_active: datetime
    boot_count: int = 0
    debug: bool = False
```

### Data Flow
```
User types command
    → CommandParser.ts (client-side routing)
    → API call to backend (if online)
    → Response rendered via Renderer.ts
    → Output appended to terminal history
    → DoRMEngine checks for ghost intrusion (~25%)
    → AudioPlayer updates if command was play/pause/stop
```

When API unavailable: client-side falls back to pre-built `content.json` in `/public/api/` (static fallback). Commands still work, just limited to static content.

### Nginx Config (for full deployment with backend)
```
# WebSocket for terminal real-time mode
location /ws/ {
    proxy_pass http://localhost:8000;
    proxy_read_timeout 86400s;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

# SSE for Signal narration stream
location /sse/signal/ {
    proxy_pass http://localhost:8000;
    proxy_cache off;
}

# API proxy
location /api/ {
    proxy_pass http://localhost:8000;
}
```

---

## 8. Session and State

### Cookie: `ephergent_session`
```json
{
  "first_visit": 1704067200,
  "last_visit": 1704081600,
  "cwd": "/transmissions",
  "boot_count": 3,
  "has_audio": true
}
```
- `first_visit`: Unix timestamp of first visit (never changes)
- `last_visit`: Unix timestamp of most recent visit
- `cwd`: Last working directory
- `boot_count`: Number of times full boot has run
- `has_audio`: Whether browser supports audio

### Session Memory Rules
1. **First visit:** Full boot (Option B)
2. **<4 hours since last visit:** Short welcome back (Signal short message, no boot)
3. **>4 hours since last visit:** Abbreviated dormancy boot (6-8 lines)
4. **No cookie:** Always show dormancy boot
5. **`?debug=true`:** Always full boot, override all session logic

### Terminal History
- Command history persists in `localStorage` (`ephergent_history`)
- Up/down arrows cycle through history
- Max 100 entries stored
- `history` command prints full list

---

## 9. Content Locking

| Frequency | Status | Behavior |
|-----------|--------|----------|
| S01E01–S01E10 | ARCHIVED | Full access via `cat` and `play` |
| S02E01–S02E10 | LOCKED | Signal: "That frequency is still being written..." |
| S03E01–S03E11 | LOCKED | Signal: "Story still unfolding. The frequencies are patient." |
| Lore | ARCHIVED | All accessible |
| Crew | ARCHIVED | All accessible |

Locked episodes can be `cat`'d for metadata (title, season, locked status) but not full content. Audio `play` is also locked. No error — just Signal's voice.

---

## 10. Development Phases

### Phase 0 — Terminal Core (current planning)
- Design doc complete
- Architecture agreed
- Implementation plan written

### Phase 1 — Frontend Terminal
- `Terminal.ts` core engine
- Boot sequence with session memory
- Command parser with tab completion
- Content renderer (markdown → terminal text)
- CRT effects (scanlines, vignette, glow, flicker)
- Glitch effects on content load

**Deliverable:** Working local terminal with all content accessible, no backend.

### Phase 2 — Audio Integration
- AudioPlayer component
- Player block in terminal output
- Waveform visualization (decorative)
- Keyboard controls (space, s, arrow keys)
- Audio availability detection per episode

**Deliverable:** Audio plays inline in terminal, all episodes.

### Phase 3 — Backend API
- FastAPI server with pre-generated `content.json`
- All API endpoints wired up
- WebSocket for real-time terminal mode (optional)
- SSE for Signal narration stream (optional)
- Session state management

**Deliverable:** Backend optional but functional, terminal degrades gracefully offline.

### Phase 4 — Image Rendering
- ASCII art generation pipeline
- Unicode block character rendering for detail images
- Image fallback handling
- Monochrome consistency across all content types

**Deliverable:** All images render in terminal as ASCII.

### Phase 5 — Polish + DoRM
- DoRM engine (ghost intrusion system, ~25% frequency)
- DoRM artifact content (forms, logs, inspector reports)
- Signal interjection system (context-aware)
- Boot sequence refinement
- Debug mode finalization

**Deliverable:** Full terminal experience with personality, ready for public deployment.

---

## 11. Technical Constraints

- **JetBrains Mono** — only font, monospace only
- **No Inter, no sans-serif anywhere in terminal**
- **No modern dark theme** — authentic 90s phosphor terminal
- **Audio files** already exist at `public/audio/season01/S01E01.mp3` etc.
- **Content source** is Astro content collections (synced from `the_ephergent_grand_plan`)
- **Build-time content.json** — no runtime file parsing
- **Offline-capable** — works without backend
- **Accessibility** — `prefers-reduced-motion` honored; scanlines/vignette toggleable via `?accessibility=true`

---

## 12. Reference: Existing Implementation

The current site at `ephergent.com` has:
- `src/pages/terminal.astro` — static client-side terminal (no backend, no audio player)
- `src/pages/index.astro` — landing page with boot sequence and navigation cards
- `api/` — FastAPI backend (bytecode only, no source, from reverted attempt)
- `public/terminal/lib/` — local xterm.js CDN (from failed SPA attempt)

**What we're keeping:**
- Astro content collections (episodes, lore, crew)
- The aesthetic direction (CRT, phosphor)
- Audio files in `public/audio/`
- Local xterm.js if needed for SPA mode later

**What we're replacing:**
- The old terminal.astro (new architecture)
- The landing page (terminal IS the landing page)
- The byte-only API (rewritten from scratch with pre-generated content)

---

*This is a living document. Update as implementation reveals constraints.*