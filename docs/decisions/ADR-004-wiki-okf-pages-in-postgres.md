# ADR-004 — Wiki w formacie OKF, przechowywana jako Strony w Postgresie, osobna dla każdego Usera

> Status: Accepted · Data: 2026-10-03 · Kontekst: pivot z trackera czytania na wiki o książkach

## Decyzja

StoryShelf przestaje być trackerem czytania. Teraz jest to wiki o książkach, którą pisze Agent LLM razem z Userem. Treść każdej Strony to dokument zgodny z **Open Knowledge Format v0.2** (GoogleCloudPlatform/knowledge-catalog/okf): Markdown z frontmatterem YAML (`type`, `sources`, `generated`, `verified`, `status`).

- **Źródło prawdy = Postgres**: tabela Stron (Ścieżka + surowy `.md`) z Historią Wersji. Pakiet OKF (katalog plików) to eksport, a nie storage. Pliki/git odrzucone z powodu współbieżnych edycji, wyszukiwania i uprawnień, które trzeba by pisać samemu.
- **Domenowe tabele znikają**: Book/Author/Genre/Tag/Serie, Rating, Review, Shelf, ShelfEntry, Follow, feed, Character/CharacterRelation (M13/M14). Książka, Postać, Miejsce i Uniwersum to Strony różnego `type`. W bazie zostają User, Profil (o mnie + Ulubione) oraz Strony z Wersjami i Propozycjami.
- **Wiki per User**: każdy User ma własną, prywatną Wiki. Ta sama książka u dwóch Userów to dwie Strony. Współdzielenie treści dla cięcia kosztów LLM i udostępnianie Wiki zostają odłożone.
- **Płaskie Ścieżki per typ** (`/books/`, `/characters/`, `/places/`, `/universes/`). Przynależność do książki lub Uniwersum jest polem we frontmatterze, nie folderem. Dzięki temu przejście z Postaci per książka (`geralt--ostatnie-zyczenie`) na Postać per Uniwersum to scalanie Stron, bez przenoszenia.

## Konsekwencje

- Zapytania „po polach" (np. Postacie w Uniwersum) czytają frontmatter, więc potrzebny jest indeks z frontmattera przy zapisie Strony.
- Wyszukiwanie semantyczne (chatbot „w której książce było…") przyjdzie później: chunkowanie + embeddingi w **pgvector** (ten sam Postgres). Qdrant odrzucony na tym etapie jako dodatkowy kontener.
- ADR-001 (JWT cookies) i ADR-003 (Celery + Redis + OpenRouter) pozostają w mocy. Model kart postaci z M13/M14 zostaje zastąpiony.
