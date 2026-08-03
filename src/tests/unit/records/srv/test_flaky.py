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


def test_stable_pass_not_flaky(project: Project) -> None:
    session = _make_session(project)
    for iteration in range(10):
        _make_record(project, session, 'test_stable_pass', success=True, index=iteration)
    result = detect_flaky_labels(project.pk)
    assert 'test_stable_pass' not in result


def test_stable_fail_not_flaky(project: Project) -> None:
    session = _make_session(project)
    for iteration in range(10):
        _make_record(project, session, 'test_stable_fail', success=False, index=iteration)
    result = detect_flaky_labels(project.pk)
    assert 'test_stable_fail' not in result


def test_same_commit_inconsistency_is_flaky(project: Project) -> None:
    session = _make_session(project, commit_hash='samecommit')
    outcomes = [True, False, True, False, True]
    for iteration, success in enumerate(outcomes):
        _make_record(
            project, session, 'test_inconsistent', success=success, index=iteration,
        )
    result = detect_flaky_labels(project.pk)
    assert 'test_inconsistent' in result
    status = result['test_inconsistent']
    assert status.total_runs == 5
    assert status.failure_ratio == 0.4


def test_high_transition_rate_is_flaky(project: Project) -> None:
    outcomes = [True, False, True, False, True, False, True, False, True, False]
    for iteration, success in enumerate(outcomes):
        session = _make_session(
            project, commit_hash=f'commit{iteration}', index=iteration,
        )
        _make_record(project, session, 'test_flaky', success=success, index=iteration)
    result = detect_flaky_labels(project.pk)
    assert 'test_flaky' in result
    status = result['test_flaky']
    assert status.flake_rate == 1.0
    assert status.failure_ratio == 0.5


def test_insufficient_data_not_flaky(project: Project) -> None:
    session = _make_session(project, commit_hash='commit1')
    _make_record(project, session, 'test_few_runs', success=True, index=0)
    _make_record(project, session, 'test_few_runs', success=False, index=1)
    _make_record(project, session, 'test_few_runs', success=True, index=2)
    result = detect_flaky_labels(project.pk)
    assert 'test_few_runs' not in result


def test_low_transition_rate_not_flaky(project: Project) -> None:
    outcomes = [True] * 8 + [False, True]
    for iteration, success in enumerate(outcomes):
        session = _make_session(
            project, commit_hash=f'commit{iteration}', index=iteration,
        )
        _make_record(
            project, session, 'test_low_transition', success=success, index=iteration,
        )
    result = detect_flaky_labels(project.pk)
    assert 'test_low_transition' not in result


def test_boundary_transition_rate(project: Project) -> None:
    outcomes = [True, False, True, False, True]
    for iteration, success in enumerate(outcomes):
        session = _make_session(
            project, commit_hash=f'commit{iteration}', index=iteration,
        )
        _make_record(project, session, 'test_boundary', success=success, index=iteration)
    result = detect_flaky_labels(project.pk)
    assert 'test_boundary' in result


def test_boundary_failure_ratio(project: Project) -> None:
    outcomes = [True] * 9 + [False]
    for iteration, success in enumerate(outcomes):
        session = _make_session(
            project, commit_hash=f'commit{iteration}', index=iteration,
        )
        _make_record(
            project, session, 'test_low_failure', success=success, index=iteration,
        )
    result = detect_flaky_labels(project.pk)
    assert 'test_low_failure' not in result


def test_multiple_labels(project: Project) -> None:
    stable_session = _make_session(project, commit_hash='stable_commit')
    for iteration in range(10):
        _make_record(project, stable_session, 'test_stable', success=True, index=iteration)
    flaky_outcomes = [True, False, True, False, True, False, True, False, True, False]
    for iteration, success in enumerate(flaky_outcomes):
        session = _make_session(
            project, commit_hash=f'flaky_commit{iteration}', index=iteration,
        )
        _make_record(project, session, 'test_flaky', success=success, index=iteration)
    result = detect_flaky_labels(project.pk)
    assert 'test_stable' not in result
    assert 'test_flaky' in result
