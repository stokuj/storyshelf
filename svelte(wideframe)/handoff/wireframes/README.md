# Wireframes — Variant A

`Wireframes.html` is the source-of-truth visual reference for Variant A:

- Sheet 01 → **Discover** route
- Sheet 02 → **Book detail** route (the right-rail "Meet the cast" panel is the
  defining feature of this variant)
- Sheet 03 → **Profile** route (classic shelves + AI sidecar)
- Sheet 04 → **Settings** (shared across all variants — implement as-is)

The graph from Variant B sheet 02 is **reused inside the relation-graph dialog**
opened from the AI panel. See `prompts/06-ai-cast-panel.md`.

The other variants (B, C, D, E) exist only as reference for future experiments and
should not influence the initial build.

## How claude-cli uses these files

These are React + Babel + HTML sketches. They run in the browser as wireframes.
Claude Code should **read them as code**, not screenshot them — it can grep for
`VariantA` and see the exact structure. Do not port the wireframe HTML directly
into Svelte; treat it as a layout reference and reimplement with shadcn-svelte
components and the project design tokens.
