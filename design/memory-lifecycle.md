# Memory Lifecycle

YOMems should not accept every piece of analysis as long-term memory.

This document defines how knowledge moves through the system.

## Lifecycle Stages

### 1. Working State

Short-lived, task-bound knowledge.

Examples:

- current phase
- next action
- current scope files
- review outcome
- current hypothesis

Storage target:

- `active_task`

Rule:

- high update frequency is acceptable
- this layer is not long-term truth

### 2. Candidate Knowledge

Useful analysis that may become durable knowledge later.

Examples:

- root-cause analysis
- architecture observations
- repeated failure patterns
- rejected design alternatives

Storage target:

- `investigation`
- draft lessons or draft decisions

Rule:

- do not promote automatically
- require review or explicit confirmation

### 3. Durable Knowledge

Stable, reusable memory that should survive task completion.

Examples:

- confirmed user preferences
- stable project facts
- accepted project decisions
- reusable lessons
- reusable long-form investigations that are worth rereading directly

Storage target:

- `identity_fact`
- `project_fact`
- `project_decision`
- `lesson`
- `investigation`

Rule:

- durable memory cards must be short, typed, and intentional
- durable investigation documents may be longer, but they still need a short summary and explicit scope

### 4. Superseded or Archived Knowledge

Old but retained for audit purposes.

Examples:

- replaced design choices
- outdated project assumptions
- lessons invalidated by implementation changes

Rule:

- keep for traceability
- exclude from default context packs

## Promotion Rules

Working state should only be promoted when at least one of these is true:

- the fact will likely matter in future tasks
- the decision has been explicitly accepted
- the lesson explains a repeated failure mode
- the information would be expensive to rediscover

## Demotion Rules

Durable memory should be demoted or archived when:

- the project changed and invalidated the memory
- the decision was replaced
- the memory is too vague to guide future work
- the memory duplicates a better record

## Default Read Policy

The system should prefer:

1. active task records
2. active project decisions
3. active project facts
4. active lessons
5. only then archived or superseded material
