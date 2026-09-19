# TCCT and legislative-source qualification — 2026-09-19

All checks used public HTTPS with robots checks and normal certificate validation. Source IDs and previous observations are retained. `config/sources.yml` is the runtime authority; `config/repairs/main.yml` preserves the intermediate handoff only. Minimal fixtures and exact fetched-body SHA-256 values are under `tests/fixtures/repairs/main-*`.

| Scope | Corrected contract and local result | Limits |
|---|---|---|
| `tcct-listing-01` | Homepage headline wrappers, full title and displayed date; 4 items | Homepage subset |
| `tcct-listing-02` | Empty legacy year URL replaced by official press archive; 137 PDF links | Overlaps original press scope; dates not inferred from issue years |
| `tcct-listing-04`, `tcct-listing-05` | Official activity-card index; 45 items each | Generic-news replacement is partial activity coverage; day/month without year remains raw/unknown |
| `tcct-listing-06` | Statistics titles and permalinks; 6 items | Reporting years in titles are not publication dates |
| `tcct-listing-07` | CKAN dataset headings, complete title attribute and available excerpt; 30 datasets | First catalogue page, not press news |
| `tcct-official-complaints-prosecution` | Correct official navigation destination and `readnews` links; 7 instruments | Procedures, not individual enforcement outcomes |
| `tcct-official-rules-guidelines` | Eight named official subject pages; 20 distinct linked instruments | Explicit eight-page bound; not all subordinate rules |
| `house-section-77-discovery` | Four AJAX category pages from official frontend; 39 distinct drafts | Consultation windows and vote counts excluded from publication dates/change signals |
| `parliament-repository-discovery` | Public DSpace discovery JSON; 20 latest accessions | Accession is not publication. Month/year issued values remain raw. Links point to real public metadata endpoints |
| `parliament-einitiative-discovery` | Inert `__NEXT_DATA__` JSON; 8 drafts | Reader route confirmed by public JS. Explicit Buddhist-calendar modified timestamps normalized; no publication date inferred or voting/personal fields collected |
| `council-of-state-discovery`, `ocs-council-of-state-law-search-discovery` | Official OCS lazy-loaded law-news block; 4 items each | Partial discovery only, not SearchLaw corpus. Missing public CA intermediate supplied and validated to existing roots; unsafe self-signed legacy krisdika host is not trusted |
| `cabinet-secretariat-discovery` | Robots HTTP403 | Permitted official feed/API or publisher-side access repair needed |
| `law-go-th-api`, `law-go-th-public-hearings` | Robots HTTP403 | No no-update conclusion possible |
| `royal-gazette-discovery` | Robots HTTP403 | Search-index visibility is not automatic collection access |
| `ocs-council-of-state-law-search-api`, `ocs-council-of-state-law-search-application` | Exact public search request derived from the app; two anonymous read-only requests returned application error `PSL_6013`, without result body | Both remain pending; HTTP200 alone is not success |

## OCS public query evidence

Public module `4.94ac84a101e451d44fec.js` calls `/ocs-api/public/doc/searchLaw`. Its query uses `pagination:{currentPage:1,pageSize:10}`, `query:{keyword:'',lawCategoryIds:[],timelineTypeIds:[],publishYearAds:[],indexCharCategories:[],lawTagIds:[],actingPersonIds:[]}`, and `orderResult:[{orderBy:'concatOrderDesc',orderDir:'desc'}]`, wrapped in the observed anonymous request header/body. Both an empty keyword and ordinary `กฎหมาย` query returned the same business error. No credentials, stored user session, authentication flow, denial retries, or guessed write operation were used. An enum mentioning `getNews` did not establish a callable public request contract and was not treated as one.

## Metadata and display follow-up

The owner requested newest-first feeds and more visible official metadata during remediation. TCCT sections now have distinct configured labels, full publisher name, source-scope document types/topics, and explicit issue numbers when present in published titles. A year in an issue number is not converted into an invented publication date. Source excerpts are short, plain-text extracts where actually available; no generated summary or legal classification is represented as source text. Existing observation events remain immutable.

## Robots parser correction

The standard-library parser converted literal `Disallow: /?` into `/`, incorrectly blocking all OCPB paths. The reproduced failure was corrected by using pinned Protego 0.6.2. Regression tests keep root-query URLs and `/download/` blocked while permitting unrelated paths; wildcard denials are now enforced as well. The project's existing fail-closed handling of unavailable/HTML robots, HTTP403, TLS failures, and challenges is unchanged. Excise root was rechecked and remains genuinely disallowed.

References: [RFC 9309 path matching](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.2.2), [Protego package](https://pypi.org/project/Protego/0.6.2/), [patched wildcard-matching advisory](https://github.com/scrapy/protego/security/advisories/GHSA-wjmf-p669-5m5p). The pinned release includes the upstream exponential-backtracking fix.
