# TCCT Decision Intelligence v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested, case-routed fourth analysis layer to the existing TCCT OCR Deep Analysis prototype while preserving source provenance and the three original branches.

**Architecture:** Pure Apps Script-compatible JavaScript modules implement decision segmentation, case-family routing, the fourth-layer schema/prompt, output guards and a current Gemini PDF request builder. Node’s built-in test runner executes the same `.gs` source through a VM; the repository’s Python unittest suite invokes those tests in CI.

**Tech Stack:** Google Apps Script V8-compatible JavaScript, Node.js built-in `node:test`, Python 3.12 unittest wrapper, Gemini Interactions API request contract.

**Spec:** `docs/superpowers/specs/2026-11-15-tcct-decision-intelligence-v02-design.md`

## Global Constraints

- Preserve `litigation`, `competition`, and `platform` as the first three analytical branches.
- Add `decision_intelligence` only after those branches complete.
- No production deployment, trigger, web app, Drive writeback or live Gemini call.
- No confidential or privileged fixture data.
- Every substantive proposition carries a provenance class and source boundary.
- Academic/comparative claims without governed sources are `NEEDS_RESEARCH`.
- Merger bundles must be segmented before analysis.
- All outputs remain `AI_DRAFT_REVIEW_REQUIRED`.

## Review Focus

1. Hybrid Section 50/57 platform rulings must route primarily to the issue actually decided without suppressing the secondary theory.
2. Section 54 monitoring/enforcement evidence must not become a universal statutory element.
3. Pre-approval and post-notification merger decisions must not share the same mandatory modules.
4. A citation from one decision segment must not validate a proposition in another segment.
5. Readable OCR output must not be labelled error-free without baseline comparison metrics.

---

### Task 1: Decision segmentation and routing

**Files:**
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/gas/25_DecisionRouter.gs`
- Test: `prototypes/tcct-ocr-deep-analysis-v0.2/tests/router.test.mjs`

**Interfaces:**
- Produces: `tcctV02ClassifyDecision(text)`, `tcctV02GetAnalysisPlan(classification)`, `tcctV02SplitDecisionBundle(text, documentId)`.

- [ ] Write routing and segmentation tests for Section 57, Section 54, merger pre-approval, merger post-notification and multi-decision bundles.
- [ ] Run the tests and confirm they fail because the module is absent.
- [ ] Implement the minimum deterministic router and module plans.
- [ ] Run the focused tests and then the full suite.

### Task 2: Fourth-layer schema and prompt contract

**Files:**
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/gas/35_DecisionIntelligenceContract.gs`
- Test: `prototypes/tcct-ocr-deep-analysis-v0.2/tests/contract.test.mjs`

**Interfaces:**
- Consumes: router classification and module plan.
- Produces: `tcctV02GetDecisionIntelligenceSchema()`, `tcctV02BuildDecisionIntelligencePrompt(context)` and `tcctV02BuildFourthLayerRequest(context)`.

- [ ] Write failing tests for theory-of-harm, actual/ideal evidence, counterarguments, critique, academic and business sections.
- [ ] Implement the structured-output schema and case-specific prompt guards.
- [ ] Verify the schema requires provenance and role-specific business translation.

### Task 3: Evidence, reasoning and OCR guards

**Files:**
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/gas/45_OutputGuard.gs`
- Test: `prototypes/tcct-ocr-deep-analysis-v0.2/tests/guard.test.mjs`

**Interfaces:**
- Produces: `tcctV02ValidateDecisionIntelligence(output, context)`, `tcctV02ValidateOcrAssessment(assessment)`, `tcctV02SanitizeMarkdown(text)` and cross-case validation.

- [ ] Write failing tests for inferred dissent, unsupported academic claims, invented percentages, uncited penalty statements, irrelevant modules, cross-case citations and absolute OCR claims.
- [ ] Implement fail-closed validation and clean private-use rendering glyphs.
- [ ] Run focused and full tests.

### Task 4: Gemini native-PDF request contract

**Files:**
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/gas/55_GeminiDocumentAdapter.gs`
- Test: `prototypes/tcct-ocr-deep-analysis-v0.2/tests/ocr.test.mjs`

**Interfaces:**
- Produces: `tcctV02BuildGeminiPdfInteraction(config)`, `tcctV02ChoosePdfProcessingPath(config)` and `tcctV02BuildOcrAssessment(input)`.

- [ ] Write failing tests for `/v1beta/interactions`, `store=false`, inline and file-URI PDF inputs, structured output and sensitive-document blocking.
- [ ] Implement request builders only; do not call the live API.
- [ ] Verify no key or model name is hard-coded.

### Task 5: Workflow integration contract

**Files:**
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/gas/95_V02Integration.gs`
- Test: `prototypes/tcct-ocr-deep-analysis-v0.2/tests/integration.test.mjs`

**Interfaces:**
- Produces: `tcctV02WorkflowStages()` and `tcctV02PlanFourthLayerForBundle(input)`.

- [ ] Write failing tests proving the original three branches stay ordered and the fourth layer runs serially per decision segment.
- [ ] Implement the integration planner without Workspace writes.
- [ ] Verify each segment receives its own allowed-source boundary.

### Task 6: CI, documentation and review package

**Files:**
- Create: `tests/test_tcct_decision_intelligence_v02.py`
- Create: `prototypes/tcct-ocr-deep-analysis-v0.2/README.md`
- Modify: `docs/WORK_LOG.md`

- [ ] Add a Python unittest wrapper that runs the Node contract suite.
- [ ] Record the RED run before implementation.
- [ ] Run repository CI after implementation and record exact results.
- [ ] Document verified capabilities, untested live integrations and the no-deploy boundary.
- [ ] Keep the pull request draft; do not merge without owner approval.