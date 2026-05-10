# ephergent.com Astro Site Scaffold

## Directory Structure

- src/
  - pages/
    - index.astro (Landing: "Tune the dial")
    - games/
      - [slug]/
        - index.astro (Game landing)
        - play.astro (Embedded Godot game)
        - about.astro (Story context, controls, credits)
    - crew/
      - [slug].astro (Crew profiles)
    - atlas/
      - frequencies/
        - [slug].astro (Frequency entries)
      - builder-stations/
        - [slug].astro (Builder Station entries)
      - glossary.astro
      - timeline.astro
    - transmissions/
      - [slug].astro (Weekly in-character posts)
  - content/
    - games/
    - crew/
    - lore/
    - transmissions/
  - components/
    - Layouts, nav, card, atlas map, etc.

## Key Notes
- Use import.meta.glob for all content collections
- Tailwind 3 for styling
- Godot games embedded via iframe
- No server runtime, SSG only
- All copy: sci-fi vocabulary only
- Transmission/blog schema: title, author, date, tags, excerpt
- 15MB/game cap
- No references to Corporate Corp/Board
