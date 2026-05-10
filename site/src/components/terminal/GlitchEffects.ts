// GlitchEffects.ts — CRT Glitch System
// Text scramble, screen tear, flicker burst, and subtle phosphor effects

export interface GlitchConfig {
  enabled?: boolean;
  reducedMotion?: boolean;
  intensity?: 'low' | 'medium' | 'high';
}

export class GlitchEffects {
  private enabled: boolean;
  private reducedMotion: boolean;
  private intensity: number;
  private rafId: number | null = null;

  constructor(config: GlitchConfig = {}) {
    this.enabled = config.enabled !== false;
    this.reducedMotion = config.reducedMotion || false;
    this.intensity = config.intensity === 'high' ? 3 : config.intensity === 'low' ? 1 : 2;
  }

  // Text scramble effect — characters cycle randomly before resolving
  scrambleText(element: HTMLElement, originalText: string, duration: number = 200): void {
    if (!this.enabled || this.reducedMotion) {
      element.textContent = originalText;
      return;
    }

    const startTime = performance.now();
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*';

    const scramble = () => {
      const elapsed = performance.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      if (progress < 1) {
        let result = '';
        for (let i = 0; i < originalText.length; i++) {
          if (originalText[i] === ' ') {
            result += ' ';
          } else if (Math.random() > progress) {
            result += chars[Math.floor(Math.random() * chars.length)];
          } else {
            result += originalText[i];
          }
        }
        element.textContent = result;
        this.rafId = requestAnimationFrame(scramble);
      } else {
        element.textContent = originalText;
      }
    };

    scramble();
  }

  // Screen tear — single horizontal line briefly offset
  triggerScreenTear(container: HTMLElement): void {
    if (!this.enabled || this.reducedMotion) return;

    const tearLine = document.createElement('div');
    tearLine.style.cssText = `
      position: absolute;
      left: 0;
      right: 0;
      height: 3px;
      background: var(--cyan, #00d4ff);
      opacity: 0.5;
      transform: translateX(${Math.random() > 0.5 ? 5 : -5}px);
      pointer-events: none;
      z-index: 999;
    `;

    container.style.overflow = 'hidden';
    container.appendChild(tearLine);

    setTimeout(() => {
      tearLine.remove();
    }, 150);
  }

  // Flicker burst — 3 rapid opacity changes on content load
  triggerFlickerBurst(element: HTMLElement, duration: number = 300): void {
    if (!this.enabled || this.reducedMotion) return;

    const startTime = performance.now();
    const flickers = [0.3, 1, 0.5, 1, 0.7];

    const flicker = () => {
      const elapsed = performance.now() - startTime;
      const progress = elapsed / duration;

      if (progress < 1) {
        const index = Math.floor(progress * flickers.length);
        element.style.opacity = String(flickers[Math.min(index, flickers.length - 1)]);
        this.rafId = requestAnimationFrame(flicker);
      } else {
        element.style.opacity = '1';
      }
    };

    flicker();
  }

  // Apply subtle continuous flicker to container
  startSubtleFlicker(element: HTMLElement): void {
    if (!this.enabled || this.reducedMotion) return;

    let opacity = 1;
    let direction = -1;

    const flicker = () => {
      opacity += direction * 0.02;
      if (opacity <= 0.97) direction = 1;
      if (opacity >= 1) direction = -1;
      element.style.opacity = String(opacity);
      this.rafId = requestAnimationFrame(flicker);
    };

    this.rafId = requestAnimationFrame(flicker);
  }

  stopSubtleFlicker(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  // Trigger glitch on specific elements based on content type
  glitchOnContentLoad(element: HTMLElement, contentType: 'episode' | 'lore' | 'crew' | 'audio'): void {
    if (!this.enabled || this.reducedMotion) return;

    // Vary effect based on content type
    switch (contentType) {
      case 'episode':
        this.triggerFlickerBurst(element, 300);
        break;
      case 'lore':
        this.triggerFlickerBurst(element, 200);
        break;
      case 'crew':
        this.scrambleText(element, element.textContent || '', 150);
        break;
      case 'audio':
        this.triggerScreenTear(element);
        break;
    }
  }

  // DoRM ghost glitch — more intense, longer duration
  triggerDoRMGlitch(container: HTMLElement): void {
    if (!this.enabled || this.reducedMotion) return;

    // Add glitch class to body or container
    container.classList.add('dorm-glitch');

    setTimeout(() => {
      container.classList.remove('dorm-glitch');
    }, 500);
  }

  // Scanline flicker (continuous subtle effect)
  startScanlineFlicker(scanlineOverlay: HTMLElement): void {
    if (!this.enabled || this.reducedMotion) return;

    let offset = 0;
    const flicker = () => {
      offset = (offset + 1) % 4;
      scanlineOverlay.style.backgroundPosition = `0 ${offset}px`;
      this.rafId = requestAnimationFrame(flicker);
    };

    this.rafId = requestAnimationFrame(flicker);
  }

  stopScanlineFlicker(): void {
    if (this.rafId !== null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  setReducedMotion(reduced: boolean): void {
    this.reducedMotion = reduced;
  }
}
