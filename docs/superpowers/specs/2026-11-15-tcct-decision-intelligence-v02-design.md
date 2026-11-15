# TCCT OCR Deep Analysis v0.2 — Decision Intelligence Design

## Intent

Extend the existing non-production TCCT OCR Deep Analysis prototype without rebuilding the Opal backup or replacing its three parallel analysis branches. The new design must turn a ruling into an auditable litigation, academic, economic and business decision record rather than merely adding longer prose.

## Findings from the Gemini-augmented outputs

The latest outputs already add three useful sections: an academic/economic deep-dive, a litigation and evidentiary war room, and a business/stakeholder translation. Those additions are directionally correct but need deterministic controls because the samples also show recurring risks:

- absolute OCR assertions such as `CLEAN_TEXT` and “zero corruption” without a source-to-extraction comparison;
- generic HHI, SSNIP or market-definition analysis applied even when the decision turns on Section 57 facts rather than market power;
- treating an enforcement mechanism as a universal legal element of a Section 54 agreement instead of one possible evidentiary indicator;
- model-created doctrine labels presented as if they were the TCCT’s own legal terminology;
- academic and comparative-law statements without governed external sources;
- inferred dissenting reasons from a majority vote;
- invented numeric targets for “ideal” evidence;
- penalties and director exposure stated without a current-law source and case-family mapping;
- merger compilations containing several decisions analyzed as one record, creating cross-case contamination risk.

## Goals

1. Preserve the original `litigation`, `competition`, and `platform` branches.
2. Add a serial fourth layer, `decision_intelligence`, after the three branch syntheses.
3. Segment multi-decision source bundles before analysis.
4. Route legal and economic modules according to the decision family, procedural posture and conduct/merger nature.
5. Separate source facts, party arguments, TCCT findings/holdings, analyst inference, academic lenses, external research, hypotheses and missing evidence.
6. Produce actual arguments/evidence, counterarguments, ideal evidence, record gaps, TCCT critique, loopholes, stronger claimant/regulator/respondent cases and outcome-changing counterfactuals.
7. Translate the dispute for boards, executives, operating teams, counterparties and capital providers without overstating what the ruling authorizes.
8. Keep all output at `AI_DRAFT_REVIEW_REQUIRED`; no live deployment or production writeback.

## Non-goals

- No production deployment, trigger, web app, Drive writeback, Gemini live call or Thai Legal Assistant import.
- No claim that OCR fidelity is proven merely because readable text was produced.
- No ungoverned web research or model-memory citation.
- No automatic legal approval or current-law certification.
- No replacement of the original three analysis branches.

## Architecture

### Stage 0 — Source preparation and decision segmentation

Retain the v0.1 source ledger, Thai-numeral analysis copy and stable source locators. Add bundle segmentation when a document contains repeated TCCT decision headings. Each segment receives its own locator and allowed-source boundary.

### Stage 1 — Decision-family and nature router

Classify each segment into one primary family, optional secondary families, nature tags and a procedural posture:

- `UNFAIR_TRADE`
- `HORIZONTAL_AGREEMENT`
- `VERTICAL_AGREEMENT`
- `ABUSE_OF_DOMINANCE`
- `MERGER_PRE_APPROVAL`
- `MERGER_POST_NOTIFICATION`
- `UNKNOWN`

`PLATFORM_HYBRID` is a secondary characteristic, not a substitute for the statutory family. Nature tags distinguish mechanisms such as forced participation, discrimination, termination, payment terms, self-preferencing, horizontal overlap, vertical foreclosure and conglomerate/ecosystem effects.

### Stage 2 — Existing parallel branches

Run the original three branches unchanged in sequence semantics:

1. `litigation`
2. `competition`
3. `platform`

The router supplies a required/optional/forbidden module plan to stop generic templates from forcing irrelevant tests.

### Stage 3 — New serial fourth layer: `decision_intelligence`

Consume the source segment plus all three branch outputs. Produce:

