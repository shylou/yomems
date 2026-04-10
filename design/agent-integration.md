# Agent Integration

This document defines how an agent should use YOMems during normal work.

YOMems should feel like a lightweight memory layer inside an agent workflow, not a separate system the user has to operate manually on every turn.

The preferred deployment model is a workspace-level memory root plus a
host-local skill bundle:

- workspace memory: `<workspace>/.yomems/`
- Codex skill: `~/.codex/skills/yomems/`
- Claude skill: `~/.claude/skills/yomems/`

## Integration Goals

An agent should be able to:

1. detect when past knowledge may help
2. query `.yomems/` cheaply
3. continue normal work with a small relevant context set
4. detect when a new durable insight appeared
5. ask the user whether that insight should be saved
6. save it in a standard markdown form after approval
7. prioritize memory lookup when the user explicitly asks for it

## Query Triggers

The agent should consider querying YOMems when one of these is true:

### 0. Explicit user request

If the user explicitly asks to check memory, history, or `.yomems`, the agent should query YOMems before continuing the main reasoning flow.

Examples:

- “先查一下 .yomems”
- “去记忆仓库看看有没有相关内容”
- “先唤醒一下以前的知识”
- “look up the existing memory first”

Preferred query:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent project-onboard --keyword "<user-topic>" --limit 3
```

### 1. Architecture or design work

Examples:

- planning a new workflow
- changing routing logic
- evaluating competing designs

Preferred query:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent project-onboard --keyword "<topic>" --limit 3
```

### 2. Complex code analysis

Examples:

- tracing a subsystem
- reading unfamiliar implementation
- investigating a repeated bug pattern

Preferred query:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent project-onboard --keyword "<module-or-problem>" --limit 3
```

### 3. Review and follow-up decisions

Examples:

- deciding whether findings stay in the current task
- checking previous design constraints
- validating whether a known lesson applies

Preferred query:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent review-context --task-id <task-id> --keyword review --limit 3
```

### 4. Task continuation

Examples:

- resuming interrupted work
- recovering focus scope
- finding next-step context quickly

Preferred query:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent continue-task --task-id <task-id> --limit 3
```

## Save Triggers

The agent should consider proposing durable memory only when the value is likely to survive the current task.

### Good save moments

- a design decision was accepted
- a reusable lesson was confirmed
- a stable project fact was discovered
- a user preference was made explicit

### Bad save moments

- raw brainstorming
- temporary hypotheses
- unverified root-cause theories
- large command output
- notes that only matter for the current minute of work

## User-Mediated Save Flow

The expected agent behavior is:

1. detect candidate knowledge
2. generate a short structured summary
3. check whether equivalent memory already exists
4. if no good match exists, render a user-facing prompt with `yomems prepare` or `yomems suggest`
5. ask the user whether it should be saved
6. on approval, write it with `yomems remember --mode save ...` or `yomems propose`
7. if proposed, promote it with `yomems approve`

## Recommended Prompt Shape

When the agent believes memory should be saved, the prompt should be short and concrete.

Example:

```text
建议保存一条记忆：

类型：project_decision
主题：task-review
摘要：Task Review 应基于当前交付是否完成，而不是仅按分数路由。

是否保存到 .yomems？
```

Recommended helper call:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems check --root "$ROOT" --input ./candidate.json
bash <skill-dir>/bin/yomems suggest --input ./candidate.json
```

Preferred combined helper call:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
bash <skill-dir>/bin/yomems prepare --root "$ROOT" --input ./candidate.json
```

Direct flag-based helper:

```bash
bash <skill-dir>/bin/yomems remember --root "$ROOT" --id <id> --kind <kind> --scope <scope> --project <project> --summary "<summary>"
```

## Save Strategy

Use `save` directly only when the user already explicitly decided to persist the knowledge.

Use `propose` when:

- the agent extracted the memory itself
- the user is approving a candidate
- the workflow benefits from a reviewable pending item
- no similar durable memory already exists

## Query Strategy

The agent should not read `.yomems/` wholesale.

The preferred order is:

1. `wake` for the normal compact retrieval path
2. `context` for intent-only recovery when no keyword is needed
3. `query` with `--keyword` and optional `--kind` when the agent needs finer control
4. only then read the specific markdown files returned by query

When possible, the agent should look at `matched_on` in query or wake results before expanding markdown files. This keeps retrieval explainable and helps the agent decide whether a result is actually relevant.

If the user explicitly requested a memory lookup, step 1 should happen before the agent continues the main answer or implementation flow.

## Host Integration

In Codex or Claude, YOMems should be treated as a host-local skill bundle that
the agent can call when:

- planning starts
- deeper implementation analysis starts
- review routing starts
- a durable insight appears

It should not run on every trivial turn.

Preferred skill directory resolution:

- Claude: `~/.claude/skills/yomems/`
- Codex: `~/.codex/skills/yomems/`

The agent should resolve the workspace memory root before query or save. It
should not default to broad filesystem search such as `find /root` when the
user explicitly requested a memory lookup.
