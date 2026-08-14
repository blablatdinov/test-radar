# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

# @todo #162:30min After RBAC migration, extend N+1 coverage for membership
#  joins: prefetch/select_related memberships where views resolve roles and
#  assert query counts do not grow with member count.


from typing import TYPE_CHECKING

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

if TYPE_CHECKING:
    from collections.abc import Iterable

_EXCLUDED_NAMESPACES: frozenset[str] = frozenset(('admin', 'djdt'))

_EXCLUDED_URL_NAMES: frozenset[str] = frozenset((
    'login',
    'logout',
    'register',
    'email_confirmation_sent',
    'email_confirm',
    'email_resend',
))


def _resolver_names(pattern: URLResolver, namespace: str) -> set[str]:
    ns = pattern.namespace or namespace
    if ns in _EXCLUDED_NAMESPACES:
        return set()
    return _extract_names(pattern.url_patterns, ns)


def _pattern_name(pattern: URLPattern) -> set[str]:
    if pattern.name and pattern.name not in _EXCLUDED_URL_NAMES:
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
    uncovered = all_names - covered_url_names
    assert not uncovered, f'URLs without N+1 coverage: {sorted(uncovered)}'
