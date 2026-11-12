# October 2026 source-health failure investigation

## Outcome and evidence boundary

The observed monitoring runs successfully collected and published retained public data. Their overall failure conclusion came from the independent source-health job. This is a real coverage/freshness warning, not evidence that all collection or Pages deployment failed.

The three verified NCSA scopes repeatedly hit the configured 32,000,000-byte transport limit. Many other enabled sources, including candidate PDPC scopes, had separate access failures. The existing default health policy treats both groups as failures. Suppressing candidates or downgrading NCSA would hide unresolved coverage, so this patch preserves that policy.

The patch provides a bounded NCSA configuration change, actionable error details, robust read-only freshness validation, exact collection-commit selection for health, and a read-only NCSA qualification command. Offline tests and artifact checks pass. **The proposed 64,000,000-byte NCSA cap has not been qualified against a current live response or a GitHub runner. No hosted recovery, production merge, deployment, or successful live qualification is claimed.**

The evidence checkpoint is **2026-10-17 03:44:34 UTC / 10:44:34 Asia/Bangkok**, with `main` at **`3de47486b2ec93cc48820708f881967c265737c5`**. A further main/recent-run read around 04:03 UTC found the same main commit and latest run. All historical repository links below are pinned to the inspected commit where possible. The compact [workflow audit](evidence/2026-10-17-health/workflow-audit.json) records the queried API URLs, jobs, run windows, sampled errors and interpretation limits.

## 1. What failed in run 38967834550

| Stage | Observed result | Meaning |
|---|---|---|
| `collect` | Success; 7 minutes 46 seconds | Collection completed with the existing source-error-tolerant publication policy. |
| `deploy` | Success; 14 seconds | The run's generated Pages artifact was deployed. |
| `health` | Failure at `python -m regwatch health`; exit 1 | Enabled sources were not all healthy. |

The run started at **2026-10-16 21:13:16 UTC**, which is **2026-10-17 04:13:16 Bangkok**. Thus the GitHub UTC date and the Thai calendar date differ. The run's triggering SHA was `b15afdf15813e21d8132ccee9a0b9fae8656292e`; its collection job committed new public outputs at `8f9b6404627eeb41b35936b17413fc9bb1699319`, pushed them at 21:21:00 UTC, and uploaded artifact `12075153782`. The health checkout resolved to that new collection commit at 21:21:23 UTC. **There is no observed stale-checkout cause in this incident.** Pinning health to an explicit output SHA prevents a future race with another writer; it does not reinterpret the recorded failure.

