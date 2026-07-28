#!/bin/sh
# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

set -e

python src/manage.py migrate --no-input
python src/manage.py compilemessages
python src/manage.py collectstatic --no-input

exec gunicorn server.wsgi:application \
    --chdir src \
    -w "$(nproc)" \
    -b 0.0.0.0:8000
