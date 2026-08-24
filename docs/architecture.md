# Architecture

## Overview

Test Radar is a monolithic Django application with three main interfaces:

1. **REST API** (`api/`) — receives test results from agents
2. **Web UI** (`gui/`) — renders the pass/fail matrix and management pages
3. **Auth** (`auth/`) — user registration, login, email confirmation

```mermaid
graph TB
    subgraph Clients
        CI[CI Pipeline Agent]
        Dev[Local Dev Agent]
        Browser[Browser / Web UI]
    end

    subgraph Django App
        API[api/ - REST API]
        GUI[gui/ - Web Views]
        AUTH[auth/ - Auth Views]
        SRV[records/srv/ - Service Layer]
        MODELS[records/models.py - Domain Models]
    end

    subgraph Data
        PG[(PostgreSQL / SQLite)]
    end

    CI -->|Token auth + bulk POST| API
    Dev -->|Token auth + bulk POST| API
    Browser -->|Session auth| GUI
    Browser -->|Session auth| AUTH

    API --> SRV
    API --> MODELS
    GUI --> SRV
    GUI --> MODELS
    SRV --> MODELS
    MODELS --> PG
```

## Request flow

### API: bulk test result submission

```mermaid
sequenceDiagram
    participant Agent
    participant Auth as AgentTokenAuthentication
    participant Token as token.py
    participant View as BulkCreateTestRecordView
    participant DB as Database

    Agent->>Auth: POST /api/v1/test_record/bulk_create/ Authorization: Token ci_xxx
    Auth->>Token: verify_token(raw_token)
    Token->>DB: Filter ApiToken by token_mask__startswith=prefix
    Token->>Token: bcrypt.checkpw for each candidate
    Token-->>Auth: ApiToken (verified)
    Auth->>DB: Update last_used_at, last_used_ip
    Auth-->>View: (agent.owner, api_token)
    View->>View: Validate via BulkCreateSerializer
    View->>DB: TestSession.objects.get_or_create(session_id)
    View->>DB: base64-decode logs, bulk_create TestRecords
    View-->>Agent: 201 {"created": N}
```

### Web UI: project matrix

```mermaid
sequenceDiagram
    participant Browser
    participant Middleware as AuthRequiredMiddleware
    participant View as ProjectView
    participant Record as record.py
    participant DB as Database

    Browser->>Middleware: GET /project/<guid>?datetime_from=...
    Middleware->>Middleware: Check auth (redirect to /login/ if unauthenticated)
    Middleware->>View: Pass request
    View->>Record: filtered_records(project_id, request)
    Record->>DB: Filter TestRecord by date/agent/branch/session
    Record->>Record: Build matrix (rows=labels, columns=sessions)
    Record-->>View: {columns, rows}
    View-->>Browser: HTML with matrix table
    Browser->>Browser: flaky.js detects flaky tests, applies badges
```

## Domain model

```mermaid
erDiagram
    User ||--o{ Project : owns
    User ||--o{ Membership : has
    User ||--o{ Agent : owns
    Project ||--o{ Membership : has
    Project ||--o{ Agent : has
    Project ||--o{ TestSession : has
    Project ||--o{ TestRecord : has
    Agent ||--|| ApiToken : has
    Agent ||--o{ TestRecord : submits
    TestSession ||--o{ TestRecord : contains

    Project {
        uuid guid
        string name
        fk owner
        datetime created_at
    }
    Membership {
        fk user
        fk project
        enum role
    }
    Agent {
        string name
        enum type
        uuid guid
        fk project
        fk owner
    }
    ApiToken {
        string token_hash
        string token_mask
        string scopes
        datetime expires_at
        datetime last_used_at
        ip last_used_ip
    }
    TestSession {
        uuid id
        fk project
        datetime started_at
        string os
        string os_version
        string arch
        string branch
        string commit_hash
    }
    TestRecord {
        hex id
        fk project
        fk agent
        fk session
        text label
        bool success
        datetime timestamp
        binary logs
    }
```

## Layering

```mermaid
graph TB
    subgraph Presentation
        API[api/ - DRF Views + Serializers]
        GUI[gui/ - Django Views + Templates]
        AUTH[auth/ - Django Views + Forms]
    end

    subgraph Service
        TOKEN[token.py - Token generation/verification]
        PERM[permissions.py - RBAC/owner checks]
        RECORD[record.py - Matrix building/filtering]
    end

    subgraph Domain
        MODELS[records/models.py]
        AUTH_MODELS[auth/models.py]
    end

    subgraph Infrastructure
        DB[(PostgreSQL)]
        EMAIL[Brevo Email]
        STATIC[WhiteNoise Static]
    end

    API --> TOKEN
    API --> MODELS
    GUI --> PERM
    GUI --> RECORD
    GUI --> MODELS
    AUTH --> AUTH_MODELS
    AUTH --> EMAIL
    TOKEN --> MODELS
    PERM --> MODELS
    RECORD --> MODELS
    MODELS --> DB
```

## Key design decisions

- **Service layer** (`records/srv/`) holds business logic, keeping views and models thin
- **Feature flags** (`RBAC_ENABLED`, `REGISTRATION_ENABLED`) control optional behavior without deployment changes
- **Token verification** uses prefix-based filtering to limit bcrypt comparisons (see [ADR-0004](adr/0004-token-prefix-scheme-for-agent-type-identification.md))
- **Log compression** happens at the model level via `zstd` (see [ADR-0001](adr/0001-zstd-compression-for-test-logs.md))
- **Flaky detection** runs client-side in `flaky.js`, not server-side, to keep the server stateless and the algorithm adjustable without redeployment

## Middleware

`AuthRequiredMiddleware` protects all URLs except `/login/`, `/logout/`, `/register/`, `/admin/`, and `/__debug__/`. Unauthenticated requests to any other URL are redirected to the login page.

## Security layers

| Layer | Mechanism |
|-------|-----------|
| Web UI auth | Django session auth via `AuthRequiredMiddleware` |
| API auth | Custom `AgentTokenAuthentication` (Token header) |
| Brute-force protection | django-axes (5 failures → 1h lockout) |
| Rate limiting | django-ratelimit |
| Token storage | bcrypt hash + masked preview, never plaintext |
| Admin URL | Obscured via `ADMIN_SECRET_PATH` prefix |
