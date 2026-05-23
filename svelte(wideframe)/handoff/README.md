# Storyshelf — frontend handoff

Everything in this folder is meant to be **dropped into a fresh SvelteKit repo** and
read by Claude Code (claude-cli). The goal: a frontend that talks to your existing
backend, implementing **Variant A — Classic catalog + AI side panel** from the
wireframes.

## What's where

| File | Purpose |
|---|---|
| `CLAUDE.md` | **Master file** — copy this to repo root. Claude Code reads it on every turn. |
| `01-design-system.md` | Colors, typography, spacing, radii, motion. |
| `02-data-model.md` | TypeScript types for Book, Character, Relation, User, Shelf, etc. |
| `03-api-contract.md` | REST endpoints to plug in. Fill in any gaps from your real backend. |
| `04-routes-and-screens.md` | SvelteKit route map + per-screen spec. |
| `05-ai-features.md` | LLM extraction flow, prompts, JSON schema, caching, spoiler control. |
| `06-iteration-plan.md` | Suggested order to feed work to claude-cli. |
| `prompts/*.md` | **Paste-and-go** prompts for claude-cli, one per slice of work. |
| `wireframes/` | The wireframe HTML + JSX you've been reviewing — Variant A focus. |
| `skeleton/` | Minimal starter files: `app.css`, `package.json` snippet, `svelte.config.js`. |

## How to use it

1. `git init` a new SvelteKit project (`npx sv create storyshelf-web`).
2. Copy `CLAUDE.md` to the repo root.
3. Copy `wireframes/` and the rest of `handoff/` into the repo (e.g. as `docs/handoff/`)
   so claude-cli can `cat` them.
4. Start with `prompts/01-setup.md` and walk down. Each prompt is a single iteration.

## Why Variant A

Lowest risk, highest reuse of existing Goodreads-style mental model. AI is **opt-in**
on the book page — easy adoption, easy A/B comparison against the no-AI baseline.
Graph and chat experiments from variants B/C can be layered on top later without
breaking the IA.
