package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.BookCharacter;
import com.stokuj.books.domain.entity.CharacterRelation;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books/{bookId}")
public class CharacterController {

    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;

    public CharacterController(BookCharacterRepository bookCharacterRepository,
                               CharacterRelationRepository characterRelationRepository) {
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
    }

    @GetMapping("/characters")
    public ResponseEntity<List<BookCharacter>> getCharacters(@PathVariable Long bookId) {
        return ResponseEntity.ok(bookCharacterRepository.findAllByBookIdWithCharacter(bookId));
    }

    @GetMapping("/relations")
    public ResponseEntity<List<CharacterRelation>> getRelations(@PathVariable Long bookId) {
        return ResponseEntity.ok(characterRelationRepository.findAllByBookId(bookId));
    }
}