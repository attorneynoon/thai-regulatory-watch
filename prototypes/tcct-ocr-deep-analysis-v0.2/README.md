# TCCT OCR Deep Analysis v0.2 — Decision Intelligence Candidate

Review-only extension of the v0.1 Google Workspace / Apps Script prototype.

## Workflow

```text
source preparation
  → decision segmentation
  → case-family and nature routing
  → litigation + competition + platform (parallel)
  → decision_intelligence (serial fourth layer)
  → evidence / audience QA
  → review-only rendering
```

The original three analytical branches remain intact. The fourth layer reconciles them and produces an auditable decision record rather than a longer free-form essay.

## What the fourth layer adds

- the boundary between what the ruling holds and what it does not decide;
- issue-by-issue positions, reasoning, outcome and evidence;
- each theory of harm classified as alleged, accepted, rejected, untested or not reached;
- actual evidence used in the record, ideal evidence, counterarguments, reply evidence and missing proof;
- stronger claimant/regulator and respondent/defense cases;
- outcome-changing counterfactuals, loopholes and repeatability risk;
- fair criticism of TCCT with limits and a counterview;
- academic schools of thought with assumptions, fit, tension and governed-source status;
- translation for boards, executives, product/operations, commercial/procurement, finance, legal/compliance, SMEs/counterparties and investors/lenders.

## Case routing

Primary families:

- `UNFAIR_TRADE`
- `HORIZONTAL_AGREEMENT`
- `VERTICAL_AGREEMENT`
- `ABUSE_OF_DOMINANCE`
- `MERGER_PRE_APPROVAL`
- `MERGER_POST_NOTIFICATION`
- `UNKNOWN`

Secondary nature tags distinguish, among other things, forced participation or tying, discriminatory treatment, termination/refusal, payment terms, self-preferencing, price fixing, market allocation, RPM, exclusive dealing, horizontal overlap, vertical foreclosure, conglomerate/ecosystem effects, data/network effects and remedy design.

The router intentionally does **not** make dependency a universal Section 57 element and does **not** make HHI mandatory for every merger. HHI is a conditional metric when the record, market definition and merger structure support it.

See [`CASE_FAMILY_PLAYBOOK.md`](CASE_FAMILY_PLAYBOOK.md).

## Evidence and provenance controls

Record propositions use only the decision segment’s permitted source IDs. Academic/comparative sources use separate governed external IDs and are not treated as case-record citations.

Material propositions use one of:

`SOURCE_FACT`, `PARTY_ARGUMENT`, `TCCT_FINDING`, `TCCT_HOLDING`, `ANALYST_INFERENCE`, `ACADEMIC_LENS`, `EXTERNAL_RESEARCH`, `HYPOTHESIS`, `MISSING_EVIDENCE`, or `NOT_APPLICABLE`.

The validator rejects, among other things:

- cross-case record citations;
- missing provenance for material holdings;
- empty stakeholder takeaways;
- unsupported numeric targets;
- inferred dissenting reasons;
- uncited penalty statements;
- academic claims marked sourced without a governed external source;
- forbidden analytical modules for the case family.

## OCR and Gemini boundary

The candidate supports a request contract for Gemini native-PDF processing and retains Drive OCR as a fallback. It uses the Interactions API revision `2026-05-20`, structured JSON output and `store=false`.

OCR status is limited to:

- `UNCHECKED`
- `TEXT_EXTRACTED`
- `MANUAL_SAMPLE_REVIEWED`
- `BASELINE_COMPARED`
- `FAILED`

`CLEAN_TEXT` and “zero errors” are not accepted without a defined baseline comparison; a zero-error assertion is rejected when the measured error rate is non-zero.

Confidential or privileged PDF requests are blocked unless provider, retention, region and access approvals are all recorded.

## Public-document smoke harness

The approved smoke harness creates a one-page, image-only public-derived TCCT fixture in CI and is designed to run four Gemini calls:

1. litigation branch;
2. competition branch;
3. platform branch;
4. serial `decision_intelligence` synthesis.

The deterministic gate checks extraction of the multi-carrier arrangement, the 20 June 2567 carrier-change request, the pleaded 3.3-kilometre distance, the approximately 600-metre finding and the fact that dominance was not reached. It also requires actual evidence, ideal evidence, counterarguments, litigation-war-room depth, a fair TCCT critique, governed academic-source status and non-empty takeaways for eight stakeholder groups. It rejects absolute OCR claims, unsupported 80-percent targets and unsourced penalty statements.

The first hosted smoke run created the scanned PDF successfully but did **not** call Gemini because no supported Actions secret was configured. Its status is deliberately `BLOCKED_NO_API_KEY`, and the workflow failed at the final gate rather than treating the blocker as a pass. See [`LIVE_SMOKE_REPORT.md`](LIVE_SMOKE_REPORT.md).

## Files

- `gas/25_DecisionRouter.gs` — segmentation, family routing, nature tags and module plans
- `gas/35_DecisionIntelligenceContract.gs` — fourth-layer schema and prompt contract
- `gas/45_OutputGuard.gs` — provenance, boundary, OCR and audience QA
- `gas/55_GeminiDocumentAdapter.gs` — current request builder; no credential is stored in source
- `gas/95_V02Integration.gs` — integration plan preserving the original three branches
- `tests/*.test.mjs` — Node contract/regression tests
- `../../tests/test_tcct_decision_intelligence_v02.py` — repository CI wrapper
- `scripts/build-public-fixture.py` — bounded scanned-PDF fixture builder
- `scripts/public-smoke-lib.mjs` — response parsing and deterministic smoke checks
- `scripts/public-smoke.mjs` — review-only live smoke runner
- `GEMINI_REVIEW.md` — re-check of the Gemini-augmented outputs
- `CASE_FAMILY_PLAYBOOK.md` — unfair conduct, agreement, dominance and merger depth
- `examples/public-unfair-shipping-decision-intelligence.md` — worked, non-confidential illustration
- `TEST_REPORT.md` — RED/GREEN and full-CI evidence
- `LIVE_SMOKE_REPORT.md` — hosted smoke result and blocker

## Verified in CI

The Node contract/regression suite now contains **34 tests**, invoked through the repository’s Python unittest suite. Validation run `43703105088` passed all **210 repository tests**, registry validation, build, XML/JSON checks and deterministic rebuild.

## Not yet verified

- a successful live Gemini request/response and model-output quality;
- live Drive OCR and Google Docs rendering;
- model performance on a representative corpus of unfair-trade, agreement, dominance and merger decisions;
- legal correctness after human review;
- Thai Legal Assistant 2.0 import/writeback;
- Apps Script execution time, quota, retry and checkpoint behavior for long documents.

## Safety status

All output remains `AI_DRAFT_REVIEW_REQUIRED`. This branch does not deploy, create production triggers, write to production Drive, change Thai Legal Assistant 2.0 or merge itself. The smoke workflow uses a public-derived fixture only and stores no API key, raw request body or base64 PDF in its report artifact.
