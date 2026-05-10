// Terminal.ts — Core Terminal Engine
// Handles input, output, history, cursor, and the primary terminal loop

export interface TerminalState {
  cwd: string;
  history: string[];
  historyIndex: number;
  bootCount: number;
  firstVisit: number;
  lastVisit: number;
  audioPlaying: boolean;
  audioSlug: string | null;
  audioPosition: number;
  audioDuration: number;
}

export type TabCompletionState = 'IDLE' | 'MENU_ACTIVE' | 'HIGHLIGHTED';

export interface OutputLine {
  text: string;
  className?: string;
  isHtml?: boolean;
  isRaw?: boolean; // skip HTML escaping (for ASCII art)
}

export class Terminal {
  private container: HTMLElement;
  private inputEl: HTMLInputElement;
  private outputEl: HTMLElement;
  private promptEl: HTMLElement;
  private state: TerminalState;
  private commandHandlers: Map<string, (args: string[]) => Promise<OutputLine[]>>;
  private onDoRMIntrusion?: (output: OutputLine[]) => void;
  private onAudioUpdate?: (state: Partial<TerminalState>) => void;
  private onSignalVoice?: (message: string) => void;

  // TAB completion state machine
  private tabCompletionState: TabCompletionState = 'IDLE';
  private tabMenuItems: string[] = [];
  private tabMenuIndex: number = -1;
  private tabTypedNumber: string = '';
  private tabMenuLineEls: HTMLDivElement[] = [];

  constructor(container: HTMLElement, initialState?: Partial<TerminalState>) {
    this.container = container;
    this.commandHandlers = new Map();

    this.state = {
      cwd: '/transmissions',
      history: [],
      historyIndex: -1,
      bootCount: 0,
      firstVisit: Date.now(),
      lastVisit: Date.now(),
      audioPlaying: false,
      audioSlug: null,
      audioPosition: 0,
      audioDuration: 0,
      ...initialState,
    };

    this.initElements();
    this.initKeyboardHandlers();
  }

  private initElements(): void {
    this.outputEl = this.container.querySelector('.terminal-output')!;
    this.inputEl = this.container.querySelector('.terminal-input')!;
    this.promptEl = this.container.querySelector('.terminal-prompt')!;
  }

  private initKeyboardHandlers(): void {
    this.inputEl.addEventListener('keydown', (e) => {
      // Handle TAB menu interactions first
      if (this.tabCompletionState !== 'IDLE') {
        if (e.key === 'Escape') {
          e.preventDefault();
          this.cancelTabCompletion();
          return;
        }
        if (e.key === 'Enter' && this.tabCompletionState === 'HIGHLIGHTED') {
          e.preventDefault();
          this.applyTabSelection();
          return;
        }
        if (e.key === 'Enter' && this.tabCompletionState === 'MENU_ACTIVE') {
          // Enter with no selection = cancel
          e.preventDefault();
          this.cancelTabCompletion();
          return;
        }
      }

      switch (e.key) {
        case 'Enter':
          this.handleCommand();
          break;
        case 'ArrowUp':
          e.preventDefault();
          this.navigateHistory(-1);
          break;
        case 'ArrowDown':
          e.preventDefault();
          this.navigateHistory(1);
          break;
        case 'Tab':
          e.preventDefault();
          this.handleTabCompletion();
          break;
        case 'l':
          if (e.ctrlKey) {
            e.preventDefault();
            this.clearOutput();
          }
          break;
        case 'c':
          if (e.ctrlKey) {
            e.preventDefault();
            this.appendOutput([{ text: '^C', className: 'terminal-cyan' }]);
          }
          break;
      }
    });
  }

  private navigateHistory(direction: number): void {
    if (this.state.history.length === 0) return;

    const newIndex = this.state.historyIndex + direction;
    if (newIndex < -1) return;
    if (newIndex >= this.state.history.length) return;

    this.state.historyIndex = newIndex;
    if (newIndex === -1) {
      this.inputEl.value = '';
    } else {
      this.inputEl.value = this.state.history[this.state.history.length - 1 - newIndex];
    }
  }

  private handleTabCompletion(): void {
    const input = this.inputEl.value;
    const cursorPos = this.inputEl.selectionStart || input.length;
    const textBeforeCursor = input.slice(0, cursorPos);
    const wordPosition = textBeforeCursor.split(/\s+/).length;

    // MENU_ACTIVE: digits type → HIGHLIGHTED
    if (this.tabCompletionState === 'MENU_ACTIVE') {
      if (/^[0-9]$/.test(e.key)) {
        this.tabCompletionState = 'HIGHLIGHTED';
        this.tabTypedNumber += e.key;
        this.tabMenuIndex = parseInt(this.tabTypedNumber, 10) - 1;
        this.updateTabMenuHighlight();
        return;
      }
    }

    const completions = this.getCompletions(input, wordPosition);

    if (completions.length === 0) {
      this.clearTabMenu();
      if (this.tabCompletionState === 'IDLE') {
        this.onSignalVoice?.('"Signal has no record of that frequency."');
      }
      this.tabCompletionState = 'IDLE';
      return;
    }

    if (completions.length === 1) {
      // Auto-insert single match
      this.clearTabMenu();
      this.tabCompletionState = 'IDLE';
      const parts = input.split(/\s+/);
      if (wordPosition === 1) {
        this.inputEl.value = completions[0] + ' ';
      } else {
        parts[parts.length - 1] = completions[0];
        this.inputEl.value = parts.join(' ');
      }
      return;
    }

    // Multiple matches → show indexed menu
    this.tabMenuItems = completions;
    this.tabTypedNumber = '';
    this.tabMenuIndex = -1;
    this.tabCompletionState = 'MENU_ACTIVE';
    this.renderTabMenu(completions);
    this.onSignalVoice?.(`"${completions.length} frequencies match. Type a number, or keep typing."`);
  }

