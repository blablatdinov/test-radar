import datetime
from unittest.mock import Mock

import pytest
from django.http import HttpRequest

from records.srv.record import filtered_records, record_by_id


@pytest.mark.django_db
def test_filtered_records(test_record_pk: str) -> None:
    request = Mock(HttpRequest)
    request.GET = {'date': datetime.datetime.now(tz=datetime.UTC).strftime('%Y-%m-%d')}

    records = filtered_records(request)

    assert len(records['records']) == 1


@pytest.mark.django_db
def test_record_by_id(test_record_pk: str) -> None:
    record = record_by_id(test_record_pk)

    assert record['record'].pk == test_record_pk
