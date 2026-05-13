from unittest.mock import patch


class TestAnalyseBook:
    def test_skips_if_no_text(self, db, book):
        from analysis.tasks import analyse_book

        analyse_book(book.id)

        from analysis.models import BookCharacter

        assert not BookCharacter.objects.filter(book=book).exists()

    def test_creates_characters_from_ner(self, db, book):
        book.text = "Frodo walked in the Shire with Gandalf."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 3, "Gandalf": 2},
                "locations": {"Shire": 1},
                "organizations": {},
            }
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                mock_llm.delay = lambda *a, **kw: None
                from analysis.tasks import analyse_book

                analyse_book(book.id)

        from analysis.models import BookCharacter, BookPlace

        assert BookCharacter.objects.filter(book=book, name="Frodo").exists()
        assert BookCharacter.objects.filter(book=book, name="Gandalf").exists()
        assert BookPlace.objects.filter(book=book, name="Shire").exists()

    def test_clears_text_after_analysis(self, db, book):
        book.text = "Frodo and Gandalf went to the Shire."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {"characters": {}, "locations": {}, "organizations": {}}
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                mock_llm.delay = lambda *a, **kw: None
                from analysis.tasks import analyse_book

                analyse_book(book.id)

        book.refresh_from_db()
        assert book.text == ""

    def test_dispatches_relations_task_when_pairs_found(self, db, book):
        book.text = "Frodo and Sam walked together."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 2, "Sam": 2},
                "locations": {},
                "organizations": {},
            }
            with patch("analysis.tasks.find_sentences_with_both_characters") as mock_fp:
                mock_fp.return_value = [
                    {"pair": ["Frodo", "Sam"], "sentences": ["Frodo and Sam walked."]}
                ]
                with patch("analysis.tasks.relations_for_book") as mock_llm:
                    from analysis.tasks import analyse_book

                    analyse_book(book.id)
                    mock_llm.delay.assert_called_once()

    def test_no_llm_dispatch_when_fewer_than_two_characters(self, db, book):
        book.text = "Frodo walked alone."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 1},
                "locations": {},
                "organizations": {},
            }
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                from analysis.tasks import analyse_book

                analyse_book(book.id)
                mock_llm.delay.assert_not_called()


class TestRelationsForBook:
    def test_skips_pair_on_empty_relations(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        BookCharacter.objects.create(name="Frodo", book=book)
        BookCharacter.objects.create(name="Sam", book=book)

        pairs_data = [{"pair": ["Frodo", "Sam"], "sentences": ["Frodo and Sam walked."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = '{"relations": []}'
            from analysis.tasks import relations_for_book

            relations_for_book(book.id, pairs_data)

        assert not CharacterRelationship.objects.filter(book=book).exists()

    def test_saves_valid_relation(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        BookCharacter.objects.create(name="Frodo", book=book)
        BookCharacter.objects.create(name="Gandalf", book=book)

        pairs_data = [{"pair": ["Frodo", "Gandalf"], "sentences": ["Gandalf mentored Frodo."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = (
                '{"relations": [{"source": "Frodo", "relation": "mentor_of",'
                ' "target": "Gandalf", "evidence": "..."}]}'
            )
            from analysis.tasks import relations_for_book

            relations_for_book(book.id, pairs_data)

        assert CharacterRelationship.objects.filter(book=book).count() == 1

    def test_skips_unknown_character(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        BookCharacter.objects.create(name="Frodo", book=book)

        pairs_data = [{"pair": ["Frodo", "Ghost"], "sentences": ["Frodo met Ghost."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = (
                '{"relations": [{"source": "Frodo", "relation": "friend_of",'
                ' "target": "Ghost", "evidence": "..."}]}'
            )
            from analysis.tasks import relations_for_book

            relations_for_book(book.id, pairs_data)

        assert not CharacterRelationship.objects.filter(book=book).exists()
