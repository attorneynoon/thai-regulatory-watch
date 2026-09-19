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
