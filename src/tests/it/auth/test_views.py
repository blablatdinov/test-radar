# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from auth.models import User


@pytest.mark.django_db
def test_login_page(client: Client) -> None:
    response = client.get(reverse('login'))

    assert response.status_code == 200
    assert 'Login' in response.text


@pytest.mark.django_db
def test_register_page(client: Client) -> None:
    response = client.get(reverse('register'))

    assert response.status_code == 200
    assert 'Sign up' in response.text


@pytest.mark.django_db
def test_register(client: Client) -> None:
    response = client.post(
        reverse('register'),
        {
            'username': 'newuser',
            'password1': 'strong-password-123',
            'password2': 'strong-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_login_page_registration_disabled(client: Client, settings: Any) -> None:
    settings.REGISTRATION_ENABLED = False

    response = client.get(reverse('login'))

    assert response.status_code == 200
    assert 'Sign up' not in response.text
    assert 'Register' not in response.text


@pytest.mark.django_db
def test_login(client: Client, user: User) -> None:
    response = client.post(
        reverse('login'),
        {
            'username': user.username,
            'password': 'test-password-123',
        },
    )

    assert response.status_code == 302
    assert response['Location'] == reverse('index_page')


@pytest.mark.django_db
def test_logout(client: Client, user: User) -> None:
    client.force_login(user)

    response = client.post(reverse('logout'))

    assert response.status_code == 302
    assert response['Location'] == reverse('login')
