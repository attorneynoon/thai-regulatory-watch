# TCCT OCR Deep Analysis v0.2 — Test and Verification Report

**Report date:** 2026-11-15  
**Branch:** `prototype/tcct-ocr-v0.2-decision-intelligence`  
**Pull request:** draft PR #22  
**Deployment status:** not deployed, not merged

## TDD evidence

| Phase | Commit | GitHub Actions run | Result | Purpose |
|---|---|---:|---|---|
| Initial RED | `cdb10b2e21bda298d6bc4afb5c33a8516350b98c` | `43694539783` | failed | design and tests before implementation |
| Initial GREEN | `f75527906c31f4f4bb2775dfb9ad5b96cafee11d` | `43694703076` | passed | initial router, fourth layer, guards, adapter and integration |
| Hardening RED | `0612991d300aaee1af967c9dff179b3f270f8ab8` | `43695017212` | failed | case-nature, source, provenance and audience regressions |
| Hardened GREEN | `e45a26d140000e3faa116436e5b30fa1cc0ac9e3` | `43695224281` | passed | implemented the hardening controls |
| API-revision RED | `0222feaf066195f251a0c7a5b0d630979f2d9e11` | `43702204810` | 26/27 Node tests passed | missing Interactions API revision header |
| API-revision GREEN | `14f6860add2819826dfc3579c17834bd7ea50a72` | `43702295272` | passed | added `Api-Revision: 2026-05-20` |
| Public-smoke RED | `2f8cd7abc06593d0e81462bff3555b4e801eb7ec` | `43702501776` | failed | smoke tests before runner implementation |
| Public-smoke implementation | `b5ae59b9b892fead1f5b1f63f33dee3880114564` | `43703105088` | passed | fixture, branch prompts, fourth-layer runner and gates |
| Manual-gate RED | `75234e0b420abeb7cdcc1768e9374702aae8db72` | `43703764941` | failed | required label and environment gate |
| Manual-gate GREEN | `79a5c5ff14eb556e8362acfbfb2467e7012b73b2` | `43703858733` | passed | label-only trigger and environment declaration |
| Sensitivity RED | `a9bcf23cb3347835359e052e824de28cffeb83ac` | `43703955051` | 34/35 Node tests passed | missing sensitivity defaulted to public |
| Sensitivity GREEN | `e17a7384dfbd29feb174ca85d390656c3da2d2f0` | `43704094689` | passed | explicit classification and fail-closed blocking |
| Dedicated-secret RED | `2d08117ed46a17a634f8cf757e64d270eea4a445` | `43704218775` | failed | workflow exposed broad fallback secret names |
| Dedicated-secret GREEN | `d90db7d9a6f380396d1177d41f90b4a222e47f91` | `43704309960` | passed | hosted workflow accepts only environment `GEMINI_API_KEY` |

## Contract/regression coverage

The Node suite contains **35 tests**. The repository suite contains **212 Python-discovered tests**, including the Node wrapper and workflow-security contracts.

Coverage includes case routing and segmentation; preservation of the three original branches; theory-of-harm, actual/ideal evidence and counterargument structures; provenance and cross-case boundaries; academic-source governance; eight business audiences; OCR certainty controls; current Interactions API request and response contracts; explicit sensitivity classification; public-smoke source-to-output checks; manual label/environment gating; and dedicated-secret enforcement.

## Latest full repository verification

Validation run `43704309960` completed successfully:

1. `python -m unittest discover -s tests -v` — **212 tests passed**;
2. `python -m regwatch validate` — passed;
3. `python -m regwatch build` — passed;
4. `python -m regwatch check` — XML and JSON contracts passed;
5. deterministic rebuild — passed with no diff.

The separate `tcct-api-qualification` job was skipped by its workflow condition; it is unrelated to this prototype’s local contract tests.

## Hosted public-document smoke result

Workflow run `43703105149` successfully built the public-derived scanned fixture and generated review reports. Fixture evidence:

- SHA-256: `9d2b6e8c19febd4e7d4100dca5e05e1411e926691e684b7b042b2deecbc5ac71`
- size: `138750` bytes
- pages: `1`
- artifact ID: `14156844552`
- artifact ZIP SHA-256: `a11ab2ddbc970ade3a7718ddb4b083c4ac142a9202d3ae92ed5f481c162ce3fb`

The live model stage did not run because no key was configured. The report states `BLOCKED_NO_API_KEY`, `liveCallExecuted: false`, model candidate `gemini-3.8-flash`, API revision `2026-05-20`, and review status `AI_DRAFT_REVIEW_REQUIRED`. The workflow failed at the final gate because only `PASS` is accepted.

## Security changes after the initial hosted run

The live workflow now:

- runs on a PR only when label `run-public-gemini-smoke` is applied to a same-repository branch;
- declares environment `tcct-public-smoke`;
- uses only `GEMINI_API_KEY` from that environment;
- retains read-only repository permissions;
- does not run on ordinary pushes or PR synchronization;
- requires explicit document sensitivity before request construction.

The repository administrator must still configure environment protection and required reviewers. The workflow file cannot itself prove that administrative setting exists.

## What is verified

- Apps Script-compatible routing, request-building and validation logic behaves as defined;
- the public scanned fixture is reproducible in hosted CI;
- missing credentials are detected before document transmission;
- source-to-output checks cover facts, evidence depth, academic status and business audiences;
- unsafe OCR certainty, unsupported numeric targets and unsourced penalty claims fail closed;
- ordinary repository validation and deterministic build controls remain green.

## What remains unverified

- successful Gemini authentication;
- four live calls and live response quality;
- native-PDF OCR fidelity on the fixture;
- live Google Drive OCR and Docs rendering;
- legal correctness after human review;
- corpus-level precision, recall, hallucination and OCR-error measurement;
- Apps Script quota, retry and checkpoint behavior;
- Thai Legal Assistant 2.0 writeback.

## Next release gate

Create/configure GitHub environment `tcct-public-smoke`, add required reviewers, store one dedicated environment secret named `GEMINI_API_KEY`, and then apply label `run-public-gemini-smoke` to draft PR #22. Do not place the key in source, a PR comment, chat or an artifact. A future `PASS` remains review-only and does not authorize merge, deployment, production Drive writes or Thai Legal Assistant integration.
