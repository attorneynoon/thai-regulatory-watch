# PDPC, ETDA, SEC and TISI qualification — 2026-09-19

Scope: all 22 existing source IDs for these four institutions. The override file preserves IDs and does not edit retained observations. Tests and live probes use the project's existing TLS-verifying, robots-respecting transport and named user agent. No cookies, login, CAPTCHA bypass, TLS disable, alternate user agent or blocked-content replay was used. All legal effect remains **Not assessed**. Local success does not establish GitHub-hosted access or complete coverage.

Final local outcome: **13 repaired configurations**, one existing successful consultation configuration retained unchanged, and **8 unresolved scopes**. The 13 include explicitly partial aggregate/page monitoring and require the shared `json-page` and host-scoped intermediate integration described below. No production state was collected by this worker.

## Repairs supported by live evidence

| Existing source | Method and observed result | Material limitation |
|---|---|---|
| `pdpc-listing-02` | Public API snapshot of 16 consultation-topic taxonomy records, whitelisting `id` and `title`. | Partial aggregate taxonomy monitoring, **not consultation opinions or individual publications**; actual endpoint URL only, publication date null. |
| `pdpc-listing-03` | Public API snapshot of 68 active knowledge records; excludes both disabled records and all internal user/media metadata. | Partial aggregate content monitoring, **not individual publications**; actual endpoint URL only, publication date null. |
| `pdpc-listing-01` | Root is a landing screen; use the official linked `/front-page/`. `.detail h3.title a` with numeric permalinks returns 21 unique news cards. | Current front-page subset; overlaps `pdpc-official-home` while preserving source provenance. |
| `pdpc-official-home` | Same verified card selector, nearest `.detail`, displayed `.date`: 21 items. | Not complete historical news. Cloud robots failures remain possible. |
| `pdpc-official-office-orders` | Same numeric article pattern returns one office order, `https://www.pdpc.or.th/1626/`, displayed `6 Jan 2566` = 2023-01-06. | One currently listed article; no nested document traversal. |
| `pdpc-official-orders` | Original index is a navigation page. Follow its four panel links with `max_pages: 5`. Panels yield 24, 39, 7 and 8 unique PDF URLs, 78 total. | Download/copy buttons deduplicate by document URL. Displayed publication dates are not decision dates. |
| `pdpc-official-private-sector` | Selected-content page watch of the public GPPC PLUS description and four component descriptions; one page record. | Partial program-description monitoring, **not individual-item collection**. No registration actions. Date unknown. |
| `sec-listing-02` | `https://market.sec.or.th/public/idisc/th/ViewMore/enforce-recent?QueryType=ALL` is permitted and serves 161 enforcement rows. Watch selected table `#gPP26T02` as one page record. | Partial table-change monitoring, **not individual enforcement-item collection**. Repeated press-release URLs cannot identify each entity's row. No blocked `www.sec.or.th` requests required. Date unknown. |
| `etda-standards` | Alternate official catalog `https://opendata.etda.or.th/th/group/etda-recommendation` serves 41 recommendation datasets over two pages. Extract `.dataset-heading a`, preserving full anchor `title`. | Partial catalog coverage; not standards-news or consultation coverage. Catalog update dates are not established publication dates and stay null. |
| `tisi-listing-03` | Alternate official `https://tcps.tisi.go.th/public/StandardList.aspx` serves community-product standards. Watch only the 50 first-page standard rows, excluding navigation. | Partial **community standards** table watch, **not individual-item collection**, general industrial standards or full certification coverage. HTTP/backslash PDF links are neither fetched nor rewritten. Date unknown. |
| `tisi-listing-04` | Qualified 10 PR cards with actual slug URLs and displayed Thai dates, after validated intermediate-chain repair. | Current first-page archive only; normal TLS/hostname and robots checks remain enforced. |
| `tisi-listing-05` | Qualified 10 document-category cards with displayed Thai dates, using the same validated chain repair. | First-page archive may include dual-category articles; nested attachments not followed. |
| `tisi-listing-06` | Existing RSS endpoint qualified with 10 items and explicit RFC timestamps, using the same validated chain repair. | Latest RSS window only, not historical completeness. |

Seven fixture tests and three JSON-snapshot behavior tests pass. They cover dated numeric news links, office orders, four-panel traversal, PDF button deduplication, full catalog titles, unknown publication dates, TISI card/RSS dates, excluded navigation, active-record filtering, field whitelists, ordering stability and fail-closed schema/empty results. Fixtures are representative public extracts, not full source mirrors.

## Exact representative evidence

