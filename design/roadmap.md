# Roadmap

## Completed Milestones

The current implementation already provides:

- fixed `.yomems/` repository layout
- typed memory objects
- markdown memory files
- compact derived indexes
- query/context/wake CLI
- candidate and committed memory separation
- workspace-root project buckets
- first-class `investigation` records for long-form analysis
- explicit lifecycle commands for `archive`, `supersede`, and `refresh-index`
- host-local skill bundles for Codex and Claude

## Remaining Milestones

### Milestone 1: Better Context Packs

Add richer intent packs such as:

- `implement-feature`
- `debug-issue`
- `prepare-review`
- `handoff`

The current packs (`continue-task`, `review-context`, `project-onboard`,
`preferences`) are enough for the MVP, but not yet broad enough to cover the
full workflow set.

### Milestone 2: Ranking and Retrieval Quality

Improve retrieval with:

- recency scoring
- stronger priority handling
- task/topic-aware ranking
- optional semantic reranking on filtered candidates only

The current retrieval path is intentionally simple and deterministic. It works,
but it does not yet optimize ranking deeply.

### Milestone 3: Agent Adapters Hardening

Codex and Claude wrappers now exist, but they still need hardening around host
behavior and user prompting. Remaining work is:

- verify skill discovery works reliably across hosts
- reduce fallback-to-filesystem behavior further
- add one or more generic CLI-agent adapter examples

These adapters should only convert environment context into YOMems queries.
They should not fork the schema.

## Non-Goals For The MVP

- vector databases
- embedding-first retrieval
- autonomous long-form summarization
- host-specific proprietary memory formats
