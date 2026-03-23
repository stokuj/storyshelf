package com.stokuj.books.controller.api;

import com.stokuj.books.dto.character.CharacterResponse;
import com.stokuj.books.dto.character.CharacterRelationResponse;
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
    public ResponseEntity<List<CharacterResponse>> getCharacters(@PathVariable Long bookId) {
        return ResponseEntity.ok(bookCharacterRepository.findAllByBookIdWithCharacter(bookId).stream()
                .map(bc -> new CharacterResponse(
                        bc.getCharacter().getId(),
                        bc.getCharacter().getName(),
                        bc.getMentionCount(),
                        bc.getRole()
                )).toList());
    }

    @GetMapping("/relations")
    public ResponseEntity<List<CharacterRelationResponse>> getRelations(@PathVariable Long bookId) {
        return ResponseEntity.ok(characterRelationRepository.findAllByBookId(bookId).stream()
                .map(cr -> new CharacterRelationResponse(
                        cr.getId(),
                        cr.getSource().getName(),
                        cr.getTarget().getName(),
                        cr.getRelation(),
                        cr.getEvidence(),
                        cr.getConfidence()
                )).toList());
    }
}