- News fixture (`blocked-pdpc-news.html`): `https://www.pdpc.or.th/front-page/`; “PDPC ย้ำความสำเร็จ คว้ารางวัลเลิศรัฐ ปี 2569”; `https://www.pdpc.or.th/28468/`; displayed `10 Sep 2569`, normalized 2026-09-10.
- Office fixture (`blocked-pdpc-office.html`): `https://www.pdpc.or.th/category/pdpc-law/announce/writ/`; “คำสั่งสำนักงานคณะกรรมการคุ้มครองข้อมูลส่วนบุคคล ที่ 1/2566 เรื่อง ระบบสำหรับการปฏิบัติหน้าที่โดยวิธีการอิเล็กทรอนิกส์”; URL/date above.
- Order fixture (`blocked-pdpc-orders.html`): `https://www.pdpc.or.th/adjudication-panel-decisionsummary-1/`; “ผลการพิจารณาตามคำสั่งคณะกรรมการผู้เชี่ยวชาญ คณะที่ ๑ ที่ ๑/๒๕๖๖ เรื่อง ไม่รับเรื่องร้องเรียน”; `https://www.pdpc.or.th/wp-content/uploads/2024/11/PDPC-Committee1-1.66.pdf`; displayed `5 Nov 2567`, normalized 2024-11-05. Root-link fixture comes from `https://www.pdpc.or.th/adjudication-panel-decisionsummary/`. The fourth panel link redirects to `https://www.pdpc.or.th/adjudication-panel-decisionsummary/adjudication-panel-decisionsummary-4/` and has 8 PDF rows.
- Private-sector fixture (`blocked-pdpc-private.html`): `https://register-gppc-plus.pdpc.or.th/`; selected description headed “แพลตฟอร์มเพื่อสนับสนุนการปฏิบัติตามกฎหมายคุ้มครองข้อมูลส่วนบุคคลสำหรับภาคเอกชน”; no publication date.
- SEC fixture (`blocked-sec-enforcement.html`): source URL above; representative table header and first row, dated 16/09/2569. This is an enforcement-row date, **not** a publication date for the aggregate page. The document has an empty HTML title; the page adapter must fall back to the configured source title.
- ETDA fixture (`blocked-etda-recommendations.html`): catalog URL above; “ขมธอ. 34-2566 ใบรับรองแพทย์อิเล็กทรอนิกส์ (Electronic Medical Certificate)”; `https://opendata.etda.or.th/th/dataset/standard_06_34`. The third fixture heading visibly truncates text while its title attribute contains the full published title; publication date unknown. The catalog's two pages are bounded, not a claim about unlisted standards.
- TISI fixture (`blocked-tisi-community.html`): source URL above; first row `1/2552`, “ขนมไทย”, “(THAI DESSERTS)”. The first row's document link is `http://tcps.tisi.go.th/pub\tcps1_52.pdf`; it is preserved as evidence, not fetched. Only the aggregate HTTPS table is monitored.

## Other checked IDs and initial blockers

