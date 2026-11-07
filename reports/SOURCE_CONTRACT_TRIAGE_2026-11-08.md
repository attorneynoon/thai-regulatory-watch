# AMLO / DIP source-contract triage — read-only preparatory patch

Date: 2026-11-08 (Asia/Bangkok). **Draft only. No production write, merge or deploy approved.**

## Findings grounded in the publisher and the hosted collector

**AMLO:** Official public intro: https://www.amlo.go.th/index.php/th/ . The official page still has a public input form. Hosted run https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/42391739725 (collect job 128460557492) reported \`amlo-listing-01 failed: Public navigation form fields changed\`. The existing exact-form guard in \`regwatch/publicform.py\` accepts only \`intro_page=1\` and rejects new hidden fields. The earlier official-site investigation in merged PR #17 notes a possible hidden CSRF control; its current live field name, value acquisition and cookie/session semantics are **not verified** in this preparatory patch.

**DIP:** Official news listing at https://www.ipthailand.go.th/th/dip-news.html shows 6 November 2569 entries and other recent news. Existing qualified source \`dip-listing-01\` uses the distinct public WordPress API at https://webnew.ipthailand.go.th/wp-json/wp/v2/news?per_page=20&orderby=date&order=desc&_fields=id,date,modified,link,title . Same hosted run reported \`Suspicious count drop greater than 50%; previous inventory retained\`. A separate publisher page, https://webnew.ipthailand.go.th/news-category/newsupdate/ , visibly presents some older September records. Their content differences DO NOT prove those listing formats are equivalent, or establish what returned from the configured API during a failed run. No replacement feed is qualified here.

## Changes

- Add \`scripts/probe_source_contracts.py\`: three bounded, GET-only checks through the existing production \`Transport\` robots/TLS/host/SSRF controls. It reports AMLO form field *names* without values, uses the existing in-memory DIP parser and count-drop comparison, and checks only metadata on the alternative DIP official news page. Raw responses, cookies, CSRF values and article contents are never stored.
- Add five synthetic/fixture tests in \`tests/test_source_contracts.py\` to detect accidental disclosure, unqualified feed promotion and disabled count-drop protection.
- Add a dedicated PR-only read-only workflow. A green diagnostic run means the probe ran successfully, **not** that AMLO/DIP collection has recovered.
- Do not modify \`config/sources.yml\`, any \`regwatch/\` production implementation, or any \`state/\`, \`site/\`, \`schemas/\` files.

## Required evidence before a follow-on remediation patch

1. AMLO: inspect the exact current public POST form action, methods, hidden names and session/cookie requirements using a permitted GET, without POSTing an unqualified form. Distinguish public navigation from authentication or challenge controls. Preserve exact-host and anti-bypass policy.
2. DIP: compare JSON API response and relevant official listing, identify item/date/URL/pagination semantics, and prove a safe baseline count against retained state. Do not suppress or lower the 50% count-drop guard.
3. Replay synthetic/source fixtures against candidate parsing rules; show no lost item IDs, observation events or health transitions and no promotion of candidate sources. Live hosted collector recovery remains a separate owner-approved validation.
4. A merge, production monitoring dispatch, site deployment or modification of production data requires explicit new approval.

## Hosted baseline and bounded 100-row diagnostic (2026-11-08)

Read-only [run 42400739385](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/42400739385) at 2026-11-07 18:20 UTC established: AMLO HTTP 200 with exact hidden names `intro_page` and `csrf_token`; no values logged or form submitted. Existing DIP API HTTP 200, 20 raw JSON rows and **3 accepted rows**, versus retained previous count **13**; the strict >50% count-drop guard correctly triggers. A separate publisher HTML GET returned only 212 bytes; no usable listing markup was qualified from GitHub. These results are observations, not source recovery.

This draft adds one additional read-only GET to the *same configured DIP WordPress endpoint*, changing only `per_page=20` to `per_page=100` in memory for qualification. No production URL or source rule is changed. The bounded probe must establish accepted rows, dates/identities and counts before any proposed config modification; no source status is promoted.

## Draft DIP same-endpoint remediation following hosted qualification

Read-only [run 42401033355](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/42401033355), 2026-11-07 18:23 UTC: original configured 20-row official WordPress API returned HTTP 200, 26,273 bytes, 20 raw / **3 accepted** / 3 unique URLs against retained prior count 13. The same exact official API and host with only `per_page=100` returned HTTP 200, 115,987 bytes, **100 raw / 78 accepted / 78 unique URLs**, SHA-256 `6b1f57b639cf4f580738970bc3b8ddc133c2c08c31b5ef47073a491a6282c1d8`. This is strong evidence that the 20-row pre-filter window was too narrow, not an upstream transport failure. No production state was written, no title/category rule weakened and no historical events were changed in the probe.

A narrowly scoped **draft** config patch now increases only `dip-listing-01` `per_page` to 100 (the already configured max_items remains 100); no host, source ID, validation label, title exclusion, publication parser, history safeguard or count-drop rule is changed. The script continues read-only comparison of the historic 20-row and candidate 100-row responses. Acceptance before merge requires dates/URLs in live log, exact CI validation, preserved 287 state/site/schema blobs and explicit owner approval. This is not a claim of complete DIP archive or parity with the distinct public news website.
