# Work record

## 2026-09-19 — implementation authorized

Owner approved RSS plus JSON, review-only GRC integration, extensible government URLs, automatic hosting and collection, and cloud maintenance. The latest instruction expands the seed inventory to all GRC regulator watch lists.

Read current enforcement, GR/GA upstream, legislative registries and cloud monitoring lane descriptions. Import only public source identities/URLs and classifications; exclude private destinations, project priorities, credentials, captures and legal determinations. Prior source status is discovery evidence, not verification of this new collector. The fixed-instrument practice registry is reference material, not a changing regulator listing.

Plan amendment: preserve the original design as history. Replace its initial 14-source limit with the reconciled watch inventory. Exact API URLs are retained pending tested adapters; additional institutions named without listing URLs remain visible pending scopes. Use complete JSON event history and configurable RSS windows (default 500); RSS is not a complete archive once that window is exceeded. Event identity includes a source-specific monotonic revision so A-B-A reversions are distinct.

Local repository is independent. No existing GRC automation or canonical store is modified. Shared brain routing was inspected; source decisions use current local project records. GitHub CLI authentication verified outside the restricted network sandbox; the target repository does not yet exist. GitHub connector currently exposes no repositories.

Implementation, tests, live validation and remote deployment outcomes will be appended below.

### First live probe and correction

Python 3.12.14: 26 tests passed. Bounded probes collected TCCT ruling links and explicit dates; two PDFs returned valid signatures and SHA-256 fingerprints. ETDA robots exceeded the response bound; TISI failed TLS validation; BOT listing returned no article links. OCPB's generic listing returned navigation links, exposed by representative inspection. The uncommitted probe state was preserved outside the public repository before resetting the draft production baseline. Parser now excludes navigation/footer/sitemap elements, TCCT has an observed .detail/.text-red2 selector fixture, and OCPB generic index plus BOT are pending. No contaminated draft observations were published. This is a pre-release qualification correction, not deletion of published history.

### Release qualification

Implemented 96 public source scopes across 53 institution groups, RSS/JSON contracts, dashboard, offline builds, hourly workflow, cloud onboarding and source-request template. Live local qualification retained 475 baseline observations from 7 successful scopes; 17 enabled scopes failed, 8 were blocked and 64 remained pending. No claim of complete regulator coverage. Date parsing now preserves RFC timestamps and explicit Thai/BE dates. Added fail-closed missing-state behavior and first-PDF-fingerprint semantics: establishing a hash does not imply a document change. Latest fingerprints are available in current item observations; immutable event evidence is not rewritten. 35 tests passed. See the verification record for release evidence and next owner actions.

### Public deployment and cloud readback

Created the owner-approved public GitHub repository, enabled Pages with workflow deployment, set its public base URL and enabled the hourly collector. First GitHub run 35432350248 passed collection and deployment; its separate health job failed for real source limitations. Retained output increased to 575 baseline items, including TCCT press releases. PDPC became access-blocked from GitHub; prior observations were preserved. HTTPS RSS/JSON/OPML readback passed, as did Linux CI and desktop/mobile browser checks. Direct GitHub connector file reads and repository permissions verified; account-specific Codex environment selection remains an owner setup step. No existing GRC tasks, canonical stores or private integrations were changed.

Next obligations: maintainers qualify failed/pending source scopes with representative fixtures and permitted live checks; owner selects the repository in Codex cloud for coding tasks and chooses where existing GRC consumers should read these public endpoints. Those downstream changes are outside this producer deployment.

Cloud/local artifact comparison exposed RSS extension ordering differences after persisted-state reload. Added a regression and sorted extension fields; 36 tests passed. This changes serialization order only, preserving all event identities and source evidence. Re-running the hosted workflow verifies the amended producer and deployment.

Final health regression found that repeated attachment failures could emit a temporary healthy transition within each run. Collector now sets final health only once after document checks. The failing regression passed after the fix; 37 tests passed. This prevents misleading recovery notices without weakening the separate health-failure signal.

Second hosted run 35432691007 passed collection/deployment and retained the same 575 event IDs and identical combined RSS bytes, with no false content-change events. Health remained red for unresolved source coverage. Public readback passed again. The final health-transition correction is test-verified and queued for the next scheduled/manual run; no claim is made that that later code path ran in this second collection.
