# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import final

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

_TOKEN_EXPIRY_HOURS = 24


@final
class UserManager(BaseUserManager['User']):
    def create_user(self, username: str, email: str, password: str) -> User:
        user = self.model(username=username, email=email, is_superuser=False)
        user.password = make_password(password)
        user.save()
        return user

    def create_superuser(self, username: str, password: str, email: str = '') -> User:
        user = self.model(username=username, email=email, is_staff=True, is_superuser=True)
        user.password = make_password(password)
        user.is_email_verified = True
        user.save()
        return user


@final
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _('Username'),
        max_length=150,
        unique=True,
    )
    email = models.EmailField(
        _('Email'),
        unique=True,
    )
    is_staff = models.BooleanField(
        _('Is staff'),
        default=False,
    )
    is_email_verified = models.BooleanField(
        _('Email verified'),
        default=False,
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


@final
class EmailConfirmationToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_confirmation_tokens',
        verbose_name=_('User'),
    )
    token = models.UUIDField(
        _('Token'),
        unique=True,
        db_index=True,
    )
    created_at = models.DateTimeField(
        _('Created at'),
        auto_now_add=True,
    )
    expired_at = models.DateTimeField(
        _('Expired at'),
    )

    class Meta:
        verbose_name = _('Email confirmation token')
        verbose_name_plural = _('Email confirmation tokens')

    def __str__(self) -> str:
        return f'EmailConfirmationToken(user={self.user_id}, token={self.token})'

    def is_expired(self) -> bool:
        return timezone.now() >= self.expired_at
