# Thai Regulatory Watch

Independent, automatically updated public regulatory RSS and JSON for review-only GRC intake.

**[Dashboard](https://attorneynoon.github.io/thai-regulatory-watch/)** · **[Tech Lawyer & Digital Platforms](https://attorneynoon.github.io/thai-regulatory-watch/practice/tech-lawyer-digital-platforms/)** · **[Changes RSS](https://attorneynoon.github.io/thai-regulatory-watch/feeds/changes.xml)** · **[All events RSS](https://attorneynoon.github.io/thai-regulatory-watch/feeds/all.xml)** · **[GRC events JSON](https://attorneynoon.github.io/thai-regulatory-watch/api/v1/events.json)** · **[Source health](https://attorneynoon.github.io/thai-regulatory-watch/feeds/health.xml)**

The inventory reconciles the existing enforcement, upstream GR/GA, legislative and cloud monitoring watch lists: **96 source scopes across 53 regulator, legislative and related public-institution groups**. It includes government agencies, statutory consumer advocacy, and self-regulatory sources with distinct authority classifications. **Inventory inclusion is not operational coverage.** Check the dashboard or `site/api/v1/sources.json` for each scope's enablement, validation and run status.

## Feeds

| Output | Contents |
|---|---|
| `feeds/all.xml` | Combined baseline and subsequent observation events |
| `feeds/changes.xml` | New items and revisions after source baseline |
| `feeds/<regulator>.xml` | Events for one regulator/institution |
| `feeds/<source-id>.xml` | Events for one monitored page/scope |
| `feeds/current/all.xml` | One current observation per canonical item, newest official dates first |
| `feeds/current/<regulator>.xml` | Deduplicated current items for one regulator |
| `feeds/topic-<topic>.xml` | Events for one topic across sources |
| `feeds/baseline.xml` | Initial inventories |
| `feeds/health.xml` | Failures and recoveries |
| `subscriptions.opml` | Regulator feeds for import into a reader |
| `api/v1/events.json` | Complete retained events and GRC metadata |
| `api/v1/items.json` | Current items, preserving source-specific observations |
| `api/v1/sources.json` | Source inventory, coverage and last-run health |

RSS keeps up to **500 entries per view**. JSON retains complete observation history. A publication may have several revision events in `all.xml`; `current/all.xml` and `current/<regulator>.xml` offer a deduplicated current-item view without deleting any history. Subscribe to a combined view **or** selected regulator/topic/source feeds to avoid duplicate reading.

Nine [practice-focus pages](docs/PRACTICE_FOCUS.md) combine relevant regulators for human reading. Each page publishes a current-items RSS and a post-baseline changes RSS. A regulator may appear in more than one practice; these are configurable reading scopes, not legal classifications.

Source-chronology feeds sort newest official publication first, then source modification; undated records follow dated ones and omit `pubDate`. Date-only values use midnight UTC solely as an RSS display convention, explicitly labelled `rss_date_precision=day`. **Changes and health feeds remain detection-ordered** so revisions to old documents are visible. Descriptions show source dates, observation dates, full publisher/section, available excerpts/document IDs, types, topics and limitations. See [feed reading and date semantics](docs/FEED_READING.md).

Initial existing publications are `BASELINE`, not new news. Legal effect remains `Not assessed`. Hash changes signal changed bytes; PDFs are not archived and a hash cannot reconstruct a previous document.

The first successful PDF fingerprint establishes its baseline, not a change alert. Latest document-check evidence is in `items.json`; immutable event records retain the evidence available when that event occurred. Listings may include general administrative news, and configuration-based topic tags do not determine relevance or legal authority.

## Automatic operation

GitHub Actions runs **hourly at minute 17** (also minute 17 Bangkok time) and supports **Actions → Regulatory Watch → Run workflow**. Collection preserves last-good records and commits state and generated outputs. A separate health job reports degraded sources; Pages can deploy diagnostics even when that health job is red. A red health job is not necessarily a failed collection or deployment—inspect the individual jobs.

Scheduling and reader polling are best effort. Public scheduled workflows can be disabled after inactivity. Check freshness externally from your existing monitoring lane; the dashboard flags runs older than three hours. No laptop, paid API or LLM API is needed for collection.

Enable Pages using **Settings → Pages → GitHub Actions** and repository Actions variables:

```text
ENABLE_PAGES=true
FEED_BASE_URL=https://attorneynoon.github.io/thai-regulatory-watch
```

Raw fallback: [all.xml](https://raw.githubusercontent.com/attorneynoon/thai-regulatory-watch/main/site/feeds/all.xml) and [changes.xml](https://raw.githubusercontent.com/attorneynoon/thai-regulatory-watch/main/site/feeds/changes.xml).

## Add another government URL

Open **Issues → New issue → Add a government source**, or ask a cloud coding task to update `config/sources.yml` using [the onboarding guide](docs/ADDING_SOURCES.md). HTML, RSS/Atom, selected-content pages and observed public JSON contracts use configuration and representative tests. Inert embedded JSON and narrow Next-data contracts are supported without executing page scripts. Requests remain pending until reviewed.

## Use from ChatGPT and Codex cloud

The public RSS/JSON links can be supplied to ChatGPT for retrieval and analysis, subject to the tools available in that chat. For code updates, connect this repository to [Codex cloud](https://chatgpt.com/codex), grant repository access, create an environment, and use the setup command below. Normal ChatGPT repository-reading access alone does not establish write capability. See [cloud operations](docs/CLOUD.md) and [GRC integration](docs/GRC_INTEGRATION.md).

## Development

```sh
python -m pip install --upgrade pip==26.2.1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m regwatch validate
python -m regwatch build
python -m regwatch check
python -m regwatch collect --source tcct-unfair
python -m regwatch health
python -m regwatch health --strict-coverage
```

`build` is offline. `collect` performs permitted public requests, writes public state and builds artifacts; `--allow-source-errors` allows last-good publication without hiding failed status. `health --strict-coverage` also fails on unverified/pending scopes. State and source IDs must be preserved. Source fixtures distinguish synthetic tests from representative official extracts.

### Interpreting a failed health job

`health` reads the tracked source registry and monitoring state without fetching websites or changing history. It is a source-health gate, not a test of the deployed Pages site. The workflow checks the exact commit persisted by its collection job; deployment continues to depend on collection independently of health.

| Source condition | Default `health` | `health --strict-coverage` |
|---|---|---|
| Enabled, verified, healthy with a valid success timestamp within three hours | Pass | Pass |
| Enabled, candidate, healthy with a valid success timestamp within three hours | Pass; still candidate | Fail: unverified coverage |
| Any enabled source failed, blocked, degraded, never run or stale | Fail, including candidates | Fail |
| Enabled source marked healthy but success time is missing, invalid, without a timezone or in the future | Fail: freshness cannot be verified | Fail |
| Disabled pending or otherwise unverified scope | Does not fail the runtime gate | Fail: unverified coverage |

The JSON output remains a list with `source`, `status` and `validation`. Additional fields identify the stored status, enabled flag, original `last_error`, last attempt/success, configured response budget and reasons for the result. `status: stale` or `invalid` is a read-time assessment; `stored_status` preserves what the collector recorded. Neither rewrites the source's health history. A candidate is not a lower-priority source: for example, blocked PDPC scopes remain fatal when enabled.

Use `site/api/v1/sources.json` for the published latest source snapshot. `site/api/v1/health.json` records health **transitions**, so a repeated failure need not add a new event. Last-good item counts after failure are retained observations, not a successful current collection or proof of no update.

For the NCSA response-budget investigation and a single-fetch, read-only verification command, see [the October 2026 investigation](reports/HEALTH_FAILURE_INVESTIGATION_2026-10-17.md). The proposed NCSA 64 MB limit remains finite; hosted recovery must be checked separately from offline tests.

See [verification](reports/VERIFICATION.md), [source coverage](docs/SOURCE_COVERAGE.md), and [work record](docs/WORK_LOG.md) for actual validation and remaining work.
