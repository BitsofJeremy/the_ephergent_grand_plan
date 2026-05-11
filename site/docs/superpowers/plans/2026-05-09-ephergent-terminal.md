# Ephergent Terminal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite ephergent.com to be a full CRT phosphor terminal — the entire site is a command line. Episodes, lore, crew render in terminal. Session memory (4-hour window). Debug mode. Terminal-native audio player. DoRM ghost intrusions.

**Architecture:** Astro static site with TypeScript terminal client. No backend in Phase 1 — reads from Astro content collections. Session via cookie. Degrades gracefully offline.

**Tech Stack:** Astro 5, vanilla TypeScript (no framework), JetBrains Mono font, CSS CRT effects

---

## File Structure

```
src/
├── components/terminal/
│   ├── Terminal.ts           # Core engine — input, output, history, session
│   ├── BootSequence.ts      # Boot logic, session memory, cookie handling
│   ├── CommandParser.ts      # Command routing, tab completion, path resolution
│   ├── ContentService.ts     # Reads Astro content collections (static JSON)
│   ├── Renderer.ts           # Markdown → terminal text, Signal styling
│   ├── AudioPlayer.ts        # Terminal-native audio, player block, controls
│   ├── GlitchEffects.ts      # CRT glitch system — text scramble, screen tear
│   └── DoRMEngine.ts         # DoRM ghost intrusions, ~25% frequency
├── pages/
│   └── terminal.astro        # Main page — replaces existing terminal.astro
└── styles/
    └── terminal.css          # CRT theme: scanlines, vignette, glow, typography

public/
├── css/terminal.css           # Compiled CSS output
└── api/content.json          # Pre-built content for frontend fallback
```

---

## Task 1: Terminal Core Engine

**Files:**
- Create: `src/components/terminal/Terminal.ts`
- Modify: `src/pages/terminal.astro` (replace entirely)
- Test: browser console, manual interaction

- [ ] **Step 1: Create Terminal.ts — Core engine**

```typescript
// src/components/terminal/Terminal.ts

export interface TerminalLine {
  text: string;
  type: 'system' | 'signal' | 'command' | 'content' | 'error' | 'dorm' | 'success';
  timestamp?: number;
}

export interface Session {
  firstVisit: number;
  lastVisit: number;
  cwd: string;
  bootCount: number;
  isReturning: boolean;
  debug: boolean;
}

export class Terminal {
  private container: HTMLElement;
  private input: HTMLInputElement;
  private session: Session;
  private history: string[];
  private historyIndex: number;
  private audioPlayer: AudioPlayer | null;

  constructor(containerId: string, inputId: string) { ... }

  // Session management
  private initSession(): void { ... }  // Read/write cookie, check 4h window
  private saveSession(): void { ... }

  // Output
  public print(text: string, type: TerminalLine['type'] = 'system'): void { ... }
  public printHTML(html: string): void { ... }
  public clear(): void { ... }

  // Input handling
  private handleInput(value: string): void { ... }
  private parseCommand(input: string): { cmd: string; args: string[] } { ... }

  // History
  private addToHistory(cmd: string): void { ... }
  private navigateHistory(direction: 'up' | 'down'): string { ... }

  // Tab completion
  private tabComplete(partial: string): string { ... }

  // Session info
  public getSession(): Session { ... }
  public getCWD(): string { ... }

  // Glitch trigger
  private triggerGlitch(): void { ... }
}
```

- [ ] **Step 2: Create BootSequence.ts — Session memory**

```typescript
// src/components/terminal/BootSequence.ts

const SESSION_COOKIE = 'ephergent_session';
const FOUR_HOURS_MS = 4 * 60 * 60 * 1000;

export interface BootConfig {
  mode: 'full' | 'returning' | 'short';
  debug: boolean;
}

export function getBootConfig(): BootConfig { ... }

export function readSession(): Session { ... }
export function writeSession(session: Session): void { ... }

export function generateBootLines(config: BootConfig): string[] {
  const lines: string[] = [];
  if (config.debug) {
    lines.push('[DEBUG MODE] — Session memory disabled');
    lines.push(`[DEBUG] Cookie: ${document.cookie || 'none'}`);
  }
  if (config.mode === 'full') {
    // Full Option B boot — 12-15 lines
  } else if (config.mode === 'returning') {
    // Abbreviated dormancy boot — 6-8 lines
  } else if (config.mode === 'short') {
    // Just Signal short message
  }
  return lines;
}

export function generateSignalIntro(mode: 'boot' | 'return' | 'short'): string {
  // Signal's voice lines, amber italic
}
```

