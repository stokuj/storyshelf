package com.stokuj.books.controller.api;

import com.stokuj.books.dto.user.UserProfileResponse;
import com.stokuj.books.dto.user.UserProfileUpdateRequest;
import com.stokuj.books.dto.user.UserSettingsResponse;
import com.stokuj.books.service.UserProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserProfileService userProfileService;

    public UserController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @GetMapping("/{username}")
    public ResponseEntity<UserProfileResponse> getProfile(@PathVariable String username) {
        return ResponseEntity.ok(
                userProfileService.toPublicResponse(
                        userProfileService.findByUsername(username)
                )
        );
    }

    @PutMapping("/me")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<UserSettingsResponse> updateProfile(@RequestBody UserProfileUpdateRequest request,
                                                              Authentication authentication) {
        return ResponseEntity.ok(
                userProfileService.updateProfile(
                        userProfileService.findByEmail(authentication.getName()),
                        request
                )
        );
    }

    @PatchMapping("/me/visibility")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<UserSettingsResponse> updateVisibility(@RequestParam boolean profilePublic,
                                                                 Authentication authentication) {
        return ResponseEntity.ok(
                userProfileService.updateVisibility(
                        userProfileService.findByEmail(authentication.getName()),
                        profilePublic
                )
        );
    }
}