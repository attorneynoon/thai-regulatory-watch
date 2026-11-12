# TCCT redesigned website: staged API qualification (2026-11-12)

## Observed contract, not complete coverage

The official frontend JavaScript on `https://www.tcct.or.th/category/verdict`
uses the read-only listing endpoint `POST https://www.tcct.or.th/api/proxy/contents/now`.
Ordinary public requests without login returned HTTP 201, application/json and
`status: success` on 12 November 2026. This is a search/listing POST, not a content
creation request. Do not use adjacent CMS create/update/delete routes.

Exact request:
```json
{"category_key":"verdict","is_active":true,"page_number":1,"limit":12,"sort_by":"start_date","sort_direction":"desc"}
```

| Observed category | First-page rows | API total | API pages | Scope |
|---|---:|---:|---:|---|
| verdict | 12 | 137 | 12 | unfair-trade rulings |
| verdict-mergers | 12 | 169 | 15 | merger rulings |
| draft-principles-hearing | 3 | 3 | 1 | draft principle consultations |
| tcct-draft-laws-hearing | 12 | 20 | 2 | draft legal instruments consultations |
| giveaway-news-2569 | 12 | 20 | 2 | year-specific news |
| activity-news-2569 | 12 | 65 | 6 | year-specific activities |

These counts are the observed API's own inventory, not independently certified
archive totals. Only first pages were probed; only the 3-row principles category
reached its advertised terminal page. No blanket archive reconciliation claimed.
News/activity latest source dates were September in the sampled responses;
availability is not proof of freshness. Year-specific keys require reviewed
rollover, not silent automatic key invention.

`tests/fixtures/tcct-api/` contains sanitized representative first-page extracts:
public content UUID, code, title, start_date and publication flags, category key,
and pagination metadata only. Owner/CMS metadata, images and attachment metadata
are deliberately excluded. The original responses contain attachments marked
`isPublic: false`; the qualifier neither downloads nor emits those file URLs.
A file appearing in a response alone is not authorization to retrieve it.

## Safe qualification tool

```sh
python -m regwatch.tcct draft-principles-hearing --max-pages 1
python -m regwatch.tcct verdict --max-pages 10
```

Output goes only to stdout, not production state. This tool enforces the exact
six keys, at most 10 pages of 12 rows, schema/category/page checks, stable UUIDs,
no duplicate identities, unchanged totals across a run, explicit truncation,
response hashes, source dates and retrieval dates separately. Ten pages cannot
certify the 12/15-page ruling archives. There is no general-purpose JSON POST.
It preserves robots, TLS, host validation and limits and refuses POST redirects.
No status-only success promotion or fallback that bypasses blocks is allowed.

The parser was replayed against all six captured first pages. Live native
Transport verification in this cloud execution environment failed at DNS/robots
resolution (`Errno -3 Temporary failure in name resolution`), while ordinary
curl public probes succeeded. This environment result is not a TCCT origin
failure. A PR-only TCCT qualification job now tests the six first pages with native
Transport on Ubuntu 24.04, contents:read, no schedule or manual dispatch trigger,
and sanitized stdout only. Its result must be checked before claiming success.
No monitoring run, merge, deployment or production source enablement is performed.

## Migration hold and lineage

The production `config/sources.yml`, collector, state, generated site and schedules
are unchanged. The new qualifier is deliberately not connected to event generation.
Existing source IDs and retained observations must not be reset. Before enabling:

1. Verify official detail URLs and document accessibility through normal public
   navigation, not guessed UUID paths or private/unmarked file URLs.
2. Build reviewed old URL/content ID/new URL mapping using titles, actual documents
   and publication evidence. Ambiguity remains unresolved, never auto-merged.
3. Dry-run against copied state: no duplicate NEW events caused by URL migration,
   no loss of history; unchanged replay and A-B-A revision GUID tests must pass.
4. Confirm live pagination/content extraction and distinguish bounded-window health
   from complete archive coverage; review newly discovered historical publications.
5. Obtain the separately required production activation approval.

Legacy verdict and merger surfaces have plausible successors above. Legacy
hearing does not have proven one-to-one equivalence to both draft categories.
News/activity are not substitutes for legal instruments. Other legacy rules,
orders, announcements, fees, hearing-results and related routes remain separately
unmapped. Six keys do not restore all 22 historical routes, nor any PDPC routes.
Do not close recovery gaps or promote legal effect from this API availability.

## Reader workflow procedure

For existing active TCCT research readers: use the exact API for scoped discovery,
retain stable content IDs and source/publication/retrieval date distinctions,
page until the configured bound or verified terminal page, and record unresolved
pagination separately. Use ordinary public detail and primary instrument evidence
for substantive legal claims. Preserve legacy lineage, source-gap labels, duplicate
and attachment/version checks. Do not revive paused sources, change cadence, infer
legal effect, or treat an unavailable source as no change. API availability updates
source health only for categories actually tested at that retrieval time.
