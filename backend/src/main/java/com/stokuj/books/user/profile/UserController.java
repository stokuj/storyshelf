package com.stokuj.books.user.profile;

import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.profile.dto.UserProfileResponse;
import com.stokuj.books.user.profile.dto.UserProfileUpdateRequest;
import com.stokuj.books.user.profile.dto.UserSettingsResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
@Tag(name = "Users", description = "Operations related to user profiles and settings")
public class UserController {

    private final UserProfileService userProfileService;

    public UserController(UserProfileService userProfileService) {
        this.userProfileService = userProfileService;
    }

    @Operation(summary = "Get user profile", description = "Retrieves the public profile of a user by their username.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved user profile")
    @ApiResponse(responseCode = "404", description = "User not found")
    @GetMapping("/{username}")
    public ResponseEntity<UserProfileResponse> getProfile(@PathVariable String username, Authentication authentication) {
        User user = userProfileService.findByUsername(username);

        boolean authenticated = authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken);
        boolean owner = authenticated && authentication.getName().equalsIgnoreCase(user.getEmail());
        boolean privileged = authenticated && authentication.getAuthorities().stream()
                .anyMatch(a -> "ROLE_ADMIN".equals(a.getAuthority()) || "ROLE_MODERATOR".equals(a.getAuthority()));

        if (!user.isProfilePublic() && !owner && !privileged) {
            throw new ResourceNotFoundException("Użytkownik nie istnieje");
        }

        return ResponseEntity.ok(
                userProfileService.toPublicResponse(
                        user
                )
        );
    }

    @Operation(summary = "Get current user settings", description = "Retrieves settings for the authenticated user.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved current user settings")
    @GetMapping("/me")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<UserSettingsResponse> getMe(Authentication authentication) {
        return ResponseEntity.ok(
                userProfileService.toSettingsResponse(
                        userProfileService.findByEmail(authentication.getName())
                )
        );
    }

    @Operation(summary = "Update user profile", description = "Updates the profile information for the authenticated user.")
    @ApiResponse(responseCode = "200", description = "Profile updated successfully")
    @PutMapping("/me")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<UserSettingsResponse> updateProfile(@Valid @RequestBody UserProfileUpdateRequest request,
                                                              Authentication authentication) {
        return ResponseEntity.ok(
                userProfileService.updateProfile(
                        userProfileService.findByEmail(authentication.getName()),
                        request
                )
        );
    }

    @Operation(summary = "Update profile visibility", description = "Updates the public visibility status of the authenticated user's profile.")
    @ApiResponse(responseCode = "200", description = "Visibility updated successfully")
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
