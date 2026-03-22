package com.stokuj.books.controller.api;

import com.stokuj.books.dto.user.UserProfileUpdateRequest;
import com.stokuj.books.dto.user.UserProfileVisibilityRequest;
import com.stokuj.books.dto.user.UserProfileResponse;
import com.stokuj.books.dto.user.UserSettingsResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.service.UserProfileService;
import jakarta.validation.Valid;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class UserProfileApiController {

    private final UserProfileService userProfileService;

    public UserProfileApiController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @GetMapping(value = "/users/{username}/profile", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<UserProfileResponse> getPublicProfile(@PathVariable String username) {
        User user;
        try {
            user = userProfileService.findByUsername(username);
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

        if (!user.isProfilePublic()) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }

        return ResponseEntity.ok(userProfileService.toPublicResponse(user));
    }

    @GetMapping(value = "/me/settings", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> getSettings(Authentication authentication) {
        try {
            User user = userProfileService.findByEmail(authentication.getName());
            return ResponseEntity.ok(userProfileService.toSettingsResponse(user));
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", ex.getMessage()));
        }
    }

    @PutMapping(value = "/me/settings", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> updateSettings(@Valid @RequestBody UserProfileUpdateRequest request,
                                            Authentication authentication) {
        try {
            User user = userProfileService.findByEmail(authentication.getName());
            UserSettingsResponse response = userProfileService.updateProfile(user, request);
            return ResponseEntity.ok(response);
        } catch (ConflictException ex) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("message", ex.getMessage()));
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", ex.getMessage()));
        }
    }

    @PutMapping(value = "/me/settings/visibility", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> updateVisibility(@Valid @RequestBody UserProfileVisibilityRequest request,
                                              Authentication authentication) {
        try {
            User user = userProfileService.findByEmail(authentication.getName());
            UserSettingsResponse response = userProfileService.updateVisibility(user, request.profilePublic());
            return ResponseEntity.ok(response);
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", ex.getMessage()));
        }
    }

    @GetMapping(value = "/admin/users/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> getAdminProfile(@PathVariable Long id) {
        try {
            User user = userProfileService.findById(id);
            return ResponseEntity.ok(userProfileService.toSettingsResponse(user));
        } catch (ResourceNotFoundException ex) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", ex.getMessage()));
        }
    }
}