  private renderTabMenu(items: string[]): void {
    this.clearTabMenu();
    const start = this.outputEl.children.length;

    for (let i = 0; i < items.length; i++) {
      const line = document.createElement('div');
      line.className = 'terminal-text terminal-amber';
      line.textContent = `  ${i + 1}. ${items[i]}`;
      line.dataset.tabIndex = String(i);
      this.outputEl.appendChild(line);
    }

    // Track our menu lines for later clearing
    const end = this.outputEl.children.length;
    this.tabMenuLineEls = Array.from(this.outputEl.children).slice(start, end) as HTMLDivElement[];
    this.scrollToBottom();
  }

  private updateTabMenuHighlight(): void {
    // Highlight the selected line
    this.tabMenuLineEls.forEach((line, i) => {
      if (i === this.tabMenuIndex) {
        line.classList.add('terminal-bold');
        line.classList.remove('terminal-amber');
        line.classList.add('terminal-cyan');
      } else {
        line.classList.remove('terminal-bold', 'terminal-cyan');
        line.classList.add('terminal-amber');
      }
    });
  }

  private clearTabMenu(): void {
    for (const el of this.tabMenuLineEls) {
      el.remove();
    }
    this.tabMenuLineEls = [];
    this.tabTypedNumber = '';
  }

  private applyTabSelection(): void {
    if (this.tabMenuIndex >= 0 && this.tabMenuIndex < this.tabMenuItems.length) {
      const selected = this.tabMenuItems[this.tabMenuIndex];
      const input = this.inputEl.value;
      const parts = input.split(/\s+/);
      parts[parts.length - 1] = selected;
      this.inputEl.value = parts.join(' ') + ' ';
      this.onSignalVoice?.('"And so the frequency resolves."');
    }
    this.clearTabMenu();
    this.tabCompletionState = 'IDLE';
    this.tabMenuIndex = -1;
  }

  private cancelTabCompletion(): void {
    this.clearTabMenu();
    this.tabCompletionState = 'IDLE';
    this.tabMenuIndex = -1;
    this.onSignalVoice?.('"Signal will wait."');
  }

  async handleCommand(): Promise<void> {
    const input = this.inputEl.value.trim();
    if (!input) return;

    // Echo the command
    this.appendOutput([{ text: `${this.getPrompt()} ${input}`, className: 'command-echo' }]);

    // Add to history
    this.state.history.push(input);
    this.state.historyIndex = -1;
    if (this.state.history.length > 100) {
      this.state.history.shift();
    }

    // Parse command
    const parts = input.split(/\s+/);
    const command = parts[0];
    const args = parts.slice(1);

    // Execute
    const handler = this.commandHandlers.get(command);
    if (handler) {
      try {
        const output = await handler(args);
        this.appendOutput(output);
      } catch (err) {
        this.appendOutput([{ text: `Error: ${err}`, className: 'terminal-red error-flash' }]);
      }
    } else {
      this.appendOutput([{ text: `Command not found: ${command}. Type 'help' for available commands.`, className: 'terminal-red' }]);
    }

    // Reset input
    this.inputEl.value = '';
  }

  getPrompt(): string {
    return `Signal@relay-7b:${this.state.cwd}$`;
  }

  updatePrompt(): void {
    this.promptEl.textContent = this.getPrompt();
  }

  appendOutput(lines: OutputLine[]): void {
    for (const line of lines) {
      const p = document.createElement('div');
      p.className = `terminal-text ${line.className || ''}`;
      if (line.isRaw) {
        p.innerHTML = line.text;
      } else if (line.isHtml) {
        p.innerHTML = line.text;
      } else {
        p.textContent = line.text;
      }
      this.outputEl.appendChild(p);
    }
    this.scrollToBottom();
  }

  appendHtml(html: string, className: string = ''): void {
    const div = document.createElement('div');
    div.className = className;
    div.innerHTML = html;
    this.outputEl.appendChild(div);
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  clearOutput(): void {
    this.outputEl.innerHTML = '';
  }

  registerCommand(command: string, handler: (args: string[]) => Promise<OutputLine[]>): void {
    this.commandHandlers.set(command, handler);
  }

  getState(): TerminalState {
    return { ...this.state };
  }

  updateState(updates: Partial<TerminalState>): void {
    Object.assign(this.state, updates);
  }

  setDoRMHandler(handler: (output: OutputLine[]) => void): void {
    this.onDoRMIntrusion = handler;
  }

  setAudioHandler(handler: (state: Partial<TerminalState>) => void): void {
    this.onAudioUpdate = handler;
  }

  setSignalVoiceHandler(handler: (message: string) => void): void {
    this.onSignalVoice = handler;
  }

  /**
   * Called by the terminal page to provide a getCompletions function.
   * This avoids circular dependencies between Terminal and CommandParser.
   */
  setCompletionProvider(fn: (partial: string, wordPosition: number) => string[]): void {
    this.getCompletions = fn;
  }

  private getCompletions(partial: string, wordPosition: number): string[] {
    return []; // Default no-op; replaced by setCompletionProvider
  }

  focusInput(): void {
    this.inputEl.focus();
  }
}
