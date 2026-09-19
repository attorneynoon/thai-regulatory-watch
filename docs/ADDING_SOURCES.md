# Adding a government portal or URL

1. Record the official listing URL, publisher, jurisdiction, intended scope and an example publication. Read robots/terms and use ordinary permitted access.
2. Add a stable source ID to `config/sources.yml`. Never rename an existing source to refresh it. IDs cannot collide with regulators or generated feed names.
3. Select the verified adapter contract: `html`, `rss`, `page`, `json`, `json-html`, `json-script`, `next-data` or `json-page`. Page mode requires `content_selector`; listing mode should use selectors scoped to actual publication cards. A homepage's menu links are not publications. JSON modes require exact observed field paths; `json-page` is explicitly partial aggregate monitoring, not individual-publication extraction.
4. Declare every allowed hostname explicitly, including document hosts and permitted redirect destinations. There is no suffix wildcard.
5. Add a synthetic fixture for engine behavior and a small representative official extract for the actual selector. Record source URL, retrieval date and the expected title/date/document URL. Never place credentials or session data in fixtures.
6. Run tests, registry validation and an offline build. Then run `python -m regwatch collect --source YOUR_ID` and inspect the extracted items against the official listing, dates, exclusions, pagination bounds and document fingerprint.
7. Keep `validation_status: candidate` until that review passes; then document what was verified and the coverage limits. Use a PR for source changes.

Example (reserved example host, not an operational source):

```yaml
- id: example-orders
  regulator_id: example
  title: Example government authority
  url: https://example.org/orders
  allowed_hosts: [example.org]
  jurisdiction: TH
  topics: [orders]
  language: th
  authority_class: official-publication
  document_type: order
  enabled: true
  validation_status: candidate
  mode: html
  link_selector: article a[href]
  item_selector: article
  date_selector: time
  include_url: '\.pdf(?:\?|$)'
  max_pages: 1
  max_items: 100
  min_items: 1
  asset_budget: 2
  fixture: tests/fixtures/listing.html
  limitations: [Candidate source awaiting representative live inspection]
```

New feeds and JSON records are generated automatically from the registry. An API endpoint must not be enabled as HTML. Add a narrow adapter and tests for its exact response/pagination contract; do not guess fields or bypass challenges.

Do not equate `healthy` transport/parser status with verified completeness. Sources remain pending when the endpoint, access or extraction contract is unresolved. Removing a publication from a live list does not remove retained history.

## Metadata and bounds

Use `publisher_name` for the full institution name and `title` for the distinct configured section. Set source-scope `document_type` and `topics` conservatively; these are not item-level legal conclusions. For HTML, `title_attribute`, `title_selector`, `summary_selector` and `date_selector` may recover full visible metadata. Use `date_pattern` to exclude view counters and other volatile text; `document_id_pattern` must capture an explicitly published identifier, never an inferred date. RSS excerpts are reduced to plain text and capped at600 characters.

JSON uses `json_rows`, `json_fields`, optional equality `json_filter`, array-membership `json_contains`, and explicit `url_template` or URL field. JSON Pointer paths support keys containing dots. `json_sort` can order a public export before the item cap. Do not include CMS user IDs, unpublished rows or private fields. Embedded `json-script` requires an inert `application/json` script; `next-data` only decodes the tested public serialization grammar, never executes JavaScript. `date_calendar: buddhist` is source-specific evidence, not a global guess.

Multiple observed discovery endpoints use `start_urls` and bounded `max_pages`. Set `max_response_bytes` only when the real public response requires it (maximum64MB); item/page/PDF budgets still apply. `item_base_url` is useful for relative links in AJAX fragments. A bounded source is not an exhaustive archive.

The AMLO `public_form` contract is deliberately restricted to its observed public intro form; it is not a general login/form-submission mechanism. `tls_intermediates` can supply a documented missing public CA intermediate for an exact host, but standard roots, full chain validation and hostname checks remain active. Never add a self-signed root or disable TLS verification. Current public certificate provenance is in [family qualification](qualification/blocked-families.md).
