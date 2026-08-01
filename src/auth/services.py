# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import uuid
from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from auth.models import EmailConfirmationToken, User

if TYPE_CHECKING:
    from django.http import HttpRequest

_TOKEN_EXPIRY_HOURS = 24


def create_confirmation_token(user: User) -> EmailConfirmationToken:
    return EmailConfirmationToken.objects.create(
        user=user,
        token=uuid.uuid4(),
        expired_at=timezone.now() + timedelta(hours=_TOKEN_EXPIRY_HOURS),
    )


def send_confirmation_email(request: HttpRequest, token: EmailConfirmationToken) -> None:
    confirmation_url = request.build_absolute_uri(
        reverse('email_confirm', args=[token.token]),
    )
    subject = str(_('Confirm your email address'))
    text_body = render_to_string(
        'emails/email_confirmation.txt',
        {'confirmation_url': confirmation_url, 'user': token.user},
    )
    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[token.user.email],
    )
