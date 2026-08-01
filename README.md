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

## Agent Authentication Flow

Agents authenticate via token-based auth, separate from the web UI session auth.

### 1. Agent & Token Creation

A `CI` or `local` agent is created (via admin or web form) and linked to a `Project` and an owner (`User`). A raw API token is generated via `records.srv.token.create_token_for_agent()`:

- Prefix `ci_` or `dev_` + `secrets.token_urlsafe(32)`
- Stored as a bcrypt hash (`token_hash`) plus a masked preview (`token_mask`, first 6 and last 3 characters) in the `ApiToken` model
- The raw token is returned once and never persisted in plaintext

### 2. Request

The agent sends requests with an `Authorization` header:

```
Authorization: Token ci_<raw_token>
```

### 3. Middleware

`AuthRequiredMiddleware` allows all `/api/` paths to pass through unchecked — DRF handles authentication and 401 responses.

### 4. DRF Authentication

`DEFAULT_AUTHENTICATION_CLASSES` (in order):

1. **`AgentTokenAuthentication`** — reads the `Token` header, calls `verify_token()` which:
   - Extracts the prefix (`ci_` / `dev_`), filters `ApiToken` candidates by `token_mask__startswith`
   - Skips expired tokens (`expires_at`)
   - Checks the raw token against each candidate's bcrypt hash
   - On success: updates `last_used_at` / `last_used_ip`, returns `(agent.owner, api_token)` — so `request.user` = agent owner, `request.auth` = `ApiToken`
   - On invalid token: raises `AuthenticationFailed` → DRF returns `401 {"detail": "Invalid agent token."}`
   - On missing header: returns `None` (falls through to next class)
2. **`SessionAuthentication`** — for browser sessions
3. **`BasicAuthentication`** — HTTP Basic auth

### 5. Permission Check

`DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` — if no class authenticated the request, DRF returns `401`.

### Flow Diagram

```
Agent (ci/local) ─┐
                  ├─ ApiToken (bcrypt hash, token_mask)
                  │
create_token_for_agent() ──▶ raw token (ci_xxx / dev_xxx)
                                    │
                  Authorization: Token ci_xxx
                                    │
                  AuthRequiredMiddleware ──▶ /api/ ──▶ pass through
                                    │
                  DRF AgentTokenAuthentication
                      verify_token() ──▶ (owner, ApiToken)
                                    │
                  DRF IsAuthenticated ──▶ request.user = owner
                                          request.auth = ApiToken
                                    │
                  View (e.g. BulkCreateTestRecordView)
```

## License

MIT
