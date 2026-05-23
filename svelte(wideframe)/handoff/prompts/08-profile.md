# 08 — Profile

Read `docs/handoff/04-routes-and-screens.md` → "Profile" — plus Variant A, sheet 03 in the wireframes.

Implement `/u/[handle]`:

1. **Header**: avatar, display name, handle, joined date, follower count, top genres.
2. **Reading challenge**: progress bar `X / Y`, picks up `user.reading_goal`.
3. **Recently read**: row of 6 covers with star ratings.
4. **Activity feed**: cards for rated/reviewed/added-to-shelf events.
5. **AI sidecar** (dashed accent border, right column):
   - Recent AI extractions list (book + char count + when).
   - Recent chats (book + msg count).
   - Inline settings preview: auto-extract on add, spoiler shield, share extractions —
     each is a link to `/settings/ai`.
6. **Visibility**:
   - If `user.visibility === 'private'` and viewer is not owner → show only avatar
     and "This profile is private." message.
   - If `friends` and viewer not approved → same.
   - If `public` or viewer is owner → full content.

## Acceptance

- `/u/alex-k` (fixture) renders fully for the owner; `/u/private-fixture` renders
  the locked state for another user.
- Layout shifts to a single column on mobile.
- All shelves are reachable from the profile.
