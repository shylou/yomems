# Naming Conventions

This document defines how YOMems memory files, ids, and topics should be named.

The goal is to keep `.yomems/` readable as it grows.

## File Name Rule

The markdown file name should always be:

```text
<memory-id>.md
```

Examples:

- `dec-review-routing.md`
- `fact-task-tracker-state-home.md`
- `lesson-relative-project-root.md`
- `task-review-refactor-followup.md`

## Memory ID Rule

Memory ids should be short, stable, and type-prefixed.

Recommended prefixes:

- `pref-` for `identity_fact`
- `fact-` for `project_fact`
- `dec-` for `project_decision`
- `lesson-` for `lesson`
- `task-` for `active_task`

Examples:

- `pref-response-language`
- `fact-task-goal-view-location`
- `dec-review-dual-mode`
- `lesson-relative-project-root`
- `task-review-routing-followup`

## Topic Rule

Topics should be slug-style, lowercase, and stable.

Recommended format:

```text
<domain>-<subject>
```

Examples:

- `task-review`
- `project-identity`
- `task-tracking`
- `memory-query`
- `install-flow`

Avoid:

- mixed case
- spaces
- punctuation-heavy topic names
- multiple near-duplicate spellings

## Summary Rule

Summary should be one short statement.

It should answer:

- what this memory is about
- why it matters

Avoid long paragraphs in `Summary`.

## Duplicate Rule

If a new memory uses the same topic and near-identical summary as an existing active memory, prefer updating or reusing the existing memory instead of creating a new one.

## Human Readability Rule

A human should be able to infer the rough purpose of a memory entry from:

1. the directory
2. the file name
3. the topic
4. the summary
