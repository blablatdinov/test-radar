import uuid
from typing import final

from django.db import migrations, models


def populate_guids(apps, schema_editor):
    Project = apps.get_model('records', 'Project')
    Agent = apps.get_model('records', 'Agent')
    for project in Project.objects.filter(guid__isnull=True):
        project.guid = uuid.uuid4()
        project.save(update_fields=['guid'])
    for agent in Agent.objects.filter(guid__isnull=True):
        agent.guid = uuid.uuid4()
        agent.save(update_fields=['guid'])


@final
class Migration(migrations.Migration):
    dependencies = [
        ('records', '0008_alter_testrecord_logs'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='guid',
            field=models.UUIDField(editable=False, null=True, verbose_name='Identifier'),
        ),
        migrations.AddField(
            model_name='agent',
            name='guid',
            field=models.UUIDField(editable=False, null=True, verbose_name='Identifier'),
        ),
        migrations.RunPython(populate_guids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='project',
            name='guid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Identifier'),
        ),
        migrations.AlterField(
            model_name='agent',
            name='guid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Identifier'),
        ),
    ]