- [ ] **Step 3: Replace terminal.astro — Wire everything together**

The new `terminal.astro` is minimal — just the HTML shell and imports the Terminal class. All logic lives in the TypeScript components.

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import '../styles/terminal.css';
---

<BaseLayout title="Ephergent Terminal" description="The Ephergent broadcast relay terminal.">
  <div class="crt-container">
    <div class="scanlines" aria-hidden="true"></div>
    <div class="vignette" aria-hidden="true"></div>
    <div class="phosphor-glow" aria-hidden="true"></div>

    <div id="terminal-output" class="terminal-output"></div>

    <div class="terminal-input-row">
      <span class="terminal-prompt">Signal@relay-7b:~<span id="cwd-display">$</span>$</span>
      <input type="text" id="terminal-input" autocomplete="off" autofocus />
    </div>

    {Deno.env.get('DEBUG') && <div class="debug-badge">DEBUG</div>}
  </div>
</BaseLayout>

<script>
  import { Terminal } from '../components/terminal/Terminal';
  import { getBootConfig, generateBootLines, generateSignalIntro } from '../components/terminal/BootSequence';

  const config = getBootConfig();
  const bootLines = generateBootLines(config);
  const signalIntro = generateSignalIntro(config.mode === 'short' ? 'return' : 'boot');

  const term = new Terminal('terminal-output', 'terminal-input');

  // Print boot sequence
  bootLines.forEach(line => {
    term.print(line, 'system');
  });

  // Print Signal intro
  term.print(signalIntro, 'signal');

  // Print prompt
  term.printPrompt();
</script>
```

- [ ] **Step 4: Test boot sequence**

Run: `cd /Users/jeremy/Documents/current_projects/my_websites/ephergent.com && npm run dev`
Open: `http://localhost:4321/terminal`

- [ ] **Step 5: Verify session memory**

1. Open terminal — full boot should show
2. Check browser DevTools → Application → Cookies → ephergent_session
3. Close tab, reopen within 4 hours — short Signal message should appear, no full boot
4. Wait 4+ hours or clear cookie — dormancy boot should appear
5. Add `?debug=true` — full boot always shows, debug badge visible

- [ ] **Step 6: Commit**

```bash
cd /Users/jeremy/Documents/current_projects/my_websites/ephergent.com
git add -A
git commit -m "feat: terminal core — boot sequence, session memory, basic engine"
```

---

## Task 2: Command Parser + Content Service

**Files:**
- Create: `src/components/terminal/CommandParser.ts`
- Create: `src/components/terminal/ContentService.ts`
- Modify: `src/components/terminal/Terminal.ts` (add command routing)
- Test: `cat s01e01`, `cd /transmissions`, `ls`, `help`

- [ ] **Step 1: Create ContentService.ts — Static content from Astro collections**

```typescript
// src/components/terminal/ContentService.ts

export interface ContentItem {
  slug: string;
  type: 'transmission' | 'lore' | 'crew' | 'game';
  title: string;
  season?: string;
  status: 'archived' | 'locked';
  audioAvailable?: boolean;
  audioPath?: string;
}

export interface ContentDetail extends ContentItem {
  rawMarkdown: string;  // Full markdown for rendering
}

export class ContentService {
  private content: Map<string, ContentItem>;
  private details: Map<string, ContentDetail>;

  constructor() {
    // Load from pre-built content.json at public/api/content.json
    // Fallback: inline static data for episodes, lore, crew
  }

  public list(type?: string): ContentItem[] { ... }

  public get(slug: string): ContentDetail | null { ... }

  public getEpisode(slug: string): ContentDetail | null { ... }

  public getLore(slug: string): ContentDetail | null { ... }

  public getCrew(slug: string): ContentDetail | null { ... }

  public isLocked(slug: string): boolean { ... }

  public hasAudio(slug: string): boolean { ... }

  public resolvePath(path: string): { type: string; items: ContentItem[] } | null { ... }
}
```

