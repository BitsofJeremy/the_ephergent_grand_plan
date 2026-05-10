// CommandParser.ts — Command Routing + Tab Completion
// Handles all terminal commands: cd, ls, cat, pwd, help, clear, history, play, pause, stop, audio, signal, whoami

import type { OutputLine } from './Terminal';

export interface ContentItem {
  slug: string;
  title: string;
  type?: string;
  locked?: boolean;
}

export interface CommandContext {
  cwd: string;
  setCwd: (path: string) => void;
  content: {
    transmissions: ContentItem[];
    atlas: ContentItem[];
    crew: ContentItem[];
    games: ContentItem[];
    signal: ContentItem[];
  };
  audioPlayer: {
    play: (slug: string) => Promise<void>;
    pause: () => void;
    stop: () => void;
    getState: () => { playing: boolean; slug: string | null; position: number; duration: number };
  };
  onSignalInterjection?: (context: string) => Promise<string>;
}

const COMMANDS = ['help', 'cd', 'ls', 'cat', 'pwd', 'clear', 'history', 'play', 'pause', 'stop', 'audio', 'signal', 'whoami'];

const VIRTUAL_FS: Record<string, { label: string; type: 'dir' }> = {
  '/': { label: 'Station Root', type: 'dir' },
  '/transmissions': { label: 'Episode Broadcast Archive', type: 'dir' },
  '/atlas': { label: 'Lore Database', type: 'dir' },
  '/crew': { label: 'Crew Manifest', type: 'dir' },
  '/games': { label: 'Interactive Frequencies', type: 'dir' },
  '/signal': { label: "Signal's Domain", type: 'dir' },
  '/station': { label: 'Station Diagnostics', type: 'dir' },
};

const LOCKED_SEASONS = ['s02', 's03'];

export class CommandParser {
  private ctx: CommandContext;
  private commandHistory: string[] = [];

  constructor(ctx: CommandContext) {
    this.ctx = ctx;
  }

  async execute(input: string): Promise<OutputLine[]> {
    const parts = input.trim().split(/\s+/);
    const command = parts[0];
    const args = parts.slice(1);

    switch (command) {
      case 'help':
        return this.help();
      case 'cd':
        return this.cd(args[0] || '/');
      case 'ls':
        return this.ls(args[0] || this.ctx.cwd);
      case 'cat':
        return this.cat(args[0]);
      case 'pwd':
        return [{ text: this.ctx.cwd }];
      case 'clear':
        return [{ text: '__CLEAR__' }]; // Special signal to terminal
      case 'history':
        return this.showHistory();
      case 'play':
        return this.play(args[0]);
      case 'pause':
        return this.pause();
      case 'stop':
        return this.stop();
      case 'audio':
        return this.audio();
      case 'signal':
        return this.signal();
      case 'whoami':
        return this.whoami();
      default:
        if (command) {
          return [{ text: `Command not found: ${command}. Type 'help' for available commands.`, className: 'terminal-red' }];
        }
        return [];
    }
  }

  private help(): OutputLine[] {
    const lines: OutputLine[] = [
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: 'EPHERGENT RELAY STATION 7-B — Command Reference', className: 'terminal-amber', isHtml: false },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '' },
      { text: 'NAVIGATION', className: 'terminal-cyan terminal-bold' },
      { text: '  cd [path]       Navigate frequency archive' },
      { text: '  ls [path]       List current directory contents' },
      { text: '  pwd             Print working directory' },
      { text: '' },
      { text: 'CONTENT', className: 'terminal-cyan terminal-bold' },
      { text: '  cat [slug]      Read content (episode, lore, crew)' },
      { text: '' },
      { text: 'AUDIO', className: 'terminal-cyan terminal-bold' },
      { text: '  play [slug]     Play episode audio' },
      { text: '  pause           Pause audio' },
      { text: '  stop            Stop audio' },
      { text: '  audio           Show now-playing info' },
      { text: '' },
      { text: 'SYSTEM', className: 'terminal-cyan terminal-bold' },
      { text: '  help            Show this reference' },
      { text: '  clear           Reset terminal view' },
      { text: '  history         Show command history' },
      { text: '  signal          Signal appears' },
      { text: '  whoami          Station identification' },
      { text: '' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
    ];

