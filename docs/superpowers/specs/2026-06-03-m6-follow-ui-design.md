# M6 — Follow/obserwowanie userów (UI) — Design

> Spec dla milestone M6. Workflow: brainstorming → **spec (ten plik)** → writing-plans → impl.
> Gałąź: `feat/m6-follow-ui`.

## Cel

Dać UI dla istniejącego backendu `UserFollow`: przycisk Follow/Unfollow na profilu publicznym,
liczniki followers/following oraz podstrony z listami. Backend follow (akcje + listy) już istnieje;
M6 dokłada UI **plus drobne dodatki backendowe** (kilka pól w serializerach), bo profil publiczny
nie zwraca jeszcze liczników ani flagi `is_following`, a listy zwracają tylko `handle`.

## Stan wyjściowy (co już jest)

- `POST/DELETE /api/users/{handle}/follow/` — follow/unfollow (auth). 400 self, 409 already, 404 not-following.
- `GET /api/users/{handle}/followers/` i `/following/` — płaska lista (`pagination_class=None`),
  bramkowane `profile_public` (404 dla prywatnego, gdy widz ≠ właściciel).
  Obecny `FollowSerializer` zwraca tylko `id, follower_handle, following_handle, followed_at`.
- `GET /api/u/{handle}/` — `UserProfileSerializer`: `handle, display_name, bio, avatar_url, member_since, profile_public`.
  **Brak** liczników i `is_following`.
- Front: `routes/u/[handle]/+page.{server.ts,svelte}` (profil), `lib/api/_client.ts` (`apiFetch`),
  `lib/components/Avatar.svelte`, `svelte-sonner` (toasty).

## Zakres (user stories)

- **US-6.1** — Jako zalogowany user (nie-właściciel) na `/u/[handle]` widzę przycisk **Follow/Unfollow** i mogę zmienić stan.
- **US-6.2** — Na profilu widzę **liczniki** followers/following (klikalne) i mogę wejść na **podstrony list**.

### Poza M6 (→ ROADMAP „Kiedyś")
Podgląd aktywności czytelniczej innych, lista `/users`, paginacja list, inline follow na wierszach,
powiadomienia, feed.

## Decyzje projektowe (zatwierdzone)

1. **Listy** = osobne podstrony `/u/[handle]/followers` i `/u/[handle]/following`; liczniki na profilu są linkami.
2. **Gość (niezalogowany)** — widzi liczniki i listy (read-only); **przycisk Follow ukryty** (brak redirectu).
3. **Wiersze list** — tylko link do `/u/[handle]` (Avatar + display_name + @handle); **bez** inline Follow → serializer listy nie potrzebuje per-wiersz `is_following`.
4. **Przycisk** — **optymistyczna aktualizacja** (`is_following` + `followers_count` ±1), w tle `apiFetch`; **błąd sieci/5xx → revert** + toast. Bez pełnego reloadu.
5. **Liczniki** — annotacje/`Count` w serializerze profilu.
6. **Bez paginacji** list w M6 (flat list zostaje).

## Zmiany backendowe

| Plik | Zmiana |
|------|--------|
| `users/serializers.py` `UserProfileSerializer` | + `followers_count`, `following_count`, `is_following`. Liczniki przez `Count` (annotacja w `UserProfileView.get_queryset`), by uniknąć N+1. `is_following`: `SerializerMethodField` — `True` gdy `request.user.is_authenticated` i istnieje `UserFollow(follower=request.user, following=obj)`; `False` dla anona, self, nie-obserwującego. |
| `users/serializers.py` | nowy `FollowUserSerializer` — zwraca **drugą stronę** relacji: `{handle, display_name, avatar_url, followed_at}`. Którą stronę → z `self.context["follower_view"]` (`True` → `obj.follower`, `False` → `obj.following`). `avatar_url` budowane z `request` w kontekście (jak w `UserProfileSerializer`). |
| `users/views.py` `UserProfileView` | annotacja liczników w `get_queryset`; `is_following` korzysta z `request` w kontekście serializera (już przekazywany). |
| `users/views.py` `FollowListView` | nadpisać `get_serializer_context()` → dodać `follower_view`; użyć `FollowUserSerializer`. `select_related("follower", "following")` już jest. |

