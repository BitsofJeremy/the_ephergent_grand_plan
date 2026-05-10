// Renderer.ts — Markdown → Terminal Text Rendering
// Converts markdown content to terminal-formatted output with ASCII art support

export interface RenderOptions {
  maxWidth?: number;
  includeHeader?: boolean;
  headerChar?: string;
}

export class Renderer {
  private maxWidth: number;
  private headerChar: string;

  constructor(options: RenderOptions = {}) {
    this.maxWidth = options.maxWidth || 72;
    this.headerChar = options.headerChar || '═';
  }

  renderMarkdown(markdown: string, options?: RenderOptions): string[] {
    const lines: string[] = [];
    const maxWidth = options?.maxWidth || this.maxWidth;

    const trimmed = markdown.trim();

    for (const line of trimmed.split('\n')) {
      const processed = this.processLine(line, maxWidth);
      lines.push(...processed);
    }

    return lines;
  }

  private processLine(line: string, maxWidth: number): string[] {
    // Headers
    if (line.startsWith('# ')) {
      const text = line.slice(2);
      return [
        '',
        this.centerText(text.toUpperCase(), maxWidth),
        this.repeatChar(this.headerChar, maxWidth),
        '',
      ];
    }

    if (line.startsWith('## ')) {
      const text = line.slice(3);
      return [
        '',
        text.toUpperCase(),
        this.repeatChar('-', text.length),
        '',
      ];
    }

    if (line.startsWith('### ')) {
      return ['', line.slice(4), ''];
    }

    // Horizontal rule
    if (line.startsWith('---') || line.startsWith('***') || line.startsWith('___')) {
      return [this.repeatChar('─', maxWidth)];
    }

    // Blockquote (Signal's voice)
    if (line.startsWith('> ')) {
      return [this.wrapText(line.slice(2), maxWidth, '  ')];
    }

    // List items
    if (line.match(/^[-*+] /)) {
      return [this.wrapText('  ' + line.slice(2), maxWidth)];
    }

    if (line.match(/^\d+\. /)) {
      return [this.wrapText('  ' + line.replace(/^\d+\. /, ''), maxWidth)];
    }

    // Code block
    if (line.startsWith('```')) {
      return []; // Skip code block markers
    }

    // Inline code
    if (line.includes('`')) {
      return [this.wrapText(line, maxWidth)];
    }

    // Bold/italic — strip markup for terminal
    const clean = line
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/_(.+?)_/g, '$1')
      .replace(/\[(.+?)\]\(.+?\)/g, '$1');

    if (clean.trim() === '') {
      return [''];
    }

    return [this.wrapText(clean, maxWidth)];
  }

  private wrapText(text: string, maxWidth: number, indent: string = ''): string {
    if (text.length <= maxWidth - indent.length) {
      return indent + text;
    }

    const words = text.split(/\s+/);
    const lines: string[] = [];
    let currentLine = indent;

    for (const word of words) {
      if (currentLine.length + word.length + 1 <= maxWidth) {
        currentLine = currentLine ? `${currentLine} ${word}` : word;
      } else {
        if (currentLine) lines.push(currentLine);
        currentLine = indent + word;
      }
    }

    if (currentLine) lines.push(currentLine);
    return lines.join('\n');
  }

  private centerText(text: string, width: number): string {
    const padding = Math.max(0, Math.floor((width - text.length) / 2));
    return ' '.repeat(padding) + text;
  }

  private repeatChar(char: string, count: number): string {
    return char.repeat(count);
  }

  renderHeader(title: string, subtitle: string = '', maxWidth: number = 72): string[] {
    const lines: string[] = [];
    const top = this.repeatChar(this.headerChar, maxWidth);

    lines.push(top);
    lines.push(this.centerText(title.toUpperCase(), maxWidth));
    if (subtitle) {
      lines.push(this.centerText(subtitle, maxWidth));
    }
    lines.push(top);

    return lines;
  }

  renderAudioBlock(slug: string, title: string, position: number, duration: number): string[] {
    const maxWidth = this.maxWidth;
    const positionStr = this.formatTime(position);
    const durationStr = this.formatTime(duration);
    const progressWidth = 30;
    const progress = Math.round((position / duration) * progressWidth);
    const empty = progressWidth - progress;

    const progressBar = '█'.repeat(progress) + '░'.repeat(empty);

    return [
      `┌${'─'.repeat(maxWidth - 2)}┐`,
      `│ ▶ NOW PLAYING: ${title.padEnd(maxWidth - 22)}│`,
      `│ ${progressBar} ${positionStr} / ${durationStr}${' '.repeat(maxWidth - 43 - positionStr.length - durationStr.length)}│`,
      `│ [SPACE] pause  [S] stop  [←][→] seek 5s${' '.repeat(Math.max(0, maxWidth - 48))}│`,
      `└${'─'.repeat(maxWidth - 2)}┘`,
    ];
  }

  private formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  generateAsciiWaveform(length: number = 40): string {
    const chars = ' ▁▂▃▅▆▇█▇▆▅▃▂▁▂▃▅▆▇█';
    let result = '';
    for (let i = 0; i < length; i++) {
      const index = Math.floor(Math.abs(Math.sin(i * 0.3)) * (chars.length - 1));
      result += chars[index];
    }
    return result;
  }
}
