package com.stokuj.books.controller.api.user;

public class UserFollowControllerIT {
    // TODO: Zabezpieczenia: Sprawdzić, czy próba obserwowania (POST /follow) bez zalogowania kończy się błędem 401 Unauthorized.
    // TODO: Uprawnienia: Sprawdzić, czy zalogowany USER może zaobserwować innego użytkownika (status 201 Created).
    // TODO: Konflikt: Upewnić się, że ponowna próba zaobserwowania tej samej osoby zwraca 409 Conflict (zgodnie z logiką w kontrolerze).
    // TODO: Unfollow: Sprawdzić, czy przestań obserwować (DELETE /follow) działa poprawnie i zwraca 204 No Content.
    // TODO: Listy: Sprawdzić, czy pobieranie listy followersów i following (GET) zwraca poprawne dane FollowResponse.
}
