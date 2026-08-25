import { describe, it, expect, beforeEach, vi } from 'vitest';

import html from './__fixtures__/flaky_table.html?raw';

describe('flaky badges', () => {
  beforeEach(async () => {
    document.body.innerHTML = html;
    vi.resetModules();
    await import('./flaky.js');
  });

  it('shows badge for commit-inconsistent flaky test', () => {
    const badge = document.querySelector(
      '[data-label="flaky-commit-inconsistency"] .flaky-badge',
    );
    expect(badge.classList.contains('inline-block')).toBe(true);
    expect(badge.classList.contains('hidden')).toBe(false);
  });

  it('hides badge for stable test', () => {
    const badge = document.querySelector(
      '[data-label="stable-test"] .flaky-badge',
    );
    expect(badge.classList.contains('hidden')).toBe(true);
    expect(badge.classList.contains('inline-block')).toBe(false);
  });

  it('hides badge when fewer than MIN_RUNS', () => {
    const badge = document.querySelector(
      '[data-label="few-runs"] .flaky-badge',
    );
    expect(badge.classList.contains('hidden')).toBe(true);
  });
});
