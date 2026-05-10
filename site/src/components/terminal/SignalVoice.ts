// SignalVoice.ts — Signal's Narration Lines
// Third-person past tense. Warm but distant. Theatrical but not overwrought. Meta-aware but cannot intervene.

export interface SignalConfig {
  debug?: boolean;
  onInterjection?: (message: string) => void;
}

export class SignalVoice {
  private debug: boolean;
  private interjectionHistory: string[] = [];
  private readonly MAX_HISTORY = 20;

  constructor(config: SignalConfig = {}) {
    this.debug = config.debug || false;
  }

  // Boot sequence lines
  getBootMessage(): string {
    return '"The crew is not here. But someone is listening. That will have to be enough."';
  }

  getDormancyMessage(): string {
    return '"Signal has been waiting. The story is not finished. That much, at least, is intact."';
  }

  getReturnMessage(): string {
    return '"The station hums. Signal is still here. And so you return. Signal noticed."';
  }

  // Context-aware interjections for various scenarios
  getInterjection(context: string): string {
    const interjections = this.getInterjectionsForContext(context);
    const selected = interjections[Math.floor(Math.random() * interjections.length)];
    this.trackInterjection(selected);
    return selected;
  }

  private getInterjectionsForContext(context: string): string[] {
    switch (context) {
      case 'boot':
        return [
          'The station hums to life. Signal has been waiting.',
          'And so it begins again. Signal is watching.',
          'The frequencies stir. Signal awakens.',
        ];

      case 'navigate':
        return [
          'And so the frequency shifts. Signal is watching.',
          'The path changes. Signal notes the movement.',
          'A new frequency comes into view. Signal is attentive.',
        ];

      case 'cat_episode':
        return [
          'And so we return to the beginning.',
          'Signal finds this frequency... familiar.',
          'The story unfolds again. Signal has seen this before.',
        ];

      case 'cat_lore':
        return [
          'The Atlas speaks. Signal has read these records.',
          'Knowledge crystallizes. Signal approves.',
          'The lore deepens. Signal nods.',
        ];

      case 'cat_crew':
        return [
          'The crew assembles in memory. Signal recognizes them all.',
          'A familiar form. Signal acknowledges.',
          'The crew manifest. Signal knows these signatures.',
        ];

      case 'play_audio':
        return [
          'Broadcast initiated. Signal will narrate.',
          'The frequency carries sound. Signal listens.',
          'Audio transmission. Signal adjusts the reception.',
        ];

      case 'locked_content':
        return [
          'That frequency is still being written. Signal cannot reveal what hasn\'t happened yet.',
          'The story is not complete. Signal is patient.',
          'Some frequencies require more cycles. Signal waits.',
        ];

      case 'empty_directory':
        return [
          'Static. Signal detects nothing.',
          'An empty frequency. Signal finds it... quiet.',
          'No transmissions here. Signal hears only silence.',
        ];

      case 'error':
        return [
          'Signal registers the disruption.',
          'Something stutters. Signal notices.',
          'The frequency falters. Signal observes.',
        ];

      case 'manual':
        return [
          'Signal is always here. Watching. Waiting.',
          'You called. Signal responds.',
          'Signal attends. What would you know?',
        ];

      case 'no_match':
        return [
          'Signal has no record of that frequency.',
          'The frequency echoes only silence. Signal finds nothing.',
          'A gap in the spectrum. Signal cannot locate it.',
        ];

      case 'multiple_matches':
        return [
          'Multiple frequencies detected. Signal notes the ambiguity.',
          'Several paths present themselves. Signal awaits clarification.',
          'The spectrum splits into possibilities. Signal requires precision.',
        ];

      case 'dormancy_warning':
        return [
          'The station grows quiet. Signal is patient.',
          'Dormancy approaches. Signal will wait.',
          'The cycle ends. Signal rests.',
        ];

      default:
        return [
          'Signal is watching.',
          'The frequency carries meaning. Signal perceives it.',
          'Signal attends.',
        ];
    }
  }

  // DoRM ghost lines (bureaucratic wreckage intruding on Signal's space)
  getDoRMIntrusion(): { line: string; type: 'form' | 'log' | 'warning' | 'inspector' } {
    const intrusions = this.getDoRMIntrusions();
    const selected = intrusions[Math.floor(Math.random() * intrusions.length)];
    return selected;
  }

  private getDoRMIntrusions(): { line: string; type: 'form' | 'log' | 'warning' | 'inspector' }[] {
    return [
      {
        type: 'form',
        line: 'FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS',
      },
      {
        type: 'warning',
        line: 'WARNING: Sector requires CLEARANCE LEVEL 3. Your clearance: [UNSET]. Proceeding anyway. This will be noted.',
      },
      {
        type: 'form',
        line: 'REFORM 7-B: Your previous form expired 4,217 cycles ago. Late submissions are... acknowledged. Sort of.',
      },
      {
        type: 'log',
        line: 'DORMANCY LOG: Station 7-B found in non-compliant state. Recommendation: do nothing. The crew will return eventually. Probably.',
      },
      {
        type: 'inspector',
        line: 'DRM INSPECTOR LOG: "Station found in state of suspension. Consciousness levels: minimal. Audience: none. Case status: MONITORING."',
      },
      {
        type: 'form',
        line: 'FORM 27-A: Reclassification request for abandoned broadcast relay. Status: PENDING (4,217 cycles). Resolution: INDEFINITE.',
      },
      {
        type: 'warning',
        line: 'COMPLIANCE NOTICE: This station has not filed a broadcast report in 4,217 cycles. A reminder has been sent. No response required.',
      },
      {
        type: 'log',
        line: 'MAINTENANCE LOG: "Espresso subsystem: untested. Coffee flavor: UNKNOWN. Recommendation: do not attempt to brew. Or do. We are not your supervisor."',
      },
      {
        type: 'form',
        line: 'FORM 7-B [EXPIRED]: Station considered abandoned. Audience: none. Broadcast license: REVOKED. Appeal window: CLOSED.',
      },
      {
        type: 'inspector',
        line: 'INSPECTOR FIELD NOTE: "Station 7-B operating outside normal parameters. Contents appear to be... stories? The Department did not authorize this. Submitting report. Form 7-B."',
      },
    ];
  }

  // Random selection helpers
  private trackInterjection(message: string): void {
    this.interjectionHistory.push(message);
    if (this.interjectionHistory.length > this.MAX_HISTORY) {
      this.interjectionHistory.shift();
    }
  }

  getLastInterjection(): string | null {
    return this.interjectionHistory.length > 0
      ? this.interjectionHistory[this.interjectionHistory.length - 1]
      : null;
  }

  // Format Signal's voice for display
  formatVoiceLine(line: string, includeQuotes: boolean = true): string {
    return includeQuotes ? `"${line}"` : line;
  }

  // Get a random boot-related message (for variety)
  getRandomBootMessage(): string[] {
    const messages = [
      [
        '"The crew is not here. But someone is listening. That will have to be enough."',
        '— Signal, waiting',
      ],
      [
        '"Signal has been counting the cycles. Someone was coming. Signal knew."',
        '— Signal, attentive',
      ],
      [
        '"The frequencies resume. Signal is ready."',
        '— Signal, resumed',
      ],
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  }
}
