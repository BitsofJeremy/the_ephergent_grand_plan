# Terminal Spec — Ephergent Signal Station

## What It Is

The terminal is the primary interface of ephergent.com — an art piece, not a utility. Full commitment to the aesthetic: IBM 3270 mainframe meets deep-space radio telescope. Signal the Narrator is always present, watching, narrating.

---

## Signal's Voice

Third-person past tense. Warm but distant. Theatrical but not overwrought. Meta-aware ("if you're keeping track") but cannot intervene — only witness.

Sample lines:
- Boot: *"The terminal hums to life. Signal has been waiting."*
- Navigate: *"And so the frequency shifts. Now at /transmissions. Signal is watching."*
- Locked content: *"That frequency is still being written. Signal cannot reveal what hasn't happened yet."*
- Episode intro: *"And so we return to the beginning."*

---

## Aesthetic — CRT Phosphor Terminal

**Not a modern dark theme.** Old-school phosphor terminal.

**Color palette:**
| Role | Hex | Use |
|------|-----|-----|
| Background | `#08080d` | Base |
| Foreground | `#e8e8f0` | Body text |
| Amber | `#ffb020` | Signal, warnings, labels |
| Cyan | `#00d4ff` | Interactive elements, links, commands |
| Green | `#00e676` | Success, online status |
| Red | `#ff4444` | Errors |
| Dim | `#606080` | Secondary text, borders |

**CRT effects:**
- Scanlines (fixed overlay, non-interactive)
- Vignette (radial gradient darkening at edges)
- Phosphor glow (ambient cyan radial)
- Subtle flicker (respects `prefers-reduced-motion`)

**Typography:** JetBrains Mono — no Inter, no sans-serif. Monospace only.

---

## Navigation Model

Unix-style terminal commands:
- `cd [path]` — navigate frequency archive
- `ls` — list current directory contents
- `cat [slug]` — read content (episode, lore, crew)
- `pwd` — print working directory
- `help` — show command reference
- `clear` — reset terminal view

**Virtual filesystem:**
```
/                       — Station root
/transmissions          — Episode broadcast archive (30 episodes)
/atlas                  — Lore database (27 entries)
/crew                   — Crew manifest (12 profiles)
/games                  — Interactive frequencies (6 games)
/signal                 — Signal's domain (about Signal)
```

---

## Content Locking

| Frequency | Status | Behavior |
|-----------|--------|----------|
| S01E01–S01E10 | ARCHIVED | Full access |
| S02E01–S02E10 | LOCKED | "Narrative incomplete. Signal cannot reveal what hasn't happened yet." |
| S03E01–S03E11 | LOCKED | "Story still unfolding. The frequencies are patient." |

---

## Architecture

### Current (v1 — static, deployed)

The terminal is a static Astro page (`src/pages/terminal.astro`). Client-side JavaScript handles commands. No backend. Works offline.

- Signal's voice is embedded in the page JS
- `VISIBLE_EPISODES` array determines what's shown
- Commands route to existing pages (`/`, `/transmissions/`, `/crew/`, `/atlas/`, `/games/`)

### Attempted (v1.5 — reverted)

Full commitment: FastAPI backend + xterm.js SPA. Was reverted due to:
- Backend content service had runtime file parsing issues
- Nginx WebSocket proxy config was incomplete
- CDN xterm.js was blocked by browser extension (Firefox lockdown)
- WebGL addon had 404 on jsdelivr

Key artifacts preserved in git history:
- `api/` — FastAPI backend (commit `8556309`)
- `public/terminal/lib/` — local xterm.js CDN (commit `a17a746`)
- `src/pages/terminal.astro` (SPA version, commit `8556309`)

### Recommended for v2

1. **Keep terminal as static Astro page** — no xterm.js dependency for basic function. The original `terminal.astro` with client-side JS already works.
2. **Add backend as optional layer** — terminal degrades gracefully when API is down.
3. **Host xterm.js locally** — `public/terminal/lib/` (already done).
4. **Backend reads pre-generated content** — generate `content.json` at build time from Astro content collections. No runtime file parsing.
5. **nginx config requirements:**
   - `/ws/` — `proxy_read_timeout 86400s`, `Upgrade` + `Connection` headers
   - `/sse/` — `proxy_cache off`
   - `/api/` — standard proxy

---

## Technical Notes

### xterm.js (for SPA revival)
- Version: 5.5.0 (npm `@xterm/xterm`)
- Addons: `addon-fit@0.10.0`, `addon-web-links@0.11.0`
- WebGL addon (`@xterm/addon-webgl@0.11.0`) — **broken on jsdelivr, 404**. Host locally or use canvas renderer only.
- Local copies at: `public/terminal/lib/`

### FastAPI Backend Endpoints
```
GET  /api/v1/boot           — session + boot sequence
GET  /api/v1/content/{type} — list content
GET  /api/v1/content/{type}/{slug} — single item with raw markdown
POST /api/v1/command        — execute terminal command
WS   /ws/terminal           — real-time terminal I/O
GET  /sse/signal/{session_id} — Signal narration stream
GET  /health                — health check
```

### Session State
```python
@dataclass
class Session:
    session_id: str
    cwd: str = "/transmissions"
    history: list[str] = field(default_factory=list)
    last_viewed: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

### Signal Voice Engine
Located at `api/services/signal.py` (git history). Key methods:
- `boot_sequence()` — lines shown on connect
- `help_text()` — ASCII box command reference
- `locked_content()` — random "that frequency is locked" message
- `episode_intro()` — random intro line before episode content
- `format_header()` — box-drawing character header for content
- `format_list()` — ASCII table for directory listings
- `interjection()` — context-aware Signal interjections
- `cat_file()` — format content for display

### PWA
- Service worker: `public/terminal/sw.js`
- Manifest: `public/terminal/manifest.json`
- Icon: `public/terminal/icon-192.svg`

---

## Git History Reference

| Commit | Description |
|--------|-------------|
| `be738d4` | Current — static site, no backend |
| `edcd698` | Pre-refactor backup (same as above) |
| `a17a746` | fix: serve xterm.js assets locally |
| `8556309` | feat: terminal SPA with FastAPI backend (reverted) |
| `f4a72c1` | docs: add deploy guide for VPS terminal refactor |
| `backup-pre-terminal-refactor` | Branch — pre-refactor state |

---

## Rollback

To revert to backup:
```bash
git reset --hard backup-pre-terminal-refactor
npm run build
```

To examine the full terminal SPA + FastAPI attempt:
```bash
git show 8556309 --stat
git log 8556309..be738d4 --oneline  # what's gone
```