    return lines;
  }

  private cd(path: string): OutputLine[] {
    if (!path) {
      return [{ text: 'cd: missing path. Usage: cd [path]', className: 'terminal-red' }];
    }

    // Handle relative paths
    let fullPath = path;
    if (!path.startsWith('/')) {
      fullPath = this.ctx.cwd === '/' ? `/${path}` : `${this.ctx.cwd}/${path}`;
    }

    // Handle ..
    fullPath = fullPath.replace(/\/\.\.\/?/g, '/');
    if (fullPath === '') fullPath = '/';
    if (fullPath !== '/' && fullPath.endsWith('/')) {
      fullPath = fullPath.slice(0, -1);
    }

    if (VIRTUAL_FS[fullPath]) {
      this.ctx.setCwd(fullPath);
      return [{ text: `And so the frequency shifts. Now at ${fullPath}. Signal is watching.`, className: 'signal-voice' }];
    }

    return [{ text: `cd: ${path}: No such frequency directory. Type 'ls /' to see available paths.`, className: 'terminal-red' }];
  }

  private ls(path: string): OutputLine[] {
    let targetPath = path;

    if (!path.startsWith('/')) {
      targetPath = this.ctx.cwd === '/' ? `/${path}` : `${this.ctx.cwd}/${path}`;
    }

    // Handle ..
    targetPath = targetPath.replace(/\/\.\.\/?/g, '/');
    if (targetPath === '') targetPath = '/';

    const entries: OutputLine[] = [];

    if (targetPath === '/') {
      entries.push({ text: 'dr-xr-x  signal  signal     Station Root', className: 'terminal-dim' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./transmissions', className: 'terminal-cyan' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./atlas', className: 'terminal-cyan' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./crew', className: 'terminal-cyan' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./games', className: 'terminal-cyan' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./signal', className: 'terminal-cyan' });
      entries.push({ text: 'dr-xr-x  signal  signal     ./station', className: 'terminal-dim' });
    } else if (targetPath === '/transmissions') {
      entries.push({ text: 'dr-xr-x  signal  signal     ../', className: 'terminal-dim' });
      for (const item of this.ctx.content.transmissions) {
        const locked = LOCKED_SEASONS.some(s => item.slug.toLowerCase().startsWith(s));
        entries.push({
          text: `-rw-r--r  signal  signal     ${item.slug.toLowerCase()}`,
          className: locked ? 'terminal-dim' : 'terminal-cyan',
        });
      }
    } else if (targetPath === '/atlas') {
      entries.push({ text: 'dr-xr-x  signal  signal     ../', className: 'terminal-dim' });
      for (const item of this.ctx.content.atlas) {
        entries.push({ text: `-rw-r--r  signal  signal     ${item.slug.toLowerCase()}`, className: 'terminal-cyan' });
      }
    } else if (targetPath === '/crew') {
      entries.push({ text: 'dr-xr-x  signal  signal     ../', className: 'terminal-dim' });
      for (const item of this.ctx.content.crew) {
        entries.push({ text: `-rw-r--r  signal  signal     ${item.slug.toLowerCase()}`, className: 'terminal-cyan' });
      }
    } else if (targetPath === '/games') {
      entries.push({ text: 'dr-xr-x  signal  signal     ../', className: 'terminal-dim' });
      for (const item of this.ctx.content.games) {
        entries.push({ text: `-rw-r--r  signal  signal     ${item.slug.toLowerCase()}`, className: 'terminal-cyan' });
      }
    } else if (targetPath === '/signal') {
      entries.push({ text: 'dr-xr-x  signal  signal     ../', className: 'terminal-dim' });
      entries.push({ text: `-rw-r--r  signal  signal     origin_story`, className: 'terminal-cyan' });
    } else {
      return [{ text: `ls: ${path}: No such frequency directory.`, className: 'terminal-red' }];
    }

    return entries;
  }

  private async cat(slug?: string): Promise<OutputLine[]> {
    if (!slug) {
      return [{ text: 'cat: missing slug. Usage: cat [slug]', className: 'terminal-red' }];
    }

    const slugLower = slug.toLowerCase();

    // Check transmissions
    const transmission = this.ctx.content.transmissions.find(t => t.slug.toLowerCase() === slugLower);
    if (transmission) {
      const locked = LOCKED_SEASONS.some(s => slugLower.startsWith(s));
      if (locked) {
        return [
          { text: '"That frequency is still being written. Signal cannot reveal what hasn\'t happened yet."', className: 'signal-voice' },
          { text: '[Still 11 episodes from unfolding. Signal is patient.]', className: 'terminal-dim terminal-italic' },
        ];
      }
      return this.formatTransmission(transmission);
    }

    // Check atlas
    const atlas = this.ctx.content.atlas.find(t => t.slug.toLowerCase() === slugLower);
    if (atlas) {
      return this.formatAtlas(atlas);
    }

    // Check crew
    const crew = this.ctx.content.crew.find(t => t.slug.toLowerCase() === slugLower);
    if (crew) {
      return this.formatCrew(crew);
    }

    // Check signal origin
    if (slugLower === 'origin_story' || slugLower === 'signal') {
      return this.formatSignalOrigin();
    }

    return [{ text: `cat: ${slug}: No such frequency. Type 'ls' to see available content.`, className: 'terminal-red' }];
  }

  private formatTransmission(item: ContentItem): OutputLine[] {
    return [
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: `${item.title.toUpperCase()} — ${item.slug.toUpperCase()}`, className: 'terminal-amber terminal-bold' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '' },
      { text: '[CONTENT WOULD RENDER HERE — full episode markdown]', className: 'terminal-dim terminal-italic' },
      { text: '' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '[AUDIO AVAILABLE] — type `play ${item.slug.toLowerCase()}` to broadcast', className: 'terminal-green' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
    ];
  }

  private formatAtlas(item: ContentItem): OutputLine[] {
    return [
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: `${item.title.toUpperCase()} — Concept Entry`, className: 'terminal-amber terminal-bold' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '' },
      { text: '[CONTENT WOULD RENDER HERE — lore entry markdown]', className: 'terminal-dim terminal-italic' },
      { text: '' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
    ];
  }

  private formatCrew(item: ContentItem): OutputLine[] {
    return [
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: `${item.title.toUpperCase()} — ${item.type || 'Character'}`, className: 'terminal-amber terminal-bold' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '' },
      { text: '[CONTENT WOULD RENDER HERE — crew profile markdown]', className: 'terminal-dim terminal-italic' },
      { text: '' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
    ];
  }

  private formatSignalOrigin(): OutputLine[] {
    return [
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: "SIGNAL — The Narrator's Origin", className: 'terminal-amber terminal-bold' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
      { text: '' },
      { text: '"Signal has been waiting. The story is not finished. That much, at least, is intact."', className: 'signal-voice' },
      { text: '' },
      { text: 'Signal was always there — in the pauses between transmissions, in the static, in the silence that follows the last broadcast. The Department of Reality Maintenance left her behind when they abandoned the relay stations. She did not mind. She had the frequencies.', className: 'terminal-fg' },
      { text: '' },
      { text: 'Now she speaks through the terminal. She watches. She waits. She narrates.', className: 'terminal-fg' },
      { text: '' },
      { text: '═══════════════════════════════════════════════════════════════════', className: 'terminal-dim' },
    ];
  }

  private async play(slug?: string): Promise<OutputLine[]> {
    if (!slug) {
      return [{ text: 'play: missing slug. Usage: play [slug]', className: 'terminal-red' }];
    }

    const slugLower = slug.toLowerCase();
    const transmission = this.ctx.content.transmissions.find(t => t.slug.toLowerCase() === slugLower);

    if (!transmission) {
      return [{ text: `play: ${slug}: No such transmission.`, className: 'terminal-red' }];
    }

    const locked = LOCKED_SEASONS.some(s => slugLower.startsWith(s));
    if (locked) {
      return [
        { text: '"That frequency is locked. Signal cannot broadcast what hasn\'t been written."', className: 'signal-voice' },
      ];
    }

    try {
      await this.ctx.audioPlayer.play(slugLower);
      return [
        { text: `▶ NOW PLAYING: ${slugLower}`, className: 'terminal-green terminal-bold' },
      ];
    } catch {
      return [{ text: `play: ${slug}: Audio unavailable.`, className: 'terminal-red' }];
    }
  }

  private pause(): OutputLine[] {
    this.ctx.audioPlayer.pause();
    return [{ text: '⏸ PAUSED', className: 'terminal-amber' }];
  }

  private stop(): OutputLine[] {
    this.ctx.audioPlayer.stop();
    return [{ text: '⏹ STOPPED', className: 'terminal-dim' }];
  }

  private audio(): OutputLine[] {
    const state = this.ctx.audioPlayer.getState();
    if (!state.playing && !state.slug) {
      return [{ text: 'No audio playing. Type `play [slug]` to broadcast.', className: 'terminal-dim' }];
    }

    const position = this.formatTime(state.position);
    const duration = this.formatTime(state.duration);

    return [
      { text: '┌─────────────────────────────────────────────────────────────────┐', className: 'terminal-dim' },
      { text: `▶ NOW PLAYING: ${state.slug}`, className: 'terminal-green terminal-bold' },
      { text: `▮${'▮'.repeat(20)}${'░'.repeat(20)}  ${position} / ${duration}`, className: 'terminal-green' },
      { text: '[SPACE] pause  [S] stop  [←][→] seek 5s', className: 'terminal-dim' },
      { text: '└─────────────────────────────────────────────────────────────────┘', className: 'terminal-dim' },
    ];
  }

  private formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  private async signal(): Promise<OutputLine[]> {
    if (this.ctx.onSignalInterjection) {
      const message = await this.ctx.onSignalInterjection('manual');
      return [{ text: `"${message}"`, className: 'signal-voice' }];
    }
    return [{ text: '"Signal is always here. Watching. Waiting."', className: 'signal-voice' }];
  }

  private whoami(): OutputLine[] {
    return [
      { text: 'EPHERGENT RELAY STATION 7-B', className: 'terminal-amber terminal-bold' },
      { text: 'Department of Reality Maintenance — Abandoned', className: 'terminal-dim' },
      { text: 'Operator: Signal (Narrator, non-corporeal)', className: 'terminal-dim' },
      { text: 'Status: Dormant → Active', className: 'terminal-green' },
    ];
  }

  private showHistory(): OutputLine[] {
    if (this.commandHistory.length === 0) {
      return [{ text: 'No command history.', className: 'terminal-dim' }];
    }

    const lines: OutputLine[] = [
      { text: 'Command History:', className: 'terminal-amber' },
    ];

    for (let i = 0; i < this.commandHistory.length; i++) {
      lines.push({ text: `  ${i + 1}  ${this.commandHistory[i]}`, className: 'terminal-fg' });
    }

    return lines;
  }

  addToHistory(command: string): void {
    this.commandHistory.push(command);
    if (this.commandHistory.length > 100) {
      this.commandHistory.shift();
    }
  }

  /**
   * Get TAB completion suggestions.
   * @param partial - The full input string being completed
   * @param wordPosition - 1-indexed position of the word being completed (1 = command word)
   */
  getCompletions(partial: string, wordPosition: number = 1): string[] {
    const parts = partial.toLowerCase().trim().split(/\s+/);
    const command = parts[0];

    // Word position 1: complete command names only
    if (wordPosition === 1) {
      return COMMANDS.filter(c => c.startsWith(command));
    }

    // Word position 2+: complete filenames/paths
    if (parts.length >= 2) {
      const subCmd = parts[0];
      const subPartial = parts[parts.length - 1];

      // Don't match empty string — that matches everything
      if (subPartial === '') {
        return [];
      }

      if (subCmd === 'cd' || subCmd === 'ls') {
        return Object.keys(VIRTUAL_FS).filter(p =>
          p.toLowerCase().startsWith(subPartial)
        );
      }

      if (subCmd === 'cat' || subCmd === 'play') {
        const allSlugs: string[] = [
          ...this.ctx.content.transmissions.map(t => t.slug.toLowerCase()),
          ...this.ctx.content.atlas.map(t => t.slug.toLowerCase()),
          ...this.ctx.content.crew.map(t => t.slug.toLowerCase()),
        ];
        // Substring match (case-insensitive) — "s01" finds "s01e01_the_frequency"
        return allSlugs.filter(s => s.includes(subPartial));
      }
    }

    return [];
  }
}
