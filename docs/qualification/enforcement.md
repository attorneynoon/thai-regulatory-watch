# Enforcement-family qualification — 2026-09-19

23 existing source IDs inspected:17 qualified within explicit bounded scopes,6 remain disabled/pending with evidenced access or extraction blockers. MOL was assigned to the institution-family work and ThaiBMA Hearing was outside this repair scope. These counts describe extraction qualification, not completed production collection or full institutional coverage. All observations remain unreviewed and legal effect is `Not assessed`.

Public requests used the repository `Transport`: robots checked per origin/redirect, ordinary declared User-Agent, TLS verification, explicit host allowlists, bounded responses. Initial sandbox network denials were retried with approved network execution and are not recorded as publisher failures. No CAPTCHA,403, robots, TLS or identity bypass was used. No production collection/state write ran in this lane.

## Scoped outcomes

| Existing ID | Result | Live extraction and limitation |
| --- | --- | --- |
| amlo-listing-01 | Qualified public-form HTML | Initial GET returns an image-only intro. Its explicit public POST form `intro_page=1` returns the264,585-byte homepage without authentication or retained cookies.5 unique headline/recent-card publications; split day/month dates left unknown. |
| amlo-listing-02 | Qualified HTML |20 designated-person announcement rows on first page; first `/dpl/content/detail/313`. Dates within titles left unknown. |
| amlo-listing-03 | Qualified HTML |9 SED publication cards; first `/content/detail/407`. Specific card title excludes author/view count. Raw date includes author label, so parsed date remains unknown. |
| bot-listing-01 | Qualified JSON |20 recent items. Official AEM component model and frontend JavaScript establish endpoint and fields. Server reports totalResults2216; no pagination/backfill claim. Path includes2569 and needs year-rollover review. |
| customs-listing-01 | Qualified HTML |24 accepted links in `.panel-news`; excludes generic menu links and recruitment. Dates in image tooltips are not assumed publication dates. |
| dbd-listing-01 | Qualified JSON, narrow category |12 records; API says total13 and limit12 despite requested25. Existing category is English Press Release, not the full Thai newsroom. UI confirms `/news/{slug}`. First record published2026-03-05. |
| dip-listing-01 | Qualified JSON |13 accepted IP news records from20 latest official WordPress `news` rows. Procurement/recruitment excluded. Advertised generic RSS was examined and rejected because it held organization/procurement posts. Public type metadata explicitly linked the selected news REST route. |
| diw-listing-01 | Pending |robots.txt returned HTML/HTTP200; fail-closed before homepage content. |
| diw-listing-02 | Pending |Same robots blocker prohibits news-page qualification. |
| diw-listing-03 | Pending |Same robots blocker prohibits REST qualification. Adapter support alone cannot repair source policy. |
| dsi-listing-01 | Pending |robots.txt returned HTML/HTTP200; fail-closed. Official `/th/Type/Mission-News/4` index discovered via web search, but it shares the unresolved origin policy. |
| excise-listing-01 | Pending |Homepage disallowed by robots. The separate permitted webdev publication service below is a partial institutional alternative, not equivalent homepage coverage. |
| excise-listing-02 | Qualified HTML |10 first-page rows in2569 enforcement archive; first `/1324-31`, publication2026-09-12. Year-specific archive requires annual review. |
| fda-listing-01 | Qualified JSON |10 published API newsUpdate rows, mapped to public frontend routes. First ID3617, publication2026-09-18. |
| fda-listing-02 | Qualified JSON fallback |Same first-party API replaces empty HTML shell.10 rows; existing source ID retained. Overlaps listing01, not independent evidence. |
| nbtc-listing-01 | Pending |Original News.aspx, official homepage and separately discovered official Press-Center listing returned403. Access authorization/publisher change required. |
| ncsa-listing-01 | Qualified JSON fallback |22 published announcement-category records from full official export. Date descending, cap100. |
| ncsa-listing-02 | Qualified JSON fallback |1,479 published news-category rows parsed; latest100 eligible for collection after date sort. |
| ncsa-listing-03 | Qualified JSON |1,487 published records across categories; latest100 after date sort. |
| ocpb-home | Qualified HTML alternative |4 official homepage news cards. Intro links to `index.php?filename=index`; landing page itself was only redirect JavaScript. Menu and view counts excluded from titles. |
| ocpb-listing-01 | Qualified HTML category |Required `cid=2` discovered on homepage;9 news cards. Bare more_news.php was not a usable listing. Preserve site's actual `news_view_en.php` links despite Thai titles. |
| tcc-listing-01 | Qualified RSS |9 accepted entries from advertised latest10-item RSS after existing exclusions. Arbitrary modern slugs no longer lost by dated-URL regex. |
| thaibma-listing-01 | Qualified HTML |115 PDF links; explicit cap300. Title comes from text-bearing table cell, not empty icon anchor or ordinal column. One row labeled only by year excluded. Includes amendments/historical/repealed rows; their current legal applicability is unassessed. |

NCSA's official frontend explicitly calls `/data/output/news.json`, uses `/news/{_id}`, and filters array-valued category membership. The actual response was27,500,481 bytes. The source-specific32MB ceiling replaces the insufficient default4MB bound. Three existing scopes use this same export and overlap; they must not be interpreted as three independent sources. Export order was old-first, making sort-before-cap necessary. `showdate` supplies publication metadata; CMS `_created`, `_modified` and editor identifiers are omitted from the fixture/mapping. Home JSON was also checked but contained page configuration, not a substitute news feed.

