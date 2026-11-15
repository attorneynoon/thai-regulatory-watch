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

Secondary nature tags distinguish forced participation or tying, discriminatory treatment, termination/refusal, payment terms, self-preferencing, price fixing, market allocation, RPM, exclusive dealing, horizontal overlap, vertical foreclosure, conglomerate/ecosystem effects, data/network effects and remedy design.

Dependency is not treated as a universal Section 57 element. HHI is a conditional metric when the record, market definition and merger structure support it, not a mandatory field for every merger.

See [`CASE_FAMILY_PLAYBOOK.md`](CASE_FAMILY_PLAYBOOK.md).

## Evidence and provenance controls

Record propositions use only the decision segment’s permitted source IDs. Academic/comparative sources use separate governed external IDs and are not treated as case-record citations.

Material propositions use one of:

`SOURCE_FACT`, `PARTY_ARGUMENT`, `TCCT_FINDING`, `TCCT_HOLDING`, `ANALYST_INFERENCE`, `ACADEMIC_LENS`, `EXTERNAL_RESEARCH`, `HYPOTHESIS`, `MISSING_EVIDENCE`, or `NOT_APPLICABLE`.

The validator rejects cross-case citations, missing provenance, empty stakeholder takeaways, unsupported numeric targets, inferred dissent reasons, uncited penalty statements, academic claims marked sourced without a governed external source, and case-family modules that should not apply.

## OCR and Gemini boundary

The candidate supports Gemini native-PDF processing as an optional path and retains Drive OCR as a fallback. The request contract uses Interactions API revision `2026-05-20`, structured JSON output and `store=false`.

Every PDF must be classified explicitly as `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, or `PRIVILEGED`. Missing or unsupported classifications are blocked. `INTERNAL`, `CONFIDENTIAL`, and `PRIVILEGED` require provider, retention, region and access approvals before request construction.

OCR status is limited to:

- `UNCHECKED`
- `TEXT_EXTRACTED`
- `MANUAL_SAMPLE_REVIEWED`
- `BASELINE_COMPARED`
- `FAILED`

`CLEAN_TEXT` and “zero errors” are not accepted without a defined comparison protocol; a zero-error assertion is rejected when the measured error rate is non-zero.

## Public-document smoke harness

The approved harness creates a one-page, image-only, public-derived TCCT fixture and is designed to run four Gemini calls:

1. litigation branch;
2. competition branch;
3. platform branch;
4. serial `decision_intelligence` synthesis.

The deterministic gate checks extraction of the multi-carrier arrangement, the 20 June 2567 carrier-change request, the pleaded 3.3-kilometre distance, the approximately 600-metre finding and the fact that dominance was not reached. It also requires actual evidence, ideal evidence, counterarguments, litigation-war-room depth, a fair TCCT critique, governed academic-source status and non-empty takeaways for eight stakeholder groups. It rejects absolute OCR claims, unsupported 80-percent targets and unsourced penalty statements.

The first hosted smoke built the scanned PDF but did **not** call Gemini because no API key was configured. Its status is deliberately `BLOCKED_NO_API_KEY`; the final gate failed rather than treating the blocker as a pass. See [`LIVE_SMOKE_REPORT.md`](LIVE_SMOKE_REPORT.md).

Future hosted live runs are not automatic. The workflow runs only after the same-repository PR receives label `run-public-gemini-smoke` or through manual dispatch, declares environment `tcct-public-smoke`, and consumes only the dedicated environment secret `GEMINI_API_KEY`. Repository administration must create that environment, add required reviewers and store the key there before a live run.

## Files

- `gas/25_DecisionRouter.gs` — segmentation, family routing, nature tags and module plans
- `gas/35_DecisionIntelligenceContract.gs` — fourth-layer schema and prompt contract
- `gas/45_OutputGuard.gs` — provenance, boundary, OCR and audience QA
- `gas/55_GeminiDocumentAdapter.gs` — request builder and sensitivity gate
- `gas/95_V02Integration.gs` — integration plan preserving the original branches
- `tests/*.test.mjs` — Node contract/regression tests
- `../../tests/test_tcct_decision_intelligence_v02.py` — repository CI and workflow-security tests
- `scripts/build-public-fixture.py` — bounded scanned-PDF fixture builder
- `scripts/public-smoke-lib.mjs` — response parsing and deterministic smoke checks
- `scripts/public-smoke.mjs` — review-only live smoke runner
- `GEMINI_REVIEW.md` — re-check of Gemini-augmented outputs
- `CASE_FAMILY_PLAYBOOK.md` — unfair conduct, agreement, dominance and merger depth
- `examples/public-unfair-shipping-decision-intelligence.md` — worked public illustration
- `TEST_REPORT.md` — RED/GREEN and full-CI evidence
- `LIVE_SMOKE_REPORT.md` — hosted smoke result and blocker

## Verified in CI

The Node contract/regression suite contains **35 tests**. Repository validation run `43704309960` passed all **212 Python-discovered tests**, registry validation, build, XML/JSON checks and deterministic rebuild.

## Not yet verified

- successful live Gemini authentication and response quality;
- live Drive OCR and Google Docs rendering;
- representative-corpus performance across unfair-trade, agreement, dominance and merger decisions;
- legal correctness after human review;
- Thai Legal Assistant 2.0 import/writeback;
- Apps Script quota, timeout, retry and checkpoint behavior for long documents.

## Safety status

All output remains `AI_DRAFT_REVIEW_REQUIRED`. This branch does not deploy, create production triggers, write to production Drive, change Thai Legal Assistant 2.0 or merge itself. The smoke workflow stores no API key, raw request body or base64 PDF in its report artifact.
