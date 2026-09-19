# Reading the feeds

The all-events, regulator, topic, individual-source and baseline feeds are ordered
newest official publication first. When publication is unavailable, a source
modification date is used. Undated records follow dated records, newest observation
first; event ID breaks ties deterministically. The current-inventory dashboard
uses the same order. These views retain events, including revisions; they are not
a newly adjudicated legal database.

The changes and source-health feeds, and Recent changes on the dashboard, instead
use detection order. This makes a newly detected revision to an old document
visible at the top. Baseline discovery is excluded from the changes feed.

## Dates are distinct

- Source publication: normalized date and the original date text, when available.
- Source modification: only what was extracted from the source, when available.
- Detected / observed: when this monitor recorded the observation, not when the
  publisher issued the document.

RSS `pubDate` follows publication, then modification, in source-chronology views.
If neither is available it is omitted. A source date without a time is represented
at midnight UTC solely for RSS compatibility: this is **not** an inferred source
publication time or timezone. `regwatch:rss_date_basis` identifies `published_at`,
`modified_at`, `observed_at`, or `unknown`; `regwatch:rss_date_precision` is `day`,
`timestamp`, or `unknown`. Changes and health use the observed timestamp and label
it as detection time. Unzoned timestamps are not assigned an invented timezone.
Some readers impose their own ordering or substitute an import time for undated
items; the emitted XML and its extensions preserve the distinction.

## Metadata and sections

Descriptions show the full extracted headline, recorded publisher, current
configured publisher/section, source ID, configured document type and topics,
dates, document ID, available summary, original/listing/document links, change
fields, review status and limitations. Source text is escaped, not rendered as
source-provided HTML; only HTTP(S) source links become active.

Document type, topics and section labels are configuration-based classifications,
not a legal interpretation of each article. A changed configuration may improve
the current section label without rewriting the publisher or classification
stored in a historical event. Missing source metadata is displayed as unavailable;
it is not filled with guesses. All legal effects remain `Not assessed` and review
status remains `unreviewed`.

The dashboard groups individual source-section subscriptions under each regulator.
For example, TCCT's combined feed still contains all its sections; choose the
separate configured section feeds to avoid mixing news, laws and other surfaces.
These are existing source feeds, not duplicated collection streams.

`feeds/current/all.xml` and `feeds/current/<regulator>.xml` offer a current-item
view: one representative current observation per canonical item, including only
that regulator's observations in a regulator feed. A source-dated observation is
preferred over an undated one, then the most recently seen observation (with
deterministic event-time and ID ties). Its existing event GUID is retained; a
different representative can therefore have a different GUID. The dashboard uses
the same selection. The observation-event feeds still retain overlapping source
observations and historical revisions; no records are deleted or merged in state.

RSS normally contains at most 500 events per view, selected after sorting. Undated
or older events may fall outside that window. JSON retains the complete stored
history and original metadata. Rendering does not change event IDs, GUIDs, hashes
or immutable event records. Source failures remain coverage limitations, never
proof that there were no updates.

Parser improvements can enrich a previously observed record (for example adding
an explicit document number or correctly parsing a date). Such changes may emit
an `UPDATED` observation with `changed_fields`; this does not itself prove that
the publisher revised the underlying legal document. Consult those fields and
source evidence before treating an observation as a substantive regulatory change.
