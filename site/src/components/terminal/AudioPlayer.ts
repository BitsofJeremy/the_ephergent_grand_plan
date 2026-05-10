// AudioPlayer.ts — Terminal-Native Audio Player
// Inline terminal block player with ASCII waveform, keyboard controls, persistent player block

export interface AudioPlayerState {
  playing: boolean;
  paused: boolean;
  slug: string | null;
  title: string | null;
  position: number;
  duration: number;
  volume: number;
}

export interface AudioPlayerConfig {
  audioBasePath?: string;
  onUpdate?: (state: AudioPlayerState) => void;
  onEnded?: () => void;
}

export class AudioPlayer {
  private audio: HTMLAudioElement | null = null;
  private state: AudioPlayerState;
  private audioBasePath: string;
  private onUpdate?: (state: AudioPlayerState) => void;
  private onEnded?: () => void;
  private updateInterval: number | null = null;

  constructor(config: AudioPlayerConfig = {}) {
    this.audioBasePath = config.audioBasePath || '/audio/';
    this.onUpdate = config.onUpdate;
    this.onEnded = config.onEnded;

    this.state = {
      playing: false,
      paused: false,
      slug: null,
      title: null,
      position: 0,
      duration: 0,
      volume: 0.89,
    };
  }

  async play(slug: string): Promise<void> {
    // Stop any existing audio
    this.stop();

    // Construct audio URL
    const audioUrl = `${this.audioBasePath}${slug}.mp3`;

    // Create audio element
    this.audio = new Audio(audioUrl);
    this.audio.volume = this.state.volume;

    // Set up event listeners
    this.audio.addEventListener('loadedmetadata', () => {
      this.state.duration = this.audio?.duration || 0;
      this.notifyUpdate();
    });

    this.audio.addEventListener('timeupdate', () => {
      this.state.position = this.audio?.currentTime || 0;
      this.notifyUpdate();
    });

    this.audio.addEventListener('ended', () => {
      this.state.playing = false;
      this.state.paused = false;
      this.stopUpdateInterval();
      this.notifyUpdate();
      if (this.onEnded) this.onEnded();
    });

    this.audio.addEventListener('error', () => {
      this.state.playing = false;
      this.stopUpdateInterval();
      this.notifyUpdate();
    });

    try {
      await this.audio.play();
      this.state.playing = true;
      this.state.paused = false;
      this.state.slug = slug;
      this.state.title = slug.replace(/-/g, ' ').replace(/s(\d+)e(\d+)/i, 'S$1E$2').toUpperCase();
      this.startUpdateInterval();
      this.notifyUpdate();
    } catch (err) {
      // Audio failed to play
      console.warn(`Audio playback failed for ${slug}:`, err);
      throw new Error('Audio unavailable');
    }
  }

  pause(): void {
    if (this.audio && this.state.playing && !this.state.paused) {
      this.audio.pause();
      this.state.paused = true;
      this.notifyUpdate();
    }
  }

  resume(): void {
    if (this.audio && this.state.playing && this.state.paused) {
      this.audio.play();
      this.state.paused = false;
      this.notifyUpdate();
    }
  }

  stop(): void {
    if (this.audio) {
      this.audio.pause();
      this.audio.src = '';
      this.audio = null;
    }
    this.state.playing = false;
    this.state.paused = false;
    this.state.slug = null;
    this.state.title = null;
    this.state.position = 0;
    this.state.duration = 0;
    this.stopUpdateInterval();
    this.notifyUpdate();
  }

  seek(seconds: number): void {
    if (this.audio) {
      const newPosition = Math.max(0, Math.min(this.audio.duration, this.audio.currentTime + seconds));
      this.audio.currentTime = newPosition;
      this.state.position = newPosition;
      this.notifyUpdate();
    }
  }

  setVolume(volume: number): void {
    this.state.volume = Math.max(0, Math.min(1, volume));
    if (this.audio) {
      this.audio.volume = this.state.volume;
    }
    this.notifyUpdate();
  }

  getState(): AudioPlayerState {
    return { ...this.state };
  }

  getPlayerBlock(): string[] {
    if (!this.state.slug) return [];

    const maxWidth = 72;
    const top = '┌' + '─'.repeat(maxWidth - 2) + '┐';
    const bottom = '└' + '─'.repeat(maxWidth - 2) + '┘';

    const stateChar = this.state.playing && !this.state.paused ? '▶' : '⏸';
    const stateColor = this.state.playing && !this.state.paused ? 'terminal-green' : 'terminal-amber';

    const positionStr = this.formatTime(this.state.position);
    const durationStr = this.formatTime(this.state.duration);

    const progressWidth = 30;
    const progress = this.state.duration > 0
      ? Math.round((this.state.position / this.state.duration) * progressWidth)
      : 0;
    const empty = progressWidth - progress;
    const progressBar = '█'.repeat(progress) + '░'.repeat(empty);

    const waveform = this.generateWaveform(40);

    const lines: string[] = [
      top,
      `│ ${stateChar} NOW PLAYING: ${(this.state.title || this.state.slug).padEnd(maxWidth - 26)}│`,
      `│ ${progressBar} ${positionStr} / ${durationStr}${' '.repeat(Math.max(0, maxWidth - 45 - positionStr.length - durationStr.length))}│`,
      `│ ${waveform.padEnd(maxWidth - 12)}│`,
      `│ [SPACE] pause  [S] stop  [←][→] seek 5s${' '.repeat(Math.max(0, maxWidth - 42))}│`,
      `│ [♪ ${Math.round(this.state.volume * 100)}% VOL]${' '.repeat(Math.max(0, maxWidth - 18))}│`,
      bottom,
    ];

    return lines;
  }

  private formatTime(seconds: number): string {
    if (!isFinite(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  private generateWaveform(length: number): string {
    const chars = ' ▁▂▃▅▆▇█▇▆▅▃▂▁';
    let result = '';
    for (let i = 0; i < length; i++) {
      const amplitude = Math.abs(Math.sin(i * 0.4 + (this.state.position || 0) * 0.1));
      const index = Math.floor(amplitude * (chars.length - 1));
      result += chars[index];
    }
    return result;
  }

  private startUpdateInterval(): void {
    if (this.updateInterval !== null) return;
    this.updateInterval = window.setInterval(() => {
      this.notifyUpdate();
    }, 500);
  }

  private stopUpdateInterval(): void {
    if (this.updateInterval !== null) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  private notifyUpdate(): void {
    if (this.onUpdate) {
      this.onUpdate(this.getState());
    }
  }

  // Handle keyboard events
  handleKeyboard(key: string): boolean {
    switch (key) {
      case ' ':
        if (this.state.playing) {
          if (this.state.paused) {
            this.resume();
          } else {
            this.pause();
          }
          return true;
        }
        break;

      case 's':
      case 'S':
        if (this.state.playing || this.state.paused) {
          this.stop();
          return true;
        }
        break;

      case 'ArrowLeft':
        if (this.state.playing || this.state.paused) {
          this.seek(-5);
          return true;
        }
        break;

      case 'ArrowRight':
        if (this.state.playing || this.state.paused) {
          this.seek(5);
          return true;
        }
        break;

      case '+':
      case '=':
        this.setVolume(this.state.volume + 0.1);
        return true;

      case '-':
      case '_':
        this.setVolume(this.state.volume - 0.1);
        return true;
    }

    return false;
  }
}
