# YOMems Architecture

## Problem

Most agent memory systems are either:

- prompt logs disguised as memory
- large markdown directories that must be reread
- host-specific features tied to one agent runtime

YOMems takes a different approach: memory lives in a fixed `.yomems/` markdown repository, and the system maintains lightweight derived indexes for efficient reads.

The preferred deployment model is a workspace-root repository, not a per-upstream-repo hidden directory. In a multi-repo workspace such as `/root/opendev`, the memory root should live at `/root/opendev/.yomems/` and keep each project in its own bucket.

## Core Model

### Storage Layer

Filesystem-backed markdown memory files with:

- human-readable primary documents
- separate candidate and committed stores
- compact derived JSON indexes for fast query

### Contract Layer

Typed memory objects with stable scopes:

- global
- project
- task

### Access Layer

Simple CLI commands:

- `init`
- `propose`
- `save`
- `approve`
- `reject`
- `candidates`
- `query`
- `context`

## Persistence Model

YOMems separates:

- committed memory
- candidate memory

Committed memory is part of normal query and context flow.
Candidate memory is excluded from default context packs until approved.

## Repository Model

The intended repository shape is:

- `.yomems/INDEX.md` as the human-readable entry point
- `.yomems/active-context.md` for hot task context
- global identity memory under `.yomems/identity/`
- project-scoped memory under `.yomems/projects/<project>/...`
- categorized markdown files under decisions, facts, lessons, tasks, and candidates inside each project bucket
- longer human-readable investigation documents under investigations inside each project bucket
- hidden derived indexes for fast CLI lookups

This keeps upstream repositories clean while still allowing the agent to isolate `neutron`, `ovn`, and other workspace projects inside one shared memory root.

## Read Strategy

The system should prefer:

1. compact indexes
2. filtered memory cards derived from markdown
3. intent packs
4. only then deeper investigation documents or source code

## Current MVP Limits

- no embedding search
- no automatic promotion pipeline
- no cross-project ranking
- no TTL or pruning policy yet

Those are deferred on purpose. The first version should prove that strict structure beats large free-form memory dumps.
