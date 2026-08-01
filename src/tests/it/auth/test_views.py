# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any

import pytest
from django.urls import reverse

from auth.models import User

if TYPE_CHECKING:
    from django.test import Client

pytestmark = [
    pytest.mark.django_db,
]


def test_login_page(client: Client) -> None:
    response = client.get('/login/')

    assert response.status_code == 200
    assert 'Login' in response.text


def test_register_page(client: Client) -> None:
    response = client.get('/register/')

    assert response.status_code == 200
    assert 'Sign up' in response.text


def test_register(client: Client) -> None:
    response = client.post(
        '/register/',
        {
            'username': 'newuser',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')
    assert User.objects.filter(username='newuser').exists()


def test_login_page_registration_disabled(client: Client, settings: Any) -> None:
    settings.REGISTRATION_ENABLED = False

    response = client.get('/login/')

    assert response.status_code == 200
    assert 'Sign up' not in response.text
    assert 'Register' not in response.text


def test_login(client: Client, user: User) -> None:
    response = client.post(
        '/login/',
        {
            'username': user.username,
            'password': 'test-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')


def test_logout(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post('/logout/')

    assert response.status_code == 302
    assert response['Location'] == reverse('login')
