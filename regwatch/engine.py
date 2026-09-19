"""Pure state transitions; fetching and publication live outside this module."""
from copy import deepcopy
from .models import canonical_url, digest


def empty_state():
    return {"schema_version": "1.0", "last_run_at": None, "items": {}, "sources": {}, "events": [], "health_events": []}


def source_state(state, source_id):
    return state["sources"].setdefault(source_id, {"baseline_complete": False, "observations": {}, "status": "not-run", "last_attempt_at": None, "last_success_at": None, "last_error": None, "last_count": 0})


def set_health(state, source, status, now, error=None):
    ss = source_state(state, source["id"])
    previous = ss["status"]
    if status != previous:
        n = len(state["health_events"]) + 1
        state["health_events"].append({"event_id": "health-" + digest([source["id"], n, status])[:32], "source_id": source["id"], "regulator_id": source["regulator_id"], "observed_at": now, "previous_status": previous, "status": status, "message": error, "official_url": source.get("url")})
    ss.update(status=status, last_attempt_at=now, last_error=error)
    if status == "healthy":
        ss["last_success_at"] = now


def apply_observations(state, source, candidates, now):
    ss = source_state(state, source["id"])
    baseline = not ss["baseline_complete"]
    for record in candidates:
        url = canonical_url(record["url"])
        item_id = "item-" + digest(url)[:32]
        old = ss["observations"].get(item_id)
        metadata = {k: record.get(k) for k in ("title", "summary", "published_at", "publication_date_raw", "modified_at", "selected_text_sha256", "document_url", "document_id")}
        content_hash = digest(metadata)
        attachment = record.get("attachment_sha256") or (old or {}).get("attachment_sha256")
        revision = (old or {}).get("revision", 0)
        kind = None
        if old is None:
            kind = "BASELINE" if baseline else "NEW"
        elif old["content_sha256"] != content_hash:
            kind = "UPDATED"
        elif old.get("attachment_sha256") and attachment != old["attachment_sha256"]:
            kind = "UPDATED_ATTACHMENT"
        if kind:
            revision += 1
        first = (old or {}).get("first_observed_at", now)
        observation = {**metadata, "item_id": item_id, "source_id": source["id"], "canonical_url": url, "content_sha256": content_hash, "attachment_sha256": attachment, "revision": revision, "first_observed_at": first, "last_seen_at": now, "asset": record.get("asset", (old or {}).get("asset", {}))}
        observation["event_id"] = (old or {}).get("event_id")
        ss["observations"][item_id] = observation
        item = state["items"].setdefault(item_id, {"item_id": item_id, "canonical_url": url, "first_observed_at": now, "source_ids": []})
        if source["id"] not in item["source_ids"]:
            item["source_ids"].append(source["id"])
            item["source_ids"].sort()
        item["last_seen_at"] = now
        if not kind:
            continue
        event = {"schema_version": "1.0", "event_id": "event-" + digest([source["id"], item_id, revision])[:32], "observation_id": "obs-" + digest([source["id"], item_id, revision])[:32], "item_id": item_id, "revision": revision, "previous_event_id": (old or {}).get("event_id"), "event_type": kind, "source_id": source["id"], "regulator_id": source["regulator_id"], "publisher": source["title"], "jurisdiction": source.get("jurisdiction", "TH"), "topics": source["topics"], "document_type": source.get("document_type", "publication"), "authority_class": source.get("authority_class", "official-publication"), "classification_basis": "source-configuration; item legal authority not assessed", "language": source.get("language", "th"), "title": record["title"], "summary": record.get("summary"), "official_url": url, "canonical_url": url, "listing_url": source["url"], "document_url": record.get("document_url"), "document_id": record.get("document_id"), "published_at": record.get("published_at"), "publication_date_raw": record.get("publication_date_raw"), "modified_at": record.get("modified_at"), "effective_at": None, "first_observed_at": first, "observed_at": now, "content_sha256": content_hash, "attachment_sha256": attachment, "source_response_sha256": record.get("source_response_sha256"), "extraction_method": source.get("mode", "html"), "extraction_confidence": "unassessed" if source.get("validation_status") != "verified" else "fixture-validated", "pinpoint": record.get("pinpoint"), "review_status": "unreviewed", "legal_effect": "Not assessed", "signal_candidate": "Radar", "signal_type": "public_source_observation", "temporal_horizon": "Not assessed", "coverage_status": source.get("validation_status", "candidate"), "limitations": list(source.get("limitations", [])) + (["Publication date unavailable"] if not record.get("published_at") else [])}
        event["changed_fields"] = [k for k in metadata if old and old.get(k) != metadata[k]]
        if old and attachment != old.get("attachment_sha256"):
            event["changed_fields"].append("attachment_sha256")
        observation["event_id"] = event["event_id"]
        state["events"].append(deepcopy(event))
    ss.update(baseline_complete=True, last_count=len(candidates))
    set_health(state, source, "healthy", now)
    state["last_run_at"] = now
