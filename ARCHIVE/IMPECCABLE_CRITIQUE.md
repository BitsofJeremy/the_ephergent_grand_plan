# IMPECCABLE_CRITIQUE.md — ephergent.com Design System Review

**Date:** 2026-05-04
**Agent:** impeccable:quieter (frontend refinement)
**Register:** Brand

---

## WHAT WAS DONE

### Quieter Analysis — ephergent.com

**Visual noise layering assessment** (scanlines vs. grain vs. hero effects):

The "grain texture" mentioned in DESIGN.md (`body::after { opacity: 0.04 }`) is **not present** in the generated output. It was either removed or never implemented. The only active CRT effects are:

1. **`terminal/terminal.css` scanlines** — `::before` pseudo-element on `#terminal-overlay`, repeating-linear-gradient at 1px/2px intervals, 15% black opacity, `pointer-events: none` (atmospheric only)
2. **`terminal/terminal.css` vignette** — `::after` radial-gradient from transparent center to 50% black at edges
3. **`index.html` inline `.scanlines`** — same scanline + vignette treatment as a fixed div
4. **`index.html` boot flicker** — `animation: flicker .15s infinite` on `.boot-sequence` — 150ms cycle, constant

**Finding:** The grain/scanline conflict is a false problem. Grain doesn't exist. The real intensity sources are:
- Boot flicker animation (too frequent, distracting during reading)
- Scanline density (2px intervals is aggressive; 3-4px would be subtler)
- Vignette intensity (50% black at edges is heavy; 40% would be softer)

---

## FIXES ALREADY APPLIED (this session)

### 1. `terminal/terminal.css` — prefers-reduced-motion (DONE)
Added a `@media (prefers-reduced-motion: reduce)` block that disables all terminal animations:

```css
@media (prefers-reduced-motion: reduce) {
  .line { animation: none !important; }
  .l-boot, .l-flicker, .l-typing { animation: none !important; }
  .l-prompt, .l-header, .l-warmth { animation: none !important; }
  #boot-container { animation: none !important; }
}
```

### 2. `terminal/index.html` — aria-label improvement (DONE)
Changed `aria-label="Terminal input"` to `aria-label="Terminal command input"` for better screen reader description of the terminal input field.

---

## WHAT THE OVERNIGHT AGENT SHOULD HANDLE

### P1 — Critical (Affects Accessibility / Integrity)

#### 1. Mobile Menu Accessibility (Astro source required)
**Priority: P1 — accessibility**
**Files:** The mobile menu JS is inline in every generated HTML page. The Astro source layout was not found in the repo — it appears this is a built static output only, no `.astro` source files present.

**What's needed:**
- Add `Escape` key handler to close the mobile menu (code exists for click and backdrop close, but keyboard `Escape` is missing)
- Add `aria-expanded` to the hamburger `<button id="mobile-menu-btn">` — it has `aria-label="Open menu"` but should toggle to `"Close menu"` and reflect open state via `aria-expanded`
- Add `aria-hidden="true"` to the nav panel when closed, `aria-hidden="false"` when open

**Why it needs Astro source:** These attributes need to change on state. The inline JS in the generated HTML only updates `aria-label` on the button, not `aria-expanded` or the panel's `aria-hidden`.

**If no Astro source exists:** These fixes require either:
- (a) Finding/restoring the actual Astro project source and editing the layout file
- (b) Adding the missing `aria-expanded`/`aria-hidden` handling to the inline JS in all generated HTML pages

#### 2. Root `/index.html` Terminal Entry Point (Onboarding gap)
**Priority: P1 — user experience**
**Files:** `index.html` (root landing page)

**What's needed:** The root `/` serves the terminal directly with no landing explanation. A first-time visitor types `HELP` to begin but gets no preamble about what the station is, who the crew is, or what they're supposed to do. The `terminal/terminal.js` has a boot sequence but no first-run orientation.

**Recommendation:** Either:
- Add a static landing section above or before the terminal that introduces the station and crew before the terminal overlay activates (requires Astro source)
- Or add a `HELLO` / `ABOUT` command to terminal.js that outputs a brief station orientation on first open (self-contained fix in terminal.js)

---

