---
name: yomems
description: Workspace-level memory retrieval and persistence for architecture notes, reusable facts, and long-form investigations.
---

# YOMems Skill

Use this skill when the user asks to:

- check past memory
- query previous analysis or decisions
- save current analysis into memory
- continue work using prior project knowledge

Do not fall back to broad filesystem search before trying YOMems.

## First Response Contract

When the user explicitly mentions `yomems`, `memory`, past decisions, prior analysis, or asks to save/query knowledge:

1. Resolve the installed YOMems helper path for the current host.
2. Resolve the workspace memory root.
3. Use `yomems query`, `yomems wake`, or `yomems save` first.
4. Only do ad hoc file search if YOMems returns nothing and that gap matters.

Do not start with `find /root`, `rg /root`, or generic MEMORY.md searches.

## Installed Helper Resolution

Prefer these paths in order:

1. Claude Code: `$HOME/.claude/skills/yomems/`
2. Codex: `$HOME/.codex/skills/yomems/`
3. Only when working inside the `yomems` repository itself: `./`

Wrapper command:

```bash
bash <skill-dir>/bin/yomems ...
```

Root resolver:

```bash
bash <skill-dir>/scripts/resolve-memory-root.sh
```

## Workspace Root Policy

The memory repository is workspace-level, not repo-local.

Default rule:

1. If any ancestor directory already contains `.yomems/`, use that.
2. Else, if the current directory is inside a git repo and the parent of the repo root contains `.yomems/`, use that.
3. Else, use `<current-directory>/.yomems` for initialization only.

Examples:

- `/root/opendev/neutron` -> `/root/opendev/.yomems`
- `/root/opendev/ovn` -> `/root/opendev/.yomems`

Never create `.yomems` inside an upstream project unless the user explicitly asks for a repo-local store.

## Retrieval Workflow

When the user asks to query memory:

1. Resolve the root:

```bash
ROOT="$(bash <skill-dir>/scripts/resolve-memory-root.sh)"
```

2. Prefer a targeted query:

```bash
bash <skill-dir>/bin/yomems query --root "$ROOT" --project <project> --topic <topic> --limit 10
```

3. If the request is broader or needs compact context:

```bash
bash <skill-dir>/bin/yomems wake --root "$ROOT" --project <project> --intent project-onboard --keyword <keyword> --limit 5
```

4. If there is a matching `investigation`, read or summarize that document instead of doing blind repo-wide search first.

## Persistence Workflow

When the user asks to save analysis:

- Save a short reusable fact/lesson for cheap future recall.
- Save a full `investigation` when the write-up itself is worth rereading.

Direct save example:

```bash
bash <skill-dir>/bin/yomems save --root "$ROOT" --input /tmp/memory.json
```

If user confirmation is needed first, use:

```bash
bash <skill-dir>/bin/yomems prepare --root "$ROOT" --input /tmp/memory.json
```

## Usage Heuristics

- Use `project_fact` for short stable facts.
- Use `lesson` for reusable pitfalls or debugging heuristics.
- Use `investigation` for complete architecture or subsystem analysis.
- Keep default retrieval small; only read full investigations when needed.

