# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.db import migrations


def populate_memberships(apps, schema_editor):
    Project = apps.get_model('records', 'Project')
    Membership = apps.get_model('records', 'Membership')
    Membership.objects.bulk_create([
        Membership(user_id=project.owner_id, project_id=project.id, role='owner')
        for project in Project.objects.iterator()
    ])


class Migration(migrations.Migration):
    dependencies = [
        ('records', '0015_membership'),
    ]
    operations = [
        migrations.RunPython(populate_memberships, migrations.RunPython.noop),
    ]
