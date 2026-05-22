# ADR-002: Dwa osobne workery Celery — prefork dla NER, gevent dla LLM

**Status:** Zaakceptowane
**Data:** 2026-05-13
**Supersedes:** wcześniejszy design z 5 taskami Celery i jednym typem workera

## Kontekst

Pipeline NLP ma dwa etapy o radykalnie różnych charakterystykach wydajnościowych:

- **NER** (spaCy `en_core_web_trf`, CPU-only torch) — CPU-bound, ~kilkadziesiąt sekund per książka,
  bloki BLAS/transformer trzymają GIL, nie korzysta z asyncio
- **LLM** (OpenRouter API) — I/O-bound, ~setki ms per para postaci, wiele równoległych wywołań
  HTTP, idealne dla zielonych wątków

Jeden worker Celery może mieć tylko jeden typ pool. Próba użycia jednego workera = albo
blokujemy NER przez I/O LLM, albo trwonimy CPU na coroutines, które i tak nie pomogą
synchronicznym wywołaniom torch.

## Opcje rozważone

1. **Jeden worker prefork** — blokujący na I/O LLM, brak realnej współbieżności zapytań sieciowych,
   marnowanie CPU podczas czekania
2. **Jeden worker gevent** — gevent monkey-patch nie współpracuje dobrze ze spaCy/torch (BLAS,
   GIL release w C-extensions), ryzyko zawieszenia lub niepoprawnych wyników
3. **Dwa workery, dwa pools** (wybrane) — każde zadanie trafia do właściwej kolejki przez routing
4. **Async (asyncio)** — wymagałby przepisania spaCy pipeline na async (niemożliwe — brak natywnego
   wsparcia w bibliotece), oraz async OpenRouter SDK (możliwe, ale spaCy nadal blokuje)

## Decyzja

- `celery-ner`: `--pool prefork`, kolejka `ner`, taski `analyse_book`, statystyki tekstu
- `celery-llm`: `--pool gevent`, kolejka `llm`, task `relations_for_book`
- Routing przez `CELERY_TASK_ROUTES` w `backend-django/config/celery.py`
- Dead Letter Exchange (`dlx`) w RabbitMQ z kolejką `dead_letter` dla zadań po max retry
- Flower (`:5555`) monitoruje oba workery
- W trybie dev: `CELERY_TASK_ALWAYS_EAGER=True` — taski wykonują się synchronicznie w procesie
  Django, broker niepotrzebny

## Konsekwencje

- Dwa osobne kontenery Docker (`celery-ner`, `celery-llm`) w `infra/compose/docker-compose.dev.yml`
- Dwa osobne healthchecki, dwa entrypoints
- Większy memory footprint (każdy worker ma własną kopię modelu spaCy ładowaną przy starcie —
  ale `celery-llm` nie ładuje spaCy, więc realnie tylko `celery-ner` jest ciężki)
- **RabbitMQ pin** do `rabbitmq:3-management-alpine` — wersja 4 deprecates `transient_nonexcl_queues`,
  co łamie Celery 5.6
- **`definitions.json`** musi deklarować `"vhosts": [{"name": "/"}]` **przed** kolejkami/exchangami,
  inaczej RabbitMQ 3.x crashuje przy starcie z błędem o brakującym vhost
- Skalowanie: można zwiększyć `--concurrency` celery-llm bez ruszania celery-ner (LLM łatwo
  skalować poziomo, NER ograniczony CPU)

## Linki

- Kod: `backend-django/config/celery.py`, `backend-django/analysis/tasks.py`
- Infra: `infra/compose/docker-compose.dev.yml`, `infra/rabbitmq/definitions.json`
- Strony wiki: [[celery-workers]], [[nlp-pipeline]]
