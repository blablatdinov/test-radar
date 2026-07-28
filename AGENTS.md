# AGENTS.md

## Commands

- **Run tests:** `uv run pytest`
- **Lint:** `uv run ruff check src && uv run flake8 src/`
- **Type check:** `uv run mypy src/`
- **Format:** `uv run ruff format src/`

## Conventions

- Python 3.12+, Django 6.0
- Line length: 120
- Quote style: single quotes
- Ruff rules: `ALL` with specific ignores (see `pyproject.toml`)
- External linter: wemake-python-styleguide (WPS rules via flake8)
- mypy with django-stubs plugin, settings module: `server.settings`
- Tests use pytest + pytest-django, located in `src/tests/it/`
- Test files ignore: `ARG001`, `FLY002`, `PLR2004`, `S101`
- Migrations excluded from linting
- No comments in code unless explicitly requested
- SPDX license headers at the top of every source file
- i18n enabled: use `gettext_lazy` (`_`) for all user-facing text
- When adding new user-facing strings: update `.po` files in `src/locale/ru/LC_MESSAGES/django.po` and `src/locale/en/LC_MESSAGES/django.po`, then run `uv run django-admin compilemessages -l ru -l en` (from `src/`)
- Forms: hand-rendered with Tailwind, no form libraries (no crispy-forms, etc.)
- Form views use `FormView` with `form_valid` override; `owner`/user set from `request.user` in view, not in form
- Templates extend `base.html`, Tailwind CSS v4 via CDN, green theme (`bg-green-500`), manual field rendering (label + input + errors)
- `AuthRequiredMiddleware` protects all URLs except `/login/`, `/logout/`, `/register/`, `/admin/`, `/__debug__/`
