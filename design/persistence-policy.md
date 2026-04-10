# Persistence Policy

YOMems should default to user-mediated persistence, not silent long-term writes.

## Core Rule

Durable memory is only committed when one of these is true:

1. the user explicitly asked to save it
2. the agent proposed a memory candidate and the user approved it

This keeps long-term memory trustworthy.

## Persistence Modes

### User-Mediated

This is the default mode.

Behavior:

- the agent may propose a candidate
- the candidate is stored separately from committed memory
- durable memory is committed only after explicit user approval

### Auto-Save

This mode is allowed only for low-risk working-state memory.

Behavior:

- the system may update task-scoped runtime memory without asking
- this should be limited to `active_task` objects

Auto-save must not silently create long-term facts, decisions, or lessons.

## Object-Level Policy

### Can auto-save by default

- `active_task`

### Must be user-mediated by default

- `identity_fact`
- `project_fact`
- `project_decision`
- `lesson`

## Candidate Workflow

The expected flow is:

1. agent detects a memory candidate
2. agent writes it as a candidate
3. user reviews or approves it
4. system promotes it into committed memory

This means YOMems should distinguish:

- proposed memory
- committed memory

## CLI Model

The CLI should expose:

- `propose`: write a candidate object
- `save`: commit a memory object directly when the user already decided
- `approve`: promote a candidate into committed memory

Optional:

- `reject`: remove or archive a candidate

## Storage Rule

Candidates should not live in the same files as committed memory.

They need separate storage so that:

- context packs can ignore them by default
- users can review them explicitly
- promotion is explicit and auditable

In a workspace-root deployment, candidate and committed memory should be separated per project bucket, for example:

- `.yomems/projects/neutron/candidates/`
- `.yomems/projects/neutron/decisions/`
- `.yomems/projects/ovn/candidates/`

This avoids mixing unrelated upstream projects while keeping all memory outside the individual source repositories.
