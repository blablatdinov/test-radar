# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.db import migrations, models


def populate_session_env_context(apps, schema_editor):
    TestSession = apps.get_model('records', 'TestSession')
    TestSession.objects.update(
        os='-',
        os_version='-',
        arch='-',
        branch='-',
        commit_hash='-',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0009_add_guid_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsession',
            name='os',
            field=models.CharField(max_length=50, verbose_name='OS', default='-'),
        ),
        migrations.AddField(
            model_name='testsession',
            name='os_version',
            field=models.CharField(max_length=100, verbose_name='OS version', default='-'),
        ),
        migrations.AddField(
            model_name='testsession',
            name='arch',
            field=models.CharField(max_length=20, verbose_name='Architecture', default='-'),
        ),
        migrations.AddField(
            model_name='testsession',
            name='branch',
            field=models.CharField(max_length=512, verbose_name='Git branch', default='-'),
        ),
        migrations.AddField(
            model_name='testsession',
            name='commit_hash',
            field=models.CharField(max_length=40, verbose_name='Git commit hash', default='-'),
        ),
        migrations.RunPython(populate_session_env_context, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='testsession',
            name='os',
            field=models.CharField(max_length=50, verbose_name='OS'),
        ),
        migrations.AlterField(
            model_name='testsession',
            name='os_version',
            field=models.CharField(max_length=100, verbose_name='OS version'),
        ),
        migrations.AlterField(
            model_name='testsession',
            name='arch',
            field=models.CharField(max_length=20, verbose_name='Architecture'),
        ),
        migrations.AlterField(
            model_name='testsession',
            name='branch',
            field=models.CharField(max_length=512, verbose_name='Git branch'),
        ),
        migrations.AlterField(
            model_name='testsession',
            name='commit_hash',
            field=models.CharField(max_length=40, verbose_name='Git commit hash'),
        ),
        migrations.RemoveField(
            model_name='testrecord',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='testrecord',
            name='commit',
        ),
    ]
