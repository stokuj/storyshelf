#!/usr/bin/env python3
"""Seed 20 test books with authors, genres, and tags for Django StoryShelf.

Usage:
    cd backend-django && PYTHONPATH=. python ../infra/scripts/seed.py
Or inside Docker:
    docker compose exec django python ../infra/scripts/seed.py
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "backend-django")
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from books.models import Book, BookAuthor
from library.models import Author, Genre, Tag

SEED_BOOKS = [
    {
        "title": "Wiedźmin: Ostatnie życzenie",
        "year": 1993,
        "isbn": "9788375780635",
        "description": "Zbiór opowiadań wprowadzający Geralta z Rivii — wiedźmina polującego na potwory. Mroczny świat fantasy osadzony w słowiańskiej mitologii, gdzie granica między dobrem a złem jest niewyraźna.",
        "page_count": 288,
        "rating": 4.6,
        "ratings_count": 312400,
        "author": "Andrzej Sapkowski",
        "genres": ["Fantasy", "Dark Fantasy"],
        "tags": ["wiedźmin", "sapkowski", "polska-fantastyka"],
    },
    {
        "title": "Dune",
        "year": 1965,
        "isbn": "9780441013593",
        "description": "Epicka powieść science-fiction rozgrywająca się na pustynnej planecie Arrakis, jedynym źródle bezcennej przyprawy melanżu. Historia polityki, religii i przetrwania.",
        "page_count": 412,
        "rating": 4.7,
        "ratings_count": 891200,
        "author": "Frank Herbert",
        "genres": ["Science Fiction", "Space Opera"],
        "tags": ["herbert", "klasyka-sf", "pustynna-planeta"],
    },
    {
        "title": "1984",
        "year": 1949,
        "isbn": "9780451524935",
        "description": "Dystopia przedstawiająca totalitarne państwo, w którym Wielki Brat obserwuje każdy krok obywateli. Winston Smith próbuje zachować człowieczeństwo w świecie wszechobecnej kontroli.",
        "page_count": 328,
        "rating": 4.7,
        "ratings_count": 3200000,
        "author": "George Orwell",
        "genres": ["Dystopia", "Political Fiction"],
        "tags": ["orwell", "totalitaryzm", "wielki-brat"],
    },
    {
        "title": "Zbrodnia i kara",
        "year": 1866,
        "isbn": "9780140449136",
        "description": "Psychologiczna powieść o Raskolnikowie — biednym studencie, który zabija lichwiarę przekonany o własnej wyjątkowości. Studium winy, kary i odkupienia.",
        "page_count": 551,
        "rating": 4.5,
        "ratings_count": 624000,
        "author": "Fiodor Dostojewski",
        "genres": ["Classic", "Psychological Fiction"],
        "tags": ["dostojewski", "rosja", "zbrodnia"],
    },
    {
        "title": "Mistrz i Małgorzata",
        "year": 1967,
        "isbn": "9788308060117",
        "description": "Satyra na sowiecką rzeczywistość lat 30. Diabeł Woland przybywa do Moskwy siejąc chaos. Równolegle toczy się historia Poncjusza Piłata i Jeszui Ha-Nocri.",
        "page_count": 480,
        "rating": 4.8,
        "ratings_count": 445000,
        "author": "Michaił Bułhakow",
        "genres": ["Satire", "Magical Realism"],
        "tags": ["bułhakow", "diabeł", "moskwa"],
    },
    {
        "title": "Nowy wspaniały świat",
        "year": 1932,
        "isbn": "9780060850524",
        "description": "Dystopia, w której ludzkość osiągnęła stabilność kosztem wolności i uczuć. Społeczeństwo podzielone na kasty, szczęście zapewniane przez narkotyk soma.",
        "page_count": 311,
        "rating": 4.2,
        "ratings_count": 1180000,
        "author": "Aldous Huxley",
        "genres": ["Dystopia", "Science Fiction"],
        "tags": ["huxley", "utopia", "kontrola-społeczna"],
    },
    {
        "title": "Hobbit",
        "year": 1937,
        "isbn": "9780547928227",
        "description": "Bilbo Baggins — spokojny hobbit — zostaje wciągnięty w przygodę przez czarodzieja Gandalfa. Podróż przez Dzikie Ostępy, spotkanie z trollami, elfami i smokiem Smaug.",
        "page_count": 310,
        "rating": 4.7,
        "ratings_count": 2100000,
        "author": "J.R.R. Tolkien",
        "genres": ["Fantasy", "Adventure"],
        "tags": ["tolkien", "hobbit", "smok"],
    },
    {
        "title": "Solaris",
        "year": 1961,
        "isbn": "9788308060933",
        "description": "Psycholog Kris Kelvin przybywa na stację orbitalną krążącą nad tajemniczą planetą Solaris. Ocean Solaris materializuje ludzkie wspomnienia i lęki. Filozoficzna refleksja nad granicami poznania.",
        "page_count": 272,
        "rating": 4.5,
        "ratings_count": 198000,
        "author": "Stanisław Lem",
        "genres": ["Science Fiction", "Philosophical Fiction"],
        "tags": ["lem", "kontakt", "ocean"],
    },
    {
        "title": "Fahrenheit 451",
        "year": 1953,
        "isbn": "9781451673319",
        "description": "W przyszłości, gdzie posiadanie książek jest przestępstwem, strażak Guy Montag pali je z rozkazu. Stopniowo zaczyna kwestionować sens swojej pracy i świata, w którym żyje.",
        "page_count": 249,
        "rating": 4.4,
        "ratings_count": 1560000,
        "author": "Ray Bradbury",
        "genres": ["Dystopia", "Science Fiction"],
        "tags": ["bradbury", "cenzura", "książki"],
    },
    {
        "title": "Władca Pierścieni: Drużyna Pierścienia",
        "year": 1954,
        "isbn": "9780618640157",
        "description": "Frodo Baggins dziedziczy Jedyny Pierścień i wyrusza w niebezpieczną podróż, aby zniszczyć go w Górze Przeznaczenia. Pierwsza część epickiej trylogii fantasy.",
        "page_count": 423,
        "rating": 4.9,
        "ratings_count": 4200000,
        "author": "J.R.R. Tolkien",
        "genres": ["Fantasy", "Epic Fantasy"],
        "tags": ["tolkien", "pierścień", "śródziemie"],
    },
    {
        "title": "Sto lat samotności",
        "year": 1967,
        "isbn": "9780060883287",
        "description": "Saga rodziny Buendía w fikcyjnym miasteczku Macondo. Powieść-symbol realizmu magicznego łącząca historię Ameryki Łacińskiej z mityczną wyobraźnią.",
        "page_count": 417,
        "rating": 4.6,
        "ratings_count": 870000,
        "author": "Gabriel García Márquez",
        "genres": ["Magical Realism", "Literary Fiction"],
        "tags": ["marquez", "realizm-magiczny", "saga-rodzinna"],
    },
    {
        "title": "Mały Książę",
        "year": 1943,
        "isbn": "9780156012195",
        "description": "Pilot rozbija się na Saharze i spotyka małego chłopca przybyłego z odległej asteroidy. Poetycka baśń filozoficzna o miłości, przyjaźni i sensie życia.",
        "page_count": 96,
        "rating": 4.5,
        "ratings_count": 2800000,
        "author": "Antoine de Saint-Exupéry",
        "genres": ["Classic", "Philosophical Fiction"],
        "tags": ["saint-exupery", "baśń", "filozofia"],
    },
    {
        "title": "Harry Potter i Kamień Filozoficzny",
        "year": 1997,
        "isbn": "9780747532699",
        "description": "Jedenastoletni Harry Potter odkrywa, że jest czarodziejem i zostaje przyjęty do Hogwartu — szkoły magii. Pierwsza część kultowej serii dla młodych dorosłych.",
        "page_count": 309,
        "rating": 4.8,
        "ratings_count": 8900000,
        "author": "J.K. Rowling",
        "genres": ["Fantasy", "Young Adult"],
        "tags": ["rowling", "hogwart", "magia"],
    },
    {
        "title": "Proces",
        "year": 1925,
        "isbn": "9780805209990",
        "description": "Josef K. pewnego ranka zostaje aresztowany nie wiedząc za co. Absurdalna walka jednostki z nieprzeniknioną biurokracją i wymiarem sprawiedliwości bez twarzy.",
        "page_count": 255,
        "rating": 4.3,
        "ratings_count": 389000,
        "author": "Franz Kafka",
        "genres": ["Classic", "Absurdist Fiction"],
        "tags": ["kafka", "absurd", "biurokracja"],
    },
    {
        "title": "Buszujący w zbożu",
        "year": 1951,
        "isbn": "9780316769174",
        "description": "Holden Caulfield — szesnastoletni buntownik — opuszcza szkołę i błąka się po Nowym Jorku. Kultowa powieść o bólu dorastania, autentyczności i odrzuceniu fałszu dorosłego świata.",
        "page_count": 277,
        "rating": 4.0,
        "ratings_count": 1450000,
        "author": "J.D. Salinger",
        "genres": ["Classic", "Coming-of-age"],
        "tags": ["salinger", "bunt", "dorastanie"],
    },
    {
        "title": "Diuna: Mesjasz",
        "year": 1969,
        "isbn": "9780593098233",
        "description": "Paul Atreydesa — teraz cesarz znany jako Muad'Dib — mierzy się z konsekwencjami swojego panowania i jihadu, który rozpętał. Mroczna kontynuacja Diuny.",
        "page_count": 331,
        "rating": 4.4,
        "ratings_count": 412000,
        "author": "Frank Herbert",
        "genres": ["Science Fiction", "Space Opera"],
        "tags": ["herbert", "mesjasz", "imperium"],
    },
    {
        "title": "Wywiad z wampirem",
        "year": 1976,
        "isbn": "9780345337603",
        "description": "Louis de Pointe du Lac opowiada reporterowi historię swojego życia jako wampir — od XVIII-wiecznej Luizjany po współczesny Paryż. Gotycka powieść o nieśmiertelności i winie.",
        "page_count": 340,
        "rating": 4.1,
        "ratings_count": 567000,
        "author": "Anne Rice",
        "genres": ["Horror", "Gothic Fiction"],
        "tags": ["anne-rice", "wampir", "gotyk"],
    },
    {
        "title": "Opowieść podręcznej",
        "year": 1985,
        "isbn": "9780385490818",
        "description": "W teokratycznej Republice Gilead kobiety zostały pozbawione wszelkich praw. Offred — Podręczna — jest zmuszona do rodzenia dzieci dla Dowódców. Przerażająco aktualna dystopia.",
        "page_count": 311,
        "rating": 4.5,
        "ratings_count": 2100000,
        "author": "Margaret Atwood",
        "genres": ["Dystopia", "Political Fiction"],
        "tags": ["atwood", "feminizm", "teokracja"],
    },
    {
        "title": "Złoty Kompas",
        "year": 1995,
        "isbn": "9780679879244",
        "description": "Lyra Belacqua wyrusza na Daleką Północ, aby uratować porwane dzieci. Fantasy łączące światy równoległe, demony-towarzyszów i tajemniczą substancję zwaną Pyłem.",
        "page_count": 351,
        "rating": 4.6,
        "ratings_count": 1230000,
        "author": "Philip Pullman",
        "genres": ["Fantasy", "Young Adult"],
        "tags": ["pullman", "daemon", "światy-równoległe"],
    },
    {
        "title": "Cyberiada",
        "year": 1965,
        "isbn": "9788308048320",
        "description": "Zbiór humorystycznych opowiadań o konstruktorach robotów — Trurlu i Klapaucjuszu — przemierzających kosmos. Filozofia, satyra i lingwistyczne eksperymenty w błyskotliwym wykonaniu.",
        "page_count": 295,
        "rating": 4.6,
        "ratings_count": 87000,
        "author": "Stanisław Lem",
        "genres": ["Science Fiction", "Satire"],
        "tags": ["lem", "roboty", "humor"],
    },
]


def seed():
    books_created = 0
    authors_created = 0
    genres_created = 0
    tags_created = 0

    for entry in SEED_BOOKS:
        author, a_new = Author.objects.get_or_create(name=entry["author"])
        if a_new:
            authors_created += 1

        book, b_new = Book.objects.get_or_create(
            isbn=entry["isbn"],
            defaults={
                "title": entry["title"],
                "year": entry["year"],
                "description": entry["description"],
                "page_count": entry["page_count"],
                "avg_rating": entry["rating"],
                "ratings_count": entry["ratings_count"],
            },
        )
        if b_new:
            books_created += 1

        BookAuthor.objects.get_or_create(
            book=book, author=author, defaults={"role": "AUTHOR"}
        )

        for genre_name in entry["genres"]:
            genre, g_new = Genre.objects.get_or_create(name=genre_name)
            if g_new:
                genres_created += 1
            book.genres.add(genre)

        for tag_name in entry["tags"]:
            tag, t_new = Tag.objects.get_or_create(name=tag_name)
            if t_new:
                tags_created += 1
            book.tags.add(tag)

    print(
        f"Seeded {books_created} books, {authors_created} authors, "
        f"{genres_created} genres, {tags_created} tags"
    )
    print(
        f"Total: {Book.objects.count()} books, {Author.objects.count()} authors, "
        f"{Genre.objects.count()} genres, {Tag.objects.count()} tags"
    )


if __name__ == "__main__":
    seed()
