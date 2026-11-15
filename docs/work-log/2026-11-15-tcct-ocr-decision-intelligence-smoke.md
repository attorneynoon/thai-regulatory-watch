# 2026-11-15 — TCCT OCR Decision Intelligence public smoke checkpoint

Owner approved one public-document smoke test for the review-only TCCT OCR Deep Analysis v0.2 candidate. The branch preserves `litigation`, `competition` and `platform` and adds a serial `decision_intelligence` layer covering holding boundaries, actual and ideal evidence, counterarguments, stronger cases for each side, TCCT criticism, academic-source status and business/stakeholder translation. It routes unfair trade, horizontal and vertical agreements, dominance, merger pre-approval and merger post-notification through different legal/economic modules.

The Gemini request contract uses `Api-Revision: 2026-05-20`, structured output and `store=false`. The hosted smoke harness builds a reproducible public-derived image-only Thai fixture and is designed for three parallel branch calls and one serial fourth-layer call. The source-to-output checks cover the multi-carrier arrangement, 20 June 2567, 3.3 kilometres, approximately 600 metres, dominance not reached, actual/ideal evidence, counterarguments, a litigation war room, TCCT critique, academic-source status and eight stakeholder audiences.

Validation run `43704309960` passed all 212 repository tests, registry validation, build, XML/JSON checks and deterministic rebuild. The Node subset has 35 tests.

Historical smoke run `43703105149` built a one-page 138,750-byte PDF with SHA-256 `9d2b6e8c19febd4e7d4100dca5e05e1411e926691e684b7b042b2deecbc5ac71` and uploaded the review report. The live Gemini stage did not execute because no key was configured. The report status was `BLOCKED_NO_API_KEY`, and the final workflow gate failed as intended.

Subsequent hardening requires an explicit document-sensitivity classification, a same-repository manual label trigger, environment `tcct-public-smoke`, and only a dedicated environment secret `GEMINI_API_KEY`. The repository administrator must add required reviewers to that environment before storing the key. Ordinary PR updates no longer trigger a live smoke or expose the secret.

No merge, deployment, production Drive write, production trigger, confidential-document transmission or Thai Legal Assistant 2.0 writeback occurred. A future live `PASS` remains review-only.
