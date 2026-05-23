# 07 — Character pages

Read `docs/handoff/04-routes-and-screens.md` → "Character detail" and "Cross-book character".

Implement:

1. **`/books/[slug]/characters` — full cast list**
   - Two-column layout: left = filterable list (search by name, filter by role),
     right = detail of the selected character (`?focus=`).
   - On mobile, list and detail are stacked pages.
2. **`/books/[slug]/characters/[charId]` — in-book character page**
   - Header: avatar (xl), name (display font), AKA, role, tag badges.
   - Two-column body: bio + quotes on the left, relations + appearances on the right.
   - `Edit` button → opens an editor `Sheet` (only if user has perms; show but
     disable otherwise).
3. **`/characters/[slug]` — cross-book character**
   - Same header but no book breadcrumb.
   - "Appears in" grid (12 covers + more).
   - "Recurring relations" with per-book counts.
   - AI: archetype + similar-characters card + 1–2 quotes.
   - Follow button → `POST /characters/:id/follow`.

## Acceptance

- All 3 routes render with fixture data.
- The `Edit` sheet uses superforms with optimistic UI on PATCH.
- Following a character toggles the button state and persists across refresh.
