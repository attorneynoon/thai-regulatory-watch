# Re-check of Gemini-Augmented TCCT OCR Outputs

**Review date:** 2026-11-15  
**Scope:** newly generated, non-confidential Gemini-augmented outputs in the user’s TCCT OCR folder  
**Purpose:** identify what can be retained and what requires deterministic controls before any live migration

## Improvements confirmed

The revised outputs are materially more useful than a plain OCR/transcription workflow. The reviewed samples now include:

1. an OCR/redaction pre-flight section;
2. structured extraction of the ruling;
3. an academic/economic deep-dive;
4. a litigation and evidentiary war room;
5. actual-versus-ideal evidence discussion;
6. TCCT criticism and loopholes;
7. a business, executive and stakeholder translation layer;
8. practical precautions and a traffic-light matrix.

The shipping-choice sample also captured the central case-specific evidence: the later multi-carrier arrangement and change request, the approximately 600-metre drop-off fact, and the fact that the Commission did not need to determine dominance after the pleaded conduct was not established.

## Controls still required

### 1. OCR certainty was overstated

The sample labelled the extraction `CLEAN_TEXT`, asserted that Thai numerals were fully standardized and claimed zero corruption or displaced characters. Readable output is not proof of zero error. The v0.2 contract therefore permits only `TEXT_EXTRACTED`, `MANUAL_SAMPLE_REVIEWED` or `BASELINE_COMPARED` before a positive fidelity conclusion.

### 2. Case-specific facts and systemic theories were mixed

The ruling disposed of the individual allegations on their facts. The augmented output then moved to market-wide defaults, foreclosure, route density, platform self-preferencing and future enforcement. Those can be valuable hypotheses, but they must be labelled `UNTESTED`, `NOT_REACHED`, `ACADEMIC_LENS` or `NEEDS_RESEARCH`, not presented as holdings.

### 3. Generic market-definition and HHI gaps were overstated

Where the Commission expressly did not need to determine dominance, the absence of SSNIP/SSNDQ or HHI is not automatically a defect in resolving the pleaded complaint. It may be a limitation on systemic guidance, but the workflow must distinguish:

- evidence legally necessary to decide the matter;
- evidence useful for an alternative theory;
- evidence relevant only to an academic or policy critique.

### 4. Ideal evidence included an invented numeric target

The sample proposed proof that more than 80% of merchants faced opt-out friction. No source or methodological basis was supplied for that threshold. v0.2 allows a numeric target in ideal evidence only when `numericBasisRefs` are provided.

### 5. Academic depth lacked source governance

The schools-of-thought discussion is useful, but names and propositions from Chicago, post-Chicago, ordoliberal, Neo-Brandeisian, behavioral and transaction-cost traditions must link to governed sources. Without them, the output must state `NEEDS_RESEARCH`.

### 6. Penalty and director-exposure language needs current-law verification

Business summaries should not state fines, limitation periods, criminal exposure or director liability merely from model memory. Each penalty statement requires current statute references and a law-as-of date.

### 7. Merger compilations require case segmentation

The reviewed merger source contains both pre-approval decisions under Section 51 paragraph two and post-notification decisions under Section 51 paragraph one. Treating the whole compilation as one case can contaminate facts, theories and evidence across transactions. v0.2 assigns a separate locator and source boundary to each decision before analysis.

### 8. Different merger structures require different economics

A horizontal merger may support concentration, unilateral or coordinated-effects analysis. A vertical merger requires ability/incentive/effect and foreclosure analysis. Conglomerate, ecosystem, data or network-effect cases need yet another theory. HHI is therefore conditional, not a universal mandatory field.

## Changes mapped to v0.2

| Gemini-output issue | v0.2 control |
|---|---|
| `CLEAN_TEXT` / zero-error assertion | baseline-comparison status and contradiction guard |
| individual holding mixed with systemic theory | holding boundary and theory disposition |
| HHI applied generically | case-family and nature routing; conditional HHI module |
| dependency treated as universal UTP theory | case-specific unfairness benchmark; dependency optional |
| academic claims from memory | `SUPPLIED_SOURCE` or `NEEDS_RESEARCH` |
| invented percentages | `numericBasisRefs` requirement |
| cross-transaction merger contamination | decision segmentation and allowed-source boundary |
| external academic source treated as case record | separate `externalSourceRefs` namespace |
| broad business summary | eight required stakeholder roles and non-empty takeaways |
| confidential PDF sent after one generic approval | four-part provider/retention/region/access gate |

## Retention decision

Retain the revised Gemini analytical concepts and section coverage. Do not retain its certainty labels or generic legal/economic assumptions as authoritative defaults. The v0.2 router, schema and validators are the control layer between Gemini output and any future Google Docs or Thai Legal Assistant 2.0 record.

## Verification limit

This review examined generated outputs and built/tested request and validation contracts. It did not call Gemini live, compare OCR character-by-character against a complete PDF baseline or certify the legal conclusions.
