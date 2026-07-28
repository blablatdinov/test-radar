# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import pytest
from django.test import Client
from django.urls import reverse

from auth.models import User


@pytest.mark.django_db
def test_index(client: Client, user: User, test_record_pk: str) -> None:
    client.force_login(user)

    response = client.get(reverse('index_page'))

    assert 'test_file.py::test_view' in response.text
    assert response.status_code == 200
    assert response.context_data
    assert response.context_data.get('records') is not None


@pytest.mark.django_db
def test_test_info(client: Client, user: User, test_record_pk: str) -> None:
    client.force_login(user)

    response = client.get(reverse('test_info', kwargs={'pk': test_record_pk}))

    assert '✅' in response.text
    assert response.status_code == 200
    assert response.context_data
    assert response.context_data['record'].pk == test_record_pk


@pytest.mark.django_db
def test_index_redirects_anonymous(client: Client) -> None:
    response = client.get(reverse('index_page'))

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')


@pytest.mark.django_db
def test_test_info_redirects_anonymous(client: Client, test_record_pk: str) -> None:
    response = client.get(reverse('test_info', kwargs={'pk': test_record_pk}))

    assert response.status_code == 302
    assert response.headers['Location'] == reverse('login')
