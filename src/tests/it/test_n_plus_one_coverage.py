# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT


from typing import TYPE_CHECKING

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

if TYPE_CHECKING:
    from collections.abc import Iterable

_EXCLUDED_NAMESPACES: frozenset[str] = frozenset(('admin', 'djdt'))


def _resolver_names(pattern: URLResolver, namespace: str) -> set[str]:
    ns = pattern.namespace or namespace
    if ns in _EXCLUDED_NAMESPACES:
        return set()
    return _extract_names(pattern.url_patterns, ns)


def _pattern_name(pattern: URLPattern) -> set[str]:
    if pattern.name:
        return {pattern.name}
    return set()


def _extract_names(
    patterns: Iterable[URLPattern | URLResolver],
    namespace: str = '',
) -> set[str]:
    names: set[str] = set()
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            names |= _resolver_names(pattern, namespace)
        elif isinstance(pattern, URLPattern):
            names |= _pattern_name(pattern)
    return names


def _collect_url_names() -> set[str]:
    resolver = get_resolver()
    return _extract_names(resolver.url_patterns)


def test_all_urls_have_n_plus_one_coverage(covered_url_names: set[str]) -> None:
    all_names = _collect_url_names()
    temporary_excluded = {
        # TODO #85:30min cover "agent_create" url with django_assert_max_num_queries
        'agent_create',
        # TODO #85:30min cover "api_bulk_create_test" url with django_assert_max_num_queries
        'api_bulk_create_test',
        # TODO #85:30min cover "login" url with django_assert_max_num_queries
        'login',
        # TODO #85:30min cover "register" url with django_assert_max_num_queries
        'register',
        # TODO #85:30min cover "logout" url with django_assert_max_num_queries
        'logout',
        # TODO #85:30min cover "agent_token_regenerate" url with django_assert_max_num_queries
        'agent_token_regenerate',
    }
    uncovered = all_names - temporary_excluded - covered_url_names
    assert not uncovered, f'URLs without N+1 coverage: {sorted(uncovered)}'
