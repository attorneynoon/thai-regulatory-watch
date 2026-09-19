# Practice-focus pages

Practice pages are human-readable views over the same retained observations used by regulator, topic and source feeds. They do not create, rewrite or promote events. Every page shows current items, post-baseline changes, included regulator groups and source health. Legal effect and applicability remain Not assessed.

The configured pages are:

- Privacy & Digital Regulation
- Cybersecurity & Technology
- Competition & Consumer Protection
- Financial Services, Markets & AML
- Employment & Workplace
- Healthcare & Product Safety
- Corporate, Trade, Tax & IP
- Public Law, Legislation & Enforcement
- Tech Lawyer & Digital Platforms

The cross-cutting Tech Lawyer view combines PDPC, ETDA, MDES, NBTC, TCCT, OCPB, TCC, NCSA, ThaiCERT and CCIB source groups. A regulator can appear in several practices because these pages are reading and subscription lenses rather than exclusive taxonomies.

## URLs and feeds

For a configured slug such as `tech-lawyer-digital-platforms`:

- Human page: `practice/tech-lawyer-digital-platforms/`
- Current-items RSS: `feeds/practice-tech-lawyer-digital-platforms.xml`
- Changes RSS: `feeds/practice-tech-lawyer-digital-platforms-changes.xml`

Current-items feeds deduplicate canonical items and sort by source publication time, then source modification time; undated items follow. Changes feeds retain source-specific post-baseline events in detection order. Both retain the normal 500-entry RSS window, while JSON remains the complete retained contract. For readable scanning, each page previews 15 changes and 30 current items and links to its full RSS windows. Source-section limitations are collapsed but keyboard-accessible.

## Adding or changing a practice

Edit `config/practices.yml`. Each entry requires a stable lowercase slug, a reader-facing title and summary, and a nonempty unique list of existing `regulator_id` values from `config/sources.yml`. Unknown regulators, duplicate slugs and malformed entries fail validation. Removing a regulator from a practice changes only that derived page/feed scope; it does not remove source data or history.

Run the unit suite, `python -m regwatch validate`, `python -m regwatch build`, and `python -m regwatch check`. Inspect the generated page at phone and desktop widths. Coverage warnings must remain visible: an unavailable or pending source is not evidence that no regulatory update exists.
