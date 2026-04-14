package com.stokuj.books.auth;
import com.stokuj.books.auth.dto.RegisterRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import com.stokuj.books.user.UserRole;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {
    @Mock UserRepository userRepository;
    @Mock PasswordEncoder passwordEncoder;
    @InjectMocks AuthService authService;


    @Test
    void shouldRegisterUserWithEncodedPasswordAndDefaultRole() {
        // Given
        RegisterRequest request = new RegisterRequest(
                "john",
                "john@example.com",
                "secret123"
        );
        given(userRepository.findByEmail("john@example.com")).willReturn(Optional.empty());
        given(userRepository.existsByUsername("john")).willReturn(false);
        given(passwordEncoder.encode("secret123")).willReturn("ENC(secret123)");
        User persisted = new User();
        persisted.setId(1L);
        persisted.setUsername("john");
        persisted.setEmail("john@example.com");
        persisted.setPassword("ENC(secret123)");
        persisted.setRole(UserRole.USER);
        given(userRepository.save(any(User.class))).willReturn(persisted);
        // When
        User result = authService.registerUser(request);
        // Then
        ArgumentCaptor<User> savedUserCaptor = ArgumentCaptor.forClass(User.class);
        verify(userRepository).save(savedUserCaptor.capture());
        User savedUser = savedUserCaptor.getValue();
        assertThat(savedUser.getUsername()).isEqualTo("john");
        assertThat(savedUser.getEmail()).isEqualTo("john@example.com");
        assertThat(savedUser.getPassword()).isEqualTo("ENC(secret123)");
        assertThat(savedUser.getRole()).isEqualTo(UserRole.USER);
        verify(passwordEncoder).encode("secret123");
        assertThat(result).isSameAs(persisted);
    }

    @Test
    void shouldThrowWhenUsernameAlreadyTaken() {
        // given
        // Prepare the data for the registration request
        RegisterRequest request = new RegisterRequest(
                "john",
                "john@example.com",
                "secret123"
        );

        // Tell the mock: if asked about this email, say it's NOT in the database (return empty)
        given(userRepository.findByEmail(request.email())).willReturn(Optional.empty());

        // Tell the mock: if asked if "john" exists, say YES (return true)
        given(userRepository.existsByUsername(request.username())).willReturn(true);

        // when / then
        // Try to register the user and check if it throws the expected ConflictException
        assertThatThrownBy(() -> authService.registerUser(request))
                .isInstanceOf(ConflictException.class)
                .hasMessage("Username is already taken.");

        verify(userRepository, never()).save(org.mockito.ArgumentMatchers.any());
    }

    @Test
    void shouldThrowWhenEmailAlreadyExists() {
        // given
        // Prepare the data for the registration request
        RegisterRequest request = new RegisterRequest(
                "john",
                "john@example.com",
                "secret123"
        );

        // Tell the mock: User with this email exist.
        given(userRepository.findByEmail(request.email())).willReturn(Optional.of(new User()));

        // when / then
        // Try to register the user and check if it throws the expected ConflictException
        assertThatThrownBy(() -> authService.registerUser(request))
                .isInstanceOf(ConflictException.class)
                .hasMessage("Email is already taken.");

        verify(userRepository, never()).save(org.mockito.ArgumentMatchers.any());
    }
}