- holding boundary: what the decision actually holds and does not decide;
- adjudicative issue map;
- theory-of-harm matrix: alleged, accepted, rejected, untested or not reached;
- actual evidence used and its legal purpose;
- ideal evidence with element, custodian, authenticity method, why it matters and expected rebuttal;
- counterarguments, reply evidence and missing proof;
- stronger claimant/regulator and respondent/defense cases;
- counterfactual facts or evidence that could change the outcome;
- TCCT critique separated into source-grounded omission, alternative inference, academic/comparative critique and process-design critique;
- loopholes and repeatability risks;
- academic schools of thought with assumptions, fit and tension;
- role-specific business translation and operational controls.

### Stage 4 — Evidence and audience QA

Validate provenance, case-family modules, cross-case citations, academic-source status, numeric targets, penalty statements, OCR claims and audience coverage before rendering.

## Case-family depth

### Unfair trade / Section 57

Identify the case-specific unfairness benchmark, the challenged act or term, comparator treatment, objective business justification, proportionality, notice/cure, harm, causation and remedy. Relative dependency or bargaining imbalance is context when relevant, not a universal element. Market definition or HHI is forbidden unless the source, pleaded theory or a separately reached Section 50 issue makes it relevant.

### Horizontal agreement / Section 54

Focus on contact, agreement or concerted practice, object/effect where legally relevant, direct and circumstantial evidence, implementation, monitoring/enforcement as evidence, individual attribution, withdrawal, settlement and ne bis in idem. Do not make monitoring or enforcement a universal statutory element unless an authoritative source expressly does so.

### Vertical agreement / Section 55

Focus on the vertical relationship, restraint, legal category, foreclosure or efficiency theory, coverage, duration, alternatives, pass-through and less restrictive means.

### Abuse of dominance / Section 50

Focus on relevant market, market power, conduct, exploitative or exclusionary mechanism, foreclosure, causation, efficiencies, proportionality and remedy. Keep dominance and abuse as separate propositions.

### Merger pre-approval / Sections 51(2) and 52

Focus on control, jurisdiction and thresholds; horizontal, vertical and conglomerate/ecosystem overlaps; counterfactual; market structure and concentration evidence; unilateral and coordinated effects; vertical ability/incentive/effect; entry/expansion; buyer power; efficiencies; failing-firm claims; Section 52 balancing; conditions, remedies and monitoring. HHI and delta are conditional metrics where supported, not mandatory substitutes for effects analysis.

### Merger post-notification / Section 51(1)

Focus on control, threshold, timeliness, completeness, transaction perimeter and structural change. Do not manufacture a full Section 52 merits review where the published decision merely acknowledges a filing.

## Provenance classes

Every material proposition must be tagged as one of:

`SOURCE_FACT`, `PARTY_ARGUMENT`, `TCCT_FINDING`, `TCCT_HOLDING`, `ANALYST_INFERENCE`, `ACADEMIC_LENS`, `EXTERNAL_RESEARCH`, `HYPOTHESIS`, `MISSING_EVIDENCE`, or `NOT_APPLICABLE`.

Case-record references and governed external references occupy separate namespaces. Academic or comparative claims require governed external source references. Without them, the output must say `NEEDS_RESEARCH`, not present model memory as authority.

## Business translation

The fourth layer must provide:

- a 30-second plain-language story;
- what the lawyers and regulator are actually fighting about;
- why the outcome occurred;
- what the ruling does not authorize;
- role-specific takeaways for board, C-suite, product/operations, commercial/procurement, finance, legal/compliance, SMEs/counterparties and investors/lenders;
- green/yellow/red decision guidance;
- evidence and controls to preserve before a dispute;
- concrete “next Monday” decisions.

Every required stakeholder role must contain at least one meaningful takeaway.

## OCR and Gemini boundary

Support Gemini native PDF document input as an optional extraction/verification path while retaining the deterministic source ledger and Drive OCR fallback. The request builder must use the current Interactions API path, structured output and `store=false`. Confidential or privileged documents remain blocked until provider, retention, region and access approvals are recorded.

OCR status values are limited to `UNCHECKED`, `TEXT_EXTRACTED`, `MANUAL_SAMPLE_REVIEWED`, `BASELINE_COMPARED` and `FAILED`. `CLEAN_TEXT` is not a valid status without a defined comparison protocol and metrics. A zero-error assertion is invalid if the measured error rate is non-zero.

## Safety and release status

This is a review-only candidate. All generated legal analysis remains `AI_DRAFT_REVIEW_REQUIRED`. No merge, deployment or production integration is authorized by this design.