### P2 — Important (Visual Refinement)

#### 3. Scanline Density Reduction
**Priority: P2**
**Files:** `terminal/terminal.css` (line 27-33)
**Current:** 1px/2px scanline intervals
**Proposed:** Change to 1px/3px or 1px/4px intervals for a subtler CRT effect

```css
/* Current (too aggressive) */
background: repeating-linear-gradient(
  0deg,
  rgba(0, 0, 0, 0.15) 0px,
  rgba(0, 0, 0, 0.15) 1px,
  transparent 1px,
  transparent 2px  /* ← change 2px to 3px or 4px */
);
```

#### 4. Vignette Softening
**Priority: P2**
**Files:** `terminal/terminal.css` (line 43-48), `index.html` inline style
**Current:** `rgba(0, 0, 0, 0.5) 100%` at edges
**Proposed:** Reduce to `rgba(0, 0, 0, 0.35) 100%` for a softer edge fade

#### 5. Boot Flicker Animation (index.html)
**Priority: P2 — cannot fix without Astro source**
**Current:** `animation: flicker .15s infinite` — 150ms cycle is visually distracting during extended reading
**Proposed:** Either remove entirely, or change to `animation: flicker .3s infinite` (300ms) and reduce opacity drop to `0.99` — the subtle 2% variation is enough for authenticity without distraction

**Note:** This is inline CSS in the generated `index.html` and cannot be edited without Astro source access.

---

### P3 — Nice to Have (Lower Priority)

#### 6. `--tw-ring-offset-color: #fff` in Tailwind bundle
**Priority: P3**
**File:** `_astro/_slug_.ByincVgP.css` (generated build artifact)
**Issue:** Hardcoded `#fff` in `--tw-ring-offset-color` — violates the "no pure white" rule
**Fix:** Requires modifying `tailwind.config.js` to add `ringOffsetColor: { DEFAULT: '#e8e8f0' }` or similar, then rebuilding. Cannot be fixed in the generated CSS directly.

#### 7. `/impeccable polish` — Final Quality Pass
**Priority: P3 — run after all P1/P2 fixes**
Once the mobile menu, scanline density, vignette, and entry point are resolved, run `/impeccable polish` for a final quality pass before shipping.

---

## SUMMARY TABLE

| Item | Priority | File(s) | Fixable Without Astro Source? |
|------|----------|---------|-------------------------------|
| Mobile menu Escape key | P1 | generated HTML (inline JS) | No — needs Astro source |
| aria-expanded/aria-hidden | P1 | generated HTML (inline JS) | No — needs Astro source |
| Terminal entry point | P1 | index.html or terminal.js | Partially — terminal.js can add HELLO command |
| Scanline density (2px→3px) | P2 | terminal/terminal.css | **Yes** — editable |
| Vignette softening | P2 | terminal/terminal.css | **Yes** — editable |
| Boot flicker speed | P2 | index.html inline CSS | No — Astro source needed |
| #fff in Tailwind bundle | P3 | _astro/*.css | No — build config change needed |
| `/impeccable polish` | P3 | all | Run after P1/P2 done |

---

## CONTEXT FOR OVERNIGHT AGENT

The site is a built Astro static output. The editable files are:
- `terminal/terminal.css` — **fully editable**
- `terminal/index.html` — **fully editable**
- `terminal/terminal.js` — **fully editable** (can add new commands like HELLO/ABOUT)
- `terminal/clive_haiku.js` — **fully editable**
- `terminal/a1_responses.js` — **fully editable**

Files that cannot be edited (generated build artifacts, not source):
- `_astro/*.css` — Tailwind bundle
- `index.html` — root landing page (generated, not source)
- `crew/index.html`, `atlas/index.html`, `transmissions/index.html` — generated Astro pages

**Design system reference:** `DESIGN.md` and `DESIGN.json` at project root define the phosphor palette, typography, and component rules. Any visual changes should respect the dual-accent system (amber for station voice, cyan for user voice).

**Brand register:** ephergent.com is brand (design IS the product) — sci-fi explorers who enjoy solarpunk/biopunk/steampunk world-building. The station feels inhabited. Warmth and quirk over cold efficiency.
