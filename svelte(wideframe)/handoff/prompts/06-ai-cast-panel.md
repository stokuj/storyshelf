# 06 — AI Cast Panel

Read `docs/handoff/05-ai-features.md`.

Implement the AI side panel on `/books/[slug]`. This is the **defining feature**
of Variant A. Take it slow.

1. **`ai/AICastPanel.svelte`**:
   - Dashed accent border, `Sparkles` heading "Meet the cast".
   - State machine via `$state`: `idle | pending | ready | partial | failed`.
   - **Idle**: explainer copy + spoiler `Slider` (chapter or %) + `Generate ✨` button.
   - **Pending**: 8 skeleton character rows, subtle pulsing dot + "Reading the book…" copy.
     If the backend supports SSE streaming for extraction, set state to `partial` and
     animate cards in as they stream; otherwise stay `pending` until the full payload arrives.
   - **Ready**: list of `CharacterRow` cards (avatar, name, role, AI badge if `source === 'ai'`).
     "See all (n)" link → `/books/[slug]/characters`.
     Quick-action chips at bottom: `Open relation graph`, `Spoiler-safe summary`, `Ask about this book`.
   - **Failed**: error block + `Retry` button.
2. **`ai/CharacterRow.svelte`** with a `MoreVertical` menu:
   - `Verify` → `verifyCharacter(id)`, removes the AI badge, sets `source` to `ai-verified`.
   - `Reject` → opens a `Dialog` with the 4-option form (see §verification UX).
3. **Relation graph dialog**:
   - `ai/RelationGraphDialog.svelte` — full-screen `Dialog`, contains a `@xyflow/svelte`
     `<SvelteFlow>` with `Background`, `Controls`, and `MiniMap`.
   - Node = `<CharacterAvatar size="md">` + label.
   - Edge color by `kind` (tokens `--color-rel-*`).
   - Edge `enemy` rendered as dashed; `family` solid; `romance` thicker.
   - Clicking a node navigates to the character page.
   - Filter chips at the top of the dialog (`all`, `family`, `romance`, `ally`, `enemy`).
4. **Spoiler control**:
   - Above the panel: `Slider` 0–100% OR a chapter picker. Changes refetch the
     extraction with `?through_chapter=` and animate diff.
5. **Confidence banner** when `confidence_summary.flagged_low > 0`.

## Acceptance

- In MOCK mode, clicking `Generate` transitions through `pending → ready` with the
  fixture characters.
- Verify and reject buttons hit the wrappers and update local state optimistically.
- Opening the graph shows a layout-pleasant network of the 6 fixture relations.
- Keyboard alternative to the graph: in the same dialog, render a `<ul>` of
  `Character → relation → Character` lines.
- Visual reference: Variant A, sheet 02 right column + the graph from sheet 02
  of Variant B (yes, we reuse it inside the modal).
