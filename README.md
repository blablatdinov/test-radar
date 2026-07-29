<!--
SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
SPDX-License-Identifier: MIT
-->

# Test Radar

A Django web application for monitoring and storing test results. It allows creating projects, attaching CI/local agents, submitting test results via REST API, and viewing them in a web interface.

## Features

- **Projects** — each user can create their own projects and see only their own.
- **Agents** — CI or local agents with API tokens for automatic test result submission.
- **Test records** — store the result (success/failure), logs (zlib-compressed), git branch and commit.
- **REST API** — `POST /api/v1/test_record/bulk_create/` endpoint for submitting results from agents.
- **Web interface** — project pages, detailed test info, creation forms. Tailwind CSS v4, green theme.
- **i18n** — Russian and English languages.
- **Authentication** — custom user model, `AuthRequiredMiddleware` protects all URLs except `/login/`, `/logout/`, `/register/`, `/admin/`.

## Tech Stack

- Python 3.12+, Django 6.0
- Django REST Framework
- SQLite
- Tailwind CSS v4 (CDN)
- pytest + pytest-django
- Ruff, flake8 (wemake-python-styleguide), mypy (django-stubs)

## Installation

```bash
uv sync
```

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
REGISTRATION_ENABLED=True
```

Apply migrations:

```bash
uv run python src/manage.py migrate
```

Create a superuser (optional):

```bash
uv run python src/manage.py createsuperuser
```

## Running

```bash
uv run python src/manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

## Development Commands

| Action | Command |
|---|---|
| Tests | `uv run pytest` |
| Lint | `uv run ruff check src && uv run flake8 src/` |
| Type check | `uv run mypy src/` |
| Format | `uv run ruff format src/` |
| Extract messages | `uv run django-admin makemessages -l ru -l en --no-location --no-wrap` (from `src/`) |
| Compile translations | `uv run django-admin compilemessages -l ru -l en` (from `src/`) |

## Project Structure

```
src/
├── server/          — Django settings, middleware, URL configuration
├── auth/            — custom User model, login/register forms
├── records/         — Project, Agent, ApiToken, TestRecord models; services
├── gui/             — web interface (views + templates)
├── api/             — REST API (serializers, views)
├── locale/          — translation files (ru, en)
└── tests/it/        — integration tests
```

## API

### Create test records

```
POST /api/v1/test_record/bulk_create/
```

Fields: `label`, `success`, `timestamp`, `logs`, `branch`, `commit`, `session_id`.

## License

MIT
