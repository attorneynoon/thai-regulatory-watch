# TCCT OCR Deep Analysis v0.2 — Test and Verification Report

**Report date:** 2026-11-15  
**Branch:** `prototype/tcct-ocr-v0.2-decision-intelligence`  
**Pull request:** draft PR #22  
**Deployment status:** not deployed, not merged

## TDD evidence

| Phase | Commit | GitHub Actions run | Result | Purpose |
|---|---|---:|---|---|
| Initial RED | `cdb10b2e21bda298d6bc4afb5c33a8516350b98c` | `43694539783` | failed at unittest | design and tests existed before implementation |
| Initial GREEN | `f75527906c31f4f4bb2775dfb9ad5b96cafee11d` | `43694703076` | passed | initial router, fourth layer, guards, adapter and integration |
| Hardening RED | `0612991d300aaee1af967c9dff179b3f270f8ab8` | `43695017212` | failed at unittest | case-nature, source-namespace, provenance, stakeholder and approval regressions |
| Hardened GREEN | `e45a26d140000e3faa116436e5b30fa1cc0ac9e3` | `43695224281` | passed | implemented the hardening controls |
| API-revision RED | `0222feaf066195f251a0c7a5b0d630979f2d9e11` | `43702204810` | 26/27 Node tests passed | reproduced missing current Interactions API revision header |
| API-revision GREEN | `14f6860add2819826dfc3579c17834bd7ea50a72` | `43702295272` | passed | added default `Api-Revision: 2026-05-20` |
| Public-smoke RED | `2f8cd7abc06593d0e81462bff3555b4e801eb7ec` | `43702501776` | failed at Node import | smoke tests existed before runner implementation; earlier 27 tests remained green |
| Public-smoke implementation | `b5ae59b9b892fead1f5b1f63f33dee3880114564` | `43703105088` | passed | added fixture builder, three branch prompts, fourth-layer runner and deterministic gates |

## Contract/regression coverage

The Node suite contains **34 tests**, invoked through `tests/test_tcct_decision_intelligence_v02.py` as part of the repository’s Python unittest command.

Covered behavior includes:

- Section 57 primary/secondary routing and unfair-conduct nature tags;
- Section 54 agreement evidence without inventing a universal enforcement element;
- merger pre-approval versus post-notification;
- horizontal, vertical and conglomerate/ecosystem merger tags;
- multi-decision segmentation, including Markdown headings;
- preservation of `litigation`, `competition`, `platform` and serial addition of `decision_intelligence`;
- source isolation per decision segment;
- detailed theory-of-harm and stakeholder schema;
- actual evidence, ideal evidence, counterarguments and litigation-war-room depth;
- missing-evidence custodian/authentication requirements;
- cross-case citation rejection and separate academic-source namespace;
- missing provenance, inferred dissent, unsupported numeric target and penalty-source guards;
- non-empty role-specific takeaways for eight audiences;
- native-PDF inline/file-URI request shape;
- Interactions API revision `2026-05-20`, structured JSON and `store=false`;
- confidential/privileged approval gate;
- OCR certainty/status validation and private-use-glyph cleanup;
- current `steps → model_output → content.text` response parsing;
- explicit `BLOCKED_NO_API_KEY` reporting rather than a false success.

## Latest full repository verification

Validation run `43703105088` completed successfully:

1. `python -m unittest discover -s tests -v` — **210 tests passed**;
2. `python -m regwatch validate` — **103 sources, 82 enabled, 21 pending, 53 regulator groups, 9 practices**;
3. `python -m regwatch build` — **6,110 items, 7,473 events and 267 feeds**;
4. `python -m regwatch check` — XML and JSON contracts passed;
5. deterministic rebuild — passed with no diff.

The separate `tcct-api-qualification` job was skipped by its workflow condition; it is unrelated to this prototype’s contract tests.

## Hosted public-document smoke result

Workflow run `43703105149` successfully:

- installed the pinned fixture tooling;
- rendered a one-page public-derived Thai source fixture;
- converted it into an image-only PDF;
- verified the PDF signature and bounded size;
- generated review-only JSON and Markdown reports;
- uploaded the report artifact.

Fixture evidence:

- SHA-256: `9d2b6e8c19febd4e7d4100dca5e05e1411e926691e684b7b042b2deecbc5ac71`
- size: `138750` bytes
- pages: `1`
- artifact ID: `14156844552`
- artifact ZIP SHA-256: `a11ab2ddbc970ade3a7718ddb4b083c4ac142a9202d3ae92ed5f481c162ce3fb`

The live model stage did **not** run. All three supported secret variables were empty:

- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_GENAI_API_KEY`

The generated report therefore states:

- status: `BLOCKED_NO_API_KEY`
- live call executed: `false`
- model candidate: `gemini-3.8-flash`
- API revision: `2026-05-20`
- review status: `AI_DRAFT_REVIEW_REQUIRED`

The workflow failed at the final enforcement gate because only `PASS` is accepted. This is the intended fail-closed behavior.

## What is verified

- the pure JavaScript/Apps Script-compatible routing, request-building and validation logic behaves as defined by the tests;
- the public scanned-PDF fixture can be reproduced in hosted CI;
- the smoke runner detects absent credentials before sending any document;
- the three branch and fourth-layer prompts are ready to execute once a supported secret exists;
- the repository’s existing validation, build and deterministic-output controls remain green.

## What remains unverified

- successful authentication to Gemini;
- four live calls and current response-schema compatibility;
- native-PDF OCR quality on the public fixture;
- final structured-output compliance and evidentiary quality;
- live Google Drive OCR and Google Docs rendering;
- legal correctness after human review;
- corpus-level precision, recall, hallucination and OCR-error measurement;
- Apps Script quotas, timeout, retry and checkpoint behavior;
- Thai Legal Assistant 2.0 import/writeback.

## Next release gate

Configure exactly one supported GitHub Actions repository secret—preferably `GEMINI_API_KEY`—without putting the value in source, logs or chat. Then change `smoke-trigger.txt` to start a fresh PR smoke run. A passing live run must still remain review-only and must not authorize merge, deployment, production Drive writes or Thai Legal Assistant writeback.
