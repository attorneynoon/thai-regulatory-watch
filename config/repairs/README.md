# Qualification handoff manifests — not runtime configuration

These dated manifests preserve the parallel source-qualification handoffs from 2026-09-19. They were merged into `config/sources.yml` and may be superseded by later fixes there. The collector reads **only `config/sources.yml`**. Do not merge these manifests again when adding a source. Fixture tests select each batch's source IDs here but use the final primary registry settings.

Full evidence and remaining restrictions are in `docs/qualification/`. No manifest makes a blocked source operational or establishes exhaustive coverage.
