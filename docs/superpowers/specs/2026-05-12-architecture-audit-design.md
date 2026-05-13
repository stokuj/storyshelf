# Architecture Audit — Design

This document defines a quick independent audit of repository compliance with `ARCHITECTURE.md`.
It exists to keep the audit focused on evidence, not assumptions.

**Attention Conservation Notice**
For: Maintainer reviewing repository architecture consistency
What: Scope and method for a fast `implementation vs ARCHITECTURE.md` audit
Action: Review the audit method and confirm it matches the expected output
Skip if: You only need the final audit findings and do not care about method

## What We Need From You

Review this spec and confirm the audit method is acceptable before the audit starts.

## Background

`ARCHITECTURE.md` describes the intended stack, containers, data flow, auth model,
Celery topology, database shape, and CI/CD path. The requested output is not a full
architecture review. It is a quick independent audit that highlights the most
important mismatches between the document and the current implementation.

## Audit Goal

Produce a short findings report that answers one question: which important claims in
`ARCHITECTURE.md` are supported by repository evidence, and which are not.

The audit should prefer concrete proof from code and configuration over inference.

## Audit Scope

The audit will check these architecture areas:

1. Tech stack and active runtime components
2. Container topology and local/prod orchestration
3. Request and async data flow
4. Authentication model and token handling
5. Celery workers, queues, routing, and failure handling
6. Database and key domain model claims
7. CI/CD implementation

The audit will not attempt a complete code quality review, performance review, or
security assessment unless a critical mismatch is directly visible while verifying an
architecture claim.

## Approach

Recommended approach: **hybrid, document-led verification**.

For each major section of `ARCHITECTURE.md`, the audit will:

1. Extract the highest-value architecture claims
2. Verify them against repository evidence
3. Mark each claim as one of:
   - `zgodne`
   - `częściowo zgodne`
   - `niezgodne`
   - `niezweryfikowane`
4. Record the strongest supporting file reference or mismatch reference

This keeps the audit fast while still anchored in implementation.

## Evidence Sources

Primary evidence sources:

1. `infra/compose/` and related deployment config
2. `frontend/` auth and API integration code
3. `backend-django/config/settings/` and Django app code
4. Celery worker configuration and task routing code
5. Django models, serializers, and URLs for domain-model claims
6. `.github/workflows/` for CI/CD claims
7. `AGENTS.md` only as supporting repo context, not as the source of truth over code

## Output Format

The final audit should be short and structured.

| Field | Meaning |
|---|---|
| Area | Architecture section being checked |
| Status | `zgodne`, `częściowo zgodne`, `niezgodne`, `niezweryfikowane` |
| Evidence | File path(s) and brief observation |
| Finding | The key conclusion for that area |

After the table, include a short list of the highest-priority mismatches only.

## Decision Rules

Use these rules during the audit:

1. Treat repository code and configuration as higher-confidence evidence than prose docs.
2. Treat stale documentation outside `ARCHITECTURE.md` as supporting context, not proof.
3. Prefer explicit configuration over inferred behavior.
4. If evidence is ambiguous, mark the claim `niezweryfikowane` instead of guessing.
5. Ignore legacy Java code in `backend/` unless `ARCHITECTURE.md` explicitly depends on it.

## Deliverable

The deliverable is a concise audit report in chat, not a code change.

If the audit reveals that `ARCHITECTURE.md` is stale in material ways, that can be
followed by a separate documentation update task.
