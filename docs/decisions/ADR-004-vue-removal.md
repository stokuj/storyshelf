# ADR-004: Usunięcie Vue 3 SPA jako pierwsza akcja Phase 3.0

**Status:** Zaakceptowane
**Data:** 2026-05-23
**Supersedes:** brak

## Kontekst

Phase 3.0 (migracja na SvelteKit) wymaga decyzji co zrobic z istniejacym Vue frontendem. Trzy opcje rozwazane podczas brainstormingu Phase 2.0 (2026-05-23):

1. **Okres przejsciowy** — Vue + Svelte zyja rownolegle, Caddy routuje po sciezce / nagłowku, uzytkownik dostaje stary albo nowy UI w zaleznosci od feature flag.
2. **Soft remove** — Vue zostaje w repo jako `frontend-legacy/`, ale nie jest budowane ani serwowane.
3. **Hard remove** — `rm -rf frontend/`, usuniecie serwisu Docker, czysciec konfiguracji w jednym commicie.

Vue jest traktowany jako **tymczasowy** od dnia podjecia decyzji o migracji na Svelte (roadmap 2026-05-22). Brak konsumentow zewnetrznych, brak SLA, brak okresu wsparcia. Trzymanie kodu ktory nigdy nie wroci to dlug techniczny i ryzyko nieintencjonalnego deployu starego UI.

## Opcje rozważone

| Opcja | Plus | Minus |
|---|---|---|
| Okres przejsciowy | Mozliwosc A/B, rollback | Caddy routing-kazoo, podwojny build CI, podwojny powierzchni bug |
| Soft remove | Latwy rollback, historia git zachowana | "Martwy" kod w repo myli przyszle agenty/devow; trzeba pamietac zeby go nie modyfikowac |
| Hard remove | Czystosc, jasna intencja | Brak rollback bez `git revert` (akceptowalne — historia git zostaje) |

## Decyzja

**Hard remove w jednym commicie** jako **pierwsza akcja Phase 3.0** (przed `mkdir frontend-svelte/`). Phase 2.0 niczego nie kasuje — Vue zostaje w pelni funkcjonalny do konca Phase 2. Phase 2.0 jedynie przygotowuje fundament (CORS, snapshot API) zeby Phase 3.0 mogla zaczac od `rm -rf frontend/`.

### Checklista do wykonania w Phase 3.0 (commit `chore: remove vue frontend`)

- [ ] `rm -rf frontend/` — cala Vue 3 SPA (`src/`, `tests/`, `vite.config.js`, `package.json`, `Dockerfile.prod`, `Dockerfile.dev`)
- [ ] `infra/compose/docker-compose.dev.yml` — usun serwis `frontend` / `vue`
- [ ] `infra/compose/docker-compose.prod.yml` — usun serwis `frontend` / `vue`
- [ ] `infra/caddy/Caddyfile` (lub odpowiednik) — root `/` → vue zamien na placeholder (`respond "Migration in progress"`) lub od razu skieruj na nowy build Svelte jezeli juz gotowy
- [ ] `Makefile` — sprawdz cele `dev-up` (output mentions `localhost:5173`); zaktualizuj/usun
- [ ] `.github/workflows/ci.yml` — usun step `build-and-push` dla `ghcr.io/stokuj/storyshelf-frontend:main` (linie 69-74 wg stanu z Phase 2.0)
- [ ] `CLAUDE.md` — sekcja `## Komendy → Frontend (z frontend/)` — zaktualizuj na komendy Svelte (lub `[do dodania w Phase 3.x]`)
- [ ] `docs/ARCHITECTURE.md` — tabela Tech Stack: `Vue 3 + Vite` → `SvelteKit`; sekcja "Przepływ danych" przemianowac `Vue 3 (Nginx)` na `Svelte (Nginx)`
- [ ] `docs/ROADMAP.md` — przeniesc pkt 5 "Migracja frontendu Vue 3 → Svelte" do "Zrobione"
- [ ] Backend bez zmian — CORS juz przygotowane w Phase 2.0 na cross-origin Svelte

## Konsekwencje

- **Brak rollback bez `git revert`** — akceptowalne, historia git jest pelna i tagujemy commit `pre-vue-removal` przed wykonaniem
- **Brak okresu przejsciowego** — w momencie deployu Phase 3.0 uzytkownik dostaje albo stary Vue (przed deployem), albo nowy Svelte (po). Akceptowalne dla hobby projektu bez SLA
- **JWT cookies juz cross-origin gotowe** (Phase 2.0, ADR-001 + ten ADR): Svelte hostowany na osobnym origin nie wymaga zmian w backendzie
- **API kontrakt jako test** (Phase 2.0): Svelte konsumuje `docs/api/openapi.yml` przez `openapi-typescript` — rozjazd backend ↔ frontend wykrywany w CI, nie w runtime

## Linki

- Spec: `docs/superpowers/specs/2026-05-23-phase2.0-foundation.md` (Obszar 3)
- Plan: `docs/superpowers/plans/2026-05-23-phase2.0-foundation.md` (Task 6)
- Powiazany ADR: [ADR-001](ADR-001-jwt-httponly-cookies.md) — JWT cookies (zostaja, Svelte ich uzywa)
- Roadmapa: `docs/ROADMAP.md` pkt 5 "Następne"
