# 2026-11-15 — TCCT OCR Decision Intelligence public smoke checkpoint

Owner approved one public-document smoke test for the review-only TCCT OCR Deep Analysis v0.2 candidate. The branch preserves `litigation`, `competition` and `platform` and adds a serial `decision_intelligence` layer covering holding boundaries, actual and ideal evidence, counterarguments, stronger cases for each side, TCCT criticism, academic-source status and business/stakeholder translation. It routes unfair trade, horizontal and vertical agreements, dominance, merger pre-approval and merger post-notification through different legal/economic modules.

The Gemini request contract uses `Api-Revision: 2026-05-20`, structured output and `store=false`. The hosted smoke harness builds a reproducible public-derived image-only Thai fixture and is designed for three parallel branch calls and one serial fourth-layer call. The source-to-output checks cover the multi-carrier arrangement, 20 June 2567, 3.3 kilometres, approximately 600 metres, dominance not reached, actual/ideal evidence, counterarguments, a litigation war room, TCCT critique, academic-source status and eight stakeholder audiences.

Historical smoke run `43703105149` built a one-page 138,750-byte PDF with SHA-256 `9d2b6e8c19febd4e7d4100dca5e05e1411e926691e684b7b042b2deecbc5ac71` and uploaded the review report. The live Gemini stage did not execute because no key was configured. The report status was `BLOCKED_NO_API_KEY`, and the final workflow gate failed as intended.

Subsequent hardening requires an explicit document-sensitivity classification, a same-repository manual label trigger, environment `tcct-public-smoke`, and only a dedicated environment secret `GEMINI_API_KEY`. The repository administrator must add required reviewers to that environment before storing the key. Ordinary PR updates no longer trigger a live smoke or expose the secret.

## Owner approval and merge gate

On 15 November 2026, the owner approved completing the GitHub process and merging PR #22 into `main` after a fresh green validation against the then-current base branch. The approved integration covers the review-only prototype, deterministic controls, tests, documentation and manually gated public-smoke harness.

Final review added two further fail-closed controls before merge:

- litigation-war-room argument and stronger-case records must contain auditable fields rather than merely a non-empty object; and
- runtime receipts record the number of API calls actually attempted, so a key present during a pre-call failure cannot be misreported as a live request.

The RED run `43709642242` failed on those exact missing contracts. The GREEN run `43709953399` then passed 212 repository tests, including 40 Node decision-intelligence tests, registry validation, build, XML/JSON checks and deterministic rebuild against the current synthetic merge.

This approval and green merge gate do not convert `BLOCKED_NO_API_KEY` into a successful live Gemini test and do not authorize deployment, production Drive writes, confidential-document processing, Thai Legal Assistant 2.0 writeback or automatic production activation. The live public smoke remains a separate post-merge review gate once environment `tcct-public-smoke` and its dedicated `GEMINI_API_KEY` are configured.
