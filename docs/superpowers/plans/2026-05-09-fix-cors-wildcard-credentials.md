# Fix CORS — remove allowCredentials with wildcard origins — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove dead CORS configuration from Spring Security (wildcard + credentials combo is invalid per CORS spec, and all browser requests are same-origin anyway).

**Architecture:** Two changes in one file — replace `corsConfigurationSource()` bean with `cors.disable()` and remove the `.cors(Customizer.withDefaults())` usage. No new files, no new tests needed.

**Tech Stack:** Java 17+, Spring Security 6+, Spring Boot

---

### Task 1: Disable CORS in SecurityConfig

**Files:**
- Modify: `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java:29,82-93`

- [ ] **Step 1: Change `.cors(Customizer.withDefaults())` to `.cors(cors -> cors.disable())`**

At line 29, change:
```java
                .cors(Customizer.withDefaults())
```
To:
```java
                .cors(cors -> cors.disable())
```

- [ ] **Step 2: Remove the `corsConfigurationSource()` bean (lines 82-93)**

Remove the entire bean:
```java
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOriginPatterns(List.of("*"));
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
```

- [ ] **Step 3: Remove unused CORS imports**

The following imports are now unused and should be removed:
```java
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
```

- [ ] **Step 4: Build backend to verify compilation**

```bash
./gradlew build -x test
```
Run from `backend/backend/` directory.

Expected: BUILD SUCCESSFUL

- [ ] **Step 5: Commit**

```bash
git add backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java
git commit -m "fix: remove dead CORS config with wildcard + credentials"
```
