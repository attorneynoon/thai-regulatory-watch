# Health patch continuation — 17 October 2026

## Status

The maintenance patch has been integrated with the newer production snapshot and verified again. **It has not been pushed, merged, deployed, or exercised by a hosted qualification run.** The current live NCSA response size remains unknown. The original [investigation](HEALTH_FAILURE_INVESTIGATION_2026-10-17.md) remains a dated record of the earlier `3de47486...` snapshot; this addendum records the subsequent work rather than changing that evidence.

The refreshed base is `c57493285ec3c7abee6df1adf5217916d1b746e9`. The reviewed implementation was applied as local commit `075dfe71bea0b2a67f89cf29c988d2e76e6ce6a1`, whose direct parent is that base. Its production code, registry, workflows, scripts and tests are identical to the previously tested `8b2c3bff...` patch. A following documentation commit records this continuation. Public GitHub noreply identity was verified for both author and committer. Maintenance publication remains subject to the repository's branch/PR and noreply requirements.

## Latest production evidence

The repository refresh at 05:14 UTC, rechecked at **06:40:34 UTC / 13:40:34 Bangkok**, found main at [c57493285...](https://github.com/attorneynoon/thai-regulatory-watch/commit/c57493285ec3c7abee6df1adf5217916d1b746e9). The latest observed [monitoring run 39002923821](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/39002923821) started at 04:32:03 UTC and was last updated at 04:41:54 UTC.

| Job | Result | Interpretation |
|---|---|---|
| [collect](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/39002923821/job/117309434255) | Success | The unpatched production workflow passed its 122 tests and persisted new observations. |
| [deploy](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/39002923821/job/117311164974) | Success | The generated Pages artifact was deployed. |
| [health](https://github.com/attorneynoon/thai-regulatory-watch/actions/runs/39002923821/job/117311165020) | Failure, exit 1 | The command reported the same 26 enabled nonhealthy sources. Its checkout was already the new collection commit c574. |

This preserves the original diagnosis: source coverage is failing while collection and deployment continue. Explicit health-SHA pinning addresses a possible future race; neither the requested incident nor this latest run demonstrated that race.

The new snapshot contains **3,977 items, 4,502 observation events and 442 health transitions**. Relative to the earlier snapshot, it adds three items and three events. Every previous item ID remains present, all 4,499 previous observation events are an identical prefix, and all 442 previous health events are an identical prefix. These additions came from the existing production collector, not from applying this patch.

The [source snapshot](https://github.com/attorneynoon/thai-regulatory-watch/blob/c57493285ec3c7abee6df1adf5217916d1b746e9/site/api/v1/sources.json) still has 52 stored healthy, 22 blocked and four failed enabled scopes. The state run timestamp is 04:33:56 UTC. At the fresh read-only CLI check at **06:46:20 UTC**, the patched default command correctly exited 1 for **26 issues**: three failed verified NCSA scopes, one failed candidate and 22 blocked candidates. Strict coverage exited 1 for **85 issues**, additionally rejecting the 38 healthy candidates and 21 unverified pending scopes. Neither command changed the state bytes. Thus the earlier 78-issue stale evaluation and the newer 26-issue fresh evaluation refer to different snapshots and clocks; no freshness rule was relaxed.

## Verification on the refreshed base

The complete required checks ran on a disposable export of `075dfe71...` with Python 3.12 and the repository's pinned dependencies:

| Check | Result |
|---|---|
| Unit/regression suite | 152 tests passed in 5.938 seconds. |
| Registry validation | Passed: 99 scopes, 78 enabled, 21 pending, 53 regulators, nine practices. |
| Offline build | Passed: 3,977 items, 4,502 events, 262 feeds. |
| XML/JSON contract check | Passed. |
| Required second build | All 282 generated site files were byte-identical. |
| Disposable state | Unchanged by both builds and validation. |
| Protected production snapshot | All 287 tracked state/site/schema files byte-identical to c574. |
| Independent integration review | No findings; prior history, qualification labels, reviewed code and noreply identities preserved. |

The preserved monitor-state SHA-256 is `80d28e7666d70612115227e6bdd8d74bf330a33759cd4b3810d497fd0edfa013`. No tracked state, site or schema file belongs to the maintenance diff. The [continuation evidence](evidence/2026-10-17-health/continuation.json) records these checks separately from the original verification.

## Bounded local NCSA attempt

One additional read-only qualification attempt ran at **05:14:56 UTC**, using the proposed 64,000,000-byte cap and the earlier `3de47486...` retained state. It stopped during the robots check with `Robots unavailable: [Errno -3] Temporary failure in name resolution` and exited 1. HTTP status, response byte count, response digest and content type were all null because no content response was obtained.

This is an environment DNS failure, not an observed publisher denial or evidence that 64 MB succeeds. The helper's temporary blocked results retained verified labels and counts 23/100/100, with `count_basis: retained-state` and `history_preserved: true`. Those temporary results were not written into production history. All 283 tracked state/site files checked around this attempt retained their hashes; that narrower probe manifest excludes the four schemas included in the 287-file integration check.

## Remaining acceptance

The implementation and refreshed offline verification are complete. Remote branch/PR publication, hosted CI, current NCSA payload measurement and qualification, and post-application monitoring are still outstanding. No remote branch, PR, commit, workflow dispatch, merge or deployment was created by this continuation.

Once the patch is reviewed and applied through an authenticated maintenance route, run the read-only NCSA qualification and inspect actual response size, HTTP/content checks, all three collectors and history preservation. The newly added manual workflow must exist on the default branch before GitHub exposes its manual dispatch. Then verify an ordinary monitoring run preserves old item IDs and event prefixes, deploys successfully, and checks the exact collection SHA. Remaining PDPC and other access failures must remain visible even if NCSA recovers. The latest run-start gap was 4 hours 53 minutes 18 seconds; the reason for schedule gaps is still unestablished, and the three-hour freshness gate remains unchanged.
