---
name: ephergent-ebook-export
description: Use when exporting The Ephergent episodes to EPUB or plain-text ebook format.
author: Jeremy (BitsofJeremy)
license: MIT
tags: [ephergent, epub, ebook, export]
related_skills: [the-ephergent]
---

# ephergent-ebook-export

Generate EPUB and plain-text ebook from episode markdown source files.

## Source

Episodes from original source (NOT website content collections):
```
~/Documents/code_repos/the_ephergent_grand_plan/phase_04_episodes/
  season01/  season02/  season03/
```
Plain markdown files — no frontmatter, first `# H1` is the title.

## Script

```
python3 /home/debian/.hermes/scripts/epub_export.py
```

## Output

```
~/Documents/The_Ephergent_Archive/epub_output/
  the_ephergent.epub   (EPUB 3.0, ~194KB)
  the_ephergent.txt    (plain text, ~460KB, 80-char wrapped)
```

## EPUB Structure

- Cover page (dark terminal aesthetic)
- Navigation document (TOC)
- One XHTML chapter per episode
- Georgia/serif body font, 1.75 line-height
- Haiku lines in italic with preserved whitespace
- Section dividers (━━ label ━━)

## Episode Ordering

The script's `EPISODES` list defines canonical order (S01E01 → S03E10). Missing files print WARN and skip — does not abort.

## After Running

Deliver via:
- `send_message` with `MEDIA:/home/debian/Documents/The_Ephergent_Archive/epub_output/the_ephergent.epub`
- or share the output directory path