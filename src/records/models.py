# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import base64
import secrets
import zlib

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.utils.translation import gettext_lazy as _


def _hex_token() -> str:
    return secrets.token_hex(16)


class CompressedTextField(models.TextField):
    def from_db_value(self, value: str, expression: models.TextField, connection: BaseDatabaseWrapper) -> str:  # noqa: ARG002,ANN001
        if not value:
            return value
        decoded = base64.b64decode(value)
        decompressed = zlib.decompress(decoded)
        return decompressed.decode('utf-8')


class Project(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    owner = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_('Owner'),
    )
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    def __str__(self) -> str:
        return str(self.name)


class TestRecord(models.Model):
    id = models.CharField(
        _('Indentifier'),
        primary_key=True,
        max_length=32,
        default=_hex_token,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='records',
        null=True,
        verbose_name=_('Project'),
    )
    label = models.CharField(_('Label'), max_length=128)
    success = models.BooleanField(_('Success'))
    timestamp = models.DateTimeField(_('Timestamp'))
    logs = CompressedTextField(_('Logs'), blank=True)
    branch = models.CharField(_('Git branch'), max_length=512)
    commit = models.CharField(_('Git commit'), max_length=40)

    class Meta:
        verbose_name = _('Test record')
        verbose_name_plural = _('Test records')

    def __str__(self) -> str:
        return str(self.label)
