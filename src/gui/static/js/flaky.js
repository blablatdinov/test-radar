// SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
// SPDX-License-Identifier: MIT

const MIN_RUNS = 5;
const MIN_PAIRS_FOR_TRANSITION = 2;
const FLAKY_TRANSITION_RATE = 0.4;
const FLAKY_MIN_FAILURE_RATIO = 0.15;
const FLAKY_MAX_FAILURE_RATIO = 0.85;

function transitionRate(outcomes) {
  if (outcomes.length < MIN_PAIRS_FOR_TRANSITION) {
    return 0;
  }
  let transitions = 0;
  for (let i = 1; i < outcomes.length; i++) {
    if (outcomes[i] !== outcomes[i - 1]) {
      transitions++;
    }
  }
  return transitions / (outcomes.length - 1);
}

function hasSameCommitInconsistency(records) {
  const commitOutcomes = new Map();
  for (const rec of records) {
    const hash = rec.commitHash || '';
    if (!commitOutcomes.has(hash)) {
      commitOutcomes.set(hash, new Set());
    }
    commitOutcomes.get(hash).add(rec.success);
  }
  for (const outcomes of commitOutcomes.values()) {
    if (outcomes.size > 1) {
      return true;
    }
  }
  return false;
}

function isFlakyByTransition(rate, failureRatio) {
  return rate >= FLAKY_TRANSITION_RATE
    && failureRatio >= FLAKY_MIN_FAILURE_RATIO
    && failureRatio <= FLAKY_MAX_FAILURE_RATIO;
}

function isLabelFlaky(records) {
  if (records.length < MIN_RUNS) {
    return false;
  }
  const outcomes = records.map((r) => r.success);
  const failures = outcomes.filter((s) => !s).length;
  const total = outcomes.length;
  if (failures === 0 || failures === total) {
    return false;
  }
  const failureRatio = failures / total;
  const rate = transitionRate(outcomes);
  if (hasSameCommitInconsistency(records)) {
    return true;
  }
  return isFlakyByTransition(rate, failureRatio);
}

function collectRowRecords(row) {
  const cells = row.querySelectorAll('td a[data-success]');
  return Array.from(cells).map((cell) => ({
    success: cell.dataset.success === 'true',
    commitHash: cell.dataset.commit || '',
  }));
}

function applyFlakyBadges() {
  const rows = document.querySelectorAll('tr[data-label]');
  rows.forEach((row) => {
    const records = collectRowRecords(row);
    if (isLabelFlaky(records)) {
      const badge = row.querySelector('.flaky-badge');
      if (badge) {
        badge.classList.remove('hidden');
        badge.classList.add('inline-block');
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', applyFlakyBadges);
