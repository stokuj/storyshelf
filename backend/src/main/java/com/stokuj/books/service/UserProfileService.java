package com.stokuj.books.service;

import com.stokuj.books.dto.UserProfileUpdateRequest;
import com.stokuj.books.dto.UserProfileResponse;
import com.stokuj.books.dto.UserSettingsResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.repository.UserRepository;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import org.springframework.stereotype.Service;

@Service
public class UserProfileService {

    private final UserRepository userRepository;

    public UserProfileService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("Użytkownik nie istnieje"));
    }

    public User findByEmail(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("Użytkownik nie istnieje"));
    }

    public User findById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Użytkownik nie istnieje"));
    }

    public UserProfileResponse toPublicResponse(User user) {
        return new UserProfileResponse(
                user.getUsername(),
                user.getBio(),
                user.getAvatarUrl(),
                toMemberSince(user)
        );
    }

    public UserSettingsResponse toSettingsResponse(User user) {
        return new UserSettingsResponse(
                user.getUsername(),
                user.getBio(),
                user.getAvatarUrl(),
                toMemberSince(user),
                user.isProfilePublic(),
                user.getEmail(),
                user.getRole()
        );
    }

    public UserSettingsResponse updateProfile(User user, UserProfileUpdateRequest request) {
        if (!user.getUsername().equals(request.username())
                && userRepository.existsByUsername(request.username())) {
            throw new ConflictException("Username jest już zajęty");
        }

        user.setUsername(request.username());
        if (request.bio() != null) {
            user.setBio(request.bio());
        }
        if (request.avatarUrl() != null) {
            user.setAvatarUrl(request.avatarUrl());
        }

        User saved = userRepository.save(user);
        return toSettingsResponse(saved);
    }

    public UserSettingsResponse updateVisibility(User user, boolean profilePublic) {
        user.setProfilePublic(profilePublic);
        User saved = userRepository.save(user);
        return toSettingsResponse(saved);
    }

    private LocalDateTime toMemberSince(User user) {
        if (user.getCreatedAt() == null) {
            return null;
        }
        return LocalDateTime.ofInstant(user.getCreatedAt(), ZoneOffset.UTC);
    }
}
