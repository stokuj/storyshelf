# 10 — AI chat ("Ask about this book")

Read `docs/handoff/05-ai-features.md` → "Ask about this book".

Implement:

1. **`ai/AskBookSheet.svelte`** — slide-in `Sheet` from the right on `/books/[slug]`:
   - Header: book title, spoiler-up-to indicator, close button.
   - Conversation list (renders `MessageBubble`s).
   - Composer at the bottom (Textarea + send button, Cmd+Enter to send).
   - Suggested-prompts chips above composer:
     - "Who fights whom?"
     - "Summarize chapter X"
     - "What's the love triangle?"
     - "Themes I might miss?"
2. **`ai/MessageBubble.svelte`**:
   - Variants: `user`, `assistant`.
   - Assistant can render mixed blocks: markdown text, embedded `CharacterCard`,
     embedded mini-graph (smaller version of the relation graph).
   - Citations rendered as superscript chips → click opens a Popover with the quote
     + chapter; clicking through links to the relevant character/scene.
3. **Streaming**:
   - `src/lib/api/ai.ts` `askAboutBook(bookId, message)` opens an EventSource.
   - Map SSE event types: `token`, `block:character_card`, `block:mini_graph`,
     `done`, `error`. Append to message state.
   - Cancel button stops the stream and aborts the EventSource.
4. **Persistence**:
   - Conversations persist server-side, scoped to `(user_id, book_id)`.
   - On open, `GET /books/:id/ai/conversation` to load history.

## Acceptance

- Send a message → assistant streams reply token-by-token; mini-graph and character
  cards appear inline as blocks.
- Cancel mid-stream stops further updates and shows a "stopped" pill.
- Refreshing the page restores the conversation.
- Closing the Sheet without sending preserves the draft.
