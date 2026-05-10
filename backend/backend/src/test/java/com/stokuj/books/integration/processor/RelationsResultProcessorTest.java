package com.stokuj.books.integration.processor;

import com.stokuj.books.integration.kafka.ChapterEventProducer;
import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.character.core.StoryCharacter;
import com.stokuj.books.book.character.core.StoryCharacterService;
import com.stokuj.books.book.character.relation.StoryCharacterRelation;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class RelationsResultProcessorTest {

    @Mock StoryCharacterRelationRepository characterRelationRepository;
    @Mock StoryCharacterService characterService;
    @Mock ChapterEventProducer chapterEventProducer;

    @InjectMocks RelationsResultProcessor processor;

    @Test
    void shouldSkipIndividualRelationThatAlreadyHasValue() {
        Book book = book(1L);
        StoryCharacter alice = character(10L, "Alice");
        StoryCharacter bob = character(20L, "Bob");
        StoryCharacter charlie = character(30L, "Charlie");

        StoryCharacterRelation existingRelation = new StoryCharacterRelation();
        existingRelation.setBook(book);
        existingRelation.setSource(alice);
        existingRelation.setTarget(bob);
        existingRelation.setRelation("friend");

        given(characterService.findOrCreate("Alice")).willReturn(alice);
        given(characterService.findOrCreate("Bob")).willReturn(bob);
        given(characterService.findOrCreate("Charlie")).willReturn(charlie);
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 20L))
                .willReturn(Optional.of(existingRelation));
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 30L))
                .willReturn(Optional.empty());

        Map<String, Object> result = Map.of("all_relations", List.of(
                Map.of("relations", Map.of("relations", List.of(
                        Map.of("source", "Alice", "target", "Bob", "relation", "enemy"),
                        Map.of("source", "Alice", "target", "Charlie", "relation", "ally")
                )))
        ));

        processor.processRelationsResult(book, result);

        ArgumentCaptor<StoryCharacterRelation> captor = ArgumentCaptor.forClass(StoryCharacterRelation.class);
        verify(characterRelationRepository).save(captor.capture());
        assertThat(captor.getValue().getRelation()).isEqualTo("ally");
    }

    @Test
    void shouldUpdateRelationThatHasBlankValue() {
        Book book = book(1L);
        StoryCharacter alice = character(10L, "Alice");
        StoryCharacter bob = character(20L, "Bob");

        StoryCharacterRelation existingEmpty = new StoryCharacterRelation();
        existingEmpty.setBook(book);
        existingEmpty.setSource(alice);
        existingEmpty.setTarget(bob);
        existingEmpty.setRelation("  ");

        given(characterService.findOrCreate("Alice")).willReturn(alice);
        given(characterService.findOrCreate("Bob")).willReturn(bob);
        given(characterRelationRepository.findByBookIdAndSourceIdAndTargetId(1L, 10L, 20L))
                .willReturn(Optional.of(existingEmpty));

        Map<String, Object> result = Map.of("all_relations", List.of(
                Map.of("relations", Map.of("relations", List.of(
                        Map.of("source", "Alice", "target", "Bob", "relation", "friend")
                )))
        ));

        processor.processRelationsResult(book, result);

        verify(characterRelationRepository).save(any(StoryCharacterRelation.class));
    }

    private Book book(Long id) {
        Book book = new Book();
        setField(book, "id", id);
        return book;
    }

    private StoryCharacter character(Long id, String name) {
        StoryCharacter character = new StoryCharacter();
        setField(character, "id", id);
        setField(character, "name", name);
        return character;
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
