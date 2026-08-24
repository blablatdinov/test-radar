# Onboarding

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker and Docker Compose (for Docker-based setup)
- PostgreSQL 18 (optional, for local non-Docker setup; SQLite works for development)

## Quick start with Docker (recommended)

Docker Compose provides PostgreSQL 18 and the Django dev server with hot-reload.

```bash
# Clone the repository
git clone https://github.com/blablatdinov/test-radar.git
cd test-radar

# Build the dev image and pull PostgreSQL
docker compose build app
docker compose pull db

# Start the stack
docker compose up -d

# Run migrations
docker compose exec app uv run python src/manage.py migrate

# Create a superuser
docker compose exec app uv run python src/manage.py createsuperuser

# Open http://localhost:8000
```

The dev server auto-reloads on file changes because the project directory is mounted as a volume.

### Running tests in Docker

```bash
docker compose run app task tests
```

### Using the shell

```bash
docker compose exec app task shell
```

## Local development (without Docker)

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env as needed. For SQLite, set:
# DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Run migrations and start the dev server

```bash
uv run python src/manage.py migrate
uv run python src/manage.py runserver
```

### 4. Create a superuser

```bash
uv run python src/manage.py createsuperuser
```

Open http://localhost:8000.

## Common commands

| Task | Command |
|------|---------|
| Run tests | `uv run pytest` |
| Run tests (fast, no integration) | `uv run pytest src -m 'not integration' -vv` |
| Coverage report | `uv run pytest src --cov-report=html` |
| Lint | `uv run ruff check src && uv run flake8 src/` |
| Type check | `uv run mypy src/` |
| Format | `uv run ruff format src/` |
| Auto-fix lint issues | `uv run ruff check src --fix --fix-only` |
| Make migrations | `uv run python src/manage.py makemigrations && uv run python src/manage.py migrate` |
| Shell with shell_plus | `uv run python src/manage.py shell_plus` |
| Generate test data | `uv run python src/manage.py generate_test_data` |
| Update translations | `cd src && uv run django-admin makemessages -l ru -l en --no-location --no-wrap` |
| Compile translations | `cd src && uv run django-admin compilemessages -l ru -l en` |

If you have [Task](https://taskfile.dev) installed, most of these are available as `task` commands (see `Taskfile.yml`).

## Project structure

```
src/
├── server/          # Django project (settings, urls, middleware)
├── auth/            # User model, registration, login, email confirmation
├── records/         # Core domain: models, services, forms
│   └── srv/         # Service layer (token, permissions, record)
├── api/             # REST API (bulk test record creation)
├── gui/             # Web UI (views, templates, static)
│   └── views/       # One view per file
├── locale/          # i18n .po files (en, ru)
└── tests/           # Test suite
    ├── fixtures.py  # All pytest fixtures
    ├── it/           # Integration tests
    └── unit/         # Unit tests
```

## Development conventions

See [AGENTS.md](../AGENTS.md) for detailed conventions. Key points:

- Python 3.14+, Django 6.0, line length 120, single quotes
- Ruff `ALL` rules + wemake-python-styleguide (WPS) via flake8
- mypy with django-stubs
- No comments in code unless explicitly requested (0pdd puzzles are the exception)
- All user-facing strings use `gettext_lazy` (`_`)
- Tests in `src/tests/it/`, fixtures in `src/tests/fixtures.py`
- SPDX license headers at the top of every source file
- `@final` decorator on all classes

## Generating test data

To populate a project with sample data for development:

```bash
uv run python src/manage.py generate_test_data
```

This creates a project, agent, test sessions, and test records so you can see the matrix populated.

## Environment variables

See [`.env.example`](../.env.example) for all available variables. Key ones for development:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | `insecure` | Django secret key |
| `DEBUG` | `False` | Debug mode (set to `true` for dev) |
| `DATABASE_URL` | — | Database URL (`postgres://...` or `sqlite:///...`) |
| `REGISTRATION_ENABLED` | `False` | Enable user registration |
| `RBAC_ENABLED` | `False` | Enable RBAC permission system |
| `SILK_ENABLE` | `False` | Enable django-silk profiling |
