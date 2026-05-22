# StoryShelf — llm-wiki

> Żywa baza wiedzy o stanie systemu StoryShelf (book-tracking + literary analysis).
> Spec-Driven Development z superpowers. Architektura: [docs/ARCHITECTURE.md](../../ARCHITECTURE.md).

## Komponenty

- [Auth Flow](../auth-flow.md): JWT przez HttpOnly cookies, refresh, integracja Django + Vue
- [NLP Pipeline](../nlp-pipeline.md): spaCy NER + LLM (OpenRouter), 2 taski Celery, encje per-book
- [API Conventions](../api-conventions.md): kontrakt frontend↔backend (trailing /, camelCase, pagination)
- [Celery Workers](../celery-workers.md): NER (prefork) + LLM (gevent), RabbitMQ, DLX, Flower
- [Dev Setup](../dev-setup.md): Docker Compose, DJANGO_ENV, reset DB, seed, healthchecks

## Architektura i decyzje

- [System overview](../../ARCHITECTURE.md)
- [Decyzje (ADR)](../../decisions/)
- [Roadmapa](../../ROADMAP.md)

## Meta

- [Log operacji wiki](log.md)

## Konwencja stron

Każda strona w wiki ma frontmatter z:
- `title`, `last_updated`, `last_verified_commit` (git SHA)
- `owns:` — pliki, które ta strona dokumentuje (`/wiki-lint` sprawdza istnienie)
- `related_pages:` — sąsiedzi w grafie (back-reference obowiązkowy)
- `status: stable | wip | deprecated`

Wymagane sekcje: **Co to jest**, **Jak działa**, **Decyzje**, **Typowe operacje**, **Pułapki**,
**Pytania, na które ta strona odpowiada**.