> **GOTCHA — `related_name`-y modelu `UserFollow` są odwrócone względem intuicji:**
> - `follower` FK → `related_name="following_set"` (wiersze, gdzie user jest obserwującym = kogo user obserwuje).
> - `following` FK → `related_name="follower_set"` (wiersze, gdzie user jest obserwowanym = kto obserwuje usera).
>
> Zatem:
> - `followers_count` = `Count("follower_set")` (kto obserwuje tego usera),
> - `following_count` = `Count("following_set")` (kogo ten user obserwuje).
>
> W `FollowUserSerializer`: dla `follower_view=True` (lista „kto mnie obserwuje", queryset `UserFollow.objects.filter(following=user)`) pokazujemy `obj.follower`; dla `False` (lista „kogo obserwuję", `filter(follower=user)`) pokazujemy `obj.following`.
>
> Liczniki widoczne tylko dla dostępnych profili — prywatny i tak zwraca 404.

## Zmiany frontendowe

| Plik | Zmiana |
|------|--------|
| `lib/types/user.ts` | + `followers_count: number`, `following_count: number`, `is_following: boolean` |
| `lib/api/follow.ts` (nowy) | `followUser(fetch, handle)` (POST), `unfollowUser(fetch, handle)` (DELETE), `fetchFollowers(fetch, handle, isServerSide?)`, `fetchFollowing(fetch, handle, isServerSide?)` |
| `lib/types/follow.ts` (nowy) | typ `FollowUser { handle; display_name; avatar_url: string \| null; followed_at: string }` |
| `routes/u/[handle]/+page.svelte` | przycisk Follow/Unfollow (gdy `viewer` zalogowany i nie-owner) z optymistycznym stanem; dwa klikalne liczniki (linki `./followers`, `./following`) |
| `routes/u/[handle]/followers/+page.server.ts` + `+page.svelte` (nowe) | SSR load `fetchFollowers` + render `FollowList` |
| `routes/u/[handle]/following/+page.server.ts` + `+page.svelte` (nowe) | j.w. dla `fetchFollowing` |
| `lib/components/FollowList.svelte` (nowy) | render listy `FollowUser[]` + empty state ("No followers yet" / "Not following anyone yet"); przyjmuje tytuł/empty-text przez prop |
| `lib/components/UserRow.svelte` (nowy) | wiersz: `Avatar` + display_name + `@handle`; cały wiersz to link do `/u/[handle]` |

Prywatny profil na podstronach list → backend zwraca 404 → `+page.server.ts` rzuca `error(404, …)` (jak w profilu).

## Obsługa błędów

- Przycisk: błąd sieci (`status: 0`) lub 5xx → revert lokalnego stanu + toast. 409 (already following) / 404 (not following) traktujemy jako osiągnięty stan docelowy (bez revertu — stan i tak zgodny z intencją).
- Listy: 404 → strona błędu (reużyć wzorca z profilu); inny błąd → `error(500, …)`.

## Testy

**Backend** (`DJANGO_ENV=dev`, w kontenerze `storyshelf-django`):
- `UserProfileSerializer`: `followers_count`/`following_count` poprawne; `is_following` dla anon=False, self=False, follower=True, non-follower=False.
- `FollowUserSerializer`: dla `follower_view=True` zwraca dane **followera**, dla `False` — **following**; zawiera `display_name`, `avatar_url`, `handle`, `followed_at`.
- Prywatny profil: listy + profil → 404 dla obcego (już pokryte — potwierdzić).

**Frontend**: `npm run check` + `npm run lint`.

**E2E** (Playwright, 1–2 scenariusze): user A obserwuje B → licznik followers B +1, A widnieje na `/u/B/followers`; unfollow → −1.

## Czego NIE robimy w M6

Paginacji list, inline follow na wierszach, powiadomień, feedu aktywności, listy `/users`, podglądu cudzej półki/aktywności czytelniczej.
