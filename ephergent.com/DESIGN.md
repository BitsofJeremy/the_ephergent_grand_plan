---
name: Ephergent — ephergent.com
description: Games-as-story hub; episodic micro-games and lore
colors:
  bg-deep: "#08080d"
  bg-surface: "#121219"
  bg-elevated: "#1c1c28"
  text-primary: "#e8e8f0"
  text-secondary: "#7878a0"
  border-subtle: "#2a2a3a"
  accent-cyan: "#00d4ff"
  accent-amber: "#ffb020"
  accent-magenta: "#e040fb"
  accent-pink: "#F12CA5"
  accent-green: "#00e676"
typography:
  display:
    fontFamily: "Space Grotesk, Inter, system-ui, sans-serif"
  body:
    fontFamily: "Inter, system-ui, sans-serif"
---

# Design System: Ephergent

## Color tokens (suggested)
- brand-60: #7E3BFF  /* primary saturated accent for calls-to-action */
- brand-40: #A07BFF  /* hover / emphasis */
- accent-20: #00D8C1 /* secondary for playful highlights */

- neutral-100: #0B0A0D  /* base near-black, tinted slightly toward brand */
- neutral-90:  #121015
- neutral-70:  #222025
- neutral-40:  #6B676E
- neutral-10:  #F6F5F7  /* off-white — do not use pure #fff */

Accessibility note: prefer sufficient contrast for body/heading text; use tinted neutrals rather than pure black/white.

## Typography
- UI / body: Inter (variable) — 16px base, 1.4 line-height
- Display / headings: Space Grotesk or Outfit — expressive but readable, tighter leading
- Scale: 1.25 modular scale for headings (H1→H2→H3)
- Max measure: 65–75ch for longform copy

## Spacing & layout
- Base spacing unit: 8px; rhythm scales: 8 / 12 / 16 / 24 / 32 / 48
- Content width: 840–1080px for narrative pages; tighter for side-by-side play + transcript views
- Use generous vertical rhythm in story pages to support skimming

## Elevation & surfaces
- Use low-contrast tints for surfaces, no heavy drop shadows
- Avoid glassmorphism and blurred background cards as defaults

## Components
- Hero: narrative-focused: headline, subhead, 'Play' CTA, small context panel (episode, length, file size)
- Card: variable-height content cards (no identical grids), include leading icons or episode numbers
- Nav: simple top nav with search; persistent footer with lore index
- Player embed: progressive enhancement — native audio/video fallbacks, keyboard controls, captions

## Motion
- Micro-interactions only: ease-out-quart; 180–300ms durations
- Avoid animating layout properties; prefer transforms & opacity

## Imagery & art
- Treat art as narrative panels. Respect aspect ratio, provide alt text and captions.
- Lazy-load high-res assets; use placeholders for first paint

## Tokens & theming
- Keep tokens in a single source (CSS vars or tailwind tokens). Keep token names semantic (e.g., --surface-muted, --accent-primary).

## Implementation notes
- Host fonts locally or via performant CDN with font-display: swap
- Export color tokens to tailwind config (oklch ideal but hex acceptable for now)

