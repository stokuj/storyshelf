# StoryShelf

Wiki o książkach. Strony pisze agent LLM razem z userem. Treść jest w formacie Open Knowledge Format (OKF).

## Language

### Wiki

**Wiki**:
Zbiór **Stron** jednego **Usera**, który tworzy jeden pakiet OKF.
_Avoid_: katalog, baza wiedzy

**User**:
Osoba z kontem. Ma dokładnie jedną własną **Wiki**.
_Avoid_: konto, czytelnik

**Profil**:
Wizytówka Usera: „o mnie" oraz **Ulubione** Strony. Jest oddzielna od Wiki. User sam ustawia, czy Profil jest publiczny czy prywatny.
_Avoid_: strona usera, konto

**Ulubione**:
Strony typu `book` lub `character` z Wiki Usera, które wyróżnił na swoim Profilu. Inni widzą je jako kartę (tytuł i opis) bez dostępu do samej Strony.
_Avoid_: półka, lista, zakładki

**Strona**:
Jeden dokument Markdown z frontmatterem YAML, który opisuje jeden byt (koncept OKF).
_Avoid_: artykuł, wpis, rekord

**Typ strony**:
Obowiązkowe pole `type` we frontmatterze Strony. Wartości: `book`, `character`, `place`, `universe`.
_Avoid_: kategoria, rodzaj

**Ścieżka**:
Położenie Strony w Wiki. Jest jednocześnie jej tożsamością (OKF: ścieżka pliku = tożsamość konceptu). Ścieżki są płaskie, jeden katalog na Typ strony (`/books/`, `/characters/`, `/places/`, `/universes/`). Powiązania nie wynikają z folderów.
_Avoid_: id, slug

**Odnośnik**:
Zwykły link Markdown z jednej Strony do drugiej. Odnośniki tworzą graf powiązań.
_Avoid_: relacja (gdy chodzi o samo podlinkowanie)

**Źródło**:
Materiał, z którego pochodzi treść Strony, np. Wikipedia, wątek z Reddita albo fragment książki (OKF: `sources`).
_Avoid_: cytat, referencja

**Weryfikacja**:
Potwierdzenie treści Strony przez człowieka (`human:<id>`) lub maszynę (OKF: `verified`). Bez Weryfikacji Strona jest niezweryfikowana.
_Avoid_: akceptacja, zatwierdzenie

### Byty opisywane w Wiki

**Uniwersum**:
Świat wspólny dla wielu książek (cykl, seria, uniwersum), np. Wiedźmin. Strona typu `universe`. Książka należy do co najwyżej jednego Uniwersum (pole `universe`).
_Avoid_: seria, cykl, saga (jako osobne pojęcia)

**Postać**:
Strona typu `character`. Na razie należy do jednej książki (pole `book`), docelowo do Uniwersum. Ta sama osoba w dwóch książkach to na razie dwie Postacie.
_Avoid_: bohater, osoba

**Wzmianka**:
Krótki opis roli Postaci lub Miejsca w danej książce, w sekcji Strony książki, z Odnośnikiem (badge) do osobnej Strony. Opis jest specyficzny dla tej książki.
_Avoid_: karta postaci, sekcja postaci

**Miejsce**:
Strona typu `place`. Zakotwiczona tak samo jak Postać.
_Avoid_: lokacja, lokalizacja

**Autor**:
Na razie tylko tekst w polu `author` Strony książki, nie osobna Strona.
_Avoid_: pisarz

### Agent i zmiany

**Agent**:
Asystent LLM, który identyfikuje książki i pisze treść Stron (OKF: `generated.by`).
_Avoid_: bot, AI, model

**Kandydat**:
Książka (tytuł, autor, rok, okładka), którą Agent proponuje na podstawie prośby Usera, zanim powstanie Strona.
_Avoid_: wynik wyszukiwania, sugestia

**Szablon**:
Stały układ sekcji Markdown dla danego Typu strony. Nowa Strona powstaje jako pusty Szablon.
_Avoid_: wzór, layout

**Generowanie**:
Pierwsze wypełnienie pustej Strony przez Agenta na żądanie Usera. Zapisuje się od razu, bez akceptacji.
_Avoid_: regeneracja, uzupełnianie

