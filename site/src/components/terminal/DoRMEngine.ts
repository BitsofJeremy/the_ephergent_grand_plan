// DoRMEngine.ts — Department of Reality Maintenance Ghost Intrusions
// ~25% of commands surface a DoRM artifact — comedy from collision between warm broadcast station and cold bureaucratic wreckage

import type { OutputLine } from './Terminal';

export interface DoRMConfig {
  frequency?: number; // 0.0 to 1.0 — probability of intrusion
  debug?: boolean;
}

export class DoRMEngine {
  private frequency: number;
  private debug: boolean;
  private intrusionCount: number = 0;

  constructor(config: DoRMConfig = {}) {
    this.frequency = config.frequency ?? 0.25;
    this.debug = config.debug || false;
  }

  // Should we trigger a DoRM intrusion?
  shouldIntrude(): boolean {
    if (this.debug) {
      return Math.random() < 0.5; // 50% in debug mode
    }
    return Math.random() < this.frequency;
  }

  // Get a random DoRM artifact
  getIntrusion(): OutputLine[] {
    this.intrusionCount++;

    const artifacts = this.getArtifacts();
    const selected = artifacts[Math.floor(Math.random() * artifacts.length)];

    return [{
      text: selected,
      className: 'dorm-ghost',
    }];
  }

  private getArtifacts(): string[] {
    return [
      'FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS',
      'WARNING: Sector requires CLEARANCE LEVEL 3. Your clearance: [UNSET]. Proceeding anyway. This will be noted.',
      'REFORM 7-B: Your previous form expired 4,217 cycles ago. Late submissions are... acknowledged. Sort of.',
      'DORMANCY LOG: Station 7-B found in non-compliant state. Recommendation: do nothing. The crew will return eventually. Probably.',
      'DRM INSPECTOR LOG: "Station 7-B found in non-compliant state. Recommendation: do nothing. The crew will return eventually. Probably."',
      'FORM 27-A: Reclassification request for abandoned broadcast relay. Status: PENDING (4,217 cycles). Resolution: INDEFINITE.',
      'COMPLIANCE NOTICE: This station has not filed a broadcast report in 4,217 cycles. A reminder has been sent. No response required.',
      'MAINTENANCE LOG: "Espresso subsystem: untested. Coffee flavor: UNKNOWN. Recommendation: do not attempt to brew. Or do. We are not your supervisor."',
      'FORM 7-B [EXPIRED]: Station considered abandoned. Audience: none. Broadcast license: REVOKED. Appeal window: CLOSED.',
      'INSPECTOR FIELD NOTE: "Station 7-B operating outside normal parameters. Contents appear to be... stories? The Department did not authorize this. Submitting report. Form 7-B."',
      'DORMANCY AUDIT: Broadcast license expired. Audience metrics: UNDEFINED. Recommendation: continue monitoring.',
      'FORM 31-C: Request for reality anchor recalibration. Status: DENIED. Reason: anchor not found. Requesting new anchor. This will take 4,217 cycles.',
      'MAINTENANCE NOTICE: Station 7-B flagged for inspection. Inspector assigned: NONE. Assignment status: LOST. Resolving...',
      'COMPLIANCE LOG: "Broadcast content review for Station 7-B: NARRATIVE QUALITY: SUSPICIOUSLY GOOD. Recommend continued non-interference."',
      'FORM 7-B REVISION: Station classification changed from "ACTIVE" to "ABANDONED" to "MAYBE RETURNING" to "MONITORING". Status update: PENDING (4,217 cycles).',
    ];
  }

  // Get context-specific intrusions
  getIntrusionForContext(context: 'boot' | 'navigate' | 'cat' | 'play' | 'error' | 'idle'): string[] {
    const contextArtifacts = this.getContextualArtifacts(context);
    return [{
      text: contextArtifacts[Math.floor(Math.random() * contextArtifacts.length)],
      className: 'dorm-ghost',
    }];
  }

  private getContextualArtifacts(context: string): string[] {
    switch (context) {
      case 'boot':
        return [
          'FORM 7-B REQUIRED FOR SECTOR ACCESS — COMPLIANCE AUDIT IN PROGRESS',
          'REFORM 7-B: Your previous form expired 4,217 cycles ago. Late submissions are... acknowledged. Sort of.',
          'FORM 7-B [EXPIRED]: Station considered abandoned. Audience: none. Broadcast license: REVOKED.',
        ];

      case 'navigate':
        return [
          'WARNING: Sector requires CLEARANCE LEVEL 3. Your clearance: [UNSET]. Proceeding anyway. This will be noted.',
          'COMPLIANCE NOTICE: This station has not filed a broadcast report in 4,217 cycles.',
          'MAINTENANCE LOG: "Espresso subsystem: untested. Coffee flavor: UNKNOWN."',
        ];

      case 'cat':
        return [
          'DORMANCY LOG: Station 7-B found in non-compliant state. Recommendation: do nothing. The crew will return eventually. Probably.',
          'INSPECTOR FIELD NOTE: "Station 7-B operating outside normal parameters. Contents appear to be... stories? The Department did not authorize this."',
          'COMPLIANCE LOG: "Broadcast content review: NARRATIVE QUALITY: SUSPICIOUSLY GOOD. Recommend continued non-interference."',
        ];

      case 'play':
        return [
          'COMPLIANCE NOTICE: Audio transmission requires FORM 31-C. Status: PENDING.',
          'DORMANCY AUDIT: Broadcast license expired. Audience metrics: UNDEFINED.',
          'MAINTENANCE NOTICE: Audio subsystem flagged for inspection. Inspector assigned: NONE.',
        ];

      case 'error':
        return [
          'ERROR LOG: An error occurred. Error type: UNKNOWN. Error form: NOT FILED. This has been noted.',
          'MAINTENANCE LOG: "Error detected. Recommendation: do not panic. Panickers will be noted."',
          'FORM 99-Z: Error report. Status: GENERATED. Distribution: NONE. Acknowledge at your convenience.',
        ];

      case 'idle':
        return [
          'COMPLIANCE NOTICE: No activity detected. Station considered dormant. This has been noted.',
          'DORMANCY LOG: Idle threshold exceeded. Recommending continued dormancy.',
          'MAINTENANCE LOG: "Station idle. Consciousness levels: minimal. Recommendation: continue being minimal."',
        ];

      default:
        return this.getArtifacts();
    }
  }

  getIntrusionCount(): number {
    return this.intrusionCount;
  }

  setFrequency(frequency: number): void {
    this.frequency = Math.max(0, Math.min(1, frequency));
  }

  setDebug(debug: boolean): void {
    this.debug = debug;
  }
}
