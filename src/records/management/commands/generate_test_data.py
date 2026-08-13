# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

# flake8: noqa: WPS

import argparse
import datetime
import secrets
import uuid
from compression import zstd
from dataclasses import dataclass, field
from typing import Any, final

from django.core.management.base import BaseCommand
from model_bakery import baker

from auth.models import User
from records.models import Agent, Project, TestRecord, TestSession
from records.srv.token import create_token_for_agent

_PROJECT_NAMES = (
    'Web Frontend',
    'API Gateway',
    'Auth Service',
    'Payment Core',
    'Mobile App',
    'Notification Service',
    'Search Engine',
    'Data Pipeline',
    'Analytics Dashboard',
    'ML Inference',
)

_AGENT_NAMES = (
    'github-actions',
    'gitlab-ci',
    'jenkins',
    'local-dev',
    'teamcity',
    'circle-ci',
)

_TEST_LABELS = (
    'test_auth.py::test_login',
    'test_auth.py::test_logout',
    'test_auth.py::test_register',
    'test_api.py::test_create_resource',
    'test_api.py::test_list_resources',
    'test_api.py::test_delete_resource',
    'test_api.py::test_update_resource',
    'test_models.py::test_project_str',
    'test_models.py::test_agent_str',
    'test_models.py::test_token_creation',
    'test_views.py::test_index_page',
    'test_views.py::test_project_detail',
    'test_views.py::test_agent_create',
    'test_integration.py::test_full_flow',
    'test_integration.py::test_api_token_flow',
    'test_utils.py::test_compression',
    'test_utils.py::test_token_mask',
    'test_utils.py::test_hex_token',
    'test_services.py::test_filtered_records',
    'test_services.py::test_record_by_id',
)

_MAIN_BRANCHES = ('main', 'develop')
_FEATURE_BRANCHES = (
    'feature/auth-improvements',
    'feature/api-v2',
    'fix/payment-bug',
    'fix/token-leak',
    'refactor/models-cleanup',
    'chore/dependencies-update',
)

_HEX_CHARS = '0123456789abcdef'

_FAIL_LOGS = (
    '============================= test session starts =============================\n'
    'platform linux -- Python 3.12.0\n'
    'rootdir: /home/runner/work/project\n'
    'collected 20 items\n'
    '\n'
    'tests/test_file.py F                                                   [100%]\n'
    '\n'
    '=================================== FAILURES ===================================\n'
    '________________________________ test_function ________________________________\n'
    '    def test_function():\n'
    '>       assert result == expected\n'
    'E       assert 42 == 43\n'
    '\n'
    'tests/test_file.py:15: AssertionError\n'
    '=========================== short test summary info ============================\n'
    'FAILED tests/test_file.py::test_function - assert 42 == 43\n'
    '============================== 1 failed in 12.30s =============================='
)

_SUCCESS_LOGS = (
    '============================= test session starts =============================\n'
    'platform linux -- Python 3.12.0\n'
    'rootdir: /home/runner/work/project\n'
    'collected 20 items\n'
    '\n'
    'tests/test_file.py .                                                   [100%]\n'
    '\n'
    '============================== 1 passed in 8.12s ==============================='
)

_DAYS_BACK = 30
_COMMIT_LENGTH = 40
_HOURS_PER_DAY = 23
_FEATURE_BRANCH_PROBABILITY_PERCENT = 20
_FLAKY_PASS_PROBABILITY_PERCENT = 50
_TEST_ABSENT_PROBABILITY_PERCENT = 10
_STABLE_FAIL_COUNT = 3
_FLAKY_COUNT = 3
_DEFAULT_PROJECTS = 5
_DEFAULT_AGENTS_PER_PROJECT = 3
_DEFAULT_RUNS_PER_PROJECT = 30


def _compress_logs(text: str) -> bytes:
    return zstd.compress(text.encode())


def _random_commit() -> str:
    return ''.join(secrets.choice(_HEX_CHARS) for _ in range(_COMMIT_LENGTH))


def _randint(low: int, high: int) -> int:
    return low + secrets.randbelow(high - low + 1)


def _build_names(base: tuple[str, ...], count: int, fallback_prefix: str) -> list[str]:
    names = list(base[:count])
    if count > len(base):
        start = len(base)
        names.extend(f'{fallback_prefix} #{idx}' for idx in range(start, count))
    return names


def _pick_branch() -> str:
    if secrets.randbelow(100) < _FEATURE_BRANCH_PROBABILITY_PERCENT:
        return secrets.choice(_FEATURE_BRANCHES)
    return secrets.choice(_MAIN_BRANCHES)


def _pop_random(items: list[str], count: int) -> list[str]:
    return [items.pop(secrets.randbelow(len(items))) for _ in range(count)]


