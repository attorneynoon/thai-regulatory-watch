# TCCT Public Gemini Smoke — Hosted Result

**Run date:** 2026-11-15  
**GitHub Actions run:** `43703105149`  
**Commit tested:** `b5ae59b9b892fead1f5b1f63f33dee3880114564`  
**Status:** `BLOCKED_NO_API_KEY`  
**Live Gemini call executed:** `false`

## Scope approved

One public-derived, anonymized, image-only TCCT unfair-trade fixture. The run was not authorized to deploy, merge, write to production Drive or update Thai Legal Assistant 2.0.

## Fixture result

The workflow built the scanned fixture successfully:

- one PDF page;
- 138,750 bytes;
- SHA-256 `9d2b6e8c19febd4e7d4100dca5e05e1411e926691e684b7b042b2deecbc5ac71`;
- expected public facts include the multi-carrier arrangement, the 20 June 2567 carrier-change request, the pleaded 3.3-kilometre distance, the approximately 600-metre finding and dominance not being reached.

## Credential gate

The runner checked, in order:

1. `GEMINI_API_KEY`
2. `GOOGLE_API_KEY`
3. `GOOGLE_GENAI_API_KEY`

All were empty. The runner therefore generated a blocked report before constructing or transmitting a live request. No PDF bytes or prompt were sent to Gemini.

## Workflow behavior

The following steps passed:

- checkout;
- Python setup;
- bounded Playwright/Chromium installation;
- public scanned-fixture construction;
- smoke-runner execution;
- report printing;
- review-artifact upload.

The final enforcement step failed because it accepts only `PASS`. It correctly rejected `BLOCKED_NO_API_KEY` rather than converting a missing credential into a green check.

## Artifact

- artifact ID: `14156844552`
- artifact name: `tcct-public-gemini-smoke`
- artifact ZIP SHA-256: `a11ab2ddbc970ade3a7718ddb4b083c4ac142a9202d3ae92ed5f481c162ce3fb`
- retained for 14 days under the workflow configuration

The artifact contains only the review report. It does not contain the API key, raw request body, base64 PDF, privileged material or production data.

## Deterministic verification in the companion run

Validation run `43703105088` passed 210 repository tests, registry validation, build, XML/JSON checks and deterministic rebuild. The Node portion contains 34 TCCT decision-intelligence tests, including the public-smoke response parser and source-to-output gates.

## Remaining action

A repository administrator must configure one supported Actions secret—preferably `GEMINI_API_KEY`—and a new change to `smoke-trigger.txt` must start a fresh run. The secret must not be placed in source, a PR comment, a chat message or the report artifact.

A future `PASS` would verify only this public-fixture smoke path. It would not by itself approve production deployment, confidential-document processing, full-corpus legal accuracy, Google Drive writeback or Thai Legal Assistant integration.
