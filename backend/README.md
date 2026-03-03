# springshelf

A book tracking and recommendation app inspired by Goodreads. Built with Java Spring Boot, FastAPI (Python ML microservice), Docker, and GitHub Actions.
Features will include user authentication via OAuth2, book ratings and reviews, and a recommendation engine. The project documents my learning journey with the Spring ecosystem and event-driven architecture.

## Struktura projektu

- `backend/` - aplikacja Spring Boot (REST API, JWT, OAuth2)
- `frontend/` - statyczny frontend (HTML + JS, daisyUI)

## Changelog

### [0.2.0] - 2026-03-03

Działający prototyp z frontendem.

#### Added

- Aplikacja ma osobny frontend oparty o Node.js + Tailwind + daisyUI.
- Proste podstrony: base, settings, login, register.
- Backend ma modele książek, książek użytkownika oraz użytkowników.

![img.png](img.png)

### [0.1.1] - 2026-03-02

Działający prototyp ze Swagger UI.

#### Added

- Dodałem logowanie oraz rejestrację.
- Dodałem połączenie z GitHubem.
- Dodałem zmienne środowiskowe z profilu `local` w `application-local.properties` (`.gitignore`).
- Dodałem autoryzację poprzez tokeny JWT.

![img_1.png](img_1.png)

### [0.1.0] - 2026-03-02

Pierwsza wersja robocza backendu.

#### Added

- Start projektu Spring Boot 4 + Java 21.
- Konfiguracja połączenia z PostgreSQL.
- Model `Book` i repozytorium `BookRepository`.
- Logika biznesowa w `BookService`.
- REST API w `BookController` (`GET`, `POST`, `PUT`, `DELETE`).
- Walidacja payloadu przez `BookRequest`.
- Globalny handler błędów (`GlobalExceptionHandler`).
- Konteneryzacja aplikacji i bazy danych.

### Plan na kolejne etapy

- Dodać prosty frontend jako monolit (template'y Thymeleaf).
- Oceny i recenzje książek.
- Serwis rekomendacji (FastAPI + ML).
- CI/CD (GitHub Actions) i testy integracyjne.
