# Thai Regulatory Watch — Design Specification

**Status:** Approved conversational design, written for owner review  
**Date:** 19 September 2026  
**Repository target:** public GitHub repository `attorneynoon/thai-regulatory-watch`  
**Operating boundary:** public-source monitoring and review-only GRC intake

## 1. Purpose

Thai Regulatory Watch is an independently operable monitor for public Thai government and regulator websites. It discovers new publications and revisions, retains last-good observations, and publishes automatically updated RSS and versioned JSON outputs. People can subscribe to the RSS feeds, while downstream GRC processes and automated tasks can consume the richer JSON contract.

The project is a public intake and change-detection layer. It does not decide legal effect, create canonical risk records, contact regulators, or contain confidential GRC analysis. Downstream GRC processes remain responsible for legal review, entity matching, risk promotion, control mapping, and any canonical write.

## 2. Goals

The first release will:

1. Run independently in a public GitHub repository using Python 3.12 and GitHub Actions.
2. Collect bounded public metadata from configured regulator pages and linked public documents.
3. Distinguish initial inventory, new publications, metadata changes, attachment changes, and source-health changes.
4. Generate one combined feed, a changes-only feed, regulator feeds, topic feeds, individual-source feeds, a baseline feed, and a separate health feed.
5. Publish equivalent versioned JSON suitable for automated GRC intake.
6. Retain provenance, timestamps, hashes, limitations, and last-good source state.
7. Make adding government URLs primarily a configuration-and-review workflow.
8. Support local Codex and Codex cloud maintenance through reproducible setup, repository instructions, tests, issues, branches, and pull requests.
9. Host outputs through GitHub Pages while retaining raw GitHub URLs as a fallback.

## 3. Non-goals

The first release will not:

- infer legal effective dates, deadlines, legal conclusions, parties, cases, obligations, risks, or controls;
- promote an observation into a canonical GRC record or knowledge graph;
- archive complete historical PDF contents;
- bypass robots rules, CAPTCHAs, access controls, rate limits, or technical challenges;
- use browser automation, OCR, or automatic public-API discovery;
- guarantee complete agency coverage or real-time delivery;
- treat hashes as proof of legal materiality or as a substitute for the changed document;
- treat a source-access failure as evidence that no update exists;
- store confidential GRC analysis, credentials, personal contact data, or internal priorities in the public repository.

## 4. System architecture

The system has six bounded components:

1. **Source registry** — declarative source definitions and lifecycle state.
2. **Collectors** — adapters for HTML listings, RSS/Atom feeds, selected page content, and linked public documents.
3. **Normalizer** — converts adapter results into one validated observation model.
4. **State and change engine** — compares observations with retained public state and emits deterministic events.
5. **Publisher** — builds RSS, JSON, OPML, health data, and a static dashboard from the same event/state model.
6. **Automation** — validates changes, performs scheduled collection, commits changed public artifacts, reports health, and optionally deploys GitHub Pages.

The data flow is:

```text
sources.yml -> bounded collection -> normalization -> state comparison
            -> event emission -> RSS/JSON/dashboard build -> Git commit/Pages
```

All output views come from the same retained state. Adding a feed never creates another scraping job.

## 5. Repository layout

```text
regwatch/                         Python package
  adapters/                       HTML, RSS/Atom, page, and document adapters
  models.py                       Normalized source, item, event, and health models
  registry.py                     Source configuration loading and validation
  engine.py                       State comparison and event emission
  feeds.py                        RSS and OPML generation
  api.py                          Versioned JSON generation
  dashboard.py                    Static dashboard generation
  cli.py                          validate, collect, build, and health commands
config/sources.yml                Extensible government-source registry
schemas/                          Versioned JSON Schemas
state/monitor.json                Retained public observation state
site/feeds/                       Generated RSS feeds
site/api/v1/                      Generated JSON outputs
site/index.html                   Static status and update dashboard
tests/                            Unit, contract, and integration tests
tests/fixtures/                   Synthetic and representative source fixtures
docs/                             Operations and source-onboarding guidance
reports/                          Verification and source-readiness reports
.github/workflows/                CI, monitor, and Pages workflows
.github/ISSUE_TEMPLATE/           Add-government-source issue form
AGENTS.md                         Repository rules for local and cloud agents
README.md                         Browser-first setup and operating guide
requirements.txt                 Pinned runtime dependencies
pyproject.toml                    Package and test configuration
```

## 6. Source registry and extensibility

`config/sources.yml` is the normal entry point for new government URLs. Each source has:

