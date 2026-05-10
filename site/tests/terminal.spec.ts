import { test, expect, type Page } from '@playwright/test';
import { TerminalPage } from './pageobjects/terminal';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Wait for the terminal to be fully booted and input ready */
async function waitForBooted(terminal: TerminalPage): Promise<void> {
  await terminal.goto();
  await terminal.waitForInputFocused();
}

/** Return the terminal output lines from the most recent command (excludes boot noise) */
async function getRecentOutput(terminal: TerminalPage, afterText: string): Promise<string[]> {
  const all = await terminal.getOutput();
  const idx = all.findIndex(l => l.includes(afterText));
  return idx >= 0 ? all.slice(idx) : all;
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

test('boot sequence renders terminal and focuses input', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await terminal.goto();
  await expect(terminal.outputEl).toBeVisible();
  await expect(terminal.inputEl).toBeFocused();
});

// ---------------------------------------------------------------------------
// Core Commands
// ---------------------------------------------------------------------------

test('help command displays command reference', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  const outputBefore = await terminal.getOutput();
  await terminal.runCommand('help');
  const outputAfter = await terminal.getOutput();
  expect(outputAfter.length).toBeGreaterThan(outputBefore.length);
});

test('pwd shows current directory', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('pwd');
  await terminal.waitForOutputContains('/transmissions');
});

test('cd /transmissions changes prompt', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('cd /atlas');
  const prompt = await terminal.getPromptText();
  expect(prompt).toContain('/atlas');
});

test('cd /atlas shows Signal voice navigation message', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('cd /atlas');
  await terminal.waitForOutputContains('Signal');
});

test('ls shows directory entries', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('ls');
  const output = await terminal.getOutput();
  const joined = output.join(' ');
  expect(joined).toMatch(/\.\.\/|transmissions|atlas|crew/);
});

test('ls /atlas lists atlas entries', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('ls /atlas');
  await terminal.waitForOutputContains('atlas');
});

// ---------------------------------------------------------------------------
// cat command
// ---------------------------------------------------------------------------

test('cat s01e01_the_frequency shows episode content', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('cat s01e01_the_frequency');
  // Should show episode title or "FREQUENCY"
  await terminal.waitForOutputContains(/FREQUENCY|Signal|The Ephergent/i);
});

test('cat nonexistent shows error', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('cat no_such_slug_xyz');
  await terminal.waitForOutputContains(/no such frequency|cat: no/i);
});

test('cat with no args produces output', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  const outputBefore = await terminal.getOutput();
  await terminal.runCommand('cat');
  const outputAfter = await terminal.getOutput();
  // Should produce at least the command echo line
  expect(outputAfter.length).toBeGreaterThan(outputBefore.length);
});

// ---------------------------------------------------------------------------
// play / audio
// ---------------------------------------------------------------------------

test('play s01e01_the_frequency triggers now-playing or valid response', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  const outputBefore = await terminal.getOutput();
  await terminal.runCommand('play s01e01_the_frequency');
  const outputAfter = await terminal.getOutput();
  expect(outputAfter.length).toBeGreaterThan(outputBefore.length);
});

// ---------------------------------------------------------------------------
// Signal Voice
// ---------------------------------------------------------------------------

test('signal command shows Signal interjection', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('signal');
  await terminal.waitForOutputContains('Signal');
});

// ---------------------------------------------------------------------------
// History Navigation
// ---------------------------------------------------------------------------

test('arrow up recalls previous command', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('help');
  await terminal.inputEl.press('ArrowUp');
  const val = await terminal.getInputValue();
  expect(val).toContain('help');
});

test('arrow down after arrow up returns to empty', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('help');
  await terminal.inputEl.press('ArrowUp');
  await terminal.inputEl.press('ArrowDown');
  const val = await terminal.getInputValue();
  expect(val).toBe('');
});

// ---------------------------------------------------------------------------
// Ctrl keys
// ---------------------------------------------------------------------------

