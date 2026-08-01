# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from collections.abc import Iterable

import pytest

pytest_plugins = [
    'tests.fixtures',
]

_covered_url_names: set[str] = set()


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: Iterable[pytest.Item],
) -> None:  # noqa: ARG001
    for item in items:
        marker = item.get_closest_marker('n_plus_one')
        if marker and marker.args:
            _covered_url_names.add(marker.args[0])


@pytest.fixture
def covered_url_names() -> set[str]:
    return _covered_url_names.copy()
