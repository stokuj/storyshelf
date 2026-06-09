# Holistyczny audyt projektu — subagenci Sonnet (design / spec)

> Status: zatwierdzony 2026-06-09. Gałąź: `chore/holistic-audit`.
> Wzorzec: M10 (audyt → raport → spec fixów → `/writing-plans` → implementacja).
> Następny krok po akceptacji specki: wykonanie audytu wg tego dokumentu.

## Cel

Pełny audyt repo po M11–M14. Ostatni pełny audyt był przy M10 (2026-06-04, PR #73);
od tego czasu doszły: M11 (discover users), M12 (social feed + reakcje), M13 (AI
characters: Celery+Redis+OpenRouter), M14 (typed relations). Audytujemy: poprawność,
aktualność wzorców, martwy kod, overengineering, security, spójność docs i jakość testów.

**Model pracy:** subagenci Sonnet skanują z wysoką czułością (false-positives
akceptowane i pożądane — lepiej zgłosić za dużo niż przegapić), główny agent (Fable)
weryfikuje każdy finding w kodzie i wydaje werdykt. Subagenci **read-only** — żadnych
edycji, audyt odbywa się na working tree gałęzi audytu (stan = `main`).

## Produkt

1. **Raport:** `docs/superpowers/specs/2026-06-09-holistic-audit-report.md` — pełna
   lista findings z werdyktami, w tym odrzucone (z uzasadnieniem odrzucenia).
2. **Spec fixów:** osobny plik w `docs/superpowers/specs/` — tylko confirmed findings,
   pogrupowane Blocker/Important/Nit, każdy z krokiem weryfikacji. Idzie w normalny
   cykl `/writing-plans` → implementacja po akceptacji użytkownika.

Oba commitowane na gałęzi audytu; spec/plan usuwane przed PR wg konwencji projektu.

## Poza zakresem

- Konfiguracja wdrożenia produkcyjnego (deploy step `ci.yml`, Let's Encrypt, sekrety,
  `CORS_ALLOWED_ORIGINS`, `JWT_COOKIE_DOMAIN`) — wg ROADMAP osobny temat.
- Znane intencjonalne NIT-y z M10 (stale `finish_date` przy round-tripie statusu,
  `time_on_shelf_days` od `created_at`) — udokumentowane decyzje, nie zgłaszamy ponownie.
- Nowe funkcje — audyt niczego nie dodaje, tylko znajduje problemy w istniejącym.

## Przebieg

### Krok 0 — baseline

`make verify` (testy backend `DJANGO_ENV=dev` + ruff + svelte-check + eslint/prettier)
na czystym stanie gałęzi. Cel: odróżnić „znalezione w audycie" od „już było zepsute"
i mieć punkt odniesienia dla specki fixów. Wynik baseline'u zapisany w raporcie.

### Faza 1 — 5 agentów obszarowych (Sonnet, równolegle, read-only)

| # | Agent | Teren | Na co poluje |
|---|-------|-------|--------------|
| 1 | backend | `backend-django/` | wzorce Django 6 / DRF, N+1 i missing select/prefetch_related, martwy kod (nieużywane serializery/pola/utils), overengineering, security (permissiony, gating `profile_public`, throttling, walidacja inputu LLM w `characters/`), spójność stylu między appkami |
| 2 | frontend | `svelte-frontend/src/` | idiomy Svelte 5 (runes; znane gotchas: writable `$derived` + mutacje in-place, unmount dropdownu), martwe komponenty/typy/utils, duplikacja, obsługa błędów API, a11y |
| 3 | infra/CI | `infra/`, `.github/`, `Makefile`, Dockerfiles | dryf compose dev/prod, Caddy, env vars (w tym nowe Redis/OpenRouter), CI vs `make verify`, sieroty po starych etapach |
| 4 | docs | `docs/` vs kod | ARCHITECTURE/ROADMAP/ADR-y vs rzeczywisty stan (znany przykład: brak M14 w ROADMAP), stale przykłady, martwe odnośniki, nieaktualne komendy |
| 5 | testy | `backend-django/*/tests/`, `svelte-frontend/e2e/` | luki pokrycia (zwłaszcza M13/M14), kruche wzorce, martwe fixtures, jakość asercji, dryf E2E vs aktualne UI |

**Format zgłoszenia (wspólny dla wszystkich agentów):**

```
- [WAGA: blocker|important|nit] [CONFIDENCE: high|med|low]
  Claim: <jedno zdanie, co jest nie tak>
  Dowód: <file:line + krótki cytat/uzasadnienie>
  Sugestia: <opcjonalnie, jak naprawić>
```

Instrukcja dla agentów wprost: „zgłaszaj też niepewne podejrzenia — od odsiewu jest
adjudykator; nie edytuj żadnych plików; cały wynik w finalnej wiadomości".

### Adjudykacja (główny agent, po każdej fazie)

Każdy finding weryfikowany w kodzie (Read/Grep, nie na słowo agenta). Werdykty:

| Werdykt | Znaczenie |
|---------|-----------|
| confirmed | problem realny → trafia do specki fixów |
| false-positive | agent się myli; w raporcie z uzasadnieniem |
| intentional | świadoma, udokumentowana decyzja (ADR / ROADMAP / memory) |
| out-of-scope | realne, ale poza zakresem (np. deploy prod) → notka w raporcie, ewentualnie ROADMAP „Kiedyś" |

### Faza 2 — agenci celowani (1–3, Sonnet, read-only)

- **Slot stały: agent kontraktu API** — `svelte-frontend/src/lib/api/*.ts` ↔ serializery
  DRF ↔ `docs/api/openapi.yml` ↔ sekcja API w ARCHITECTURE. Łapie rozjazdy między
  warstwami, których nie widzi żaden agent obszarowy (pola w typie TS bez odpowiednika
  w serializerze i odwrotnie, endpointy w docs bez implementacji itd.).
- **0–2 sloty wg luk z fazy 1:** decyzja głównego agenta po pierwszej adjudykacji —
  np. głębsza weryfikacja hipotezy przekrojowej albo obszar, gdzie agent fazy 1 zwrócił
  podejrzanie mało/dużo. Jeśli faza 1 nie wskaże luk, faza 2 = sam agent kontraktu.

Po fazie 2 — druga runda adjudykacji, dopisanie do raportu.

### Krok końcowy — raport + spec fixów

1. Raport z pełną listą (confirmed + odrzucone z uzasadnieniem) + wynik baseline.
2. Spec fixów (tylko confirmed, Blocker/Important/Nit, każdy punkt z weryfikacją).
3. Commit obu na gałęzi → użytkownik recenzuje spec fixów → `/writing-plans`.

## Kryteria sukcesu

- Każdy finding z faz 1–2 ma w raporcie werdykt z uzasadnieniem — nic nie ginie.
- Spec fixów zawiera wyłącznie pozycje zweryfikowane przez głównego agenta w kodzie.
- Zero zmian w kodzie aplikacji na etapie audytu (tylko docs na gałęzi audytu).
- Baseline `make verify` udokumentowany przed fazą 1.
