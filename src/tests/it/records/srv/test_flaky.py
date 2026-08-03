# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime

import pytest
from model_bakery import baker

from records.models import Project, TestRecord, TestSession
from records.srv.flaky import detect_flaky_labels

pytestmark = [
    pytest.mark.django_db,
]


def _make_session(
    project: Project, commit_hash: str = 'abc123', index: int = 0,
) -> TestSession:
    return baker.make(
        TestSession,
        project=project,
        started_at=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(hours=index),
        commit_hash=commit_hash,
    )


def _make_record(
    project: Project,
    session: TestSession,
    label: str,
    *,
    success: bool,
    index: int = 0,
) -> TestRecord:
    return baker.make(
        TestRecord,
        label=label,
        success=success,
        timestamp=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(minutes=index),
        project=project,
        session=session,
        logs=b'',
    )


def _make_records(
    project: Project, label: str, outcomes: list[bool], commit_prefix: str = 'commit',
) -> None:
    for iteration, success in enumerate(outcomes):
        session = _make_session(
            project, commit_hash=f'{commit_prefix}{iteration}', index=iteration,
        )
        _make_record(project, session, label, success=success, index=iteration)


def test_stable_pass_not_flaky(project: Project) -> None:
    session = _make_session(project)
    for iteration in range(10):
        _make_record(project, session, 'test_stable_pass', success=True, index=iteration)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_stable_pass' not in flaky_map


def test_stable_fail_not_flaky(project: Project) -> None:
    session = _make_session(project)
    for iteration in range(10):
        _make_record(project, session, 'test_stable_fail', success=False, index=iteration)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_stable_fail' not in flaky_map


def test_same_commit_inconsistency_is_flaky(project: Project) -> None:
    session = _make_session(project, commit_hash='samecommit')
    for iteration, success in enumerate([True, False, True, False, True]):
        _make_record(
            project, session, 'test_inconsistent', success=success, index=iteration,
        )
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_inconsistent' in flaky_map
    status = flaky_map['test_inconsistent']
    assert status.total_runs == 5
    assert status.failure_ratio == 0.4


def test_high_transition_rate_is_flaky(project: Project) -> None:
    outcomes = [True, False, True, False, True, False, True, False, True, False]
    _make_records(project, 'test_flaky', outcomes)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_flaky' in flaky_map
    status = flaky_map['test_flaky']
    assert status.flake_rate == 1.0
    assert status.failure_ratio == 0.5


def test_insufficient_data_not_flaky(project: Project) -> None:
    session = _make_session(project, commit_hash='commit1')
    _make_record(project, session, 'test_few_runs', success=True, index=0)
    _make_record(project, session, 'test_few_runs', success=False, index=1)
    _make_record(project, session, 'test_few_runs', success=True, index=2)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_few_runs' not in flaky_map


def test_low_transition_rate_not_flaky(project: Project) -> None:
    outcomes = [True, True, True, True, True, True, True, True, False, True]
    _make_records(project, 'test_low_transition', outcomes)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_low_transition' not in flaky_map


def test_boundary_transition_rate(project: Project) -> None:
    _make_records(project, 'test_boundary', [True, False, True, False, True])
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_boundary' in flaky_map


def test_boundary_failure_ratio(project: Project) -> None:
    outcomes = [True, True, True, True, True, True, True, True, True, False]
    _make_records(project, 'test_low_failure', outcomes)
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_low_failure' not in flaky_map


def test_multiple_labels(project: Project) -> None:
    stable_session = _make_session(project, commit_hash='stable_commit')
    for iteration in range(10):
        _make_record(project, stable_session, 'test_stable', success=True, index=iteration)
    flaky_outcomes = [True, False, True, False, True, False, True, False, True, False]
    _make_records(project, 'test_flaky', flaky_outcomes, commit_prefix='flaky_commit')
    flaky_map = detect_flaky_labels(project.pk)
    assert 'test_stable' not in flaky_map
    assert 'test_flaky' in flaky_map