| Source ID | Live evidence and alternative investigation | Remaining condition |
|---|---|---|
| `etda-listing-01` | `www.etda.or.th/robots.txt` returns 302 to `/th/`; the destination is an oversized HTML homepage, not a robots policy. Official ETDA catalog works but is not a substitute for Thai press news. | Operator must expose usable robots policy or an official permitted news feed. |
| `etda-listing-02` | Same host policy failure. The English press scope cannot be established from the recommendation catalog. | Usable robots policy or permitted official English-news feed. |
| `etda-listing-03` | Same policy failure for knowledge-sharing path. Catalog was inspected and contains datasets; it does not establish equivalent knowledge-article coverage. | Usable robots policy or a qualified official knowledge-article service. |
| `pdpc-listing-02` | Lawcenter API returned HTTP 200 and a `data` array of topic taxonomy records such as “หน้าที่ของผู้ควบคุมข้อมูลส่วนบุคคล/ผู้ประมวลผลข้อมูลส่วนบุคคล”, with IDs and `created_at`; no publication URL. | Subsequently repaired as explicitly partial aggregate taxonomy monitoring. Individual consultation coverage remains unestablished. |
| `pdpc-listing-03` | Lawcenter public knowledge API returned 70 records: 68 `status:1` and 2 `status:0`, including disabled test content. Active records have public text but no verified reader URL. | Subsequently repaired as an explicitly partial active-content snapshot. Creation timestamps are not publication dates; disabled records were not collected or placed in fixtures. |
| `pdpc-official-consultations` | Existing configured attachment adapter still works locally: 81 PDF opinions. Latest representative `consultation-81-1.pdf`, displayed 29 Aug 2569 = 2026-08-29. | Existing successful scope left unchanged. Local/cloud access can differ; do not misreport cloud robots failures as no updates. |
| `pdpc-official-gppc` | `gppc.pdpc.or.th` robots response is HTTP 200 HTML; fail closed. Search surfaced official course pages on this same host, which does not resolve host policy. | Usable robots policy or independently permitted official program listing. |
| `pdpc-official-public-hearings` | Configured `contact-us/public_hearing/` returns a generic public feedback form with name, phone, email and CAPTCHA, not hearing notices. The linked WordPress API discovery URL returns HTTP 403; no further API access attempted. | Need an official hearing-notice listing. A public submission form must not be promoted as publication coverage. |
| `sec-listing-01` | `www.sec.or.th/robots.txt` returns HTTP 403. The market subdomain's enforcement table works, but is already covered by the separate enforcement source and is not equivalent to general SEC news. | Allowed official general-news service or usable robots policy. |
| `tisi-listing-01` | `www.tisi.go.th` robots returns HTTP 200 HTML; fail closed. Search confirms newer public news URLs but same host policy applies. | Usable policy or independent official notice listing. |
| `tisi-listing-02` | Same main-host robots failure. Official community-standards service does not replace press news. | Usable policy or independent official news listing. |
| `tisi-listing-04` | Initially failed TLS certificate validation before content access. | Subsequently repaired using the public missing intermediate, validated to standard roots. |
| `tisi-listing-05` | Initially same PR-host TLS failure for documents category. | Subsequently repaired using the same validated intermediate and tested card selector. |
| `tisi-listing-06` | Initially same PR-host TLS failure for RSS. | Subsequently repaired using the same validated intermediate; RSS contract passed. |

Additional TISI alternatives: `https://appdb.tisi.go.th/tis_dev/p3_tis/p3tis.php?data=B` is permitted but serves an initially empty table. Its public script explicitly uses a **POST** DataTables request to `get_tis_data.php` with `data`, `txt_tis` and paging fields; no guess-based GET adapter was enabled. Supporting that contract would require a bounded read-only POST transport plus tested response/detail semantics. The separately discovered `itisi.tisi.go.th` service failed DNS resolution. These limitations do not imply there are no new standards.

## Verification and handoff

Local live probes were read-only except for scratch evidence under `work/blocked-families`; they never invoked production collection or changed `state/`. Thirteen scoped overrides are in `config/repairs/blocked-families.yml`. The main maintainer owns shared adapter integration, registry merge, production collection, hosted verification and the chronological work record. The shared parser requires `title_attribute` for full ETDA titles, a nonempty configured-title fallback for SEC, and dispatch for `json-page` to `regwatch/jsonsnapshot.py`. Shared transport must apply configured intermediates only to their exact host while preserving default trusted roots, hostname verification and robots handling.

During verification, the initially inspected first three PDPC panels yielded 70 rows, but the full root fixture exposed a fourth link. The bound was corrected from four to five pages, the fourth endpoint was fetched normally (8 rows), and the navigation test now asserts all four links. Earlier 70-row evidence is superseded by the 78-row total, preserving the reason for the correction.

### Later qualification: partial JSON snapshots

The initial API assessment withheld individual publications because no reader URLs or publication-date semantics were verified. The main maintainer then authorized an explicitly partial aggregate approach. `parse_json_snapshot` emits one record at the actual API endpoint with a deterministic hash of sorted, explicitly whitelisted public scalar fields. It emits a selected-record count, not public record bodies. The knowledge snapshot filters `status: 1`, includes only `id`, `document_number`, `subject`, `legal_topic`, `research_direction`, `consultation`, and excludes `user_id`, timestamps and media paths. Topic taxonomy whitelists only `id`, `title`. Changes to unselected fields or record ordering do not create a content change. Missing fields, nonarray results and empty selected content fail closed. Tests first failed on the absent module, then passed after implementation.

Representative JSON fixtures are reduced public extracts from the exact existing API URLs in the registry. They contain two topic entries and one active knowledge entry; no disabled/test content or internal user IDs. Full local payloads verified 16 and 68 selected records respectively. This supersedes the prior pending classification only for aggregate snapshots, not individual-publication coverage.

### Later qualification: TISI public certificate-chain repair

