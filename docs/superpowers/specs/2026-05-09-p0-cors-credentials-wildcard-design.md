# Spec: Fix CORS — remove allowCredentials with wildcard origins

**Date:** 2026-05-09
**Issue:** [#5](https://github.com/stokuj/storyshelf/issues/5)
**File:** `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java:82-93`

## Problem

`SecurityConfig.java` używa `setAllowedOriginPatterns(List.of("*"))` razem z `setAllowCredentials(true)` — kombinacja nieważna według specyfikacji CORS. Przeglądarki odrzucają credentialed requesty z wildcard origin.

## Kontekst architektury

Wszystkie requesty z przeglądarki do backendu są **same-origin**:

| Środowisko | Jak |
|---|---|
| Dev lokalne | Vite proxy (`localhost:5173` → `localhost:8080`) |
| Dev Docker | Vite proxy (`frontend:5173` → `backend:8080`) |
| Prod | Caddy serwuje frontend i backend z jednego origina (port 80/443), routując `/api/*` → backend |

Frontend nigdy nie wysyła cross-origin requestów do backendu przez przeglądarkę. Auth opiera się na `JSESSIONID` cookie.

Konsekwencja: **CORS w backendzie to martwy kod.** Żaden cross-origin request z przeglądarki nie istnieje w tej architekturze.

## Design

### Co usunąć

1. Usunąć cały bean `corsConfigurationSource()` (linie 82-93 w `SecurityConfig.java`)
2. Zmienić `.cors(Customizer.withDefaults())` na `.cors(cors -> cors.disable())`

### Dlaczego `disable()` zamiast po prostu usunięcia beana

Bez jawnego `.cors()` Spring Security dodaje domyślnie `CorsConfigurer` z `Customizer.withDefaults()`, który szuka `CorsConfigurationSource` beana. Usunięcie beana bez zmiany linii `.cors(Customizer.withDefaults())` spowoduje, że Spring utworzy domyślny `CorsConfigurationSource` z pustymi regułami — co nadal będzie marnować cykle i logikę na niepotrzebny CORS. Jawne `.disable()` eliminuje cały `CorsFilter` z łańcucha.

### Efekt

- `CorsFilter` znika z łańcucha Spring Security
- Mniej kodu, mniej cykli CPU na request
- Brak fałszywego alarmu security (wildcard + credentials)
- Żaden istniejący request nie przestaje działać (wszystkie były same-origin)

## Weryfikacja

1. Spring Boot startuje bez błędów
2. OPTIONS preflight z innego origina nie zwraca już CORS nagłówków (CORS wyłączony)
3. Istniejące testy integracyjne backendu przechodzą
4. Frontend działa w dev i prod (same-origin requesty nie wymagają CORS)
