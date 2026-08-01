# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(default='', max_length=254, verbose_name='Email'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False, verbose_name='Email verified'),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='Email'),
        ),
        migrations.CreateModel(
            name='EmailConfirmationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(db_index=True, unique=True, verbose_name='Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('expired_at', models.DateTimeField(verbose_name='Expired at')),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='email_confirmation_tokens', to='authentication.user', verbose_name='User')),
            ],
            options={
                'verbose_name': 'Email confirmation token',
                'verbose_name_plural': 'Email confirmation tokens',
            },
        ),
    ]
