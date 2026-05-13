from unittest.mock import patch


class TestAnalyseChapter:
    def test_updates_chapter_stats(self, db, book):
        from books.models import Chapter

        chapter = Chapter.objects.create(
            book=book, chapter_number=1, text="Hello world test"
        )
        from analysis.tasks import analyse_chapter

        analyse_chapter(chapter.id, "Hello world test")
        chapter.refresh_from_db()
        assert chapter.analysis_completed is True
        assert chapter.word_count == 3
        assert chapter.char_count > 0

    def test_skips_if_already_completed(self, db, book):
        from books.models import Chapter

        chapter = Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="test",
            analysis_completed=True,
            char_count=4,
            word_count=1,
            token_count=2,
        )
        from analysis.tasks import analyse_chapter

        analyse_chapter(chapter.id, "test")
        chapter.refresh_from_db()
        assert chapter.char_count == 4


class TestNerChapter:
    def test_stores_ner_pending(self, db, book):
        from books.models import Chapter

        chapter = Chapter.objects.create(book=book, chapter_number=1, text="Frodo")
        book.chapters_count = 2
        book.save()

        with patch("analysis.ner_engine.extract_entities") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 2},
                "organizations": {},
                "locations": {},
            }
            from analysis.tasks import ner_chapter

            ner_chapter(chapter.id, "Frodo")

        chapter.refresh_from_db()
        assert chapter.ner_pending["characters"] == {"Frodo": 2}

    def test_skips_if_already_processed(self, db, book):
        from books.models import Chapter

        chapter = Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="test",
            ner_pending={"characters": {"Frodo": 1}},
        )
        with patch("analysis.ner_engine.extract_entities") as mock_ner:
            from analysis.tasks import ner_chapter

            ner_chapter(chapter.id, "test")
            mock_ner.assert_not_called()

    def test_triggers_merge_when_all_done(self, db, book):
        from books.models import Chapter

        chapter = Chapter.objects.create(book=book, chapter_number=1, text="Frodo")
        book.chapters_count = 1
        book.save()

        with patch("analysis.ner_engine.extract_entities") as mock_ner:
            with patch("analysis.tasks.merge_book_ner.delay") as mock_merge:
                mock_ner.return_value = {
                    "characters": {"Frodo": 1},
                    "organizations": {},
                    "locations": {},
                }
                from analysis.tasks import ner_chapter

                ner_chapter(chapter.id, "Frodo")
            mock_merge.assert_called_once_with(book.id)


class TestMergeBookNer:
    def test_upserts_entities(self, db, book):
        from analysis.models import BookCharacter, BookPlace
        from books.models import Chapter

        Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="old",
            ner_pending={"characters": {"Frodo": 2}, "locations": {"Shire": 3}},
        )
        Chapter.objects.create(
            book=book,
            chapter_number=2,
            text="old",
            ner_pending={"characters": {"Frodo": 1, "Gandalf": 2}},
        )

        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner

            merge_book_ner(book.id)

        frodo = BookCharacter.objects.get(name="Frodo")
        assert frodo.mention_count == 3
        gandalf = BookCharacter.objects.get(name="Gandalf")
        assert gandalf.mention_count == 2
        shire = BookPlace.objects.get(name="Shire")
        assert shire.mention_count == 3

    def test_clears_chapter_text(self, db, book):
        from books.models import Chapter

        ch = Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="Frodo walked",
            ner_pending={"characters": {"Frodo": 1}},
        )
        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner

            merge_book_ner(book.id)
        ch.refresh_from_db()
        assert ch.text == ""
        assert ch.ner_pending is None

    def test_increments_existing_mention_count(self, db, book):
        from analysis.models import BookCharacter
        from books.models import Chapter

        BookCharacter.objects.create(name="Frodo", mention_count=5)
        Chapter.objects.create(
            book=book,
            chapter_number=1,
            text="old",
            ner_pending={"characters": {"Frodo": 2}},
        )
        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner

            merge_book_ner(book.id)
        frodo = BookCharacter.objects.get(name="Frodo")
        assert frodo.mention_count == 7
