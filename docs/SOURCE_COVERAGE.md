# Source coverage

## Reconciled inventory — 19 September 2026

The initial inventory contains **96 distinct source scopes across 53 institution groups**. It reconciles the owner's enforcement watch list (21 agencies), GR/GA upstream scopes (12), legislative source groups (8), initial feed requests and additional institutions explicitly named in cloud monitoring lanes. Overlapping exact URLs are consolidated with `origin_ids`; different pages remain distinct. The fixed-instrument practice reference list is not treated as a changing discovery listing.

Only public identities, URLs and broad source classifications were imported. Private task destinations, business priorities, source captures and adjudicated GRC records were not imported. This repository does not modify those other processes.

The authoritative configuration is [sources.yml](../config/sources.yml). The machine-readable [live inventory](https://attorneynoon.github.io/thai-regulatory-watch/api/v1/sources.json) contains every scope, URL (or explicit missing URL), status, limitation and provenance ID. The dashboard links separate RSS views, including empty feeds for pending scopes.

## Initial local run

Of 96 scopes, **32 candidates were enabled and 64 remained pending**. Across the bounded local qualification runs, the final snapshot had **7 healthy, 17 failed and 8 blocked enabled scopes**, with **475 retained items/events**. All initial content events were BASELINE; they are not newly issued regulations. All enabled sources remain candidate coverage, not completeness-verified coverage.

| Successful source scope | Retained initial items | Important limitation |
|---|---:|---|
| PDPC consultation opinions | 81 | Opinions, not open public hearings; representative attachment-box fixture |
| Revenue Department listing | 6 | Broad public-news documents, including administrative/non-regulatory material |
| TCCT announcements | 100 | Bounded current listing; may include administrative publications |
| TCCT merger rulings | 100 | Bounded current listing, not full historical coverage |
| TCCT orders | 26 | Includes internal/appointment orders; binding effect not assessed |
| TCCT unfair-trade rulings | 134 | Representative listing/date fixture; no nested-detail traversal |
| ThaiBMA hearing documents | 28 | Attachment titles can be generic; hearing context needs review |

The initial local failures include empty/undersized results from candidate selectors, ETDA robots response limits, SEC robots access denial and TISI TLS certificate validation failures. These are access/extraction limitations, not evidence of no regulatory movement. No bypass or disabled TLS validation is used. GitHub-hosted access can differ; the live health endpoint supersedes this historical snapshot.

## Pending and partial coverage

**First hosted-run amendment:** The GitHub run retained 575 initial items/events after collecting 100 TCCT press-release PDFs (`tcct-listing-03`). Hosted status was 7 healthy, 11 failed, 14 blocked and 64 pending. PDPC returned robots HTTP 403 from GitHub, preserving the 81 local observations without asserting continued access. The historical local counts above are not overwritten; use live sources JSON for current status.

- Known API endpoints are preserved as pending until payload, pagination and access policy have a tested adapter.
- Institutions named without a qualified discovery URL remain visible with a null URL, not an invented endpoint.
- BOT's listing returned no article links in plain HTML; OCPB's generic index returned navigation rather than publications. Those paths remain pending.
- One listing page is the default. `max_pages`, `max_items`, `listing_pages_checked`, `pagination_truncated` and `item_limit_reached` disclose bounds. A healthy fetch does not establish historical completeness.
- Direct PDF checks rotate under `asset_budget`; `attachment_backlog` and per-item asset timestamps disclose unchecked evidence. First hashes are baselines; only later differences are document-change events.
- No OCR, full document extraction, legal effective-date inference or automatic canonical GRC promotion is implemented.

## Next qualification queue

Maintainers should prioritize empty enabled selectors, known first-party API adapters, then pending institution URLs according to the owner's priorities. For each source, supply a representative fixture and compare recent items to the official listing. Use [Adding sources](ADDING_SOURCES.md); leave sources pending when permitted access or evidence is insufficient. Coverage expansion does not require changing the GRC consumer contract.
