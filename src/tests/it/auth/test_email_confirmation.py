# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from django.core import mail
from django.urls import reverse

from auth.models import EmailConfirmationToken, User

if TYPE_CHECKING:
    from django.test import Client

pytestmark = [
    pytest.mark.django_db,
]


def test_register_creates_unverified_user(client: Client) -> None:
    response = client.post(
        '/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 302
    user = User.objects.get(username='newuser')
    assert user.is_email_verified is False


def test_register_creates_confirmation_token(client: Client) -> None:
    client.post(
        '/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    user = User.objects.get(username='newuser')
    assert EmailConfirmationToken.objects.filter(user=user).exists()


def test_register_does_not_login_user(client: Client) -> None:
    client.post(
        '/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    response = client.get(reverse('index_page'))
    assert response.status_code == 302
    assert response['Location'] == reverse('login')


def test_register_sends_email(client: Client) -> None:
    client.post(
        '/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert len(mail.outbox) == 1
    assert 'newuser@example.com' in mail.outbox[0].to


def test_register_redirects_to_sent_page(client: Client) -> None:
    response = client.post(
        '/register/',
        {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('email_confirmation_sent')


def test_confirm_with_valid_token(client: Client, unverified_user: User) -> None:
    token = EmailConfirmationToken.objects.create(
        user=unverified_user,
        token='12345678-1234-5678-1234-567812345678',
        expired_at='2099-01-01T00:00:00Z',
    )

    response = client.get(reverse('email_confirm', args=[token.token]))

    assert response.status_code == 302
    assert response['Location'] == reverse('login')
    unverified_user.refresh_from_db()
    assert unverified_user.is_email_verified is True
    assert not EmailConfirmationToken.objects.filter(pk=token.pk).exists()


def test_confirm_with_expired_token(client: Client, unverified_user: User) -> None:
    token = EmailConfirmationToken.objects.create(
        user=unverified_user,
        token='12345678-1234-5678-1234-567812345678',
        expired_at='2000-01-01T00:00:00Z',
    )

    response = client.get(reverse('email_confirm', args=[token.token]))

    assert response.status_code == 302
    assert response['Location'] == reverse('email_resend')
    unverified_user.refresh_from_db()
    assert unverified_user.is_email_verified is False
    assert not EmailConfirmationToken.objects.filter(pk=token.pk).exists()


def test_confirm_with_nonexistent_token(client: Client) -> None:
    response = client.get(reverse('email_confirm', args=['00000000-0000-0000-0000-000000000000']))

    assert response.status_code == 302
    assert response['Location'] == reverse('email_resend')


def test_login_blocked_for_unverified(client: Client, unverified_user: User) -> None:
    response = client.post(
        '/login/',
        {
            'username': unverified_user.username,
            'password': 'test-password-123',
        },
    )

    assert response.status_code == 200
    assert 'confirm your email' in response.text.lower()


def test_login_succeeds_for_verified(client: Client, verified_user: User) -> None:
    response = client.post(
        '/login/',
        {
            'username': verified_user.username,
            'password': 'test-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')


def test_resend_for_unverified_user(client: Client, unverified_user: User) -> None:
    response = client.post(
        reverse('email_resend'),
        {'email': unverified_user.email},
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('email_confirmation_sent')
    assert len(mail.outbox) == 1
    assert EmailConfirmationToken.objects.filter(user=unverified_user).exists()


def test_resend_for_nonexistent_email(client: Client) -> None:
    response = client.post(
        reverse('email_resend'),
        {'email': 'nonexistent@example.com'},
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('email_confirmation_sent')
    assert len(mail.outbox) == 0


def test_resend_for_verified_user_no_send(client: Client, verified_user: User) -> None:
    response = client.post(
        reverse('email_resend'),
        {'email': verified_user.email},
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('email_confirmation_sent')
    assert len(mail.outbox) == 0


def test_register_duplicate_email_rejected(client: Client, unverified_user: User) -> None:
    response = client.post(
        '/register/',
        {
            'username': 'another',
            'email': unverified_user.email,
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 200
    assert 'already exists' in response.text.lower()


def test_sent_page_accessible(client: Client) -> None:
    response = client.get(reverse('email_confirmation_sent'))

    assert response.status_code == 200
    assert 'Check your email' in response.text


def test_resend_page_accessible(client: Client) -> None:
    response = client.get(reverse('email_resend'))

    assert response.status_code == 200
    assert 'Resend' in response.text


def test_send_email_uses_send_mail(client: Client) -> None:
    with patch('auth.services.send_mail') as mock_send:  # noqa: WPS118
        client.post(
            '/register/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'strong-password-123',
                'password2': 'strong-password-123',
            },
        )
        assert mock_send.call_count == 1
        call_kwargs = mock_send.call_args
        assert 'newuser@example.com' in call_kwargs.kwargs['recipient_list']
