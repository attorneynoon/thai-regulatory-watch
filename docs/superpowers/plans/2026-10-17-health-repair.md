# Source health repair implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement the tasks with regression tests and independent final review.

**Goal:** Repair the observed NCSA response-budget limitation and make source-health failures actionable without relaxing source verification or altering retained history.

**Architecture:** Keep collection, publication and source-health evaluation separate. Increase only the three explicit NCSA response budgets within the existing registry ceiling. Evaluate health without mutating state, and bind the workflow health check to the exact persisted collection commit.

**Tech stack:** Python 3.12, existing pinned requirements, unittest, GitHub Actions.

**Spec:** Owner's 2026-10-17 request: investigate run 38967834550 against current main, distinguish access limitations from software faults, preserve verified/candidate standards, keep working collection/deployment, and verify without rewriting collected history. Existing project constraints are in AGENTS.md and docs/ADDING_SOURCES.md.

## Global constraints

- Base: `3de47486b2ec93cc48820708f881967c265737c5`.
- No changes to stored `state/`, generated `site/`, schemas, existing event IDs or source IDs.
- No source promotions, downgrades, disabling, relaxed robots/TLS/allowlists, or bypasses.
- Default health still fails for every enabled nonhealthy source, including candidates. Strict coverage additionally fails every nonverified registry scope.
- Keep the three-hour freshness threshold and `deploy.needs: collect`.
- Use a noreply identity for public commits. No production merge or deployment is part of patch preparation.

## Review focus

1. Oversized error pages must not be accepted as valid NCSA publications after a budget increase.
2. Missing, malformed, naive or future success timestamps must not produce false healthy results or crash health evaluation.
3. Candidate PDPC failures remain fatal; healthy candidates remain unverified under strict coverage.
4. A failed push must not publish a collection SHA; a no-change run must still provide one.
5. Verification must preserve bytes and identities of all retained data, and local checks must not be described as hosted source recovery.

## Task 1: Bounded NCSA capacity and useful transport diagnostics

**Files:** config/sources.yml, regwatch/transport.py, tests/test_response_budget.py, qualification/report documentation.

**Interface:** `Transport.fetch` keeps its current return tuple and finite byte limit. Overflow remains a ValueError with the existing message prefix, enriched with the configured limit, minimum bytes observed, HTTP status and content type.

- [x] Test a valid synthetic NCSA JSON response larger than 32,000,000 bytes through the actual transport and collector with repository source definitions; confirm the old configuration fails.
- [x] Test exact byte-limit acceptance, one-byte-over rejection, full preservation of prior observations/events on overflow, and rejection of an HTTP403 response.
- [x] Change only the three NCSA budgets to 64,000,000 bytes, the already-supported registry ceiling; update current limitations without rewriting prior qualification evidence.
- [x] Verify the targeted tests and existing publication/category/date-sort tests pass.

**Evidence boundary:** The current hosted errors prove that the 32MB response guard fires, not that today's body is valid JSON. The 64MB proposal is bounded operational headroom; live payload size and hosted recovery remain unverified until the read-only qualification command succeeds. No global limit increases.

## Task 2: Read-only health evaluation

**Files:** regwatch/health.py, regwatch/cli.py, tests/test_health.py, README.md.

**Interface:** `health_problems(sources, state, *, strict_coverage=False, now=None)` returns the existing list of problem rows with additive diagnostics. Preserve `source`, `status`, `validation`; add stored status, enabled flag, last attempt/success/error, byte limit, and explicit reasons. It never changes state.

- [x] Write regressions for verified and candidate failure, strict coverage of healthy candidates and disabled pending scopes, stale boundary, invalid success timestamps, retained errors and state immutability.
- [x] Observe the timestamp/diagnostic regressions fail against the original CLI, then extract and correct the health evaluator.
- [x] Keep CLI stdout as a JSON array and preserve healthy-candidate/default and strict-coverage exit semantics.
- [x] Verify the targeted health tests pass.

## Task 3: Exact snapshot and repeatable source qualification

**Files:** .github/workflows/monitor.yml, scripts/qualify_ncsa.py, .github/workflows/ncsa-qualification.yml, tests/test_workflows.py, tests/test_ncsa_qualification.py.

**Interfaces:** Collection emits `state_sha` after a successful preservation step, including a no-change run. Health checks out that SHA. The qualification script fetches the common NCSA export once, evaluates all three configured scopes against an in-memory copy of retained state, prints bounded diagnostic JSON, and performs no file writes or deployment.

- [x] Test the actual preservation shell step in temporary local Git repositories for changed, unchanged and push-failure paths before altering workflow wiring.
- [x] Add the step/job output and exact health checkout ref without changing collection/deployment dependencies or behavior.
- [x] Test qualification for a valid response, blocked response, oversize response and historical preservation; then implement the script and a read-only manually triggered workflow.
- [x] Run the whole suite, registry validation, offline build and artifact contract checks in a disposable export of the checkout.
- [x] Compare retained state/site/schema hashes before and after verification; independently review the complete diff.
- [x] Package the tested patch with a source-backed investigation report and public-safe run audit. Clearly distinguish local verification from the unexecuted hosted qualification.

## Execution notes

- Baseline with pinned dependencies: 122 tests passed on Python3.12.
- The ordinary NCSA probe stopped on environment DNS resolution before content retrieval. No source denial, measured payload growth or hosted recovery is inferred from that probe.
- The authenticated connector does not expose commit-author control; the local Git checkout has no push credential. Public commit preparation must retain the noreply requirement instead of assuming the connector's default identity is safe.

## Verification closeout

- 152 tests passed in the independent full-suite run; review found no code findings.
- Registry validation, offline build, XML/JSON checks, and deterministic rebuild passed in a disposable export. All 282 generated site files matched across repeated builds.
- All 287 tracked state/site/schema files retain their base hashes; state remains 3,974 items / 4,499 observation events / 442 health transitions.
- Four actual-state clock-controlled CLI comparisons retained identical original/patched problem sets and exit codes.
- The current NCSA payload and GitHub-hosted recovery remain unverified. Remaining live acceptance is documented in reports/HEALTH_FAILURE_INVESTIGATION_2026-10-17.md.
