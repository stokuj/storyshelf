package com.stokuj.books.auth;

import com.stokuj.books.user.User;
import com.stokuj.books.auth.AuthMeResponse;
import com.stokuj.books.auth.AuthResponse;
import com.stokuj.books.auth.LoginRequest;
import com.stokuj.books.auth.RegisterRequest;
import com.stokuj.books.auth.AuthService;
import com.stokuj.books.user.UserProfileService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.context.SecurityContextRepository;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

@RestController
@RequestMapping("/api/auth")
@Tag(name = "Authentication", description = "Endpoints for user registration and authentication")
public class AuthApiController {

    private final AuthService authService;
    private final AuthenticationManager authenticationManager;
    private final SecurityContextRepository securityContextRepository;
    private final UserProfileService userProfileService;

    public AuthApiController(AuthService authService,
                             AuthenticationManager authenticationManager,
                             SecurityContextRepository securityContextRepository,
                             UserProfileService userProfileService) {
        this.authService = authService;
        this.authenticationManager = authenticationManager;
        this.securityContextRepository = securityContextRepository;
        this.userProfileService = userProfileService;
    }

    @Operation(summary = "Register a new user", description = "Registers a new user with the provided details.")
    @ApiResponse(responseCode = "201", description = "User registered successfully")
    @ApiResponse(responseCode = "400", description = "Validation error or username/email already exists")
    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        User user = authService.registerUser(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new AuthResponse("User registered successfully", user.getUsername()));
    }

    @Operation(summary = "Login user", description = "Authenticates a user and returns a session token/cookie.")
    @ApiResponse(responseCode = "200", description = "Login successful")
    @ApiResponse(responseCode = "401", description = "Invalid credentials")
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request,
                                              HttpServletRequest httpRequest,
                                              HttpServletResponse httpResponse) {

        UsernamePasswordAuthenticationToken token = 
                new UsernamePasswordAuthenticationToken(request.username(), request.password());

        Authentication authentication = authenticationManager.authenticate(token);

        SecurityContext context = SecurityContextHolder.createEmptyContext();
        context.setAuthentication(authentication);
        SecurityContextHolder.setContext(context);
        securityContextRepository.saveContext(context, httpRequest, httpResponse);

        return ResponseEntity.ok(new AuthResponse("Login successful", authentication.getName()));
    }

    @Operation(summary = "Get authenticated user session", description = "Returns the current authentication state and basic user data.")
    @ApiResponse(responseCode = "200", description = "Session state returned successfully")
    @org.springframework.web.bind.annotation.GetMapping("/me")
    public ResponseEntity<AuthMeResponse> me(Authentication authentication) {
        if (authentication == null
                || !authentication.isAuthenticated()
                || authentication instanceof AnonymousAuthenticationToken) {
            return ResponseEntity.ok(new AuthMeResponse(false, null, null, null));
        }

        User user = userProfileService.findByEmail(authentication.getName());
        return ResponseEntity.ok(new AuthMeResponse(true, user.getEmail(), user.getUsername(), user.getRole()));
    }
}
