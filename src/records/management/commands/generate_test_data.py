# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import argparse
import base64
import datetime
import secrets
import zlib
from dataclasses import dataclass
from typing import Any

from django.core.management.base import BaseCommand
from model_bakery import baker

from auth.models import User
from records.models import Agent, Project, TestRecord
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

_BRANCHES = (
    'main',
    'develop',
    'feature/auth-improvements',
    'feature/api-v2',
    'fix/payment-bug',
    'fix/token-leak',
    'refactor/models-cleanup',
    'chore/dependencies-update',
)

_HEX_CHARS = '0123456789abcdef'

_FAIL_LOGS = '\n'.join((
    '============================= test session starts =============================',
    'platform linux -- Python 3.12.0',
    'rootdir: /home/runner/work/project',
    'collected 20 items',
    '',
    'tests/test_file.py F                                                   [100%]',
    '',
    '=================================== FAILURES ===================================',
    '________________________________ test_function ________________________________',
    '    def test_function():',
    '>       assert result == expected',
    'E       assert 42 == 43',
    '',
    'tests/test_file.py:15: AssertionError',
    '=========================== short test summary info ============================',
    'FAILED tests/test_file.py::test_function - assert 42 == 43',
    '============================== 1 failed in 12.30s ==============================',
))

_SUCCESS_LOGS = '\n'.join((
    '============================= test session starts =============================',
    'platform linux -- Python 3.12.0',
    'rootdir: /home/runner/work/project',
    'collected 20 items',
    '',
    'tests/test_file.py .                                                   [100%]',
    '',
    '============================== 1 passed in 8.12s ===============================',
))

_DAYS_BACK = 30
_COMMIT_LENGTH = 40
_HOURS_PER_DAY = 23
_SUCCESS_RATE_PERCENT = 80
_DEFAULT_PROJECTS = 5
_DEFAULT_AGENTS_PER_PROJECT = 3
_DEFAULT_RECORDS_PER_PROJECT = 75
_USERNAME = 'hp'


def _compress_logs(text: str) -> str:
    return base64.b64encode(zlib.compress(text.encode())).decode()


def _random_commit() -> str:
    return ''.join(secrets.choice(_HEX_CHARS) for _ in range(_COMMIT_LENGTH))


def _randint(low: int, high: int) -> int:
    return low + secrets.randbelow(high - low + 1)


def _build_names(base: tuple[str, ...], count: int, fallback_prefix: str) -> list[str]:
    names = list(base[:count])
    if count > len(base):
        names.extend(f'{fallback_prefix} #{idx}' for idx in range(len(base), count))
    return names


@dataclass
class _GenStats:
    projects: int = 0
    agents: int = 0
    tokens: int = 0
    records: int = 0

    @property
    def total(self) -> int:
        return self.projects + self.agents + self.tokens + self.records


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
            '--records',
            type=int,
            default=_DEFAULT_RECORDS_PER_PROJECT,
            help='Number of test records per project',
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        user = User.objects.get(username=_USERNAME)
        stats = self._generate(
            user,
            options['projects'],
            options['agents'],
            options['records'],
        )
        self._print_stats(stats)

    def _generate(
        self,
        user: User,
        project_count: int,
        agents_per_project: int,
        records_per_project: int,
    ) -> _GenStats:
        stats = _GenStats()
        for name in _build_names(_PROJECT_NAMES, project_count, 'Project'):
            project = baker.make(Project, name=name, owner=user)
            stats.projects += 1
            agents = self._create_agents(project, user, agents_per_project)
            stats.agents += len(agents)
            stats.records += self._create_records(project, agents, records_per_project)
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

    @staticmethod
    def _create_records(project: Project, agents: list[Agent], count: int) -> int:
        for _ in range(count):
            success = secrets.randbelow(100) < _SUCCESS_RATE_PERCENT
            timestamp = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(
                days=_randint(0, _DAYS_BACK),
                hours=_randint(0, _HOURS_PER_DAY),
            )
            logs = _SUCCESS_LOGS if success else _FAIL_LOGS
            baker.make(
                TestRecord,
                project=project,
                label=secrets.choice(_TEST_LABELS),
                success=success,
                timestamp=timestamp,
                logs=_compress_logs(logs),
                branch=secrets.choice(_BRANCHES),
                commit=_random_commit(),
                agent=secrets.choice(agents) if agents else None,
            )
        return count

    def _print_stats(self, stats: _GenStats) -> None:
        lines = (
            'Test data generated:',
            f'  Projects: {stats.projects}',
            f'  Agents:   {stats.agents}',
            f'  Tokens:   {stats.tokens + stats.agents}',
            f'  Records:  {stats.records}',
            f'  Total:    {stats.total + stats.agents} objects',
        )
        self.stdout.write(self.style.SUCCESS('\n'.join(lines)))
