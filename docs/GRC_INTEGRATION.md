# Review-only GRC integration contract

Fetch `api/v1/events.json` and `api/v1/sources.json` from the hosted site or raw GitHub. Validate the schema and deduplicate by **event_id**, retaining a consumer-owned set/checkpoint. Use `item_id` to group revisions of the same canonical URL, `source_id` for publisher-specific observations and `previous_event_id` for revision chains. Timestamp-only checkpoints can miss equal-time events; always deduplicate by identity. On recovery, replay the complete retained JSON history safely using the same IDs.

Prefer `changes.xml` for alerts and JSON for machine ingestion. RSS extensions expose the metadata but some readers strip unfamiliar namespaces. The full JSON contract is published alongside each endpoint as `*.schema.json`.

| GRC need | Source fields |
|---|---|
| Observation identity | event_id, observation_id, item_id, revision, previous_event_id |
| Publisher and scope | source_id, regulator_id, publisher, jurisdiction, topics, document_type, authority_class |
| Evidence retrieval | official_url, canonical_url, listing_url, document_url, observed_at, source_response_sha256 |
| Change evidence | event_type, changed_fields, content_sha256, attachment_sha256 |
| Dates | published_at, publication_date_raw, modified_at, first_observed_at, observed_at |
| Extraction provenance | extraction_method, pinpoint, extraction_confidence, limitations |
| Candidate handling | review_status=unreviewed, legal_effect=Not assessed, signal_candidate=Radar |
| Coverage | coverage_status plus current source status/last_success_at in sources.json |

`authority_class`, topics and document type initially describe configured source scope. `classification_basis` makes that explicit. A regulator news page does not make every publication binding authority. `content_sha256` fingerprints normalized metadata; `source_response_sha256` fingerprints the fetched listing; `attachment_sha256` fingerprints checked PDF bytes. These are distinct evidence levels. Document IDs, legal effect, effective dates, detailed procedural posture, entity matching, obligations and private business relevance remain unassessed unless a later source-specific extraction or human review supplies evidence.

The producer does not assign canonical risk IDs, risk scores, controls, owners or legal conclusions. A downstream process can store these observations in its own review queue under its existing authority. It must not treat a preliminary signal as a promoted risk record. No existing GRC task is changed automatically by deploying this repository.

Suggested cloud-task instruction:

> Read the public events JSON and current source-health JSON. Select unseen non-BASELINE event IDs using this task's checkpoint. Preserve event/source/item IDs, URLs, hashes, original Thai title, observed time and publication-date uncertainty. Produce review-only intake candidates. Report blocked, stale and pending coverage separately. Do not infer no movement from source failure, and do not promote canonical risks. Save the checkpoint only after the task's permitted output has been verified.

GitHub writes and downstream GRC writes need their respective authorizations. The public monitor contains no private integration endpoints or credentials.
