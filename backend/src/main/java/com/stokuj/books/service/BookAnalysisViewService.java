package com.stokuj.books.service;

import com.stokuj.books.model.entity.BookCharacter;
import com.stokuj.books.model.entity.CharacterRelation;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class BookAnalysisViewService {

    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;

    public BookAnalysisViewService(BookCharacterRepository bookCharacterRepository,
                                   CharacterRelationRepository characterRelationRepository) {
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
    }

    public List<BookCharacter> getBookCharacters(Long bookId) {
        return bookCharacterRepository.findAllByBookId(bookId);
    }

    public List<CharacterRelation> getCharacterRelations(Long bookId) {
        return characterRelationRepository.findAllByBookId(bookId);
    }
}