test('Ctrl+C cancels input', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('partial command');
  await terminal.pressCtrlC();
  await terminal.waitForOutputContains('^C');
  const val = await terminal.getInputValue();
  expect(val).toBe('');
});

test('Ctrl+L clears output', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.runCommand('help');
  await terminal.pressCtrlL();
  const output = await terminal.getOutput();
  // After Ctrl+L, output should be empty
  expect(output).toHaveLength(0);
});

// ---------------------------------------------------------------------------
// TAB Completion
// ---------------------------------------------------------------------------

test('TAB at word 1 ("cat") does not produce "cat cat"', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cat');
  await terminal.pressTab();
  const val = await terminal.getInputValue();
  // Must NOT be "cat cat"
  expect(val).not.toBe('cat cat');
  // Should still start with "cat"
  expect(val).toMatch(/^cat/);
});

test('TAB at word 1 ("cd") completes to "cd "', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cd');
  await terminal.pressTab();
  const val = await terminal.getInputValue();
  expect(val).toBe('cd ');
});

test('TAB with "cat " (empty arg) shows completions or does nothing', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cat ');
  await terminal.pressTab();
  // The bug was that empty string matched ALL slugs. After fix, it should
  // either complete to a specific slug or show no completions.
  // The fix returns [] for empty string, so the input stays "cat " (no change).
  const val = await terminal.getInputValue();
  expect(val).toBe('cat ');
});

test('TAB with "cat s01" substring-matches episode', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cat s01');
  await terminal.pressTab();
  const val = await terminal.getInputValue();
  // Should complete to a slug containing "s01"
  expect(val).toMatch(/s01e\d|s01/i);
  // And should NOT be "cat cat s01..."
  expect(val).not.toMatch(/cat cat/i);
});

test('TAB with "cat s" shows multiple matches (indexed menu)', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cat s');
  await terminal.pressTab();
  // Should show 2+ amber-colored menu lines with "N. " format
  await terminal.waitForTabMenu();
  const count = await terminal.getTabMenuCount();
  expect(count).toBeGreaterThanOrEqual(2);
});

test('TAB with "cat xyznonexistent" shows Signal "no record" message', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cat xyznonexistent');
  await terminal.pressTab();
  await terminal.waitForOutputContains(/signal|no record/i);
});

test('TAB with "cd /at" completes to "cd /atlas"', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  await terminal.input('cd /at');
  await terminal.pressTab();
  const val = await terminal.getInputValue();
  expect(val).toMatch(/\/atlas/);
});

// ---------------------------------------------------------------------------
// Indexed Menu Selection
// ---------------------------------------------------------------------------

test('TAB menu: number + Enter selects item and executes it', async ({ page }) => {
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);
  // "cat s" produces multiple matches
  await terminal.input('cat s');
  await terminal.pressTab();
  await terminal.waitForTabMenu();

  // Get the menu count and pick the first item
  const count = await terminal.getTabMenuCount();
  expect(count).toBeGreaterThanOrEqual(2);

  // Type "1" and press Enter to select and execute
  await terminal.input('1');
  await terminal.pressEnter();

  // After selection + execute, we should see output from the cat command
  // (not an error about unknown command)
  await terminal.waitForOutputContains(/FREQUENCY|transmission|Signal/i);
});

// ---------------------------------------------------------------------------
// DoRM Intrusions (probabilistic — tagged)
// ---------------------------------------------------------------------------

test('DoRM ghost appears on some commands', async ({ page }) => {
  test.skip(!process.env.RUN_DORM_TESTS, 'Set RUN_DORM_TESTS=1 to enable DoRM tests');
  const terminal = new TerminalPage(page);
  await waitForBooted(terminal);

  let dormFound = false;
  for (let i = 0; i < 20; i++) {
    await terminal.runCommand('ls');
    const output = await terminal.getOutput();
    const hasDorm = output.some(l => /FORM|DORM|compliance|auditing/i.test(l));
    if (hasDorm) {
      dormFound = true;
      break;
    }
  }
  expect(dormFound).toBe(true);
});