- [ ] **Step 2: Create CommandParser.ts — Routing + tab completion**

```typescript
// src/components/terminal/CommandParser.ts

import { ContentService } from './ContentService';

export interface ParsedCommand {
  cmd: string;
  args: string[];
  raw: string;
}

export class CommandParser {
  private content: ContentService;

  constructor(content: ContentService) {
    this.content = content;
  }

  public parse(input: string): ParsedCommand { ... }

  public getCompletions(partial: string): string[] {
    // Tab completion: commands, paths, slugs
  }

  public resolvePath(path: string): string[] { ... }

  // Command handlers return lines to print
  public async execute(cmd: ParsedCommand, terminal: Terminal): Promise<void> { ... }
}

// Commands:
const COMMANDS = ['help', 'cd', 'ls', 'cat', 'pwd', 'clear', 'history', 'play', 'pause', 'stop', 'audio', 'signal', 'whoami'];
```

- [ ] **Step 3: Implement help command**

```typescript
// help command output:
SIGNAL: Let me show you what you can do here.

Available commands:
  help                — Show this reference
  cd [path]           — Navigate frequency archive
  ls                  — List current directory
  cat [slug]          — Read content (episode, lore, crew)
  pwd                 — Print working directory
  clear               — Clear terminal output
  history             — Show command history
  play [slug]         — Play episode audio
  pause               — Pause audio
  stop                — Stop audio
  audio               — Show now-playing info
  signal              — Signal appears (random interjection)
  whoami              — Station identification

Signal: Navigation model
  /transmissions      — Episode archive (30 episodes)
  /atlas              — Lore database (27 entries)
  /crew               — Crew manifest (12 profiles)
  /games              — Interactive frequencies (6 games)
  /signal             — Signal's domain (about Signal)
```

- [ ] **Step 4: Implement cd + ls**

```typescript
// cd /transmissions → cwd = /transmissions, print listing
// ls → list current directory contents

// Directory listings formatted as ASCII table:
/transmissions/
  S01E01_the_frequency.md...........[ARCHIVED] [AUDIO]
  S01E02_ruins_ripples.md...........[ARCHIVED] [AUDIO]
  ...
  S02E01_first_station.md...........[LOCKED]
  ...
  S03E11_the_green_listening.md.....[LOCKED]
```

- [ ] **Step 5: Implement cat — render episode/lore/crew**

```typescript
// cat s01e01 → fetch from ContentService, render via Renderer
// Content locked → Signal message instead

// Episode rendering:
// ════════════════════════════════════════════════════════════════════
// THE FREQUENCY — S01E01
// ════════════════════════════════════════════════════════════════════
// [prose sections with Signal voice amber/italic]
// [coffee chart if present]
// ════════════════════════════════════════════════════════════════════
// [AUDIO AVAILABLE] — type `play s01e01` to broadcast
// ════════════════════════════════════════════════════════════════════
```

- [ ] **Step 6: Test commands**

```bash
help    # → command list
cd /transmissions  # → listing
ls    # → directory contents
cat s01e01  # → episode text
cat s02e01  # → locked message
pwd   # → /transmissions
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: command parser, content service, full navigation"
```

---

## Task 3: Renderer + Markdown → Terminal

**Files:**
- Create: `src/components/terminal/Renderer.ts`
- Modify: `src/components/terminal/CommandParser.ts` (integrate renderer)

- [ ] **Step 1: Create Renderer.ts**

```typescript
// src/components/terminal/Renderer.ts

export class Renderer {
  // Render episode markdown to terminal lines
  public renderEpisode(markdown: string, slug: string): TerminalLine[] { ... }

  // Render lore entry
  public renderLore(markdown: string): TerminalLine[] { ... }

  // Render crew profile
  public renderCrew(markdown: string): TerminalLine[] { ... }

  // Strip YAML frontmatter
  private stripFrontmatter(markdown: string): string { ... }

  // Parse markdown to terminal-formatted text
  // - ## headers → uppercase with ═══ underline
  // - *italic* → amber colored (Signal's voice)
  // - **bold** → bright white
  // - [links](url) → cyan with ↗
  // - `code` → bright cyan monospace
  // - Scene breaks · · ·
  private parseMarkdown(md: string): TerminalLine[] { ... }

  // Box-drawing header
  public boxHeader(title: string, width = 64): string { ... }

  // Format content listing
  public formatList(items: ContentItem[]): string[] { ... }
}
```

