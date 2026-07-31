# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

FROM python:3.12-slim AS base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS uv-export
RUN pip install uv --no-cache-dir
COPY pyproject.toml uv.lock /app/
RUN uv export --no-dev -o requirements.txt

FROM base AS build
COPY --from=uv-export /app/requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends gettext && \
  python -m venv /app/.venv && \
  /app/.venv/bin/pip install -r /tmp/requirements.txt

FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV DJANGO_DB_CONNECTION_CHECK=0
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gettext && \
  rm -rf /var/lib/apt/lists/*

COPY --from=build /app/.venv /app/.venv
COPY src /app
RUN mkdir /app/db
RUN DATABASE_URL=sqlite:///:memory: python manage.py compilemessages
