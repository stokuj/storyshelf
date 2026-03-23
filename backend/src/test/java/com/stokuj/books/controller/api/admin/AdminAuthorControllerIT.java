package com.stokuj.books.controller.api.admin;

public class AdminAuthorControllerIT {
    // TODO: Zabezpieczenia: Sprawdzić, czy niezalogowany Gość dostaje błąd 401 przy próbie użycia metody POST (dodanie autora).
    // TODO: Zabezpieczenia: Sprawdzić, czy zalogowany zwykły USER (bez roli MODERATOR) dostaje błąd 403 Forbidden przy próbie usunięcia autora (DELETE).
    // TODO: Zabezpieczenia: Sprawdzić, czy MODERATOR ma pełny dostęp i otrzymuje kod 200/201 lub 204.
    // TODO: Walidacja wejścia: Upewnić się, że przesłanie AuthorRequest z pustym lub nullowym polem 'name' przez Moderatora kończy się statusem 400 Bad Request.
    // TODO: Walidacja wejścia: Sprawdzić czy przekroczenie limitu wielkości znaków (powyżej 255) z adnotacji @Size zwraca błąd walidacyjny.
}
