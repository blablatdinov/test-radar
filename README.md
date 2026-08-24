<!--
SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
SPDX-License-Identifier: MIT
-->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="Test Radar — Django test monitoring app with pass/fail matrix UI">
</p>

Test Radar is a Django application that collects test results from CI and local agents and displays them in a pass/fail matrix with flaky-test detection.

## Why

Test results disappear when CI pipelines roll over. Test Radar keeps them — so teams can:

- **Spot flaky tests** — the matrix highlights tests that pass and fail on the same commit, making non-deterministic failures visible at a glance
- **Track test history** — every run is stored with logs, branch, and commit, so you can trace when a test started failing and why
- **Compare across environments** — CI and local agents feed into the same project, making environment-specific failures easy to isolate
- **Own your data** — self-hosted, no third-party telemetry or per-seat licensing

## How it works

1. An agent (CI or local) sends test results via a single REST API call
2. Test Radar stores each record with compressed logs, git context, and session metadata
3. The web UI renders a pass/fail matrix (test labels × sessions) with client-side flaky detection

## Documentation

| Document | What's inside |
|---|---|
| [Onboarding](docs/onboarding.md) | Setup (Docker / local), commands, project structure, conventions |
| [User Guide](docs/user-guide.md) | Web UI pages, filters, matrix, flaky detection, dark mode, i18n |
| [Architecture](docs/architecture.md) | Domain model, request flows, layering, security, ADR links |
| [Deployment](docs/deployment.md) | Docker image, CI/CD pipeline, Nginx, production env, manual ops |
| [ADRs](docs/adr/) | Decision records (zstd logs, bcrypt tokens, RBAC, hex PK, more) |

## License

MIT
