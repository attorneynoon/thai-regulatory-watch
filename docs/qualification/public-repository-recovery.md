# Public repository comparison and bounded source recovery

## 2026-09-19 findings

Only public third-party repositories were considered for reuse. No third-party code or dependencies were copied in this change.

| Public project | License inspected | Useful method | Limitation |
| --- | --- | --- | --- |
| [devruji/ratchakitcha-scraper](https://github.com/devruji/ratchakitcha-scraper) | MIT | Playwright navigation of the official Gazette monthly-report UI, including the month selector and download button | Monthly reports, not a demonstrated working current-publication feed. Does not establish access from our GitHub runner. Browser flags and browser identity were not copied. |
| [open-law-data-thailand/thai-legal-watch](https://github.com/open-law-data-thailand/thai-legal-watch) | MIT | Feed generation and static faceted viewing over the public OpenLawData Gazette dataset | Secondary data, not an official-source scraper. Must have separate provenance and cannot count as recovered official coverage. |

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
