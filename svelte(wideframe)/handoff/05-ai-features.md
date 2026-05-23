# 05 · AI features

The two AI surfaces in Variant A:

1. **Cast extraction** on the book page (`POST /books/:id/ai/extract`).
2. **Ask-about-this-book** chat (`POST /books/:id/ai/ask`, SSE-streamed).

## Cast extraction — UX states

| State | Trigger | UI |
|---|---|---|
| `idle` (no extraction yet) | first visit | Big `Generate ✨` button + explainer. Spoiler slider visible. |
| `pending` | user clicked Generate, or arrived while server still running | Skeleton list (8 rows), pulsing dot, copy: "Reading the book…" |
| `ready` | server returned characters & relations | Cards rendered. Each AI-only card has `Verify` / `Reject`. |
| `partial` | streamed | New cards animate in (fade + small Y) one by one. |
| `failed` | error | Inline error block + `Retry`. Log to Sentry. |

## Verification UX

Every AI-generated card has a tiny `MoreVertical` menu:

- `Verify` — sets `source: 'ai-verified'`, removes the AI badge.
- `Reject (this is wrong)` — opens a Dialog: "What's wrong?" with 4 radio options:
  - not a character
  - wrong role
  - merge with: …
  - other (textarea)
- Rejections feed back to the backend for future training data.

## Spoiler control

- User sets `coverage` (chapter or %). Sent as `?through_chapter=` to the extract endpoint.
- Backend returns characters/relations marked with `spoiler_chapter <= through_chapter`.
- If user later increases coverage, frontend refetches and **animates new cards in**.

## "Ask about this book" chat

- Triggered from a `Sheet` slid in from the right (mobile-friendly fallback to full screen).
- Conversation persisted server-side keyed by `(user_id, book_id)`.
- Streaming via SSE. Use `EventSource` wrapped in a small typed helper.
- Each AI message can contain rich blocks (also via SSE events):
  - `text` — markdown
  - `character_card` — id → renders `<CharacterCard>`
  - `mini_graph` — small relation cluster → renders inline SVG via `@xyflow/svelte` in static mode

```ts
// src/lib/api/ai.ts — sketch
export function askAboutBook(bookId: string, message: string) {
  const url = `${PUBLIC_API_URL}/books/${bookId}/ai/ask`;
  const sse = new EventSource(url + `?q=${encodeURIComponent(message)}`, { withCredentials: true });
  return sse;
}
```

## Quote citations

When the model claims something, the backend should return citations. Frontend renders
them as superscript chips that, when clicked, open a Popover showing the quote and
chapter. This is **non-optional** for trust — without citations users (correctly)
distrust the output.

## Confidence flags

`confidence_summary.flagged_low > 0` → show a yellow banner above the cast list:

> ⚠ 3 characters detected with low confidence. They may be one-off mentions
> mistaken for named characters. [Review]

Clicking `Review` filters the list to just those.

## Caching & cost

- Backend caches extractions. Frontend does **not** retry without explicit user action.
- `Refresh extraction` button (under a `MoreVertical` menu on the panel) calls the
  `refresh` endpoint and warns: "This will use AI credits and may take 30–60s."
- Show user's remaining credits if your backend exposes them.
