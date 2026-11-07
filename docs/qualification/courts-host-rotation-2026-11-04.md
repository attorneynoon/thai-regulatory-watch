# Courts listing host rotation — 2026-11-04

The scheduled production run [41806560563](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/41806560563) restored collection/deployment after the runner fix. `courts-watch` separately failed its empty-parse gate. No source-health gate is relaxed here.

## Current official evidence

The exact `courts-watch` API URL in `config/sources.yml` returned HTTP 200 on 2026-11-04 around 09:33 UTC, with six `.infocard` records in its `html` field. The official `https://www.coj.go.th/robots.txt` allowed this API for ThaiRegulatoryWatch. The existing selectors and date pattern still match; all six destinations were discarded because their hosts were absent from the exact allowlist.

Observed official listing destinations:

- https://lbrmc.coj.go.th:443/content/page/index/id/592930
- https://lbrmc.coj.go.th:443/content/page/index/id/592862
- https://cmic.coj.go.th:443/content/page/index/id/592861
- https://crmc.coj.go.th:443/content/page/index/id/592660
- https://pttc.coj.go.th:443/content/page/index/id/592605
- https://crimsb.coj.go.th:443/content/page/index/id/592527

All five destination hosts returned HTTP 200 robots files permitting the observed article URL. Chiang Mai and Chiang Rai article requests returned HTTP 200 and matched their listing titles. The other three destination hosts returned HTTP 503 for the checked article; no retry or bypass was attempted. This patch qualifies **listing metadata provenance**, not availability or contents of every destination article. The national official listing is the source of the records, and no article-body or attachment-fetch behavior is added.

## Minimal change and safety

Add only the five explicitly observed official court hostnames. Preserve the existing seven hosts, source ID, URL, selectors, metadata semantics, candidate status, limits, TLS/robots rules, and retained history. No suffix wildcard, automatic host admission, or access-denial fallback is introduced. Future unqualified destinations remain excluded and an empty accepted result remains failed.

`tests/fixtures/repairs/courts-20261104.json` is a representative extract of the public six-card response, with image and duplicate detail-link markup removed; titles, destination links and raw dates are retained. The original fixture remains unchanged. Regression tests reproduce zero accepted records before the config change and six afterward. A synthetic unqualified-host mutation still fails closed without altering retained observations/events.

## Verification limits

The execution environment could not resolve the source through production `Transport` with environment proxies disabled. Ordinary HTTPS research retrieved the public robots/API evidence; no production transport settings were changed. Local fixture/in-memory validation is not a GitHub live collection result. Production recovery for this source must be checked after an explicitly authorized application; this draft does not alter main or generated data.

AMLO and prosecutor failures are separate: AMLO added a hidden CSRF field and requires a separately qualified form/session contract; the prosecutor homepage, feed and robots routes returned HTTP 404. Neither is changed by this patch.
