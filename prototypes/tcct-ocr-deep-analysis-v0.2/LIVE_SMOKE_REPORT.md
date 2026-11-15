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
- expected facts include the multi-carrier arrangement, the 20 June 2567 carrier-change request, the pleaded 3.3-kilometre distance, the approximately 600-metre finding and dominance not being reached.

## Credential gate

At the time of this historical run, all supported key variables were empty. The runner generated a blocked report before constructing or transmitting a live request. No PDF bytes or prompt were sent to Gemini.

The workflow has since been hardened. Future hosted runs consume only the dedicated secret `GEMINI_API_KEY` from environment `tcct-public-smoke`; broad `GOOGLE_API_KEY` and `GOOGLE_GENAI_API_KEY` fallbacks are no longer exposed by the hosted workflow.

## Workflow behavior

The following steps passed:

- checkout;
- Python setup;
- bounded Playwright/Chromium installation;
- public scanned-fixture construction;
- blocked-report generation;
- report printing;
- review-artifact upload.

The final enforcement step failed because it accepts only `PASS`. It correctly rejected `BLOCKED_NO_API_KEY` rather than converting a missing credential into a green check.

## Artifact

- artifact ID: `14156844552`
- artifact name: `tcct-public-gemini-smoke`
- artifact ZIP SHA-256: `a11ab2ddbc970ade3a7718ddb4b083c4ac142a9202d3ae92ed5f481c162ce3fb`
- retention configured for 14 days

The artifact contains only the review report. It does not contain an API key, raw request body, base64 PDF, privileged material or production data.

## Deterministic verification after hardening

Validation run `43704309960` passed 212 repository tests, registry validation, build, XML/JSON checks and deterministic rebuild. The Node subset contains 35 decision-intelligence and smoke-contract tests.

Additional fail-closed controls now require:

- manual label `run-public-gemini-smoke` or manual dispatch;
- same-repository PR for label-triggered runs;
- environment declaration `tcct-public-smoke`;
- one dedicated environment secret `GEMINI_API_KEY`;
- explicit `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, or `PRIVILEGED` classification;
- complete provider/retention/region/access approvals for non-public documents.

## Remaining administrative action

A repository administrator must create or configure environment `tcct-public-smoke`, add required reviewers and place the dedicated `GEMINI_API_KEY` secret in that environment. After that, applying label `run-public-gemini-smoke` to draft PR #22 will start the bounded public smoke.

A future `PASS` would verify only this public-fixture path. It would not approve production deployment, confidential-document processing, full-corpus accuracy, Drive writeback or Thai Legal Assistant integration.
