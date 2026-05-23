# 09 — Settings

Read `docs/handoff/04-routes-and-screens.md` → "Settings".

Implement the full `/settings` section:

1. **Layout** `src/routes/settings/+layout.svelte`:
   - Left rail with links: `Account` (default), `Profile & privacy`, `Notifications`,
     `AI preferences`, `Reading & shelves`, `Connected apps`, `Data & export`, `Danger zone`.
   - Active link styling: `bg-ink text-paper rounded-md`.
2. **`/settings` — Account**:
   - Avatar block: drag-and-drop area (uses `<input type="file" accept="image/*">`
     hidden behind the dropzone). On change → `uploadAvatar`. Show preview + crop
     dialog (use `shadcn-svelte Dialog`).
   - "Generate ✨" alt: calls a backend endpoint (out of scope here — placeholder button
     that toasts "AI avatar coming soon").
   - Display name / username / email forms — superforms each, auto-save on blur.
   - Email change triggers a verify-email modal.
   - Password form (current / new / confirm) with `zxcvbn`-style strength bar.
3. **`/settings/profile` — Profile & privacy**:
   - 3 big radio cards (Public / Friends only / Private). Use shadcn `RadioGroup`
     styled as cards.
   - Granular toggles (Switch components) for: real-name visibility, activity feed,
     followed-characters visibility, AI-learning, search-engine indexing.
4. **`/settings/notifications`**: email + push toggles per event type
   (new follower, new review on your shelf, club update, AI extraction ready).
5. **`/settings/ai`**:
   - Tone radio.
   - Default spoiler limit radio.
   - Cite quotes radio.
   - Chat history retention slider (7 / 30 / 90 / forever).
6. **`/settings/data`**:
   - Export data — calls `/users/me/export`, then shows resulting `download_url` in a
     dialog with copy-to-clipboard.
   - Pause account (toggle).
   - **Delete account** — red outlined button → dialog requiring user to type their
     handle to confirm. Calls `DELETE /users/me` → signs out → redirects to `/`.

## Acceptance

- All forms validate client-side; failed server validations surface inline.
- Switching visibility immediately updates the profile sidebar preview.
- The danger-zone delete flow requires typing the handle, never one-click.
- Visual reference: shared Settings sheet at the bottom of the wireframes.
