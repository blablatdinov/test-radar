# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import logging
from datetime import timedelta

from celery import Task, shared_task
from django.utils import timezone

from records.models import TestRecord, Status
from records.srv.flaky import detect_flaky_labels

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
# TODO #151:30min fix high complexity
def recalculate_flaky_statuses(self: Task) -> dict[str, int]:  # noqa: WPS210, WPS231
    cutoff = timezone.now() - timedelta(hours=24)

    stale_labels = (
        TestRecord.objects.filter(timestamp__gte=cutoff)
        .values_list('label', flat=True)
        .distinct()
    )

    if not stale_labels:
        logger.info('No stale labels found, skipping flaky recalculation')
        return {'updated': 0}

    updated_count = 0
    project_ids = (
        TestRecord.objects.filter(label__in=stale_labels)
        .values_list('project_id', flat=True)
        .distinct()
    )

    for project_id in project_ids:
        # TODO #151:30min fix try body length
        try:  # noqa: WPS229
            flaky_map = detect_flaky_labels(project_id)
            flaky_labels_set = set(flaky_map.keys())

            target_records = TestRecord.objects.filter(
                project_id=project_id,
                label__in=stale_labels,
            )

            # Ставим FLAKY для flaky-тестов
            flaky_count = target_records.filter(
                label__in=flaky_labels_set,
            ).update(status=Status.FLAKY)

            # Возвращаем PASSED/FAILED для тех, кто больше не flaky
            # Восстанавливаем статус на основе success
            non_flaky = target_records.exclude(label__in=flaky_labels_set)
            passed_count = non_flaky.filter(success=True).update(status=None)
            failed_count = non_flaky.filter(success=False).update(status=None)

            updated_count += flaky_count + passed_count + failed_count
            logger.info(
                'Project %s: %d flaky, %d passed, %d failed',
                project_id, flaky_count, passed_count, failed_count,
            )
        except Exception as exc:
            logger.exception('Failed to recalculate status for project %s', project_id)
            self.retry(exc=exc, countdown=60)

    logger.info('Status recalculation complete: %d records updated', updated_count)
    return {'updated': updated_count}
