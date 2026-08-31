# Roadmap

## v0.1 — transcript → structured trace

Shipped. `afr ingest` reads a visible session log and writes a flight record.

## v0.2 — evidence-linked pattern extraction

Shipped as a first cut. Seed patterns exist. `afr library` attaches sessions to stable IDs such as `AFR-P001`.

## v0.2.1 — attribution hardening

Shipped. Canonical speaker roles, role-aware recovery pairing, fixture-fingerprint removal, separated extraction vs corroboration confidence, adversarial negatives, CI.

## v0.3 — multi-session library + deduplication

Partial. Matching is by `pattern_id`. Title clustering and counterexample intake are next.

## v0.4 — compare two agents on the same task

Not shipped. Same transcript task, two models, diff the process events and refusals.

## Later

- Operating cards exported for local coding agents
- Better parsers for product-specific export formats
- Human confirm/reject UI for extracted patterns