- [ ] **Step 2: Test episode rendering**

```bash
cat s01e01  # Should show formatted episode with headers, Signal voice styled
cat barrys-field-notes-grabovoi  # Lore entry, formatted
cat pixel_paradox  # Crew profile, formatted
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat: markdown renderer for terminal content"
```

---

## Task 4: Audio Player — Terminal-Native Inline

**Files:**
- Create: `src/components/terminal/AudioPlayer.ts`
- Modify: `src/components/terminal/CommandParser.ts` (add play/pause/stop/audio)

- [ ] **Step 1: Create AudioPlayer.ts**

```typescript
// src/components/terminal/AudioPlayer.ts

export interface AudioState {
  isPlaying: boolean;
  isPaused: boolean;
  currentSlug: string | null;
  currentTime: number;
  duration: number;
  volume: number;
}

export class AudioPlayer {
  private audio: HTMLAudioElement;
  private terminal: Terminal;
  private state: AudioState;

  constructor(terminal: Terminal) {
    this.audio = new Audio();
    this.terminal = terminal;
    this.state = { isPlaying: false, isPaused: false, currentSlug: null, currentTime: 0, duration: 0, volume: 0.9 };
    this.bindEvents();
  }

  public async play(slug: string): Promise<void> { ... }

  public pause(): void { ... }

  public stop(): void { ... }

  public seek(seconds: number): void { ... }

  public setVolume(vol: number): void { ... }

  // Render player block to terminal
  public renderPlayerBlock(): void { ... }

  // ASCII waveform (decorative, updates every 0.5s)
  private generateWaveform(): string { ... }

  // Update player block in-place (replace previous block)
  private updatePlayerBlock(): void { ... }

  private bindEvents(): void {
    this.audio.addEventListener('timeupdate', () => this.updatePlayerBlock());
    this.audio.addEventListener('ended', () => this.onEnded());
    this.audio.addEventListener('error', () => this.onError());
  }
}
```

- [ ] **Step 2: Player block design**

```
┌─────────────────────────────────────────────────────────────────┐
│ ▶ NOW PLAYING: s01e01_the_frequency                            │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  00:42 / 02:14 │
│ [SPACE] pause  [S] stop  [←][→] seek 5s                       │
│ [♪ 90% VOL]                                                    │
└─────────────────────────────────────────────────────────────────┘

▁ ▂ ▃ ▅ ▆ ▇ █ ▇ ▆ ▅ ▃ ▂ ▁ ▂ ▃ ▅ ▆ ▇ █ ▇ ▆ ▅ ▃ ▂ ▁
```

Player block is:
- Green border when playing, amber when paused, dim when stopped
- Persists in terminal output (like a log entry) until user types `clear`
- Updates every 0.5s with current time + waveform animation

- [ ] **Step 3: Keyboard controls**

```typescript
// Global keydown handler in Terminal.ts:
if (e.key === ' ' && audioPlayer?.isPlaying()) {
  e.preventDefault();
  audioPlayer.pause();
}
if (e.key === 's' && !e.ctrlKey) {
  audioPlayer.stop();
}
if (e.key === 'ArrowLeft') {
  audioPlayer.seek(-5);
}
if (e.key === 'ArrowRight') {
  audioPlayer.seek(5);
}
```

- [ ] **Step 4: Test audio**

```bash
play s01e01  # → player block appears, audio starts
# Waveform animates, time updates
pause       # → amber state
space       # → resumes
stop        # → player block disappears
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: terminal-native audio player with inline block"
```

---

## Task 5: CRT Effects + Glitch System

**Files:**
- Create: `src/components/terminal/GlitchEffects.ts`
- Modify: `src/styles/terminal.css` (add full CRT styling)
- Modify: `src/pages/terminal.astro` (update structure)

- [ ] **Step 1: Create GlitchEffects.ts**

