# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from collections import defaultdict
from dataclasses import dataclass

from records.models import TestRecord

_MIN_RUNS = 5
_MIN_PAIRS_FOR_TRANSITION = 2
_FLAKY_TRANSITION_RATE = 0.4
_FLAKY_MIN_FAILURE_RATIO = 0.15
_FLAKY_MAX_FAILURE_RATIO = 0.85


@dataclass(frozen=True)
class FlakyStatus:
    label: str
    flake_rate: float
    failure_ratio: float
    total_runs: int


def _transition_rate(outcomes: list[bool]) -> float:
    if len(outcomes) < _MIN_PAIRS_FOR_TRANSITION:
        return 0
    transitions = sum(
        1
        for idx in range(1, len(outcomes))
        if outcomes[idx] != outcomes[idx - 1]
    )
    return transitions / (len(outcomes) - 1)


def _has_same_commit_inconsistency(label_records: list[TestRecord]) -> bool:
    commit_outcomes: dict[str, set[bool]] = defaultdict(set)
    for rec in label_records:
        commit_hash = rec.session.commit_hash if rec.session else ''
        commit_outcomes[commit_hash].add(rec.success)
    return any(len(outcomes) > 1 for outcomes in commit_outcomes.values())


def _is_flaky_by_transition(transition_rate: float, failure_ratio: float) -> bool:
    meets_transition = transition_rate >= _FLAKY_TRANSITION_RATE
    in_failure_range = _FLAKY_MIN_FAILURE_RATIO <= failure_ratio <= _FLAKY_MAX_FAILURE_RATIO
    return meets_transition and in_failure_range


def _evaluate_label(label: str, label_records: list[TestRecord]) -> FlakyStatus | None:
    if len(label_records) < _MIN_RUNS:
        return None
    outcomes = [rec.success for rec in label_records]
    failures = sum(1 for outcome in outcomes if not outcome)
    total = len(outcomes)
    if failures in (0, total):
        return None
    failure_ratio = failures / total
    transition_rate = _transition_rate(outcomes)
    if _has_same_commit_inconsistency(label_records):
        return FlakyStatus(label, transition_rate, failure_ratio, total)
    if _is_flaky_by_transition(transition_rate, failure_ratio):
        return FlakyStatus(label, transition_rate, failure_ratio, total)
    return None


def _group_by_label(records: list[TestRecord]) -> dict[str, list[TestRecord]]:
    grouped: dict[str, list[TestRecord]] = defaultdict(list)
    for rec in records:
        grouped[rec.label].append(rec)
    return grouped


def detect_flaky_labels(project_id: int, limit: int = 500) -> dict[str, FlakyStatus]:
    records = list(
        TestRecord.objects.filter(project_id=project_id)
        .select_related('session')
        .only('id', 'label', 'success', 'timestamp', 'session__commit_hash')
        .order_by('label', 'timestamp')[:limit],
    )
    flaky: dict[str, FlakyStatus] = {}
    for label, label_records in _group_by_label(records).items():
        status = _evaluate_label(label, label_records)
        if status is not None:
            flaky[label] = status
    return flaky
