package com.stokuj.books.controller.api.user;

public class BookShelfControllerIT {
    // TODO: Zabezpieczenia: Próba dodania książki na półkę bez bycia zalogowanym - oczekiwany błąd 401.
    // TODO: Działanie (Zalogowany User): Poprawne pobranie listy książek z półki zalogowanego usera. Sprawdzenie przypisania odpowiedniego contextu Spring Security.
    // TODO: Walidacja: Aktualizacja statusu książki (PATCH) na pustą wartość 'status' powinna zatrzymać się na adnotacji @NotNull z DTO i zwrócić 400.
}