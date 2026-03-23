package com.stokuj.books.controller.api;

public class ReviewControllerIT {
    // TODO: Uprawnienia: Pobieranie recenzji (GET) powinno być dostępne dla niepołączonych gości (200 OK).
    // TODO: Zabezpieczenia: Próba dodania oceny (POST) przez anonimowego użytkownika powinna być odrzucona (401).
    // TODO: Walidacja (Krytyczne): Wysłanie przez zalogowanego usera ReviewRequest z wartością ratingu '9' (lub -1). Upewnić się, że adnotacja @Max(5) blokuje to wejście!
    // TODO: Walidacja: Ograniczenie treści recenzji – wysłanie za dużego stringa i oczekiwanie błędu rozmiaru.
}