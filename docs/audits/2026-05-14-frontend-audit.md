# Frontend Audit — 2026-05-14

## Summary

The StoryShelf Vue 3 frontend is well-structured with proper routing, authentication handling, and state management using composables. However, there are critical API contract mismatches between the frontend and Django backend that will cause runtime errors. The frontend lacks comprehensive test coverage with only 2 test files covering ~65 lines of code. Token storage uses localStorage instead of HttpOnly cookies, exposing JWT tokens to XSS attacks.

---

## Critical Issues

**API Contract Mismatches:**

1. **BookDetailView.vue:68-80** — Frontend expects `details.book.rating` but backend serializer returns `avg_rating`. Displays as `undefined` in the UI.

2. **BookDetailView.vue:246** — Frontend displays `relation.relation` but backend `CharacterRelationSerializer` returns `relation_type`. Field name mismatch causes undefined rendering.

3. **BookDetailView.vue:248** — Frontend references `relation.evidence` which does not exist in the backend response. `CharacterRelationSerializer` provides no `evidence` field.

**Token Security:**

4. **api.js:2-3** — Tokens stored in localStorage are vulnerable to XSS. Should use HttpOnly, Secure cookies.

---

## Important Issues

**Test Coverage:**

5. Only 2 test files exist (~65 LOC total). Missing: API layer, router guards, auth flow, complex views, error handling.

**Component Quality:**

6. **BookDetailView.vue:268-397** — 130 LOC handling multiple concerns: book details, shelf management, reviews, characters, relations. Should be split.

7. **ProfileView.vue:105-127** — Multiple parallel async operations without request cancellation. Promises continue executing on unmount.

8. **HomeView.vue:51-66** — Search watcher triggers full reload on each keystroke without debouncing — excessive API calls.

9. **router.js:59-68** — `refreshAuth()` called on every navigation including between public routes. Should refresh once per session.

**Error Handling:**

10. **BookDetailView.vue:335-341** — Review loading has no explicit error handling; `sortedReviews` stays stale with no user feedback on failure.

11. **api.js:46-59** — 401 retry doesn't verify refreshed token is valid before using it.

**Accessibility:**

12. **App.vue:5-38** — Hamburger menu uses `tabindex="0"` with click handler but no keyboard support (Enter/Space). Dropdown lacks `role="menu"` / `aria-orientation`.

---

## Minor Issues

- **vite.config.js:21** — `build.sourcemap: true` in production exposes source code.
- **nginx.conf:13** — CSP uses `'unsafe-inline'` for styles; could use nonce-based approach.
- **App.vue:11** — `aria-label` on hamburger exists but dropdown lacks full ARIA attributes.
- **useAsyncState.js** — No request timeout; network hangs indefinitely.
- **BookCard.vue:30-36** — Defensive author check for both object/string suggests inconsistent backend response shape.

---

## API Contract

| Endpoint | Frontend call | Backend route | Status |
|----------|---------------|---------------|--------|
| GET /api/books/ | `fetchBooks()` | `BookListView` | ✓ |
| GET /api/books/{id}/ | `fetchBookDetails()` | `BookRetrieveView` | **MISMATCH** — returns `avg_rating`, frontend expects `rating` |
| GET /api/reviews/ | `fetchReviews()` | `ReviewListCreateView` | ✓ |
| POST /api/reviews/ | `createReview()` | `ReviewListCreateView` | ✓ |
| PATCH /api/reviews/{id}/ | `updateReview()` | `ReviewDetailView` | ✓ |
| DELETE /api/reviews/{id}/ | `deleteReview()` | `ReviewDetailView` | ✓ |
| GET /api/shelf/ | `fetchBookshelf()` | `ShelfListView` | ✓ |
| POST /api/shelf/{id}/ | `addToBookshelf()` | `ShelfEntryView` | ✓ |
| PATCH /api/shelf/{id}/ | `updateBookshelfStatus()` | `ShelfEntryView` | ✓ |
| DELETE /api/shelf/{id}/ | `removeFromBookshelf()` | `ShelfEntryView` | ✓ |
| POST /api/auth/login/ | `loginUser()` | `LoginView` | ✓ |
| POST /api/auth/register/ | `registerUser()` | `RegisterView` | ✓ |
| POST /api/auth/refresh/ | `refreshAccessToken()` | `TokenRefreshView` | ✓ |
| GET /api/auth/me/ | `fetchAuthMe()` | `AuthMeView` | ✓ |
| GET /api/users/me/ | `fetchCurrentUserSettings()` | `UserSettingsView` | ✓ |
| PUT /api/users/me/ | `updateCurrentUserSettings()` | `UserSettingsView` | ✓ |
| PATCH /api/users/me/visibility/ | `updateCurrentUserVisibility()` | `UserVisibilityView` | ✓ |
| GET /api/users/{username}/ | `fetchUserProfile()` | `UserProfileView` | ✓ |
| GET /api/users/{username}/followers/ | `fetchFollowers()` | `FollowListView` | ✓ |
| GET /api/users/{username}/following/ | `fetchFollowing()` | `FollowListView` | ✓ |
| POST /api/users/{username}/follow/ | `followUser()` | `UserFollowView` | ✓ |
| DELETE /api/users/{username}/follow/ | `unfollowUser()` | `UserFollowView` | ✓ |
| CharacterRelation fields | `relation.relation`, `relation.evidence` | `CharacterRelationSerializer` | **MISSING** — returns `relation_type`, no `evidence` field |

---

## Metrics

- Vue files: 11 (7 views + 4 components)
- Test files: 2 (~65 LOC)
- Views: 7 | Components: 4 | Composables: 1
- Total frontend LOC: ~1 232
- Test coverage: ~5%
- Runtime dependencies: 2 (vue, vue-router)
- Dev dependencies: 8

---

## Priority Recommendations

1. **CRITICAL** — Fix API mismatches: `avg_rating`→`rating`, `relation_type`→`relation`, add/remove `evidence` field
2. **CRITICAL** — Migrate JWT from localStorage to HttpOnly cookies (requires backend CSRF config)
3. **HIGH** — Add test coverage: API layer, router guards, BookDetailView, auth flow (target 60%+)
4. **HIGH** — Add request cancellation (AbortController) in ProfileView and BookDetailView
5. **HIGH** — Refactor BookDetailView: extract ReviewForm, ReviewsList, CharactersTable, RelationsTable
6. **MEDIUM** — Debounce search query watcher in HomeView
7. **MEDIUM** — Refresh auth once per session, not on every navigation
8. **MEDIUM** — Disable sourcemaps in production build
9. **LOW** — Improve ARIA support on hamburger menu and dropdowns
10. **LOW** — Add request timeout in `useAsyncState`
