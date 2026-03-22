package com.stokuj.books.dto.service;

import com.stokuj.books.domain.entity.Character;
import com.stokuj.books.repository.CharacterRepository;
import java.util.Optional;

import com.stokuj.books.service.CharacterService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.dao.DataIntegrityViolationException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class CharacterServiceTest {

    @Mock
    CharacterRepository characterRepository;

    @InjectMocks
    CharacterService characterService;

    @Test
    void shouldReturnExistingCharacterIgnoringCase() {
        Character existing = new Character();
        existing.setId(1L);
        existing.setName("Anna");

        given(characterRepository.findByNameIgnoreCase("anna"))
                .willReturn(Optional.of(existing));

        Character result = characterService.findOrCreate(" anna ");

        assertThat(result).isSameAs(existing);
        verify(characterRepository, never()).save(any(Character.class));
    }

    @Test
    void shouldCreateCharacterWhenMissing() {
        given(characterRepository.findByNameIgnoreCase("Piotr"))
                .willReturn(Optional.empty());
        given(characterRepository.saveAndFlush(any(Character.class)))
                .willAnswer(inv -> inv.getArgument(0));

        Character result = characterService.findOrCreate("  Piotr  ");

        assertThat(result.getName()).isEqualTo("Piotr");
        verify(characterRepository).saveAndFlush(any(Character.class));
    }

    @Test
    void shouldReturnExistingWhenConcurrentInsertHappens() {
        Character existing = new Character();
        existing.setId(2L);
        existing.setName("Ewa");

        given(characterRepository.findByNameIgnoreCase("Ewa"))
                .willReturn(Optional.empty())
                .willReturn(Optional.of(existing));
        doThrow(new DataIntegrityViolationException("duplicate"))
                .when(characterRepository)
                .saveAndFlush(any(Character.class));

        Character result = characterService.findOrCreate("Ewa");

        assertThat(result).isSameAs(existing);
        verify(characterRepository).saveAndFlush(any(Character.class));
    }
}
