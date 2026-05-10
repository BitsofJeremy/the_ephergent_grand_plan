import { type Page, type Locator, expect } from '@playwright/test';

export class TerminalPage {
  readonly page: Page;
  readonly inputEl: Locator;
  readonly outputEl: Locator;
  readonly promptEl: Locator;

  constructor(page: Page) {
    this.page = page;
    this.inputEl = page.locator('.terminal-input');
    this.outputEl = page.locator('.terminal-output');
    this.promptEl = page.locator('.terminal-prompt');
  }

  async goto(): Promise<void> {
    await this.page.goto('/');
  }

  async input(text: string): Promise<void> {
    await this.inputEl.fill(text);
  }

  async pressEnter(): Promise<void> {
    await this.inputEl.press('Enter');
  }

  async pressTab(): Promise<void> {
    await this.inputEl.press('Tab');
  }

  async pressArrowUp(): Promise<void> {
    await this.inputEl.press('ArrowUp');
  }

  async pressArrowDown(): Promise<void> {
    await this.inputEl.press('ArrowDown');
  }

  async pressCtrlC(): Promise<void> {
    await this.inputEl.press('Control+c');
  }

  async pressCtrlL(): Promise<void> {
    await this.inputEl.press('Control+l');
  }

  async pressEscape(): Promise<void> {
    await this.inputEl.press('Escape');
  }

  /**
   * Get all output line text content as an array.
   */
  async getOutput(): Promise<string[]> {
    const lines = await this.outputEl.locator('.terminal-text').allTextContents();
    return lines;
  }

  /**
   * Get the current prompt text.
   */
  async getPromptText(): Promise<string> {
    return this.promptEl.textContent() ?? '';
  }

  /**
   * Wait for output to contain a string (substring match).
   */
  async waitForOutputContains(text: string, timeout = 5000): Promise<void> {
    await expect(this.outputEl).toContainText(text, { timeout });
  }

  /**
   * Wait for output NOT to contain a string.
   */
  async waitForOutputNotContains(text: string, timeout = 5000): Promise<void> {
    await expect(this.outputEl).not.toContainText(text, { timeout });
  }

  /**
   * Execute a command: type it and press Enter.
   */
  async runCommand(command: string): Promise<void> {
    await this.inputEl.fill(command);
    await this.pressEnter();
  }

  /**
   * Count how many tab menu lines are visible.
   * Tab menu lines have class 'terminal-amber' and format "  N. slug"
   */
  async getTabMenuCount(): Promise<number> {
    const lines = await this.outputEl.locator('.terminal-text.terminal-amber').allTextContents();
    // Filter to lines matching menu format "  N. "
    const menuLines = lines.filter(l => /^\s+\d+\.\s/.test(l));
    return menuLines.length;
  }

  /**
   * Wait for tab completion menu to appear.
   * Menu items have class 'terminal-amber' and format "  N. slug"
   */
  async waitForTabMenu(timeout = 3000): Promise<void> {
    // Wait for at least one amber menu line to be visible
    await expect(this.outputEl.locator('.terminal-text.terminal-amber').first()).toBeVisible({ timeout });
  }

  /**
   * Submit the current input and wait for the tab menu to appear.
   * Then type a number and press Enter to select an item.
   */
  async selectTabMenuItem(n: number): Promise<void> {
    // Tab menu is already shown; type the number and Enter
    await this.inputEl.fill(String(n));
    await this.pressEnter();
  }

  /**
   * Get the input value.
   */
  async getInputValue(): Promise<string> {
    return this.inputEl.inputValue();
  }

  /**
   * Wait for input to be focused.
   */
  async waitForInputFocused(): Promise<void> {
    await expect(this.inputEl).toBeFocused();
  }

  /**
   * Clear the output.
   */
  async clearOutput(): Promise<void> {
    await this.pressCtrlL();
  }
}