```typescript
// src/components/terminal/GlitchEffects.ts

export class GlitchEffects {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  // Text scramble — 1-2 characters cycle randomly before resolving
  public scrambleText(element: HTMLElement, finalText: string, duration = 200): void {
    // On heavy content load
  }

  // Screen tear — single horizontal line briefly offset
  public screenTear(): void {
    // 150ms, triggered on content load
  }

  // Flicker burst — 3 rapid opacity changes
  public flickerBurst(): void {
    // 3 changes over 150ms, triggered on DoRM intrusions
  }

  // Content load trigger
  public onContentLoad(): void {
    this.screenTear();
    this.scrambleText(...);  // Applied to last output line
  }

  // DoRM intrusion trigger
  public onDoRMIntrusion(): void {
    this.flickerBurst();
  }

  // Respect prefers-reduced-motion
  public shouldAnimate(): boolean {
    return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }
}
```

- [ ] **Step 2: Full terminal.css**

```css
/* CRT Theme — JetBrains Mono only */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

:root {
  --bg: #08080d;
  --fg: #e8e8f0;
  --amber: #ffb020;
  --cyan: #00d4ff;
  --green: #00e676;
  --red: #ff4444;
  --dim: #606080;
  --font: 'JetBrains Mono', monospace;
}

body {
  background: var(--bg);
  color: var(--fg);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.6;
}

/* Scanlines overlay */
.scanlines {
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.15) 2px,
    rgba(0, 0, 0, 0.15) 4px
  );
  pointer-events: none;
  z-index: 1000;
}

/* Vignette */
.vignette {
  position: fixed;
  inset: 0;
  background: radial-gradient(
    ellipse at center,
    transparent 50%,
    rgba(0, 0, 0, 0.7) 100%
  );
  pointer-events: none;
  z-index: 999;
}

/* Phosphor glow */
.phosphor-glow {
  position: fixed;
  inset: 0;
  background: radial-gradient(
    ellipse at 50% 50%,
    rgba(0, 212, 255, 0.03) 0%,
    transparent 70%
  );
  pointer-events: none;
  z-index: 998;
}

/* Terminal container */
.crt-container {
  position: relative;
  min-height: 100vh;
  padding: 24px;
  overflow: hidden;
}

/* Terminal output */
.terminal-output {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
  margin-bottom: 16px;
}

.terminal-output::-webkit-scrollbar {
  width: 8px;
}
.terminal-output::-webkit-scrollbar-track {
  background: rgba(18, 18, 25, 0.3);
}
.terminal-output::-webkit-scrollbar-thumb {
  background: #2a2a3a;
  border-radius: 4px;
}

/* Line types */
.line-system { color: var(--dim); }
.line-signal { color: var(--amber); font-style: italic; }
.line-command { color: var(--cyan); }
.line-content { color: var(--fg); }
.line-error { color: var(--red); }
.line-dorm { color: var(--green); }
.line-success { color: var(--green); }

/* Input row */
.terminal-input-row {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(18, 18, 25, 0.6);
  border: 1px solid #2a2a3a;
  border-radius: 4px;
}

.terminal-prompt {
  color: var(--amber);
  margin-right: 8px;
  white-space: nowrap;
}

#terminal-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--cyan);
  font-family: var(--font);
  font-size: 14px;
  caret-color: var(--cyan);
}

/* DoRM text */
.dorm-artifact {
  color: var(--dim);
  border-left: 2px solid var(--dim);
  padding-left: 8px;
}

.dorm-artifact.amber {
  color: var(--amber);
  border-color: var(--amber);
}

/* Audio player block */
.audio-player-block {
  border: 1px solid var(--green);
  padding: 8px 12px;
  margin: 8px 0;
  font-size: 12px;
}

.audio-player-block.paused {
  border-color: var(--amber);
}

.audio-player-block.stopped {
  border-color: var(--dim);
  opacity: 0.6;
}

/* Debug badge */
.debug-badge {
  position: fixed;
  top: 8px;
  right: 8px;
  background: rgba(255, 68, 68, 0.2);
  color: var(--red);
  border: 1px solid var(--red);
  padding: 2px 8px;
  font-size: 10px;
  z-index: 1001;
}

/* Subtle flicker animation */
@keyframes flicker {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.97; }
}

.crt-container {
  animation: flicker 0.1s infinite;
}

/* Reduced motion: disable flicker */
@media (prefers-reduced-motion: reduce) {
  .crt-container { animation: none; }
  .scanlines { opacity: 0.5; }
}
```