- stable `id`;
- `regulator_id` and display name;
- `jurisdiction`, initially `TH`;
- one or more topics;
- document type and authority class;
- source language;
- collection mode: `html`, `rss`, or `page`;
- official URL and explicit allowed hosts;
- an `enabled` flag controlling whether scheduled collection attempts the source;
- an independent validation status of `pending`, `candidate`, `verified`, or `disabled`;
- selectors, include/exclude patterns, pagination controls, and item limits where applicable;
- date and content extraction rules;
- linked-document checking budget;
- notes describing coverage limits and validation evidence.

The registry validator rejects duplicate or reserved identifiers, feed-name collisions, unsafe schemes, missing host allowlists, redirects outside allowed hosts, malformed selectors or patterns, and enabled sources without the required fixture and expectations. A candidate may use a synthetic behavior fixture when live markup is not yet available, but its limitation must be explicit. Only a successful live run and representative inspection can change validation status to `verified`.

Ordinary HTML, RSS/Atom, and selected-content sources are configuration-only. JavaScript-only portals, unusual APIs, detail-page traversal, or image-only announcements require a separately tested adapter. New adapters implement a narrow interface returning normalized candidate items; they do not write state or feeds directly.

The repository includes an **Add a government source** issue form requesting the official URL, regulator, topic, page type, expected example item, and known limitations. An issue is a review request, not activation. A source becomes enabled only through a reviewed pull request with configuration, a fixture, extraction assertions, and validation evidence. Enabling a `candidate` means the workflow will attempt it; it does not present the source as verified coverage.

## 7. Observation and event model

Every official publication has a stable `item_id`. Every observed baseline, new item, metadata revision, or attachment revision has a stable `event_id` derived from the source identity, item identity, event type, and version fingerprint.

The normalized event contract includes:

- schema version;
- `event_id`, `item_id`, `source_id`, and `regulator_id`;
- event type: `BASELINE`, `NEW`, `UPDATED`, or `UPDATED_ATTACHMENT`;
- title and source-supplied summary when available;
- jurisdiction, topics, document type, authority class, and language;
- official, canonical, listing, and document URLs as applicable;
- regulator publication time, first-observed time, event-observed time, and source-supplied modified time;
- legal effective time only when explicitly present and identified as such by the official source;
- selected-content and attachment SHA-256 fingerprints;
- source provenance and extraction method;
- extraction confidence and explicit limitations;
- review-only fields: `review_status: unreviewed`, `legal_effect: Not assessed`, and an optional non-canonical `signal_candidate` of Radar, Watch, Action, or null;
- source coverage and health context.

Unknown source fields remain null. Unsupported assessments remain `Not assessed`. Extraction confidence describes parsing confidence, not legal certainty.

## 8. Event semantics

- The first successful inventory for a newly enabled source emits `BASELINE` events.
- A newly discovered canonical item after baseline emits `NEW`.
- A change to retained listing metadata or explicitly selected page content emits `UPDATED`.
- A change to directly checked document bytes emits `UPDATED_ATTACHMENT`.
- A transition from content A to B and later back to A emits two separate revision events.
- A listing omission never deletes the retained item and never implies withdrawal, repeal, or supersession.
- Cross-source matching canonical URLs share the underlying item identity while preserving source-specific observations and provenance.
- Different titles alone do not merge different URLs.

## 9. RSS outputs

RSS is the human-subscription interface. Standard RSS elements provide broad reader compatibility; a `regwatch` XML namespace carries structured extension metadata. Readers that ignore the namespace still receive a useful title, link, GUID, description, categories, and observation `pubDate`.

Generated feeds include:

- `feeds/all.xml` — all observation events across enabled sources, including labelled baseline events;
- `feeds/changes.xml` — only `NEW`, `UPDATED`, and `UPDATED_ATTACHMENT` events after source baseline;
- `feeds/<regulator>.xml` — all events for one regulator;
- `feeds/topic-<topic>.xml` — all events for one topic;
- `feeds/<source-id>.xml` — all events for one configured source;
- `feeds/baseline.xml` — baseline events;
- `feeds/health.xml` — source failures, degradation, blocking, and recovery, separate from regulatory content.

RSS `pubDate` is the observation-event time so readers detect revisions. The regulator publication time is preserved separately in the namespace and may be unknown. Each event is visibly labelled by event type. The dashboard, rather than RSS layout, provides separate Recent changes and Current inventory sections.

Feed generation is bounded by a configurable maximum item count while complete retained public state remains available through JSON/state history. Feed entries use stable GUIDs and deterministic ordering so an unchanged build produces byte-identical output.

## 10. Versioned JSON outputs

JSON is the preferred automated GRC integration contract:

- `api/v1/events.json` — normalized observation events in reverse chronological order;
- `api/v1/items.json` — latest retained state for each official item;
- `api/v1/sources.json` — source definitions, validation state, and coverage limitations;
- `api/v1/health.json` — source operational status and health transitions.

