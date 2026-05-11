## Why

Frontend miał kilka problemów UX i technicznych: brak linku "Moja półka" w
navbarze dla zalogowanych użytkowników, 118 linii martwego kodu (nieużywane
funkcje API + dead file), twardo zakodowany placeholder "Vue" zamiast
dynamicznego gatunku, niespójną nazwę projektu ("SpringShelf" vs "StoryShelf")
oraz brak strony 404.

## What

- Dodany link "Moja półka" w navbarze dla zalogowanych użytkowników
- Usunięte 12 nieużywanych funkcji z api.js (fetchAuthors, fetchSeries,
  fetchBookshelfEntry, wszystkie *Moderator*)
- Usunięty martwy plik mock-data.js
- Znaczek gatunku w HomeView dynamiczny (`book.genres[0]`) zamiast hardcoded "Vue"
- Nazwa projektu ujednolicona do "StoryShelf" (App.vue + index.html)
- Dodana strona 404 (NotFoundView.vue + catch-all route)
- Dodany gotcha do AGENTS.md o rebuildzie frontendu w Dockerze

## How

Zmiany czysto kosmetyczne. Bez zmian logiki biznesowej.

## Testing

- [x] `npm run build` — build przechodzi bez błędów
- [x] Docker image przebudowany i kontener frontendu jest healthy
- [ ] Manual: po zalogowaniu navbar pokazuje [Moja półka] [Profil] [Wyloguj]
- [ ] Manual: nieistniejący URL (np. /xyz) pokazuje stronę 404
- [ ] Manual: książki z gatunkami pokazują dynamiczny badge

## Rollback

`git revert ecab2fd 5d347ad` — bez migracji, bez zmian w API.

## Risk

Low — zmiany tylko w warstwie prezentacji frontendu, zero zmian w backendzie
ani API.
