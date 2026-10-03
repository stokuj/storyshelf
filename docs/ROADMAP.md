# Roadmapa StoryShelf

> Stan: 2026-10-03. Aktualizowane ręcznie. Nie automatyzowane.

---

## Aktualny krok (next action for any Claude session)

**PIVOT 2026-10-03:** StoryShelf przestaje być trackerem czytania. Staje się **prywatną wiki o książkach (OKF v0.2) pisaną przez Agenta LLM razem z Userem**. Patrz [CONTEXT.md](../CONTEXT.md), [ADR-004](decisions/ADR-004-wiki-okf-pages-in-postgres.md), [ADR-005](decisions/ADR-005-react-vite-spa.md), [ARCHITECTURE](ARCHITECTURE.md).

**ZADANIE:** **W0 — makiety** kluczowych ekranów (jaśniejsza wersja stylu starego frontendu). Po akceptacji makiet: `/brainstorming` → spec **W1**.

Kod na `main` to wciąż stary tracker (M1–M14). Tabela niżej to historia sprzed pivotu.

---

## Zrobione

| Etap | Zakres | Wynik |
|------|--------|-------|
| Migracja z Java Spring Boot | Backend przepisany na Django + DRF | `backend-django/`, legacy `backend/` usunięty |
| JWT przez HttpOnly cookies | Migracja z localStorage, `JWTCookieAuthentication`, silent refresh | [ADR-001](decisions/ADR-001-jwt-httponly-cookies.md) |
| Django audit fixes | validators, unique constraints, signals, lint config | — |
| SDD docs restructure | Wprowadzenie struktury `docs/` (ARCHITECTURE, ROADMAP, decisions/) + integracja z plugin superpowers | PR #43 |
| M1 Auth + profil | Register, login, profile/settings, public profile, follow | ✅ zmergowane do main |
| M2 Katalog książek | Books API (paginacja, slug, filtry/search/sort), SvelteKit frontend (/discover, /books/[slug]), E2E | ✅ zmergowane do main (PR #60) |
| PRE-M3 cleanup | Usunięcie AI/Celery kodu (analysis, reviews, shelf apps), uproszczenie infra do 3 kontenerów | ✅ branch fix/pre-m3-cleanup |
| M3 Rating + Shelf | `ratings/` (PUT-upsert, sygnał → avg_rating), `shelf/` (ShelfEntry CRUD, status, current_page), frontend `/shelf` + kontrolki na `/books/[slug]`, E2E | ✅ zmergowane do main (PR #62 + post-M3 fixes #63) |
| M4 Reviews | `reviews/` (Review = body, unique user+book, PUT-upsert, publiczna lista, `/me`, owner-only delete, `author_rating` z Rating via Subquery), eksport danych, frontend sekcja recenzji na `/books/[slug]` (LoadMore), E2E (4 scenariusze) | ✅ zmergowane do main (PR #64 + poprawki po review #65–#67) |
| M5 Custom shelves | `shelf/` (Shelf + ShelfMembership obok ShelfEntry; owner CRUD `/api/shelves/`, membership add/remove idempotentne, publiczny odczyt `/api/u/{handle}/shelves/` bramkowany `profile_public`), eksport danych, frontend (zakładka „Moje półki" na `/shelf`, `/shelf/[slug]`, kontrolka na `/books/[slug]`, publiczny `/u/[handle]/shelves/[slug]`), E2E (4 scenariusze) | ✅ zmergowane do main (PR #68) |
| Google Books import | `import_books` management command (CLI) — import po ISBN, dedup+update po `isbn`, `categories` → split na osobne `genres`, reuse `BookWriteSerializer`, stdlib `urllib` (zero nowych deps); `--file`, `--dry-run`; M2M (authors/genres/tags) zachowane gdy Google ich nie zwróci; testy z mockiem `urlopen` | ✅ zmergowane do main (PR #69) |
| Audyt + cleanup | Audyt dokumentacji/infra (subagenci), `.env`→`infra/`, Caddy/porty/ścieżki, fixy B1/S1/B2 + F1/F3, usunięcie dead code; usunięcie `.claude/` ze śledzenia remote | ✅ zmergowane do main (PR #70) |
| M6 Follow/obserwowanie (UI) | Profil: `followers_count`/`following_count`/`is_following` (annotacje + SerializerMethodField), `FollowUserSerializer` (wzbogacone listy), optymistyczny `FollowButton` (writable `$derived`, revert na realny błąd), klikalne liczniki, trasy `/u/[handle]/followers` i `/following` (`UserRow`/`FollowList`); E2E follow flow + gość-bez-przycisku; OpenAPI snapshot zregenerowany | ✅ zmergowane do main (PR #71) |
| M8 Half-wired stories | Eksport danych (download ZIP), upload avatara, `current_page` jako progress czytania — wszystkie trzy okazały się już w pełni podpięte we froncie | ✅ zrobione wcześniej przy audycie (PR #70); M8 zamknięte bez osobnej pracy 2026-06-04 |
| M9 Statystyki czytania | `GET /api/users/me/stats/` (auth, own-only) + `users/stats.py::build_user_stats` (liczby per status, książki/rok z `finish_date`, rozkład ocen, time-on-shelf); auto-set `ShelfEntry.finish_date` na przejściu do READ; frontend `/stats` + ręczny `BarChart` (zero deps); E2E `stats.spec.ts`; OpenAPI zregenerowany | ✅ zmergowane do main (PR #72) |
| M10 Audyt / fix / cleanup | Audyt subagentami M6–M9: usunięcie `total_books` (redundantne), konsolidacja prefiksu follow → `/api/u/`, klikalne linki autor recenzji + gatunki (`ReviewCard`/`BookHeader`), sync `ARCHITECTURE.md`/`ROADMAP.md`, usunięcie martwego duplikatu `backend-django/docs/api/openapi.yml` | ✅ zmergowane do main (PR #73) |
| M11 Discover users + cudza półka | `GET /api/users/` (lista publicznych profili: paginacja, `?search=`, `?ordering=`, filtr `profile_public`) + publiczny odczyt domyślnej półki `GET /api/u/{handle}/shelf/` (bramkowane `profile_public`); frontend `/users` + sekcja „Reading" na `/u/[handle]` + nav „People"; fix enum `ShelfEntryStatusEnum` | ✅ zmergowane do main (PR #74) |
| M12 Social feed + reakcje | App `feed/` (`GET /api/feed/`, auth, merge w locie Rating/Review/ShelfEntry obserwowanych z `profile_public=True`, cursor `?before=`); polubienia recenzji (`ReviewLike`, `POST/DELETE /api/reviews/{id}/like/`, `likes_count`/`is_liked`); publiczne recenzje `GET /api/u/{handle}/reviews/` (paginowane, bramkowane); `ShelfEntry.finished_at` (stabilny sort „finished", zastąpił `updated_at` po review); refactor `users/selectors.py::public_owner_or_404` (dedup gatingu shelf+reviews); frontend `/feed` + `FeedItem`, lajk na `ReviewCard` (optimistic), sekcja Reviews na `/u/[handle]` (load-more), nav „Feed"; E2E `social-feed.spec.ts` (3 scen.); OpenAPI zregenerowany | ✅ zmergowane do main (PR #75) |
| M13 AI Character Analysis | app `characters/` (Celery+Redis, OpenRouter); sekcja postaci pod książką (karty monogram), podstrona postaci + ego-graf relacji; `POST .../generate/` async (throttle `character_generate`), publiczny odczyt; ADR-003 | ✅ zmergowane do main (PR #77) |
| M14 Typed character relations | Enum RelationType (~20 typów / 7 grup) zamiast free-text label, unique (from, to, type), kolorowy ego-graf z pigułkami i legendą, hardening walidacji LLM | ✅ zmergowane do main (PR #78) |

## Następne (wiki — kolejność wiążąca)

> Każdy etap: `/brainstorming` → spec → plan → implementacja na własnej gałęzi → PR.

| Etap | Zakres |
|------|--------|
| **W0 — Makiety** | Statyczne makiety: panel Books/Characters/Places/Universes, Strona książki z Wzmiankami (badge), czat z Agentem (Kandydat), pusta Strona + „Generuj", Propozycja z diffem, Historia, Profil. Bez backendu. |
| **W1 — Fundament wiki (backend)** | Usunięcie starych apps/modeli (books, library, ratings, shelf, reviews, feed, characters, follow); model Page / PageVersion / Proposal per User; parser + walidacja OKF (frontmatter, `type`); Szablony 4 typów; API Stron, Historii i Edycji; Profil (o mnie + Ulubione, przełącznik publiczny); eksport pakietu OKF. |
| **W2 — Frontend React** | Usunięcie `svelte-frontend/`; nowy Vite SPA (ADR-005): auth (cookies), panel boczny, render Strony (react-markdown + badge), Edycja, Historia, Profil; E2E. |
| **W3 — Agent: dodawanie i Generowanie** | Czat (SSE) → Kandydaci (LLM + Google Books/OpenLibrary) → Strona z Szablonu; Generowanie (Celery + OpenRouter) treści, Wzmianek oraz Stron Postaci/Miejsc per książka; Propozycje na prośbę Usera (diff, akceptuj/odrzuć). |

## Później (po W3, bez kolejności)

- Postacie/Miejsca per **Uniwersum**: scalanie `geralt--x` + `geralt--y` → `/characters/geralt.md` (migracja A→C)
- Strony **Autorów** (i analogicznie pod Uniwersum)
- Propozycje jako skutek uboczny pracy nad inną Stroną (cross-page)
- Źródła Agenta stopniowo: web search, Wikipedia, Reddit, zewnętrzne API, fragmenty książki (OKF `sources`)
- Chatbot „w której książce było…": chunkowanie + embeddingi w **pgvector**
- **Mapa relacji** (graf z Odnośników; Cytoscape / React Flow)
- Udostępnianie Wiki; linki z kart Ulubionych na publicznym Profilu
- Współdzielenie wspólnej treści między Wiki (cięcie kosztów LLM)
- Rozbudowa Szablonów o kolejne sekcje
- **Wdrożenie produkcyjne** (Caddy + Let's Encrypt, VPS, deploy step w `ci.yml`)

## Czego NIE robimy

- **Recenzje, oceny, półki, statystyki czytania, follow, feed**: usunięte przy pivocie (decyzja 2026-10-03)
- **Wspólna, edytowana społecznie Wiki** (model Wikipedii): każdy User ma własną Wiki
- **SSR / SEO**: Wiki i Profil są prywatne (ADR-005)
- **Real-time collaboration**: brak live cursors i wspólnego edytora
- **Native mobile (iOS/Android)**: PWA wystarczy
- **Subskrypcje / płatności**: projekt hobbystyczny / portfoliowy

## Konwencja aktualizacji

- Nowy etap zaczyna się od `/brainstorming` → spec w `docs/superpowers/specs/`
- Po zakończeniu przesuwamy etap do **Zrobione** + link do ADR (jeśli powstał)
- „Czego NIE robimy" jest **immutable jak ADR**: zmiana wymaga osobnego brainstormingu (ostatnia: grilling pivotu 2026-10-03)
