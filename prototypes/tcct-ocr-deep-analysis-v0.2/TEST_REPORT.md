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
| Hardening RED | `0612991d300aaee1af967c9dff179b3f270f8ab8` | `43695017212` | failed at unittest | added case-nature, source-namespace, provenance, stakeholder and approval regressions |
| Hardened GREEN | `e45a26d140000e3faa116436e5b30fa1cc0ac9e3` | `43695224281` | passed | implemented only the controls required by the hardening tests |

## Contract/regression coverage

The Node suite contains 27 tests, invoked through `tests/test_tcct_decision_intelligence_v02.py` as part of the repository’s Python unittest command.

Covered behavior includes:

- Section 57 primary/secondary routing;
- unfair-conduct nature tags;
- Section 54 agreement evidence without inventing a universal enforcement element;
- merger pre-approval versus post-notification;
- horizontal, vertical and conglomerate/ecosystem merger tags;
- multi-decision segmentation, including Markdown headings;
- preservation of `litigation`, `competition`, `platform` and serial addition of `decision_intelligence`;
- source isolation per decision segment;
- detailed theory-of-harm and stakeholder schema;
- actual versus ideal evidence fields;
- missing evidence custodian/authentication requirements;
- cross-case citation rejection;
- separation of academic external sources from the case record;
- missing provenance rejection;
- inferred-dissent guard;
- unsupported numeric-target guard;
- penalty-source guard;
- non-empty role-specific takeaways;
- native-PDF inline/file-URI request shape;
- structured JSON and `store=false`;
- confidential/privileged approval gate;
- OCR certainty/status validation;
- private-use rendering-glyph cleanup.

## Latest full repository verification

For run `43695224281`, the following steps completed successfully:

1. `python -m unittest discover -s tests -v`
2. `python -m regwatch validate`
3. `python -m regwatch build`
4. `python -m regwatch check`
5. deterministic rebuild

The separate `tcct-api-qualification` job was skipped by its workflow condition; it is unrelated to this prototype’s local contract tests.

## What this proves

The pure JavaScript/Apps Script-compatible routing, request-building and validation logic behaves as defined by the tests. The repository’s existing build and deterministic-output controls were not broken by the candidate branch.

## What this does not prove

- no live Gemini request was made;
- no live Google Drive OCR or Google Docs write was performed;
- no legal conclusion was human-approved;
- no corpus-level precision/recall, hallucination or OCR character-error study was run;
- no Apps Script quota, timeout, retry or checkpoint test was run;
- no Thai Legal Assistant 2.0 import/writeback was exercised;
- no production configuration, trigger or deployment was changed.

## Release gate

Before any merge or live test, review the PR diff and approve a narrowly scoped public-document smoke test. Confidential or privileged material remains blocked until provider, retention, region and access approvals are all recorded.
