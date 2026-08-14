# AGENTS.md

## Commands

- **Run tests:** `uv run pytest`
- **Coverage:** runs automatically on every pytest run (fail under 80%); HTML report: `uv run pytest src --cov-report=html`
- **Lint:** `uv run ruff check src && uv run flake8 src/`
- **Type check:** `uv run mypy src/`
- **Format:** `uv run ruff format src/`

## Conventions

- Python 3.14+, Django 6.0
- Line length: 120
- Quote style: single quotes
- Ruff rules: `ALL` with specific ignores (see `pyproject.toml`)
- External linter: wemake-python-styleguide (WPS rules via flake8)
- mypy with django-stubs plugin, settings module: `server.settings`
- Tests use pytest + pytest-django, located in `src/tests/it/`
- Test files ignore: `ARG001`, `FLY002`, `PLR2004`, `S101`, `S106`
- Migrations excluded from linting
- No comments in code unless explicitly requested
- Avoid `noqa` comments — fix the underlying linter issue instead. If a rule is genuinely a false positive or cannot be reasonably fixed, flag it to the user rather than suppressing with `noqa`
- In tests, use `@pytest.mark.usefixtures('fixture_name')` for fixtures that set up state but are not referenced directly in the test body, instead of unused function arguments
- Test data setup (model instances, bulk-created records, etc.) belongs in fixtures (`src/tests/fixtures.py`), not inline in test functions. Reuse existing fixtures before creating new ones.
- Avoid `typing.cast()` — perform explicit validation (e.g. `isinstance` checks, direct attribute access) instead of type casting. This prevents conflicts between ruff TC006 (requires quotes in `cast`) and WPS226 (flags repeated string literals)
- SPDX license headers at the top of every source file
- i18n enabled: use `gettext_lazy` (`_`) for all user-facing text
- When adding new user-facing strings: run `uv run django-admin makemessages -l ru -l en --no-location --no-wrap` (from `src/`) to regenerate `.po` files, then fill in translations in `src/locale/ru/LC_MESSAGES/django.po` and `src/locale/en/LC_MESSAGES/django.po`, then run `uv run django-admin compilemessages -l ru -l en` (from `src/`). Always use `makemessages` to generate `.po` entries — manual edits will be overwritten and cause CI failures
- Forms: hand-rendered with Tailwind, no form libraries (no crispy-forms, etc.)
- Form views use `FormView` with `form_valid` override; `owner`/user set from `request.user` in view, not in form
- All imports (stdlib, third-party, local) must be at the top of the file — never inside functions
- Templates extend `base.html`, Tailwind CSS v4 via CDN, green theme (`bg-green-500`), manual field rendering (label + input + errors)
- `AuthRequiredMiddleware` protects all URLs except `/login/`, `/logout/`, `/register/`, `/admin/`, `/__debug__/`
