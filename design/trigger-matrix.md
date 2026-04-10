# Trigger Matrix

This document defines when an agent should call YOMems during normal work.

The goal is to avoid two failure modes:

- querying too often and wasting tokens
- proposing too many memory saves and interrupting the user

## Query Triggers

The agent should call `wake` only when one of these is true.

| Situation | Trigger | Recommended Call |
|---|---|---|
| User explicitly asks for memory lookup | The user directly asks to check `.yomems`, memory, or past decisions | `yomems-agent-wake "<project>" project-onboard "<user-topic>"` |
| Starting architecture or design work | A new design topic, workflow, or routing rule is being discussed | `yomems-agent-wake "<project>" project-onboard "<topic>"` |
| Entering deep implementation analysis | The agent is tracing unfamiliar code or subsystem behavior | `yomems-agent-wake "<project>" project-onboard "<module-or-problem>"` |
| Review routing or follow-up judgment | The agent needs historical review decisions or known lessons | `yomems-agent-wake "<project>" review-context "review" "<task-id>"` |
| Resuming interrupted work | There is an active task and the agent needs fast recovery | `yomems-agent-wake "<project>" continue-task "" "<task-id>"` |
| Explicit historical question from user | The user asks “what did we decide before?” or similar | `yomems-agent-wake "<project>" project-onboard "<keyword>"` |

## Non-Triggers For Query

The agent should usually not call `wake` when:

- the request is trivial and self-contained
- the task is a one-shot shell command
- the current answer does not depend on past project knowledge
- the same memory was already loaded in the current working context

## Save Triggers

The agent should call `prepare`, `suggest`, or `remember` only when one of these is true.

| Situation | Trigger | Recommended Call |
|---|---|---|
| Design decision confirmed | A choice was explicitly accepted | `yomems-agent-remember prepare project_decision ...` |
| Reusable lesson confirmed | A pattern or pitfall clearly applies beyond the current task | `yomems-agent-remember prepare lesson ...` |
| Stable project fact discovered | A script, path, module, or behavior has a durable meaning | `yomems-agent-remember prepare project_fact ...` |
| User preference stated clearly | The user explicitly establishes a stable preference | `yomems-agent-remember prepare identity_fact ...` |
| Runtime task state update | Current phase/next step changed and should stay resumable | `yomems-agent-remember save active_task ...` |

## Non-Triggers For Save

The agent should not suggest saving when:

- the idea is still speculative
- the discussion is still comparing alternatives
- the result is just a large output dump
- the note only matters for the next minute of work
- the same durable memory already exists

## Interaction Budget

The save flow should stay lightweight.

- At most one proactive save suggestion per meaningful subtopic.
- Avoid repeating the same suggestion if the user already declined.
- Prefer fewer, higher-value memory proposals.
- Run a duplicate check before suggesting durable memory saves.

## Query Budget

- Default `wake` should return at most 3 matches.
- If `context` already answers the need, do not broaden query.
- Only read the returned markdown files when the compact result is insufficient.
- If the user explicitly requested lookup, do not skip `wake` just because the agent thinks it can answer from memory.
