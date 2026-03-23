package com.stokuj.books.controller.api.user;

public class UserControllerIT {
    // TODO: Dostępność: Pobieranie publicznego profilu innej osoby (GET /api/users/{username}) dostępne dla każdego.
    // TODO: Ochrona własnych danych: Aktualizacja (PUT /api/users/me) zmusza do zalogowania. Próba nieautoryzowana daje 401.
    // TODO: Walidacja: Zmiana profilu wysyła UserProfileUpdateRequest. Test sprawdza, czy próba z nullowym 'username' odrzuci request poprawnym błędem "Username cannot be blank" z adnotacji.
}