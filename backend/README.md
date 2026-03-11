# springshelf

A book tracking and recommendation app inspired by Goodreads. Built with Java Spring Boot, FastAPI (Python ML microservice), Docker, and GitHub Actions.
Features will include user authentication via OAuth2, book ratings and reviews, and a recommendation engine. The project documents my learning journey with the Spring ecosystem and event-driven architecture.

## Struktura projektu

- `src/main/java/` - backend Spring Boot (REST API + kontrolery stron)
- `src/main/resources/templates/` - frontend serwowany przez Thymeleaf
- `src/main/resources/application.properties` - konfiguracja aplikacji i OAuth2

## Changelog

### [0.3.0] - 2026-03-05

Migracja frontendu do Thymeleaf i uporządkowanie autoryzacji web/API.

#### Added

- Dodano widoki Thymeleaf: `home`, `book`, `bookshelf`, `login`, `register`, `settings`, `error` oraz layout bazowy.
- Dodano `PageController` do obsługi stron, logowania/rejestracji i akcji półki przez formularze HTML.
- Dodano `UserDetailsServiceImpl` pod logowanie sesyjne (form login).

#### Changed

- Usunięto stary frontend SPA (`frontend/`) oparty o statyczne HTML + JS i token w `localStorage`.
- Rozdzielono security na dwa łańcuchy:
  - `/api/**` — JWT + stateless,
  - web (`/**`) — sesja + form login + OAuth2.
- OAuth2 success flow loguje użytkownika do sesji i przekierowuje na `/`.
- Zmieniono `GlobalExceptionHandler`, aby dla `/api/**` zwracał JSON, a dla stron webowych renderował `error.html`.

#### Fixed

- Poprawiono renderowanie elementów zależnych od logowania w szablonach (`sec:authorize`).
- Naprawiono przypadek błędnej identyfikacji anonimowego użytkownika w `PageController`.
- Na stronie głównej (`/`) osoba niezalogowana nie widzi już akcji `+ Dodaj`.

### [0.3.1] - 2026-03-11

Porządki w konfiguracji Dockera i env oraz częściowa aktualizacja książek.

#### Added

- `PATCH /api/books/{id}` do częściowej aktualizacji książki.
- Przykładowy `.env.example` pod uruchamianie przez Docker Compose.

#### Changed

- `docker-compose.yml`: poprawiona konfiguracja usług, healthcheck DB, stały wolumen danych i pin obrazu Postgres do 16.
- `application.properties`: obsługa zmiennych środowiskowych dla DB i `jwt.secret`.

#### Removed

- `src/main/resources/application-local.properties` (konfiguracja lokalna przeniesiona do env).

### [0.2.1] - 2026-03-04

Rozbudowa modelu książki i porządki.

#### Added

- Nowe pola w modelu `Book`: `isbn`, `description`, `pageCount`, `genres`, `tags`, `rating`, `ratingsCount`, `createdAt`, `updatedAt`.
- Tabele `book_genres` i `book_tags` do filtrowania książek po gatunkach i tagach.

#### Changed

- Refaktoryzacja `BookService` — mapowanie DTO na encję wydzielone do osobnej metody `mapRequestToBook()`.
- Usunięto pole `category` z modelu (zastąpione przez `genres`).
- Usunięto `rating` i `ratingsCount` z `BookRequest` — klient nie może już ustawiać ocen ręcznie.

#### Fixed

- Naprawiono duplikaty wpisów w `.gitignore`.
- Usunięto `styles.css` z trackingu gita.
- Poprawiono nazwę parametru w setterze `setIsbn()`.

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
