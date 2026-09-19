# Verification record

## Local release qualification — 19 September 2026

- Windows / Python 3.12.14: **35 unit and contract tests passed**.
- `python -m regwatch validate`: 96 sources, 53 institution groups, 32 enabled candidates, 64 pending.
- `python -m regwatch build`: 475 retained items, 475 events, 180 RSS feeds.
- `python -m regwatch check`: all generated RSS/OPML XML and four versioned JSON contracts passed.
- Representative official TCCT and PDPC extracts tested for titles, URLs and explicit publication dates. Broad Revenue Department and ThaiBMA samples inspected; relevance limitations retained.
- Live source qualification and unresolved coverage: [Source coverage](../docs/SOURCE_COVERAGE.md).

Regression coverage includes source-specific observations, stable IDs, A-B-A reversions, unchanged reruns, omission retention, source failure retention, missing/corrupt state, exclusive writers, private IP rejection, exact-host redirect policy, robots failure/denial/delay, XML entity rejection, Thai and RFC dates, unknown dates, PDF signature/hash/conditional checks, first-fingerprint baseline semantics, RSS windows versus JSON history, health separation and workflow permissions.

Standards review: modules separate collection, parsing, state transitions and publication; source configuration is extensible; no private GRC writer or credentials are included. Spec review: combined/change/regulator/topic/source/baseline/health feeds and JSON implemented; unsupported sources are explicitly pending. Full watchlist inventory is not full operational coverage. No legal-effect inference is made.

Remote Actions, Pages readback and browser checks will be appended after execution. Cloud repository authorization is account-specific and is not established by the local GitHub login.

## GitHub and public-host verification — 19 September 2026

- Public repository created: [attorneynoon/thai-regulatory-watch](https://github.com/attorneynoon/thai-regulatory-watch).
- [Linux CI](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/35432348035) passed tests, registry validation, contracts and deterministic two-build comparison.
- [First hosted monitor](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/35432350248): collect **passed**, Pages deploy **passed**, health **failed as intended for unresolved coverage**. This is not an all-green operational result.
- Cloud snapshot: **575 items/events**, all BASELINE; 7 healthy, 11 failed, 14 blocked and 64 pending scopes. TCCT press releases added 100 initial items; PDPC returned robots HTTP 403 from the cloud, so its 81 previously collected observations were retained.
- HTTPS readback: dashboard, eight representative RSS views, OPML and four JSON endpoints returned HTTP 200 with appropriate content types. XML parsing, unique RSS GUIDs, the 500-entry window, review-only extension metadata and all JSON schemas passed. Combined RSS had 500 events, full JSON 575; changes RSS had zero post-baseline events.
- Dashboard rendered at 1440x1000 and 390x844 using headless Edge. Source filtering worked at both widths (96 total rows, 10 PDPC rows); no page-level horizontal overflow or JavaScript errors. Screenshots visually inspected. Added explicit empty-change wording to avoid implying complete coverage.
- Public-file scan found no local user paths, private Drive/Notion destinations, token patterns or private-key markers. Source-derived text remains untrusted evidence. This is a bounded scan, not a security certification.
- Direct GitHub connector metadata and AGENTS.md reads succeeded; metadata reports repository push permission. Repository search enumeration was still empty. Codex cloud environment selection/authorization was not performed; follow [Cloud setup](../docs/CLOUD.md).
- Action logs annotate older Node 20 action runtimes forced onto Node 24 and an upcoming ubuntu-latest migration. Executed jobs passed despite those maintenance warnings. Download of the complete log archive timed out; job/step conclusions and committed output were read successfully.

The hourly schedule is configured, with manual invocation proven. Scheduled delivery is best effort; future unattended executions and all remaining source adapters are not yet verified.

### Reload-determinism amendment

Comparison of cloud-generated XML with an offline rebuild exposed differing extension-field order after state serialization. Added a failing state-roundtrip regression and fixed RSS field ordering. **36 tests passed** after the correction, including identical artifact bytes before/after state JSON reload. Event IDs, observation contents and retained history were unchanged.

### Health-transition amendment

A repeated PDF failure regression exposed intermediate healthy/degraded transitions within one collection. Final health is now emitted once after all listing/document work. **37 tests passed** including repeated-failure deduplication. No recovery is emitted merely because the listing succeeds while its checked attachment still fails.

### Second hosted run

[Run 35432691007](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/35432691007) passed collection and deployment; health remained failed for the same coverage limits. Public readback passed again. All 575 event IDs were unchanged, the changes feed remained empty, and the combined RSS SHA-256 remained `7f1ee6fdb9fa22131de167bf24d6bce67398d2c353e519a972a8a9f035c2f3cf`. New first-time PDF fingerprints did not create revision alerts. The final health-transition amendment was verified by regression tests; it was made after this hosted run and will be picked up by the next scheduled/manual collection.
