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

The candidate supports a request contract for Gemini native-PDF processing and retains Drive OCR as a fallback. It uses structured JSON output and `store=false`.

OCR status is limited to:

- `UNCHECKED`
- `TEXT_EXTRACTED`
- `MANUAL_SAMPLE_REVIEWED`
- `BASELINE_COMPARED`
- `FAILED`

`CLEAN_TEXT` and “zero errors” are not accepted without a defined baseline comparison; a zero-error assertion is rejected when the measured error rate is non-zero.

Confidential or privileged PDF requests are blocked unless provider, retention, region and access approvals are all recorded.

## Files

- `gas/25_DecisionRouter.gs` — segmentation, family routing, nature tags and module plans
- `gas/35_DecisionIntelligenceContract.gs` — fourth-layer schema and prompt contract
- `gas/45_OutputGuard.gs` — provenance, boundary, OCR and audience QA
- `gas/55_GeminiDocumentAdapter.gs` — request builder only; no live API call
- `gas/95_V02Integration.gs` — integration plan preserving the original three branches
- `tests/*.test.mjs` — Node contract/regression tests
- `../../tests/test_tcct_decision_intelligence_v02.py` — repository CI wrapper
- `GEMINI_REVIEW.md` — re-check of the Gemini-augmented outputs
- `CASE_FAMILY_PLAYBOOK.md` — unfair conduct, agreement, dominance and merger depth
- `examples/public-unfair-shipping-decision-intelligence.md` — worked, non-confidential illustration
- `TEST_REPORT.md` — RED/GREEN and full-CI evidence

## Verified in CI

The candidate has 27 Node contract/regression tests invoked through the repository’s Python unittest suite. The latest hardened run also passed repository validation, build, check and deterministic rebuild.

See [`TEST_REPORT.md`](TEST_REPORT.md) for exact commits and run IDs.

## Not yet verified

- live Gemini request/response behavior and output quality;
- live Drive OCR and Google Docs rendering;
- model performance on a representative corpus of unfair-trade, agreement, dominance and merger decisions;
- legal correctness after human review;
- Thai Legal Assistant 2.0 import/writeback;
- Apps Script execution time, quota, retry and checkpoint behavior for long documents.

## Safety status

All output remains `AI_DRAFT_REVIEW_REQUIRED`. This branch does not deploy, create triggers, write to production Drive, call Gemini live, change Thai Legal Assistant 2.0 or merge itself.
