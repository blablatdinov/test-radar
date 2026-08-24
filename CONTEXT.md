# Test Radar

A web application that collects test results from CI pipelines and local development agents, displaying them in a pass/fail matrix with flaky-test detection.

## Language

### Core entities

**Project**:
A named container for test results, owned by a User. Agents, test sessions, and test records all belong to a Project.
_Avoid_: Workspace, repository, suite

**Agent**:
A CI pipeline or local development process that submits test results via the REST API. Has a type (CI or Local), a name unique within its Project, and an API token.
_Avoid_: Runner, worker, bot

**TestSession**:
A single run of a test suite identified by a client-provided UUID. Captures the environment (OS, architecture), git context (branch, commit hash), and start time. Groups a batch of TestRecords.
_Avoid_: Run, build, pipeline run

**TestRecord**:
An individual test result within a TestSession. Contains a label, pass/fail status, timestamp, and compressed logs. Identified by a hex token primary key.
_Avoid_: Test result, test case, test entry

### Access control

**Membership**:
A role-based relationship between a User and a Project. Roles: Owner, Maintainer, Developer. Only one membership per (User, Project) pair.
_Avoid_: Permission, access grant, team membership

**Role**:
The access level a Membership grants. Owner can manage everything including members. Maintainer can manage CI agents. Developer can manage local agents and view the matrix.
_Avoid_: Permission level, access level

**ApiToken**:
A credential issued to an Agent for authenticating API requests. Stored as a bcrypt hash with a masked preview. Has optional expiry and tracks last usage.
_Avoid_: Key, secret, credential

### UI concepts

**Matrix**:
The pass/fail grid on the Project page. Rows are test labels, columns are TestSessions. Each cell shows pass (green check) or fail (red cross).
_Avoid_: Grid, table, dashboard

**Flaky test**:
A test label that alternates between pass and fail across sessions without a code change. Detected client-side: requires at least 5 runs, a transition rate >= 0.4, and a failure ratio between 0.15 and 0.85, or inconsistent results for the same commit hash.
_Avoid_: Unstable test, intermittent failure, flickering test

**Token mask**:
A truncated preview of an API token (first 6 chars + last 3 chars) shown in the UI so users can identify a token without seeing the full value.
_Avoid_: Token preview, masked token, token hint

### Token scheme

**Token prefix**:
The leading segment of a raw API token before the underscore. `ci_` for CI agents, `dev_` for Local agents. Used to narrow token verification queries by filtering on the masked preview's prefix.
_Avoid_: Token type identifier, token tag