**Propozycja**:
Zmiana treści istniejącej Strony przygotowana przez Agenta na prośbę Usera, na podstawie konkretnej Wersji. Wchodzi w życie dopiero po akceptacji Usera. Gdy Strona dostanie nowszą Wersję, Propozycja staje się nieaktualna i nie da się jej zaakceptować.
_Avoid_: sugestia, draft, PR

**Edycja**:
Ręczna zmiana treści Strony przez Usera, bez Agenta. Tworzy nową Wersję od razu, bez akceptacji.
_Avoid_: poprawka, korekta

**Wersja**:
Utrwalony stan Strony po każdej zmianie: utworzeniu z Szablonu, Generowaniu, zaakceptowanej Propozycji albo ręcznej Edycji. Wersje tworzą Historię Strony.
_Avoid_: rewizja, snapshot

## Relationships

- **User** ma dokładnie jedną **Wiki**; **Wiki** należy do dokładnie jednego **Usera**
- **Wiki** jest widoczna tylko dla swojego **Usera** (udostępnianie dopiero później)
- **User** ma jeden **Profil**; **Ulubione** na Profilu wskazują Strony z jego Wiki
- **Wiki** składa się z wielu **Stron**
- **Ścieżka** jest unikalna w obrębie jednej **Wiki** (dwie Wiki mogą mieć Stronę `/books/wiedzmin.md`)
- Każda **Strona** ma dokładnie jeden **Typ strony** i jedną **Ścieżkę**
- **Strona** może zawierać wiele **Odnośników** do innych **Stron**
- Prośba Usera → **Agent** pokazuje **Kandydata** → User potwierdza → powstaje **Strona** z pustym **Szablonem**
- Pusta **Strona** → User uruchamia **Generowanie** → pierwsza wypełniona **Wersja** (bez akceptacji)
- Każda kolejna zmiana Agenta to **Propozycja**; zaakceptowana tworzy nową **Wersję**, odrzucona nie zmienia Strony
- **Strona książki** ma sekcję **Wzmianek**; każda **Wzmianka** linkuje do osobnej Strony **Postaci**/**Miejsca**
- Na razie **Postać** należy do jednej książki (ta sama osoba w 2 książkach = 2 Strony); docelowo jedna **Postać** na **Uniwersum** (migracja)
- **Strona** ma jedną lub więcej **Wersji**
- **Strona** ma zero lub więcej **Źródeł** i zero lub więcej **Weryfikacji**

## Example dialogue

> **Dev:** „Postać Geralta to rekord w bazie czy **Strona**?"
> **Domain expert:** „**Strona** typu `character`. Strona książki ma do niej **Wzmiankę** z **Odnośnikiem**, a w UI wyświetlamy ją jako badge."
> **Dev:** „Czy Geralt z »Ostatniego życzenia« i z »Krwi elfów« to jedna **Postać**?"
> **Domain expert:** „Na razie dwie, bo w każdej książce robi co innego. Po scaleniu w **Uniwersum** będzie jedna **Postać**, a rolę w konkretnej książce opisuje **Wzmianka**."

## Flagged ambiguities

- „open knowledge format": chodzi o OKF v0.1 (GoogleCloudPlatform/knowledge-catalog/okf), czyli katalog plików `.md` z frontmatterem YAML. Rozstrzygnięte: format treści Wiki jest zgodny z OKF **v0.2** (SPEC.md w knowledge-catalog/okf).
- „wspólna wiedza": Wiki NIE jest współdzielona. Każdy User ma własną kopię Stron, nawet o tej samej książce. Współdzielenie treści między Wiki (cache kosztów LLM) to przyszła optymalizacja, a nie część modelu.
- „publiczny profil" ≠ „publiczna Wiki": publiczny Profil pokazuje karty Ulubionych, ale nie odsłania żadnej Strony. Szczegóły doprecyzujemy razem z udostępnianiem Wiki.
- „agent uzna, że trzeba poprawić": na razie Propozycję uruchamia wyłącznie prośba Usera na Stronie. Propozycje jako skutek uboczny pracy nad inną Stroną przyjdą razem z postaciami w obrębie Uniwersum.
- „zagnieżdżenie" vs „powiązanie": Strony nie są zagnieżdżone w folderach (Postać nie leży „w" książce). Przynależność do książki lub Uniwersum to pole we frontmatterze, a widoki („Postacie w tym Uniwersum") są z niego wyliczane.
