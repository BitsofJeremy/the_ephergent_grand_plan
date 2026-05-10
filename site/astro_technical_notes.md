# Astro Technical Notes — ephergent.com

*Technical reference for site developers. Last updated: July 2025.*

---

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Astro 5 (static site generation) |
| CSS | Tailwind 3 |
| Hosting | Static files, auto-deployed via GitHub Actions |
| Game engine | Godot 4.3+ HTML5 export (primary), Phaser.js / GB Studio for lighter games |

SSG only — no server runtime, no SSR. Every page is pre-rendered at build time.

---

## Content Collections

Four collections live under `src/content/`:

| Collection | Purpose |
|------------|---------|
| `games/` | Game entries (4 at launch). Each entry includes metadata for the game page: slug, title, genre, engine, size, embed path, and story context. |
| `crew/` | 9 character profiles. Name, role, voice description, portrait, and lore links. |
| `lore/` | World-building entries — dimensions, factions, glossary fragments. Grows over time. |
| `transmissions/` | Blog-style posts authored by Hermes character agents. Weekly cadence. |

Each collection uses Astro content collection schemas defined in `src/content/config.ts`.

---

## The `import.meta.glob` Quirk

**This is the single most important technical note in this document.**

`getCollection()` from `astro:content` fails inside `getStaticPaths()` during SSG builds. This is a known Astro 5 quirk in this project. **Use `import.meta.glob` instead everywhere.**

### ❌ Broken pattern

```astro
---
// src/pages/games/[slug].astro
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const games = await getCollection('games');  // FAILS at build time
  return games.map((game) => ({
    params: { slug: game.slug },
    props: { game },
  }));
}
---
```

### ✅ Correct pattern

```astro
---
// src/pages/games/[slug].astro
const games = await Astro.glob('../content/games/*.md');

export async function getStaticPaths() {
  const games = import.meta.glob('../content/games/*.md', { eager: true });
  return Object.values(games).map((game) => ({
    params: { slug: game.frontmatter.slug },
    props: { game },
  }));
}
---
```

Use `import.meta.glob` with `{ eager: true }` for synchronous access to frontmatter. This applies to all four collections — games, crew, lore, and transmissions.

---

## Game Embedding

All games are Godot 4 HTML5 exports, browser-playable, **free forever**. No paywalls, no IAP.

### 15MB Per-Game Hard Cap

Godot baseline is ~5MB, leaving ~10MB for game content (art, audio, scripts).

**Enforcement pipeline:**

```bash
# After Godot export:
du -sh export/
# Must be ≤ 15MB. If over, reduce assets before proceeding.

# Deploy:
cp -r export/* public/games/[slug]/
```

Games are embedded in Astro pages via iframe with `canvas_resize_policy=2`:

```html
<iframe
  src="/games/meatballs-big-walk/index.html"
  width="100%"
  height="600"
  style="border: none;"
  allowfullscreen
></iframe>
```

### Allowed Engines

| Engine | Use case |
|--------|----------|
| Godot 4.3+ | Primary engine for narrative/exploration games |
| Phaser.js | Lighter games (e.g., Static Run endless runner) |
| GB Studio | Retro-style simpler games |

### Save State

`localStorage` via Godot's `JavaScriptBridge` — no server-side persistence.

---

## Hermes Agent Integration

Nine character agents (one per crew member) generate weekly transmissions — in-character blog posts written from each crew member's voice and perspective.

### Integration Points

1. **Content generation**: Hermes agents produce markdown files with valid frontmatter matching the `transmissions/` collection schema.
2. **File drop**: Generated `.md` files land in `src/content/transmissions/`.
3. **Build trigger**: A push to the repo (including agent-authored content) triggers GitHub Actions → rebuild → deploy.
4. **No runtime dependency**: The agents are Godot-adjacent — they feed content into the static build pipeline but do not run on the site itself.

Transmission frontmatter should include at minimum: `title`, `author` (crew member slug), `date`, `tags`, and `excerpt`.

---

## Deploy Pipeline

```
push to main → GitHub Actions → astro build → deploy static files
```

- Auto-deploy on every push. No manual steps.
- Build runs `astro build`, producing static output.
- Game assets live in `public/games/[slug]/` and are copied as-is to the deploy target.
- Content changes (new transmissions, lore updates) deploy the same way — push and forget.

---

## The Three Sites

| Site | Role | Notes |
|------|------|-------|
| **beforegreatness.com** | Corporate umbrella | Minimal. Links to other properties. |
| **jeremyschroeder.net** | Jeremy's devlog | Build notes, design decisions, Godot posts. Same Astro+Tailwind stack. |
| **ephergent.com** | Story hub | **This is the technical focus.** Games, crew, lore, transmissions. |

---

## Gotchas & Common Pitfalls

### 1. `getCollection()` in `getStaticPaths` — it will break your build
Use `import.meta.glob` instead. See the dedicated section above. This is the #1 issue new contributors hit.

### 2. Game size creep
Measure with `du -sh export/` after every Godot export. The 15MB cap is a hard constraint, not a suggestion. Audio and spritesheets are the usual offenders.

### 3. No nautical metaphors
The Game Bible mandates **sci-fi vocabulary only**. Use: fly, dock, hangar, cockpit. Never use: sail, anchor, port, starboard, helm, crew quarters (use "quarters" alone). This applies to all site copy, game text, and transmissions.

### 4. Transmission schema mismatches
Hermes-generated markdown must match the `transmissions/` collection schema exactly. A bad frontmatter field will fail the build silently or produce empty pages. Validate agent output before committing.

### 5. Canvas resize policy
Godot embeds must use `canvas_resize_policy=2` (adaptive). Missing this causes the game to render at a fixed size and ignore the iframe dimensions.

### 6. No removed antagonists
Corporate Corp / The Board were removed in the 2026 refactor. Do not reference them in any site content, lore entries, or transmissions. Hermes agents should be configured to exclude these.