Sources: [run](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/38967834550), [collection job](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/38967834550/job/117198615415), [health job](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/38967834550/job/117201654719), [deployment job](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/38967834550/job/117201654637), and [generated-data commit](https://github.com/attorneynoon/thai-regulatory-watch/commit/8f9b6404627eeb41b35936b17413fc9bb1699319).

The review covered 22 nearby scheduled runs. Every inspected run had successful collection and deployment and failed at the health command. Of those, 21 fall within October 13–16 UTC, while 19 fall within October 13–16 Bangkok. The latest observed run, [38982519301](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/38982519301), finished on October 16 at 23:46:52 UTC with the same outcome and checked the current `3de47486...` state. All three NCSA failures appeared in every inspected health log. Six sampled collection logs, including the requested run, identified the same byte-budget error. These are observations from the [run audit](evidence/2026-10-17-health/workflow-audit.json), not an assumption based only on notification subjects.

The existing [workflow](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/.github/workflows/monitor.yml) intentionally uses `collect --allow-source-errors`. This allows other sources and retained observations to be published while preserving failed source status. Both `deploy` and `health` depend on `collect` independently. The patch keeps these commands and dependencies.

## 2. Separate causes and confidence

| Finding | Classification | What the evidence establishes |
|---|---|---|
| Three NCSA scopes: `Response exceeds byte budget` | Source-specific capacity limit and incomplete diagnostics | The 32,000,000-byte streaming guard fired. It does not establish today's full size, valid JSON, or an HTTP denial. |
| PDPC and other sources: content HTTP 403 or unavailable robots/network/TLS service | Access or upstream-service condition | The collector could not obtain an acceptable response. This is not a successful no-update observation. The publisher's reason for a denial is not established. |
| `courts-watch`: suspicious empty/undersized parse | Extraction/data-quality guard | The current response did not satisfy the existing minimum/count safeguards. Root cause within the site's content or selectors remains unqualified. |
| Original health accepts missing/future success timestamps or crashes on malformed/naive values | Software validation defects found during review | Reproduced by regression tests. These defects were not the demonstrated cause of the requested run. |
| Health checks movable `main` | Preventive workflow hardening | Another writer could change the checked snapshot. The requested run already used the correct collection commit. |
| Overall workflow conclusion is failure | Expected result of an independent health gate | A failed health job affects the overall run even though collection and deployment succeed. |

The supporting current errors are in the pinned [monitor state](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/state/monitor.json). The pre-patch [transport](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/regwatch/transport.py) and [CLI health logic](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/regwatch/cli.py) explain these distinct failure paths.

### NCSA: one export, three overlapping scopes

All three source IDs fetch the same official endpoint, `https://www.ncsa.or.th/data/output/news.json`. They apply different category scopes; they are not independent corroborating sources. The September qualification recorded **27,500,481 bytes**, below the previous 32,000,000-byte cap, with response SHA-256 `888d0024275372f74edf40a96d19fb477fdfee75de3e30bde7dd752046f7fb21`. That is historical evidence only. See the unchanged [NCSA qualification record](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/docs/qualification/enforcement.md) and [source definitions](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/config/sources.yml).

All three last succeeded on **September 29 at 08:35:30 UTC**. The transition into the persistent byte-budget failure occurred at **15:56:04 UTC that day**, before the October notification window. Their retained `last_count` values are **23 / 100 / 100**, with **25 / 132 / 132** retained source observations. These are last-good counts, not counts collected in the failed October runs. The public [health transition history](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/site/api/v1/health.json) and [state snapshot](evidence/2026-10-17-health/snapshot.json) preserve this distinction.

The current reachable commit history shows no collector/transport/registry change at that onset: the last relevant configuration, transport and CLI edits predate it in September 19 commits. This supports investigating an upstream response crossing the limit rather than an October code regression, but it does not prove the response was valid publication JSON. The streaming limit runs before later HTTP/content/parser checks, so an oversized error page could produce the same old message. Path-history evidence is retained in the [audit](evidence/2026-10-17-health/workflow-audit.json).

A single ordinary probe at **2026-10-17 03:44:19 UTC**, using the existing production transport and proposed finite cap, stopped before content retrieval with `Robots unavailable: [Errno -3] Temporary failure in name resolution`. That is a limitation of this execution environment; it is not evidence that NCSA denied the request. No retry through a bypass, raw response retention, state update or local scheduled collector was introduced.

### PDPC: candidate status does not remove the obligation

The current registry contains 13 PDPC scopes, all `candidate`. Twelve are blocked with content HTTP 403; only `pdpc-official-private-sector` is stored as healthy. Its selected-content scope does not establish access to PDPC laws, decisions, consultations or the other blocked listings. The 81 retained official consultation observations last succeeded on September 19. GPPC last succeeded on October 16 at 07:14:46 UTC but is blocked in the latest snapshot. It must not be described as continuously recovered. See the pinned [source snapshot](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/site/api/v1/sources.json) and the compact [evidence extract](evidence/2026-10-17-health/snapshot.json).

Other inspected runs include transient verified-source failures at robots retrieval, such as HTTP 522 for TCC, AMLO TLS/read-timeout failures, and OCPB HTTP 503. Later runs recovered those sources, whereas NCSA's byte-limit failure persisted. They are separate failures at separate layers, as recorded in the [job/error audit](evidence/2026-10-17-health/workflow-audit.json).

## 3. Qualification, runtime health and freshness

`validation_status` records qualification of a source/adapter and its documented scope. Runtime `status` records what collection most recently observed. Health additionally evaluates freshness when the stored source status is healthy. A verified source can fail today; a candidate can return parseable content without becoming verified.

The existing [source qualification procedure](https://github.com/attorneynoon/thai-regulatory-watch/blob/3de47486b2ec93cc48820708f881967c265737c5/docs/ADDING_SOURCES.md) requires official provenance, explicit host and adapter contracts, representative fixtures/extracts, live inspection of titles/dates/document links, exclusions and pagination bounds, and documented limitations. A candidate stays a candidate until that review passes. The patch changes no qualification labels, source IDs, enablement decisions, publication/category filters, item/page limits or access policy.

At `last_run_at = 2026-10-16T23:39:32Z`, the stored snapshot is:

| Qualification | Healthy | Blocked | Failed | Disabled/not run | Total |
|---|---:|---:|---:|---:|---:|
| Verified | 14 | 0 | 3 | 0 | 17 |
| Candidate | 38 | 22 | 1 | 0 | 61 |
| Pending | 0 | 0 | 0 | 21 | 21 |
| Total | 52 | 22 | 4 | 21 | 99 |

These are stored collection statuses, not an assertion that the 52 sources remain fresh at any later reading. Source: [snapshot evidence](evidence/2026-10-17-health/snapshot.json), derived from the pinned registry and state.

| Condition | Default health | Strict coverage |
|---|---|---|
| Enabled verified source, healthy, valid success time no more than three hours old | Pass | Pass |
| Enabled candidate, healthy, valid success time no more than three hours old | Pass, still candidate | Fail for unverified coverage |
| Any enabled source failed, blocked, degraded, never run or stale | Fail, including candidate sources | Fail |
| Enabled source marked healthy but success time is missing, malformed, has no timezone or lies in the future | Fail with an explicit diagnostic | Fail |
| Disabled pending/unverified scope | Does not fail runtime health | Fail for unverified coverage |

No `continue-on-error`, verified-only filter, source disabling, false healthy state or longer freshness window is used. Exactly three hours remains within the boundary; a success older than three hours is stale. The new `stored_status`, `reasons` and `health_error` explain the read-time decision without changing persisted history.

The original and patched real CLI were replayed against the same current registry/state with only the clock fixed for comparison. Normalized `(source, status, validation)` rows were identical in all four cases:

| Evaluation time, UTC | Gate | Original / patched issue count | Exit codes |
|---|---|---:|---|
| October 16, 23:46:52 | Default | 26 / 26 | 1 / 1 |
| October 16, 23:46:52 | Strict | 85 / 85 | 1 / 1 |
| October 17, 03:44:34 | Default | 78 / 78 | 1 / 1 |
| October 17, 03:44:34 | Strict | 99 / 99 | 1 / 1 |

At the later time the 52 stored healthy sources are stale, which explains the larger issue count. Clock freezing was a test technique, not a runtime bypass added to the CLI. See [gate replay evidence](evidence/2026-10-17-health/health-gate-replay.json).

`site/api/v1/health.json` contains health **transitions**. Repeated identical failure status need not append a transition, even though another failed attempt occurred. Use `state/monitor.json` or the published `site/api/v1/sources.json` for the latest attempt, last success, last error and retained counts. The health command reads the registry and monitor state directly; it does not fetch the deployed Pages health URL.

## 4. Patch contents

| Files | Change and purpose |
|---|---|
| `config/sources.yml` | Increase only the three NCSA response caps from 32,000,000 to 64,000,000 bytes, the existing registry ceiling; document the live qualification limitation. |
| `regwatch/transport.py` | Keep the overflow failure and add the configured limit, minimum bytes received, HTTP status and bounded content type to the error. |
| `regwatch/health.py`, `regwatch/cli.py` | Evaluate health without mutation; retain the JSON list and original identifying fields; add diagnostics and reject unprovable timestamps without crashing. |
| `.github/workflows/monitor.yml` | Emit `state_sha` after successful persistence, including no-change runs, and check out that SHA in health. A failed push emits no successful output. Collection and deployment behavior remain independent of health. |
| `scripts/qualify_ncsa.py` | Fetch the common export once through the existing transport, run all three real source collectors in memory, check retained identities/history, and print compact diagnostics. |
| `.github/workflows/ncsa-qualification.yml` | Add a manual-only, read-only, five-minute qualification workflow with pinned actions/dependencies and no deployment or persistence. |
| Tests and documentation | Add regression coverage, the interpretation table, evidence and this report. |

The 64 MB setting is decimal bytes and remains a source-specific upper bound. It is proposed headroom based on repeated 32 MB guard failures, not a measured current payload size. The global default and maximum supported cap are unchanged. HTTP denial, challenges, robots, TLS, host restrictions, JSON shape, published-row/category filters and suspicious count-drop checks remain active. Tests explicitly demonstrate that a large HTTP 403 response or malformed JSON cannot become a successful collection merely because the byte cap increased.

The qualification helper does not save the response body, update tracked state/site files, promote sources or rewrite simulated results into history. Failed-source counts are labeled `retained-state`; successful counts are labeled `current-response`. A healthy response still does not establish exhaustive regulatory coverage.

## 5. Verification completed without rewriting history

| Verification | Result |
|---|---|
| Baseline suite | 122 tests passed before changes. |
| New regressions | 30 added tests: 8 health, 5 transport/budget, 4 persistence/snapshot, 13 qualification tests. Failure reproduced before implementation. |
| Independent complete suite | 152 tests passed in 5.898 seconds with Python 3.12 and pinned requirements. |
| Registry validation | Passed: 99 scopes, 78 enabled, 21 pending, 53 regulator groups, 9 practices. |
| Offline build in a disposable export | Passed: 3,974 items, 4,499 observation events, 262 feeds. |
| XML/JSON contract checks | Passed. |
| Required deterministic second build | All 282 generated site files byte-identical to the first build. |
| Protected checkout hashes | All 287 tracked files under `state/`, `site/`, and `schemas/` unchanged from the base. |
| Retained state in the disposable export | Byte-identical before and after building; 3,974 items, 4,499 observation events, 442 health transitions retained. |
| Independent code review | No Critical, Important or Minor findings. |
| Live NCSA and GitHub qualification | Not completed; the local probe stopped at DNS resolution. |

The preserved `state/monitor.json` SHA-256 is **`922a6a0655395b8b16b5b38279dcf6634f8e581ac7ecda4a36d01081c0182ce9`**. Byte identity is stronger than merely checking unchanged counts. Regression tests also exercise prior event/observation preservation when a response is oversized, blocked, malformed or suspiciously small. Git workflow tests use isolated temporary repositories for real changed/no-change/rejected-push/concurrent-writer scenarios; they do not push this project.

All builds occurred in a disposable export, not in the production worktree. No changed file under `state/`, `site/` or `schemas/` is part of this patch. The [verification evidence](evidence/2026-10-17-health/verification.json) records commands and results without machine-specific paths.

## 6. Reproduce offline validation and qualify hosted behavior

Apply the patch on its recorded base or review its diff against a newer main commit. Keep generated outputs out of the maintenance commit. In a disposable checkout with Python 3.12 and the repository's pinned dependencies, run:

```bash
python -m pip install --upgrade pip==26.2.1
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
python -B -m regwatch validate
python -B -m regwatch build
python -B -m regwatch check
```

Repeat `build` and compare every generated file's hash as the existing CI workflow does. Compare retained-state hashes before and after. Running build only in the disposable checkout keeps regenerated presentation metadata out of the retained production tree.

Then, from an environment with ordinary permitted NCSA access, run the read-only command:

```bash
python -B scripts/qualify_ncsa.py
```

This command makes one export fetch and evaluates all three existing source definitions. It exits zero only when every source is healthy and history preservation checks pass. Review the actual `bytes`, `sha256`, `http_status`, `content_type`, per-source counts and `count_basis`, and confirm `history_preserved: true`. Validate representative publications against the official scope and existing qualification procedure if the response contract or content has changed. No body, state, generated site or source status is written.

The new manual workflow provides the same command on a GitHub runner once that workflow is registered on the default branch. A newly added `workflow_dispatch` file cannot be invoked from GitHub's manual UI before it exists on the default branch, as documented in [GitHub's workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch); the command can be run earlier in an already permitted review environment. A local success must not be described as GitHub recovery.

If the response still exceeds 64,000,000 bytes or fails HTTP/JSON/count checks, preserve the failure and use the richer diagnostic to select the next repair. Do not automatically raise the global ceiling, disable verification or replace important PDPC/NCSA coverage with adjacent publicity/service pages. Any alternative official feed or endpoint needs its own provenance and extraction qualification.

After review and application, observe a normal monitoring run: collection persists its data, deployment uses that run's artifact, and health checks the emitted collection SHA. Verify old item IDs and the immutable event prefix remain present, allowing ordinary new observations to append through the collector. Successful NCSA qualification does **not** require the entire health job to turn green: at the fresh replay time, the snapshot already had 23 other enabled nonhealthy candidates, and later stale sources also remain fatal. Acceptance is accurate status, preserved history, working collection/deployment and demonstrable recovery for the sources actually repaired.

## 7. Separate freshness scheduling follow-up

The inspected workflow declares hourly cron `17 * * * *`, but 19 of the 20 within-window intervals for October 13–16 UTC exceeded three hours; the maximum observed gap was **8 hours 17 minutes 7 seconds**. The Bangkok-date window has 18 intervals, all exceeding three hours. These are observed run-start gaps, not measured execution queue times. At the evidence checkpoint there were no queued or in-progress runs returned by the queried endpoints. The [audit](evidence/2026-10-17-health/workflow-audit.json) retains the interval calculations and query scope.

This is a separate freshness concern even for sources whose last stored status is healthy. The available evidence does not establish why scheduled runs were so far apart. Investigate scheduling delivery and repository/runner availability separately; the patch deliberately retains the three-hour freshness rule. The failed health job itself is not configured as a dependency that stops deployment or future scheduled collection.

## Remaining acceptance evidence

The maintenance patch and local verification are complete. Current live NCSA payload measurement, permitted hosted qualification, actual post-application monitoring, remaining PDPC/other source access, and the scheduling-gap cause remain outstanding. These unresolved facts should remain visible in operational reporting instead of being converted into a successful health result.

The subsequent main refresh, unchanged-code integration, repeated offline validation and bounded local qualification attempt are recorded in the [October 17 continuation](HEALTH_PATCH_CONTINUATION_2026-10-17.md). This original report retains its original snapshot and evaluation times.
