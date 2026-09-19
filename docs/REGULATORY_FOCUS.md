# Regulatory focus and meaningful updates

The owner requested fewer institutional-publicity items and more substantive regulatory material. Collection remains entirely on GitHub; no local scheduled collector or local-state upload is authorized.

## Feed selection

- `feeds/changes.xml` now includes post-baseline events from explicitly curated regulatory sections only. Existing subscribers to this URL stop receiving routine agency publicity. No post-baseline event is invented when a newly collected archive contains old publications.
- `feeds/regulatory.xml` contains one current observation per canonical item from those sections, newest source publication first. This is the recommended combined inventory subscription and includes the initial baseline.
- `feeds/changes-all.xml` preserves the former unfiltered changes view.
- `feeds/all.xml`, `feeds/current/all.xml`, agency/section feeds and full JSON retain general news and the full history. No historic items/events are deleted.

Selection is declared by `feed_priority: regulatory` in the source registry. Unclassified sources default to `radar`; they are not asserted to be unimportant. The initial curated set includes PDPC order summaries, consultation opinions, laws and secondary announcements; TCCT orders, rulings, announcements and procedural/regulatory guidance; ETDA standards; OCS law-news discovery and wage-committee publications. Coverage is intentionally explicit, not a claim that every relevant article across all agencies has been classified.

PDPC general news and GPPC programme news remain in broad feeds. They include publicity, recruitment and award items. A regulatory source classification is a configured relevance preference, not legal analysis or automatic promotion to a GRC obligation. All records remain unreviewed and legal effect Not assessed.

The focused current view deduplicates only after choosing eligible source observations, so a later general-news observation cannot hide a regulatory observation of the same URL. Changes remain source-specific events; overlap across sources does not rewrite their provenance or GUIDs.

## PDPC coverage

Existing expert-panel collection follows the parent page to all four child panels under a five-page bound. Consultation opinions are separate. New explicit law, secondary-announcement and news archives retain three-page bounds and original displayed dates. Download/copy controls use `data-href`, not just ordinary anchors. Publication dates must not be confused with order dates or effective dates.

`PDPC runner qualification` is read-only, manually dispatchable, and runs on PRs that change its diagnostic files. It tests the eight exact public URLs with the same identified, robots/TLS-checked transport on standard GitHub Linux, Windows and macOS runners. It does not write production state, upload local snapshots, use proxies or bypass challenges. Successful workflow execution only means the diagnostic ran; its per-page status and record counts establish access.

Hosted recovery must be documented after ordinary collection and public RSS/JSON verification. Local accessibility alone is insufficient.

## GitHub-only access result

[Qualification run35446919600](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/35446919600) tested all eight exact owner-specified PDPC pages on19 September2026. All eight returned content HTTP403 on each of Linux, Windows and macOS:24 denials, zero recovered pages. The same identified transport and URL paths were used; this result does not establish the publisher's reason for denial. Workflow success means the read-only probe completed, not source access success.

The owner declined a local scheduled collector and requires collection entirely on GitHub. No local scrape results are imported into production. Main-PDPC remains blocked until a publisher-supported access arrangement or independently qualified permitted official endpoint becomes available to GitHub. Merely changing OS, marking sources healthy, or replaying old local snapshots is not a fix. The focused RSS channel descriptions name incomplete regulatory sources, and source-health remains separately visible.
