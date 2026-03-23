package com.stokuj.books.controller.api;

public class AuthApiControllerIT {
    // TODO: Rejestracja - Walidacja: Weryfikacja czy użycie zbyt krótkiego hasła (mniej niż 6 znaków) w RegisterRequest skutkuje czytelnym błędem walidacji (400).
    // TODO: Rejestracja - Walidacja: Wysłanie niepoprawnego formatu e-mail (bez @) i upewnienie się, że adnotacja @Email prawidłowo go odrzuca.
    // TODO: Rejestracja - Konkurent: Sprawdzenie, czy obsługa błędu przy rejestracji na już zajęty email rzuca ładny JSON z kodem 409 Conflict.
    // TODO: Logowanie: Przetestowanie prawidłowego logowania poprawnego użytkownika i wystawienia tokena sesji/ciastka (200 OK).
    // TODO: Logowanie: Symulacja niepoprawnego loginu/hasła i oczekiwanie kodu 401 Unauthorized.
}