package com.stokuj.books.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.ModelAndView;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    // -------------------------------------------------------------------------
    // Helpery
    // -------------------------------------------------------------------------

    private boolean isApiRequest(HttpServletRequest request) {
        return request.getRequestURI().startsWith("/api/");
    }

    private ResponseEntity<ApiError> buildJsonResponse(HttpStatus status,
                                                        String message,
                                                        String path,
                                                        Map<String, String> validationErrors) {
        ApiError error = new ApiError(
                Instant.now(),
                status.value(),
                status.getReasonPhrase(),
                message,
                path,
                validationErrors
        );
        return ResponseEntity.status(status).body(error);
    }

    private ModelAndView buildHtmlErrorView(HttpStatus status, String message) {
        ModelAndView mav = new ModelAndView("error");
        mav.addObject("status", status.value());
        mav.addObject("error", status.getReasonPhrase());
        mav.addObject("message", message);
        return mav;
    }

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Object handleValidationErrors(MethodArgumentNotValidException ex, HttpServletRequest request) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(error -> {
            String field = ((FieldError) error).getField();
            String msg = error.getDefaultMessage();
            errors.put(field, msg);
        });

        if (isApiRequest(request)) {
            return buildJsonResponse(HttpStatus.BAD_REQUEST, "Validation failed", request.getRequestURI(), errors);
        }
        return buildHtmlErrorView(HttpStatus.BAD_REQUEST, "Nieprawidłowe dane formularza");
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public Object handleNotFound(ResourceNotFoundException ex, HttpServletRequest request) {
        if (isApiRequest(request)) {
            return buildJsonResponse(HttpStatus.NOT_FOUND, ex.getMessage(), request.getRequestURI(), null);
        }
        return buildHtmlErrorView(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(ConflictException.class)
    public Object handleConflict(ConflictException ex, HttpServletRequest request) {
        if (isApiRequest(request)) {
            return buildJsonResponse(HttpStatus.CONFLICT, ex.getMessage(), request.getRequestURI(), null);
        }
        return buildHtmlErrorView(HttpStatus.CONFLICT, ex.getMessage());
    }

    @ExceptionHandler(UnauthorizedException.class)
    public Object handleUnauthorized(UnauthorizedException ex, HttpServletRequest request) {
        if (isApiRequest(request)) {
            return buildJsonResponse(HttpStatus.UNAUTHORIZED, ex.getMessage(), request.getRequestURI(), null);
        }
        return buildHtmlErrorView(HttpStatus.UNAUTHORIZED, ex.getMessage());
    }

    @ExceptionHandler(RuntimeException.class)
    public Object handleRuntime(RuntimeException ex, HttpServletRequest request) {
        if (isApiRequest(request)) {
            return buildJsonResponse(HttpStatus.INTERNAL_SERVER_ERROR, ex.getMessage(), request.getRequestURI(), null);
        }
        return buildHtmlErrorView(HttpStatus.INTERNAL_SERVER_ERROR, "Wystąpił błąd serwera");
    }
}
