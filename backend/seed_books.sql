-- =============================================================
--  seed_books.sql  —  20 testowych książek dla SpringShelf
--  Użycie: psql -U postgres -d booksdb -f seed_books.sql
-- =============================================================

BEGIN;

-- Wyczyść istniejące dane seed (opcjonalne, odkomentuj jeśli potrzebujesz czystego slate)
-- DELETE FROM book_chapters WHERE book_id IN (SELECT id FROM books WHERE ratings_count > 0);
-- DELETE FROM book_tags   WHERE book_id IN (SELECT id FROM books WHERE ratings_count > 0);
-- DELETE FROM book_genres WHERE book_id IN (SELECT id FROM books WHERE ratings_count > 0);
-- DELETE FROM user_books  WHERE book_id IN (SELECT id FROM books WHERE ratings_count > 0);
-- DELETE FROM books       WHERE ratings_count > 0;

-- -----------------------------------------------------------
--  BOOKS
-- -----------------------------------------------------------
INSERT INTO books (
  title,
  author,
  year,
  isbn,
  description,
  page_count,
  rating,
  ratings_count,
  chapters_count,
  ner_completed_count,
  characters,
  find_pairs_result,
  relations_result,
  created_at,
  updated_at
)
VALUES
-- 1
('Wiedźmin: Ostatnie życzenie',
 'Andrzej Sapkowski',
 1993,
 '9788375780635',
 'Zbiór opowiadań wprowadzający Geralta z Rivii — wiedźmina polującego na potwory. Mroczny świat fantasy osadzony w słowiańskiej mitologii, gdzie granica między dobrem a złem jest niewyraźna.',
  288, 4.6, 312400, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 2
('Dune',
 'Frank Herbert',
 1965,
 '9780441013593',
 'Epicka powieść science-fiction rozgrywająca się na pustynnej planecie Arrakis, jedynym źródle bezcennej przyprawy melanżu. Historia polityki, religii i przetrwania.',
  412, 4.7, 891200, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 3
('1984',
 'George Orwell',
 1949,
 '9780451524935',
 'Dystopia przedstawiająca totalitarne państwo, w którym Wielki Brat obserwuje każdy krok obywateli. Winston Smith próbuje zachować człowieczeństwo w świecie wszechobecnej kontroli.',
  328, 4.7, 3200000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 4
('Zbrodnia i kara',
 'Fiodor Dostojewski',
 1866,
 '9780140449136',
 'Psychologiczna powieść o Raskolnikowie — biednym studencie, który zabija lichwiarę przekonany o własnej wyjątkowości. Studium winy, kary i odkupienia.',
  551, 4.5, 624000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 5
('Mistrz i Małgorzata',
 'Michaił Bułhakow',
 1967,
 '9788308060117',
 'Satyra na sowiecką rzeczywistość lat 30. Diabeł Woland przybywa do Moskwy siejąc chaos. Równolegle toczy się historia Poncjusza Piłata i Jeszui Ha-Nocri.',
  480, 4.8, 445000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 6
('Nowy wspaniały świat',
 'Aldous Huxley',
 1932,
 '9780060850524',
 'Dystopia, w której ludzkość osiągnęła stabilność kosztem wolności i uczuć. Społeczeństwo podzielone na kasty, szczęście zapewniane przez narkotyk soma.',
  311, 4.2, 1180000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 7
('Hobbit',
 'J.R.R. Tolkien',
 1937,
 '9780547928227',
 'Bilbo Baggins — spokojny hobbit — zostaje wciągnięty w przygodę przez czarodzieja Gandalfa. Podróż przez Dzikie Ostępy, spotkanie z trollami, elfami i smokiem Smaug.',
  310, 4.7, 2100000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 8
('Solaris',
 'Stanisław Lem',
 1961,
 '9788308060933',
 'Psycholog Kris Kelvin przybywa na stację orbitalną krążącą nad tajemniczą planetą Solaris. Ocean Solaris materializuje ludzkie wspomnienia i lęki. Filozoficzna refleksja nad granicami poznania.',
  272, 4.5, 198000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 9
('Fahrenheit 451',
 'Ray Bradbury',
 1953,
 '9781451673319',
 'W przyszłości, gdzie posiadanie książek jest przestępstwem, strażak Guy Montag pali je z rozkazu. Stopniowo zaczyna kwestionować sens swojej pracy i świata, w którym żyje.',
  249, 4.4, 1560000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 10
('Władca Pierścieni: Drużyna Pierścienia',
 'J.R.R. Tolkien',
 1954,
 '9780618640157',
 'Frodo Baggins dziedziczy Jedyny Pierścień i wyrusza w niebezpieczną podróż, aby zniszczyć go w Górze Przeznaczenia. Pierwsza część epickiej trylogii fantasy.',
  423, 4.9, 4200000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 11
('Sto lat samotności',
 'Gabriel García Márquez',
 1967,
 '9780060883287',
 'Saga rodziny Buendía w fikcyjnym miasteczku Macondo. Powieść-symbol realizmu magicznego łącząca historię Ameryki Łacińskiej z mityczną wyobraźnią.',
  417, 4.6, 870000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 12
('Mały Książę',
 'Antoine de Saint-Exupéry',
 1943,
 '9780156012195',
 'Pilot rozbija się na Saharze i spotyka małego chłopca przybyłego z odległej asteroidy. Poetycka baśń filozoficzna o miłości, przyjaźni i sensie życia.',
  96, 4.5, 2800000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 13
('Harry Potter i Kamień Filozoficzny',
 'J.K. Rowling',
 1997,
 '9780747532699',
 'Jedenastoletni Harry Potter odkrywa, że jest czarodziejem i zostaje przyjęty do Hogwartu — szkoły magii. Pierwsza część kultowej serii dla młodych dorosłych.',
  309, 4.8, 8900000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 14
('Proces',
 'Franz Kafka',
 1925,
 '9780805209990',
 'Josef K. pewnego ranka zostaje aresztowany nie wiedząc za co. Absurdalna walka jednostki z nieprzeniknioną biurokracją i wymiarem sprawiedliwości bez twarzy.',
  255, 4.3, 389000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 15
('Buszujący w zbożu',
 'J.D. Salinger',
 1951,
 '9780316769174',
 'Holden Caulfield — szesnastoletni buntownik — opuszcza szkołę i błąka się po Nowym Jorku. Kultowa powieść o bólu dorastania, autentyczności i odrzuceniu fałszu dorosłego świata.',
  277, 4.0, 1450000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 16
('Diuna: Mesjasz',
 'Frank Herbert',
 1969,
 '9780593098233',
 'Paul Atreydesa — teraz cesarz znany jako Muad''Dib — mierzy się z konsekwencjami swojego panowania i jihadu, który rozpętał. Mroczna kontynuacja Diuny.',
  331, 4.4, 412000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 17
('Noc żywych truposzy — Wywiad z wampirem',
 'Anne Rice',
 1976,
 '9780345337603',
 'Louis de Pointe du Lac opowiada reporterowi historię swojego życia jako wampir — od XVIII-wiecznej Luizjany po współczesny Paryż. Gotycka powieść o nieśmiertelności i winie.',
  340, 4.1, 567000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 18
('Opowieść podręcznej',
 'Margaret Atwood',
 1985,
 '9780385490818',
 'W teokratycznej Republice Gilead kobiety zostały pozbawione wszelkich praw. Offred — Podręczna — jest zmuszona do rodzenia dzieci dla Dowódców. Przerażająco aktualna dystopia.',
  311, 4.5, 2100000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 19
('Ciemne materie: Złoty Kompas',
 'Philip Pullman',
 1995,
 '9780679879244',
 'Lyra Belacqua wyrusza na Dalekę Północ, aby uratować porwane dzieci. Fantasy łączące światy równoległe, demony-towarzyszów i tajemniczą substancję zwaną Pyłem.',
  351, 4.6, 1230000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE),
-- 20
('Cyberiada',
 'Stanisław Lem',
 1965,
 '9788308048320',
 'Zbiór humorystycznych opowiadań o konstruktorach robotów — Trurlu i Klapaucjuszu — przemierzających kosmos. Filozofia, satyra i lingwistyczne eksperymenty w błyskotliwym wykonaniu.',
  295, 4.6, 87000, 0, 0, NULL, NULL, NULL, CURRENT_DATE, CURRENT_DATE);

-- -----------------------------------------------------------
--  GENRES  (pobieramy ID przez subquery po ISBN)
-- -----------------------------------------------------------
INSERT INTO book_genres (book_id, genre) VALUES
((SELECT id FROM books WHERE isbn = '9788375780635'), 'Fantasy'),
((SELECT id FROM books WHERE isbn = '9788375780635'), 'Dark Fantasy'),

((SELECT id FROM books WHERE isbn = '9780441013593'), 'Science Fiction'),
((SELECT id FROM books WHERE isbn = '9780441013593'), 'Space Opera'),

((SELECT id FROM books WHERE isbn = '9780451524935'), 'Dystopia'),
((SELECT id FROM books WHERE isbn = '9780451524935'), 'Political Fiction'),

((SELECT id FROM books WHERE isbn = '9780140449136'), 'Classic'),
((SELECT id FROM books WHERE isbn = '9780140449136'), 'Psychological Fiction'),

((SELECT id FROM books WHERE isbn = '9788308060117'), 'Satire'),
((SELECT id FROM books WHERE isbn = '9788308060117'), 'Magical Realism'),

((SELECT id FROM books WHERE isbn = '9780060850524'), 'Dystopia'),
((SELECT id FROM books WHERE isbn = '9780060850524'), 'Science Fiction'),

((SELECT id FROM books WHERE isbn = '9780547928227'), 'Fantasy'),
((SELECT id FROM books WHERE isbn = '9780547928227'), 'Adventure'),

((SELECT id FROM books WHERE isbn = '9788308060933'), 'Science Fiction'),
((SELECT id FROM books WHERE isbn = '9788308060933'), 'Philosophical Fiction'),

((SELECT id FROM books WHERE isbn = '9781451673319'), 'Dystopia'),
((SELECT id FROM books WHERE isbn = '9781451673319'), 'Science Fiction'),

((SELECT id FROM books WHERE isbn = '9780618640157'), 'Fantasy'),
((SELECT id FROM books WHERE isbn = '9780618640157'), 'Epic Fantasy'),

((SELECT id FROM books WHERE isbn = '9780060883287'), 'Magical Realism'),
((SELECT id FROM books WHERE isbn = '9780060883287'), 'Literary Fiction'),

((SELECT id FROM books WHERE isbn = '9780156012195'), 'Classic'),
((SELECT id FROM books WHERE isbn = '9780156012195'), 'Philosophical Fiction'),

((SELECT id FROM books WHERE isbn = '9780747532699'), 'Fantasy'),
((SELECT id FROM books WHERE isbn = '9780747532699'), 'Young Adult'),

((SELECT id FROM books WHERE isbn = '9780805209990'), 'Classic'),
((SELECT id FROM books WHERE isbn = '9780805209990'), 'Absurdist Fiction'),

((SELECT id FROM books WHERE isbn = '9780316769174'), 'Classic'),
((SELECT id FROM books WHERE isbn = '9780316769174'), 'Coming-of-age'),

((SELECT id FROM books WHERE isbn = '9780593098233'), 'Science Fiction'),
((SELECT id FROM books WHERE isbn = '9780593098233'), 'Space Opera'),

((SELECT id FROM books WHERE isbn = '9780345337603'), 'Horror'),
((SELECT id FROM books WHERE isbn = '9780345337603'), 'Gothic Fiction'),

((SELECT id FROM books WHERE isbn = '9780385490818'), 'Dystopia'),
((SELECT id FROM books WHERE isbn = '9780385490818'), 'Political Fiction'),

((SELECT id FROM books WHERE isbn = '9780679879244'), 'Fantasy'),
((SELECT id FROM books WHERE isbn = '9780679879244'), 'Young Adult'),

((SELECT id FROM books WHERE isbn = '9788308048320'), 'Science Fiction'),
((SELECT id FROM books WHERE isbn = '9788308048320'), 'Satire');

-- -----------------------------------------------------------
--  TAGS
-- -----------------------------------------------------------
INSERT INTO book_tags (book_id, tag) VALUES
((SELECT id FROM books WHERE isbn = '9788375780635'), 'wiedźmin'),
((SELECT id FROM books WHERE isbn = '9788375780635'), 'sapkowski'),
((SELECT id FROM books WHERE isbn = '9788375780635'), 'polska-fantastyka'),

((SELECT id FROM books WHERE isbn = '9780441013593'), 'herbert'),
((SELECT id FROM books WHERE isbn = '9780441013593'), 'klasyka-sf'),
((SELECT id FROM books WHERE isbn = '9780441013593'), 'pustynna-planeta'),

((SELECT id FROM books WHERE isbn = '9780451524935'), 'orwell'),
((SELECT id FROM books WHERE isbn = '9780451524935'), 'totalitaryzm'),
((SELECT id FROM books WHERE isbn = '9780451524935'), 'wielki-brat'),

((SELECT id FROM books WHERE isbn = '9780140449136'), 'dostojewski'),
((SELECT id FROM books WHERE isbn = '9780140449136'), 'rosja'),
((SELECT id FROM books WHERE isbn = '9780140449136'), 'zbrodnia'),

((SELECT id FROM books WHERE isbn = '9788308060117'), 'bułhakow'),
((SELECT id FROM books WHERE isbn = '9788308060117'), 'diabeł'),
((SELECT id FROM books WHERE isbn = '9788308060117'), 'moskwa'),

((SELECT id FROM books WHERE isbn = '9780060850524'), 'huxley'),
((SELECT id FROM books WHERE isbn = '9780060850524'), 'utopia'),
((SELECT id FROM books WHERE isbn = '9780060850524'), 'kontrola-społeczna'),

((SELECT id FROM books WHERE isbn = '9780547928227'), 'tolkien'),
((SELECT id FROM books WHERE isbn = '9780547928227'), 'hobbit'),
((SELECT id FROM books WHERE isbn = '9780547928227'), 'smok'),

((SELECT id FROM books WHERE isbn = '9788308060933'), 'lem'),
((SELECT id FROM books WHERE isbn = '9788308060933'), 'kontakt'),
((SELECT id FROM books WHERE isbn = '9788308060933'), 'ocean'),

((SELECT id FROM books WHERE isbn = '9781451673319'), 'bradbury'),
((SELECT id FROM books WHERE isbn = '9781451673319'), 'cenzura'),
((SELECT id FROM books WHERE isbn = '9781451673319'), 'książki'),

((SELECT id FROM books WHERE isbn = '9780618640157'), 'tolkien'),
((SELECT id FROM books WHERE isbn = '9780618640157'), 'pierścień'),
((SELECT id FROM books WHERE isbn = '9780618640157'), 'śródziemie'),

((SELECT id FROM books WHERE isbn = '9780060883287'), 'marquez'),
((SELECT id FROM books WHERE isbn = '9780060883287'), 'realizm-magiczny'),
((SELECT id FROM books WHERE isbn = '9780060883287'), 'saga-rodzinna'),

((SELECT id FROM books WHERE isbn = '9780156012195'), 'saint-exupery'),
((SELECT id FROM books WHERE isbn = '9780156012195'), 'baśń'),
((SELECT id FROM books WHERE isbn = '9780156012195'), 'filozofia'),

((SELECT id FROM books WHERE isbn = '9780747532699'), 'rowling'),
((SELECT id FROM books WHERE isbn = '9780747532699'), 'hogwart'),
((SELECT id FROM books WHERE isbn = '9780747532699'), 'magia'),

((SELECT id FROM books WHERE isbn = '9780805209990'), 'kafka'),
((SELECT id FROM books WHERE isbn = '9780805209990'), 'absurd'),
((SELECT id FROM books WHERE isbn = '9780805209990'), 'biurokracja'),

((SELECT id FROM books WHERE isbn = '9780316769174'), 'salinger'),
((SELECT id FROM books WHERE isbn = '9780316769174'), 'bunt'),
((SELECT id FROM books WHERE isbn = '9780316769174'), 'dorastanie'),

((SELECT id FROM books WHERE isbn = '9780593098233'), 'herbert'),
((SELECT id FROM books WHERE isbn = '9780593098233'), 'mesjasz'),
((SELECT id FROM books WHERE isbn = '9780593098233'), 'imperium'),

((SELECT id FROM books WHERE isbn = '9780345337603'), 'anne-rice'),
((SELECT id FROM books WHERE isbn = '9780345337603'), 'wampir'),
((SELECT id FROM books WHERE isbn = '9780345337603'), 'gotyk'),

((SELECT id FROM books WHERE isbn = '9780385490818'), 'atwood'),
((SELECT id FROM books WHERE isbn = '9780385490818'), 'feminizm'),
((SELECT id FROM books WHERE isbn = '9780385490818'), 'teokracja'),

((SELECT id FROM books WHERE isbn = '9780679879244'), 'pullman'),
((SELECT id FROM books WHERE isbn = '9780679879244'), 'daemon'),
((SELECT id FROM books WHERE isbn = '9780679879244'), 'światy-równoległe'),

((SELECT id FROM books WHERE isbn = '9788308048320'), 'lem'),
((SELECT id FROM books WHERE isbn = '9788308048320'), 'roboty'),
((SELECT id FROM books WHERE isbn = '9788308048320'), 'humor');

COMMIT;