The initial TLS failure was investigated with public certificate-only diagnostics. `pr.tisi.go.th` sends **only its leaf certificate** (`CN=*.tisi.go.th`), valid 2026-02-16 to 2027-03-20. Its issuer is `GlobalSign GCC R6 AlphaSSL CA 2025`; it was not expired or self-signed. The leaf advertises the public CA issuer URL `http://secure.globalsign.com/cacert/gsgccr6alphasslca2025.crt`. That 1,425-byte DER intermediate was retrieved, converted to PEM, and verified with the server leaf using `openssl verify -CAfile <certifi roots> -untrusted <intermediate> <leaf>`: **OK**. A default-root SSL context with that intermediate then completed hostname-and-chain verification.

Only after verification succeeded did the worker request robots and source content with the same verified SSL context. All three PR URLs returned HTTP 200 with robots checks active. The category selectors were corrected from a date-path regex to `#magone-archive-blog-rolls .item-title a`, nearest `.item`, `.meta-item-date span`. Both archives yielded 10 records; RSS yielded 10. Example PR/RSS URL `https://pr.tisi.go.th/news_11-9-69/` has card date `11 กันยายน 2569` (2026-09-11) and explicit RSS timestamp `Fri, 11 Sep 2026 03:24:34 +0000`. Example document URL `https://pr.tisi.go.th/tisi_market/`, title “เอกสารเผยแพร่แผ่นพับโครงการร้าน มอก.”, has card date `7 กันยายน 2569` (2026-09-07).

Public intermediate stored at `config/tls/globalsign-gcc-r6-alphassl-2025.pem`:

- Subject: `C=BE, O=GlobalSign nv-sa, CN=GlobalSign GCC R6 AlphaSSL CA 2025`.
- Issuer: `OU=GlobalSign Root CA - R6, O=GlobalSign, CN=GlobalSign`.
- Validity: 2025-05-21 02:36:52 UTC to 2027-05-21 00:00:00 UTC.
- SHA-256 certificate DER fingerprint: `A883559231F8388DAF35CE41C8101040AE8FD9B656434247B9475AF592CC08CA`.
- SHA-256 checked-in PEM bytes: `C5E33C47FFB2B81739DC8003611C251241F663712AC628787D6D48E4ED6799CD`.

This adds a missing intermediate, not a new root or self-signed trust exception. No TISI HTTP response was fetched with verification disabled. Normal verification will fail closed if the leaf/chain expires or changes incompatibly; the publisher should still repair its server chain. The configured intermediate is scoped only to `pr.tisi.go.th`. This evidence supersedes the initial unresolved TLS classification for the three PR scopes.

### Additional bounded assistance: OCS certificates and source discovery

At the main maintainer's request, the same certificate-only diagnostic was applied to `www.ocs.go.th` and `www.krisdika.go.th`. OCS sends only a leaf with `CN=*.ocs.go.th`, valid 2025-10-01 to 2026-11-02, issuer `GlobalSign RSA OV SSL CA 2018`. Its organization string is `Krung Thai Bank Public Company Limited`; this is recorded exactly as certificate metadata, not inferred ownership. The advertised intermediate at `http://secure.globalsign.com/cacert/gsrsaovsslca2018.crt` verified the leaf to standard certifi roots. Stored public intermediate `config/tls/globalsign-rsa-ov-2018.pem` is valid 2018-11-21 to 2028-11-21 and chains to `GlobalSign Root CA - R3`.

- OCS intermediate DER SHA-256 fingerprint: `B676FFA3179E8812093A1B5EAFEE876AE7A6AAF231078DAD1BFB21CD2893764A`.
- Checked-in PEM SHA-256: `20AB099881F1A46DD93B360BA3FD28FBA95D37E36067E85E79DB0EDE29A5E963`.

With verified TLS and normal robots checks, `https://www.ocs.go.th/` returned HTTP 200. The page explicitly exposes lazy content blocks. `https://www.ocs.go.th/indexs/block/8?mode=frontend&screen=auto` returns four law-news cards; block 9 has academic articles and block 10 activities. Useful law-news selectors are `.carousel-inner a[aria-label="gotocontent"][href]` and each card's `span[title]` full title attribute. Live view counters must be excluded from titles/fingerprints. Three block-8 links are official OCS file-reader URLs and one is an official `law.go.th` hearing. No explicit publication dates appear. Scratch bodies and exact URL evidence were handed to the main maintainer, who owns any OCS configuration/adapter changes; this is not counted among the 13 family repairs.

`www.krisdika.go.th` instead presents a **self-signed default certificate** (`C=XX, L=Default City, O=Default Company Ltd`). It remains blocked: no self-signed trust exception or content fetch was attempted.
