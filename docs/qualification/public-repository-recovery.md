# Public repository comparison and bounded source recovery

## 2026-09-19 findings

Only public third-party repositories were considered for reuse. No third-party code or dependencies were copied in this change.

| Public project | License inspected | Useful method | Limitation |
| --- | --- | --- | --- |
| [devruji/ratchakitcha-scraper](https://github.com/devruji/ratchakitcha-scraper) | MIT | Playwright navigation of the official Gazette monthly-report UI, including the month selector and download button | Monthly reports, not a demonstrated working current-publication feed. Does not establish access from our GitHub runner. Browser flags and browser identity were not copied. |
| [open-law-data-thailand/thai-legal-watch](https://github.com/open-law-data-thailand/thai-legal-watch) | MIT | Feed generation and static faceted viewing over the public OpenLawData Gazette dataset | Secondary data, not an official-source scraper. Must have separate provenance and cannot count as recovered official coverage. |
| [DGA-Thailand/open-law-data](https://github.com/DGA-Thailand/open-law-data) | No code reused; license not established in this review | DGA's public project links Gazette OCR datasets on Hugging Face and a community showcase | Dataset discovery, not proof of complete or timely regulator updates. |
| [sarapab-th/thai-open-data-mcp](https://github.com/sarapab-th/thai-open-data-mcp) | README declares MIT | Dataset search, agency/resource metadata and canonical data.go.th references | README explicitly says its hosted endpoint is paused as of July2026. Not installed or treated as an operational fallback. |

The narrow RSSHub Gazette code search returned no matches. This is not an exhaustive survey. These projects offer discovery and feed-design references, but neither resolves the observed official content denials by itself.

## Official-source repairs

Successful malformed robots responses now retain all parseable rules under RFC 9309 section 2.3.1.5; the previous blanket HTML rejection produced false blockers. The bounded robots budget is 1 MB. Valid disallows, 429, network failures and server errors still stop collection. Explicit challenge markers remain blocked; Incapsula incident responses are now recognized even when HTTP status is 200. Merely embedding the Incapsula resource script is not treated as an incident challenge.

- GPPC: three actual homepage articles extracted locally, with source timestamps and excerpts. Its advertised `/feed/` returns HTML and was rejected as an RSS source.
- DSI: six homepage publication headlines extracted locally from `/th`, replacing the root splash page. Dates are unknown and coverage is not the full archive.
- ETDA knowledge: ten articles extracted locally from the observed `knowledge-sharing/articles.aspx` listing. Featured and ordinary cards preserve excerpts and raw abbreviated Thai dates; unknown normalized dates are not replaced with scrape time.

Representative fixtures omit tracking/session content. Existing source IDs and stored history remain unchanged. These are local qualification results, not verified GitHub-hosted recoveries.

## Remaining limitations observed in this retry

All 44 previously nonhealthy or pending scopes were probed locally. DIW and SEPO served Incapsula incident pages. DLT and TISI returned application shells; the OCS app was also a shell, while its API root returned 404. The law.go.th API GET returned an application error, not legal records. Cabinet, law.go.th frontend, MDES, MorProm, NBTC, Gazette and SEC remained denied; MOT returned 418. Excise remains explicitly disallowed. SSO had a connection abort. ETDA's old news route timed out. Some PDPC and institutional sources work locally but previously failed from GitHub, which remains a distinct unresolved deployment limitation.

No authentication, challenge circumvention, identity spoofing, disabled TLS verification or secondary-data substitution was introduced. A source-access failure does not establish that there are no updates.

## Hosted verification — run35439231530

[PR5](https://github.com/attorneynoon/thai-regulatory-watch/pull/5) passed CI and merged as ed27291. The [hosted run](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/35439231530) completed collection and Pages deployment successfully. The distinct source-health job remained red for genuine unresolved coverage.

Public HTTPS readback verified55 healthy,18 blocked,2 failed and21 pending scopes, across96 configured scopes. GPPC, DSI and ETDA knowledge are now healthy from GitHub, increasing healthy coverage from52 to55. Published state contains1,500 items and1,867 events; all1,472 pre-repair items and1,839 pre-repair events are retained. RSS/JSON schema checks, current-feed uniqueness and review-only invariants passed.

The18 blocked enabled scopes comprise13 content403 responses (DOPA, MOPH, NACC, Parliament, SEC and8 main-PDPC scopes) and5 robots/network failures (DLPW, DOE, Labour Court, Labour Relations and NHSO). ETDA's2 news sources now reach the content request but time out; changing their classification from blocked to failed is not recovery. The currently advertised `/th/newsevents/news-list.aspx` also timed out locally and was not substituted. Pending scopes retain the limitations recorded above and in the source registry.

Remaining work requires usable official endpoints, a qualified browser-rendered adapter for genuine application shells, or a separately approved execution arrangement where ordinary public access succeeds. Secondary datasets must remain separately attributed and cannot silently close these official-source gaps.
