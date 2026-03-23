package com.stokuj.books.controller.api.admin;

public class AdminBookControllerIT {
    // TODO: Zabezpieczenia: Weryfikacja blokady 403 Forbidden dla zwykłego użytkownika przy edycji książki (PUT/PATCH).
    // TODO: Walidacja wejścia: Potwierdzić, że metoda POST /api/admin/books odrzuca BookRequest bez wymaganego tytułu (błąd 400).
    // TODO: Walidacja wejścia: Sprawdzić czy system odrzuca ujemną liczbę stron książki w żądaniu PATCH (zgodnie z adnotacją @Min(0)).
    // TODO: Działanie poprawne: Symulacja prawidłowego dodania książki przez Moderatora i sprawdzenie formatu JSON zwracanego jako odpowiedź.
}
