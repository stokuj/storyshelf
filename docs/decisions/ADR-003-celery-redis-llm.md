# ADR-003 — Celery + Redis i zewnętrzny provider LLM (OpenRouter)

> Status: Accepted · Data: 2026-06-06 · Kontekst: M13 AI Character Analysis

## Kontekst

M13 dodaje generację „kart postaci" przez LLM. Jeden call generuje do 12 postaci
+ relacje (15–40 s). Każdy zalogowany user może kliknąć „Generate AI".

## Decyzja

- **Asynchronicznie, nie synchronicznie.** Synchroniczny call blokowałby worker
  webowy na czas generacji — przy wielu równoległych klikach (np. 100) pula
  workerów się wyczerpuje i cała aplikacja przestaje odpowiadać (worker starvation).
- **Celery + Redis** jako kolejka zadań (Redis = broker + result backend). RabbitMQ
  odrzucone jako przerost — niski wolumen, brak potrzeby zaawansowanego routingu.
- **OpenRouter** jako provider (model konfigurowalny przez `OPENROUTER_MODEL`),
  wołany gołym `urllib` (spójnie z `import_books`). Bez LangChain — to jeden
  structured-output call, framework orkiestracji byłby zbędną zależnością.
- **Idempotencja per książka** + bounded worker concurrency jako bezpieczniki:
  jeden job na książkę naraz; do OpenRoutera leci max `--concurrency` (flaga CLI workera w compose).

## Konsekwencje

- +2 elementy infry: kontener `redis` i proces `celery` worker (ten sam obraz django).
- Otwarcie fazy AI projektu — wcześniej „bez AI/Celery" było **odłożone**, nie zakazane.
- **Znane ryzyko (świadomy dług):** „każdy user + regeneracja dozwolona" = otwarta
  furtka kosztowa. Throttle wdrożony: scope `character_generate` 10/h per user
  (commit f524d53), konfigurowalny env `THROTTLE_CHARACTER_GENERATE`.
- Testy: `CELERY_TASK_ALWAYS_EAGER=True` — taski wykonują się synchronicznie, bez workera.
