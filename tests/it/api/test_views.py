import base64
import datetime
import zlib

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_success_record_create(client: Client) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC)

    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={
            'label': 'test_file.py::test_some',
            'timestamp': timestamp.isoformat(),
            'success': True,
            'logs': '',
        },
    )
    json = response.json()

    assert response.status_code == 201
    assert json['label'] == 'test_file.py::test_some'
    assert json['timestamp'] == timestamp.isoformat().replace('+00:00', 'Z')
    assert json['success']


@pytest.mark.django_db
def test_failed_record_create(client: Client) -> None:
    timestamp = datetime.datetime.now(tz=datetime.UTC)
    logs = '\n'.join(
        [
            '   def test_some() -> None:',
            '>      assert 1 == 0',
            'E      assert 1 == 0',
        ],
    )

    response = client.post(
        reverse('api_create_test'),
        content_type='application/json',
        data={
            'label': 'test_file.py::test_some',
            'timestamp': timestamp.isoformat(),
            'success': False,
            'logs': base64.b64encode(zlib.compress(logs.encode('utf-8'))).decode('utf-8'),
        },
    )
    json = response.json()

    assert response.status_code == 201
    assert json['label'] == 'test_file.py::test_some'
    assert json['timestamp'] == timestamp.isoformat().replace('+00:00', 'Z')
    assert not json['success']
    assert zlib.decompress(base64.b64decode(json['logs'])).decode('utf-8') == logs