The corresponding files under `schemas/` define required fields, enums, nullability, formats, and compatibility rules. Breaking changes require a new API version. Additive optional fields may be introduced within v1 when old consumers continue to validate.

GRC consumers pull these artifacts and map observations into their own review queue. This repository does not call private GRC endpoints in v1. A future outbound adapter may be added behind explicit configuration and secret handling, but it must remain disabled by default and preserve the same review-only contract.

## 11. State and change retention

`state/monitor.json` is the public, repository-retained state required for independent scheduled operation. It records source health, current items, source-specific observations, event history, document fingerprints, validators, check times, and document-check backlog without storing document bodies.

State loading is schema-versioned and fail-closed. Corrupt or unsupported state is rejected, not silently replaced. Collection writes new state and generated artifacts to temporary paths, validates them, and replaces production files only after the complete build succeeds.

Source listing failures preserve the previous successful inventory. Attachment failures preserve the previous fingerprint. A valid source with no new items produces no content event; an invalid or unavailable source produces or updates health status instead.

## 12. Collection safety and source health

Collectors enforce:

- HTTPS by default and explicit allowed hosts;
- robots policy checks without bypass;
- bounded redirects with allowlist validation at each hop;
- connection/read timeouts and bounded retries;
- response-size, pagination, item-count, and asset budgets;
- rate spacing and respected crawl delays within an operational ceiling;
- content-type and signature validation for linked documents;
- ETag and Last-Modified validators, plus periodic forced document downloads;
- rejection of challenge pages and HTML error responses masquerading as documents;
- suspicious empty-result and material-count-drop detection.

Source states include pending, not-run, healthy, degraded, blocked, and failed. A failure or access restriction is reported as a coverage limitation, never as proof of no update. Recovery emits a health event. Health events remain separate from regulatory publication feeds.

## 13. GitHub Actions workflows

### Pull-request validation

A read-only workflow runs on pull requests and pushes that modify code or configuration. It installs pinned dependencies under Python 3.12, runs all tests, validates the source registry and JSON Schemas, parses every generated XML file, checks deterministic builds, and verifies workflow files where tooling is available. It does not perform production collection, write state, deploy Pages, or receive write credentials.

### Scheduled and manual collection

The monitor workflow runs hourly at minute 17 and supports manual dispatch. A single non-cancelling concurrency group prevents overlapping writers. The workflow:

1. checks out the default branch;
2. installs pinned Python dependencies;
3. runs validation and offline tests;
4. performs bounded collection while retaining per-source failures;
5. rebuilds and validates state, RSS, JSON, OPML, and dashboard files;
6. commits and pushes only when tracked public artifacts changed;
7. runs the health gate after preservation so degraded-source diagnostics are not lost.

Only the collection job receives `contents: write`. Conflicts cause a safe failure and later retry; the workflow never force-pushes. Branch protection or repository policy may require an alternative reviewed state-update branch, which will be documented if enabled.

### GitHub Pages

A separate deployment job uploads only `site/` and deploys it to the `github-pages` environment when Pages is enabled. It receives `contents: read`, `pages: write`, and `id-token: write`. Raw GitHub URLs continue to provide usable feeds when Pages is disabled or temporarily unavailable.

## 14. Dashboard and subscriptions

The static dashboard displays:

- a prominent run state, including NOT RUN before the first successful collection;
- recent `NEW`, `UPDATED`, and `UPDATED_ATTACHMENT` events;
- current retained inventory;
- regulator, topic, and source coverage;
- pending, degraded, blocked, and failed sources;
- last attempted and last successful times;
- publication-date and legal-effect caveats;
- direct RSS, JSON, and OPML links.

Staleness is calculated in the browser from recorded timestamps. A previously green static page is not presented as current health merely because it still renders.

## 15. GRC integration boundary

The integration seam is pull-based and review-only. Downstream automations may consume `changes.xml` for simple alerts or `api/v1/events.json` for structured intake. Recommended matching keys are official/canonical URL, regulator, source, document identity, title, document type, topic, jurisdiction, publication time, and content fingerprints.

The project provides provenance and candidate classification but does not create risk owners, scores, obligations, controls, due dates, legal conclusions, or canonical graph relationships. Downstream GRC automation must retain its own review gates and distinguish source fact, extraction result, inference, and legal assessment.

## 16. Cloud maintenance

The repository is designed to be selected as a Codex cloud environment after the GitHub connection is granted access. It contains:

- pinned dependencies and a one-command validation path;
- `AGENTS.md` with public-data, review-only, source-safety, state-preservation, and verification rules;
- no dependency on local private paths;
- no required production secret for normal public collection;
- issue templates and documented source-addition steps;
- fixture-based tests that cloud tasks can run without live-network access.

