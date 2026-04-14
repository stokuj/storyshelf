package com.stokuj.books.book.character.core;

import com.stokuj.books.book.character.aggregation.BookCharacter;
import com.stokuj.books.book.character.aggregation.BookCharacterRepository;
import com.stokuj.books.book.character.core.dto.CharacterResponse;
import com.stokuj.books.book.character.relation.StoryCharacterRelation;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import com.stokuj.books.book.character.relation.dto.CharacterRelationResponse;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.lang.reflect.Field;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class StoryCharacterControllerTest {

    @Mock
    BookCharacterRepository bookCharacterRepository;

    @Mock
    StoryCharacterRelationRepository characterRelationRepository;

    @InjectMocks
    StoryCharacterController storyCharacterController;

    @Nested
    class GetCharacters {

        @Test
        void shouldReturnCharactersForBook() {
            BookCharacter bc1 = bookCharacter(1L, "Paul Atreides", 23, "PROTAGONIST");
            BookCharacter bc2 = bookCharacter(2L, "Chani", 11, "SUPPORTING");
            given(bookCharacterRepository.findAllByBookIdWithCharacter(10L)).willReturn(List.of(bc1, bc2));

            ResponseEntity<List<CharacterResponse>> response = storyCharacterController.getCharacters(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).name()).isEqualTo("Paul Atreides");
            assertThat(response.getBody().get(1).name()).isEqualTo("Chani");
        }

        @Test
        void shouldReturnEmptyCharactersList() {
            given(bookCharacterRepository.findAllByBookIdWithCharacter(10L)).willReturn(List.of());

            ResponseEntity<List<CharacterResponse>> response = storyCharacterController.getCharacters(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEmpty();
        }
    }

    @Nested
    class GetRelations {

        @Test
        void shouldReturnRelationsForBook() {
            StoryCharacterRelation r1 = relation(1L, "Paul Atreides", "Chani", "ALLY", "They trust each other", 0.92);
            StoryCharacterRelation r2 = relation(2L, "Paul Atreides", "Baron", "ENEMY", "They are in conflict", 0.88);
            given(characterRelationRepository.findAllByBookId(10L)).willReturn(List.of(r1, r2));

            ResponseEntity<List<CharacterRelationResponse>> response = storyCharacterController.getRelations(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).sourceCharacterName()).isEqualTo("Paul Atreides");
            assertThat(response.getBody().get(1).targetCharacterName()).isEqualTo("Baron");
        }

        @Test
        void shouldReturnEmptyRelationsList() {
            given(characterRelationRepository.findAllByBookId(10L)).willReturn(List.of());

            ResponseEntity<List<CharacterRelationResponse>> response = storyCharacterController.getRelations(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEmpty();
        }
    }

    private BookCharacter bookCharacter(Long characterId, String name, int mentionCount, String role) {
        StoryCharacter character = new StoryCharacter();
        setField(character, "id", characterId);
        setField(character, "name", name);

        BookCharacter bookCharacter = new BookCharacter();
        setField(bookCharacter, "character", character);
        setField(bookCharacter, "mentionCount", mentionCount);
        setField(bookCharacter, "role", role);
        return bookCharacter;
    }

    private StoryCharacterRelation relation(Long id, String source, String target, String relation, String evidence, double confidence) {
        StoryCharacter sourceCharacter = new StoryCharacter();
        setField(sourceCharacter, "name", source);
        StoryCharacter targetCharacter = new StoryCharacter();
        setField(targetCharacter, "name", target);

        StoryCharacterRelation entity = new StoryCharacterRelation();
        setField(entity, "id", id);
        setField(entity, "source", sourceCharacter);
        setField(entity, "target", targetCharacter);
        setField(entity, "relation", relation);
        setField(entity, "evidence", evidence);
        setField(entity, "confidence", confidence);
        return entity;
    }

    private void setField(Object target, String fieldName, Object value) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
