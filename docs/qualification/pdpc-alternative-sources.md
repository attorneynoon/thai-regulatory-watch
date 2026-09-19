# PDPC alternative-source review — 2026-09-19

## Result

No public source reviewed here is an evidence-equivalent replacement for the PDPC adjudication summaries, consultation opinions, laws or secondary-announcement archives. A source-access failure is a coverage limitation, not evidence that the regulator made no update.

Two official PDPC-adjacent services are operational from GitHub and remain useful as separate Radar signals:

- `pdpc-official-gppc` — `https://gppc.pdpc.or.th/`; three current GPPC programme/publication cards in the latest hosted run.
- `pdpc-official-private-sector` — `https://register-gppc-plus.pdpc.or.th/`; one current private-sector registration-service observation in the latest hosted run.

They do not publish the expert-panel decisions, consultation attachments or law archive requested by the watchlist, so they are not promoted as substitutes and remain outside the regulatory-priority feed.

## Routes tested from GitHub

Rendered-source qualification runs `35448681570` and `35449189618` received HTTP 403 from the PDPC main pages, including the four expert-panel decision pages, consultations, law/announcement/news categories and the public-hearing page. The same hosted check received HTTP 403 from the site root/category RSS routes, WordPress posts/categories APIs, and the documented `lawcenter-service.pdpc.or.th` consultation and knowledge APIs. Chromium rendering did not change the denial because the top-level response itself was denied; there was no permitted page content to render.

This remains a host/access boundary, not a parser diagnosis and not a no-update conclusion. Retained historical observations remain published with their original provenance and health status.

## Other discovery checked

The internal `agent-reach` workflow confirmed that the Jina reader path is available, while its optional Exa route and GitHub CLI are not installed in this environment. Public GitHub code search for the exact PDPC decision-summary path, lawcenter service hostname and PDPC WordPress API path returned no reusable public implementation. Search-engine results were irrelevant and were rejected rather than promoted.

Cross-government services such as the Royal Gazette and `law.go.th` may independently publish laws or consultations, but they are complementary publication authorities with different scope and identifiers. They must be qualified under their own source IDs and provenance; they must not silently stand in for PDPC decisions or PDPC-site publication dates.

Separately, the same internal source-recovery process found official ETDA RSS links advertised in the rendered Thai and English press-page metadata. Direct qualification returned 909 Thai records (`SHA-256 B11148AA6723EB180ACFCE64910FAC4D169459A431969E4586E079A4C7B77BEC`) and 312 English records (`SHA-256 5854B58384FFAC7A272138722BD19CDA2EFD71D5BF37A7333A3563ADC32B6ADD`). Those feeds are source-equivalent ETDA alternatives and replace the browser selectors; their records are sorted by source publication time before collection limits are applied.

## Next qualification trigger

Re-test when PDPC exposes a documented public feed/API, permits GitHub-hosted access, or publishes the same records through an independently verifiable official portal. Preserve the ordinary robots, TLS, public-address, response-size and challenge checks; do not add proxy, stealth, CAPTCHA or access-control bypasses.