Cloud changes are made on branches and reviewed as pull requests. Repository instructions do not authorize publication, secret changes, private GRC access, or canonical promotion. GitHub permissions remain the enforcement boundary for cloud writes and merges.

## 17. Initial source scope

The supplied reconnaissance identifies eight configurations suitable as **candidates for live validation**, not verified production coverage:

- TCCT unfair-trade rulings;
- TCCT merger rulings;
- TCCT numbered press releases;
- TCCT orders;
- TCCT announcements and draft announcements;
- ETDA public relations;
- ETDA standards and consultations;
- OCPB homepage-linked news and committee announcements.

Six scopes remain pending until exact official listings and extraction behavior are established:

- TCCT dedicated consultations;
- PDPC consultations;
- PDPC committee or expert orders;
- PDPC public relations;
- SEC news;
- NCSA regulator news or consultations.

The initial production state contains no synthetic regulatory observations. Candidate sources may be configured for first-run validation, but none is described as live-verified until an actual workflow run and representative inspection pass the acceptance gates.

## 18. Testing strategy

The suite uses synthetic and saved representative fixtures and covers:

- registry validation and feed-name collisions;
- safe URL, allowlist, robots, redirect, timeout, and content-size behavior;
- HTML, RSS/Atom, page, pagination, date, and linked-document extraction;
- Thai Buddhist Era dates, Thai digits, Western dates, and unknown dates;
- first-run baseline, new items, metadata changes, attachment changes, and reversions;
- cross-source URL identity and source-specific provenance;
- omission retention, suspicious empty results, and source failures/recoveries;
- ETag/Last-Modified caching and forced document checks;
- corrupt-state rejection and deterministic state transitions;
- RSS escaping, GUID stability, XML parsing, OPML parsing, and deterministic bytes;
- JSON Schema validation and GRC contract fixtures;
- dashboard links, labels, staleness, and NOT RUN state;
- workflow trigger, dependency, permission, and job-order expectations.

An integration scenario proves that an unchanged repeated collection emits no duplicate event, changed document bytes emit `UPDATED_ATTACHMENT`, and a later source failure retains all prior observations and feed output.

Live validation is separate from offline correctness. Each enabled source requires a successful robots/HTTP/parser run, representative extracted-item inspection, official URL and publication-date provenance review, exclusion review, known-current-item comparison, pagination/archive-bound assessment, and at least one expected document fingerprint when documents are collected.

## 19. GitHub setup and release gates

The intended remote is a public repository named `thai-regulatory-watch` under `attorneynoon`, with `main` as the default branch. Repository setup includes:

1. pushing the reviewed implementation and history;
2. enabling GitHub Actions with the workflow-declared permissions;
3. granting the OpenAI/Codex GitHub connection access to the repository;
4. creating a Codex cloud environment for the repository;
5. optionally enabling Pages with GitHub Actions as its publishing source;
6. running the validation workflow;
7. manually running the monitor workflow;
8. inspecting logs, source health, representative items, and generated artifacts;
9. reading back the raw and Pages feed URLs;
10. keeping existing regulatory monitoring active until live-source checks pass.

Repository creation and publication are external actions covered by the owner's build-and-GitHub request, but successful setup still depends on an authenticated GitHub session with repository-creation and app-installation permission.

## 20. Acceptance criteria

The project is ready for first live validation when:

- all offline tests pass under Python 3.12;
- registry validation succeeds;
- every generated RSS and OPML file parses;
- every generated JSON file validates against its declared schema;
- unchanged input produces byte-identical state-derived outputs;
- the initial state contains no synthetic regulator observations;
- the dashboard visibly says NOT RUN before collection;
- pull-request workflows are read-only;
- the collection workflow has only the required write scope and a single-writer concurrency guard;
- the Pages workflow deploys only `site/` with documented permissions;
- source failures preserve last-good observations and surface health events;
- GRC contract tests prove review-only values and no canonical promotion fields;
- the public repository can be opened in Codex cloud and its documented validation command succeeds there.

The deployment is operational only after a scheduled or manual workflow completes, representative source output is inspected, repository changes are committed, and the published feed is read back. Live source coverage is verified source by source; one successful workflow run does not establish completeness.

## 21. Future-compatible extensions

The design permits later additions without changing the core contracts:

- new government sources through registry entries;
- new narrow adapters behind the normalized collector interface;
- additional jurisdictions;
- monthly event archives if public history outgrows the primary JSON response;
- detail-page attachment discovery;
- optional downstream webhook delivery behind explicit secrets and review controls;
- signed releases or artifact attestations;
- external freshness monitoring independent of GitHub's scheduler.

Each extension must preserve stable identities, public/private separation, review-only GRC semantics, last-good retention, and versioned contracts.
