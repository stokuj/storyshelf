package com.stokuj.books.book.character.core;

import com.stokuj.books.book.character.aggregation.BookCharacterRepository;
import com.stokuj.books.book.character.core.dto.CharacterResponse;
import com.stokuj.books.book.character.relation.dto.CharacterRelationResponse;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.List;

@RestController
@RequestMapping("/api/books/{bookId}")
@Tag(name = "Characters", description = "Operations related to characters and their relations in a book")
public class StoryCharacterController {

    private final BookCharacterRepository bookCharacterRepository;
    private final StoryCharacterRelationRepository characterRelationRepository;

    public StoryCharacterController(BookCharacterRepository bookCharacterRepository,
                               StoryCharacterRelationRepository characterRelationRepository) {
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
    }

    @Operation(summary = "Get characters in a book", description = "Retrieves a list of all characters identified in a specific book.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved characters")
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

    @Operation(summary = "Get character relations in a book", description = "Retrieves a list of relations between characters in a specific book.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved relations")
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