- [ ] **Step 3: Test CRT effects**

- Scanlines visible
- Vignette darkens edges
- Phosphor glow visible on text
- Subtle flicker (check with `prefers-reduced-motion` off)
- Glitch effects fire on content load

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: CRT effects, glitch system, full terminal styling"
```

---

## Task 6: DoRM Engine + Signal Interjections

**Files:**
- Create: `src/components/terminal/DoRMEngine.ts`
- Create: `src/components/terminal/SignalInterjections.ts`
- Modify: `src/components/terminal/Terminal.ts` (integrate DoRM + Signal)

- [ ] **Step 1: Create DoRMEngine.ts**

```typescript
// src/components/terminal/DoRMEngine.ts

export interface DoRMArtifact {
  text: string[];
  type: 'form' | 'log' | 'inspection' | 'compliance' | 'corrupted';
  urgency: 'low' | 'medium' | 'high';
}

const DORM_ARTIFACTS: DoRMArtifact[] = [
  {
    type: 'form',
    text: ['FORM 7-B (EXPIRED) — Sector access requires reauthorization.',
           'Your previous submission: 4,217 cycles ago.',
           'Late submissions: acknowledged. Sort of.'],
    urgency: 'low'
  },
  {
    type: 'inspection',
    text: ['DRM INSPECTOR LOG: Station 7-B found in non-compliant state.',
           'Recommendation: do nothing. The crew will return eventually.',
           'Filing report... report lost in bureaucracy. Case closed.'],
    urgency: 'low'
  },
  // ... 20+ more artifacts
];

export class DoRMEngine {
  private intrusionRate: number; // 0.25 default, 0.5 in debug
  private debug: boolean;

  constructor(debug = false) {
    this.debug = debug;
    this.intrusionRate = debug ? 0.5 : 0.25;
  }

  public shouldIntrude(): boolean {
    return Math.random() < this.intrusionRate;
  }

  public getArtifact(): DoRMArtifact {
    return DORM_ARTIFACTS[Math.floor(Math.random() * DORM_ARTIFACTS.length)];
  }

  public formatArtifact(artifact: DoRMArtifact): string[] {
    // Format with box-drawing, dim color, appropriate urgency styling
  }
}
```

- [ ] **Step 2: Create SignalInterjections.ts**

```typescript
// src/components/terminal/SignalInterjections.ts

export class SignalInterjections {
  private debug: boolean;

  constructor(debug = false) {
    this.debug = debug;
  }

  public getInterjection(context: 'navigate' | 'content' | 'locked' | 'audio' | 'idle' | 'error'): string[] { ... }

  // Random idle message when cursor sits >60s
  public getIdleMessage(): string {
    const idle = [
      'Signal is patient.',
      'The frequencies are quiet.',
      'Someone is still listening.',
      'The story continues whether or not anyone is watching.',
      // ... 10+ more
    ];
    return idle[Math.floor(Math.random() * idle.length)];
  }

  public formatInterjection(lines: string[]): TerminalLine[] {
    return lines.map(line => ({ text: line, type: 'signal' as const }));
  }
}
```

- [ ] **Step 3: Integrate into Terminal.ts**

```typescript
// In Terminal.handleInput(), after command executes:
// Check DoRMEngine.shouldIntrude() — if true, print DoRM artifact
// Check idle timer — if >60s with no input, print Signal idle message
// In debug mode: Signal interjects every 3-4 commands
```

- [ ] **Step 4: Test DoRM frequency**

```bash
# Run 10 commands — should see DoRM artifact 2-3 times normally, 5 times in debug
# Run ?debug=true session — DoRM at 50%, more Signal interjections
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: DoRM engine, Signal interjections, full personality"
```

---

## Task 7: Debug Mode + Polish

**Files:**
- Modify: `src/components/terminal/BootSequence.ts` (add debug detection)
- Modify: `src/components/terminal/Terminal.ts` (add debug badge, override session)
- Modify: `src/styles/terminal.css` (debug badge styles)
- Modify: `terminal.astro` (add debug badge conditional)

- [ ] **Step 1: Debug mode detection**

```typescript
// In BootSequence.ts:
export function getBootConfig(): BootConfig {
  const urlParams = new URLSearchParams(window.location.search);
  const debugParam = urlParams.get('debug') === 'true';
  const localStorageDebug = localStorage.getItem('debug') === '1';

  return {
    mode: 'full', // debug always forces full boot
    debug: debugParam || localStorageDebug
  };
}