OCPB and SED compound date text remains in `publication_date_raw`; parsed dates are null rather than guessed. ThaiBMA filename/title years are not promoted to publication dates. These known metadata limits do not become assertions of no regulatory change.

Amendment after integrated review: the OCPB part of that initial limitation is superseded. Both OCPB selectors now extract only the explicit Thai date, excluding the changing view count. `18 ก.ย. 2569` normalizes to `2026-09-18`; a counter-only-change regression produces identical records. SED's remaining compound-date limitation is unchanged. Integrated collection also found that the standard-library robots parser collapsed literal `/?` into `/`; the standards-based parser correction and its access-preserving tests are recorded in [main qualification](main.md#robots-parser-correction).

Later metadata follow-up also resolves SED's compound date: an explicit leading `DD/MM/YYYY` before the observed `Post by` label is selected; `04/09/2569` parses to `2026-09-04`. Author and view-counter text are not publication dates. The focused official-fixture regression passed after this configuration change.

## Reproducible evidence

AMLO continuation supersedes the initial GET-only blocker: the inspected intro supplied an ordinary public navigation form, not an access challenge. Exact request: POST `https://www.amlo.go.th/index.php/th/`, `Content-Type: application/x-www-form-urlencoded`, body `intro_page=1`. Verification retained Transport's robots, host, DNS, TLS, timing and byte checks, with cookies cleared before and after the request. Result HTTP200, five distinct publication links. `regwatch/publicform.py` validates the exact current GET form before submission: one matching POST action, one configured hidden field, correct value, no duplicate/unexpected named controls, and no changed page destination. Only this AMLO contract is supported. Transport/collector integration is owned by the main repair work; raw verification used an equivalent session wrapper. No authentication, token or retained session was introduced.

The minimal representative fixtures under `tests/fixtures/repairs/enforcement-*` preserve selected source text, links and DOM/JSON structure. They were mechanically reduced from responses fetched on2026-09-19. Full raw responses stay in ignored scratch storage; fixtures omit unrelated images, scripts, content bodies and CMS editor IDs. The ThaiBMA fixture includes both an unnumbered memorandum row and a numbered rule row to guard against selecting an ordinal as the title.

| Source response | SHA-256 of exact fetched body |
| --- | --- |
| AMLO public-form homepage | `01398036315e4007d576581849d7dbb5d3610adff5c410a202e13b3d84e59fab` |
| AMLO DPL | `04908bc5fc31e55f967b49f488cb50082bd9e6ad559e6deda2f0b6de1ee0be52` |
| AMLO SED | `42d27bfde4a78b5cddca5f171468138aab55a7fa07aa41c2f52cdf2e0b5336f0` |
| BOT JSON | `b2935598791348536322c672766c4e42451c9daba002351d0afc62a381b69160` |
| Customs | `c9732306dfbcf521e352d42e3abebf1a9314c2ebf88e0310f6056e111a03da0f` |
| DBD JSON | `80a2b8aec554bb36d70072bc44b949e49a6342cba73314a51fd746a841235473` |
| DIP JSON | `2f525ed5be3bdf4d917b5a4a39a4e643c8e4b329ed41a5a58f1124c6223b5677` |
| Excise archive | `8f2b6cf9e6ad65dd0d8e84bc8527cbd6fdd4f0ba57e1d5cdfc8c9536772f58fe` |
| FDA JSON | `778784ba5a0bb0ab023c72311968e6b2040af9b82d796fc5de6f59452e408a42` |
| NCSA JSON | `888d0024275372f74edf40a96d19fb477fdfee75de3e30bde7dd752046f7fb21` |
| OCPB homepage | `cc201cd5e759c4fd88b4c65f53108ef2b842e4571684d99fe20e0cd22b550ec9` |
| OCPB category2 | `ec5437e8180bd11ea3d6ee8bc734df4772e498a52b66796d0e0a9133afde9ad6` |
| TCC RSS | `a3148adc74f576c856b77e7b0ef9a6a751a5f96856f1f6de80e975c62d8cd7ca` |
| ThaiBMA Rules | `4a5b2b1d5bfdf03675e7a20ec39c67ab599938fd57481383db82dee2482c56ac` |

Source URLs and exact extraction configurations reside in `config/repairs/enforcement.yml`, merged over existing IDs without renaming. Routes were cross-checked against observed public JavaScript for DBD/FDA/NCSA, the BOT component model, DIP WordPress type metadata, or links in official HTML/RSS declarations. An item route returning a client-rendered shell verifies routing only, not full article-body extraction.

Validation: `python -m unittest discover -s tests -p test_enforcement_qualified.py -v` passed10 tests. They cover every enabled fixture, the exact AMLO form and altered-field/action rejection, clean AMLO card titles, meaningful ThaiBMA titles, menu/count exclusion, official routes and Thai dates, NCSA published/category/order gates, procurement exclusions, modern RSS slugs and disabled unresolved sources. Live counts above use the actual parser against fetched responses; they are not synthetic-fixture counts. Wider integration/collection verification belongs to the main repair work.

Unresolved next triggers: publisher-compatible robots policy for DIW/DSI; permitted access for NBTC/Excise root. Do not enable these sources merely because neighboring scopes work. No absence-of-update claim is supported for blocked scopes.
