# Roadmap

## Current State

The MVP currently provides:

- fixed `.yomems/` repository layout
- typed memory objects
- markdown memory files
- compact derived indexes
- query and context CLI

## Next Milestones

### Milestone 1: Better Context Packs

Add richer intent packs such as:

- `implement-feature`
- `debug-issue`
- `prepare-review`
- `handoff`

### Milestone 2: Investigation Records

Add a first-class object type for analysis that is not yet durable memory.

This will allow:

- draft findings
- rejected alternatives
- promotion into lessons or decisions

### Milestone 3: Promotion Pipeline

Add a CLI flow such as:

- `archive`
- `supersede`
- `refresh-index`

so the lifecycle becomes explicit instead of manual.

### Milestone 4: Ranking and Retrieval Quality

Improve retrieval with:

- recency scoring
- stronger priority handling
- task/topic-aware ranking
- optional semantic reranking on filtered candidates only

### Milestone 5: Agent Adapters

Provide thin wrappers for:

- Codex
- Claude
- generic CLI agents

These adapters should only convert environment context into YOMems queries. They should not fork the schema.

## Non-Goals For The MVP

- vector databases
- embedding-first retrieval
- autonomous long-form summarization
- host-specific proprietary memory formats