// In Terminal.ts:
public isDebug(): boolean { return this.session.debug; }
```

- [ ] **Step 2: Debug features in debug mode**

- `?debug=true` on URL forces full boot, no session memory
- Debug badge top-right corner (dim, small red text)
- DoRM intrusions at 50%
- Signal interjects more frequently
- All content accessible (no locking)
- Artificial delays reduced to 0
- `localStorage.setItem('debug', '1')` to persist debug mode

- [ ] **Step 3: Write DEPLOY.md for Moguera**

```markdown
# Deploy: Ephergent Terminal v2

## Prerequisites
- VPS: Debian Linux 13
- SSH access with passwordless sudo
- Domain: ephergent.com, pointing to server

## Build Steps

1. SSH to server
2. Pull latest from main branch
3. Run `npm run build`
4. If build succeeds → done
5. If build fails → check error, fix, retry

## Rollback

If something goes wrong:
```bash
git reset --hard origin/archive-pre-terminal-v2
npm run build
```

## Architecture

- Static Astro site — no backend required for Phase 1
- Terminal reads from pre-built content.json
- If API needed later: FastAPI on port 8000, nginx proxies /api/ and /ws/

## CDN / Asset Notes

- JetBrains Mono via Google Fonts (no local needed)
- No external JS dependencies — vanilla TypeScript
- Audio files in public/audio/ (already exists)
```

- [ ] **Step 4: Final test pass**

- [ ] Boot sequence correct on first visit
- [ ] <4h return shows short message
- [ ] >4h return shows dormancy boot
- [ ] `cat s01e01` renders episode with Signal styling
- [ ] `cat s02e01` shows locked Signal message
- [ ] `play s01e01` shows inline audio player
- [ ] Audio controls (space, s, arrows) work
- [ ] `?debug=true` shows debug badge + full boot
- [ ] DoRM artifacts appear ~25% commands
- [ ] Signal idle message after 60s inactivity
- [ ] No Inter, no sans-serif — JetBrains Mono only
- [ ] CRT effects (scanlines, vignette, glow, flicker) all visible
- [ ] Tab completion works for commands and paths

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: ephergent terminal v2 — full rewrite complete"
```

---

## Verification Commands

```bash
cd /Users/jeremy/Documents/current_projects/my_websites/ephergent.com
npm run dev
# Open http://localhost:4321/terminal

# Test all scenarios:
# 1. Fresh boot
# 2. <4h return (check console: "returning")
# 3. >4h return (check console: "dormancy")
# 4. ?debug=true (check: debug badge, full boot)
# 5. help, cat s01e01, play s01e01, pause, stop
# 6. cd /transmissions, ls, cat grabovoi-codes, cat pixel_paradox
# 7. Run 10 commands — DoRM appears ~2-3 times
# 8. Idle 60s — Signal idle message appears
```

---

## Spec Coverage Check

- [x] Station personality (abandoned + glitchy hybrid) — Task 5, 6
- [x] Signal voice (third-person past, warm-distant) — Task 2, 3, 6
- [x] DoRM ghosts ~25% — Task 6
- [x] Session <4h / >4h / no cookie — Task 1
- [x] Debug mode — Task 7
- [x] Audio inline player — Task 4
- [x] Images monochrome — deferred to Phase 4
- [x] JetBrains Mono only, no Inter/sans-serif — Task 5
- [x] CRT effects (scanlines, vignette, glow, flicker) — Task 5
- [x] Content locking (S02, S03 locked) — Task 2
- [x] Navigation (cd, ls, cat, pwd, help) — Task 2
- [x] DEPLOY.md for Moguera — Task 7
- [x] Rollback branch — already done

**Phase 1 scope complete.** Phase 2 (API) deferred.