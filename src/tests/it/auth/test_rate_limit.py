# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from auth.models import User

if TYPE_CHECKING:
    from django.test import Client

pytestmark = [
    pytest.mark.django_db,
]


def test_login_lockout_after_failure_limit(client: Client, verified_user: User) -> None:
    for _ in range(5):
        client.post(
            '/login/',
            {'username': verified_user.username, 'password': 'wrong-password-123'},
        )

    response = client.post(
        '/login/',
        {'username': verified_user.username, 'password': 'wrong-password-123'},
    )

    assert response.status_code == 429


def test_login_no_lockout_before_failure_limit(client: Client, verified_user: User) -> None:
    for _ in range(4):
        response = client.post(
            '/login/',
            {'username': verified_user.username, 'password': 'wrong-password-123'},
        )
        assert response.status_code != 403


def test_login_success_resets_counter(client: Client, verified_user: User) -> None:
    for _ in range(4):
        client.post(
            '/login/',
            {'username': verified_user.username, 'password': 'wrong-password-123'},
        )

    response = client.post(
        '/login/',
        {'username': verified_user.username, 'password': 'test-password-123'},
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')

    for _ in range(4):
        response = client.post(
            '/login/',
            {'username': verified_user.username, 'password': 'wrong-password-123'},
        )
        assert response.status_code != 403


def test_login_lockout_is_ip_specific(client: Client, verified_user: User) -> None:
    for _ in range(5):
        client.post(
            '/login/',
            {'username': verified_user.username, 'password': 'wrong-password-123'},
            REMOTE_ADDR='192.168.1.1',
        )

    response = client.post(
        '/login/',
        {'username': verified_user.username, 'password': 'test-password-123'},
        REMOTE_ADDR='192.168.1.2',
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')


def test_register_rate_limit_blocks_after_limit(client: Client) -> None:
    for idx in range(5):
        response = client.post(
            '/register/',
            {
                'username': f'user{idx}',
                'email': f'user{idx}@example.com',
                'password1': 'strong-password-123',
                'password2': 'strong-password-123',
            },
        )
        assert response.status_code == 302

    response = client.post(
        '/register/',
        {
            'username': 'user6',
            'email': 'user6@example.com',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 403
    assert not User.objects.filter(username='user6').exists()
