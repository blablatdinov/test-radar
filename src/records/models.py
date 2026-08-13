# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import final
import secrets
import uuid
from compression import zstd

from django.db import models
from django.utils.translation import gettext_lazy as _


def _hex_token() -> str:
    return secrets.token_hex(16)


@final
class Project(models.Model):
    guid = models.UUIDField(_('Identifier'), default=uuid.uuid4, editable=False, unique=True)
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


@final
class Agent(models.Model):
    class AgentType(models.TextChoices):
        CI = 'ci', _('CI')
        LOCAL = 'local', _('Local')

    name = models.CharField(_('Name'), max_length=128)
    type = models.CharField(_('Agent type'), max_length=10, choices=AgentType.choices)
    guid = models.UUIDField(_('Identifier'), default=uuid.uuid4, editable=False, unique=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='agents',
        verbose_name=_('Project'),
    )
    owner = models.ForeignKey(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='agents',
        verbose_name=_('Owner'),
    )
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('Agent')
        verbose_name_plural = _('Agents')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'project'],
                name='uniq_agent_name_per_project',
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


@final
class ApiToken(models.Model):
    agent = models.OneToOneField(
        Agent,
        on_delete=models.CASCADE,
        related_name='token',
        verbose_name=_('Agent'),
    )
    token_hash = models.CharField(_('Token hash'), max_length=128)
    token_mask = models.CharField(_('Token mask'), max_length=32)
    scopes = models.CharField(_('Scopes'), max_length=255, default='write:results')
    expires_at = models.DateTimeField(_('Expires at'), null=True, blank=True)
    last_used_at = models.DateTimeField(_('Last used at'), null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(_('Last used IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('API token')
        verbose_name_plural = _('API tokens')

    def __str__(self) -> str:
        return f'{self.token_mask} ({self.agent})'


@final
class TestSession(models.Model):
    __test__ = False
    id = models.UUIDField(_('Identifier'), primary_key=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        verbose_name=_('Project'),
    )
    started_at = models.DateTimeField(_('Started at'))
    os = models.CharField(_('OS'), max_length=50)
    os_version = models.CharField(_('OS version'), max_length=100)
    arch = models.CharField(_('Architecture'), max_length=20)
    branch = models.CharField(_('Git branch'), max_length=512)
    commit_hash = models.CharField(_('Git commit hash'), max_length=40)

    class Meta:
        verbose_name = _('Test session')
        verbose_name_plural = _('Test sessions')

    def __str__(self) -> str:
        return str(self.id)


@final
class TestRecord(models.Model):
    __test__ = False
    id = models.CharField(
        _('Identifier'),
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
    label = models.TextField(_('Label'))
    success = models.BooleanField(_('Success'))
    timestamp = models.DateTimeField(_('Timestamp'))
    logs = models.BinaryField(_('Logs'), blank=True)
    agent = models.ForeignKey(
        Agent,
        on_delete=models.SET_NULL,
        related_name='records',
        null=True,
        blank=True,
        verbose_name=_('Agent'),
    )
    session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name='records',
        null=True,
        verbose_name=_('Test session'),
    )

    class Meta:
        verbose_name = _('Test record')
        verbose_name_plural = _('Test records')

    def __str__(self) -> str:
        return str(self.label)

    @property
    def decompressed_logs(self) -> str:
        if not self.logs:
            return ''
        return zstd.decompress(self.logs).decode('utf-8')
