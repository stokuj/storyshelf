package com.stokuj.books.book.character.core;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;

import java.lang.reflect.Field;
import java.util.NoSuchElementException;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class StoryCharacterServiceTest {

    @Mock
    StoryCharacterRepository characterRepository;

    @InjectMocks
    StoryCharacterService storyCharacterService;

    @Test
    void shouldThrowWhenNameIsNull() {
        assertThatThrownBy(() -> storyCharacterService.findOrCreate(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Character name cannot be null");
    }

    @Test
    void shouldThrowWhenNameIsBlank() {
        assertThatThrownBy(() -> storyCharacterService.findOrCreate("   "))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Character name cannot be blank");
    }

    @Test
    void shouldReturnExistingCharacterByNormalizedName() {
        StoryCharacter existing = character(1L, "Paul Atreides");
        given(characterRepository.findByNameIgnoreCase("Paul Atreides")).willReturn(Optional.of(existing));

        StoryCharacter result = storyCharacterService.findOrCreate("  Paul Atreides  ");

        assertThat(result).isEqualTo(existing);
    }

    @Test
    void shouldCreateCharacterWhenNotExists() {
        StoryCharacter created = character(2L, "Chani");
        given(characterRepository.findByNameIgnoreCase("Chani")).willReturn(Optional.empty());
        given(characterRepository.saveAndFlush(any(StoryCharacter.class))).willReturn(created);

        StoryCharacter result = storyCharacterService.findOrCreate("  Chani ");

        assertThat(result).isEqualTo(created);
    }

    @Test
    void shouldReturnCharacterAfterIntegrityViolationRaceCondition() {
        StoryCharacter existing = character(3L, "Duncan Idaho");
        given(characterRepository.findByNameIgnoreCase("Duncan Idaho"))
                .willReturn(Optional.empty())
                .willReturn(Optional.of(existing));
        given(characterRepository.saveAndFlush(any(StoryCharacter.class)))
                .willThrow(new DataIntegrityViolationException("duplicate"));

        StoryCharacter result = storyCharacterService.findOrCreate("Duncan Idaho");

        assertThat(result).isEqualTo(existing);
    }

    @Test
    void shouldPropagateWhenIntegrityViolationAndSecondLookupFails() {
        given(characterRepository.findByNameIgnoreCase("Jessica"))
                .willReturn(Optional.empty())
                .willReturn(Optional.empty());
        given(characterRepository.saveAndFlush(any(StoryCharacter.class)))
                .willThrow(new DataIntegrityViolationException("duplicate"));

        assertThatThrownBy(() -> storyCharacterService.findOrCreate("Jessica"))
                .isInstanceOf(NoSuchElementException.class);
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
