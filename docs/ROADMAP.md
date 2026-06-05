# Roadmapa StoryShelf

> Stan: 2026-06-05. Aktualizowane ręcznie. Nie automatyzowane.

---

## Aktualny krok (next action for any Claude session)

**Bieżący branch:** `main` (M12 zmergowane PR #75; M11 PR #74).

**ZADANIE:** Brak aktywnego milestone — **M11 i M12 zamknięte**, lista „Następne" wyczerpana. Pozostaje jedynie **wdrożenie produkcyjne** (odłożone na decyzję użytkownika; osobny temat, nie milestone — patrz „Po M11–M12"). Ewentualny kolejny kierunek to kandydaci z „Kiedyś" (np. M13: spersonalizowana strona główna `/`). Każdy nowy milestone = osobny `/brainstorming` → spec → plan → implementacja.

**M8 zamknięte bez nowej pracy (2026-06-04):** Wszystkie trzy historie (eksport danych z download, upload avatara, `current_page` jako progress czytania) okazały się już w pełni podpięte na `main` — zrobione przy okazji audytu/cleanup (PR #70), po dacie audytu który je oznaczył jako half-wired. Zweryfikowane w kodzie: `settings/data/export/+server.ts` (proxy ZIP) + przycisk; `settings/+page.svelte` avatar `onchange`→`requestSubmit` + akcja `avatar`; `ShelfBookCard.svelte` input strony + `/shelf/+page.svelte` `handleProgressChange` (optymistyczny revert). Pozostałości poza zakresem M8: brak kontrolki progresu na `/books/[slug]`, navbar Search no-op — do ewentualnego „Kiedyś".

**M7 odłożone (2026-06-04):** Osobny panel importu w SvelteKit uznany za przekomplikowany — import książek to rzadka, jednorazowa czynność robiona przez właściciela, a działają już CLI `import_books <isbn>` i Django admin (`/admin/`, staff-only). Gdy wróci, najpewniej w formie lekkiej **opcji A: przycisk/akcja „Import from Google Books" w Django adminie** (pole ISBN → reuse logiki importu), bez nowego API i tras we froncie. Pełny panel w SvelteKit tylko jeśli pojawią się nietechniczni admini bez dostępu do `/admin/`.

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

## W toku

Brak aktywnego milestone. M11–M12 zamknięte; lista „Następne" wyczerpana. Otwarte tylko **wdrożenie produkcyjne** (decyzja użytkownika — patrz „Po M11–M12") oraz kandydaci z „Kiedyś".

**Decyzja 2026-05-25:** profil publiczny/prywatny — bool `profile_public`, bez 3-state friends/private.

**Decyzja 2026-06-03:** faza post-MVP = M6–M10 (Follow UI, Admin import UI, dokończenie half-wired stories, statystyki czytania, audyt/cleanup). Każdy milestone osobna specka. Wdrożenie produkcyjne dopiero po M10.

## Następne (priorytetyzowane)

> Każdy milestone: osobny `/brainstorming` → spec w `docs/superpowers/specs/` → plan → implementacja na własnej gałęzi → PR. Kolejność wiążąca.

| Milestone | Zakres | Gałąź |
|-----------|--------|-------|
| ~~**M11 — Discover users + cudza półka**~~ ✅ ZROBIONE (PR #74) | `GET /api/users/` (lista publicznych profili: paginacja, `?search=` po handle/display_name, `?ordering=`, filtr `profile_public`) + publiczny odczyt domyślnej półki `GET /api/u/{handle}/shelf/` (ShelfEntry, status/postęp, bramkowane `profile_public`); frontend `/users` (reuse `UserRow`/`FollowList`/`FollowButton` z M6) + sekcja „Reading" na `/u/[handle]`. Domyka M6 Follow — daje *jak* znaleźć userów. Decyzja do brainstormingu: publiczna półka = tylko domyślna `ShelfEntry` czy też custom (te już publiczne z M5). | `feat/m11-user-discovery` |
| ~~**M12 — Social feed + reakcje**~~ ✅ ZROBIONE (PR #75) | Feed aktywności obserwowanych `GET /api/feed/` (ocena / recenzja / skończona książka; liczony „w locie" z Rating/Review/ShelfEntry, bez modelu `Activity`; bramkowane `profile_public`), publiczne recenzje na profilu `GET /api/u/{handle}/reviews/`, polubienia recenzji (`ReviewLike` unique user+review, `POST/DELETE /api/reviews/{id}/like/`, `likes_count`+`is_liked`); frontend `/feed` + sekcja recenzji na `/u/[handle]`. Zależała od M11. YAGNI: bez powiadomień, komentarzy, repostów. | `feat/m12-social-feed` |
| ~~**M7 — Import książek z UI admina** (A2)~~ **ODŁOŻONE** | Panel w SvelteKit uznany za przekomplikowany (patrz „Aktualny krok"). Wróci najpewniej jako lekki przycisk w Django adminie (opcja A). Działają już CLI `import_books` i Django admin. | `—` (gałąź `feat/m7-admin-import-ui` zostawiona pusta) |

Po M11–M12:

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt, sekrety na VPS (DigitalOcean). Wymaga konfiguracji `CORS_ALLOWED_ORIGINS` i `JWT_COOKIE_DOMAIN`.

## Kiedyś (bez priorytetu)

- Rekomendacje (collaborative + content-based)
- System tagowania społecznościowego (tagi user-defined poza adminem)
- Importer książek z OpenLibrary / Goodreads (CSV z Goodreads, ISBN→OpenLibrary; Google Books — zrobione, patrz „Zrobione")
- PWA (krok przed natywnym mobile)
- ~~Lista userów `/users` + cudza półka~~ → awansowane do **M11** (patrz „Następne")
- ~~Social: feed, recenzje publiczne, polubienia~~ → awansowane do **M12** (patrz „Następne")
- Spersonalizowana strona główna `/` (Continue reading, aktywność followowanych, rekomendacje; dla gości trending + opis apki) zamiast redirectu na `/discover` — naturalny kandydat na M13 po M11/M12
- Rozszerzenia statystyk (po M9): reading streak (dni z rzędu), yearly wrap
- AI — analiza książek (karty postaci, graf relacji, tematy/ton; per-book LLM call + pgvector) — **poza MVP**, patrz „Czego NIE robimy"
- ML/DE do CV: semantic search + embeddingi (sentence-transformers + pgvector), pipeline analityczny w dbt, Character Knowledge Graph (NetworkX + LLM extraction)

## Czego NIE robimy

- **Skala >10k książek na jedną instancję** — projekt single-tenant, nie marketplace
- **Real-time collaboration** — żadnych live cursors, presence, edytora wspólnego
- **Native mobile (iOS/Android)** — PWA wystarczy
- **AI/LLM w MVP** — brak Celery, RabbitMQ, Redis; NLP/AI pipeline odłożone poza M5
- **Subskrypcje / płatności** — projekt hobbystyczny / portfoliowy

## Konwencja aktualizacji

- Nowy etap zaczyna się od `/brainstorming` → spec w `docs/superpowers/specs/`
- Po zakończeniu przesuwamy wpis z **W toku** do **Zrobione** + dopisujemy link do ADR (jeśli powstał)
- "Następne" przeglądamy raz na kilka etapów — kolejność może się zmieniać
- "Czego NIE robimy" jest **immutable jak ADR** — wykreślenie wymaga osobnego brainstormingu
