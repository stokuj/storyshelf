# Subagenci StoryShelf

Pusty na start. Subagentów dodajemy gdy zauważymy powtarzalny wzorzec pracy wymagający
**świeżego kontekstu** (subagent dostaje czystą sesję, nie zaśmieca głównej rozmowy).

## Format pliku subagenta

`.claude/agents/<nazwa>.md` z frontmatterem:

```yaml
---
name: <nazwa>
description: <kiedy używać — jednoznacznie, dla auto-routingu>
tools: [Read, Grep, Glob]   # ograniczone narzędzia
model: sonnet               # opcjonalne: sonnet | opus | haiku
---
```

Po frontmatterze — instrukcje, kontekst, przykłady wywołań.

## Kandydaci (nie tworzymy na start — premature)

- **`django-reviewer`** — review kodu Django wg konwencji projektu (camelCase mapping,
  `pagination_class = None`, trailing slashes, custom permissions inline, related_name)
- **`vue-reviewer`** — review kodu Vue z kontraktem API (snake→camel mapping, no localStorage
  tokens, useAsyncState patterns, AlertMessage convention)
- **`celery-task-writer`** — szablon dla nowego taska Celery: routing przez `CELERY_TASK_ROUTES`,
  DLX dla failed tasks, idempotentność jeśli wymagana
- **`wiki-page-author`** — tworzy nową stronę `docs/llm-wiki/<slug>.md` z poprawnym frontmatter
  (`owns`, `related_pages`, `last_verified_commit`) i wszystkimi 6 wymaganymi sekcjami
- **`adr-author`** — szkielet nowego ADR w `docs/decisions/`: numeracja, format Nygard,
  linki do commitów/wiki

## Kiedy dodać subagenta

Konkretny powtarzalny wzorzec — np. "trzeci raz proszę Claude o napisanie nowej strony wiki
i za każdym razem podaję te same instrukcje". Wtedy `wiki-page-author` zaczyna mieć sens.

Bez konkretnego use case = premature optimization. Subagenci kosztują tokeny (świeży kontekst
do załadowania) — mają sens dopiero gdy oszczędzają więcej tokenów niż konsumują.
