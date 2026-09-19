# Adding a government portal or URL

1. Record the official listing URL, publisher, jurisdiction, intended scope and an example publication. Read robots/terms and use ordinary permitted access.
2. Add a stable source ID to `config/sources.yml`. Never rename an existing source to refresh it. IDs cannot collide with regulators or generated feed names.
3. Select `html`, `rss` or `page`. Page mode requires `content_selector`; listing mode should use selectors scoped to the actual publication cards. A homepage's menu links are not publications.
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
