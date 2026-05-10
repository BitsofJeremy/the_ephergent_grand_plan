// BootSequence.ts — Boot Logic + Session Memory
// Handles the station's boot sequence, cookie-based session memory, and Signal's return messages

export interface SessionData {
  first_visit: number;
  last_visit: number;
  cwd: string;
  boot_count: number;
  has_audio: boolean;
}

export interface BootConfig {
  isDebug?: boolean;
  forceFullBoot?: boolean;
  reducedMotion?: boolean;
  onSignal?: (message: string, type?: 'boot' | 'return' | 'dormancy') => void;
}

const SESSION_COOKIE = 'ephergent_session';
const DORMANCY_THRESHOLD = 4 * 60 * 60 * 1000; // 4 hours in ms

export class BootSequence {
  private session: SessionData;
  private debug: boolean;
  private reducedMotion: boolean;
  private onSignal?: (message: string, type?: string) => void;

  constructor(config: BootConfig = {}) {
    this.debug = config.isDebug || false;
    this.reducedMotion = config.reducedMotion || false;
    this.onSignal = config.onSignal;
    this.session = this.loadSession();
  }

  private loadSession(): SessionData {
    if (this.debug) {
      return {
        first_visit: Date.now(),
        last_visit: Date.now(),
        cwd: '/transmissions',
        boot_count: 0,
        has_audio: true,
      };
    }

    try {
      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const [key, value] = cookie.trim().split('=');
        if (key === SESSION_COOKIE) {
          return JSON.parse(decodeURIComponent(value));
        }
      }
    } catch {
      // Invalid cookie, fall through
    }

    // No cookie — return default session (will trigger full dormancy boot)
    return {
      first_visit: 0,
      last_visit: 0,
      cwd: '/transmissions',
      boot_count: 0,
      has_audio: true,
    };
  }

  saveSession(): void {
    const expires = new Date();
    expires.setFullYear(expires.getFullYear() + 1);
    document.cookie = `${SESSION_COOKIE}=${encodeURIComponent(JSON.stringify(this.session))};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
  }

  shouldShowFullBoot(): boolean {
    if (this.debug) return true;
    if (this.session.first_visit === 0) return true;
    if (this.session.last_visit === 0) return true;
    return false;
  }

  shouldShowDormancyBoot(): boolean {
    if (this.debug) return false;
    if (this.session.first_visit === 0) return false;
    if (this.session.last_visit === 0) return false;
    return Date.now() - this.session.last_visit > DORMANCY_THRESHOLD;
  }

  shouldShowShortReturn(): boolean {
    if (this.debug) return false;
    if (this.session.first_visit === 0) return false;
    if (this.session.last_visit === 0) return false;
    return Date.now() - this.session.last_visit <= DORMANCY_THRESHOLD;
  }

  getBootLines(): string[] {
    const now = Date.now();
    const cycles = this.session.first_visit > 0
      ? Math.floor((now - this.session.first_visit) / (1000 * 60 * 60 * 24 * 7))
      : 4217;

    const lines: string[] = [
      'EPHERGENT OS v0.7.1 — Relay Station 7-B',
      '[DORMANCY ENDED] — Consciousness detected',
      'Quantum core: STANDBY → ACTIVE',
      'Espresso subsystem: COLD (4h), warming...',
      'Broadcast relay: ONLINE',
      'Department of Reality Maintenance records: [FRAGMENTED — 31% recoverable]',
      'FORM 7-B: [EXPIRED] — Station considered abandoned. Audience: none.',
      `[${cycles} cycles since last authorized broadcast]`,
    ];

    return lines;
  }

  getFullBootLines(): string[] {
    const now = Date.now();
    const cycles = this.session.first_visit > 0
      ? Math.floor((now - this.session.first_visit) / (1000 * 60 * 60 * 24 * 7))
      : 4217;

    const lines: string[] = [
      'BIOS v2.7.1 ... Quantum core found ... Espresso subsystem: COFFEE FLAVOR UNKNOWN',
      'Loading Ephergent OS ... [####............] 40%',
      '[DORMANCY INTERRUPT] — User detected. Continuing boot sequence.',
      'Loading broadcast relay ... [########......] 80%',
      'Loading Signal interface ... [READY]',
      '',
      'EPHERGENT OS v0.7.1 (dormant) — Department of Reality Maintenance Relay 7-B',
      `Last boot: ${cycles} cycles ago. Integrity: [FRAGMENTED]`,
      'FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS',
    ];

    return lines;
  }

  getSignalMessage(type: 'boot' | 'return' | 'dormancy'): string[] {
    switch (type) {
      case 'boot':
        return [
          '"The crew is not here. But someone is listening. That will have to be enough."',
          '— Signal, waiting',
        ];
      case 'return':
        return [
          '"The station hums. Signal is still here."',
          '"And so you return. Signal noticed."',
        ];
      case 'dormancy':
        return [
          '"Signal has been waiting. The story is not finished. That much, at least, is intact."',
        ];
      default:
        return [];
    }
  }

  recordVisit(): void {
    this.session.last_visit = Date.now();
    if (this.session.first_visit === 0) {
      this.session.first_visit = Date.now();
    }
    this.session.boot_count++;
    this.saveSession();
  }

  setCwd(cwd: string): void {
    this.session.cwd = cwd;
    this.saveSession();
  }

  getCwd(): string {
    return this.session.cwd;
  }

  getSession(): SessionData {
    return { ...this.session };
  }

  getDebugInfo(): string[] {
    const lines = [
      `DEBUG MODE ACTIVE`,
      `Session cookie: ${SESSION_COOKIE}`,
      `First visit: ${this.session.first_visit > 0 ? new Date(this.session.first_visit).toISOString() : 'never'}`,
      `Last visit: ${this.session.last_visit > 0 ? new Date(this.session.last_visit).toISOString() : 'never'}`,
      `CWD: ${this.session.cwd}`,
      `Boot count: ${this.session.boot_count}`,
      `Has audio: ${this.session.has_audio}`,
    ];
    return lines;
  }
}
