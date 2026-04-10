# YOMems

YOMems is an agent-agnostic memory repository manager for AI coding agents.

The goal is to let agents recover the smallest useful slice of past knowledge from a fixed workspace memory directory without rereading large note collections or replaying full chat history. YOMems treats memory as a curated markdown repository with lightweight indexing, not a prompt log.

## Design Goals

- Agent-agnostic: Claude, Codex, or any other agent can read and write the same store.
- Low-token recovery: default reads should return compact, filtered context.
- Structured writes: memory entries are typed and normalized before they are saved as markdown.
- User-mediated persistence: durable memory should be approved, not silently accumulated.
- Gradual accumulation: knowledge can grow without turning into an unreadable document dump.
- Human-auditable: the store is plain files that can be reviewed and versioned.

## MVP Scope

This repository implements a filesystem-backed MVP with:

- typed memory objects
- a fixed `.yomems/` repository layout
- markdown memory files as the primary store
- compact derived indexes for fast lookup
- candidate and committed memory separation
- CLI commands to initialize, propose, save, approve, query, and build intent-oriented context packs

## Memory Object Types

- `identity_fact`
- `project_fact`
- `project_decision`
- `lesson`
- `active_task`
- `investigation`

## Store Layout

```text
.yomems/
├── INDEX.md
├── active-context.md
├── TOPICS.md
├── .index.json
├── .candidates.json
├── identity/
├── projects/
│   └── <project>/
│       ├── facts/
│       ├── decisions/
│       ├── lessons/
│       ├── tasks/
│       ├── investigations/
│       └── candidates/
└── archive/
```

Recommended usage for a multi-repo workspace:

```text
<workspace-root>/.yomems/
```

For example, if your workspace is `/root/opendev`, keep memory in:

```text
/root/opendev/.yomems/
```

and use `--project neutron`, `--project ovn`, and so on to keep per-project memory isolated without writing into those upstream repositories.

## CLI

Initialize a store:

```bash
python3 -m yomems init
```

By default, YOMems uses `./.yomems`. In a multi-repo workspace, point `--root` at the workspace memory repository and use `--project` to choose the project scope.

Propose a candidate memory object:

```bash
python3 -m yomems propose \
  --input ./examples/project-decision.json
```

Create a memory suggestion or save directly without preparing a JSON file:

```bash
python3 -m yomems remember \
  --id dec-review-routing \
  --kind project_decision \
  --scope project \
  --project yomems \
  --topic review \
  --summary "Review routing should prefer continuing the current task."

python3 -m yomems remember \
  --mode save \
  --id dec-review-routing \
  --kind project_decision \
  --scope project \
  --project yomems \
  --topic review \
  --summary "Review routing should prefer continuing the current task."
```

Render the standard user-facing save prompt before persistence:

```bash
python3 -m yomems check --input ./examples/project-decision.json
python3 -m yomems suggest \
  --input ./examples/project-decision.json
```

Prepare a save suggestion with duplicate checking in one step:

```bash
python3 -m yomems prepare \
  --root .yomems \
  --input ./examples/project-decision.json
```

Approve a candidate:

```bash
python3 -m yomems approve \
  --project yomems \
  --id dec_review_intent_001
```

Save a memory object directly when the user already decided to persist it:

```bash
python3 -m yomems save \
  --input ./examples/project-decision.json
```

Query memory objects:

```bash
python3 -m yomems query \
  --project yomems \
  --kind project_decision \
  --tag routing
```

Build a compact context pack:

```bash
python3 -m yomems context \
  --project yomems \
  --intent continue-task
```

Wake relevant memory for an agent with one command:

```bash
python3 -m yomems wake \
  --project yomems \
  --intent continue-task \
  --keyword review \
  --limit 3
```

## Markdown Templates

YOMems writes standardized markdown files under `.yomems/`:

- `project_decision` entries get `Context`, `Decision`, and `Consequences`
- `project_fact` entries get `Fact` and `Usage`
- `lesson` entries get `Problem Pattern`, `Lesson`, and `Next Time`
- `active_task` entries get `Details` and `Next Steps`
- `investigation` entries get `Summary`, `Key Findings`, and a full `Document`

This keeps saved memory readable for humans while still making it indexable for agents.

## Intent Model

The current MVP supports these intent-oriented context packs:

- `continue-task`
- `review-context`
- `project-onboard`
- `preferences`

Each context pack is assembled from a small filtered set instead of loading the entire store.

The default operating model is:

1. the agent works normally
2. when a durable insight is found, the agent first checks whether similar memory already exists
3. if not, the agent uses `yomems prepare`, `yomems suggest`, or `yomems remember` to ask whether it should be saved
4. on approval, YOMems writes a standard markdown memory file into `.yomems/`
5. when related knowledge is needed later, YOMems uses `context`, `query`, or `wake` to return a small relevant set

Human-readable entry points inside `.yomems/`:

- `INDEX.md`: overall committed memory index
- `active-context.md`: current hot task context
- `TOPICS.md`: topic-oriented grouped memory view

Naming and topic rules live in [design/naming-conventions.md](design/naming-conventions.md).

## Persistence Model

YOMems defaults to user-mediated persistence:

- `active_task` may be auto-saved as runtime state
- durable memory should be proposed first or explicitly saved by the user
- candidate memory is stored separately from committed memory

See [design/persistence-policy.md](design/persistence-policy.md).

## Query Model

Queries should stay small.

- default retrieval is driven by the hidden `.index.json`
- keyword matching prefers title matches, then summary matches, then details/findings/document matches
- query and wake results include `matched_on` so the agent can see why an entry was returned
- full investigation documents are stored as markdown for humans, but should only be queried when the task needs deeper context
- project-scoped queries still include global identity memory
- candidate memory is excluded from normal query and context results until approved

Example:

```bash
python3 -m yomems query \
  --project yomems \
  --keyword review \
  --limit 3
```

## Installation

Install into Codex:

```bash
bash scripts/install-codex.sh install
```

Install into Claude Code:

```bash
bash scripts/install-claude.sh install
```

Remove from the selected host:

```bash
bash scripts/install-codex.sh remove
bash scripts/install-claude.sh remove
```

Generic installer:

```bash
bash scripts/install.sh help
```

The installer places a host-local helper bundle under the host skills root:

- Codex: `~/.codex/skills/yomems/`
- Claude Code: `~/.claude/skills/yomems/`

It also creates a wrapper command at:

- `<skills-root>/yomems/bin/yomems`

## Agent Workflow

YOMems is designed to be called from within an agent workflow.

- query when architecture, review, or deep analysis work begins
- query immediately when the user explicitly asks to check `.yomems` or past memory
- use `context` for compact recovery
- use `query --keyword ... --limit 3` for targeted knowledge wake-up
- when the agent detects a durable insight, ask the user whether it should be saved
- after approval, persist it into `.yomems/` using the standard markdown templates

See [design/agent-integration.md](design/agent-integration.md).
See [design/trigger-matrix.md](design/trigger-matrix.md).

Thin helper wrappers are also provided:

```bash
bash scripts/agent-wake.sh <project> [intent] [keyword] [task_id]
bash scripts/agent-remember.sh <suggest|prepare|propose|save|check> <kind> <id> <project> <topic> <summary> [task_id]
```

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```