@final
@dataclass
class _TestSuite:
    stable_pass: list[str] = field(default_factory=list)
    stable_fail: list[str] = field(default_factory=list)
    flaky: list[str] = field(default_factory=list)

    @classmethod
    def from_labels(cls) -> _TestSuite:
        labels = list(_TEST_LABELS)
        stable_fail = _pop_random(labels, _STABLE_FAIL_COUNT)
        flaky = _pop_random(labels, _FLAKY_COUNT)
        return cls(stable_pass=labels, stable_fail=stable_fail, flaky=flaky)

    def run_labels(self) -> list[str]:
        all_labels = self.stable_pass + self.stable_fail + self.flaky
        return [label for label in all_labels if secrets.randbelow(100) >= _TEST_ABSENT_PROBABILITY_PERCENT]

    def is_success(self, label: str) -> bool:
        if label in self.stable_pass:
            return True
        if label in self.stable_fail:
            return False
        return secrets.randbelow(100) < _FLAKY_PASS_PROBABILITY_PERCENT


@final
@dataclass
class _GenStats:
    projects: int = 0
    agents: int = 0
    records: int = 0

    @property
    def total(self) -> int:
        return self.projects + self.agents + self.records


@final
@dataclass
class _RunContext:
    timestamp: datetime.datetime
    branch: str
    commit: str
    agent: Agent | None
    os: str
    os_version: str
    arch: str


_OS_CHOICES = ('linux', 'windows', 'macos')
_ARCH_CHOICES = ('x64', 'arm64')


def _make_run_context(agents: list[Agent], now: datetime.datetime) -> _RunContext:
    delta = datetime.timedelta(
        days=_randint(0, _DAYS_BACK),
        hours=_randint(0, _HOURS_PER_DAY),
    )
    return _RunContext(
        timestamp=now - delta,
        branch=_pick_branch(),
        commit=_random_commit(),
        agent=secrets.choice(agents) if agents else None,
        os=secrets.choice(_OS_CHOICES),
        os_version='10.0.19045',
        arch=secrets.choice(_ARCH_CHOICES),
    )


def _make_single_run(
    project: Project,
    agents: list[Agent],
    suite: _TestSuite,
    now: datetime.datetime,
) -> int:
    ctx = _make_run_context(agents, now)
    records = 0
    session = baker.make(
        TestSession,
        id=uuid.uuid4(),
        project=project,
        started_at=datetime.datetime.now(tz=datetime.UTC),
        os=ctx.os,
        os_version=ctx.os_version,
        arch=ctx.arch,
        branch=ctx.branch,
        commit_hash=ctx.commit,
    )
    for label in suite.run_labels():
        success = suite.is_success(label)
        logs = _SUCCESS_LOGS if success else _FAIL_LOGS
        baker.make(
            TestRecord,
            project=project,
            label=label,
            success=success,
            timestamp=ctx.timestamp,
            logs=_compress_logs(logs),
            agent=ctx.agent,
            session=session,
        )
        records += 1
    return records


def _create_test_runs(
    project: Project,
    agents: list[Agent],
    run_count: int,
    suite: _TestSuite,
) -> int:
    now = datetime.datetime.now(tz=datetime.UTC)
    return sum(_make_single_run(project, agents, suite, now) for _ in range(run_count))


@final
class Command(BaseCommand):
    help = 'Generate test data for local debugging'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--projects', type=int, default=_DEFAULT_PROJECTS, help='Number of projects to create')
        parser.add_argument(
            '--agents',
            type=int,
            default=_DEFAULT_AGENTS_PER_PROJECT,
            help='Number of agents per project',
        )
        parser.add_argument(
            '--runs',
            type=int,
            default=_DEFAULT_RUNS_PER_PROJECT,
            help='Number of test runs per project',
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        username = input('Input an username for the data agent: ')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write('User with the provided username does not exist')
            return
        stats = self._generate(
            user,
            options['projects'],
            options['agents'],
            options['runs'],
        )
        self._print_stats(stats)

    def _generate(
        self,
        user: User,
        project_count: int,
        agents_per_project: int,
        runs_per_project: int,
    ) -> _GenStats:
        stats = _GenStats()
        for name in _build_names(_PROJECT_NAMES, project_count, 'Project'):
            project = baker.make(Project, name=name, owner=user)
            stats.projects += 1
            agents = self._create_agents(project, user, agents_per_project)
            stats.agents += len(agents)
            suite = _TestSuite.from_labels()
            stats.records += _create_test_runs(project, agents, runs_per_project, suite)
        return stats

    def _create_agents(self, project: Project, user: User, count: int) -> list[Agent]:
        agents: list[Agent] = []
        for agent_name in _build_names(_AGENT_NAMES, count, 'agent'):
            agent_type = secrets.choice([Agent.AgentType.CI, Agent.AgentType.LOCAL])
            agent = baker.make(
                Agent,
                name=agent_name,
                type=agent_type,
                project=project,
                owner=user,
            )
            agents.append(agent)
            create_token_for_agent(agent)
        return agents

    def _print_stats(self, stats: _GenStats) -> None:
        total = stats.total + stats.agents
        lines = (
            'Test data generated:',
            f'  Projects: {stats.projects}',
            f'  Agents:   {stats.agents}',
            f'  Tokens:   {stats.agents}',
            f'  Records:  {stats.records}',
            f'  Total:    {total} objects',
        )
        self.stdout.write(self.style.SUCCESS('\n'.join(lines)))
