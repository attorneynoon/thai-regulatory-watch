"""Read-only source health checks; qualification and runtime health are distinct."""
from datetime import datetime, timedelta, timezone


def health_problems(sources, state, *, strict_coverage=False, now=None):
    now = now or datetime.now(timezone.utc)
    problems = []
    for source in sources:
        record = state['sources'].get(source['id'], {})
        stored_status = record.get('status', 'not-run')
        status = stored_status
        success = record.get('last_success_at')
        reason = 'source_status'
        health_error = None
        if source['enabled'] and status == 'healthy':
            if success is None or success == '':
                status, reason = 'invalid', 'missing_success_timestamp'
                health_error = 'Healthy source has no last_success_at; freshness cannot be verified'
            else:
                try:
                    if not isinstance(success, str):
                        raise ValueError('Timestamp must be a string')
                    stamp = datetime.fromisoformat(success.replace('Z', '+00:00'))
                    if stamp.utcoffset() is None:
                        raise ValueError('Timestamp must include a timezone')
                except ValueError:
                    status, reason = 'invalid', 'invalid_success_timestamp'
                    health_error = 'last_success_at must be a valid timezone-aware timestamp'
                else:
                    if stamp > now:
                        status, reason = 'invalid', 'future_success_timestamp'
                        health_error = 'last_success_at is in the future; freshness cannot be verified'
                    elif now - stamp > timedelta(hours=3):
                        status, reason = 'stale', 'stale_success'
                        health_error = 'Last successful collection is more than three hours old'
        reasons = []
        if source['enabled'] and status != 'healthy':
            reasons.append(reason)
        if strict_coverage and source['validation_status'] != 'verified':
            reasons.append('unverified_coverage')
        if reasons:
            problems.append({
                'source': source['id'], 'status': status,
                'validation': source['validation_status'],
                'enabled': source['enabled'], 'stored_status': stored_status,
                'url': source.get('url'), 'reasons': reasons,
                'last_attempt_at': record.get('last_attempt_at'),
                'last_success_at': success, 'last_error': record.get('last_error'),
                'health_error': health_error,
                'max_response_bytes': source.get('max_response_bytes', 4_000_000),
            })
    return problems
