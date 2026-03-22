package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.User;
import com.stokuj.books.dto.auth.AuthResponse;
import com.stokuj.books.dto.auth.LoginRequest;
import com.stokuj.books.dto.auth.RegisterRequest;
import com.stokuj.books.service.AuthService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
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

@RestController
@RequestMapping("/api/auth")
public class AuthApiController {

    private final AuthService authService;
    private final AuthenticationManager authenticationManager;
    private final SecurityContextRepository securityContextRepository;

    public AuthApiController(AuthService authService,
                             AuthenticationManager authenticationManager,
                             SecurityContextRepository securityContextRepository) {
        this.authService = authService;
        this.authenticationManager = authenticationManager;
        this.securityContextRepository = securityContextRepository;
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        User user = authService.registerUser(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new AuthResponse("User registered successfully", user.getUsername()));
    }

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
}