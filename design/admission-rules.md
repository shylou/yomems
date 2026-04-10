# Memory Admission Rules

This document defines what should and should not enter YOMems.

Durable memory should default to user-mediated persistence:

- the user asks to save it, or
- the agent proposes it and the user approves it

## Good Memory Candidates

### Identity Facts

Accept when the fact is stable and cross-task.

Examples:

- response language preference
- code language preference
- default review expectations

### Project Facts

Accept when the fact describes stable project reality.

Examples:

- a script's real responsibility
- the canonical config location
- the true source of task state

### Project Decisions

Accept when a design choice was actually made.

Examples:

- where compact task-goal data lives
- how project identity is resolved
- how review routes back into implementation

### Lessons

Accept when the lesson is concise, repeatable, and useful beyond the original task.

Examples:

- relative project roots create unstable buckets
- wide substring matching pollutes scoped review inputs

### Active Tasks

Accept when the object helps resume current work cheaply.

Examples:

- current phase
- next action
- review outcome
- focus scope

### Investigations

Accept when the user or agent needs a complete write-up that should remain directly readable later.

Examples:

- subsystem architecture analysis
- root-cause reports that explain the full chain
- implementation deep-dives that future work can reuse

## Bad Memory Candidates

Reject these by default:

- raw chat transcripts
- long command output dumps
- unverified speculation
- one-off implementation details with no reuse value
- large natural-language notes that duplicate code or docs

## Writing Rules

Every memory write should satisfy these rules:

1. It has a type.
2. It has a scope.
3. It has a short content field.
4. It can be filtered later by project, task, topic, or tags.
5. It is worth the token cost of future retrieval.

## Compression Rule

If the same knowledge can be represented as:

- a 2-3 sentence memory object, or
- a full-page note

prefer the short memory object for default retrieval, and save the full-page note as an `investigation` only when the long form is itself useful to reread.

## Review Rule

Before promoting working knowledge into durable memory, ask:

1. Will this matter again?
2. Is it actually confirmed?
3. Is this better stored as a fact, a decision, or a lesson?
4. Can it stay understandable in one short entry?
