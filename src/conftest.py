# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import contextlib
from collections.abc import Iterator

import pytest
from axes.models import AccessAttempt
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings

settings.REGISTRATION_ENABLED = True


@pytest.fixture(autouse=True)
def _use_simple_staticfiles() -> Iterator[None]:
    with override_settings(
        STORAGES={
            'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        },
    ):
        yield


@pytest.fixture(autouse=True)
def _clear_rate_limit_state() -> Iterator[None]:
    cache.clear()
    with contextlib.suppress(RuntimeError):
        AccessAttempt.objects.all().delete()
    yield
    cache.clear()
