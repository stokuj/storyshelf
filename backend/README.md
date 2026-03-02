# springshelf

A book tracking and recommendation app inspired by Goodreads. Built with Java Spring Boot, FastAPI (Python ML microservice), Docker, and GitHub Actions. 
Features will include user authentication via OAuth2, book ratings and reviews, and a recommendation engine. The project documents my learning journey with the Spring ecosystem and event-driven architecture.

## Changelog

### [0.1.0] - 2026-03-02

Pierwsza wersja robocza backendu.

#### Added

- Start projektu Spring Boot 4 + Java 21.
- Konfiguracja polaczenia z PostgreSQL.
- Model `Book` i repozytorium `BookRepository`.
- Logika biznesowa w `BookService`.
- REST API w `BookController` (`GET`, `POST`, `PUT`, `DELETE`).
- Walidacja payloadu przez `BookRequest`.
- Globalny handler bledow (`GlobalExceptionHandler`).
- Konteneryzacja aplikacji i bazy danych.

### [0.1.1] - 2026-03-02

#### Added

- Dodałem logowanie oraz rejestracje
- Dodałem połączenie z githubem
- Dodałem zmienne środowiskowe z profilu 'local' w application-local.properties (.gitignore)
- Autoryzacja poprzez tokeny JWT

### Plan na kolejne etapy

- Dodać prosty frontend jako monolit (templatki Thymeleaf)
- Oceny i recenzje ksiazek.
- Serwis rekomendacji (FastAPI + ML).
- CI/CD (GitHub Actions) i testy integracyjne.
